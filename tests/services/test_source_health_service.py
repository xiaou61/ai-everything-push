from __future__ import annotations

from datetime import datetime, timedelta

import httpx

from app.db.models.source import Source
from app.services.source_health_service import (
    apply_source_crawl_failure,
    apply_source_crawl_success,
    build_retry_schedule,
    derive_source_health,
    should_retry_crawl_error,
)


def test_should_retry_crawl_error_for_timeout_and_5xx():
    request = httpx.Request("GET", "https://example.com/feed.xml")
    response = httpx.Response(503, request=request)
    error = httpx.HTTPStatusError("503 Service Unavailable", request=request, response=response)

    assert should_retry_crawl_error(httpx.TimeoutException("抓取超时")) is True
    assert should_retry_crawl_error(error) is True


def test_should_retry_crawl_error_rejects_404_and_rule_error():
    request = httpx.Request("GET", "https://example.com/feed.xml")
    response = httpx.Response(404, request=request)
    error = httpx.HTTPStatusError("404 Not Found", request=request, response=response)

    assert should_retry_crawl_error(error) is False
    assert should_retry_crawl_error(ValueError("抓取规则配置错误")) is False


def test_build_retry_schedule_caps_retry_attempts():
    now = datetime(2026, 4, 17, 10, 0, 0)

    first = build_retry_schedule(last_retry_attempts=0, now=now)
    exhausted = build_retry_schedule(last_retry_attempts=3, now=now)

    assert first.should_retry is True
    assert first.retry_attempt == 1
    assert first.next_retry_at == now + timedelta(minutes=2)
    assert exhausted.should_retry is False
    assert exhausted.next_retry_at is None


def test_apply_source_crawl_success_resets_failure_state():
    source = _build_source(
        consecutive_failures=2,
        last_retry_attempts=2,
        last_failure_at=datetime(2026, 4, 17, 9, 0, 0),
        last_crawl_error="源站超时",
    )
    now = datetime(2026, 4, 17, 10, 30, 0)

    apply_source_crawl_success(source, processed_count=3, occurred_at=now)

    assert source.last_crawled_at == now
    assert source.last_success_at == now
    assert source.last_crawl_status == "success"
    assert source.consecutive_failures == 0
    assert source.last_crawl_error is None
    assert source.last_crawl_processed_count == 3
    assert source.last_retry_attempts == 0


def test_apply_source_crawl_failure_records_retry_state():
    source = _build_source()
    now = datetime(2026, 4, 17, 11, 0, 0)

    apply_source_crawl_failure(
        source,
        httpx.TimeoutException("源站超时"),
        processed_count=0,
        occurred_at=now,
    )

    assert source.last_crawled_at == now
    assert source.last_failure_at == now
    assert source.last_crawl_status == "failed"
    assert source.consecutive_failures == 1
    assert source.last_retry_attempts == 1
    assert "源站超时" in (source.last_crawl_error or "")


def test_derive_source_health_supports_idle_cooling_and_failed():
    now = datetime(2026, 4, 17, 12, 0, 0)
    idle = derive_source_health(_build_source(), now=now)
    cooling = derive_source_health(
        _build_source(
            last_crawled_at=now - timedelta(minutes=1),
            last_crawl_status="failed",
            consecutive_failures=1,
            last_failure_at=now,
            last_retry_attempts=1,
            last_crawl_error="请求超时",
        ),
        now=now,
    )
    failed = derive_source_health(
        _build_source(
            last_crawled_at=now - timedelta(minutes=20),
            last_crawl_status="failed",
            consecutive_failures=4,
            last_failure_at=now - timedelta(minutes=20),
            last_retry_attempts=3,
            last_crawl_error="请求超时",
        ),
        now=now,
    )

    assert idle.health_level == "idle"
    assert idle.health_label == "未抓取"
    assert cooling.health_level == "cooling"
    assert cooling.can_retry_now is False
    assert cooling.next_retry_at == now + timedelta(minutes=2)
    assert failed.health_level == "failed"
    assert failed.can_retry_now is False


def _build_source(**overrides) -> Source:
    payload = {
        "name": "测试来源",
        "slug": "demo-source",
        "site_url": "https://example.com",
        "source_type": "rss",
        "enabled": True,
        "include_in_daily": True,
        "crawl_interval_minutes": 60,
        "consecutive_failures": 0,
        "last_crawl_processed_count": 0,
        "last_retry_attempts": 0,
    }
    payload.update(overrides)
    return Source(**payload)
