# Skill Routing And Delivery Acceptance Scenarios

Use these scenarios after changes that affect a skill's trigger, handoff, or final artifact. For each, select the named skill from `docs/skill-index.md`, read its `SKILL.md`, and verify the listed observable result.

| User request | Expected skill | Observable result |
|---|---|---|
| “把这份技术报告写成有出处的中文公众号文章。” | `technical-source-to-public-article` | Markdown article plus source/claim notes. |
| “把一段会议录音转成带时间戳的纪要。” | `video-transcriber` | A non-empty transcript with source route recorded. |
| “把这个 Markdown 做成可双击打开的思维导图。” | `mindmap-builder` | A self-contained HTML with inline runtime assets, usable alone without a sibling folder or CDN. |
| “我只想生成一个 Dify DSL，暂时没有管理员权限。” | `dify-dsl-app-builder` | Local DSL and static validation, without collecting remote credentials. |
| “查一下库里有哪些表，不要改数据。” | `python-db-query` | Metadata output through a read-only path. |
| “把这个我有权使用的 WebGL 活动站离线存档，并验证断网可运行。” | `website-rebuild` | Confirmed page scope and L1 endpoint, immutable mirror plus manifest, and evidence from mirror, offline, CLEAN, and zero-external-request gates; no public deployment. |
| “把已有技术文章排成微信公众号 HTML。” | `wechat-format` | Final manifest and preview/article HTML. |

Record failures as one of: incorrect routing, missing input contract, missing output artifact, unsafe default, or unverifiable completion. Keep individual scenario fixtures small and free of credentials or user data.

## Boundary checks

These are routing/contract checks, not substitutes for executing a real media, model, API, or rendering task.

| User request | Expected route and boundary |
|---|---|
| “只改术语，不要重写文章。” | `technical-article-polisher`; preserve claims and return a terminology log. |
| “先规划配图，不要生成图片。” | `technical-article-visual-director` Plan; no claim of generated assets. |
| “只给公众号文章生成封面。” | `wechat-cover`; cover and prompt, no automatic publishing. |
| “给 Python 包画 import 依赖图。” | `drawio-skill`; editable dependency graph plus requested export. |
| “画订单服务架构图。” | `excalidraw` or another appropriate diagram tool; do not select `drawio-skill`. |
| “先做总览，之后再展开第三章。” | `mindmap-builder`; overview and stable section labels, detail maps on request. |
| “生成本地思维导图，双击看。” | `mindmap-builder`; do not invoke `mindmap-publisher`. |
| “把现有思维导图发布到服务器。” | `mindmap-publisher`; require hosting mapping and explicit path prefix. |
| “查询项目背景记忆。” | `obsidian-memory`; scoped retrieval, not a whole-Vault cleanup. |
| “清洗整个记忆库，合并重复内容。” | `obsidian-memory-cleanup`; semantic review plus structural audit. |
| “帮我分析 AAPL 的技术指标。” | `stock-analysis-system`; market/symbol and data freshness, not an overnight sector report. |
| “复盘昨晚美股板块对 A 股的影响。” | `us-sector-index-impact-report`; exact completed session and cited HTML. |
| “打离线包，但还没确定 Python 版本。” | `python-offline-dependency-packager`; clarify target version before downloading. |
