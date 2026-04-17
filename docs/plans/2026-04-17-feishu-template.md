# 飞书推送模板可配置 Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 让飞书日报推送的标题和正文在后台可配置，不再写死在代码中。

**Architecture:** 继续复用 `system_settings` 保存飞书标题模板和正文模板，后端推送时读取配置并做轻量变量替换，设置页新增模板编辑和示例预览，不增加新的数据库表。

**Tech Stack:** FastAPI、SQLAlchemy、Vue 3、Vite、TypeScript、pytest

---

### Task 1: 增加飞书模板系统设置

**Files:**
- Modify: `app/services/system_setting_service.py`
- Test: `tests/routes/test_settings_routes.py`

**Step 1: Write the failing test**

```python
def test_default_settings_include_feishu_templates(client):
    response = client.get("/admin/api/settings")
    keys = {item["setting_key"] for item in response.json()}
    assert "feishu.report_title_template" in keys
```

**Step 2: Run test to verify it fails**

Run: `python -m pytest tests/routes/test_settings_routes.py::test_default_settings_include_feishu_templates -q`
Expected: FAIL because settings key missing

**Step 3: Write minimal implementation**

在默认设置中加入：

- `feishu.report_title_template`
- `feishu.report_body_template`

**Step 4: Run test to verify it passes**

Run: `python -m pytest tests/routes/test_settings_routes.py::test_default_settings_include_feishu_templates -q`
Expected: PASS

**Step 5: Commit**

```bash
git add app/services/system_setting_service.py tests/routes/test_settings_routes.py
git commit -m "feat: add default feishu template settings"
```

### Task 2: 实现飞书模板渲染与推送

**Files:**
- Modify: `app/services/notifier/feishu.py`
- Test: `tests/services/test_feishu.py`

**Step 1: Write the failing test**

```python
def test_push_report_to_feishu_uses_template_settings():
    result = push_report_to_feishu(session, date(2026, 4, 17))
    assert captured_payload["content"]["post"]["zh_cn"]["title"] == "日报：2026-04-17"
```

**Step 2: Run test to verify it fails**

Run: `python -m pytest tests/services/test_feishu.py -q`
Expected: FAIL because payload is still hardcoded

**Step 3: Write minimal implementation**

实现：

- 模板上下文构造
- 模板渲染函数
- 使用模板生成飞书标题和正文

**Step 4: Run test to verify it passes**

Run: `python -m pytest tests/services/test_feishu.py -q`
Expected: PASS

**Step 5: Commit**

```bash
git add app/services/notifier/feishu.py tests/services/test_feishu.py
git commit -m "feat: render feishu report message from templates"
```

### Task 3: 实现设置页模板编辑与预览

**Files:**
- Modify: `frontend/src/views/SettingsView.vue`
- Modify: `frontend/src/types/admin.ts`

**Step 1: Extend settings form**

增加：

- 飞书标题模板字段
- 飞书正文模板字段

**Step 2: Add preview**

使用前端样例数据本地渲染模板预览。

**Step 3: Save template settings**

把两个模板字段加入批量保存 payload。

**Step 4: Build to verify**

Run: `cd frontend && npm run build`
Expected: PASS

**Step 5: Commit**

```bash
git add frontend/src/views/SettingsView.vue frontend/src/types/admin.ts
git commit -m "feat: add feishu template editor in settings"
```

### Task 4: 全量回归

**Files:**
- Test: `tests/services/test_feishu.py`
- Test: `tests/routes/test_settings_routes.py`
- Test: `tests/routes/test_feishu_routes.py`

**Step 1: Run focused backend tests**

Run:

```bash
python -m pytest tests/services/test_feishu.py tests/routes/test_settings_routes.py tests/routes/test_feishu_routes.py -q
```

Expected: PASS

**Step 2: Run full backend tests**

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
git commit -m "feat: add configurable feishu push templates"
```
