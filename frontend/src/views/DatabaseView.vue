<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'

import EmptyState from '../components/ui/EmptyState.vue'
import PanelCard from '../components/ui/PanelCard.vue'
import { api } from '../lib/api'
import { createReportLink, formatDate, formatDateTime } from '../lib/format'
import { useUiStore } from '../stores/ui'
import type { DatabaseOverview, Report } from '../types/admin'

const ui = useUiStore()

const loading = ref(true)
const overview = ref<DatabaseOverview | null>(null)
const reports = ref<Report[]>([])
const cleanupDays = ref(14)
const actionLoading = ref<'jobs' | 'failed' | number | null>(null)

const statCards = computed(() => {
  if (!overview.value) {
    return []
  }

  return [
    {
      label: '总行数',
      value: overview.value.metrics.total_rows,
      detail: '当前各核心表记录总量。',
    },
    {
      label: '文章库',
      value: overview.value.metrics.article_count,
      detail: `${overview.value.metrics.failed_articles} 篇需要清理或重抓`,
    },
    {
      label: '日报数',
      value: overview.value.metrics.report_count,
      detail: '含公开页元数据和历史记录。',
    },
    {
      label: '任务日志',
      value: overview.value.metrics.job_run_count,
      detail: '调度和手动运行的执行轨迹。',
    },
  ]
})

const recentReports = computed(() => reports.value.slice(0, 6))

async function loadData() {
  loading.value = true

  try {
    const [databaseOverview, reportList] = await Promise.all([api.getDatabaseOverview(), api.getReports()])
    overview.value = databaseOverview
    reports.value = reportList
  } catch (error) {
    ui.notify(error instanceof Error ? error.message : '加载数据维护页面失败', 'error')
  } finally {
    loading.value = false
  }
}

async function runJobCleanup() {
  actionLoading.value = 'jobs'

  try {
    const result = await api.cleanupOldJobs(cleanupDays.value)
    ui.notify(result.message, 'success')
    await loadData()
  } catch (error) {
    ui.notify(error instanceof Error ? error.message : '清理任务日志失败', 'error')
  } finally {
    actionLoading.value = null
  }
}

async function runFailedArticleCleanup() {
  actionLoading.value = 'failed'

  try {
    const result = await api.cleanupFailedArticles()
    ui.notify(result.message, 'success')
    await loadData()
  } catch (error) {
    ui.notify(error instanceof Error ? error.message : '清理失败文章失败', 'error')
  } finally {
    actionLoading.value = null
  }
}

async function removeReport(report: Report) {
  if (!window.confirm(`确认删除 ${report.report_date} 的日报记录吗？对应公开 HTML 也会一起删掉。`)) {
    return
  }

  actionLoading.value = report.id

  try {
    const result = await api.deleteReport(report.id)
    ui.notify(result.message, 'success')
    await loadData()
  } catch (error) {
    ui.notify(error instanceof Error ? error.message : '删除日报失败', 'error')
  } finally {
    actionLoading.value = null
  }
}

onMounted(loadData)
</script>

