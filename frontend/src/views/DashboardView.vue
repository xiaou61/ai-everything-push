<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'

import EmptyState from '../components/ui/EmptyState.vue'
import PanelCard from '../components/ui/PanelCard.vue'
import StatusBadge from '../components/ui/StatusBadge.vue'
import { api } from '../lib/api'
import { formatDateTime } from '../lib/format'
import { useUiStore } from '../stores/ui'
import type { DashboardResponse } from '../types/admin'

const ui = useUiStore()

const dashboard = ref<DashboardResponse | null>(null)
const loading = ref(true)
const actionLoading = ref<string | null>(null)
const starterLoading = ref(false)
const reportDate = ref(new Date().toISOString().slice(0, 10))

const statCards = computed(() => {
  if (!dashboard.value) {
    return []
  }

  return [
    {
      label: '内容源',
      value: dashboard.value.stats.source_count,
      detail: `${dashboard.value.stats.enabled_source_count} 个启用中`,
    },
    {
      label: '文章池',
      value: dashboard.value.stats.article_count,
      detail: '待翻译与待总结内容都在这里汇总',
    },
    {
      label: '日报',
      value: dashboard.value.stats.report_count,
      detail: '含已发布的可访问日报页面',
    },
    {
      label: '模型',
      value: dashboard.value.stats.model_count,
      detail: `${dashboard.value.stats.job_count} 条任务执行记录`,
    },
  ]
})

const healthCards = computed(() => {
  if (!dashboard.value) {
    return []
  }

  return [
    { key: 'healthy', label: '健康', count: dashboard.value.source_health_summary.healthy, tone: 'success' },
    { key: 'warning', label: '待重试', count: dashboard.value.source_health_summary.warning, tone: 'warning' },
    { key: 'cooling', label: '冷却中', count: dashboard.value.source_health_summary.cooling, tone: 'info' },
    { key: 'failed', label: '失败', count: dashboard.value.source_health_summary.failed, tone: 'danger' },
    { key: 'idle', label: '未抓取', count: dashboard.value.source_health_summary.idle, tone: 'info' },
  ]
})

async function loadDashboard() {
  loading.value = true

  try {
    dashboard.value = await api.getDashboard()
  } catch (error) {
    ui.notify(error instanceof Error ? error.message : '加载仪表盘失败', 'error')
  } finally {
    loading.value = false
  }
}

async function runJob(kind: 'crawl' | 'process' | 'report' | 'push') {
  actionLoading.value = kind

  try {
    if (kind === 'crawl') {
      const result = await api.runCrawlJob()
      const skipped = typeof result.skipped_count === 'number' ? result.skipped_count : 0
      ui.notify(skipped > 0 ? `抓取任务已执行，跳过 ${skipped} 个冷却来源` : '抓取任务已执行', 'success')
    } else if (kind === 'process') {
      await api.runProcessJob()
      ui.notify('处理任务已执行', 'success')
    } else if (kind === 'report') {
      await api.runReportJob(reportDate.value)
      ui.notify(`已生成 ${reportDate.value} 的日报`, 'success')
    } else {
      await api.runPushJob(reportDate.value)
      ui.notify(`已推送 ${reportDate.value} 的日报到飞书`, 'success')
    }

    await loadDashboard()
  } catch (error) {
    ui.notify(error instanceof Error ? error.message : '任务执行失败', 'error')
  } finally {
    actionLoading.value = null
  }
}

async function applyStarterPack() {
  starterLoading.value = true

  try {
    const result = await api.applyStarterPresets()

    ui.notify(
      `已注入 ${result.created_sources.length} 个来源、${result.created_models.length} 个模型预设`,
      'success',
    )
    await loadDashboard()
  } catch (error) {
    ui.notify(error instanceof Error ? error.message : '注入 starter 预设失败', 'error')
  } finally {
    starterLoading.value = false
  }
}

onMounted(loadDashboard)
</script>

