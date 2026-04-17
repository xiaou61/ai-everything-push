from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Iterable, Optional

import httpx

from app.db.models.source import Source

MAX_RETRY_ATTEMPTS = 3
RETRY_BACKOFF_MINUTES = (2, 5, 15)
HEALTH_LABELS = {
    "idle": "未抓取",
    "healthy": "健康",
    "warning": "待重试",
    "cooling": "冷却中",
    "failed": "失败",
}
RETRYABLE_STATUS_CODES = {429, 500, 502, 503, 504}
RETRYABLE_MESSAGE_HINTS = (
    "timeout",
    "timed out",
    "超时",
    "连接失败",
    "connection",
    "network",
    "temporarily unavailable",
    "service unavailable",
    "429",
    "502",
    "503",
    "504",
)
NON_RETRYABLE_MESSAGE_HINTS = (
    "404",
    "not found",
    "invalid url",
    "配置错误",
    "规则错误",
    "selector",
    "schema",
)


@dataclass(frozen=True)
class RetrySchedule:
    should_retry: bool
    retry_attempt: int
    next_retry_at: Optional[datetime]
    wait_minutes: Optional[int]


@dataclass(frozen=True)
class SourceHealthSnapshot:
    health_level: str
    health_label: str
    next_retry_at: Optional[datetime]
    can_retry_now: bool


def should_retry_crawl_error(error: Exception) -> bool:
    # 优先识别明确的网络层异常，再用错误文案兜底，减少不同抓取器实现带来的耦合。
    if isinstance(error, (httpx.TimeoutException, httpx.ConnectError, httpx.NetworkError)):
        return True

    if isinstance(error, httpx.HTTPStatusError):
        status_code = error.response.status_code if error.response is not None else None
        return status_code in RETRYABLE_STATUS_CODES

    message = _extract_error_message(error).lower()
    if any(keyword in message for keyword in NON_RETRYABLE_MESSAGE_HINTS):
        return False
    return any(keyword in message for keyword in RETRYABLE_MESSAGE_HINTS)


def build_retry_schedule(last_retry_attempts: int, now: Optional[datetime] = None) -> RetrySchedule:
    current_time = _normalize_datetime(now) or datetime.utcnow()
    retry_attempt = max(last_retry_attempts, 0) + 1
    if retry_attempt > MAX_RETRY_ATTEMPTS:
        return RetrySchedule(False, max(last_retry_attempts, 0), None, None)

    wait_minutes = RETRY_BACKOFF_MINUTES[min(retry_attempt - 1, len(RETRY_BACKOFF_MINUTES) - 1)]
    return RetrySchedule(
        should_retry=True,
        retry_attempt=retry_attempt,
        next_retry_at=current_time + timedelta(minutes=wait_minutes),
        wait_minutes=wait_minutes,
    )


def calculate_next_retry_at(source: Source) -> Optional[datetime]:
    if source.last_failure_at is None or source.last_retry_attempts <= 0:
        return None

    if source.last_retry_attempts > MAX_RETRY_ATTEMPTS:
        return None

    retry_index = min(source.last_retry_attempts - 1, len(RETRY_BACKOFF_MINUTES) - 1)
    failure_time = _normalize_datetime(source.last_failure_at)
    if failure_time is None:
        return None
    return failure_time + timedelta(minutes=RETRY_BACKOFF_MINUTES[retry_index])


def derive_source_health(source: Source, now: Optional[datetime] = None) -> SourceHealthSnapshot:
    current_time = _normalize_datetime(now) or datetime.utcnow()
    retryable_error = _can_retry_from_source_state(source)
    next_retry_at = calculate_next_retry_at(source) if retryable_error else None
    can_retry_now = bool(next_retry_at is not None and next_retry_at <= current_time and not _is_retry_exhausted(source))

    if source.last_crawl_status is None and source.last_crawled_at is None:
        return _build_snapshot("idle", None, False)

    if source.last_crawl_status == "success" and source.consecutive_failures == 0:
        return _build_snapshot("healthy", None, False)

    if source.last_crawl_status == "partial_success":
        if next_retry_at is not None and not can_retry_now:
            return _build_snapshot("cooling", next_retry_at, False)
        return _build_snapshot("warning", next_retry_at, can_retry_now)

    if source.last_crawl_status == "failed":
        # 连续失败次数超过已安排的重试阶段时，说明自动重试额度已经耗尽。
        if _is_retry_exhausted(source) or not retryable_error:
            return _build_snapshot("failed", None, False)
        if next_retry_at is not None and not can_retry_now:
            return _build_snapshot("cooling", next_retry_at, False)
        return _build_snapshot("warning", next_retry_at, can_retry_now)

    if source.consecutive_failures > 0:
        return _build_snapshot("warning", next_retry_at, can_retry_now)

    return _build_snapshot("healthy", None, False)


def apply_source_crawl_success(
    source: Source,
    processed_count: int,
    occurred_at: Optional[datetime] = None,
) -> None:
    current_time = _normalize_datetime(occurred_at) or datetime.utcnow()
    source.last_crawled_at = current_time
    source.last_success_at = current_time
    source.last_crawl_status = "success"
    source.consecutive_failures = 0
    source.last_retry_attempts = 0
    source.last_crawl_error = None
    source.last_crawl_processed_count = processed_count