<template>
  <div class="view-stack">
    <section class="hero-banner">
      <div>
        <p class="hero-banner__eyebrow">Data Maintenance</p>
        <h3>这里负责给数据库做体检和瘦身，适合本地长期跑任务后定期维护。</h3>
      </div>
      <div v-if="overview" class="hero-inline">
        <span class="meta-pill">{{ overview.connection.dialect }}</span>
        <span class="meta-pill">{{ overview.connection.database }}</span>
      </div>
    </section>

    <div v-if="loading" class="panel-grid panel-grid--metrics">
      <PanelCard v-for="item in 4" :key="item" eyebrow="Loading" title="数据加载中">
        <div class="skeleton-block skeleton-block--tall" />
      </PanelCard>
    </div>

    <template v-else-if="overview">
      <div class="panel-grid panel-grid--metrics panel-grid--metrics-4">
        <PanelCard
          v-for="item in statCards"
          :key="item.label"
          :eyebrow="item.label"
          :title="String(item.value)"
          accent="copper"
        >
          <p class="muted-copy">{{ item.detail }}</p>
        </PanelCard>
      </div>

      <div class="panel-grid panel-grid--two">
        <PanelCard eyebrow="Connection" title="数据库连接">
          <div class="info-grid">
            <div class="info-item">
              <span>驱动</span>
              <strong>{{ overview.connection.driver }}</strong>
            </div>
            <div class="info-item">
              <span>数据库</span>
              <strong>{{ overview.connection.database }}</strong>
            </div>
            <div class="info-item info-item--full">
              <span>连接串</span>
              <code>{{ overview.connection.masked_url }}</code>
            </div>
          </div>
        </PanelCard>

        <PanelCard eyebrow="Recent" title="最近活动" accent="ink">
          <div class="status-list">
            <div class="status-list__item">
              <span>最新日报</span>
              <strong>{{ formatDate(overview.recent.latest_report_date) }}</strong>
            </div>
            <div class="status-list__item">
              <span>最新文章入库</span>
              <strong>{{ formatDateTime(overview.recent.latest_article_created_at) }}</strong>
            </div>
            <div class="status-list__item">
              <span>最新任务运行</span>
              <strong>{{ formatDateTime(overview.recent.latest_job_started_at) }}</strong>
            </div>
          </div>
        </PanelCard>
      </div>

      <PanelCard eyebrow="Tables" title="核心表概览">
        <div class="data-table-grid">
          <article v-for="item in overview.tables" :key="item.key" class="data-table-card">
            <p class="data-table-card__label">{{ item.label }}</p>
            <h4>{{ item.count }}</h4>
            <p class="muted-copy">{{ item.description }}</p>
            <small>最近变更：{{ formatDateTime(item.last_updated_at) }}</small>
          </article>
        </div>
      </PanelCard>

      <div class="panel-grid panel-grid--two">
        <PanelCard eyebrow="Breakdown" title="状态分布">
          <div class="breakdown-grid">
            <div class="breakdown-column">
              <h4>文章处理状态</h4>
              <div class="breakdown-list">
                <div v-for="item in overview.article_status_breakdown" :key="item.key" class="breakdown-item">
                  <span>{{ item.label }}</span>
                  <strong>{{ item.count }}</strong>
                </div>
              </div>
            </div>

            <div class="breakdown-column">
              <h4>来源抓取健康</h4>
              <div class="breakdown-list">
                <div v-for="item in overview.source_health_breakdown" :key="item.key" class="breakdown-item">
                  <span>{{ item.label }}</span>
                  <strong>{{ item.count }}</strong>
                </div>
              </div>
            </div>
          </div>
        </PanelCard>

        <PanelCard eyebrow="Maintenance" title="清理动作" accent="copper">
          <div class="maintenance-stack">
            <div class="maintenance-card">
              <div class="maintenance-card__head">
                <div>
                  <h4>清理旧任务日志</h4>
                  <p class="muted-copy">保留最近一段时间的运行记录，避免日志越积越多。</p>
                </div>
                <label class="shell-field shell-field--inline">
                  <span>保留天数</span>
                  <input v-model.number="cleanupDays" class="shell-input" type="number" min="0" max="3650" />
                </label>
              </div>
              <button class="shell-button shell-button--secondary" :disabled="actionLoading !== null" @click="runJobCleanup">
                {{ actionLoading === 'jobs' ? '清理中...' : '执行清理' }}
              </button>
            </div>

            <div class="maintenance-card maintenance-card--danger">
              <div class="maintenance-card__head">
                <div>
                  <h4>清理失败文章</h4>
                  <p class="muted-copy">删除 AI 处理失败或抓取失败的文章，并同步移除关联正文和日报条目。</p>
                </div>
              </div>
              <button class="shell-button shell-button--ghost" :disabled="actionLoading !== null" @click="runFailedArticleCleanup">
                {{ actionLoading === 'failed' ? '清理中...' : '清理失败文章' }}
              </button>
            </div>
          </div>
        </PanelCard>
      </div>

      <PanelCard eyebrow="Report Cleanup" title="日报记录维护">
        <template v-if="recentReports.length">
          <div class="report-grid">
            <article v-for="item in recentReports" :key="item.id" class="report-card">
              <div class="report-card__header">
                <div>
                  <p class="report-card__date">{{ formatDate(item.report_date) }}</p>
                  <h4>{{ item.title }}</h4>
                </div>
              </div>

              <p class="muted-copy">{{ item.intro || '每日技术内容汇总' }}</p>

              <div class="report-card__meta">
                <span>{{ item.article_count }} 篇文章</span>
                <span>{{ item.source_count }} 个来源</span>
                <span>{{ item.status }}</span>
              </div>

              <div class="table-actions">
                <a class="shell-link" :href="createReportLink(item.report_date, item.html_url)" target="_blank" rel="noreferrer">
                  打开日报
                </a>
                <button
                  class="shell-link shell-link--button shell-link--danger"
                  :disabled="actionLoading !== null"
                  @click="removeReport(item)"
                >
                  {{ actionLoading === item.id ? '删除中...' : '删除日报' }}
                </button>
              </div>
            </article>
          </div>
        </template>
        <EmptyState
          v-else
          title="还没有日报记录"
          description="等生成出日报后，这里就可以直接做历史记录和 HTML 页面清理。"
        />
      </PanelCard>
    </template>
  </div>
</template>
