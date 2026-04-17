from pydantic import BaseModel, Field


class DigestArticleItem(BaseModel):
    article_id: int | None = None
    title: str
    original_title: str | None = None
    url: str
    source_name: str
    summary: str
    author: str | None = None
    language: str | None = None
    content: str | None = None
    original_content: str | None = None
    published_at: str | None


class DigestSectionItem(BaseModel):
    category: str
    count: int
    articles: list[DigestArticleItem] = Field(default_factory=list)


class DigestResponse(BaseModel):
    id: int
    digest_date: str
    headline: str
    overview: str
    article_count: int
    section_count: int
    sections: list[DigestSectionItem] = Field(default_factory=list)
    pushed_at: str | None
