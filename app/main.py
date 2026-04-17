from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.api.routes.admin_pages import router as admin_pages_router
from app.api.routes.admin_actions import router as admin_actions_router
from app.api.routes.health import router as health_router
from app.api.routes.jobs import router as jobs_router
from app.api.routes.models import router as models_router
from app.api.routes.reports import router as reports_router
from app.api.routes.settings import router as settings_router
from app.api.routes.source_rules import router as source_rules_router
from app.api.routes.sources import router as sources_router
from app.core.config import get_settings
from app.core.database import SessionLocal, init_db
from app.core.logging import configure_logging
from app.services.scheduler.runtime import scheduler_runtime
from app.services.system_setting_service import ensure_default_settings

BASE_DIR = Path(__file__).resolve().parent
settings = get_settings()


@asynccontextmanager
async def lifespan(_: FastAPI):
    configure_logging()
    init_db()
    session = SessionLocal()
    try:
        ensure_default_settings(session)
    finally:
        session.close()
    scheduler_runtime.start()
    yield
    scheduler_runtime.stop()


app = FastAPI(title=settings.app_name, debug=settings.app_debug, lifespan=lifespan)
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")

app.include_router(health_router)
app.include_router(admin_pages_router)
app.include_router(admin_actions_router)
app.include_router(sources_router)
app.include_router(models_router)
app.include_router(jobs_router)
app.include_router(reports_router)
app.include_router(settings_router)
app.include_router(source_rules_router)
