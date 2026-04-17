# 技术论坛日报

一个本地优先运行的技术内容聚合系统，支持：

- 科技类技术博客/论坛内容源管理
- RSS 与网页抓取
- 英文自动翻译、中文直接保留
- 大模型摘要、分类、标题生成
- 按天生成日报页面
- 定时推送飞书
- Vue 3 后台管理台

## 技术栈

- Python
- FastAPI
- MySQL
- SQLAlchemy
- LangChain
- APScheduler

## 本地启动

1. 创建虚拟环境并安装依赖

```bash
pip install -e ".[dev]"
```

2. 安装前端依赖

```bash
cd frontend
npm install
cd ..
```

3. 复制 `.env.example` 为 `.env`
4. 配置 `DATABASE_URL`、`AIWANWU_API_KEY`、`FEISHU_WEBHOOK_URL`
5. 启动后端：

```bash
uvicorn app.main:app --reload
```

6. 前端开发模式再开一个终端：

```bash
cd frontend
npm run dev
```

7. 访问后台：

```text
开发模式：
http://127.0.0.1:5173/admin/

构建后由 FastAPI 托管：
http://127.0.0.1:8000/admin/
```

## 前端构建

```bash
cd frontend
npm run build
```

构建完成后，FastAPI 会直接托管 `frontend/dist`，访问 `/admin/` 即可。

## 当前后台能力

- `/admin/`：Vue 控制台入口
- `/admin/#/dashboard`：仪表盘
- `/admin/#/sources`：内容源管理
- `/admin/#/sources/:id/rules`：抓取规则配置与预览
- `/admin/#/articles`：文章列表
- `/admin/#/models`：模型配置
- `/admin/#/reports`：日报管理
- `/admin/#/jobs`：任务日志
- `/admin/#/settings`：系统设置和自动调度

## 当前任务接口

- `POST /admin/api/jobs/crawl/run`
- `POST /admin/api/jobs/process/run`
- `POST /admin/api/jobs/report/run`
- `POST /admin/api/jobs/push/run`
- `POST /admin/api/scheduler/reload`
- `GET /admin/api/integrations/feishu/status`
- `POST /admin/api/integrations/feishu/test`

## 飞书联调

- 飞书机器人 Webhook 继续通过 `.env` 里的 `FEISHU_WEBHOOK_URL` 配置
- 后台设置页可以直接查看当前 webhook 是否已配置
- 后台设置页支持发送一条测试消息，用来确认 webhook 是否可用
- 真正的日报推送仍然走 `POST /admin/api/jobs/push/run`

## 当前进度

当前已完成：

- 项目骨架
- FastAPI + MySQL + SQLAlchemy 后端链路
- Vue 3 + Vite 独立后台前端
- 内容源管理、抓取规则预览、模型配置
- 手动抓取、处理、日报生成、飞书推送链路
- 文章池、日报管理、任务日志、系统设置页
- APScheduler 自动调度运行时
