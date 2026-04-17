from fastapi import APIRouter

from app.api.routes import articles, dashboard, digests, health, sources


api_router = APIRouter()
api_router.include_router(health.router, tags=["health"])
api_router.include_router(dashboard.router, prefix="/dashboard", tags=["dashboard"])
api_router.include_router(articles.router, prefix="/articles", tags=["articles"])
api_router.include_router(sources.router, prefix="/sources", tags=["sources"])
api_router.include_router(digests.router, prefix="/digests", tags=["digests"])
