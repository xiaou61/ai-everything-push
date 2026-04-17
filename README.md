# 技术论坛日报

一个本地优先运行的技术内容聚合系统，支持：

- 科技类技术博客/论坛内容源管理
- RSS 与网页抓取
- 英文自动翻译、中文直接保留
- 大模型摘要、分类、标题生成
- 按天生成日报页面
- 定时推送飞书
- 简单后台管理页面

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

2. 复制 `.env.example` 为 `.env`
3. 配置 `DATABASE_URL`、`OPENAI_API_KEY`、`OPENAI_BASE_URL`
4. 启动服务：

```bash
uvicorn app.main:app --reload
```

5. 访问后台：

```text
http://127.0.0.1:8000/admin
```

## 当前后台页面

- `/admin`：仪表盘
- `/admin/sources`：内容源管理
- `/admin/sources/{id}/rules`：抓取规则配置
- `/admin/articles`：文章列表
- `/admin/models`：模型配置
- `/admin/reports`：日报管理
- `/admin/settings`：系统设置和自动调度

## 当前任务接口

- `POST /admin/api/jobs/crawl/run`
- `POST /admin/api/jobs/process/run`
- `POST /admin/api/jobs/report/run`
- `POST /admin/api/jobs/push/run`
- `POST /admin/api/scheduler/reload`

## 当前进度

当前已完成：

- 项目骨架
- 基础数据库模型
- 后台首页
- 内容源管理
- 模型配置管理
- 内容源抓取规则管理
- 手动抓取、处理、日报生成、飞书推送链路
- 系统设置页
- APScheduler 自动调度运行时
