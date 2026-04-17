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

  if (['success', 'published', 'enabled', 'running', 'true', '是'].includes(text)) {
    return 'success'
  }

  if (['failed', 'error', 'danger', 'false', '否'].includes(text)) {
    return 'danger'
  }

  if (['draft', 'pending', 'manual'].includes(text)) {
    return 'warning'
  }

  return 'info'
})
</script>

<template>
  <span class="status-badge" :data-tone="badgeTone">{{ label }}</span>
</template>
