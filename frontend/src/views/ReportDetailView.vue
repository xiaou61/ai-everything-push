<script setup lang="ts">
import { computed, shallowRef, watch } from 'vue'
import { useRoute } from 'vue-router'

import ArticleDetailPanel from '../components/reports/ArticleDetailPanel.vue'
import DigestSection from '../components/reports/DigestSection.vue'
import { useArticleDetail } from '../composables/useArticleDetail'
import { useDigestDetail } from '../composables/useDigestDetail'

const route = useRoute()
const digestDate = computed(() => String(route.params.digestDate ?? ''))
const { digest, loading, errorMessage } = useDigestDetail(() => digestDate.value)
const selectedArticleId = shallowRef<number | null>(null)
const isArticlePanelOpen = computed(() => selectedArticleId.value !== null)
const {
  article,
  loading: articleLoading,
  errorMessage: articleErrorMessage,
} = useArticleDetail(() => selectedArticleId.value)

function handleSelectArticle(articleId: number) {
  selectedArticleId.value = articleId
}

function handleCloseArticlePanel() {
  selectedArticleId.value = null
}

watch(digestDate, () => {
  selectedArticleId.value = null
})
</script>

<template>
  <section class="page">
    <header class="detail-hero">
      <p class="page-kicker">Report Detail</p>
      <h2 class="page-title">{{ digest?.headline || '日报详情' }}</h2>
      <p class="detail-copy">{{ digest?.overview || '按日期查看分类汇总、重点条目和来源分布。' }}</p>
    </header>

    <p v-if="errorMessage" class="status-banner status-error">{{ errorMessage }}</p>
    <p v-else-if="loading" class="status-banner">日报详情加载中...</p>

    <div v-if="digest" class="section-grid">
      <DigestSection
        v-for="section in digest.sections"
        :key="section.category"
        :section="section"
        @select-article="handleSelectArticle"
      />
    </div>

    <ArticleDetailPanel
      :article="article"
      :loading="articleLoading"
      :error-message="articleErrorMessage"
      :open="isArticlePanelOpen"
      @close="handleCloseArticlePanel"
    />
  </section>
</template>

<style scoped>
.page {
  display: grid;
  gap: 1.5rem;
}

.detail-hero {
  display: grid;
  gap: 0.75rem;
  padding: 1.8rem;
  border-radius: 1.8rem;
  background:
    radial-gradient(circle at bottom left, rgba(255, 159, 67, 0.16), transparent 38%),
    rgba(5, 21, 40, 0.88);
  border: 1px solid rgba(255, 255, 255, 0.08);
}

.page-kicker,
.detail-copy {
  margin: 0;
  color: var(--color-muted);
}

.page-title {
  margin: 0;
}

.section-grid {
  display: grid;
  gap: 1rem;
}
</style>
