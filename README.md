# 技术论坛日报

一个面向技术内容团队、个人信息流整理和论坛日报场景的本地优先聚合系统。

它可以把多个技术博客、工程论坛、公司技术团队博客和 AI 工程站点的内容抓下来，自动完成语言识别、英文翻译、摘要、分类、标题生成，再按天生成公开日报页面，并推送到飞书。

当前项目重点支持：

- 技术内容源管理
- RSS 与网页抓取
- 英文内容翻译，中文内容直出
- 基于 OpenAI 兼容接口的多任务模型调用
- 每日 HTML 日报生成
- 飞书机器人推送
- Vue 3 后台管理台
- APScheduler 自动调度
- 日报人工编辑和手动补文章
- 作业互斥保护，避免重复执行

## 1. 适合什么场景

这个项目适合下面几类使用方式：

- 个人每天收集技术资讯，自动生成“今日技术摘要”
- 团队内部每天整理工程博客、AI 论坛和基础设施动态
- 运营或内容团队生成可访问的技术日报链接，再发到飞书群
- 想先本地跑通、后续再部署到云服务器的小型自动化项目

## 2. 当前能力

### 内容链路

- 管理内容源
- 配置网页抓取规则
- 抓取文章正文
- 文章入库与去重
- AI 翻译、摘要、分类、标题生成
- 生成日报
- 推送飞书

### 后台能力

- Dashboard 仪表盘
- 内容源管理
- 抓取规则预览
- 文章池查看与重处理
- 模型配置
- 日报列表、编辑、发布
- 候选文章手动加入日报
- 数据库概览与清理
- 任务日志
- 系统设置与自动调度

### 新增稳定性能力

- 核心作业统一互斥
- 手动触发与定时触发共用同一套运行守卫
- 同名任务运行中再次触发时返回 `409 Conflict`
- 过旧的 running 作业会自动标记为 `timeout`
- 定时飞书推送会跳过已推送日报，减少重复推送

## 3. 技术栈

### 后端

- Python 3.9+
- FastAPI
- SQLAlchemy 2.x
- MySQL
- APScheduler
- LangChain
- langchain-openai

### 前端

- Vue 3
- Vite
- TypeScript

### 外部集成

- OpenAI 兼容大模型接口
- 飞书机器人 Webhook

## 4. 系统架构

整体链路如下：

1. `Source` 保存内容源配置
2. 抓取任务从 RSS 或网页列表页拉文章
3. 正文入库到 `Article` 与 `ArticleContent`
4. AI 任务对文章执行语言识别、翻译、摘要、分类、标题生成
5. 日报任务按日期挑选可用文章，生成 `DailyReport`
6. 推送任务把日报摘要和公开链接发到飞书

核心服务目录：

- `app/services/crawl_service.py`：抓取入口
- `app/services/article_processing_service.py`：文章 AI 处理
- `app/services/report_service.py`：日报生成与编辑
- `app/services/notifier/feishu.py`：飞书推送
- `app/services/scheduler/runtime.py`：APScheduler 调度运行时
- `app/services/job_service.py`：作业运行守卫与任务记录

## 5. 目录结构

```text
f:/luntantuisong
├─ app/
│  ├─ api/routes/                # FastAPI 路由
│  ├─ core/                      # 配置、数据库、日志、模板
│  ├─ db/models/                 # 数据模型
│  ├─ services/                  # 业务服务
│  │  ├─ ai/                     # AI 调用与处理流水线
│  │  ├─ crawler/                # RSS / 网页抓取底层
│  │  ├─ notifier/               # 飞书通知
│  │  └─ scheduler/              # 定时调度
│  ├─ static/                    # 后端静态资源
│  └─ templates/                 # 公开页和旧后台模板
├─ docs/
│  ├─ plans/                     # 设计与实施计划
│  └─ reports/                   # 生成后的日报 HTML
├─ frontend/                     # Vue 3 管理台
├─ tests/                        # pytest 测试
├─ .env.example                  # 环境变量模板
├─ pyproject.toml                # Python 依赖
└─ README.md
```

## 6. 环境变量

先把 `.env.example` 复制为 `.env`。

```powershell
Copy-Item .env.example .env
```

当前支持的关键环境变量如下：

