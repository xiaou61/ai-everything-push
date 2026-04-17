<script setup lang="ts">
import DigestTimeline from '../components/reports/DigestTimeline.vue'
import { useDigests } from '../composables/useDigests'

const {
  digests,
  loading,
  errorMessage,
  actionMessage,
  generateTodayDigest,
  pushDigest,
} = useDigests()
</script>

<template>
  <section class="page">
    <header class="page-header">
      <div>
        <p class="page-kicker">Digest Center</p>
        <h2 class="page-title">日报与推送</h2>
      </div>
      <button class="primary-button" type="button" @click="generateTodayDigest">
        生成今日日报
      </button>
    </header>

    <p v-if="errorMessage" class="status-banner status-error">{{ errorMessage }}</p>
    <p v-else-if="actionMessage" class="status-banner">{{ actionMessage }}</p>
    <p v-else-if="loading" class="status-banner">日报列表加载中...</p>

    <DigestTimeline :digests="digests" @push="pushDigest" />
  </section>
</template>

<style scoped>
.page {
  display: grid;
  gap: 1.5rem;
}

.page-header {
  display: flex;
  align-items: end;
  justify-content: space-between;
  gap: 1rem;
}

.page-kicker {
  margin: 0;
  color: var(--color-muted);
}

.page-title {
  margin: 0.35rem 0 0;
}

@media (max-width: 720px) {
  .page-header {
    align-items: stretch;
    flex-direction: column;
  }
}
</style>

