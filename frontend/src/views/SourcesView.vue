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
const sources = ref<Source[]>([])
const togglingId = ref<number | null>(null)

const filteredSources = computed(() => {
  const keyword = search.value.trim().toLowerCase()

  if (!keyword) {
    return sources.value
  }

  return sources.value.filter((item) =>
    [item.name, item.slug, item.category || '', item.language_hint || '', item.site_url]
      .join(' ')
      .toLowerCase()
      .includes(keyword),
  )
})

const sourceSummary = computed(() => ({
  total: sources.value.length,
  enabled: sources.value.filter((item) => item.enabled).length,
  included: sources.value.filter((item) => item.include_in_daily).length,
  unhealthy: sources.value.filter((item) => (item.consecutive_failures || 0) > 0).length,
}))

function getHealthLabel(source: Source): string {
  if (!source.last_crawl_status) {
    return 'idle'
  }

  if (source.last_crawl_status === 'success' && source.consecutive_failures === 0) {
    return 'success'
  }

  return source.last_crawl_status
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
      <PanelCard eyebrow="日报收录" :title="String(sourceSummary.included)">
        <p class="muted-copy">处理后允许进入日报候选池。</p>
      </PanelCard>
      <PanelCard eyebrow="异常来源" :title="String(sourceSummary.unhealthy)">
        <p class="muted-copy">连续失败大于 0 的来源建议优先排查。</p>
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
        <div class="table-scroll">
          <table class="shell-table">
            <thead>
              <tr>
                <th>名称</th>
                <th>类型</th>
                <th>语言</th>
                <th>分类</th>
                <th>抓取健康</th>
                <th>最近抓取</th>
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
                <td>{{ item.source_type }}</td>
                <td>{{ item.language_hint || '-' }}</td>
                <td>{{ item.category || '-' }}</td>
                <td>
                  <div class="table-primary">
                    <StatusBadge :label="getHealthLabel(item)" />
                    <span class="table-subcopy">
                      {{ item.consecutive_failures > 0 ? `连续失败 ${item.consecutive_failures} 次` : `最近处理 ${item.last_crawl_processed_count} 条` }}
                    </span>
                    <span v-if="item.last_crawl_error" class="table-error">{{ item.last_crawl_error }}</span>
                  </div>
                </td>
                <td>{{ formatDateTime(item.last_crawled_at) }}</td>
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