| 变量名 | 必填 | 说明 | 示例 |
| --- | --- | --- | --- |
| `APP_NAME` | 否 | 应用标题 | `技术论坛日报` |
| `APP_ENV` | 否 | 运行环境，测试环境会关闭调度器 | `development` |
| `APP_HOST` | 否 | FastAPI 监听地址 | `127.0.0.1` |
| `APP_PORT` | 否 | FastAPI 监听端口 | `8000` |
| `APP_DEBUG` | 否 | 是否开启调试 | `true` |
| `DATABASE_URL` | 是 | 数据库连接串，推荐 MySQL | `mysql+pymysql://root:password@127.0.0.1:3306/tech_daily?charset=utf8mb4` |
| `OPENAI_API_KEY` | 否 | 默认 OpenAI 兼容密钥 | `replace_me` |
| `OPENAI_BASE_URL` | 否 | 默认 OpenAI 兼容地址 | `https://www.aiwanwu.cc/v1` |
| `AIWANWU_API_KEY` | 强烈建议 | 给模型配置页引用的环境变量名 | `replace_me` |
| `FEISHU_WEBHOOK_URL` | 否 | 飞书机器人 webhook | `https://open.feishu.cn/...` |
| `SITE_BASE_URL` | 是 | 日报公开访问地址基准 | `http://127.0.0.1:8000` |

说明：

- 模型真正调用时，读取的是模型配置里的 `api_key_env_name` 对应的环境变量值。
- 如果你在模型配置里把 `api_key_env_name` 设成 `AIWANWU_API_KEY`，那 `.env` 里就必须有这个变量。
- `OPENAI_API_KEY` 和 `OPENAI_BASE_URL` 更像默认保留项，当前后台推荐通过模型配置页来管理模型入口。

## 7. 推荐本地环境

- Windows 10/11 或 Linux/macOS
- Python 3.10 或 3.11
- Node.js 20+
- MySQL 8.x

如果你只是本地快速体验，也可以临时改成 SQLite：

```env
DATABASE_URL=sqlite+pysqlite:///./tech_daily.db
```

## 8. 从零启动

### 8.1 安装 Python 依赖

建议先创建虚拟环境：

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -U pip
pip install -e ".[dev]"
```

### 8.2 安装前端依赖

```powershell
cd frontend
npm install
cd ..
```

### 8.3 配置 `.env`

至少要填：

- `DATABASE_URL`
- `AIWANWU_API_KEY`
- `FEISHU_WEBHOOK_URL`，如果需要飞书推送
- `SITE_BASE_URL`

### 8.4 启动后端

```powershell
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

第一次启动会自动：

- 初始化数据库表
- 注入默认系统设置
- 启动 APScheduler

### 8.5 启动前端开发服务

另开一个终端：

```powershell
cd frontend
npm run dev
```

### 8.6 访问地址

开发模式：

- 后端 API：`http://127.0.0.1:8000`
- 前端管理台：`http://127.0.0.1:5173/admin/`

构建后由 FastAPI 托管：

- 管理台：`http://127.0.0.1:8000/admin/`
- 日报公开页：`http://127.0.0.1:8000/daily/YYYY-MM-DD`

## 9. 前端构建

需要用 FastAPI 直接托管后台时：

```powershell
cd frontend
npm run build
cd ..
```

构建完成后，FastAPI 会读取 `frontend/dist` 并托管 `/admin/`。

## 10. 第一次进入后台建议怎么做

推荐按这个顺序：

1. 打开 `/admin/#/dashboard`
2. 在首页应用 Starter Presets，快速创建默认来源和默认模型
3. 进入 `/admin/#/models` 检查模型配置
4. 确认 `api_key_env_name` 对应的环境变量已写进 `.env`
5. 进入 `/admin/#/settings` 检查时区、cron 和飞书模板
6. 进入 `/admin/#/sources` 检查内容源启用状态
7. 手动执行抓取、处理、生成日报、飞书推送

## 11. 默认来源与模型

当前预置来源包括：

- 美团技术团队
- Anthropic Engineering
- GitHub Engineering
- Cloudflare Blog

当前预置模型任务包括：

- `translation`
- `summary`
- `classification`
- `title`

默认都指向 `https://www.aiwanwu.cc/v1`，并读取 `AIWANWU_API_KEY`。

## 12. 后台页面说明

