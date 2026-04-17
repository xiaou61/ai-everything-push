<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'

import EmptyState from '../components/ui/EmptyState.vue'
import PanelCard from '../components/ui/PanelCard.vue'
import StatusBadge from '../components/ui/StatusBadge.vue'
import { api } from '../lib/api'
import { useUiStore } from '../stores/ui'
import type { Source, SourceRulePayload, SourceRulePreviewResult } from '../types/admin'

const route = useRoute()
const ui = useUiStore()

const loading = ref(true)
const saving = ref(false)
const previewing = ref<'list' | 'article' | null>(null)
const source = ref<Source | null>(null)
const previewUrl = ref('')
const preview = ref<SourceRulePreviewResult | null>(null)

const form = ref<SourceRulePayload>({
  list_item_selector: null,
  link_selector: null,
  title_selector: null,
  published_at_selector: null,
  author_selector: null,
  content_selector: null,
  remove_selectors: null,
  request_headers_json: null,
})

const sourceId = computed(() => Number(route.params.id))

function fillForm(payload?: Partial<SourceRulePayload> | null) {
  form.value = {
    list_item_selector: payload?.list_item_selector || null,
    link_selector: payload?.link_selector || null,
    title_selector: payload?.title_selector || null,
    published_at_selector: payload?.published_at_selector || null,
    author_selector: payload?.author_selector || null,
    content_selector: payload?.content_selector || null,
    remove_selectors: payload?.remove_selectors || null,
    request_headers_json: payload?.request_headers_json || null,
  }
}

function normalizePayload(): SourceRulePayload {
  return {
    list_item_selector: form.value.list_item_selector || null,
    link_selector: form.value.link_selector || null,
    title_selector: form.value.title_selector || null,
    published_at_selector: form.value.published_at_selector || null,
    author_selector: form.value.author_selector || null,
    content_selector: form.value.content_selector || null,
    remove_selectors: form.value.remove_selectors || null,
    request_headers_json: form.value.request_headers_json || null,
  }
}

async function loadData() {
  loading.value = true

  try {
    const [sourceDetail, rule] = await Promise.all([
      api.getSource(sourceId.value),
      api.getSourceRules(sourceId.value),
    ])

    source.value = sourceDetail
    previewUrl.value = sourceDetail.list_url || sourceDetail.site_url
    fillForm(rule)
  } catch (error) {
    ui.notify(error instanceof Error ? error.message : '加载抓取规则失败', 'error')
  } finally {
    loading.value = false
  }
}

async function saveRules() {
  saving.value = true

  try {
    await api.saveSourceRules(sourceId.value, normalizePayload())
    ui.notify('抓取规则已保存', 'success')
  } catch (error) {
    ui.notify(error instanceof Error ? error.message : '保存抓取规则失败', 'error')
  } finally {
    saving.value = false
  }
}

async function runPreview(mode: 'list' | 'article') {
  previewing.value = mode

  try {
    preview.value = await api.previewSourceRules(sourceId.value, {
      ...normalizePayload(),
      preview_mode: mode,
      preview_url: previewUrl.value || null,
    })
    ui.notify(mode === 'list' ? '列表预览已刷新' : '正文预览已刷新', 'success')
  } catch (error) {
    preview.value = null
    ui.notify(error instanceof Error ? error.message : '预览失败', 'error')
  } finally {
    previewing.value = null
  }
}

onMounted(loadData)
</script>

<template>
  <div class="view-stack">
    <section class="hero-banner">
      <div>
        <p class="hero-banner__eyebrow">Rule Studio</p>
        <h3>选择器在这里调准，后面的抓取、翻译、汇总才会真正稳定。</h3>
      </div>
      <div v-if="source" class="hero-inline">
        <StatusBadge :label="source.source_type" tone="info" />
        <span>{{ source.name }}</span>
      </div>
    </section>

    <div class="panel-grid panel-grid--two">
      <PanelCard eyebrow="Selectors" title="抓取规则" accent="copper">
        <div v-if="loading" class="skeleton-block skeleton-block--tall" />
        <form v-else class="shell-form" @submit.prevent="saveRules">
          <div class="shell-form__grid">
            <label class="shell-field">
              <span>列表项选择器</span>
              <input v-model="form.list_item_selector" class="shell-input" type="text" placeholder="article, .post-item" />
            </label>

            <label class="shell-field">
              <span>链接选择器</span>
              <input v-model="form.link_selector" class="shell-input" type="text" placeholder="a[href]" />
            </label>

            <label class="shell-field">
              <span>标题选择器</span>
              <input v-model="form.title_selector" class="shell-input" type="text" />
            </label>

            <label class="shell-field">
              <span>发布时间选择器</span>
              <input v-model="form.published_at_selector" class="shell-input" type="text" />
            </label>

            <label class="shell-field">
              <span>作者选择器</span>
              <input v-model="form.author_selector" class="shell-input" type="text" />
            </label>

            <label class="shell-field">
              <span>正文选择器</span>
              <input v-model="form.content_selector" class="shell-input" type="text" placeholder="article, .post-content" />
            </label>

            <label class="shell-field shell-field--full">
              <span>预览地址</span>
              <input v-model="previewUrl" class="shell-input" type="url" />
            </label>

            <label class="shell-field shell-field--full">
              <span>移除节点</span>
              <textarea v-model="form.remove_selectors" class="shell-textarea" rows="4" placeholder=".share, .ad, script" />
            </label>

            <label class="shell-field shell-field--full">
              <span>请求头 JSON</span>
              <textarea
                v-model="form.request_headers_json"
                class="shell-textarea shell-textarea--mono"
                rows="6"
                placeholder='{"User-Agent": "Mozilla/5.0"}'
              />
            </label>
          </div>

          <div class="form-actions">
            <button class="shell-button" type="submit" :disabled="saving || loading">
              {{ saving ? '保存中...' : '保存规则' }}
            </button>
            <button class="shell-button shell-button--secondary" type="button" :disabled="previewing !== null" @click="runPreview('list')">
              {{ previewing === 'list' ? '预览中...' : '预览列表' }}
            </button>
            <button class="shell-button shell-button--ghost" type="button" :disabled="previewing !== null" @click="runPreview('article')">
              {{ previewing === 'article' ? '预览中...' : '预览正文' }}
            </button>
          </div>
        </form>
      </PanelCard>

      <PanelCard eyebrow="Preview" title="实时预览" accent="ink">
        <template v-if="preview">
          <div class="preview-meta">
            <div>
              <span>请求地址</span>
              <strong>{{ preview.request_url }}</strong>
            </div>
            <div v-if="preview.article_url">
              <span>正文地址</span>
              <strong>{{ preview.article_url }}</strong>
            </div>
          </div>

          <template v-if="preview.mode === 'list'">
            <div class="preview-list">
              <article v-for="item in preview.items" :key="item.url" class="preview-list__item">
                <h4>{{ item.title }}</h4>
                <a :href="item.url" target="_blank" rel="noreferrer">{{ item.url }}</a>
              </article>
            </div>
          </template>

          <template v-else>
            <div class="preview-article">
              <p class="muted-copy">提取长度：{{ preview.extracted_length || 0 }} 字</p>
              <pre>{{ preview.extracted_text || '没有提取到正文内容' }}</pre>
            </div>
          </template>
        </template>

        <EmptyState
          v-else
          title="还没有预览结果"
          description="保存后先点“预览列表”，确认文章入口没问题，再继续预览正文。"
        />
      </PanelCard>
    </div>
  </div>
</template>
