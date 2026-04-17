import { createRouter, createWebHashHistory } from 'vue-router'

import AdminLayout from '../layouts/AdminLayout.vue'

const router = createRouter({
  history: createWebHashHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      component: AdminLayout,
      children: [
        {
          path: '',
          redirect: '/dashboard',
        },
        {
          path: 'dashboard',
          name: 'dashboard',
          component: () => import('../views/DashboardView.vue'),
          meta: {
            title: '编辑部总览',
            subtitle: '抓取、处理、生成与飞书推送状态一眼看清。',
          },
        },
        {
          path: 'sources',
          name: 'sources',
          component: () => import('../views/SourcesView.vue'),
          meta: {
            title: '内容源管理',
            subtitle: '维护技术博客、论坛和抓取入口。',
          },
        },
        {
          path: 'sources/new',
          name: 'source-new',
          component: () => import('../views/SourceFormView.vue'),
          meta: {
            title: '新增内容源',
            subtitle: '添加新的站点、语言和采集策略。',
          },
        },
        {
          path: 'sources/:id/edit',
          name: 'source-edit',
          component: () => import('../views/SourceFormView.vue'),
          meta: {
            title: '编辑内容源',
            subtitle: '调整抓取入口、频率和日报收录策略。',
          },
        },
        {
          path: 'sources/:id/rules',
          name: 'source-rules',
          component: () => import('../views/SourceRulesView.vue'),
          meta: {
            title: '抓取规则调试',
            subtitle: '配置选择器并立即预览抓取结果。',
          },
        },
        {
          path: 'articles',
          name: 'articles',
          component: () => import('../views/ArticlesView.vue'),
          meta: {
            title: '文章池',
            subtitle: '查看抓取结果、语言状态与 AI 处理概览。',
          },
        },
        {
          path: 'models',
          name: 'models',
          component: () => import('../views/ModelsView.vue'),
          meta: {
            title: '模型配置',
            subtitle: '管理翻译、摘要、分类与标题生成模型。',
          },
        },
        {
          path: 'reports',
          name: 'reports',
          component: () => import('../views/ReportsView.vue'),
          meta: {
            title: '日报发布台',
            subtitle: '生成日报、预览公开页并执行飞书推送。',
          },
        },
        {
          path: 'jobs',
          name: 'jobs',
          component: () => import('../views/JobsView.vue'),
          meta: {
            title: '任务日志',
            subtitle: '跟踪定时调度和手动触发任务的执行结果。',
          },
        },
        {
          path: 'settings',
          name: 'settings',
          component: () => import('../views/SettingsView.vue'),
          meta: {
            title: '系统设置',
            subtitle: '调整调度周期、日报上限与运行开关。',
          },
        },
      ],
    },
  ],
})

export default router
