import type {
  Article,
  ArticleDetail,
  ArticleReprocessResult,
  DashboardResponse,
  DatabaseMaintenanceResult,
  DatabaseOverview,
  FeishuStatus,
  FeishuTestSendPayload,
  FeishuTestSendResult,
  JobResult,
  JobRun,
  ModelConfig,
  ModelConfigPayload,
  Report,
  ReportDetail,
  ReportUpdatePayload,
  SchedulerStatus,
  StarterOverview,
  Source,
  SourcePayload,
  SourceRule,
  SourceRulePayload,
  SourceRulePreviewPayload,
  SourceRulePreviewResult,
  SourceRuleTemplateResult,
  SystemSetting,
  SystemSettingPayload,
} from '../types/admin'

export class ApiError extends Error {
  status: number
  detail: string

  constructor(status: number, detail: string) {
    super(detail)
    this.name = 'ApiError'
    this.status = status
    this.detail = detail
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(path, {
    headers: {
      'Content-Type': 'application/json',
      ...(init?.headers ?? {}),
    },
    ...init,
  })

  if (!response.ok) {
    const contentType = response.headers.get('content-type') || ''

    if (contentType.includes('application/json')) {
      const payload = (await response.json()) as { detail?: string }
      throw new ApiError(response.status, payload.detail || '请求失败')
    }

    throw new ApiError(response.status, await response.text())
  }

  if (response.status === 204) {
    return undefined as T
  }

  return (await response.json()) as T
}

function encodeReportDate(reportDate?: string): string {
  return reportDate ? `?report_date=${encodeURIComponent(reportDate)}` : ''
}

export const api = {
  getDashboard() {
    return request<DashboardResponse>('/admin/api/dashboard')
  },
  getDatabaseOverview() {
    return request<DatabaseOverview>('/admin/api/database/overview')
  },
  getSources() {
    return request<Source[]>('/admin/api/sources')
  },
  getSource(sourceId: number) {
    return request<Source>(`/admin/api/sources/${sourceId}`)
  },
  createSource(payload: SourcePayload) {
    return request<Source>('/admin/api/sources', {
      method: 'POST',
      body: JSON.stringify(payload),
    })
  },
  updateSource(sourceId: number, payload: Partial<SourcePayload>) {
    return request<Source>(`/admin/api/sources/${sourceId}`, {
      method: 'PUT',
      body: JSON.stringify(payload),
    })
  },
  toggleSource(sourceId: number) {
    return request<Source>(`/admin/api/sources/${sourceId}/toggle`, {
      method: 'POST',
    })
  },
  getSourceRules(sourceId: number) {
    return request<SourceRule | null>(`/admin/api/sources/${sourceId}/rules`)
  },
  saveSourceRules(sourceId: number, payload: SourceRulePayload) {
    return request<SourceRule>(`/admin/api/sources/${sourceId}/rules`, {
      method: 'POST',
      body: JSON.stringify(payload),
    })
  },
  previewSourceRules(sourceId: number, payload: SourceRulePreviewPayload) {
    return request<SourceRulePreviewResult>(`/admin/api/sources/${sourceId}/rules/preview`, {
      method: 'POST',
      body: JSON.stringify(payload),
    })
  },
  getSourceRuleTemplate(sourceId: number) {
    return request<SourceRuleTemplateResult>(`/admin/api/sources/${sourceId}/rules/template`)
  },
  getArticles() {
    return request<Article[]>('/admin/api/articles')
  },
  getArticle(articleId: number) {
    return request<ArticleDetail>(`/admin/api/articles/${articleId}`)
  },
  reprocessArticle(articleId: number) {
    return request<ArticleReprocessResult>(`/admin/api/articles/${articleId}/reprocess`, {
      method: 'POST',
    })
  },
  getModels() {
    return request<ModelConfig[]>('/admin/api/models')
  },
  createModel(payload: ModelConfigPayload) {
    return request<ModelConfig>('/admin/api/models', {
      method: 'POST',
      body: JSON.stringify(payload),
    })
  },
  updateModel(id: number, payload: Partial<ModelConfigPayload>) {
    return request<ModelConfig>(`/admin/api/models/${id}`, {
      method: 'PUT',
      body: JSON.stringify(payload),
    })
  },
  getReports() {
    return request<Report[]>('/admin/api/reports')
  },
  getReport(reportId: number) {
    return request<ReportDetail>(`/admin/api/reports/${reportId}`)
  },
  updateReport(reportId: number, payload: ReportUpdatePayload) {
    return request<ReportDetail>(`/admin/api/reports/${reportId}`, {
      method: 'PUT',
      body: JSON.stringify(payload),
    })
  },
  publishReport(reportId: number) {
    return request<{ message: string; html_url: string | null; report: ReportDetail }>(`/admin/api/reports/${reportId}/publish`, {
      method: 'POST',
    })
  },
  cleanupOldJobs(keepDays: number) {
    return request<DatabaseMaintenanceResult>('/admin/api/database/maintenance/jobs/cleanup', {
      method: 'POST',
      body: JSON.stringify({ keep_days: keepDays }),
    })
  },
  cleanupFailedArticles() {
    return request<DatabaseMaintenanceResult>('/admin/api/database/maintenance/articles/failed/cleanup', {
      method: 'POST',
    })
  },
  deleteReport(reportId: number) {
    return request<DatabaseMaintenanceResult>(`/admin/api/database/reports/${reportId}`, {
      method: 'DELETE',
    })
  },
  getJobs() {
    return request<JobRun[]>('/admin/api/jobs')
  },
  getSchedulerStatus() {
    return request<SchedulerStatus>('/admin/api/scheduler/status')
  },
  getStarterOverview() {
    return request<StarterOverview>('/admin/api/bootstrap/starter')
  },
  applyStarterPresets() {
    return request<{
      created_sources: string[]
      created_models: string[]
      skipped_sources: string[]
      skipped_models: string[]
      overview: StarterOverview
    }>('/admin/api/bootstrap/starter', {
      method: 'POST',
    })
  },
  getSettings() {
    return request<SystemSetting[]>('/admin/api/settings')
  },
  getFeishuStatus() {
    return request<FeishuStatus>('/admin/api/integrations/feishu/status')
  },
  sendFeishuTestMessage(payload: FeishuTestSendPayload) {
    return request<FeishuTestSendResult>('/admin/api/integrations/feishu/test', {
      method: 'POST',
      body: JSON.stringify(payload),
    })
  },
  saveSettingsBatch(payload: SystemSettingPayload[]) {
    return request<SystemSetting[]>('/admin/api/settings/batch', {
      method: 'POST',
      body: JSON.stringify(payload),
    })
  },
  reloadScheduler() {
    return request<SchedulerStatus>('/admin/api/scheduler/reload', {
      method: 'POST',
    })
  },
  runCrawlJob() {
    return request<JobResult>('/admin/api/jobs/crawl/run', {
      method: 'POST',
    })
  },
  runProcessJob() {
    return request<JobResult>('/admin/api/jobs/process/run', {
      method: 'POST',
    })
  },
  runReportJob(reportDate?: string) {
    return request<JobResult>(`/admin/api/jobs/report/run${encodeReportDate(reportDate)}`, {
      method: 'POST',
    })
  },
  runPushJob(reportDate?: string) {
    return request<JobResult>(`/admin/api/jobs/push/run${encodeReportDate(reportDate)}`, {
      method: 'POST',
    })
  },
}
