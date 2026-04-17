import type { ArticleDetailPayload, DashboardPayload, DigestPayload, SourceDraft, SourcePayload } from '../types'

const apiBaseUrl = import.meta.env.VITE_API_BASE_URL || '/api/v1'

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${apiBaseUrl}${path}`, {
    headers: {
      'Content-Type': 'application/json',
      ...(init?.headers ?? {}),
    },
    ...init,
  })

  if (!response.ok) {
    const payload = await response.json().catch(() => ({ detail: '请求失败' }))
    throw new Error(payload.detail || '请求失败')
  }

  return response.json() as Promise<T>
}

export const api = {
  getDashboard(): Promise<DashboardPayload> {
    return request<DashboardPayload>('/dashboard')
  },
  getDigests(): Promise<DigestPayload[]> {
    return request<DigestPayload[]>('/digests')
  },
  getDigestByDate(digestDate: string): Promise<DigestPayload> {
    return request<DigestPayload>(`/digests/by-date/${digestDate}`)
  },
  getArticleById(articleId: number): Promise<ArticleDetailPayload> {
    return request<ArticleDetailPayload>(`/articles/${articleId}`)
  },
  generateDigest(digestDate?: string): Promise<DigestPayload> {
    const query = digestDate ? `?digest_date=${encodeURIComponent(digestDate)}` : ''
    return request<DigestPayload>(`/digests/generate${query}`, {
      method: 'POST',
    })
  },
  pushDigest(digestId: number): Promise<DigestPayload> {
    return request<DigestPayload>(`/digests/${digestId}/push`, {
      method: 'POST',
    })
  },
  getSources(): Promise<SourcePayload[]> {
    return request<SourcePayload[]>('/sources')
  },
  createSource(payload: SourceDraft): Promise<SourcePayload> {
    return request<SourcePayload>('/sources', {
      method: 'POST',
      body: JSON.stringify(payload),
    })
  },
  syncAllSources(): Promise<{ new_articles: number }> {
    return request<{ new_articles: number }>('/sources/sync', {
      method: 'POST',
    })
  },
  syncSource(sourceId: number): Promise<{ new_articles: number }> {
    return request<{ new_articles: number }>(`/sources/${sourceId}/sync`, {
      method: 'POST',
    })
  },
}
