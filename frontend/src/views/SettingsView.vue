<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'

import PanelCard from '../components/ui/PanelCard.vue'
import StatusBadge from '../components/ui/StatusBadge.vue'
import { api } from '../lib/api'
import { useUiStore } from '../stores/ui'
import type { FeishuStatus, SchedulerStatus, SystemSetting } from '../types/admin'

const ui = useUiStore()

const loading = ref(true)
const saving = ref(false)
const reloading = ref(false)
const testingFeishu = ref(false)
const settings = ref<SystemSetting[]>([])
const schedulerStatus = ref<SchedulerStatus | null>(null)
const feishuStatus = ref<FeishuStatus | null>(null)

const form = ref({
  schedulerEnabled: true,
  schedulerTimezone: 'Asia/Shanghai',
  schedulerCrawlCron: '0 */2 * * *',
  schedulerProcessCron: '10 */2 * * *',
  schedulerReportCron: '0 18 * * *',
  schedulerPushCron: '5 18 * * *',
  reportMaxArticlesPerDay: '30',
})

const feishuForm = ref({
  title: '技术论坛日报联调消息',
  message: '这是一条来自后台的飞书测试消息，用于确认机器人 webhook 是否可用。',
})

const extraSettings = computed(() =>
  settings.value.filter(
    (item) =>
      ![
        'scheduler.enabled',
        'scheduler.timezone',
        'scheduler.crawl_cron',
        'scheduler.process_cron',
        'scheduler.report_cron',
        'scheduler.push_cron',
        'report.max_articles_per_day',
      ].includes(item.setting_key),
  ),
)

function applySettings(items: SystemSetting[]) {
  settings.value = items
  const valueMap = Object.fromEntries(items.map((item) => [item.setting_key, item.setting_value]))

  form.value = {
    schedulerEnabled: (valueMap['scheduler.enabled'] || 'true') === 'true',
    schedulerTimezone: valueMap['scheduler.timezone'] || 'Asia/Shanghai',
    schedulerCrawlCron: valueMap['scheduler.crawl_cron'] || '0 */2 * * *',
    schedulerProcessCron: valueMap['scheduler.process_cron'] || '10 */2 * * *',
    schedulerReportCron: valueMap['scheduler.report_cron'] || '0 18 * * *',
    schedulerPushCron: valueMap['scheduler.push_cron'] || '5 18 * * *',
    reportMaxArticlesPerDay: valueMap['report.max_articles_per_day'] || '30',
  }
}

async function loadSettings() {
  loading.value = true

  try {
    const [settingList, scheduler, feishu] = await Promise.all([
      api.getSettings(),
      api.getSchedulerStatus(),
      api.getFeishuStatus(),
    ])
    applySettings(settingList)
    schedulerStatus.value = scheduler
    feishuStatus.value = feishu
  } catch (error) {
    ui.notify(error instanceof Error ? error.message : '加载系统设置失败', 'error')
  } finally {
    loading.value = false
  }
}

async function saveSettings() {
  saving.value = true

  try {
    const saved = await api.saveSettingsBatch([
      {
        setting_key: 'scheduler.enabled',
        setting_value: String(form.value.schedulerEnabled),
        description: '是否启用 APScheduler 自动调度',
      },
      {
        setting_key: 'scheduler.timezone',
        setting_value: form.value.schedulerTimezone,
        description: '调度任务时区',
      },
      {
        setting_key: 'scheduler.crawl_cron',
        setting_value: form.value.schedulerCrawlCron,
        description: '抓取任务 cron',
      },
      {
        setting_key: 'scheduler.process_cron',
        setting_value: form.value.schedulerProcessCron,
        description: '文章处理任务 cron',
      },
      {
        setting_key: 'scheduler.report_cron',
        setting_value: form.value.schedulerReportCron,
        description: '日报生成任务 cron',
      },
      {
        setting_key: 'scheduler.push_cron',
        setting_value: form.value.schedulerPushCron,
        description: '飞书推送任务 cron',
      },
      {
        setting_key: 'report.max_articles_per_day',
        setting_value: form.value.reportMaxArticlesPerDay,
        description: '日报每天最多展示文章数',
      },
    ])

    applySettings(saved)
    schedulerStatus.value = await api.getSchedulerStatus()
    ui.notify('系统设置已保存', 'success')
  } catch (error) {
    ui.notify(error instanceof Error ? error.message : '保存系统设置失败', 'error')
  } finally {
    saving.value = false
  }
}

async function reloadScheduler() {
  reloading.value = true

  try {
    schedulerStatus.value = await api.reloadScheduler()
    ui.notify('调度器已重新加载', 'success')
  } catch (error) {
    ui.notify(error instanceof Error ? error.message : '重载调度器失败', 'error')
  } finally {
    reloading.value = false
  }
}

async function sendFeishuTest() {
  testingFeishu.value = true

  try {
    const result = await api.sendFeishuTestMessage(feishuForm.value)
    ui.notify(result.message, result.status === 'success' ? 'success' : 'error')
    feishuStatus.value = await api.getFeishuStatus()
  } catch (error) {
    ui.notify(error instanceof Error ? error.message : '发送飞书测试消息失败', 'error')
  } finally {
    testingFeishu.value = false
  }
}

onMounted(loadSettings)
</script>

