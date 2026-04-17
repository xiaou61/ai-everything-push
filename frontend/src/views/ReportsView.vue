<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'

import EmptyState from '../components/ui/EmptyState.vue'
import PanelCard from '../components/ui/PanelCard.vue'
import StatusBadge from '../components/ui/StatusBadge.vue'
import { api } from '../lib/api'
import { createReportLink, formatDate, formatDateTime } from '../lib/format'
import { useUiStore } from '../stores/ui'
import type { Report } from '../types/admin'

const ui = useUiStore()

const loading = ref(true)
const actionLoading = ref<'report' | 'push' | null>(null)
const reportDate = ref(new Date().toISOString().slice(0, 10))
const reports = ref<Report[]>([])

const reportStats = computed(() => ({
  total: reports.value.length,
  pushed: reports.value.filter((item) => item.feishu_pushed).length,
  published: reports.value.filter((item) => item.status === 'published').length,
}))

async function loadReports() {
  loading.value = true

  try {
    reports.value = await api.getReports()
  } catch (error) {
    ui.notify(error instanceof Error ? error.message : '加载日报失败', 'error')
  } finally {
    loading.value = false
  }
}

async function runReport() {
  actionLoading.value = 'report'

  try {
    await api.runReportJob(reportDate.value)
    ui.notify(`已生成 ${reportDate.value} 的日报`, 'success')
    await loadReports()
  } catch (error) {
    ui.notify(error instanceof Error ? error.message : '生成日报失败', 'error')
  } finally {
    actionLoading.value = null
  }
}

async function runPush(reportDay?: string) {
  actionLoading.value = 'push'

  try {
    await api.runPushJob(reportDay || reportDate.value)
    ui.notify(`已推送 ${(reportDay || reportDate.value)} 的日报`, 'success')
    await loadReports()
  } catch (error) {
    ui.notify(error instanceof Error ? error.message : '飞书推送失败', 'error')
  } finally {
    actionLoading.value = null
  }
}

onMounted(loadReports)
</script>

<template>
  <div class="view-stack">
    <section class="hero-banner">
      <div>
        <p class="hero-banner__eyebrow">Publishing Desk</p>
        <h3>日报生成和公开链接都在这一层收口，适合每天固定时间审一遍再发出去。</h3>
      </div>
      <label class="shell-field shell-field--inline">
        <span>日报日期</span>
        <input v-model="reportDate" class="shell-input" type="date" />
      </label>
    </section>

    <div class="panel-grid panel-grid--metrics">
      <PanelCard eyebrow="总日报数" :title="String(reportStats.total)" accent="copper">
        <p class="muted-copy">已经入库的日报历史。</p>
      </PanelCard>
      <PanelCard eyebrow="已发布" :title="String(reportStats.published)">
        <p class="muted-copy">可对外访问的日报数量。</p>
      </PanelCard>
      <PanelCard eyebrow="已推送飞书" :title="String(reportStats.pushed)">
        <p class="muted-copy">已经发到飞书群的日报数量。</p>
      </PanelCard>
    </div>

    <PanelCard eyebrow="Manual Actions" title="手动发布台">
      <div class="action-matrix">
        <button class="shell-button" :disabled="actionLoading !== null" @click="runReport">
          {{ actionLoading === 'report' ? '生成中...' : '生成日报' }}
        </button>
        <button class="shell-button shell-button--secondary" :disabled="actionLoading !== null" @click="runPush()">
          {{ actionLoading === 'push' ? '推送中...' : '推送飞书' }}
        </button>
      </div>
    </PanelCard>

    <PanelCard eyebrow="History" title="日报历史">
      <div v-if="loading" class="skeleton-block skeleton-block--table" />
      <template v-else-if="reports.length">
        <div class="report-grid">
          <article v-for="item in reports" :key="item.id" class="report-card">
            <div class="report-card__header">
              <div>
                <p class="report-card__date">{{ formatDate(item.report_date) }}</p>
                <h4>{{ item.title }}</h4>
              </div>
              <StatusBadge :label="item.status" />
            </div>

            <p class="muted-copy">{{ item.intro || '每日技术内容汇总' }}</p>

            <div class="report-card__meta">
              <span>{{ item.article_count }} 篇文章</span>
              <span>{{ item.source_count }} 个来源</span>
              <span>{{ item.feishu_pushed ? '已推送' : '未推送' }}</span>
            </div>

            <div class="table-actions">
              <a class="shell-link" :href="createReportLink(item.report_date, item.html_url)" target="_blank" rel="noreferrer">
                打开日报
              </a>
              <button class="shell-link shell-link--button" :disabled="actionLoading !== null" @click="runPush(item.report_date)">
                单独推送
              </button>
              <span class="muted-copy">{{ formatDateTime(item.updated_at) }}</span>
            </div>
          </article>
        </div>
      </template>
      <EmptyState
        v-else
        title="还没有日报记录"
        description="先跑一次日报生成任务，公开页地址和推送状态就会在这里集中展示。"
      />
    </PanelCard>
  </div>
</template>
