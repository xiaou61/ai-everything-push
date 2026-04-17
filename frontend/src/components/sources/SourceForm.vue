<script setup lang="ts">
import { computed, reactive } from 'vue'

import type { SourceDraft, SourceType } from '../../types'

interface Props {
  initialValue: SourceDraft
}

const props = defineProps<Props>()
const emit = defineEmits<{
  save: [payload: SourceDraft]
}>()

const formState = reactive<SourceDraft>({
  ...props.initialValue,
  parser_config: { ...props.initialValue.parser_config },
})

const parserConfigText = computed({
  get: () => JSON.stringify(formState.parser_config, null, 2),
  set: (value: string) => {
    try {
      formState.parser_config = JSON.parse(value || '{}') as Record<string, unknown>
    } catch {
      formState.parser_config = {}
    }
  },
})

const sourceTypeOptions: SourceType[] = ['rss', 'json', 'html']

function handleSubmit() {
  emit('save', {
    ...formState,
    category_hint: formState.category_hint.trim(),
    url: formState.url.trim(),
    name: formState.name.trim(),
    parser_config: { ...formState.parser_config },
  })
}
</script>

<template>
  <form class="source-form" @submit.prevent="handleSubmit">
    <label class="field-group">
      <span class="field-label">名称</span>
      <input v-model="formState.name" class="field-control" placeholder="如：Hacker News" />
    </label>

    <label class="field-group">
      <span class="field-label">源地址</span>
      <input v-model="formState.url" class="field-control" placeholder="https://example.com/feed.xml" />
    </label>

    <div class="field-row">
      <label class="field-group">
        <span class="field-label">类型</span>
        <select v-model="formState.source_type" class="field-control">
          <option v-for="item in sourceTypeOptions" :key="item" :value="item">{{ item }}</option>
        </select>
      </label>

      <label class="field-group">
        <span class="field-label">分类提示</span>
        <input v-model="formState.category_hint" class="field-control" placeholder="AI / Product / Security" />
      </label>
    </div>

    <div class="field-row">
      <label class="field-group">
        <span class="field-label">抓取条数</span>
        <input v-model.number="formState.fetch_limit" class="field-control" type="number" min="1" max="100" />
      </label>

      <label class="field-group field-switch">
        <span class="field-label">启用</span>
        <input v-model="formState.enabled" type="checkbox" />
      </label>
    </div>

    <label class="field-group">
      <span class="field-label">解析规则 JSON</span>
      <textarea v-model="parserConfigText" class="field-textarea" rows="8" placeholder='{"items_path":"data.items"}' />
    </label>

    <button class="primary-button" type="submit">保存数据源</button>
  </form>
</template>

<style scoped>
.source-form {
  display: grid;
  gap: 1rem;
  padding: 1.5rem;
  border-radius: 1.5rem;
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid rgba(255, 255, 255, 0.08);
}

.field-row {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 1rem;
}

.field-group {
  display: grid;
  gap: 0.55rem;
}

.field-label {
  color: var(--color-muted);
  font-size: 0.9rem;
}

.field-control,
.field-textarea {
  width: 100%;
  padding: 0.9rem 1rem;
  border-radius: 1rem;
  border: 1px solid rgba(255, 255, 255, 0.1);
  background: rgba(5, 21, 40, 0.9);
  color: var(--color-text);
}

.field-switch {
  align-content: end;
}

@media (max-width: 720px) {
  .field-row {
    grid-template-columns: 1fr;
  }
}
</style>