### Dashboard

- 展示文章数、日报数、任务数
- 查看最近任务
- 查看调度器状态
- 一键应用 starter 预置

### Sources

- 管理 RSS / 网页来源
- 控制是否启用
- 控制是否纳入日报

### Source Rules

- 为网页类来源配置抓取规则
- 预览列表页与文章页提取结果

### Articles

- 查看文章池
- 查看 AI 处理结果
- 单篇重处理

### Models

- 为不同任务类型配置默认模型
- 绑定不同 `api_key_env_name`

### Reports

- 查看日报历史
- 编辑日报标题、导语、排序、分组
- 手动加入候选文章
- 重新发布公开页
- 手动推送飞书

### Jobs

- 查看任务日志
- 查看运行状态、错误和处理数量

### Database

- 查看库连接、表统计、状态分布
- 执行基础清理操作

### Settings

- 配置 cron
- 配置时区
- 配置日报篇数上限
- 配置飞书模板
- 测试飞书消息

## 13. 自动调度说明

系统启动时会读取数据库中的系统设置，并注册以下任务：

- `crawl_sources_job`
- `process_articles_job`
- `generate_report_job`
- `push_report_job`

默认 cron：

| 设置项 | 默认值 | 说明 |
| --- | --- | --- |
| `scheduler.enabled` | `true` | 是否启用调度器 |
| `scheduler.timezone` | `Asia/Shanghai` | 调度时区 |
| `scheduler.crawl_cron` | `0 */2 * * *` | 每 2 小时抓取一次 |
| `scheduler.process_cron` | `10 */2 * * *` | 抓取后 10 分钟处理 |
| `scheduler.report_cron` | `0 18 * * *` | 每天 18:00 生成日报 |
| `scheduler.push_cron` | `5 18 * * *` | 每天 18:05 推送飞书 |

### 当前互斥策略

核心任务按 `job_name` 互斥：

- 抓取任务不能重入
- 处理任务不能重入
- 日报生成不能重入
- 飞书推送不能重入

如果你在任务正在执行时重复点击按钮，接口会返回：

```json
{
  "detail": "xxx_job 正在运行中，请稍后再试"
}
```

HTTP 状态码为 `409 Conflict`。

### 调度器额外行为

- 如果调度器触发飞书推送时，当天日报已经推送过，则会直接跳过
- 过旧的 running 任务会自动标记为 `timeout`

## 14. 公开日报页面

日报生成后会写入：

- 数据库里的 `DailyReport`
- 本地 `docs/reports/YYYY-MM-DD.html`

默认公开地址格式：

```text
http://127.0.0.1:8000/daily/2026-04-17
```

真正发给飞书的地址由 `SITE_BASE_URL` 决定，所以部署后一定要改成真实域名。

## 15. 主要接口

### 健康检查

- `GET /health`

### Dashboard / 数据

- `GET /admin/api/dashboard`
- `GET /admin/api/articles`
- `GET /admin/api/reports`
- `GET /admin/api/jobs`
- `GET /admin/api/scheduler/status`
- `GET /admin/api/bootstrap/starter`
- `POST /admin/api/bootstrap/starter`

### 内容源

- `GET /admin/api/sources`
- `POST /admin/api/sources`
- `PUT /admin/api/sources/{id}`
- `POST /admin/api/sources/{id}/toggle`

### 抓取规则

- `GET /admin/api/sources/{id}/rules`
- `POST /admin/api/sources/{id}/rules`
- `POST /admin/api/sources/{id}/rules/preview`
- `GET /admin/api/sources/{id}/rules/template`

### 文章

- `GET /admin/api/articles/{id}`
- `POST /admin/api/articles/{id}/reprocess`

### 模型

- `GET /admin/api/models`
- `POST /admin/api/models`
- `PUT /admin/api/models/{id}`

### 日报

- `GET /admin/api/reports/{id}`
- `PUT /admin/api/reports/{id}`
- `POST /admin/api/reports/{id}/publish`
- `GET /daily/{report_date}`

### 任务

- `POST /admin/api/jobs/crawl/run`
- `POST /admin/api/jobs/process/run`
- `POST /admin/api/jobs/report/run`
- `POST /admin/api/jobs/push/run`

### 设置与飞书

