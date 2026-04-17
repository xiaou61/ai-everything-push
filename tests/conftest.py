from __future__ import annotations

import os
from pathlib import Path
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

TEST_DB_PATH = Path(f"tests/test_app_{uuid4().hex}.db")
os.environ["DATABASE_URL"] = f"sqlite+pysqlite:///./{TEST_DB_PATH.as_posix()}"
os.environ["APP_ENV"] = "test"

from app.core.database import SessionLocal, engine, init_db  # noqa: E402
from app.main import app  # noqa: E402


@pytest.fixture(scope="session", autouse=True)
def setup_test_database():
    if TEST_DB_PATH.exists():
        TEST_DB_PATH.unlink(missing_ok=True)
    init_db()
    yield
    engine.dispose()
    if TEST_DB_PATH.exists():
        TEST_DB_PATH.unlink(missing_ok=True)


@pytest.fixture(autouse=True)
def clean_tables():
    from app.db.models import Article, ArticleContent, DailyReport, DailyReportItem, JobRun, ModelConfig, Source, SourceRule, SystemSetting

    session = SessionLocal()
    try:
        for model in [DailyReportItem, DailyReport, ArticleContent, Article, SourceRule, Source, ModelConfig, JobRun, SystemSetting]:
            session.query(model).delete()
        session.commit()
        yield
    finally:
        session.close()


@pytest.fixture()
def client():
    with TestClient(app) as test_client:
        yield test_client