<template>
  <div class="view-stack">
    <section class="hero-banner">
      <div>
        <p class="hero-banner__eyebrow">Morning Pulse</p>
        <h3>技术论坛日报已经具备自动运行的骨架，剩下的是把每个环节打磨顺。</h3>
        <div v-if="dashboard" class="hero-inline">
          <span class="meta-pill">异常来源 {{ dashboard.source_alerts.abnormal_count }}</span>
          <span class="meta-pill">冷却中 {{ dashboard.source_alerts.cooling_count }}</span>
          <span class="meta-pill">已失败 {{ dashboard.source_alerts.failed_count }}</span>
        </div>
      </div>
      <div class="hero-banner__meta">
        <label class="shell-field">
          <span>任务日期</span>
          <input v-model="reportDate" class="shell-input" type="date" />
        </label>
      </div>
    </section>

    <div v-if="loading" class="panel-grid panel-grid--metrics">
      <PanelCard v-for="item in 4" :key="item" eyebrow="Loading" title="数据加载中">
        <div class="skeleton-block skeleton-block--tall" />
      </PanelCard>
    </div>

    <template v-else-if="dashboard">
      <div class="panel-grid panel-grid--metrics">
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
        <PanelCard eyebrow="Source Health" title="来源健康雷达" accent="copper">
          <div class="signal-grid">
            <article v-for="item in healthCards" :key="item.key" class="signal-card" :data-tone="item.tone">
              <span>{{ item.label }}</span>
              <strong>{{ item.count }}</strong>
            </article>
          </div>
          <p class="muted-copy">冷却中的来源会暂时跳过抓取，避免在异常窗口内反复打源站。</p>
        </PanelCard>

        <PanelCard eyebrow="Alerts" title="异常来源提醒" accent="ink">
          <template v-if="dashboard.source_alerts.recent_failures.length">
            <div class="source-alert-list">
              <article
                v-for="item in dashboard.source_alerts.recent_failures"
                :key="item.id"
                class="source-alert-item"
              >
                <div class="source-alert-item__meta">
                  <strong>{{ item.name }}</strong>
                  <span>{{ item.category || item.slug }}</span>
                </div>
                <StatusBadge :label="item.health_label" />
                <span class="table-subcopy">失败时间 {{ formatDateTime(item.last_failure_at) }}</span>
                <span v-if="item.can_retry_now" class="table-ready">已到重试窗口</span>
                <span v-if="item.last_crawl_error" class="table-error">{{ item.last_crawl_error }}</span>
              </article>
            </div>
          </template>
          <EmptyState
            v-else
            title="来源状态稳定"
            description="当前没有需要优先处理的异常来源，可以继续关注文章处理与日报编排。"
          />
        </PanelCard>
      </div>

      <div class="panel-grid panel-grid--two">
        <PanelCard eyebrow="Actions" title="手动任务台">
          <div class="action-matrix">
            <button class="shell-button" :disabled="actionLoading !== null" @click="runJob('crawl')">
              {{ actionLoading === 'crawl' ? '抓取中...' : '立即抓取' }}
            </button>
            <button class="shell-button shell-button--secondary" :disabled="actionLoading !== null" @click="runJob('process')">
              {{ actionLoading === 'process' ? '处理中...' : '处理文章' }}
            </button>
            <button class="shell-button shell-button--secondary" :disabled="actionLoading !== null" @click="runJob('report')">
              {{ actionLoading === 'report' ? '生成中...' : '生成日报' }}
            </button>
            <button class="shell-button shell-button--ghost" :disabled="actionLoading !== null" @click="runJob('push')">
              {{ actionLoading === 'push' ? '推送中...' : '推送飞书' }}
            </button>
          </div>
        </PanelCard>

        <PanelCard eyebrow="Scheduler" title="自动调度状态" accent="ink">
          <div class="status-list">
            <div class="status-list__item">
              <span>运行状态</span>
              <StatusBadge :label="dashboard.scheduler_status.running ? 'running' : 'stopped'" />
            </div>
            <div class="status-list__item">
              <span>启用配置</span>
              <StatusBadge :label="dashboard.scheduler_status.enabled ? 'enabled' : 'disabled'" />
            </div>
            <div class="status-list__item">
              <span>任务数量</span>
              <strong>{{ dashboard.scheduler_status.jobs.length }}</strong>
            </div>
          </div>
          <p class="muted-copy">{{ dashboard.scheduler_status.message || '调度器正在等待下一轮执行。' }}</p>
        </PanelCard>
      </div>

      <PanelCard eyebrow="Starter Pack" title="推荐起步配置">
        <div class="starter-layout">
          <div class="starter-column">
            <h4>推荐来源</h4>
            <div class="starter-tags">
              <span
                v-for="item in dashboard.starter.sources"
                :key="item.slug"
                class="starter-tag"
                :data-ready="item.exists"
              >
                {{ item.name }}
              </span>
            </div>
          </div>

          <div class="starter-column">
            <h4>默认模型</h4>
            <div class="starter-tags">
              <span
                v-for="item in dashboard.starter.models"
                :key="item.task_type"
                class="starter-tag"
                :data-ready="item.exists"
              >
                {{ item.task_type }}
              </span>
            </div>
          </div>
        </div>

        <div class="form-actions">
          <button
            class="shell-button shell-button--secondary"
            :disabled="
              starterLoading ||
              (dashboard.starter.missing_source_count === 0 && dashboard.starter.missing_model_count === 0)
            "
            @click="applyStarterPack"
          >
            {{
              starterLoading
                ? '注入中...'
                : dashboard.starter.missing_source_count === 0 && dashboard.starter.missing_model_count === 0
                  ? 'Starter 已齐全'
                  : '一键注入推荐配置'
            }}
          </button>
        </div>
      </PanelCard>

      <PanelCard eyebrow="Recent Runs" title="最近任务">
        <template v-if="dashboard.recent_jobs.length">
          <div class="table-scroll">
            <table class="shell-table">
              <thead>
                <tr>
                  <th>任务</th>
                  <th>状态</th>
                  <th>触发方式</th>
                  <th>开始时间</th>
                  <th>完成时间</th>
                  <th>处理数量</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="item in dashboard.recent_jobs" :key="item.id">
                  <td>{{ item.job_name }}</td>
                  <td><StatusBadge :label="item.status" /></td>
                  <td>{{ item.trigger_type }}</td>
                  <td>{{ formatDateTime(item.started_at) }}</td>
                  <td>{{ formatDateTime(item.finished_at) }}</td>
                  <td>{{ item.processed_count }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </template>
        <EmptyState
          v-else
          title="还没有任务记录"
          description="先执行一次抓取或处理任务，这里就会开始累积运行历史。"
        />
      </PanelCard>
    </template>
  </div>
</template>
