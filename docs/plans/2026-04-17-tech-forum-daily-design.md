# 技术论坛日报项目设计文档

**日期：** 2026-04-17

## 1. 项目目标

从 0 搭建一个本地优先运行的技术内容聚合系统，自动完成以下链路：

1. 定时采集科技类技术论坛/技术博客内容
2. 判断文章语言，英文自动翻译为中文，中文保留原文
3. 使用大模型完成摘要、分类、标题生成
4. 按天汇总生成日报
5. 生成可访问的网页页面
6. 定时推送日报链接到飞书
7. 提供一个简单后台页面，用于管理内容源、模型配置、任务日志和日报结果

## 2. 约束与原则

- 首版仅支持本地运行，不优先考虑云端部署
- 暂不做登录鉴权，默认单用户本地使用
- 技术栈固定为 `Python + FastAPI + MySQL + LangChain`
- 模型调用必须支持通过 OpenAI 兼容中转站接入
- 后台页面需要支持数据库管理，不使用纯配置文件方案
- 内容采集首版支持 `RSS + 网页抓取`
- 首版聚焦中文和英文内容
- 英文内容翻译为中文，中文内容不翻译
- 定时任务执行时间需要支持后台配置

## 3. 总体架构

项目采用单体应用架构，统一由 `FastAPI` 提供后台页面、API、静态日报访问和定时任务入口。

### 3.1 模块划分

- `Web 层`
  - 后台管理页面
  - JSON API
  - 日报 HTML 页面
- `业务层`
  - 内容源管理
  - 文章采集与解析
  - 语言识别与翻译
  - 摘要/分类/标题生成
  - 日报生成
  - 飞书推送
  - 调度与任务执行
- `数据层`
  - MySQL 持久化
  - SQLAlchemy ORM
- `集成层`
  - LangChain 模型调用
  - RSS 抓取
  - 网页抓取
  - 飞书 Webhook

### 3.2 核心执行链路

1. 定时任务读取启用中的内容源
2. 对 RSS 源抓取 Feed，对网页源抓取列表页并解析文章链接
3. 对文章链接做去重，拉取正文并清洗
4. 检测语言
5. 若为英文，执行翻译链；若为中文，跳过翻译
6. 调用摘要链、分类链、标题链
7. 保存文章处理结果
8. 聚合当天内容生成日报
9. 渲染 HTML 页面并保存页面元数据
10. 向飞书推送日报摘要和访问链接

## 4. 技术选型

### 4.1 后端

- `FastAPI`：API、后台页面、静态页面访问入口
- `Jinja2`：后台管理页与日报 HTML 渲染
- `Uvicorn`：本地开发服务

### 4.2 数据库

- `MySQL 8+`
- `SQLAlchemy 2.x`
- `Alembic`：数据库迁移
- `PyMySQL`：MySQL 驱动

### 4.3 采集与任务

- `feedparser`：RSS/Atom 解析
- `httpx`：HTTP 请求
- `BeautifulSoup4 + readability-lxml`：网页正文提取与清洗
- `APScheduler`：定时任务调度

### 4.4 AI 编排

- `LangChain`
- `langchain-openai`
- OpenAI 兼容中转站 `base_url`

### 4.5 校验与工具

- `Pydantic v2`
- `python-dotenv`
- `langdetect`

## 5. 目录结构

建议目录如下：

```text
f:/luntantuisong/
├── app/
│   ├── api/
│   │   └── routes/
│   ├── core/
│   ├── db/
│   │   ├── models/
│   │   └── repositories/
│   ├── schemas/
│   ├── services/
│   │   ├── ai/
│   │   ├── crawler/
│   │   ├── notifier/
│   │   ├── report/
│   │   └── scheduler/
│   ├── templates/
│   ├── static/
│   └── main.py
├── alembic/
├── docs/
│   ├── plans/
│   ├── reports/
│   └── previews/
├── tests/
├── .env.example
├── pyproject.toml
└── README.md
```

## 6. 数据模型设计

### 6.1 `sources`

用于管理内容源。

关键字段：

