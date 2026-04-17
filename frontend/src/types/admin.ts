export interface DashboardStats {
  source_count: number
  enabled_source_count: number
  article_count: number
  report_count: number
  model_count: number
  job_count: number
}

export interface SchedulerStatus {
  available: boolean
  running: boolean
  enabled: boolean
  jobs: string[]
  message: string
}

export interface JobRun {
  id: number
  job_name: string
  trigger_type: string
  status: string
  started_at: string | null
  finished_at: string | null
  processed_count: number
  error_message: string | null
  details_json: string | null
}

export interface DashboardResponse {
  stats: DashboardStats
  recent_jobs: JobRun[]
  scheduler_status: SchedulerStatus
  starter: StarterOverview
}

export interface Source {
  id: number
  name: string
  slug: string
  site_url: string
  source_type: 'rss' | 'web'
  feed_url: string | null
  list_url: string | null
  language_hint: string | null
  category: string | null
  enabled: boolean
  include_in_daily: boolean
  crawl_interval_minutes: number
  last_crawled_at: string | null
  last_crawl_status: 'success' | 'failed' | 'partial_success' | null
  consecutive_failures: number
  last_crawl_error: string | null
  last_crawl_processed_count: number
}

export interface SourcePayload {
  name: string
  slug: string
  site_url: string
  source_type: 'rss' | 'web'
  feed_url: string | null
  list_url: string | null
  language_hint: string | null
  category: string | null
  enabled: boolean
  include_in_daily: boolean
  crawl_interval_minutes: number
}

export interface SourceRule {
  id: number
  source_id: number
  list_item_selector: string | null
  link_selector: string | null
  title_selector: string | null
  published_at_selector: string | null
  author_selector: string | null
  content_selector: string | null
  remove_selectors: string | null
  request_headers_json: string | null
}

export interface SourceRulePayload {
  list_item_selector: string | null
  link_selector: string | null
  title_selector: string | null
  published_at_selector: string | null
  author_selector: string | null
  content_selector: string | null
  remove_selectors: string | null
  request_headers_json: string | null
}

export interface SourceRulePreviewPayload extends SourceRulePayload {
  preview_mode: 'list' | 'article'
  preview_url?: string | null
}

export interface SourceRulePreviewResult {
  mode: 'list' | 'article'
  source_type: string
  request_url: string
  article_url: string | null
  items: Array<{ title: string; url: string }>
  extracted_text: string | null
  extracted_length: number | null
}

export interface SourceRuleTemplateResult {
  available: boolean
  requires_rule: boolean
  message: string
  payload: SourceRulePayload | null
}

export interface Article {
  id: number
  title: string
  canonical_url: string
  language: string | null
  status: string
  source_name: string
  source_id: number
  published_at: string | null
  generated_title: string | null
  summary: string | null
  category: string | null
  has_content: boolean
}

export interface ModelConfig {
  id: number
  task_type: 'translation' | 'summary' | 'classification' | 'title'
  provider_name: string
  model_name: string
  base_url: string
  api_key_env_name: string
  temperature: string
  max_tokens: number
  enabled: boolean
  is_default: boolean
}

export interface ModelConfigPayload {
  task_type: 'translation' | 'summary' | 'classification' | 'title'
  provider_name: string
  model_name: string
  base_url: string
  api_key_env_name: string
  temperature: string
  max_tokens: number
  enabled: boolean
  is_default: boolean
}

export interface Report {
  id: number
  report_date: string
  title: string
  intro: string | null
  status: string
  html_path: string | null
  html_url: string | null
  source_count: number
  article_count: number
  feishu_pushed: boolean
  created_at: string
  updated_at: string
}

export interface SystemSetting {
  id: number
  setting_key: string
  setting_value: string
  description: string
}

export interface SystemSettingPayload {
  setting_key: string
  setting_value: string
  description: string
}

export interface FeishuStatus {
  configured: boolean
  masked_webhook: string
  site_base_url: string
  message: string
}

export interface FeishuTestSendPayload {
  title: string
  message: string
}

export interface FeishuTestSendResult {
  status: string
  message: string
  detail: string
}

export interface JobResult {
  job_id?: number
  job_name?: string
  source_count?: number
  processed_count?: number
  created_count?: number
  updated_count?: number
  success_count?: number
  failed_count?: number
  report_id?: number
  report_date?: string
  article_count?: number
  html_url?: string | null
  errors?: string[]
  message?: string
  [key: string]: unknown
}

export interface StarterSourcePreset {
  name: string
  slug: string
  source_type: 'rss' | 'web'
  site_url: string
  list_url: string | null
  feed_url: string | null
  category: string | null
  language_hint: string | null
  enabled: boolean
  include_in_daily: boolean
  crawl_interval_minutes: number
  exists: boolean
}

export interface StarterModelPreset {
  task_type: 'translation' | 'summary' | 'classification' | 'title'
  provider_name: string
  model_name: string
  base_url: string
  api_key_env_name: string
  temperature: string
  max_tokens: number
  enabled: boolean
  is_default: boolean
  exists: boolean
}

export interface StarterOverview {
  sources: StarterSourcePreset[]
  models: StarterModelPreset[]
  missing_source_count: number
  missing_model_count: number
}

export interface DatabaseTableStat {
  key: string
  label: string
  description: string
  count: number
  last_updated_at: string | null
}

export interface DatabaseBreakdownItem {
  key: string
  label: string
  count: number
}

export interface DatabaseOverview {
  connection: {
    dialect: string
    driver: string
    database: string
    masked_url: string
  }
  tables: DatabaseTableStat[]
  metrics: {
    total_rows: number
    article_count: number
    failed_articles: number
    report_count: number
    job_run_count: number
  }
  article_status_breakdown: DatabaseBreakdownItem[]
  source_health_breakdown: DatabaseBreakdownItem[]
  recent: {
    latest_report_date: string | null
    latest_article_created_at: string | null
    latest_job_started_at: string | null
  }
}

export interface DatabaseMaintenanceResult {
  action: string
  deleted_count: number
  message: string
  keep_days?: number
  deleted_content_count?: number
  deleted_report_item_count?: number
  report_date?: string
  removed_html?: boolean
}
