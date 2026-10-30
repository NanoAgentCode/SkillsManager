---
name: dify-dsl-app-builder
description: Use when designing or updating Dify workflow/advanced-chat DSL from requirements, generating a local DSL file, or delivering it to a Dify app. Local generation does not require admin credentials; remote operations use dify-console-admin-api.
---

# Dify DSL App Builder

涉及远端 Console Admin API 时，先读取同级 [dify-console-admin-api](../dify-console-admin-api/SKILL.md)。

## 基本原则

- 先给出 DSL 设计方案并征求用户确认，用户同意后再修改文件或调用接口。
- 优先编辑已有 DSL 文件；没有 DSL 文件时再创建新的本地 DSL 文件。
- 不要把 `ADMIN_API_KEY` 写入仓库文件、PR 描述、长期脚本或最终回复。
- 默认 `include_secret=false`，除非用户明确要求导出密钥。
- 覆盖更新前先导出旧 DSL 作为备份，避免丢失已有配置。
- Admin API 卡住或失败时，先报告错误和排查建议；只有用户明确授权，才允许直接写数据库。

## 参数收集

先确认操作类型：创建应用、更新应用、只生成 DSL。

- **只生成 DSL**：只收集需求、应用模式、目标 Dify 版本或参考 DSL、输出路径；不要求 Dify 地址、workspace 或管理员密钥。
- **创建或更新应用**：再收集 `DIFY_BASE_URL`、`ADMIN_API_KEY` 与 `WORKSPACE_ID`，并遵循 Console Admin API skill。

按操作类型继续确认：

- 创建应用：`APP_NAME`，可选 `APP_DESCRIPTION`。
- 更新应用：`APP_ID`，可选现有 DSL 文件路径。
- 只生成 DSL：目标文件路径或应用名称。

## DSL 设计流程

根据用户需求先形成方案：

1. 明确应用模式，默认使用 `workflow`。
2. 明确输入参数，包括变量名、类型、是否必填、默认值。
3. 明确节点链路，例如 `start -> http-request -> code -> end`。
4. 明确外部依赖，例如 HTTP API、插件、知识库、模型。
5. 明确输出字段和输出格式。
6. 明确错误处理策略，例如外部 API 失败时返回“未知”或错误信息。

方案确认后再生成 DSL。节点结构应参考当前仓库中已导出的 DSL 或测试 fixture，保持字段名和节点类型与 Dify 当前版本一致。

## 创建应用流程

1. 生成本地 DSL 文件。
2. 使用 `skills/ai-application-delivery/dify-console-admin-api/SKILL.md` 的创建应用接口创建 workflow 应用。
3. 使用返回的 `APP_ID` 覆盖导入 DSL。
4. 如果导入返回 `202 pending`，调用 confirm 接口。
5. 重新导出该应用 DSL，验证远端内容包含关键节点、变量和输出。

## 更新应用流程

1. 使用 `APP_ID` 导出当前 DSL，保存为备份文件。
2. 修改或生成新的本地 DSL。
3. 使用 `apps/imports` 传入 `app_id` 覆盖导入。
4. 如果导入返回 `202 pending`，调用 confirm 接口。
5. 重新导出该应用 DSL，验证远端内容包含关键节点、变量和输出。

## 验证要求

只生成 DSL 时，先运行 `quick_validate.py --input <dsl路径>`。它会检查节点/edge ID、连接端点、edge 的源/目标类型、必填 handle，以及变量选择器引用；这项静态检查不等同于远端导入或运行验证。

更新完成后至少验证：

- 远端导出的 DSL 能成功返回。
- 远端 DSL 包含预期输入变量。
- 远端 DSL 包含预期节点类型和关键配置。
- 远端 DSL 包含预期输出字段或输出文本。

最终回复只说明结果、文件路径、应用 ID 和验证结论；不要泄露 `ADMIN_API_KEY`。

## DSL 导入规则

生成或检查可导入 DSL 时，先阅读 [dsl-import-rules.md](dsl-import-rules.md)。该文件集中说明节点类型信息、edge 类型/连接规则、必填 edge 字段、迭代内部 edge 的特殊要求，以及可复用的通用 DSL builder 模式。

## 节点位置布局建议

节点从左到右按 x=80,384,688,992… 排列（间隔 304），y 统一 282。分支节点上下偏移约 ±130。

每个节点的外层通用字段：`id`、`height`（54/90/110/126/178）、`position`/`positionAbsolute`（x/y）、`selected: false`、`sourcePosition: right`、`targetPosition: left`、`type: custom`、`width: 242`。

## 节点参考

需要用到某类节点时，读取对应文件获取完整模板：

| 文件 | 包含节点 |
|---|---|
| [nodes-basic.md](nodes-basic.md) | `start`、`end`、`answer` |
| [nodes-logic.md](nodes-logic.md) | `if-else`、`variable-aggregator`、`iteration` |
| [nodes-processing.md](nodes-processing.md) | `code`、`template-transform`、`parameter-extractor` |
| [nodes-ai.md](nodes-ai.md) | `llm`、`agent`（Function Calling / MCP SSE）、将 Dify 工具暴露为 MCP 服务（mcp_compat_dify_tools） |
| [nodes-external.md](nodes-external.md) | `http-request`、`tool`、`knowledge-retrieval` |
| [dsl-import-rules.md](dsl-import-rules.md) | 导入规则、edge 结构、迭代内部连接、通用 DSL builder 模式 |
