<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { RouterLink } from 'vue-router'

import EmptyState from '../components/ui/EmptyState.vue'
import PanelCard from '../components/ui/PanelCard.vue'
import StatusBadge from '../components/ui/StatusBadge.vue'
import { api } from '../lib/api'
import { formatBoolean, formatDateTime } from '../lib/format'
import { useUiStore } from '../stores/ui'
import type { Source } from '../types/admin'

const ui = useUiStore()

const loading = ref(true)
const search = ref('')
const healthFilter = ref<'all' | 'healthy' | 'abnormal' | 'cooling'>('all')
const sources = ref<Source[]>([])
const togglingId = ref<number | null>(null)

const filterOptions = [
  { value: 'all', label: '全部来源' },
  { value: 'healthy', label: '健康' },
  { value: 'abnormal', label: '异常' },
  { value: 'cooling', label: '冷却中' },
] as const

const filteredSources = computed(() => {
  const keyword = search.value.trim().toLowerCase()

  return sources.value.filter((item) => {
    const matchesKeyword =
      !keyword ||
      [item.name, item.slug, item.category || '', item.language_hint || '', item.site_url]
        .join(' ')
        .toLowerCase()
        .includes(keyword)

    if (!matchesKeyword) {
      return false
    }

    if (healthFilter.value === 'healthy') {
      return item.health_level === 'healthy'
    }

    if (healthFilter.value === 'cooling') {
      return item.health_level === 'cooling'
    }

    if (healthFilter.value === 'abnormal') {
      return ['warning', 'cooling', 'failed'].includes(item.health_level)
    }

    return true
  })
})

const sourceSummary = computed(() => ({
  total: sources.value.length,
  enabled: sources.value.filter((item) => item.enabled).length,
  healthy: sources.value.filter((item) => item.health_level === 'healthy').length,
  abnormal: sources.value.filter((item) => ['warning', 'cooling', 'failed'].includes(item.health_level)).length,
  cooling: sources.value.filter((item) => item.health_level === 'cooling').length,
}))

function getFilterCount(value: 'all' | 'healthy' | 'abnormal' | 'cooling'): number {
  if (value === 'all') {
    return sourceSummary.value.total
  }

  if (value === 'healthy') {
    return sourceSummary.value.healthy
  }

  if (value === 'cooling') {
    return sourceSummary.value.cooling
  }

  return sourceSummary.value.abnormal
}

function describeHealth(source: Source): string {
  if (source.health_level === 'cooling' && source.next_retry_at) {
    return `冷却至 ${formatDateTime(source.next_retry_at)}`
  }

  if (source.can_retry_now) {
    return '已进入重试窗口'
  }

  if (source.last_retry_attempts > 0) {
    return `重试阶段 ${source.last_retry_attempts}/3`
  }

  if (source.consecutive_failures > 0) {
    return `连续失败 ${source.consecutive_failures} 次`
  }

  return `最近处理 ${source.last_crawl_processed_count} 条`
}

async function loadSources() {
  loading.value = true

  try {
    sources.value = await api.getSources()
  } catch (error) {
    ui.notify(error instanceof Error ? error.message : '加载内容源失败', 'error')
  } finally {
    loading.value = false
  }
}

async function toggleSource(source: Source) {
  togglingId.value = source.id

  try {
    await api.toggleSource(source.id)
    ui.notify(`${source.name} 已切换状态`, 'success')
    await loadSources()
  } catch (error) {
    ui.notify(error instanceof Error ? error.message : '切换内容源失败', 'error')
  } finally {
    togglingId.value = null
  }
}

onMounted(loadSources)
</script>

