<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'

import EmptyState from '../components/ui/EmptyState.vue'
import PanelCard from '../components/ui/PanelCard.vue'
import StatusBadge from '../components/ui/StatusBadge.vue'
import { api } from '../lib/api'
import { formatDateTime } from '../lib/format'
import { useUiStore } from '../stores/ui'
import type { Article, ArticleDetail } from '../types/admin'

const ui = useUiStore()

const loading = ref(true)
const detailLoading = ref(false)
const reprocessLoading = ref(false)
const search = ref('')
const languageFilter = ref('all')
const statusFilter = ref('all')
const articles = ref<Article[]>([])
const selectedArticleId = ref<number | null>(null)
const selectedArticle = ref<ArticleDetail | null>(null)

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

async function selectArticle(articleId: number) {
  selectedArticleId.value = articleId
  detailLoading.value = true

  try {
    selectedArticle.value = await api.getArticle(articleId)
  } catch (error) {
    ui.notify(error instanceof Error ? error.message : '加载文章详情失败', 'error')
  } finally {
    detailLoading.value = false
  }
}

async function reprocessSelectedArticle() {
  if (!selectedArticle.value) {
    return
  }

  reprocessLoading.value = true

  try {
    const result = await api.reprocessArticle(selectedArticle.value.id)
    selectedArticle.value = result.article
    ui.notify(result.message, result.status === 'processed' ? 'success' : 'error')
    await loadArticles()
  } catch (error) {
    ui.notify(error instanceof Error ? error.message : '重新处理文章失败', 'error')
  } finally {
    reprocessLoading.value = false
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

    <PanelCard eyebrow="Inspector" title="文章详情">
      <div v-if="detailLoading" class="skeleton-block skeleton-block--tall" />
      <template v-else-if="selectedArticle">
        <div class="detail-shell">
          <div class="detail-head">
            <div>
              <p class="article-card__source">{{ selectedArticle.source_name }}</p>
              <h4>{{ selectedArticle.generated_title || selectedArticle.title }}</h4>
              <p class="muted-copy">{{ selectedArticle.summary || '这篇文章还没有摘要内容。' }}</p>
            </div>

            <div class="detail-actions">
              <StatusBadge :label="selectedArticle.status" />
              <button
                class="shell-button shell-button--secondary"
                :disabled="reprocessLoading || !selectedArticle.has_content"
                @click="reprocessSelectedArticle"
              >
                {{ reprocessLoading ? '重处理中...' : '重新处理' }}
              </button>
              <a :href="selectedArticle.canonical_url" target="_blank" rel="noreferrer" class="shell-button shell-button--ghost">
                打开原文
              </a>
            </div>
          </div>

          <div class="detail-grid">
            <div class="detail-kv">
              <span>语言</span>
              <strong>{{ selectedArticle.language || 'unknown' }}</strong>
            </div>
            <div class="detail-kv">
              <span>分类</span>
              <strong>{{ selectedArticle.category || '未分类' }}</strong>
            </div>
            <div class="detail-kv">
              <span>AI 状态</span>
              <strong>{{ selectedArticle.ai_status || '-' }}</strong>
            </div>
            <div class="detail-kv">
              <span>发布时间</span>
              <strong>{{ formatDateTime(selectedArticle.published_at) }}</strong>
            </div>
            <div class="detail-kv">
              <span>处理时间</span>
              <strong>{{ formatDateTime(selectedArticle.processed_at) }}</strong>
            </div>
            <div class="detail-kv">
              <span>来源 slug</span>
              <strong>{{ selectedArticle.source_slug || '-' }}</strong>
            </div>
          </div>

          <div v-if="selectedArticle.ai_error || selectedArticle.crawl_error" class="message-card message-card--danger">
            <strong>异常信息</strong>
            <p>{{ selectedArticle.ai_error || selectedArticle.crawl_error }}</p>
          </div>

          <div class="content-stack">
            <section class="content-panel">
              <div class="content-panel__head">
                <h4>清洗正文</h4>
                <span>{{ selectedArticle.clean_content ? '已提取' : '暂无' }}</span>
              </div>
              <pre>{{ selectedArticle.clean_content || '暂无正文内容。' }}</pre>
            </section>

            <section class="content-panel">
              <div class="content-panel__head">
                <h4>中文内容</h4>
                <span>{{ selectedArticle.translated_content ? '可用于日报' : '暂无' }}</span>
              </div>
              <pre>{{ selectedArticle.translated_content || selectedArticle.clean_content || '暂无中文内容。' }}</pre>
            </section>
          </div>
        </div>
      </template>
      <EmptyState
        v-else
        title="还没有选中文章"
        description="从下方文章列表点开一篇，就可以直接查看正文、摘要、AI 状态并单独重处理。"
      />
    </PanelCard>

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
            <option value="crawled">crawled</option>
            <option value="processed">processed</option>
            <option value="failed">failed</option>
          </select>
        </div>
      </template>

      <div v-if="loading" class="skeleton-block skeleton-block--table" />
      <template v-else-if="filteredArticles.length">
        <div class="article-grid">
          <article
            v-for="item in filteredArticles"
            :key="item.id"
            class="article-card"
            :class="{ 'is-active': selectedArticleId === item.id }"
          >
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

            <div class="article-actions">
              <button class="shell-link shell-link--button" @click="selectArticle(item.id)">
                {{ selectedArticleId === item.id ? '查看中' : '查看详情' }}
              </button>
              <a :href="item.canonical_url" target="_blank" rel="noreferrer" class="shell-link">
                打开原文
              </a>
            </div>
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
