---
name: dify-dsl-app-builder
description: Use when designing or updating Dify workflow/advanced-chat DSL from requirements, generating a local DSL file, or delivering it to a Dify app. Local generation does not require admin credentials; remote operations use dify-console-admin-api.
---

# Dify DSL App Builder

## 选择交付范围

- **本地 DSL**。按需求新建或编辑用户指定的 DSL 文件，新建文件默认放在业务项目的 `output/dify-dsl-app-builder/`。已给清楚的本地需求直接生成。应用模式、目标版本或输入输出契约缺失且会影响设计时，合并询问关键缺项。模式未指定时采用 `workflow`，对话型需求采用 `advanced-chat`。本地交付无需管理员凭据。
- **远端交付**。用户明确要求创建、更新或导入远端应用时，读取 [dify-console-admin-api](../dify-console-admin-api/SKILL.md)，按其操作授权和确认规则执行。仓库入口为 `skills/ai-application-delivery/dify-console-admin-api/SKILL.md`。如果用户只要求设计或生成 DSL，交付本地文件。

## 设计与本地验证

1. 复用用户提供的 DSL、相同版本的导出或仓库 fixture。读 [dsl-import-rules.md](dsl-import-rules.md)，按实际需要加载下表中的节点参考。
2. 确定输入变量和默认值、节点链路、插件或模型等依赖、输出格式和错误处理。用户要求先审方案，或有影响交付的设计选项待定时，先给方案和待确认项。
3. 保存 DSL，从业务项目目录调用本技能自带的 [校验脚本](scripts/validate_dsl.py)。以下命令中的技能目录和 Python 解释器请替换为本机路径；JSON 仅需 Python，YAML 需要 PyYAML。

   ```powershell
   & 'C:\path\to\python.exe' 'C:\path\to\dify-dsl-app-builder\scripts\validate_dsl.py' --input .\app.yml
   ```

   ```bash
   python3 /path/to/dify-dsl-app-builder/scripts/validate_dsl.py --input ./app.yml
   ```

   脚本检查节点和边的 ID、连接端点、边类型和 handle，定位选择器及模板中引用的节点，并核对开始节点的输入名和代码节点声明的输出名。运行时变量、插件输出和嵌套字段还需目标环境核实。退出码为 0 表示这些静态检查通过。

## 远端交付

1. 将已验证 DSL、环境和 workspace，以及新应用名或 `APP_ID` 交给 Console 技能。更新以远端现状为输入时，先导出 `include_secret=false` 的备份并据此编辑。交接备份路径，覆盖导入前复用该备份。
2. 由 Console 技能处理创建、覆盖导入和 `202 pending`。有未获授权的影响或待确认的告警时，保留本地结果并等待答复。API 失败时沿 Console 技能排查，直接写数据库属于另行授权的操作。
3. 导入完成后重新导出，比对输入变量、关键节点与配置、输出字段。交付 DSL、应用 ID、适用的备份路径和实际验证结果。远端运行验证按用户要求及可用环境执行。

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
