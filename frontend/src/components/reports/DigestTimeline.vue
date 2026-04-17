<script setup lang="ts">
import { RouterLink } from 'vue-router'

import type { DigestPayload } from '../../types'

interface Props {
  digests: DigestPayload[]
}

defineProps<Props>()
const emit = defineEmits<{
  push: [digestId: number]
}>()
</script>

<template>
  <div class="timeline">
    <article v-for="digest in digests" :key="digest.id" class="timeline-card">
      <div class="timeline-main">
        <p class="timeline-date">{{ digest.digest_date }}</p>
        <h3 class="timeline-title">{{ digest.headline }}</h3>
        <p class="timeline-overview">{{ digest.overview }}</p>
      </div>

      <div class="timeline-meta">
        <span>{{ digest.article_count }} 条</span>
        <span>{{ digest.section_count }} 类</span>
        <span>{{ digest.pushed_at ? '已推送' : '未推送' }}</span>
      </div>

      <div class="timeline-actions">
        <RouterLink :to="`/reports/${digest.digest_date}`" class="ghost-link">查看详情</RouterLink>
        <button class="ghost-button" type="button" @click="emit('push', digest.id)">
          推送到飞书
        </button>
      </div>
    </article>
  </div>
</template>

<style scoped>
.timeline {
  display: grid;
  gap: 1rem;
}

.timeline-card {
  display: grid;
  gap: 1rem;
  padding: 1.4rem;
  border-radius: 1.5rem;
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid rgba(255, 255, 255, 0.08);
}

.timeline-date,
.timeline-overview {
  margin: 0;
  color: var(--color-muted);
}

.timeline-title {
  margin: 0.25rem 0 0;
}

.timeline-meta,
.timeline-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 0.75rem;
  align-items: center;
}

.ghost-link,
.ghost-button {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 0.8rem 1rem;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.08);
  color: var(--color-text);
  text-decoration: none;
  border: none;
  cursor: pointer;
}
</style>

