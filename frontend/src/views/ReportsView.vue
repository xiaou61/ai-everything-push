<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'

import EmptyState from '../components/ui/EmptyState.vue'
import PanelCard from '../components/ui/PanelCard.vue'
import StatusBadge from '../components/ui/StatusBadge.vue'
import { api } from '../lib/api'
import { createReportLink, formatDate, formatDateTime } from '../lib/format'
import { useUiStore } from '../stores/ui'
import type { Report, ReportDetail, ReportEditorItem } from '../types/admin'

const ui = useUiStore()

const loading = ref(true)
const detailLoading = ref(false)
const actionLoading = ref<'report' | 'push' | 'save' | 'publish' | null>(null)
const reportDate = ref(new Date().toISOString().slice(0, 10))
const reports = ref<Report[]>([])
const selectedReportId = ref<number | null>(null)
const selectedReport = ref<ReportDetail | null>(null)
const editor = ref({
  title: '',
  intro: '',
  items: [] as ReportEditorItem[],
})

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

function applyEditor(report: ReportDetail) {
  selectedReport.value = report
  selectedReportId.value = report.id
  editor.value = {
    title: report.title,
    intro: report.intro || '',
    items: report.items.map((item) => ({ ...item })),
  }
}

async function loadReportDetail(reportId: number) {
  detailLoading.value = true

  try {
    const report = await api.getReport(reportId)
    applyEditor(report)
  } catch (error) {
    ui.notify(error instanceof Error ? error.message : '加载日报详情失败', 'error')
  } finally {
    detailLoading.value = false
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

function moveItem(index: number, direction: -1 | 1) {
  const targetIndex = index + direction
  if (targetIndex < 0 || targetIndex >= editor.value.items.length) {
    return
  }

  const nextItems = [...editor.value.items]
  const [current] = nextItems.splice(index, 1)
  nextItems.splice(targetIndex, 0, current)
  editor.value.items = nextItems
}

function removeItem(index: number) {
  editor.value.items = editor.value.items.filter((_, currentIndex) => currentIndex !== index)
}

async function saveReport() {
  if (!selectedReport.value) {
    return
  }

  actionLoading.value = 'save'

  try {
    const updated = await api.updateReport(selectedReport.value.id, {
      title: editor.value.title,
      intro: editor.value.intro || null,
      items: editor.value.items.map((item, index) => ({
        id: item.id,
        display_order: index + 1,
        section_name: item.section_name,
      })),
    })
    applyEditor(updated)
    await loadReports()
    ui.notify('日报改动已保存', 'success')
  } catch (error) {
    ui.notify(error instanceof Error ? error.message : '保存日报失败', 'error')
  } finally {
    actionLoading.value = null
  }
}

async function publishSelectedReport() {
  if (!selectedReport.value) {
    return
  }

  actionLoading.value = 'publish'

  try {
    const result = await api.publishReport(selectedReport.value.id)
    applyEditor(result.report)
    await loadReports()
    ui.notify(result.message, 'success')
  } catch (error) {
    ui.notify(error instanceof Error ? error.message : '重新发布日报失败', 'error')
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

    <div class="report-workspace">
      <PanelCard eyebrow="History" title="日报历史">
        <div v-if="loading" class="skeleton-block skeleton-block--table" />
        <template v-else-if="reports.length">
          <div class="report-stack">
            <article
              v-for="item in reports"
              :key="item.id"
              class="report-card"
              :class="{ 'is-active': selectedReportId === item.id }"
            >
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
                <button class="shell-link shell-link--button" @click="loadReportDetail(item.id)">
                  {{ selectedReportId === item.id ? '编辑中' : '编辑日报' }}
                </button>
                <a class="shell-link" :href="createReportLink(item.report_date, item.html_url)" target="_blank" rel="noreferrer">
                  打开日报
                </a>
                <button class="shell-link shell-link--button" :disabled="actionLoading !== null" @click="runPush(item.report_date)">
                  单独推送
                </button>
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

      <PanelCard eyebrow="Editor" title="日报编辑器" accent="ink">
        <div v-if="detailLoading" class="skeleton-block skeleton-block--table" />
        <template v-else-if="selectedReport">
          <div class="editor-shell">
            <div class="shell-form__grid">
              <label class="shell-field shell-field--full">
                <span>日报标题</span>
                <input v-model="editor.title" class="shell-input" type="text" maxlength="255" />
              </label>

              <label class="shell-field shell-field--full">
                <span>日报导语</span>
                <textarea v-model="editor.intro" class="shell-textarea" rows="4" maxlength="2000" />
              </label>
            </div>

            <div class="editor-meta">
              <span>{{ selectedReport.report_date }}</span>
              <span>{{ editor.items.length }} 篇条目</span>
              <span>{{ selectedReport.feishu_pushed ? '已推送飞书' : '未推送飞书' }}</span>
              <span>{{ formatDateTime(selectedReport.updated_at) }}</span>
            </div>

            <div class="editor-items">
              <article v-for="(item, index) in editor.items" :key="item.id" class="editor-item">
                <div class="editor-item__head">
                  <div>
                    <p class="article-card__source">{{ item.source_name }}</p>
                    <h4>{{ item.generated_title || item.article_title }}</h4>
                  </div>
                  <div class="editor-item__controls">
                    <button class="shell-link shell-link--button" :disabled="index === 0" @click="moveItem(index, -1)">上移</button>
                    <button
                      class="shell-link shell-link--button"
                      :disabled="index === editor.items.length - 1"
                      @click="moveItem(index, 1)"
                    >
                      下移
                    </button>
                    <button class="shell-link shell-link--button shell-link--danger" @click="removeItem(index)">移除</button>
                  </div>
                </div>

                <label class="shell-field">
                  <span>分组名</span>
                  <input v-model="item.section_name" class="shell-input" type="text" maxlength="100" />
                </label>

                <p class="muted-copy">{{ item.summary || '暂无摘要内容。' }}</p>

                <div class="article-card__meta">
                  <span>{{ item.category || '未分类' }}</span>
                  <a :href="item.canonical_url" target="_blank" rel="noreferrer" class="shell-link">查看原文</a>
                </div>
              </article>
            </div>

            <div class="form-actions">
              <button class="shell-button" :disabled="actionLoading !== null" @click="saveReport">
                {{ actionLoading === 'save' ? '保存中...' : '保存改动' }}
              </button>
              <button class="shell-button shell-button--secondary" :disabled="actionLoading !== null" @click="publishSelectedReport">
                {{ actionLoading === 'publish' ? '发布中...' : '重新发布' }}
              </button>
              <button class="shell-button shell-button--ghost" :disabled="actionLoading !== null" @click="runPush(selectedReport.report_date)">
                {{ actionLoading === 'push' ? '推送中...' : '推送飞书' }}
              </button>
              <a class="shell-link" :href="createReportLink(selectedReport.report_date, selectedReport.html_url)" target="_blank" rel="noreferrer">
                查看当前公开页
              </a>
            </div>
          </div>
        </template>
        <EmptyState
          v-else
          title="还没有选中日报"
          description="从左侧历史列表点开一份日报，就可以直接改标题、导语、分组和条目顺序。"
        />
      </PanelCard>
    </div>
  </div>
</template>
