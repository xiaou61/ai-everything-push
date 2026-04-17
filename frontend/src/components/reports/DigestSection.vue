<script setup lang="ts">
import { computed } from 'vue'

import type { DigestSectionItem } from '../../types'

interface Props {
  section: DigestSectionItem
}

const props = defineProps<Props>()
const emit = defineEmits<{
  selectArticle: [articleId: number]
}>()

const sectionArticles = computed(() => props.section.articles)

function handleSelectArticle(articleId: number | null) {
  if (articleId == null) {
    return
  }

  emit('selectArticle', articleId)
}
</script>

<template>
  <section class="section-card">
    <header class="section-header">
      <div>
        <p class="section-kicker">Category</p>
        <h3 class="section-title">{{ section.category }}</h3>
      </div>
      <strong class="section-count">{{ section.count }} 条</strong>
    </header>

    <article v-for="article in sectionArticles" :key="article.article_id ?? article.url" class="section-article">
      <div class="section-article-main">
        <button
          class="section-article-title"
          type="button"
          :disabled="article.article_id == null"
          @click="handleSelectArticle(article.article_id)"
        >
          {{ article.title }}
        </button>
        <p v-if="article.original_title && article.original_title !== article.title" class="section-article-original">
          原始标题：{{ article.original_title }}
        </p>
        <p class="section-article-summary">{{ article.summary }}</p>
      </div>

      <div class="section-article-meta">
        <span>{{ article.source_name }}</span>
        <span>{{ article.author ? `作者：${article.author}` : '作者未知' }}</span>
        <span>{{ `语言：${article.language || '未知'}` }}</span>
        <span>{{ article.published_at ? article.published_at.slice(0, 16).replace('T', ' ') : '时间未知' }}</span>
      </div>

      <div class="section-article-actions">
        <button
          class="section-action-button"
          type="button"
          :disabled="article.article_id == null"
          @click="handleSelectArticle(article.article_id)"
        >
          {{ article.article_id == null ? '详情暂不可用' : '查看详情' }}
        </button>
        <a class="section-action-link" :href="article.url" target="_blank" rel="noreferrer">打开原文</a>
      </div>
    </article>
  </section>
</template>

<style scoped>
.section-card {
  display: grid;
  gap: 1rem;
  padding: 1.5rem;
  border-radius: 1.5rem;
  background: rgba(5, 21, 40, 0.86);
  border: 1px solid rgba(255, 255, 255, 0.08);
}

.section-header {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 1rem;
}

.section-kicker,
.section-article-summary,
.section-article-meta,
.section-article-original {
  margin: 0;
  color: var(--color-muted);
}

.section-title {
  margin: 0.25rem 0 0;
}

.section-count {
  font-size: 1.4rem;
}

.section-article {
  display: grid;
  gap: 0.75rem;
  padding-top: 1rem;
  border-top: 1px solid rgba(255, 255, 255, 0.08);
}

.section-article-title {
  padding: 0;
  border: none;
  background: transparent;
  color: var(--color-text);
  text-align: left;
  font-weight: 700;
  font-size: 1rem;
  cursor: pointer;
}

.section-article-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 0.75rem;
}

.section-article-title:disabled {
  cursor: not-allowed;
  opacity: 0.6;
}

.section-article-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 0.75rem;
}

.section-action-button,
.section-action-link {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-height: 2.75rem;
  padding: 0.75rem 1rem;
  border-radius: 999px;
  font-weight: 700;
}

.section-action-button {
  border: none;
  cursor: pointer;
  color: #06223d;
  background: linear-gradient(135deg, var(--color-accent), var(--color-accent-secondary));
}

.section-action-button:disabled {
  cursor: not-allowed;
  opacity: 0.55;
}

.section-action-link {
  color: var(--color-text);
  text-decoration: none;
  background: rgba(255, 255, 255, 0.06);
}
</style>
