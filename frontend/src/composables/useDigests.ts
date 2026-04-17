import { computed, onMounted, shallowRef } from 'vue'

import { api } from '../services/api'
import type { DigestPayload } from '../types'

export function useDigests() {
  const digests = shallowRef<DigestPayload[]>([])
  const loading = shallowRef(false)
  const errorMessage = shallowRef('')
  const actionMessage = shallowRef('')

  const latestDigest = computed(() => digests.value[0] ?? null)

  async function refreshDigests() {
    loading.value = true
    errorMessage.value = ''
    try {
      digests.value = await api.getDigests()
    } catch (error) {
      errorMessage.value = error instanceof Error ? error.message : '日报加载失败'
    } finally {
      loading.value = false
    }
  }

  async function generateTodayDigest() {
    actionMessage.value = ''
    try {
      const digest = await api.generateDigest()
      actionMessage.value = `已生成 ${digest.digest_date} 日报`
      await refreshDigests()
    } catch (error) {
      actionMessage.value = error instanceof Error ? error.message : '日报生成失败'
    }
  }

  async function pushDigest(digestId: number) {
    actionMessage.value = ''
    try {
      const digest = await api.pushDigest(digestId)
      actionMessage.value = `${digest.digest_date} 日报已推送到飞书`
      await refreshDigests()
    } catch (error) {
      actionMessage.value = error instanceof Error ? error.message : '日报推送失败'
    }
  }

  onMounted(() => {
    void refreshDigests()
  })

  return {
    digests,
    latestDigest,
    loading,
    errorMessage,
    actionMessage,
    refreshDigests,
    generateTodayDigest,
    pushDigest,
  }
}

