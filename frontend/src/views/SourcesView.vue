<script setup lang="ts">
import SourceForm from '../components/sources/SourceForm.vue'
import SourceTable from '../components/sources/SourceTable.vue'
import { useSources } from '../composables/useSources'

const {
  sources,
  loading,
  errorMessage,
  actionMessage,
  initialDraft,
  createSource,
  syncAllSources,
  syncSingleSource,
} = useSources()
</script>

<template>
  <section class="page">
    <header class="page-header">
      <div>
        <p class="page-kicker">Source Control</p>
        <h2 class="page-title">数据源管理</h2>
      </div>
      <button class="primary-button" type="button" @click="syncAllSources">
        同步全部数据源
      </button>
    </header>

    <p v-if="errorMessage" class="status-banner status-error">{{ errorMessage }}</p>
    <p v-else-if="actionMessage" class="status-banner">{{ actionMessage }}</p>
    <p v-else-if="loading" class="status-banner">数据源加载中...</p>

    <div class="page-grid">
      <SourceForm :initial-value="initialDraft" @save="createSource" />
      <SourceTable :sources="sources" @sync="syncSingleSource" />
    </div>
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

.page-grid {
  display: grid;
  grid-template-columns: 360px minmax(0, 1fr);
  gap: 1rem;
}

@media (max-width: 1100px) {
  .page-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 720px) {
  .page-header {
    align-items: stretch;
    flex-direction: column;
  }
}
</style>

