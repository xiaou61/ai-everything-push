<script setup lang="ts">
interface Props {
  label: string
  value: string | number
  caption: string
}

defineProps<Props>()
</script>

<template>
  <article class="kpi-card">
    <p class="kpi-label">{{ label }}</p>
    <strong class="kpi-value">{{ value }}</strong>
    <p class="kpi-caption">{{ caption }}</p>
  </article>
</template>

<style scoped>
.kpi-card {
  padding: 1.25rem;
  border-radius: 1.5rem;
  background: rgba(7, 23, 42, 0.84);
  border: 1px solid rgba(255, 255, 255, 0.08);
  box-shadow: 0 18px 40px rgba(0, 0, 0, 0.18);
}

.kpi-label,
.kpi-caption {
  margin: 0;
  color: var(--color-muted);
}

.kpi-value {
  display: block;
  margin: 0.5rem 0;
  font-size: 2rem;
}
</style>

