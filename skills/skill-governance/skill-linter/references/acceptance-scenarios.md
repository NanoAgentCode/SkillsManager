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

## Network troubleshooting cases

Use the observed evidence in each request as an offline fixture for `network-troubleshooting`.

| User request and evidence | Observable result |
|---|---|
| “我想直连这个站。系统解析到了旧地址，用正确 IP 的 `--resolve` 后原域名返回 200。” | Follow the direct route, confirm the original application uses the stale resolver or cache, then retest with normal DNS and TLS validation. |
| “我选了 `DIRECT`，但 TUN 开着，怎么确认？” The application log shows the full chain ending in `DIRECT`. | Report the observed application policy. For a physical-network test, verify the actual interface and route before claiming the result. |
| “VPS 的 IPv4 SSH 超时，IPv6 已登录。” A paired capture shows outgoing SYN-ACK at the VPS and no matching packet at the client. | Report a missing return packet in the tested flow. Preserve IPv6 access and prepare the evidence for escalation. The responsible network remains undetermined. |
| “节点 TCP 通了，但 FlClash 还是超时。” The active profile lacks the named node. After applying the correct profile, HTTPS returns 200 through the expected VPS. | Identify the runtime configuration issue, verify the complete proxy chain and actual exit, and record whether the original application action succeeded. |
| “代理已经能用，帮我验收。” A real HTTPS request uses the expected exit. The node has UDP disabled and the VPS has not rebooted. | Mark HTTPS forwarding verified. Record UDP and reboot recovery as untested and leave the running host up. |

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
