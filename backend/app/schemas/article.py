from pydantic import BaseModel


class ArticleResponse(BaseModel):
    id: int
    title: str
    original_title: str
    url: str
    source_name: str
    category: str
    summary: str
    author: str | None
    language: str
    content: str | None
    original_content: str | None
    published_at: str | None
    created_at: str
    updated_at: str
    raw_payload: dict
