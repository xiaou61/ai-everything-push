# 前端管理台说明

这个目录是项目的独立后台前端，技术栈为：

- Vue 3
- TypeScript
- Vite

## 本地开发

```powershell
npm install
npm run dev
```

默认开发地址：

`http://127.0.0.1:5173/admin/`

## 生产构建

```powershell
npm run build
```

构建结果输出到 `frontend/dist`，由 FastAPI 直接托管。

## 主要页面

- `src/views/DashboardView.vue`
- `src/views/SourcesView.vue`
- `src/views/SourceRulesView.vue`
- `src/views/ArticlesView.vue`
- `src/views/ModelsView.vue`
- `src/views/ReportsView.vue`
- `src/views/JobsView.vue`
- `src/views/DatabaseView.vue`
- `src/views/SettingsView.vue`

## 关键文件

- `src/lib/api.ts`：后台 API 请求封装
- `src/types/admin.ts`：后台类型定义
- `src/styles/theme.css`：主题变量
- `src/styles/base.css`：页面样式
- `src/layouts/AdminLayout.vue`：后台主布局

## 当前约定

- 所有后台接口统一走 `/admin/api/*`
- 管理台路由统一挂在 `/admin/`
- 开发模式由 Vite 提供前端，构建模式由 FastAPI 提供静态资源

## 开发提醒

- 改完前端后记得跑一次：

```powershell
npm run build
```

- 如果接口字段变化，要同步更新：
  - `src/types/admin.ts`
  - `src/lib/api.ts`
  - 对应视图组件
