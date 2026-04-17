import { onMounted, shallowRef } from 'vue'

import { api } from '../services/api'
import type { DashboardPayload } from '../types'

export function useDashboard() {
  const dashboard = shallowRef<DashboardPayload | null>(null)
  const loading = shallowRef(false)
  const errorMessage = shallowRef('')

  async function refreshDashboard() {
    loading.value = true
    errorMessage.value = ''
    try {
      dashboard.value = await api.getDashboard()
    } catch (error) {
      errorMessage.value = error instanceof Error ? error.message : '仪表盘加载失败'
    } finally {
      loading.value = false
    }
  }

  onMounted(() => {
    void refreshDashboard()
  })

  return {
    dashboard,
    loading,
    errorMessage,
    refreshDashboard,
  }
}

