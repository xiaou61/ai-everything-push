# 技术论坛日报 Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 构建一个本地可运行的技术论坛日报系统，支持内容源管理、文章采集、英文翻译、中文汇总、日报生成、网页访问和飞书推送。

**Architecture:** 使用 `FastAPI` 单体应用承载后台页面、API 和日报访问；以 `MySQL + SQLAlchemy` 做数据持久化，`APScheduler` 负责定时任务，`LangChain` 统一封装翻译、摘要、分类、标题生成链路。首版以服务端渲染后台页面为主，优先打通完整流程。

**Tech Stack:** Python 3.12、FastAPI、Jinja2、SQLAlchemy、Alembic、MySQL、LangChain、APScheduler、httpx、feedparser、BeautifulSoup4、pytest

---

### Task 1: 初始化项目骨架

**Files:**
- Create: `pyproject.toml`
- Create: `.gitignore`
- Create: `.env.example`
- Create: `README.md`
- Create: `app/__init__.py`
- Create: `app/main.py`
- Create: `app/core/config.py`
- Create: `app/core/database.py`
- Create: `app/core/logging.py`
- Create: `app/templates/base.html`
- Create: `app/static/styles.css`
- Test: `tests/test_health.py`

**Step 1: Write the failing test**

```python
from fastapi.testclient import TestClient

from app.main import app


def test_health_check():
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_health.py -v`
Expected: FAIL with import or route missing error

**Step 3: Write minimal implementation**

```python
from fastapi import FastAPI

app = FastAPI()


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_health.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add .
git commit -m "feat: initialize fastapi project skeleton"
```

### Task 2: 建立数据库基础设施与 ORM 模型

**Files:**
- Modify: `app/core/database.py`
- Create: `app/db/base.py`
- Create: `app/db/models/source.py`
- Create: `app/db/models/article.py`
- Create: `app/db/models/report.py`
- Create: `app/db/models/model_config.py`
- Create: `app/db/models/job_run.py`
- Create: `app/db/models/system_setting.py`
- Create: `tests/db/test_models.py`

**Step 1: Write the failing test**

```python
from app.db.models.source import Source


def test_source_model_has_expected_fields():
    assert hasattr(Source, "name")
    assert hasattr(Source, "source_type")
    assert hasattr(Source, "enabled")
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/db/test_models.py -v`
Expected: FAIL with model import error

**Step 3: Write minimal implementation**

```python
class Source(Base):
    __tablename__ = "sources"
    id = mapped_column(Integer, primary_key=True)
    name = mapped_column(String(255), nullable=False)
    source_type = mapped_column(String(32), nullable=False)
    enabled = mapped_column(Boolean, default=True, nullable=False)
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/db/test_models.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add .
git commit -m "feat: add core database models"
```

### Task 3: 实现后台首页和内容源管理

**Files:**
- Create: `app/api/routes/admin_pages.py`
- Create: `app/api/routes/sources.py`
- Create: `app/schemas/source.py`
- Create: `app/services/source_service.py`
- Create: `app/templates/dashboard.html`
- Create: `app/templates/sources/list.html`
- Create: `app/templates/sources/form.html`
- Create: `tests/routes/test_sources.py`

**Step 1: Write the failing test**

```python
def test_create_source(client):
    response = client.post(
        "/admin/api/sources",
        json={
            "name": "美团技术团队",
            "slug": "meituan-tech",
            "source_type": "web",
            "site_url": "https://tech.meituan.com",
        },
    )
    assert response.status_code == 201
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/routes/test_sources.py -v`
Expected: FAIL with route missing error

**Step 3: Write minimal implementation**

```python
@router.post("/admin/api/sources", status_code=201)
def create_source(payload: SourceCreate, session: SessionDep):
    source = source_service.create_source(session, payload)
    return {"id": source.id}
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/routes/test_sources.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add .
git commit -m "feat: add source management pages"
```

### Task 4: 实现模型配置管理

**Files:**
- Create: `app/api/routes/models.py`
- Create: `app/schemas/model_config.py`
- Create: `app/services/model_config_service.py`
- Create: `app/templates/models/list.html`
- Create: `tests/routes/test_model_configs.py`

