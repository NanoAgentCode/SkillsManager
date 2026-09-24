---
name: obsidian-memory
description: 将本地 Obsidian Vault 作为 Codex 可检索、可审核、可视化的中文外部长期记忆系统。Use when 用户要求接入或日常使用 Obsidian 外部记忆、检索项目背景与偏好、写入或归档候选记忆、处理单条冲突或维护索引；全库去重、碎片合并、过期事实核查和分类调整使用 obsidian-memory-cleanup。
---

# Obsidian 外部记忆

将 Obsidian Vault 视为用户可检查的长期记忆源。不同设备上的 Vault 路径可能不同，不设置机器级默认目录；如果用户或当前项目上下文没有给出路径，先向用户索要本机的具体 Vault 路径，再执行检索、写入、归档或索引维护。

用户要求审核或清洗全部正式记忆时，改用同目录下的 `../obsidian-memory-cleanup/SKILL.md`；本 Skill 只处理日常检索、候选写入、单条冲突和索引维护。

## 工作流程

1. 从用户指令或当前项目上下文取得 Vault 路径；路径不明确时向用户询问，不根据盘符、用户名或历史机器目录猜测。
2. 确认 Vault 路径存在。
3. 读取 Vault 根目录的 `AGENTS.md`、`90-System/Memory-Rules.md` 和 `90-System/Codex-Memory-Index.md`。
4. 从当前任务提取 2 到 5 个关键词，运行 `scripts/search-memory.ps1`。多关键词默认要求同一文件全部命中，并按文件名、标题、标签和正文相关度排序；只读取排名靠前的少量相关笔记，不遍历整个 Vault。
5. 仅采用与当前任务相关、状态有效且来源清楚的记忆。用户当前指令始终优先于历史记忆。
6. 完成用户任务。
7. 完成任务后判断是否出现值得长期保存的信息。优先从用户纠正、最终有效的排障路径、验证结果和项目约定中提炼；只有稳定偏好、重要决策、可复用知识、项目长期背景或已验证方案才进入候选记忆。跨工具经验使用相同标准，不自动采集完整会话。
8. 按 `references/memory-schema.md` 和 Vault 中的模板写入 `00-Inbox/Codex/`。除非用户明确要求，不要直接写入正式记忆目录。
9. 用户确认并将候选记忆归档后，运行 `scripts/rebuild-index.ps1` 更新索引。

## 检索记忆

从仓库根目录运行：

```powershell
powershell -ExecutionPolicy Bypass -File .\skills\knowledge-visualization\obsidian-memory\scripts\search-memory.ps1 `
  -Query "检索词" -VaultPath "<用户提供的 Vault 绝对路径>"
```

需要限制范围时，传入 `-Scope "30-Decisions"`。检索结果只用于定位文件；读取后还要检查 `scope`、`status`、`source` 和适用场景。

多关键词以空格或中英文逗号、分号分隔，双引号可以保留短语。默认 `-MatchMode All` 要求同一文件命中全部关键词；需要扩大召回范围时使用 `-MatchMode Any`：

```powershell
powershell -ExecutionPolicy Bypass -File .\skills\knowledge-visualization\obsidian-memory\scripts\search-memory.ps1 `
  -Query 'RAG "向量检索"' -MatchMode All -Scope "20-Knowledge" -Limit 10 `
  -VaultPath "<用户提供的 Vault 绝对路径>"
```

结果按文件去重，`Limit` 表示最多返回的文件数；每条结果包含相关度分数、实际命中的关键词和代表性内容行。

## 写入候选记忆

- 文件名使用 `YYYY-MM-DD-简短主题.md`，同日重名时增加两位序号。
- 使用 `Templates/长期记忆模板.md`，内容使用中文。
- 写明摘要、适用场景、不适用场景、证据来源和关联笔记。
- 对任务过程提炼出的结论，写清任务或会话来源、相关文件或命令、验证方式与结果；仅保留复核所需的最少证据，不复制完整提示、响应或工具日志。历史记录只作为证据，易变化的结论使用前核对当前事实。
- 不保存密码、令牌、身份证号、银行卡号、私钥、Cookie 或未脱敏的个人敏感信息。
- 不把一次性任务步骤、临时错误、未经验证的推测保存为长期记忆。

## 处理冲突和过期

- 当前事实与旧记忆冲突时，不静默覆盖。
- 新建或更新正确记忆，将旧记忆的 `status` 改为 `superseded`，并填写 `superseded_by`。
- 暂时无法确认的内容使用 `uncertain`，已过时但没有替代项的内容使用 `stale`。
- 只有 `status: active` 且来源可信的记忆可以直接作为当前任务依据。

## 重建索引

候选记忆被人工归档后运行：

```powershell
powershell -ExecutionPolicy Bypass -File .\skills\knowledge-visualization\obsidian-memory\scripts\rebuild-index.ps1 `
  -VaultPath "<用户提供的 Vault 绝对路径>"
```

脚本只索引正式目录，不索引 `00-Inbox/Codex/`。

## 资源

- `scripts/search-memory.ps1`：按单关键词或多关键词搜索中文 Markdown 记忆，支持 All/Any 匹配和相关度排序。
- `tests/test-search-memory.ps1`：多关键词解析、匹配模式、排序、范围和限制参数的回归测试。
- `scripts/rebuild-index.ps1`：根据正式记忆目录重建 Obsidian 双向链接索引。
- `references/memory-schema.md`：记忆分类、字段和生命周期规范。
