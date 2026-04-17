# Forum Digest Platform

一个基于 `FastAPI + MySQL + Vue3` 的论坛情报聚合平台，面向“每天汇总论坛与资讯内容、英文自动翻译、中文保留原文、按分类生成日报、网站展示并推送到飞书”的场景。

## 已实现能力

- 采集层：
  支持 `RSS`、`JSON API`、`HTML 规则抓取` 三类数据源。
- 处理层：
  自动识别语言，英文内容自动翻译成中文，中文内容不翻译。
- 汇总层：
  对每日文章按分类聚合，生成日报 headline、overview 和分类 sections。
- 展示层：
  Vue 3 网站提供概览页、日报列表/详情页、数据源管理页。
- 推送层：
  支持把指定日报推送到飞书自定义机器人。
- 调度层：
  APScheduler 定时同步数据源，并按 CRON 定时生成/推送日报。

## 技术栈

- 后端：`FastAPI`、`SQLAlchemy`、`MySQL`、`APScheduler`
- 采集：`httpx`、`feedparser`、`BeautifulSoup`
- 处理：`langdetect`、`deep-translator`
- 前端：`Vue 3`、`TypeScript`、`Vue Router`、`Pinia`、`Vite`

## 项目结构

```text
backend/
  app/
    api/            # FastAPI 路由
    core/           # 配置、数据库、调度器
    models/         # SQLAlchemy 模型
    schemas/        # Pydantic 响应模型
    services/       # 采集、翻译、分类、汇总、飞书
  tests/            # 后端单元测试
frontend/
  src/
    components/     # 页面组件
    composables/    # Vue 组合式逻辑
    router/         # 路由
    views/          # 页面级视图
Dockerfile
docker-compose.yml
```

## 快速启动

### 方式一：Docker Compose

```bash
docker compose up --build
```

启动后访问：

- 网站：`http://localhost:8000`
- API 文档：`http://localhost:8000/docs`

### 方式二：本地开发

后端：

```bash
cd backend
python -m pip install -e .[dev]
uvicorn app.main:app --reload
```

前端：

```bash
cd frontend
npm install
npm run dev
```

如果前端本地开发独立运行，默认访问：

- 前端：`http://localhost:5173`
- 后端：`http://localhost:8000`

## 环境变量

可参考根目录 [`.env.example`](/e:/ai-everything-push/.env.example)。

关键配置：

- `MYSQL_*`：MySQL 连接信息
- `CORS_ORIGINS`：前端访问白名单
- `SOURCE_SYNC_INTERVAL_MINUTES`：自动同步数据源间隔
- `DAILY_DIGEST_CRON`：日报生成/推送时间
- `DAILY_DIGEST_SITE_BASE_URL`：飞书卡片里的可访问网址前缀
- `FEISHU_WEBHOOK_URL`：飞书机器人 webhook
- `OPENAI_*`：可选，用于更稳定的翻译能力

## 数据源配置说明

### 1. RSS

只需要填写：

- `name`
- `url`
- `source_type = rss`

### 2. JSON API

`parser_config` 示例：

```json
{
  "items_path": "data.items",
  "title_field": "title",
  "link_field": "url",
  "content_field": "summary",
  "published_at_field": "published_at",
  "external_id_field": "id"
}
```

### 3. HTML 规则抓取

`parser_config` 示例：

```json
{
  "item_selector": ".topic-list-item",
  "title_selector": ".topic-title",
  "link_selector": ".topic-title a",
  "content_selector": ".topic-excerpt",
  "published_at_selector": "time",
  "author_selector": ".topic-author"
}
```

## 常用接口

- `GET /api/v1/dashboard`
- `GET /api/v1/sources`
- `POST /api/v1/sources`
- `POST /api/v1/sources/sync`
- `POST /api/v1/sources/{source_id}/sync`
- `GET /api/v1/digests`
- `POST /api/v1/digests/generate`
- `GET /api/v1/digests/by-date/{digest_date}`
- `POST /api/v1/digests/{digest_id}/push`

## 飞书推送说明

1. 在飞书群里创建自定义机器人。
2. 拿到 webhook 后写入 `FEISHU_WEBHOOK_URL`。
3. 设置 `DAILY_DIGEST_SITE_BASE_URL` 为你的可访问网址。
4. 定时任务到点后会自动生成并推送日报，也可以在前端日报页手动点击“推送到飞书”。

## 关于“可访问的网址”

当前项目已经具备“单网址访问”的部署结构：

- Vue 构建产物会在容器里被 FastAPI 一并托管
- 只需要把容器部署到云服务器并放开 `8000` 端口，或者再接一个 Nginx / Caddy 反向代理
- 把 `DAILY_DIGEST_SITE_BASE_URL` 配成你的公网域名，例如 `https://digest.example.com`

这样飞书消息里的“查看完整日报”链接就会跳到真实可访问网页。
