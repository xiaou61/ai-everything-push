from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse

from app.api.router import api_router
from app.core.config import get_settings
from app.core.database import init_db
from app.core.scheduler import configure_scheduler


settings = get_settings()


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    scheduler = configure_scheduler()
    if not scheduler.running:
        scheduler.start()
    yield
    if scheduler.running:
        scheduler.shutdown(wait=False)


app = FastAPI(title=settings.app_name, lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins or ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(api_router, prefix=settings.api_prefix)


@app.get("/", include_in_schema=False, response_model=None)
async def root():
    index_path = settings.frontend_dist_path / "index.html"
    if index_path.exists():
        return FileResponse(index_path)
    return JSONResponse(
        {
            "message": "Forum Digest Platform backend is running.",
            "frontend_build_expected_at": str(index_path),
        }
    )


@app.get("/{full_path:path}", include_in_schema=False, response_model=None)
async def spa_fallback(full_path: str):
    if full_path.startswith(settings.api_prefix.strip("/")):
        raise HTTPException(status_code=404, detail="Not found")

    target_path = settings.frontend_dist_path / full_path
    if target_path.exists() and target_path.is_file():
        return FileResponse(target_path)

    index_path = settings.frontend_dist_path / "index.html"
    if index_path.exists():
        return FileResponse(index_path)

    raise HTTPException(status_code=404, detail="Page not found")
