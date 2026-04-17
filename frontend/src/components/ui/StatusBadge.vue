<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{
  label: string
  tone?: 'default' | 'success' | 'warning' | 'danger' | 'info'
}>()

const badgeTone = computed(() => {
  if (props.tone) {
    return props.tone
  }

  const text = props.label.toLowerCase()

  if (['success', 'published', 'enabled', 'running', 'true', '是', 'healthy', '健康'].includes(text)) {
    return 'success'
  }

  if (['failed', 'error', 'danger', 'false', '否', '失败'].includes(text)) {
    return 'danger'
  }

  if (['draft', 'pending', 'manual', 'partial_success', 'warning', '待重试'].includes(text)) {
    return 'warning'
  }

  if (['cooling', '冷却中', 'idle', '未抓取', 'disabled', 'stopped'].includes(text)) {
    return 'info'
  }

  return 'info'
})
</script>

<template>
  <span class="status-badge" :data-tone="badgeTone">{{ label }}</span>
</template>
