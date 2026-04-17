export function formatDateTime(value: string | null | undefined): string {
  if (!value) {
    return '-'
  }

  return new Intl.DateTimeFormat('zh-CN', {
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  }).format(new Date(value))
}

export function formatDate(value: string | null | undefined): string {
  if (!value) {
    return '-'
  }

  return new Intl.DateTimeFormat('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
  }).format(new Date(value))
}

export function formatBoolean(value: boolean): string {
  return value ? '是' : '否'
}

export function formatTaskType(value: string): string {
  const labelMap: Record<string, string> = {
    translation: '翻译',
    summary: '摘要',
    classification: '分类',
    title: '标题',
  }

  return labelMap[value] ?? value
}

export function createReportLink(reportDate: string, htmlUrl?: string | null): string {
  return htmlUrl || `/daily/${reportDate}`
}
