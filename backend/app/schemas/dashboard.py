from pydantic import BaseModel


class DashboardResponse(BaseModel):
    source_count: int
    article_count: int
    digest_count: int
    latest_digest_date: str | None
    latest_digest_headline: str | None
    latest_sync_at: str | None

