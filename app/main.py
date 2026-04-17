from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles

from app.api.routes.admin_data import router as admin_data_router
from app.api.routes.admin_pages import router as admin_pages_router
from app.api.routes.admin_actions import router as admin_actions_router
from app.api.routes.articles import router as articles_router
from app.api.routes.health import router as health_router
from app.api.routes.jobs import router as jobs_router
from app.api.routes.models import router as models_router
from app.api.routes.database_admin import router as database_admin_router
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
PROJECT_DIR = BASE_DIR.parent
FRONTEND_DIST_DIR = PROJECT_DIR / "frontend" / "dist"
FRONTEND_ASSETS_DIR = FRONTEND_DIST_DIR / "assets"
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
if FRONTEND_ASSETS_DIR.exists():
    app.mount("/admin/assets", StaticFiles(directory=str(FRONTEND_ASSETS_DIR)), name="admin-assets")


@app.get("/admin", include_in_schema=False)
def admin_root_redirect():
    return RedirectResponse(url="/admin/", status_code=307)


@app.get("/admin/", include_in_schema=False)
def admin_spa_index():
    index_file = FRONTEND_DIST_DIR / "index.html"
    if index_file.exists():
        return FileResponse(index_file)
    return HTMLResponse(
        content=(
            "<html><body><h1>前端尚未构建</h1>"
            "<p>请先在 frontend 目录执行 npm run build，"
            "或在开发模式下访问 Vite 地址 http://127.0.0.1:5173/admin/ 。</p></body></html>"
        ),
        status_code=503,
    )


@app.get("/admin/favicon.svg", include_in_schema=False)
def admin_spa_favicon():
    asset_file = FRONTEND_DIST_DIR / "favicon.svg"
    if asset_file.exists():
        return FileResponse(asset_file)
    raise HTTPException(status_code=404, detail="资源不存在")


@app.get("/admin/icons.svg", include_in_schema=False)
def admin_spa_icons():
    asset_file = FRONTEND_DIST_DIR / "icons.svg"
    if asset_file.exists():
        return FileResponse(asset_file)
    raise HTTPException(status_code=404, detail="资源不存在")

app.include_router(health_router)
app.include_router(admin_data_router)
app.include_router(database_admin_router)
app.include_router(articles_router)
app.include_router(admin_pages_router)
app.include_router(admin_actions_router)
app.include_router(sources_router)
app.include_router(models_router)
app.include_router(jobs_router)
app.include_router(reports_router)
app.include_router(settings_router)
app.include_router(source_rules_router)
