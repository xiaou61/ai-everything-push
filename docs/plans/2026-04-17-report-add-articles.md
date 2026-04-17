# 日报手动加入文章 Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 让后台可以把同一天、已处理完成但未入选的文章手动加入已生成日报。

**Architecture:** 继续复用现有日报详情和编辑接口，在详情接口附带候选文章列表，并扩展保存 payload 以同时支持旧条目更新和新文章加入，不新增独立搜索接口。

**Tech Stack:** FastAPI、SQLAlchemy、Vue 3、Vite、TypeScript、pytest

---

### Task 1: 补候选文章与新增条目后端能力

**Files:**
- Modify: `app/services/report_service.py`
- Modify: `app/api/routes/reports.py`
- Test: `tests/routes/test_report_editor_routes.py`

**Step 1: Write the failing test**

```python
def test_report_detail_includes_candidate_articles(client):
    response = client.get("/admin/api/reports/1")
    assert response.status_code == 200
    assert len(response.json()["candidate_articles"]) == 1
```

**Step 2: Run test to verify it fails**

Run: `python -m pytest tests/routes/test_report_editor_routes.py::test_report_detail_includes_candidate_articles -q`
Expected: FAIL because candidate list missing

**Step 3: Write minimal implementation**

实现：

- `list_report_candidate_articles()`
- 报详情返回 `candidate_articles`
- 扩展 `update_report()` 支持新文章加入

**Step 4: Run test to verify it passes**

Run: `python -m pytest tests/routes/test_report_editor_routes.py -q`
Expected: PASS

**Step 5: Commit**

```bash
git add app/services/report_service.py app/api/routes/reports.py tests/routes/test_report_editor_routes.py
git commit -m "feat: support adding candidate articles into reports"
```

### Task 2: 实现日报编辑器候选文章区

**Files:**
- Modify: `frontend/src/types/admin.ts`
- Modify: `frontend/src/lib/api.ts`
- Modify: `frontend/src/views/ReportsView.vue`
- Modify: `frontend/src/styles/base.css`

**Step 1: Extend report detail types**

增加：

- `ReportCandidateArticle`
- `ReportUpdatePayload.items[].article_id`
- `ReportUpdatePayload.items[].id` 可为空

**Step 2: Add candidate UI**

在编辑器增加：

- 搜索框
- 候选文章卡片
- “加入日报”按钮

**Step 3: Save new items**

保存时把新条目一起提交给后端。

**Step 4: Build to verify**

Run: `cd frontend && npm run build`
Expected: PASS

**Step 5: Commit**

```bash
git add frontend/src/types/admin.ts frontend/src/lib/api.ts frontend/src/views/ReportsView.vue frontend/src/styles/base.css
git commit -m "feat: add candidate article panel to report editor"
```

### Task 3: 全量回归

**Files:**
- Test: `tests/routes/test_report_editor_routes.py`
- Test: `tests/routes/test_process_and_report_jobs.py`

**Step 1: Run focused tests**

Run:

```bash
python -m pytest tests/routes/test_report_editor_routes.py tests/routes/test_process_and_report_jobs.py -q
```

Expected: PASS

**Step 2: Run full backend suite**

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
git commit -m "feat: add manual article selection for reports"
```