def apply_source_crawl_failure(
    source: Source,
    error: Exception,
    processed_count: int,
    occurred_at: Optional[datetime] = None,
) -> RetrySchedule:
    current_time = _normalize_datetime(occurred_at) or datetime.utcnow()
    source.last_crawled_at = current_time
    source.last_failure_at = current_time
    source.last_crawl_status = "partial_success" if processed_count > 0 else "failed"
    source.consecutive_failures = max(source.consecutive_failures, 0) + 1
    source.last_crawl_error = _extract_error_message(error)
    source.last_crawl_processed_count = processed_count

    if should_retry_crawl_error(error):
        # 这里记录的是“当前已安排到第几次重试”，方便前端直接展示冷却阶段。
        schedule = build_retry_schedule(source.last_retry_attempts, now=current_time)
        if schedule.should_retry:
            source.last_retry_attempts = schedule.retry_attempt
        else:
            source.last_retry_attempts = max(source.last_retry_attempts, MAX_RETRY_ATTEMPTS)
        return schedule

    source.last_retry_attempts = 0
    return RetrySchedule(False, 0, None, None)


def should_skip_source_crawl(source: Source, now: Optional[datetime] = None) -> bool:
    return derive_source_health(source, now=now).health_level == "cooling"


def serialize_source(source: Source, now: Optional[datetime] = None) -> dict:
    health = derive_source_health(source, now=now)
    return {
        "id": source.id,
        "name": source.name,
        "slug": source.slug,
        "site_url": source.site_url,
        "source_type": source.source_type,
        "feed_url": source.feed_url,
        "list_url": source.list_url,
        "language_hint": source.language_hint,
        "category": source.category,
        "enabled": source.enabled,
        "include_in_daily": source.include_in_daily,
        "crawl_interval_minutes": source.crawl_interval_minutes,
        "last_crawled_at": source.last_crawled_at,
        "last_success_at": source.last_success_at,
        "last_failure_at": source.last_failure_at,
        "last_crawl_status": source.last_crawl_status,
        "consecutive_failures": source.consecutive_failures,
        "last_retry_attempts": source.last_retry_attempts,
        "last_crawl_error": source.last_crawl_error,
        "last_crawl_processed_count": source.last_crawl_processed_count,
        "next_retry_at": health.next_retry_at,
        "can_retry_now": health.can_retry_now,
        "health_level": health.health_level,
        "health_label": health.health_label,
    }


def summarize_source_health(sources: Iterable[Source], now: Optional[datetime] = None) -> dict:
    summary = {key: 0 for key in HEALTH_LABELS}
    for source in sources:
        summary[derive_source_health(source, now=now).health_level] += 1
    return summary


def build_source_alerts(sources: Iterable[Source], now: Optional[datetime] = None, limit: int = 5) -> dict:
    current_time = _normalize_datetime(now) or datetime.utcnow()
    serialized_sources = [serialize_source(item, now=current_time) for item in sources]
    abnormal_sources = [item for item in serialized_sources if item["health_level"] in {"warning", "cooling", "failed"}]
    recent_failures = sorted(
        abnormal_sources,
        key=lambda item: _normalize_datetime(item["last_failure_at"]) or datetime.min,
        reverse=True,
    )

    return {
        "abnormal_count": len(abnormal_sources),
        "cooling_count": sum(1 for item in abnormal_sources if item["health_level"] == "cooling"),
        "failed_count": sum(1 for item in abnormal_sources if item["health_level"] == "failed"),
        "warning_count": sum(1 for item in abnormal_sources if item["health_level"] == "warning"),
        "recent_failures": recent_failures[:limit],
    }


def _build_snapshot(level: str, next_retry_at: Optional[datetime], can_retry_now: bool) -> SourceHealthSnapshot:
    return SourceHealthSnapshot(
        health_level=level,
        health_label=HEALTH_LABELS[level],
        next_retry_at=next_retry_at,
        can_retry_now=can_retry_now,
    )


def _can_retry_from_source_state(source: Source) -> bool:
    if not source.last_crawl_error:
        return False
    if source.last_retry_attempts <= 0 and source.last_crawl_status != "failed":
        return False
    return should_retry_crawl_error(RuntimeError(source.last_crawl_error))


def _is_retry_exhausted(source: Source) -> bool:
    return source.last_retry_attempts >= MAX_RETRY_ATTEMPTS and source.consecutive_failures > source.last_retry_attempts


def _extract_error_message(error: Exception) -> str:
    if isinstance(error, httpx.HTTPStatusError) and error.response is not None:
        return f"HTTP {error.response.status_code}: {error}"
    return str(error)


def _normalize_datetime(value: Optional[datetime]) -> Optional[datetime]:
    if value is None:
        return None
    if value.tzinfo is None:
        return value
    return value.astimezone(timezone.utc).replace(tzinfo=None)