- `GET /admin/api/settings`
- `POST /admin/api/settings`
- `POST /admin/api/settings/batch`
- `POST /admin/api/scheduler/reload`
- `GET /admin/api/integrations/feishu/status`
- `POST /admin/api/integrations/feishu/test`

## 16. 本地接口烟测

项目开发完成后，推荐至少做一次接口 smoke test。

### PowerShell 示例

```powershell
Invoke-RestMethod http://127.0.0.1:8000/health
Invoke-RestMethod http://127.0.0.1:8000/admin/api/dashboard
Invoke-RestMethod http://127.0.0.1:8000/admin/api/sources
Invoke-RestMethod http://127.0.0.1:8000/admin/api/articles
Invoke-RestMethod http://127.0.0.1:8000/admin/api/models
Invoke-RestMethod http://127.0.0.1:8000/admin/api/reports
Invoke-RestMethod http://127.0.0.1:8000/admin/api/jobs
Invoke-RestMethod http://127.0.0.1:8000/admin/api/settings
Invoke-RestMethod http://127.0.0.1:8000/admin/api/integrations/feishu/status
```

如果你要测试写接口，建议先在后台应用 starter 预置后再执行：

```powershell
Invoke-RestMethod -Method Post http://127.0.0.1:8000/admin/api/jobs/crawl/run
Invoke-RestMethod -Method Post http://127.0.0.1:8000/admin/api/jobs/process/run
Invoke-RestMethod -Method Post "http://127.0.0.1:8000/admin/api/jobs/report/run?report_date=$(Get-Date -Format yyyy-MM-dd)"
```

飞书测试消息：

```powershell
$body = @{
  title = "联调测试"
  message = "这是一条来自技术论坛日报后台的测试消息"
} | ConvertTo-Json

Invoke-RestMethod `
  -Method Post `
  -Uri http://127.0.0.1:8000/admin/api/integrations/feishu/test `
  -ContentType "application/json" `
  -Body $body
```

## 17. 测试

### 后端测试

```powershell
python -m pytest -q
```

### 前端构建验证

```powershell
cd frontend
npm run build
cd ..
```

## 18. 常见问题

### 1. 管理台打开提示“前端尚未构建”

说明你现在访问的是 FastAPI 托管的 `/admin/`，但前端还没 build。

解决：

```powershell
cd frontend
npm run build
cd ..
```

或者直接访问开发地址：

`http://127.0.0.1:5173/admin/`

### 2. 模型不出结果

先检查：

- `.env` 里是否有对应密钥
- 模型配置里的 `api_key_env_name` 是否和 `.env` 一致
- `base_url` 是否是可访问的 OpenAI 兼容地址
- 对应任务类型是否启用了默认模型

### 3. 飞书推送失败

先检查：

- `FEISHU_WEBHOOK_URL` 是否正确
- 设置页的飞书状态是否显示已配置
- 测试消息是否能成功发送
- `SITE_BASE_URL` 是否为外网可访问地址

### 4. 为什么点两次任务按钮会报 409

这是这轮新增的互斥保护，说明同名任务已经在跑。

### 5. 调度器为什么没启动

检查：

- `APP_ENV` 不能是 `test`
- 是否安装了 `apscheduler`
- `scheduler.enabled` 是否为 `true`

### 6. 日报里没有文章

通常检查这几个点：

- 文章是否已抓到正文
- 文章 AI 是否处理成功
- 文章日期是否命中日报日期
- `report.max_articles_per_day` 是否设置太小

## 19. 生产部署建议

当前版本适合单机部署。推荐：

- 一个 MySQL
- 一个 FastAPI 进程
- 由 FastAPI 直接托管 build 后的前端
- `SITE_BASE_URL` 指向真实域名
- 飞书 webhook 使用正式群机器人

建议补充：

- 反向代理，例如 Nginx
- HTTPS
- 日志轮转
- 数据库备份
- 进程守护，例如 NSSM、systemd 或 Supervisor

## 20. 后续优化建议

如果继续往下做，我建议优先级是：

1. 文章近似去重
2. 来源健康评分和失败重试
3. 日报编排规则
4. 模型 fallback
5. 更完整的接口 smoke test 脚本
6. 多实例部署时的分布式锁

---

如果你要继续迭代，建议下一轮直接做“来源健康监控 + 文章近似去重”。
