# 作业互斥与 README 补全 Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 给核心作业增加统一互斥保护与基础幂等策略，并把 README 补成完整的项目运行手册。

**Architecture:** 新增作业运行守卫层，统一管理 `JobRun` 的开始、完成、冲突与超时清理；抓取、处理、生成日报、飞书推送四个服务统一接入。文档部分直接重写根目录 README，并在实现完成后做一次本地接口烟测。

**Tech Stack:** FastAPI、SQLAlchemy、APScheduler、pytest、Vue 3、Vite

---

### Task 1: 实现统一作业运行守卫

**Files:**
- Modify: `app/services/job_service.py`
- Modify: `app/services/crawl_service.py`
- Modify: `app/services/article_processing_service.py`
- Modify: `app/services/report_service.py`
- Modify: `app/services/notifier/feishu.py`
- Modify: `app/services/scheduler/runtime.py`
- Modify: `app/api/routes/jobs.py`
- Test: `tests/routes/test_crawl_jobs.py`
- Test: `tests/routes/test_process_and_report_jobs.py`
- Test: `tests/services/test_scheduler_runtime.py`

**Step 1: 写失败测试，覆盖重复执行冲突**

```python
def test_run_crawl_job_returns_409_when_same_job_is_running(client):
    ...
    assert response.status_code == 409
```

**Step 2: 运行对应测试确认失败**

Run: `python -m pytest tests/routes/test_crawl_jobs.py tests/routes/test_process_and_report_jobs.py tests/services/test_scheduler_runtime.py -q`
Expected: FAIL，因为当前没有统一运行锁

**Step 3: 写最小实现**

实现：

- `job_service.py` 增加开始/完成作业与冲突异常
- 服务层统一改成通过守卫创建 `JobRun`
- `scheduler/runtime.py` 改成以 `trigger_type="scheduler"` 调用服务
- `jobs.py` 捕获冲突异常并返回 409

**Step 4: 跑测试确认通过**

Run: `python -m pytest tests/routes/test_crawl_jobs.py tests/routes/test_process_and_report_jobs.py tests/services/test_scheduler_runtime.py -q`
Expected: PASS

**Step 5: Commit**

```bash
git add app/services/job_service.py app/services/crawl_service.py app/services/article_processing_service.py app/services/report_service.py app/services/notifier/feishu.py app/services/scheduler/runtime.py app/api/routes/jobs.py tests/routes/test_crawl_jobs.py tests/routes/test_process_and_report_jobs.py tests/services/test_scheduler_runtime.py
git commit -m "feat: add job execution guard"
```

### Task 2: 补调度器幂等行为

**Files:**
- Modify: `app/services/notifier/feishu.py`
- Modify: `app/services/scheduler/runtime.py`
- Test: `tests/services/test_feishu.py`
- Test: `tests/services/test_scheduler_runtime.py`

**Step 1: 写失败测试，覆盖已推送日报的调度跳过**

```python
def test_scheduler_push_skips_when_report_already_pushed(session):
    ...
    assert result["status"] == "skipped"
```

**Step 2: 运行对应测试确认失败**

Run: `python -m pytest tests/services/test_feishu.py tests/services/test_scheduler_runtime.py -q`
Expected: FAIL，因为当前调度推送不会跳过

**Step 3: 写最小实现**

实现：

- `push_report_to_feishu(..., trigger_type="manual")`
- 当 `trigger_type == "scheduler"` 且 `report.feishu_pushed` 为真时直接 skipped

**Step 4: 跑测试确认通过**

Run: `python -m pytest tests/services/test_feishu.py tests/services/test_scheduler_runtime.py -q`
Expected: PASS

**Step 5: Commit**

```bash
git add app/services/notifier/feishu.py app/services/scheduler/runtime.py tests/services/test_feishu.py tests/services/test_scheduler_runtime.py
git commit -m "feat: skip duplicated scheduled feishu push"
```

### Task 3: 重写 README 并补自测说明

**Files:**
- Modify: `README.md`

**Step 1: 重写 README**

补齐：

- 项目介绍
- 架构与目录
- 环境变量表
- 本地启动与构建
- 后台页面说明
- 自动调度说明
- API 列表
- 飞书/模型配置
- 常见问题
- 生产建议

**Step 2: 人工检查内容完整性**

Run: `Get-Content -Raw README.md`
Expected: 信息完整、结构清晰、没有占位段落

**Step 3: Commit**

```bash
git add README.md
git commit -m "docs: expand project readme"
```

### Task 4: 全量验证与接口烟测

**Files:**
- Verify: `app/main.py`
- Verify: `README.md`

**Step 1: 跑后端全量测试**

Run: `python -m pytest -q`
Expected: PASS

**Step 2: 跑前端构建**

Run: `cd frontend && npm run build`
Expected: PASS

**Step 3: 启动本地服务并做接口烟测**

Run:

```bash
uvicorn app.main:app --host 127.0.0.1 --port 8000
```

然后验证：

- `GET /health`
- `GET /admin/api/dashboard`
- `GET /admin/api/sources`
- `GET /admin/api/articles`
- `GET /admin/api/models`
- `GET /admin/api/reports`
- `GET /admin/api/jobs`
- `GET /admin/api/settings`
- `GET /admin/api/integrations/feishu/status`

以及主要 POST 接口：

- `POST /admin/api/jobs/crawl/run`
- `POST /admin/api/jobs/process/run`
- `POST /admin/api/jobs/report/run`
- `POST /admin/api/jobs/push/run`
- `POST /admin/api/integrations/feishu/test`

**Step 4: 检查 git 状态**

Run: `git status --short`
Expected: 只有当前轮需要提交的改动，最终为空

**Step 5: Commit**

```bash
git add .
git commit -m "feat: harden job execution and refresh docs"
```
