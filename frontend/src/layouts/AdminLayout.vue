<script setup lang="ts">
import { computed } from 'vue'
import { RouterLink, RouterView, useRoute } from 'vue-router'

const route = useRoute()

const navItems = [
  { label: '总览', to: '/dashboard', names: ['dashboard'], index: '01' },
  { label: '内容源', to: '/sources', names: ['sources', 'source-new', 'source-edit', 'source-rules'], index: '02' },
  { label: '文章池', to: '/articles', names: ['articles'], index: '03' },
  { label: '模型', to: '/models', names: ['models'], index: '04' },
  { label: '日报', to: '/reports', names: ['reports'], index: '05' },
  { label: '任务', to: '/jobs', names: ['jobs'], index: '06' },
  { label: '数据', to: '/database', names: ['database'], index: '07' },
  { label: '设置', to: '/settings', names: ['settings'], index: '08' },
]

const pageTitle = computed(() => String(route.meta.title || '编辑部控制台'))
const pageSubtitle = computed(() => String(route.meta.subtitle || '技术论坛日报后台'))
const todayReportPath = computed(() => `/daily/${new Date().toISOString().slice(0, 10)}`)
const todayLabel = computed(() =>
  new Intl.DateTimeFormat('zh-CN', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
    weekday: 'long',
  }).format(new Date()),
)

function isActive(names: string[]): boolean {
  return names.includes(String(route.name || ''))
}
</script>

<template>
  <div class="admin-shell">
    <aside class="admin-sidebar">
      <div class="brand-card">
        <p class="brand-card__eyebrow">AI Daily Skill</p>
        <h1>编辑部控制台</h1>
        <p class="brand-card__text">
          把论坛、博客、日报生成和飞书推送串成一条顺滑的自动化流水线。
        </p>
      </div>

      <nav class="nav-stack">
        <RouterLink
          v-for="item in navItems"
          :key="item.to"
          :to="item.to"
          class="nav-link"
          :class="{ 'is-active': isActive(item.names) }"
        >
          <span class="nav-link__index">{{ item.index }}</span>
          <span class="nav-link__label">{{ item.label }}</span>
        </RouterLink>
      </nav>

      <div class="sidebar-note">
        <p class="sidebar-note__label">工作流</p>
        <p>抓取 -> 翻译/保留中文 -> 汇总 -> 生成日报 -> 推送飞书</p>
      </div>
    </aside>

    <main class="admin-main">
      <header class="topbar">
        <div>
          <p class="topbar__eyebrow">{{ todayLabel }}</p>
          <h2>{{ pageTitle }}</h2>
          <p class="topbar__text">{{ pageSubtitle }}</p>
        </div>
        <a class="topbar__public-link" :href="todayReportPath" target="_blank" rel="noreferrer">
          查看公开日报
        </a>
      </header>

      <RouterView v-slot="{ Component }">
        <Transition name="page-fade" mode="out-in">
          <component :is="Component" />
        </Transition>
      </RouterView>
    </main>
  </div>
</template>
