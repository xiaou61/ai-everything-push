# Admin Vue Migration Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 将现有 FastAPI/Jinja 后台管理台迁移为 `Vue 3 + Vite` 独立前端项目，并保留 FastAPI 作为 API 和公开日报服务。

**Architecture:** 新建 `frontend/` 作为独立 SPA，使用 `Vue 3 + Vue Router + Pinia` 承载 `/admin*` 管理台。FastAPI 保留现有业务逻辑，新增管理台所需 JSON API，并提供 SPA 回退入口以便本地联调和后续构建部署。

**Tech Stack:** Vue 3、Vite、TypeScript、Vue Router、Pinia、FastAPI、SQLAlchemy、APScheduler

---

### Task 1: 初始化 Vue 前端工程

**Files:**
- Create: `frontend/package.json`
- Create: `frontend/vite.config.ts`
- Create: `frontend/tsconfig.json`
- Create: `frontend/index.html`
- Create: `frontend/src/main.ts`
- Create: `frontend/src/App.vue`

**Step 1: 创建 Vite Vue 项目骨架**

Run: `npm create vite@latest frontend -- --template vue-ts`
Expected: 生成 Vue 3 + TypeScript 前端目录

**Step 2: 安装依赖**

Run: `npm install`
Expected: 成功安装基础依赖

**Step 3: 安装路由和状态库**

Run: `npm install vue-router pinia`
Expected: 增加前端运行时依赖

**Step 4: 配置 Vite 代理与 /admin/ base**

实现 `vite.config.ts`，为 `/admin/api`、`/daily`、`/health` 配置代理，设置打包输出目录和 `base`

**Step 5: 验证前端能启动**

Run: `npm run build`
Expected: 前端可构建

### Task 2: 补齐后台 JSON API

**Files:**
- Modify: `app/api/routes/*.py`
- Create: `app/api/routes/dashboard_api.py`
- Create: `app/api/routes/articles_api.py`
- Create: `app/api/routes/jobs_api.py`
- Create: `app/api/routes/reports_api.py`

**Step 1: 给仪表盘暴露 JSON 数据**

新增 dashboard stats、recent jobs、scheduler status 的 API

**Step 2: 给文章、日报、任务日志提供列表 API**

为前端列表页提供稳定 JSON 接口

**Step 3: 保留现有业务 API 并整理命名**

避免破坏现有抓取、处理、生成、推送接口

**Step 4: 为 SPA 提供回退入口**

必要时让 FastAPI 在构建后可回退到 `frontend/dist/index.html`

**Step 5: 运行测试**

Run: `pytest -q`
Expected: 后端测试通过

### Task 3: 实现 Vue 管理台骨架和视觉系统

**Files:**
- Create: `frontend/src/router/index.ts`
- Create: `frontend/src/stores/*.ts`
- Create: `frontend/src/layouts/AdminLayout.vue`
- Create: `frontend/src/styles/*.css`
- Create: `frontend/src/components/ui/*.vue`

**Step 1: 定义全局布局**

实现左侧导航、顶部标题区、内容区的控制台布局

**Step 2: 建立视觉变量**

定义主题色、字体、阴影、状态色、按钮和表格风格

**Step 3: 构建基础组件**

包括卡片、按钮、状态标签、表格容器、空状态、表单字段

**Step 4: 实现统一 API 客户端**

使用 `fetch` 或轻量封装处理请求和错误

**Step 5: 构建通过**

Run: `npm run build`
Expected: 无 TS/Vue 编译错误

### Task 4: 迁移后台页面到 Vue

**Files:**
- Create: `frontend/src/views/*.vue`
- Modify: `frontend/src/router/index.ts`

**Step 1: 迁移仪表盘**

展示统计、最近任务、手动任务触发和调度状态

**Step 2: 迁移内容源管理与编辑**

实现列表、新增、编辑和启停操作

**Step 3: 迁移抓取规则页**

支持保存规则与预览列表/正文

**Step 4: 迁移文章、模型、日报、任务日志、系统设置**

把当前 Jinja 管理页全部迁到 Vue

**Step 5: 验证主要页面**

Run: `npm run build`
Expected: 全部页面编译通过

### Task 5: 清理旧后台入口并更新文档

**Files:**
- Modify: `app/main.py`
- Modify: `README.md`
- Modify: `docs/plans/...`

**Step 1: 让 /admin 指向 Vue SPA**

保留 `/daily/*` 公开日报页不动

**Step 2: 取消旧 Jinja admin 页面路由**

避免 `/admin` 与 SPA 冲突

**Step 3: 更新本地启动文档**

写清楚前后端分别如何启动

**Step 4: 全量验证**

Run:
- `pytest -q`
- `npm run build`

Expected: 后端测试通过，前端构建通过
