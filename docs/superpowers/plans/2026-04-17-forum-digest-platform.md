# Forum Digest Platform Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 构建一个基于 `FastAPI + MySQL + Vue3` 的论坛情报聚合平台，支持采集、英文翻译、分类、日报汇总、网站展示与飞书推送。

**Architecture:** 后端负责采集、清洗、翻译、分类、汇总、调度和 API 输出；前端负责日报与数据源管理界面；生产环境通过单容器挂载 Vue 构建产物对外提供统一网址。

**Tech Stack:** FastAPI, SQLAlchemy, MySQL, APScheduler, httpx, feedparser, BeautifulSoup, Vue 3, TypeScript, Vite

---

### Task 1: 后端核心领域模型与配置

**Files:**
- Create: `backend/pyproject.toml`
- Create: `backend/app/core/*.py`
- Create: `backend/app/models/*.py`

- [ ] 定义 Python 依赖、环境配置、数据库连接与数据表模型

### Task 2: 采集与内容处理服务

**Files:**
- Create: `backend/app/services/*.py`
- Create: `backend/tests/test_*.py`

- [ ] 先写语言识别、分类汇总等单元测试
- [ ] 实现 RSS / HTML / JSON 源解析、翻译、分类、摘要与日报生成

### Task 3: FastAPI API 与调度

**Files:**
- Create: `backend/app/api/**/*.py`
- Create: `backend/app/main.py`

- [ ] 暴露仪表盘、日报、数据源、手动同步、手动推送接口
- [ ] 接入 APScheduler 定时采集和日报推送任务

### Task 4: Vue 3 前端

**Files:**
- Modify: `frontend/**/*`

- [ ] 建立 Vue 3 + TypeScript + Router 的页面骨架
- [ ] 实现仪表盘、日报列表、日报详情、数据源管理页面

### Task 5: 交付与部署

**Files:**
- Create: `Dockerfile`
- Create: `docker-compose.yml`
- Modify: `README.md`

- [ ] 提供 MySQL + 应用的一键启动方式
- [ ] 说明飞书 webhook、翻译能力、生产部署与访问方式

