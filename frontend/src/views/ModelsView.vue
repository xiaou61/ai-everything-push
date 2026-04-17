<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'

import EmptyState from '../components/ui/EmptyState.vue'
import PanelCard from '../components/ui/PanelCard.vue'
import StatusBadge from '../components/ui/StatusBadge.vue'
import { api } from '../lib/api'
import { formatTaskType } from '../lib/format'
import { useUiStore } from '../stores/ui'
import type { ModelConfig, ModelConfigPayload } from '../types/admin'

const ui = useUiStore()

const loading = ref(true)
const saving = ref(false)
const models = ref<ModelConfig[]>([])
const editingId = ref<number | null>(null)

const defaultForm = (): ModelConfigPayload => ({
  task_type: 'summary',
  provider_name: 'aiwanwu',
  model_name: 'gpt-4.1-mini',
  base_url: 'https://www.aiwanwu.cc/v1',
  api_key_env_name: 'AIWANWU_API_KEY',
  temperature: '0.2',
  max_tokens: 4000,
  enabled: true,
  is_default: true,
})

const form = ref<ModelConfigPayload>(defaultForm())

const formTitle = computed(() => (editingId.value ? '编辑模型配置' : '新增模型配置'))

async function loadModels() {
  loading.value = true

  try {
    models.value = await api.getModels()
  } catch (error) {
    ui.notify(error instanceof Error ? error.message : '加载模型失败', 'error')
  } finally {
    loading.value = false
  }
}

function editModel(item: ModelConfig) {
  editingId.value = item.id
  form.value = {
    task_type: item.task_type,
    provider_name: item.provider_name,
    model_name: item.model_name,
    base_url: item.base_url,
    api_key_env_name: item.api_key_env_name,
    temperature: item.temperature,
    max_tokens: item.max_tokens,
    enabled: item.enabled,
    is_default: item.is_default,
  }
}

function resetForm() {
  editingId.value = null
  form.value = defaultForm()
}

async function submitForm() {
  saving.value = true

  try {
    if (editingId.value) {
      await api.updateModel(editingId.value, form.value)
      ui.notify('模型配置已更新', 'success')
    } else {
      await api.createModel(form.value)
      ui.notify('模型配置已创建', 'success')
    }

    resetForm()
    await loadModels()
  } catch (error) {
    ui.notify(error instanceof Error ? error.message : '保存模型失败', 'error')
  } finally {
    saving.value = false
  }
}

onMounted(loadModels)
</script>

<template>
  <div class="view-stack">
    <section class="hero-banner">
      <div>
        <p class="hero-banner__eyebrow">Model Stack</p>
        <h3>先把中转站模型调顺，再考虑后续扩展更多任务类型和模型档位。</h3>
      </div>
    </section>

    <div class="panel-grid panel-grid--two">
      <PanelCard eyebrow="Available Models" title="已配置模型" accent="ink">
        <div v-if="loading" class="skeleton-block skeleton-block--tall" />
        <template v-else-if="models.length">
          <div class="stack-list">
            <button
              v-for="item in models"
              :key="item.id"
              class="stack-card"
              type="button"
              @click="editModel(item)"
            >
              <div class="stack-card__header">
                <strong>{{ formatTaskType(item.task_type) }}</strong>
                <StatusBadge :label="item.enabled ? 'enabled' : 'disabled'" />
              </div>
              <p>{{ item.model_name }}</p>
              <div class="stack-card__meta">
                <span>{{ item.provider_name }}</span>
                <span>{{ item.api_key_env_name }}</span>
                <span>{{ item.is_default ? '默认模型' : '备用模型' }}</span>
              </div>
            </button>
          </div>
        </template>
        <EmptyState
          v-else
          title="还没有模型配置"
          description="先配置一组摘要/翻译模型，日报处理链路才能跑起来。"
        />
      </PanelCard>

      <PanelCard eyebrow="Editor" :title="formTitle" accent="copper">
        <form class="shell-form" @submit.prevent="submitForm">
          <div class="shell-form__grid">
            <label class="shell-field">
              <span>任务类型</span>
              <select v-model="form.task_type" class="shell-select">
                <option value="translation">translation</option>
                <option value="summary">summary</option>
                <option value="classification">classification</option>
                <option value="title">title</option>
              </select>
            </label>

            <label class="shell-field">
              <span>服务商</span>
              <input v-model="form.provider_name" class="shell-input" type="text" />
            </label>

            <label class="shell-field">
              <span>模型名</span>
              <input v-model="form.model_name" class="shell-input" type="text" />
            </label>

            <label class="shell-field">
              <span>温度</span>
              <input v-model="form.temperature" class="shell-input" type="text" />
            </label>

            <label class="shell-field shell-field--full">
              <span>Base URL</span>
              <input v-model="form.base_url" class="shell-input" type="url" />
            </label>

            <label class="shell-field">
              <span>API Key 环境变量</span>
              <input v-model="form.api_key_env_name" class="shell-input" type="text" />
            </label>

            <label class="shell-field">
              <span>最大 Token</span>
              <input v-model="form.max_tokens" class="shell-input" type="number" min="128" max="32768" />
            </label>

            <label class="toggle-field">
              <input v-model="form.enabled" type="checkbox" />
              <span>启用模型</span>
            </label>

            <label class="toggle-field">
              <input v-model="form.is_default" type="checkbox" />
              <span>设为默认</span>
            </label>
          </div>

          <p class="muted-copy">
            这里建议只保存环境变量名，不要把真实密钥直接写进数据库。当前可先统一用
            <code>AIWANWU_API_KEY</code>。
          </p>

          <div class="form-actions">
            <button class="shell-button" type="submit" :disabled="saving">
              {{ saving ? '保存中...' : editingId ? '保存修改' : '创建模型' }}
            </button>
            <button class="shell-button shell-button--secondary" type="button" @click="resetForm">
              新建空白
            </button>
          </div>
        </form>
      </PanelCard>
    </div>
  </div>
</template>
