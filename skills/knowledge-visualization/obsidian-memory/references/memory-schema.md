# 记忆数据规范

## 分类

| 目录 | 保存内容 | 典型示例 |
|---|---|---|
| `00-Inbox/Codex/` | 尚未确认的候选记忆 | 新发现的偏好、待核实结论 |
| `10-Projects/` | 跨任务持续有效的项目背景和状态 | 项目目标、架构边界、当前阶段 |
| `20-Knowledge/` | 可复用且相对稳定的知识 | 已验证方案、术语解释、操作经验 |
| `30-Decisions/` | 重要选择及其原因 | 技术选型、约束、被否决方案 |
| `40-Preferences/` | 用户明确或反复确认的稳定偏好 | 写作风格、沟通方式、交付习惯 |

## Frontmatter 字段

```yaml
---
type: memory
scope: global
status: candidate
source: user-confirmed
created: 2026-07-12
updated: 2026-07-12
tags:
  - codex-memory
related:
  - "[[相关主题]]"
superseded_by:
---
```

- `type` 固定为 `memory`。
- `scope` 使用 `global` 或明确项目名。
- `status` 使用 `candidate`、`active`、`uncertain`、`stale` 或 `superseded`。
- `source` 优先使用 `user-confirmed`、`project-file`、`verified-result`；推断内容使用 `inferred`。
- `created`、`updated` 使用 `YYYY-MM-DD`。
- `related` 使用 Obsidian 双向链接；被替代时填写 `superseded_by`。

## 长期价值判断

至少满足一项才创建候选记忆：

1. 未来多个任务仍可能使用。
2. 记录了重要决策及其理由。
3. 是用户明确或反复表达的稳定偏好。
4. 是已验证、可复用的解决方案。
5. 能避免未来重复犯错或重复调查。

不要保存一次性指令、未经核实的猜测、可以从源码即时获得的普通事实、敏感信息或没有适用范围的孤立结论。

## 从任务过程提炼

- 关注用户纠正、最终有效的排障路径、验证结果和项目约定；区分最终结论与未成功的尝试。
- 候选记忆的“证据与来源”记录可定位的任务或会话、相关文件或命令，以及验证方式与结果。只保留复核所需的最少信息，不复制完整会话。
- 来自其他代理工具的经验适用同一写入和审核标准；会话记录不能单独证明结论在当前项目中仍有效。对易变化的事实重新核验。

## 项目知识的证据分层

- 项目总览保存 README、架构文档、构建清单、仓库级配置、CodeGraph 状态等多个链路共同使用的公共证据，并作为专项记忆的检索入口。
- 专项记忆只保存该功能链路实际使用的源码文件、配置文件和验证命令；不要复制其他链路的证据清单。
- 公共证据只在总览维护一次；专项通过双向链接关联总览，降低重复内容的漂移风险。

## 生命周期

```text
candidate → active → stale
                  ↘ superseded
candidate → uncertain → active
```

候选记忆必须经过用户审核才能进入正式目录。发生冲突时保留历史记录，通过 `superseded_by` 建立替代关系。
