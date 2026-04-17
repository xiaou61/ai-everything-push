<script setup lang="ts">
import { computed } from 'vue'

import type { ArticleDetailPayload } from '../../types'

interface Props {
  article: ArticleDetailPayload | null
  loading: boolean
  errorMessage: string
  open: boolean
}

const props = defineProps<Props>()
const emit = defineEmits<{
  close: []
}>()

const displayContent = computed(() => props.article?.content || props.article?.summary || '暂无正文')
const showOriginalContent = computed(() => {
  if (!props.article?.original_content || !props.article.content) {
    return false
  }
  return props.article.original_content.trim() !== props.article.content.trim()
})
</script>

<template>
  <aside v-if="open" class="panel-wrapper">
    <div class="panel-overlay" @click="emit('close')" />
    <section class="panel">
      <header class="panel-header">
        <div class="panel-header-copy">
          <p class="panel-kicker">Article Detail</p>
          <h3 class="panel-title">{{ article?.title || '文章详情' }}</h3>
        </div>
        <button class="panel-close" type="button" @click="emit('close')">关闭</button>
      </header>

      <p v-if="errorMessage" class="panel-banner panel-error">{{ errorMessage }}</p>
      <p v-else-if="loading" class="panel-banner">文章详情加载中...</p>

      <div v-if="article" class="panel-body">
        <div class="panel-meta">
          <span>{{ article.source_name }}</span>
          <span>{{ article.author ? `作者：${article.author}` : '作者未知' }}</span>
          <span>{{ `分类：${article.category}` }}</span>
          <span>{{ `语言：${article.language}` }}</span>
          <span>{{ article.published_at ? article.published_at.slice(0, 16).replace('T', ' ') : '时间未知' }}</span>
        </div>

        <div class="panel-section">
          <p class="panel-label">摘要</p>
          <p class="panel-text">{{ article.summary }}</p>
        </div>

        <div v-if="article.original_title && article.original_title !== article.title" class="panel-section">
          <p class="panel-label">原始标题</p>
          <p class="panel-text">{{ article.original_title }}</p>
        </div>

        <div class="panel-section">
          <p class="panel-label">正文</p>
          <p class="panel-text">{{ displayContent }}</p>
        </div>

        <div v-if="showOriginalContent" class="panel-section">
          <p class="panel-label">原文</p>
          <p class="panel-text panel-text-muted">{{ article.original_content }}</p>
        </div>

        <a class="panel-link" :href="article.url" target="_blank" rel="noreferrer">
          打开原文链接
        </a>
      </div>
    </section>
  </aside>
</template>

<style scoped>
.panel-wrapper {
  position: fixed;
  inset: 0;
  z-index: 30;
}

.panel-overlay {
  position: absolute;
  inset: 0;
  background: rgba(2, 8, 18, 0.55);
  backdrop-filter: blur(4px);
}

.panel {
  position: absolute;
  top: 0;
  right: 0;
  width: min(520px, 100%);
  height: 100%;
  padding: 1.5rem;
  display: grid;
  grid-template-rows: auto auto 1fr;
  gap: 1rem;
  background:
    radial-gradient(circle at top right, rgba(65, 218, 255, 0.18), transparent 28%),
    linear-gradient(180deg, rgba(8, 17, 31, 0.98), rgba(12, 30, 53, 0.98));
  border-left: 1px solid rgba(255, 255, 255, 0.08);
  box-shadow: -20px 0 50px rgba(0, 0, 0, 0.28);
  overflow-y: auto;
}

.panel-header {
  display: flex;
  align-items: start;
  justify-content: space-between;
  gap: 1rem;
}

.panel-header-copy {
  display: grid;
  gap: 0.4rem;
}

.panel-kicker,
.panel-label,
.panel-text-muted,
.panel-meta,
.panel-banner {
  margin: 0;
  color: var(--color-muted);
}

.panel-title {
  margin: 0;
  line-height: 1.2;
}

.panel-close {
  padding: 0.7rem 0.9rem;
  border: none;
  border-radius: 999px;
  cursor: pointer;
  background: rgba(255, 255, 255, 0.08);
  color: var(--color-text);
}

.panel-banner {
  padding: 0.9rem 1rem;
  border-radius: 1rem;
  background: rgba(255, 255, 255, 0.05);
}

.panel-error {
  background: rgba(255, 99, 132, 0.14);
  color: #ffc9d6;
}

.panel-body {
  display: grid;
  gap: 1rem;
}

.panel-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 0.7rem;
}

.panel-section {
  display: grid;
  gap: 0.45rem;
  padding: 1rem;
  border-radius: 1rem;
  background: rgba(255, 255, 255, 0.04);
}

.panel-text {
  margin: 0;
  color: var(--color-text);
  line-height: 1.8;
  white-space: pre-wrap;
}

.panel-link {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: fit-content;
  padding: 0.85rem 1rem;
  border-radius: 999px;
  text-decoration: none;
  color: #06223d;
  background: linear-gradient(135deg, var(--color-accent), var(--color-accent-secondary));
  font-weight: 700;
}

@media (max-width: 720px) {
  .panel {
    width: 100%;
  }
}
</style>
