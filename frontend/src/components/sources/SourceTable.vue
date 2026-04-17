<script setup lang="ts">
import type { SourcePayload } from '../../types'

interface Props {
  sources: SourcePayload[]
}

defineProps<Props>()
const emit = defineEmits<{
  sync: [sourceId: number]
}>()
</script>

<template>
  <div class="source-table">
    <article v-for="source in sources" :key="source.id" class="source-card">
      <div class="source-main">
        <div class="source-head">
          <h3 class="source-title">{{ source.name }}</h3>
          <span class="source-tag">{{ source.source_type }}</span>
        </div>
        <p class="source-url">{{ source.url }}</p>
        <p class="source-meta">
          分类提示：{{ source.category_hint || '未设置' }} · 抓取上限：{{ source.fetch_limit }} ·
          {{ source.enabled ? '启用中' : '已停用' }}
        </p>
      </div>

      <div class="source-actions">
        <span class="source-sync-time">
          {{ source.last_synced_at ? `最近同步 ${source.last_synced_at.slice(0, 16).replace('T', ' ')}` : '尚未同步' }}
        </span>
        <button class="ghost-button" type="button" @click="emit('sync', source.id)">
          立即同步
        </button>
      </div>
    </article>
  </div>
</template>

<style scoped>
.source-table {
  display: grid;
  gap: 1rem;
}

.source-card {
  display: grid;
  gap: 1rem;
  padding: 1.4rem;
  border-radius: 1.4rem;
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid rgba(255, 255, 255, 0.08);
}

.source-head,
.source-actions {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
}

.source-title,
.source-url,
.source-meta,
.source-sync-time {
  margin: 0;
}

.source-url,
.source-meta,
.source-sync-time {
  color: var(--color-muted);
}

.source-tag {
  padding: 0.35rem 0.8rem;
  border-radius: 999px;
  background: rgba(65, 218, 255, 0.14);
  color: #7ee7ff;
}
</style>

