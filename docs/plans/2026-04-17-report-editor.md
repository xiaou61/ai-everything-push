# 日报编辑后再发布 Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 为现有日报系统补充后台编辑与重新发布能力，让用户能在自动生成后人工润色再对外发布。

**Architecture:** 基于现有 `daily_reports` 与 `daily_report_items` 直接扩展后端编辑 API 和 Vue 报表页编辑面板，不新增新表，不引入单独 CMS。保存动作只更新数据库，发布动作单独重新渲染公开 HTML 页面，保持现有飞书推送链路不变。

**Tech Stack:** FastAPI、SQLAlchemy、Jinja2、Vue 3、Vite、TypeScript、pytest

---

### Task 1: 补日报详情与编辑接口

**Files:**
- Modify: `app/services/report_service.py`
- Modify: `app/api/routes/reports.py`
- Test: `tests/routes/test_report_editor_routes.py`

**Step 1: Write the failing test**

```python
def test_get_report_detail_api(client):
    response = client.get("/admin/api/reports/1")
    assert response.status_code == 200
    assert len(response.json()["items"]) == 2
```

**Step 2: Run test to verify it fails**

Run: `python -m pytest tests/routes/test_report_editor_routes.py::test_get_report_detail_api -q`
Expected: FAIL with route missing error

**Step 3: Write minimal implementation**

实现：

- `get_report(report_id)`
- `serialize_report_detail(report)`
- `GET /admin/api/reports/{report_id}`
- `PUT /admin/api/reports/{report_id}`

保存接口支持更新：

- `title`
- `intro`
- `items[].id`
- `items[].display_order`
- `items[].section_name`

并自动重算：

- `article_count`
- `source_count`

**Step 4: Run test to verify it passes**

Run: `python -m pytest tests/routes/test_report_editor_routes.py -q`
Expected: PASS

**Step 5: Commit**

```bash
git add app/services/report_service.py app/api/routes/reports.py tests/routes/test_report_editor_routes.py
git commit -m "feat: add report detail and editing api"
```

### Task 2: 补重新发布能力

**Files:**
- Modify: `app/services/report_service.py`
- Modify: `app/api/routes/reports.py`
- Test: `tests/routes/test_report_editor_routes.py`

**Step 1: Write the failing test**

```python
def test_publish_report_updates_public_html(client):
    response = client.post("/admin/api/reports/1/publish")
    assert response.status_code == 200
    public_page = client.get("/daily/2026-04-17")
    assert "新的日报标题" in public_page.text
```

**Step 2: Run test to verify it fails**

Run: `python -m pytest tests/routes/test_report_editor_routes.py::test_publish_report_updates_public_html -q`
Expected: FAIL with route missing error

**Step 3: Write minimal implementation**

实现：

- `publish_report(report_id)`
- `POST /admin/api/reports/{report_id}/publish`

发布时重新渲染公开 HTML，并返回最新 `html_url`。

**Step 4: Run test to verify it passes**

Run: `python -m pytest tests/routes/test_report_editor_routes.py -q`
Expected: PASS

**Step 5: Commit**

```bash
git add app/services/report_service.py app/api/routes/reports.py tests/routes/test_report_editor_routes.py
git commit -m "feat: add report republish flow"
```

### Task 3: 实现 Vue 日报编辑器

**Files:**
- Modify: `frontend/src/types/admin.ts`
- Modify: `frontend/src/lib/api.ts`
- Modify: `frontend/src/views/ReportsView.vue`
- Modify: `frontend/src/styles/base.css`

**Step 1: Extend frontend types**

补充：

- `ReportDetail`
- `ReportEditorItem`
- `ReportUpdatePayload`

**Step 2: Extend API client**

补充：

- `getReport(reportId)`
- `updateReport(reportId, payload)`
- `publishReport(reportId)`

**Step 3: Implement editor UI**

在日报页增加：

- 日报详情加载
- 标题/导语编辑
- 条目上移/下移
- 分组名输入
- 移除条目
- 保存
- 重新发布

**Step 4: Build to verify**

Run: `cd frontend && npm run build`
Expected: PASS with no TypeScript/Vue errors

**Step 5: Commit**

```bash
git add frontend/src/types/admin.ts frontend/src/lib/api.ts frontend/src/views/ReportsView.vue frontend/src/styles/base.css
git commit -m "feat: add report editor ui"
```

### Task 4: 全量回归

**Files:**
- Test: `tests/routes/test_report_editor_routes.py`
- Test: `tests/routes/test_process_and_report_jobs.py`

**Step 1: Run report-related backend tests**

Run:

```bash
python -m pytest tests/routes/test_report_editor_routes.py tests/routes/test_process_and_report_jobs.py -q
```

Expected: PASS

**Step 2: Run full backend test suite**

Run:

```bash
python -m pytest -q
```

Expected: PASS

**Step 3: Run frontend build**

Run:

```bash
cd frontend
npm run build
```

Expected: PASS

**Step 4: Commit**

```bash
git add .
git commit -m "feat: add editable report publishing workflow"
```