**Step 1: Write the failing test**

```python
def test_create_task_model_config(client):
    response = client.post(
        "/admin/api/models",
        json={
            "task_type": "translation",
            "provider_name": "relay",
            "model_name": "gpt-4.1-mini",
            "base_url": "https://example.com/v1",
            "api_key_env_name": "OPENAI_API_KEY",
        },
    )
    assert response.status_code == 201
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/routes/test_model_configs.py -v`
Expected: FAIL with route missing error

**Step 3: Write minimal implementation**

```python
@router.post("/admin/api/models", status_code=201)
def create_model_config(payload: ModelConfigCreate, session: SessionDep):
    record = service.create_model_config(session, payload)
    return {"id": record.id}
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/routes/test_model_configs.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add .
git commit -m "feat: add model configuration management"
```

### Task 5: 实现 RSS 与网页抓取器

**Files:**
- Create: `app/services/crawler/rss_client.py`
- Create: `app/services/crawler/web_client.py`
- Create: `app/services/crawler/content_extractor.py`
- Create: `app/services/crawler/pipeline.py`
- Create: `tests/services/test_rss_client.py`
- Create: `tests/services/test_web_client.py`

**Step 1: Write the failing test**

```python
def test_parse_rss_entries(sample_rss_content):
    entries = parse_feed_entries(sample_rss_content)
    assert len(entries) == 2
    assert entries[0].title == "Example article"
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/services/test_rss_client.py -v`
Expected: FAIL with function missing error

**Step 3: Write minimal implementation**

```python
def parse_feed_entries(raw_xml: str) -> list[FeedEntry]:
    parsed = feedparser.parse(raw_xml)
    return [FeedEntry(title=item.title, link=item.link) for item in parsed.entries]
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/services/test_rss_client.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add .
git commit -m "feat: add rss and web crawling services"
```

### Task 6: 实现文章入库与去重

**Files:**
- Create: `app/db/repositories/article_repository.py`
- Create: `app/services/article_ingest_service.py`
- Create: `tests/services/test_article_ingest.py`

**Step 1: Write the failing test**

```python
def test_duplicate_article_is_skipped(session, source):
    first = ingest_article(session, source, "https://example.com/a")
    second = ingest_article(session, source, "https://example.com/a")
    assert first.id == second.id
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/services/test_article_ingest.py -v`
Expected: FAIL with repository/service missing error

**Step 3: Write minimal implementation**

```python
def ingest_article(session: Session, source: Source, url: str) -> Article:
    url_hash = sha256(url.encode("utf-8")).hexdigest()
    existing = repo.get_by_hash(session, url_hash)
    if existing:
        return existing
    return repo.create(session, source_id=source.id, canonical_url=url, url_hash=url_hash)
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/services/test_article_ingest.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add .
git commit -m "feat: add article ingestion and deduplication"
```

### Task 7: 实现 LangChain 任务链

**Files:**
- Create: `app/services/ai/client_factory.py`
- Create: `app/services/ai/prompts.py`
- Create: `app/services/ai/translation_chain.py`
- Create: `app/services/ai/summary_chain.py`
- Create: `app/services/ai/classification_chain.py`
- Create: `app/services/ai/title_chain.py`
- Create: `app/services/ai/pipeline.py`
- Create: `tests/services/test_ai_pipeline.py`

**Step 1: Write the failing test**

```python
def test_translation_is_skipped_for_chinese():
    result = should_translate("zh-cn")
    assert result is False
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/services/test_ai_pipeline.py -v`
Expected: FAIL with function missing error

**Step 3: Write minimal implementation**

```python
def should_translate(language: str) -> bool:
    return language.lower().startswith("en")
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/services/test_ai_pipeline.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add .
git commit -m "feat: add langchain task pipelines"
```

### Task 8: 实现日报聚合与页面渲染

**Files:**
- Create: `app/services/report/report_service.py`
- Create: `app/services/report/html_renderer.py`
- Create: `app/api/routes/reports.py`
- Create: `app/templates/reports/detail.html`
- Create: `app/templates/reports/list.html`
- Create: `tests/services/test_report_service.py`

