import { createRouter, createWebHistory } from 'vue-router'

import DashboardView from '../views/DashboardView.vue'
import ReportDetailView from '../views/ReportDetailView.vue'
import ReportsView from '../views/ReportsView.vue'
import SourcesView from '../views/SourcesView.vue'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', name: 'dashboard', component: DashboardView },
    { path: '/reports', name: 'reports', component: ReportsView },
    { path: '/reports/:digestDate', name: 'report-detail', component: ReportDetailView },
    { path: '/sources', name: 'sources', component: SourcesView },
  ],
})

export default router

