import { computed, onMounted, shallowRef } from 'vue'

import { api } from '../services/api'
import type { SourceDraft, SourcePayload } from '../types'

const defaultSourceDraft: SourceDraft = {
  name: '',
  url: '',
  source_type: 'rss',
  category_hint: '',
  parser_config: {},
  enabled: true,
  fetch_limit: 20,
}

export function useSources() {
  const sources = shallowRef<SourcePayload[]>([])
  const loading = shallowRef(false)
  const errorMessage = shallowRef('')
  const actionMessage = shallowRef('')

  const initialDraft = computed<SourceDraft>(() => ({
    ...defaultSourceDraft,
    parser_config: { ...defaultSourceDraft.parser_config },
  }))

  async function refreshSources() {
    loading.value = true
    errorMessage.value = ''
    try {
      sources.value = await api.getSources()
    } catch (error) {
      errorMessage.value = error instanceof Error ? error.message : '数据源加载失败'
    } finally {
      loading.value = false
    }
  }

  async function createSource(payload: SourceDraft) {
    actionMessage.value = ''
    try {
      await api.createSource(payload)
      actionMessage.value = '数据源已创建'
      await refreshSources()
    } catch (error) {
      actionMessage.value = error instanceof Error ? error.message : '创建数据源失败'
    }
  }

  async function syncAllSources() {
    actionMessage.value = ''
    try {
      const result = await api.syncAllSources()
      actionMessage.value = `本次新增 ${result.new_articles} 条内容`
      await refreshSources()
    } catch (error) {
      actionMessage.value = error instanceof Error ? error.message : '同步全部数据源失败'
    }
  }

  async function syncSingleSource(sourceId: number) {
    actionMessage.value = ''
    try {
      const result = await api.syncSource(sourceId)
      actionMessage.value = `数据源 ${sourceId} 本次新增 ${result.new_articles} 条内容`
      await refreshSources()
    } catch (error) {
      actionMessage.value = error instanceof Error ? error.message : '同步数据源失败'
    }
  }

  onMounted(() => {
    void refreshSources()
  })

  return {
    sources,
    loading,
    errorMessage,
    actionMessage,
    initialDraft,
    refreshSources,
    createSource,
    syncAllSources,
    syncSingleSource,
  }
}