- `id`
- `name`
- `slug`
- `site_url`
- `source_type`：`rss` / `web`
- `feed_url`
- `list_url`
- `language_hint`
- `category`
- `enabled`
- `include_in_daily`
- `crawl_interval_minutes`
- `last_crawled_at`
- `created_at`
- `updated_at`

### 6.2 `source_rules`

用于保存网页抓取规则。

关键字段：

- `id`
- `source_id`
- `list_item_selector`
- `link_selector`
- `title_selector`
- `published_at_selector`
- `author_selector`
- `content_selector`
- `remove_selectors`
- `request_headers_json`
- `created_at`
- `updated_at`

### 6.3 `articles`

保存文章基础信息和去重信息。

关键字段：

- `id`
- `source_id`
- `title`
- `canonical_url`
- `author`
- `published_at`
- `language`
- `url_hash`
- `status`
- `crawl_error`
- `is_selected_for_daily`
- `created_at`
- `updated_at`

### 6.4 `article_contents`

保存正文和 AI 处理结果。

关键字段：

- `id`
- `article_id`
- `raw_html`
- `raw_content`
- `clean_content`
- `translated_content`
- `summary`
- `category`
- `generated_title`
- `keywords_json`
- `ai_status`
- `ai_error`
- `processed_at`
- `created_at`
- `updated_at`

### 6.5 `daily_reports`

保存日报信息。

关键字段：

- `id`
- `report_date`
- `title`
- `intro`
- `status`
- `html_path`
- `html_url`
- `source_count`
- `article_count`
- `feishu_pushed`
- `feishu_pushed_at`
- `created_at`
- `updated_at`

### 6.6 `daily_report_items`

日报与文章的关联表。

关键字段：

- `id`
- `report_id`
- `article_id`
- `display_order`
- `section_name`
- `created_at`

### 6.7 `model_configs`

按任务管理模型配置。

关键字段：

- `id`
- `task_type`：`translation` / `summary` / `classification` / `title`
- `provider_name`
- `model_name`
- `base_url`
- `api_key_env_name`
- `temperature`
- `max_tokens`
- `enabled`
- `is_default`
- `created_at`
- `updated_at`

说明：

- `api_key_env_name` 只存环境变量名，例如 `OPENAI_API_KEY`
- 实际密钥只从 `.env` 读取，不落库

### 6.8 `system_settings`

保存全局配置。

关键字段：

- `id`
- `setting_key`
- `setting_value`
- `description`
- `updated_at`

建议首批设置项：

- `scheduler.crawl_cron`
- `scheduler.report_cron`
- `scheduler.feishu_cron`
- `report.site_base_url`
- `feishu.webhook_url`
- `content.max_articles_per_day`

### 6.9 `job_runs`

保存任务执行日志。

关键字段：

- `id`
- `job_name`
- `trigger_type`
- `status`
- `started_at`
- `finished_at`
- `processed_count`
- `error_message`
- `details_json`

## 7. 后台页面设计

后台页面先采用服务端渲染，页面简单可用即可。

### 7.1 仪表盘

展示：

- 今日抓取文章数
- 今日成功处理数
- 今日日报状态
- 最近一次飞书推送结果
- 最近任务执行日志

### 7.2 内容源管理

支持：

- 新增内容源
- 编辑内容源
- 启停内容源
- 配置 RSS 地址或网页抓取地址
- 配置抓取规则

### 7.3 模型配置

按任务分别配置：

- 翻译模型
- 摘要模型
- 分类模型
- 标题生成模型

### 7.4 文章列表

支持查看：

- 来源
- 标题
- 发布时间
- 语言
- AI 处理状态
- 是否入选日报

### 7.5 日报管理

支持：

- 查看日报列表
- 预览日报页面
- 手动重跑生成
- 查看推送状态

### 7.6 任务日志

查看定时任务和手动任务的执行结果。

## 8. API 设计

首版 API 主要服务后台页面，也支持后续扩展。

建议接口：

