---
name: obsidian-memory-cleanup
description: Use when explicitly asked to audit or semantically clean a local Obsidian memory Vault, including deduplication, fragment merging, stale-fact verification, and reclassification. Excludes ordinary retrieval, single candidate writes, and index-only maintenance.
---

# Obsidian 记忆清洗

把清洗结果落实到正式记忆内容，而不是只重建索引或报告文件数量。自动审计用于定位问题，主题权威性、事实新旧和合并取舍必须结合正文与来源判断。

## 开始前

1. 从用户指令或当前项目上下文取得 Vault 绝对路径；路径不明确时询问，不猜测或沿用其他机器路径。
2. 完整读取 Vault 的 `AGENTS.md`、`90-System/Memory-Rules.md`、`90-System/Codex-Memory-Index.md`。若同仓库存在 `../obsidian-memory/SKILL.md`，同时读取并遵守其生命周期与安全规则。
3. 确认用户要求的是全库清洗、指定范围清洗还是只读审计。全库清洗才允许遍历全部正式目录。
4. 运行只读审计建立基线：

```powershell
powershell -ExecutionPolicy Bypass -File .\skills\knowledge-visualization\obsidian-memory-cleanup\scripts\audit-memory-vault.ps1 `
  -VaultPath "<Vault 绝对路径>"
```

在 PowerShell 7 或非 Windows 环境可用 `pwsh -File` 调用同一脚本。

## 清洗流程

1. 盘点 `10-Projects/`、`20-Knowledge/`、`30-Decisions/`、`40-Preferences/` 中的正式记忆，按 `scope`、`status`、主题和来源建立清单。
2. 为每个主题确定一条权威记忆。检查完全重复、跨文件重复事实、项目背景与技术知识混写、同一偏好在项目和全局范围重复维护等情况。
3. 读取正文后再合并碎片。保留可复用事实、适用边界、证据和必要历史；删除模板化重复、过细快照和无长期价值的过程描述。
4. 对版本、数量、路径、命名、配置、测试状态和运行行为等易漂移事实，核对当前源码、配置、Git 状态或其他权威来源。无法验证时不得继续写成当前事实，应标为 `uncertain` 或 `stale`。
5. 按分类职责调整内容：项目背景进 `10-Projects/`，技术与工程知识进 `20-Knowledge/`，重要选择及原因进 `30-Decisions/`，稳定用户偏好进 `40-Preferences/`。
6. 当前事实与历史冲突时不静默覆盖：更新或创建当前权威记忆，把旧记忆标为 `superseded` 并填写 `superseded_by`。仅在内容没有独立历史价值时才合并后删除重复文件。
7. 更新所有受影响的双向链接和历史清单；不要修改 `.obsidian/`、`.trash/` 或其他本地界面状态。
8. 按 [清洗手册](references/cleanup-playbook.md) 完成逐项验收。审计脚本的“无报错”不能替代语义复核。

## 收尾验收

再次运行 `audit-memory-vault.ps1`，并完成以下检查：

- 每条正式记忆均已纳入审核，状态、来源和范围可解释。
- 无断链、冲突标记、正式目录中的候选记忆或未说明的高相似度笔记。
- 易漂移事实已有当前证据，或已明确降级为历史、`stale`、`uncertain`、`superseded`。
- 用当前关键词和旧关键词各做一次检索回归，确认当前事实优先且历史结论不会冒充现状。
- 使用 `../obsidian-memory/scripts/rebuild-index.ps1` 重建本地索引。
- 向用户报告审核总数、实际修改数、合并或替代关系、事实核验范围、验证结果和 Git 状态。

只有用户明确要求时才提交或推送。执行 Git 操作前读取 Vault 的 `90-System/Git-Sync-Rules.md`，并排除 `.obsidian/`、`.trash/` 与本地生成索引。

## 资源

- `scripts/audit-memory-vault.ps1`：只读检查 Frontmatter、状态、双向链接、重复正文、相似内容、敏感信息和索引新鲜度。
- `references/cleanup-playbook.md`：完整清洗时使用的语义判断、事实核验、分类和验收清单。
- `tests/test-audit-memory-vault.ps1`：审计脚本的临时 Vault 回归测试。
