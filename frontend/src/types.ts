export type SourceType = 'rss' | 'json' | 'html'

export interface DashboardPayload {
  source_count: number
  article_count: number
  digest_count: number
  latest_digest_date: string | null
  latest_digest_headline: string | null
  latest_sync_at: string | null
}

export interface SourcePayload {
  id: number
  name: string
  url: string
  source_type: SourceType
  category_hint: string | null
  parser_config: Record<string, unknown>
  enabled: boolean
  fetch_limit: number
  last_synced_at: string | null
  created_at: string
  updated_at: string
}

export interface SourceDraft {
  name: string
  url: string
  source_type: SourceType
  category_hint: string
  parser_config: Record<string, unknown>
  enabled: boolean
  fetch_limit: number
}

export interface DigestArticleItem {
  article_id: number | null
  title: string
  original_title: string | null
  url: string
  source_name: string
  summary: string
  author: string | null
  language: string | null
  content: string | null
  original_content: string | null
  published_at: string | null
}

export interface DigestSectionItem {
  category: string
  count: number
  articles: DigestArticleItem[]
}

export interface DigestPayload {
  id: number
  digest_date: string
  headline: string
  overview: string
  article_count: number
  section_count: number
  sections: DigestSectionItem[]
  pushed_at: string | null
}

export interface ArticleDetailPayload {
  id: number
  title: string
  original_title: string
  url: string
  source_name: string
  category: string
  summary: string
  author: string | null
  language: string
  content: string | null
  original_content: string | null
  published_at: string | null
  created_at: string
  updated_at: string
  raw_payload: Record<string, unknown>
}
