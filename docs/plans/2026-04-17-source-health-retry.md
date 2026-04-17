# 来源健康监控与失败重试 Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 为内容源抓取链路补齐自动重试、健康状态派生、后台异常提醒和展示型 README。

**Architecture:** 在 `Source` 表上做最小字段增强，将重试判定、退避时间、健康派生和状态回写集中到独立的 `source_health_service` 中，由 `crawl_service` 只负责抓取编排。前端通过扩展后的来源与仪表盘接口直接消费健康状态和告警摘要。

**Tech Stack:** Python, FastAPI, SQLAlchemy, pytest, Vue 3, Vite, TypeScript

---

### Task 1: 补测试并定义策略边界

**Files:**
- Create: `tests/services/test_source_health_service.py`
- Modify: `tests/routes/test_crawl_jobs.py`
- Modify: `tests/routes/test_sources.py`
- Modify: `tests/routes/test_admin_data_routes.py`

**Step 1: 写失败测试**

- 为健康策略服务补充：
  - 可重试错误识别
  - 不可重试错误识别
  - 成功回写
  - 失败回写
  - 健康派生
- 为路由补充：
  - 来源接口新增健康字段
  - Dashboard 新增异常来源摘要
  - 抓取失败后的重试计数与冷却信息

**Step 2: 运行测试确认失败**

Run: `python -m pytest tests/services/test_source_health_service.py tests/routes/test_crawl_jobs.py tests/routes/test_sources.py tests/routes/test_admin_data_routes.py -q`

Expected: 因缺少新服务和新字段而失败

### Task 2: 实现后端来源健康策略

**Files:**
- Create: `app/services/source_health_service.py`
- Modify: `app/db/models/source.py`
- Modify: `app/core/schema_upgrade.py`
- Modify: `app/schemas/source.py`
- Modify: `app/services/source_service.py`
- Modify: `app/services/crawl_service.py`
- Modify: `app/services/dashboard_service.py`

**Step 1: 新增最小数据字段**

- 在 `Source` 模型增加：
  - `last_success_at`
  - `last_failure_at`
  - `last_retry_attempts`
- 在 schema upgrade 中补列

**Step 2: 抽离健康策略服务**

- 新建 `source_health_service.py`
- 提供：
  - `should_retry_crawl_error`
  - `build_retry_schedule`
  - `derive_source_health`
  - `apply_source_crawl_success`
  - `apply_source_crawl_failure`
  - `serialize_source_health`

**Step 3: 收敛抓取服务**

- `crawl_service.py` 改为调用独立策略层
- 在来源处于冷却窗口时跳过抓取
- 汇总跳过/失败/成功来源

**Step 4: 扩展 Dashboard 聚合**

- 返回来源健康统计与异常来源摘要

### Task 3: 更新前端来源页与仪表盘

**Files:**
- Modify: `frontend/src/types/admin.ts`
- Modify: `frontend/src/components/ui/StatusBadge.vue`
- Modify: `frontend/src/views/SourcesView.vue`
- Modify: `frontend/src/views/DashboardView.vue`
- Modify: `frontend/src/styles/base.css`

**Step 1: 扩展类型定义**

- 加入健康字段、摘要结构和告警列表类型

**Step 2: 调整状态徽标**

- 支持 `healthy` / `warning` / `cooling` / `failed` / `idle`
- 优先显示后端返回的中文 label

**Step 3: 更新来源页**

- 增加健康筛选
- 展示最近成功、最近失败、下次重试、重试次数

**Step 4: 更新仪表盘**

- 增加异常来源摘要卡片和最近失败来源列表

### Task 4: 重写 README 与整理注释

**Files:**
- Modify: `README.md`

**Step 1: 改成开源展示型中文 README**

- 简介
- 功能亮点
- 技术栈
- 架构流程
- 页面能力
- 快速开始
- 配置说明
- Roadmap
- 开源说明

**Step 2: 对新加策略层补中文注释**

- 只在关键逻辑处加简洁中文注释

### Task 5: 验证与提交

**Files:**
- Modify: `git index`

**Step 1: 运行后端测试**

Run: `python -m pytest -q`

Expected: 全部通过

**Step 2: 运行前端构建**

Run: `npm run build`

Workdir: `frontend`

Expected: 构建成功

**Step 3: 做一次最小烟测**

- 启动本地服务
- 请求 `/health`
- 请求 `/admin/api/dashboard`
- 请求 `/admin/api/sources`

**Step 4: 提交**

Run:

```bash
git add .
git commit -m "feat: add source health monitoring and retry workflow"
```
