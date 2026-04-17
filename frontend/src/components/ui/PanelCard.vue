<script setup lang="ts">
defineProps<{
  eyebrow?: string
  title?: string
  accent?: 'sand' | 'copper' | 'ink'
}>()
</script>

<template>
  <section class="panel-card" :data-accent="accent || 'sand'">
    <header v-if="eyebrow || title" class="panel-card__header">
      <p v-if="eyebrow" class="panel-card__eyebrow">{{ eyebrow }}</p>
      <h2 v-if="title" class="panel-card__title">{{ title }}</h2>
      <slot name="header-extra" />
    </header>
    <div class="panel-card__body">
      <slot />
    </div>
  </section>
</template>