- `GET /health`
- `GET /admin`
- `GET /admin/sources`
- `POST /admin/sources`
- `POST /admin/sources/{id}/toggle`
- `GET /admin/models`
- `POST /admin/models`
- `GET /admin/articles`
- `GET /admin/reports`
- `POST /admin/reports/run`
- `POST /admin/jobs/crawl/run`
- `POST /admin/jobs/process/run`
- `POST /admin/jobs/push/run`
- `GET /daily/{report_date}`

## 9. AI 链路设计

### 9.1 语言识别

- 使用 `langdetect` 识别文章主语言
- 首版主要支持 `zh` 和 `en`
- 非中英文文章先标记原文，后续可扩展

### 9.2 翻译链

输入：

- 标题
- 清洗后的正文

规则：

- 英文翻译为自然中文
- 中文不走翻译链
- 保留关键术语

输出：

- 中文正文

### 9.3 摘要链

输入：

- 中文正文

输出：

- 2 到 4 条要点摘要
- 一段简短导读

### 9.4 分类链

输入：

- 标题
- 中文正文

输出：

- 一级分类，例如：`AI 平台`、`模型工程`、`数据基础设施`、`后端架构`、`前端工程`

### 9.5 标题链

输入：

- 原标题
- 摘要

输出：

- 更适合日报展示的中文标题

### 9.6 输出约束

- 所有链路尽量返回 JSON
- 解析失败时记录错误并允许重试
- 单篇失败不影响整批任务

## 10. 日报生成设计

### 10.1 聚合策略

- 以自然日为维度聚合
- 默认汇总当天已成功处理的文章
- 支持限定文章数量上限
- 优先按分类分组展示

### 10.2 页面内容

- 当日标题
- 开场导语
- 分类分组
- 每篇文章的标题、摘要、原文链接、来源、发布时间
- 页面底部附带来源统计

### 10.3 页面访问方式

- 本地运行时访问 `http://localhost:8000/daily/2026-04-17`
- HTML 文件可额外落盘到 `docs/reports/`

## 11. 飞书推送设计

飞书只发送简明日报卡片，不推送整篇正文。

卡片内容建议包含：

- 当日日报标题
- 3 条核心看点
- 日报访问链接
- 文章来源数量

推送失败策略：

- 记录失败日志
- 后续支持手动重试

## 12. 定时任务设计

首版使用 `APScheduler` 内嵌调度。

建议拆分三类任务：

- `crawl_sources_job`
- `process_articles_job`
- `generate_and_push_report_job`

调度时间从 `system_settings` 读取。

## 13. 错误处理策略

- 单个内容源抓取失败不影响其他内容源
- 单篇文章解析失败记录到 `articles.crawl_error`
- AI 处理失败记录到 `article_contents.ai_error`
- 飞书推送失败记录到 `job_runs`
- 所有后台操作提供可见的失败提示

## 14. 测试策略

首版至少覆盖以下测试：

- RSS 解析测试
- 网页正文提取测试
- 语言识别与翻译分支测试
- 摘要/分类结果解析测试
- 日报聚合测试
- 飞书通知请求测试
- 数据库模型基础测试

## 15. 安全策略

- 中转站 API Key 仅存于 `.env`
- 数据库不保存明文密钥
- 所有表单输入通过 Pydantic 校验
- 后台错误对用户展示通用提示，详细错误写日志
- 抓取请求设置合理超时，避免任务卡死

## 16. 首批推荐内容源

- 美团技术团队
- Anthropic Engineering
- Uber Engineering
- Netflix TechBlog

后续可扩展：

- Cloudflare Blog
- AWS Architecture Blog
- Shopify Engineering

## 17. 首版范围边界

首版暂不实现：

- 多用户登录与权限
- 云端自动部署
- 高级审核流
- Redis/Celery 异步队列
- 向量检索与知识库
- 非中英文多语言支持

## 18. 结论

首版采用 `FastAPI 单体应用 + MySQL + LangChain + APScheduler + Jinja2`，以最小复杂度打通“采集、翻译、摘要、分类、日报生成、网页访问、飞书推送、后台管理”完整链路，并为后续扩展保留数据库和模块边界。
