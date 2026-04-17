# 技术论坛日报

一个面向技术论坛、工程博客和 AI 技术站点的自动化日报系统。

它会把你关心的内容源统一抓取进来，自动完成英文翻译、摘要、分类、标题生成，再按天生成可访问的日报页面，并支持自动推送到飞书。

## 项目定位

这个项目适合下面几类场景：

- 个人维护自己的技术资讯日报
- 团队每天整理工程博客和 AI 论坛动态
- 给飞书群自动推送一份“今天值得看”的技术内容
- 先本地跑通，再逐步部署到正式环境

## 功能亮点

- 多来源聚合：支持 RSS 和网页列表抓取
- 智能处理：英文内容自动翻译，中文内容直接进入后续流程
- 多模型任务链：翻译、摘要、分类、标题分别配置
- 日报发布：按天生成 HTML 页面，可直接对外访问
- 飞书推送：自动把日报链接推送到群聊
- 后台管理：基于 Vue 3 + Vite 的独立管理端
- 来源健康监控：显示健康、冷却中、失败、未抓取状态
- 失败重试：抓取异常自动进入短退避重试流程
- 作业互斥：避免重复点击或定时任务重入

## 技术栈

- 后端：Python、FastAPI、SQLAlchemy、MySQL、APScheduler、LangChain
- 前端：Vue 3、Vite、TypeScript
- 集成：OpenAI 兼容接口、飞书机器人 Webhook

## 核心流程

```text
内容源 Source
  -> 抓取 RSS / 网页文章
  -> 提取正文并入库
  -> AI 翻译 / 摘要 / 分类 / 标题
  -> 生成日报 HTML
  -> 推送飞书消息
```

本轮已经补齐的稳定性能力：

- 来源健康状态派生
- 冷却窗口跳过抓取
- 抓取失败自动短退避重试
- 重复运行任务返回 `409`
- 定时飞书推送跳过已发布日报

## 后台页面

- `Dashboard`：查看任务、调度状态、来源健康和异常提醒
- `Sources`：管理抓取来源、健康状态、规则入口
- `Source Rules`：为网页来源配置抓取规则并在线预览
- `Articles`：查看文章池、正文、AI 处理结果
- `Models`：配置不同任务使用的模型
- `Reports`：管理日报、编辑内容、发布公开页
- `Jobs`：查看任务执行记录
- `Database`：查看数据库概览和执行基础清理
- `Settings`：配置调度、飞书模板和系统参数

## 快速开始

### 1. 安装后端依赖

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -U pip
pip install -e ".[dev]"
```

### 2. 安装前端依赖

```powershell
cd frontend
npm install
cd ..
```

### 3. 准备环境变量

```powershell
Copy-Item .env.example .env
```

至少需要配置：

- `DATABASE_URL`
- `SITE_BASE_URL`
- 模型密钥对应的环境变量，例如 `AIWANWU_API_KEY`
- `FEISHU_WEBHOOK_URL`，如果你要启用飞书推送

### 4. 启动后端

```powershell
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

### 5. 启动前端开发环境

```powershell
cd frontend
npm run dev
```

开发访问地址：

- 后端 API：`http://127.0.0.1:8000`
- 管理后台：`http://127.0.0.1:5173/admin/`

构建后也可以直接由 FastAPI 托管：

```powershell
cd frontend
npm run build
cd ..
```

然后访问：

- 管理后台：`http://127.0.0.1:8000/admin/`
- 日报公开页：`http://127.0.0.1:8000/daily/YYYY-MM-DD`

## 推荐初始来源

当前比较适合作为第一批技术来源的站点：

- 美团技术团队
- Anthropic Engineering
- GitHub Engineering
- Cloudflare Blog

如果你继续扩内容源，推荐优先补：

- Netflix TechBlog
- Stripe Engineering
- OpenAI News / Engineering 相关公开页面
- Vercel / Next.js Blog

## 关键配置

常见关键变量如下：

| 变量名 | 说明 |
| --- | --- |
| `DATABASE_URL` | 数据库连接字符串，推荐 MySQL |
| `SITE_BASE_URL` | 日报公开访问基准地址 |
| `AIWANWU_API_KEY` | 当前中转站密钥环境变量 |
| `FEISHU_WEBHOOK_URL` | 飞书机器人地址 |
| `APP_ENV` | 运行环境，`test` 下不会启动调度器 |

说明：

- 模型真正读取的是“模型配置里填写的 `api_key_env_name`”所对应的环境变量
- 如果你想让生成的日报链接能被外部访问，`SITE_BASE_URL` 必须配置成真实可访问地址

## 测试与验证

```powershell
python -m pytest -q
```

```powershell
cd frontend
npm run build
```

## Roadmap

- 更多技术论坛 / 博客 starter preset
- 更细粒度的来源健康评分
- 单来源重试与手动补抓
- 文章近似去重
- 模型 fallback 与降级策略
- 更完整的部署与监控方案

## 开源说明

这个项目适合作为“技术内容聚合 + 自动日报 + 飞书推送”的开源起步模板。

如果你准备把它用于正式团队环境，建议继续补充：

- HTTPS 与反向代理
- 进程守护
- 数据库备份
- 日志与监控
- 更严格的密钥管理
