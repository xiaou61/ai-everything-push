<script setup lang="ts">
import { storeToRefs } from 'pinia'
import { RouterView } from 'vue-router'

import { useUiStore } from './stores/ui'

const uiStore = useUiStore()
const { notices } = storeToRefs(uiStore)
</script>

<template>
  <RouterView />

  <div class="toast-stack">
    <button
      v-for="item in notices"
      :key="item.id"
      class="toast-card"
      :data-tone="item.tone"
      type="button"
      @click="uiStore.dismiss(item.id)"
    >
      {{ item.message }}
    </button>
  </div>
</template>
