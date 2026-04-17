<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import PanelCard from '../components/ui/PanelCard.vue'
import { api } from '../lib/api'
import { useUiStore } from '../stores/ui'
import type { SourcePayload } from '../types/admin'

const route = useRoute()
const router = useRouter()
const ui = useUiStore()

const loading = ref(false)
const saving = ref(false)

const form = ref<SourcePayload>({
  name: '',
  slug: '',
  site_url: '',
  source_type: 'web',
  feed_url: null,
  list_url: null,
  language_hint: 'zh',
  category: '',
  enabled: true,
  include_in_daily: true,
  crawl_interval_minutes: 60,
})

const isEditing = computed(() => Boolean(route.params.id))
const sourceId = computed(() => Number(route.params.id))

const sourceGuide = computed(() =>
  form.value.source_type === 'rss'
    ? 'RSS 类型更适合官方博客或支持 Feed 的论坛。'
    : '网页类型适合列表页抓取，后续可继续配置选择器规则。',
)

function normalizePayload(): SourcePayload {
  return {
    ...form.value,
    feed_url: form.value.feed_url || null,
    list_url: form.value.list_url || null,
    language_hint: form.value.language_hint || null,
    category: form.value.category || null,
  }
}

async function loadSource() {
  if (!isEditing.value) {
    return
  }

  loading.value = true

  try {
    const source = await api.getSource(sourceId.value)
    form.value = {
      name: source.name,
      slug: source.slug,
      site_url: source.site_url,
      source_type: source.source_type,
      feed_url: source.feed_url,
      list_url: source.list_url,
      language_hint: source.language_hint,
      category: source.category,
      enabled: source.enabled,
      include_in_daily: source.include_in_daily,
      crawl_interval_minutes: source.crawl_interval_minutes,
    }
  } catch (error) {
    ui.notify(error instanceof Error ? error.message : '加载内容源失败', 'error')
  } finally {
    loading.value = false
  }
}

async function submitForm() {
  saving.value = true

  try {
    if (isEditing.value) {
      await api.updateSource(sourceId.value, normalizePayload())
      ui.notify('内容源已更新', 'success')
    } else {
      await api.createSource(normalizePayload())
      ui.notify('内容源已创建', 'success')
    }

    await router.push('/sources')
  } catch (error) {
    ui.notify(error instanceof Error ? error.message : '保存内容源失败', 'error')
  } finally {
    saving.value = false
  }
}

onMounted(loadSource)
</script>

<template>
  <div class="view-stack">
    <section class="hero-banner">
      <div>
        <p class="hero-banner__eyebrow">{{ isEditing ? 'Refine Source' : 'Add New Source' }}</p>
        <h3>{{ isEditing ? '把已有来源调到最适合自动化抓取的状态。' : '先把入口配清楚，后面规则和日报才会稳定。' }}</h3>
      </div>
      <button class="shell-button shell-button--ghost" type="button" @click="router.push('/sources')">
        返回列表
      </button>
    </section>

    <div class="panel-grid panel-grid--two">
      <PanelCard eyebrow="Source Form" :title="isEditing ? '编辑内容源' : '新增内容源'" accent="copper">
        <form class="shell-form" @submit.prevent="submitForm">
          <div class="shell-form__grid">
            <label class="shell-field">
              <span>名称</span>
              <input v-model="form.name" class="shell-input" type="text" required />
            </label>

            <label class="shell-field">
              <span>Slug</span>
              <input v-model="form.slug" class="shell-input" type="text" required />
            </label>

            <label class="shell-field">
              <span>类型</span>
              <select v-model="form.source_type" class="shell-select">
                <option value="web">web</option>
                <option value="rss">rss</option>
              </select>
            </label>

            <label class="shell-field">
              <span>语言提示</span>
              <select v-model="form.language_hint" class="shell-select">
                <option value="">未指定</option>
                <option value="zh">zh</option>
                <option value="en">en</option>
              </select>
            </label>

            <label class="shell-field shell-field--full">
              <span>站点地址</span>
              <input v-model="form.site_url" class="shell-input" type="url" required />
            </label>

            <label class="shell-field shell-field--full">
              <span>列表页地址</span>
              <input v-model="form.list_url" class="shell-input" type="url" placeholder="https://example.com/blog" />
            </label>

            <label class="shell-field shell-field--full">
              <span>Feed 地址</span>
              <input v-model="form.feed_url" class="shell-input" type="url" placeholder="https://example.com/feed.xml" />
            </label>

            <label class="shell-field">
              <span>分类</span>
              <input v-model="form.category" class="shell-input" type="text" placeholder="AI、后端、工程效率" />
            </label>

            <label class="shell-field">
              <span>抓取间隔（分钟）</span>
              <input v-model="form.crawl_interval_minutes" class="shell-input" type="number" min="5" max="1440" />
            </label>

            <label class="toggle-field">
              <input v-model="form.enabled" type="checkbox" />
              <span>启用该内容源</span>
            </label>

            <label class="toggle-field">
              <input v-model="form.include_in_daily" type="checkbox" />
              <span>允许进入日报</span>
            </label>
          </div>

          <div class="form-actions">
            <button class="shell-button" type="submit" :disabled="saving || loading">
              {{ saving ? '保存中...' : isEditing ? '保存修改' : '创建内容源' }}
            </button>
            <button class="shell-button shell-button--secondary" type="button" @click="router.push('/sources')">
              取消
            </button>
          </div>
        </form>
      </PanelCard>

      <PanelCard eyebrow="Editor Notes" title="配置建议" accent="ink">
        <div v-if="loading" class="skeleton-block skeleton-block--tall" />
        <template v-else>
          <p class="muted-copy">{{ sourceGuide }}</p>
          <ul class="bullet-list">
            <li>国内中文博客直接保留原文，英文来源再走翻译模型。</li>
            <li>站点地址尽量填官网首页，列表页地址填文章归档页或栏目页。</li>
            <li>如果是网页抓取，保存后继续去“抓取规则”页配置选择器。</li>
          </ul>
        </template>
      </PanelCard>
    </div>
  </div>
</template>