<template>
  <div class="view-stack">
    <section class="hero-banner">
      <div>
        <p class="hero-banner__eyebrow">Source Center</p>
        <h3>把论坛、博客和官方工程文章源头收拾干净，后面整条流水线就顺了。</h3>
        <div class="hero-inline">
          <span class="meta-pill">健康来源 {{ sourceSummary.healthy }}</span>
          <span class="meta-pill">异常来源 {{ sourceSummary.abnormal }}</span>
          <span class="meta-pill">冷却中 {{ sourceSummary.cooling }}</span>
        </div>
      </div>
      <RouterLink class="shell-button" to="/sources/new">新增内容源</RouterLink>
    </section>

    <div class="panel-grid panel-grid--metrics">
      <PanelCard eyebrow="总内容源" :title="String(sourceSummary.total)" accent="copper">
        <p class="muted-copy">目前已纳入后台管理的站点总数。</p>
      </PanelCard>
      <PanelCard eyebrow="启用中" :title="String(sourceSummary.enabled)">
        <p class="muted-copy">会被抓取任务扫描的来源。</p>
      </PanelCard>
      <PanelCard eyebrow="健康来源" :title="String(sourceSummary.healthy)">
        <p class="muted-copy">最近抓取稳定、当前没有失败积压的来源。</p>
      </PanelCard>
      <PanelCard eyebrow="异常来源" :title="String(sourceSummary.abnormal)">
        <p class="muted-copy">待重试、冷却中和失败来源都会在这里汇总。</p>
      </PanelCard>
    </div>

    <PanelCard eyebrow="Filtering" title="来源列表">
      <template #header-extra>
        <label class="shell-field shell-field--inline">
          <span>搜索</span>
          <input v-model="search" class="shell-input" type="search" placeholder="按名称、slug 或分类过滤" />
        </label>
      </template>

      <div v-if="loading" class="skeleton-block skeleton-block--table" />
      <template v-else-if="filteredSources.length">
        <div class="filter-tabs">
          <button
            v-for="item in filterOptions"
            :key="item.value"
            class="filter-tab"
            :class="{ 'is-active': healthFilter === item.value }"
            type="button"
            @click="healthFilter = item.value"
          >
            <span>{{ item.label }}</span>
            <strong>{{ getFilterCount(item.value) }}</strong>
          </button>
        </div>
        <div class="table-scroll">
          <table class="shell-table">
            <thead>
              <tr>
                <th>名称</th>
                <th>类型 / 分类</th>
                <th>抓取健康</th>
                <th>最近成功</th>
                <th>最近失败</th>
                <th>下次重试</th>
                <th>日报</th>
                <th>状态</th>
                <th>操作</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="item in filteredSources" :key="item.id">
                <td>
                  <div class="table-primary">
                    <strong>{{ item.name }}</strong>
                    <a :href="item.site_url" target="_blank" rel="noreferrer">{{ item.slug }}</a>
                  </div>
                </td>
                <td>
                  <div class="table-primary">
                    <strong>{{ item.source_type.toUpperCase() }}</strong>
                    <span class="table-subcopy">{{ item.category || '未分类' }}</span>
                    <span class="table-subcopy">{{ item.language_hint || '未标记语言' }}</span>
                  </div>
                </td>
                <td>
                  <div class="table-primary">
                    <StatusBadge :label="item.health_label" />
                    <span class="table-subcopy">{{ describeHealth(item) }}</span>
                    <span v-if="item.last_crawl_error" class="table-error">{{ item.last_crawl_error }}</span>
                  </div>
                </td>
                <td>{{ formatDateTime(item.last_success_at) }}</td>
                <td>{{ formatDateTime(item.last_failure_at) }}</td>
                <td>
                  <span v-if="item.can_retry_now" class="table-ready">可立即重试</span>
                  <span v-else>{{ formatDateTime(item.next_retry_at) }}</span>
                </td>
                <td>{{ formatBoolean(item.include_in_daily) }}</td>
                <td>
                  <StatusBadge :label="item.enabled ? 'enabled' : 'disabled'" />
                </td>
                <td>
                  <div class="table-actions">
                    <RouterLink class="shell-link" :to="`/sources/${item.id}/rules`">规则</RouterLink>
                    <RouterLink class="shell-link" :to="`/sources/${item.id}/edit`">编辑</RouterLink>
                    <button
                      class="shell-link shell-link--button"
                      :disabled="togglingId === item.id"
                      @click="toggleSource(item)"
                    >
                      {{ togglingId === item.id ? '处理中...' : item.enabled ? '停用' : '启用' }}
                    </button>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </template>
      <EmptyState
        v-else
        title="还没有内容源"
        description="先添加美团技术团队、Anthropic Engineering 这类高质量来源，日报才有内容。"
      >
        <RouterLink class="shell-button shell-button--secondary" to="/sources/new">去创建第一个来源</RouterLink>
      </EmptyState>
    </PanelCard>
  </div>
</template>