<template>
  <div class="view-stack">
    <section class="hero-banner">
      <div>
        <p class="hero-banner__eyebrow">System Control</p>
        <h3>这里控制自动化的节奏和上限，适合先跑通再逐步压缩调度周期。</h3>
      </div>
    </section>

    <div class="panel-grid panel-grid--two">
      <PanelCard eyebrow="Scheduler" title="调度状态" accent="ink">
        <template v-if="schedulerStatus">
          <div class="status-list">
            <div class="status-list__item">
              <span>可用</span>
              <StatusBadge :label="schedulerStatus.available ? 'enabled' : 'disabled'" />
            </div>
            <div class="status-list__item">
              <span>运行中</span>
              <StatusBadge :label="schedulerStatus.running ? 'running' : 'stopped'" />
            </div>
            <div class="status-list__item">
              <span>已注册任务</span>
              <strong>{{ schedulerStatus.jobs.length }}</strong>
            </div>
          </div>
          <p class="muted-copy">{{ schedulerStatus.message }}</p>
          <button class="shell-button shell-button--secondary" type="button" :disabled="reloading" @click="reloadScheduler">
            {{ reloading ? '重载中...' : '重新加载调度器' }}
          </button>
        </template>
      </PanelCard>

      <PanelCard eyebrow="Feishu" title="飞书推送联调" accent="copper">
        <template v-if="feishuStatus">
          <div class="status-list">
            <div class="status-list__item">
              <span>Webhook 状态</span>
              <StatusBadge :label="feishuStatus.configured ? 'enabled' : 'disabled'" />
            </div>
            <div class="status-list__item">
              <span>当前配置</span>
              <strong>{{ feishuStatus.masked_webhook || '未配置' }}</strong>
            </div>
            <div class="status-list__item">
              <span>日报基址</span>
              <strong>{{ feishuStatus.site_base_url }}</strong>
            </div>
          </div>
          <p class="muted-copy">{{ feishuStatus.message }}</p>

          <form class="shell-form" @submit.prevent="sendFeishuTest">
            <div class="shell-form__grid">
              <label class="shell-field shell-field--full">
                <span>测试标题</span>
                <input v-model="feishuForm.title" class="shell-input" type="text" maxlength="100" />
              </label>

              <label class="shell-field shell-field--full">
                <span>测试消息</span>
                <textarea v-model="feishuForm.message" class="shell-textarea" rows="4" maxlength="500" />
              </label>
            </div>

            <div class="form-actions">
              <button
                class="shell-button shell-button--secondary"
                type="submit"
                :disabled="testingFeishu || !feishuStatus.configured"
              >
                {{ testingFeishu ? '发送中...' : '发送飞书测试消息' }}
              </button>
            </div>
          </form>
        </template>
      </PanelCard>
    </div>

    <PanelCard eyebrow="Runtime Config" title="系统设置">
      <div v-if="loading" class="skeleton-block skeleton-block--tall" />
      <form v-else class="shell-form" @submit.prevent="saveSettings">
        <div class="shell-form__grid">
          <label class="toggle-field">
            <input v-model="form.schedulerEnabled" type="checkbox" />
            <span>启用自动调度</span>
          </label>

          <label class="shell-field">
            <span>时区</span>
            <input v-model="form.schedulerTimezone" class="shell-input" type="text" />
          </label>

          <label class="shell-field">
            <span>抓取 cron</span>
            <input v-model="form.schedulerCrawlCron" class="shell-input" type="text" />
          </label>

          <label class="shell-field">
            <span>处理 cron</span>
            <input v-model="form.schedulerProcessCron" class="shell-input" type="text" />
          </label>

          <label class="shell-field">
            <span>日报 cron</span>
            <input v-model="form.schedulerReportCron" class="shell-input" type="text" />
          </label>

          <label class="shell-field">
            <span>推送 cron</span>
            <input v-model="form.schedulerPushCron" class="shell-input" type="text" />
          </label>

          <label class="shell-field">
            <span>日报最大文章数</span>
            <input v-model="form.reportMaxArticlesPerDay" class="shell-input" type="number" min="1" max="200" />
          </label>
        </div>

        <div class="form-actions">
          <button class="shell-button" type="submit" :disabled="saving">
            {{ saving ? '保存中...' : '保存设置' }}
          </button>
        </div>
      </form>
    </PanelCard>

    <PanelCard eyebrow="Advanced" title="额外配置">
      <template v-if="extraSettings.length">
        <div class="table-scroll">
          <table class="shell-table">
            <thead>
              <tr>
                <th>Key</th>
                <th>Value</th>
                <th>描述</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="item in extraSettings" :key="item.id">
                <td>{{ item.setting_key }}</td>
                <td>{{ item.setting_value }}</td>
                <td>{{ item.description || '-' }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </template>
      <p v-else class="muted-copy">目前没有额外系统配置项。</p>
    </PanelCard>

    <PanelCard eyebrow="Recommended Env" title="部署提醒">
      <ul class="bullet-list">
        <li>模型真实密钥建议放在 `.env`，数据库里只保存环境变量名。</li>
        <li>当前中转站可以统一约定 `AIWANWU_API_KEY` 和 `https://www.aiwanwu.cc/v1`。</li>
        <li>飞书 Webhook 建议继续只放在 `FEISHU_WEBHOOK_URL` 环境变量里，不写进数据库。</li>
      </ul>
    </PanelCard>
  </div>
</template>
