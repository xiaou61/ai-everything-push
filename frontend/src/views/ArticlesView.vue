<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'

import EmptyState from '../components/ui/EmptyState.vue'
import PanelCard from '../components/ui/PanelCard.vue'
import StatusBadge from '../components/ui/StatusBadge.vue'
import { api } from '../lib/api'
import { formatDateTime } from '../lib/format'
import { useUiStore } from '../stores/ui'
import type { Article } from '../types/admin'

const ui = useUiStore()

const loading = ref(true)
const search = ref('')
const languageFilter = ref('all')
const statusFilter = ref('all')
const articles = ref<Article[]>([])

const filteredArticles = computed(() =>
  articles.value.filter((item) => {
    const keyword = search.value.trim().toLowerCase()
    const matchesKeyword =
      keyword.length === 0 ||
      [item.title, item.generated_title || '', item.source_name, item.summary || '', item.category || '']
        .join(' ')
        .toLowerCase()
        .includes(keyword)

    const matchesLanguage = languageFilter.value === 'all' || (item.language || 'unknown') === languageFilter.value
    const matchesStatus = statusFilter.value === 'all' || item.status === statusFilter.value

    return matchesKeyword && matchesLanguage && matchesStatus
  }),
)

async function loadArticles() {
  loading.value = true

  try {
    articles.value = await api.getArticles()
  } catch (error) {
    ui.notify(error instanceof Error ? error.message : '加载文章失败', 'error')
  } finally {
    loading.value = false
  }
}

onMounted(loadArticles)
</script>

<template>
  <div class="view-stack">
    <section class="hero-banner">
      <div>
        <p class="hero-banner__eyebrow">Article Pool</p>
        <h3>这里是所有抓取结果的中转池，也是翻译、摘要和分类的观察窗口。</h3>
      </div>
    </section>

    <PanelCard eyebrow="Filters" title="文章列表">
      <template #header-extra>
        <div class="filter-row">
          <input v-model="search" class="shell-input" type="search" placeholder="按标题、摘要、来源搜索" />
          <select v-model="languageFilter" class="shell-select">
            <option value="all">全部语言</option>
            <option value="zh">中文</option>
            <option value="en">英文</option>
            <option value="unknown">未识别</option>
          </select>
          <select v-model="statusFilter" class="shell-select">
            <option value="all">全部状态</option>
            <option value="pending">pending</option>
            <option value="processed">processed</option>
            <option value="failed">failed</option>
          </select>
        </div>
      </template>

      <div v-if="loading" class="skeleton-block skeleton-block--table" />
      <template v-else-if="filteredArticles.length">
        <div class="article-grid">
          <article v-for="item in filteredArticles" :key="item.id" class="article-card">
            <div class="article-card__header">
              <div>
                <p class="article-card__source">{{ item.source_name }}</p>
                <h4>{{ item.generated_title || item.title }}</h4>
              </div>
              <StatusBadge :label="item.status" />
            </div>

            <p class="muted-copy">{{ item.summary || '还没有摘要内容，等待处理任务完成。' }}</p>

            <div class="article-card__meta">
              <span>{{ item.language || 'unknown' }}</span>
              <span>{{ item.category || '未分类' }}</span>
              <span>{{ formatDateTime(item.published_at) }}</span>
            </div>

            <a :href="item.canonical_url" target="_blank" rel="noreferrer" class="shell-link">
              打开原文
            </a>
          </article>
        </div>
      </template>
      <EmptyState
        v-else
        title="还没有文章"
        description="先跑一次抓取任务，或者调整来源规则，文章池就会开始积累内容。"
      />
    </PanelCard>
  </div>
</template>
