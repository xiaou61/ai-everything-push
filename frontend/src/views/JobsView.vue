<script setup lang="ts">
import { onMounted, ref } from 'vue'

import EmptyState from '../components/ui/EmptyState.vue'
import PanelCard from '../components/ui/PanelCard.vue'
import StatusBadge from '../components/ui/StatusBadge.vue'
import { api } from '../lib/api'
import { formatDateTime } from '../lib/format'
import { useUiStore } from '../stores/ui'
import type { JobRun, SchedulerStatus } from '../types/admin'

const ui = useUiStore()

const loading = ref(true)
const actionLoading = ref<string | null>(null)
const reportDate = ref(new Date().toISOString().slice(0, 10))
const jobs = ref<JobRun[]>([])
const scheduler = ref<SchedulerStatus | null>(null)

async function loadJobs() {
  loading.value = true

  try {
    const [jobList, schedulerStatus] = await Promise.all([api.getJobs(), api.getSchedulerStatus()])
    jobs.value = jobList
    scheduler.value = schedulerStatus
  } catch (error) {
    ui.notify(error instanceof Error ? error.message : '加载任务日志失败', 'error')
  } finally {
    loading.value = false
  }
}

async function runAction(kind: 'crawl' | 'process' | 'report' | 'push') {
  actionLoading.value = kind

  try {
    if (kind === 'crawl') {
      await api.runCrawlJob()
    } else if (kind === 'process') {
      await api.runProcessJob()
    } else if (kind === 'report') {
      await api.runReportJob(reportDate.value)
    } else {
      await api.runPushJob(reportDate.value)
    }

    ui.notify(`任务 ${kind} 已执行`, 'success')
    await loadJobs()
  } catch (error) {
    ui.notify(error instanceof Error ? error.message : '执行任务失败', 'error')
  } finally {
    actionLoading.value = null
  }
}

onMounted(loadJobs)
</script>

<template>
  <div class="view-stack">
    <section class="hero-banner">
      <div>
        <p class="hero-banner__eyebrow">Runbook</p>
        <h3>任务日志页更适合排障，能同时看到手动触发和自动调度的运行结果。</h3>
      </div>
      <label class="shell-field shell-field--inline">
        <span>报告日期</span>
        <input v-model="reportDate" class="shell-input" type="date" />
      </label>
    </section>

    <div class="panel-grid panel-grid--two">
      <PanelCard eyebrow="Runner" title="手动触发任务" accent="copper">
        <div class="action-matrix">
          <button class="shell-button" :disabled="actionLoading !== null" @click="runAction('crawl')">
            {{ actionLoading === 'crawl' ? '执行中...' : '抓取' }}
          </button>
          <button class="shell-button shell-button--secondary" :disabled="actionLoading !== null" @click="runAction('process')">
            {{ actionLoading === 'process' ? '执行中...' : '处理' }}
          </button>
          <button class="shell-button shell-button--secondary" :disabled="actionLoading !== null" @click="runAction('report')">
            {{ actionLoading === 'report' ? '执行中...' : '生成日报' }}
          </button>
          <button class="shell-button shell-button--ghost" :disabled="actionLoading !== null" @click="runAction('push')">
            {{ actionLoading === 'push' ? '执行中...' : '推送飞书' }}
          </button>
        </div>
      </PanelCard>

      <PanelCard eyebrow="Scheduler" title="调度器状态" accent="ink">
        <template v-if="scheduler">
          <div class="status-list">
            <div class="status-list__item">
              <span>是否可用</span>
              <StatusBadge :label="scheduler.available ? 'enabled' : 'disabled'" />
            </div>
            <div class="status-list__item">
              <span>是否运行</span>
              <StatusBadge :label="scheduler.running ? 'running' : 'stopped'" />
            </div>
            <div class="status-list__item">
              <span>任务数</span>
              <strong>{{ scheduler.jobs.length }}</strong>
            </div>
          </div>
          <p class="muted-copy">{{ scheduler.message }}</p>
        </template>
      </PanelCard>
    </div>

    <PanelCard eyebrow="Logs" title="执行记录">
      <div v-if="loading" class="skeleton-block skeleton-block--table" />
      <template v-else-if="jobs.length">
        <div class="table-scroll">
          <table class="shell-table">
            <thead>
              <tr>
                <th>任务名</th>
                <th>状态</th>
                <th>触发方式</th>
                <th>开始</th>
                <th>完成</th>
                <th>处理数量</th>
                <th>错误信息</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="item in jobs" :key="item.id">
                <td>{{ item.job_name }}</td>
                <td><StatusBadge :label="item.status" /></td>
                <td>{{ item.trigger_type }}</td>
                <td>{{ formatDateTime(item.started_at) }}</td>
                <td>{{ formatDateTime(item.finished_at) }}</td>
                <td>{{ item.processed_count }}</td>
                <td>{{ item.error_message || '-' }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </template>
      <EmptyState
        v-else
        title="暂无任务日志"
        description="先跑一次抓取或报告任务，这里就会出现完整执行轨迹。"
      />
    </PanelCard>
  </div>
</template>