**Step 1: Write the failing test**

```python
def test_generate_daily_report_groups_articles_by_category(session, articles):
    report = generate_daily_report(session, date(2026, 4, 17))
    assert report.article_count == 3
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/services/test_report_service.py -v`
Expected: FAIL with service missing error

**Step 3: Write minimal implementation**

```python
def generate_daily_report(session: Session, report_date: date) -> DailyReport:
    articles = repo.list_ready_articles_for_date(session, report_date)
    return report_repo.create_from_articles(session, report_date, articles)
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/services/test_report_service.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add .
git commit -m "feat: add daily report generation"
```

### Task 9: 实现飞书推送

**Files:**
- Create: `app/services/notifier/feishu.py`
- Create: `tests/services/test_feishu.py`

**Step 1: Write the failing test**

```python
def test_build_feishu_payload():
    payload = build_report_payload(
        title="技术日报",
        highlights=["A", "B", "C"],
        url="http://localhost:8000/daily/2026-04-17",
    )
    assert "技术日报" in str(payload)
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/services/test_feishu.py -v`
Expected: FAIL with function missing error

**Step 3: Write minimal implementation**

```python
def build_report_payload(title: str, highlights: list[str], url: str) -> dict:
    return {
        "msg_type": "post",
        "content": {"post": {"zh_cn": {"title": title, "content": [[{"tag": "text", "text": url}]]}}},
    }
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/services/test_feishu.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add .
git commit -m "feat: add feishu notifier"
```

### Task 10: 实现定时任务与手动触发

**Files:**
- Create: `app/services/scheduler/jobs.py`
- Create: `app/services/scheduler/runtime.py`
- Create: `tests/services/test_scheduler_jobs.py`

**Step 1: Write the failing test**

```python
def test_job_names_are_registered():
    names = list_job_names()
    assert "crawl_sources_job" in names
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/services/test_scheduler_jobs.py -v`
Expected: FAIL with function missing error

**Step 3: Write minimal implementation**

```python
def list_job_names() -> list[str]:
    return ["crawl_sources_job", "process_articles_job", "generate_and_push_report_job"]
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/services/test_scheduler_jobs.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add .
git commit -m "feat: add scheduler jobs"
```

### Task 11: 完善基础测试与示例数据

**Files:**
- Create: `tests/conftest.py`
- Create: `tests/fixtures/sample_rss.xml`
- Create: `tests/fixtures/sample_article.html`
- Modify: `README.md`

**Step 1: Write the failing test**

```python
def test_dashboard_page(client):
    response = client.get("/admin")
    assert response.status_code == 200
```

**Step 2: Run test to verify it fails**

Run: `pytest -v`
Expected: FAIL because integration paths are not fully wired

**Step 3: Write minimal implementation**

```python
@router.get("/admin")
def admin_dashboard(request: Request):
    return templates.TemplateResponse("dashboard.html", {"request": request})
```

**Step 4: Run test to verify it passes**

Run: `pytest -v`
Expected: PASS or only remaining known failures

**Step 5: Commit**

```bash
git add .
git commit -m "test: add baseline fixtures and integration coverage"
```

### Task 12: 补全文档与本地启动说明

**Files:**
- Modify: `README.md`
- Modify: `.env.example`
- Create: `docs/reports/.gitkeep`
- Create: `docs/previews/.gitkeep`

**Step 1: Write the failing test**

```python
def test_env_example_contains_required_keys():
    content = Path(".env.example").read_text(encoding="utf-8")
    assert "DATABASE_URL" in content
    assert "OPENAI_API_KEY" in content
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_docs.py -v`
Expected: FAIL with missing configuration docs

**Step 3: Write minimal implementation**

```env
DATABASE_URL=mysql+pymysql://root:password@127.0.0.1:3306/tech_daily
OPENAI_API_KEY=replace_me
OPENAI_BASE_URL=https://your-relay.example.com/v1
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_docs.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add .
git commit -m "docs: add local setup instructions"
```
