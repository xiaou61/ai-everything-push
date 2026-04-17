import { shallowRef, watch } from 'vue'

import { api } from '../services/api'
import type { ArticleDetailPayload } from '../types'

export function useArticleDetail(selectedArticleId: () => number | null) {
  const article = shallowRef<ArticleDetailPayload | null>(null)
  const loading = shallowRef(false)
  const errorMessage = shallowRef('')
  let latestRequestId = 0

  async function refreshArticle() {
    const articleId = selectedArticleId()
    if (!articleId) {
      article.value = null
      errorMessage.value = ''
      loading.value = false
      return
    }

    const requestId = latestRequestId + 1
    latestRequestId = requestId
    article.value = null
    loading.value = true
    errorMessage.value = ''
    try {
      const response = await api.getArticleById(articleId)
      if (requestId !== latestRequestId) {
        return
      }
      article.value = response
    } catch (error) {
      if (requestId !== latestRequestId) {
        return
      }
      article.value = null
      errorMessage.value = error instanceof Error ? error.message : '文章详情加载失败'
    } finally {
      if (requestId === latestRequestId) {
        loading.value = false
      }
    }
  }

  watch(
    selectedArticleId,
    () => {
      void refreshArticle()
    },
    { immediate: true },
  )

  return {
    article,
    loading,
    errorMessage,
    refreshArticle,
  }
}
