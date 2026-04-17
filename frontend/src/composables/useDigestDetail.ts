import { shallowRef, watch } from 'vue'

import { api } from '../services/api'
import type { DigestPayload } from '../types'

export function useDigestDetail(digestDate: () => string) {
  const digest = shallowRef<DigestPayload | null>(null)
  const loading = shallowRef(false)
  const errorMessage = shallowRef('')

  async function refreshDetail() {
    const currentDigestDate = digestDate()
    if (!currentDigestDate) {
      return
    }

    loading.value = true
    errorMessage.value = ''
    try {
      digest.value = await api.getDigestByDate(currentDigestDate)
    } catch (error) {
      errorMessage.value = error instanceof Error ? error.message : '日报详情加载失败'
    } finally {
      loading.value = false
    }
  }

  watch(
    digestDate,
    () => {
      void refreshDetail()
    },
    { immediate: true },
  )

  return {
    digest,
    loading,
    errorMessage,
    refreshDetail,
  }
}

