<script setup lang="ts">
import KpiCard from '../components/dashboard/KpiCard.vue'
import { useDashboard } from '../composables/useDashboard'

const { dashboard, loading, errorMessage, refreshDashboard } = useDashboard()
</script>

<template>
  <section class="page">
    <header class="page-header">
      <div>
        <p class="page-kicker">Overview</p>
        <h2 class="page-title">今天的情报引擎状态</h2>
      </div>
      <button class="primary-button" type="button" @click="refreshDashboard">
        刷新概览
      </button>
    </header>

    <p v-if="errorMessage" class="status-banner status-error">{{ errorMessage }}</p>
    <p v-else-if="loading" class="status-banner">仪表盘加载中...</p>

    <div v-if="dashboard" class="kpi-grid">
      <KpiCard label="数据源" :value="dashboard.source_count" caption="当前启用的采集入口" />
      <KpiCard label="文章数" :value="dashboard.article_count" caption="已入库并处理完成的内容" />
      <KpiCard label="日报数" :value="dashboard.digest_count" caption="已生成的历史日报" />
      <KpiCard
        label="最近同步"
        :value="dashboard.latest_sync_at ? dashboard.latest_sync_at.slice(0, 16).replace('T', ' ') : '未同步'"
        caption="最近一次全量或手动同步时间"
      />
    </div>

    <section v-if="dashboard" class="hero-card">
      <p class="page-kicker">Latest Digest</p>
      <h3 class="hero-title">{{ dashboard.latest_digest_headline || '还没有生成日报' }}</h3>
      <p class="hero-copy">
        {{ dashboard.latest_digest_date ? `最近一期日报日期：${dashboard.latest_digest_date}` : '建议先去日报页手动生成一次今日日报。' }}
      </p>
    </section>
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

.page-kicker,
.hero-copy {
  margin: 0;
  color: var(--color-muted);
}

.page-title,
.hero-title {
  margin: 0.35rem 0 0;
}

.kpi-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 1rem;
}

.hero-card {
  display: grid;
  gap: 0.75rem;
  padding: 1.8rem;
  border-radius: 1.8rem;
  background:
    radial-gradient(circle at top right, rgba(65, 218, 255, 0.2), transparent 36%),
    linear-gradient(145deg, rgba(255, 159, 67, 0.22), rgba(7, 23, 42, 0.95));
  border: 1px solid rgba(255, 255, 255, 0.08);
}

@media (max-width: 1100px) {
  .kpi-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 720px) {
  .page-header {
    align-items: stretch;
    flex-direction: column;
  }

  .kpi-grid {
    grid-template-columns: 1fr;
  }
}
</style>

