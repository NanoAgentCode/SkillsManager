---
name: dify-console-admin-api
description: Use when calling Dify Console APIs with ADMIN_API_KEY to create apps, import/export DSL, overwrite apps, confirm pending imports, or diagnose authentication. For designing DSL from requirements, use dify-dsl-app-builder.
---

# Dify Console Admin API

## 先收集参数

在给出 curl 或执行请求前，先确认用户提供了这些必需参数：

- `DIFY_BASE_URL`：Dify API 地址，例如 `https://dify.example.com` 或 `http://127.0.0.1:5001`。
- `ADMIN_API_KEY`：服务端配置的 admin key。
- `WORKSPACE_ID`：目标 workspace 的 `tenants.id`。
- 操作类型：创建应用、导出 DSL、导入 DSL、覆盖导入、确认导入。

根据操作类型继续收集附加参数：

- 创建应用：`APP_NAME`，可选 `APP_DESCRIPTION`。
- 导出 DSL：`APP_ID`，可选 `INCLUDE_SECRET`、`WORKFLOW_ID`。
- 导入 DSL：`YAML_CONTENT` 或 `YAML_URL`。
- 覆盖导入：额外需要 `APP_ID`，且只能覆盖 workflow 或 advanced-chat 应用。
- 确认导入：`IMPORT_ID`。

不要把 `ADMIN_API_KEY` 写入仓库文件、PR 描述、日志或长期保存的脚本。需要展示命令时，优先使用变量。

## 前置条件

运行中的 API 进程必须启用：

```env
ADMIN_API_KEY_ENABLE=true
ADMIN_API_KEY=<admin-key>
```

修改后必须重启 API 进程。如果请求返回 `401 Invalid token`，通常表示运行中的进程没有加载 admin key，或者 key 不正确。

## 执行操作

调用接口前读取 [api-operations.md](references/api-operations.md) 中的变量模板、请求头规则和所选操作（创建、导出、导入、覆盖或确认）章节；返回异常时查看排查部分。所有请求携带 Bearer admin key 和 `X-WORKSPACE-ID`。

导出默认 `include_secret=false`。报告真实 HTTP 状态与应用/导入 ID；`202 pending` 不是完成，须按返回状态处理确认导入。
