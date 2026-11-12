# 技能路由与交接

先按用户要求的交付物选一个主技能，仅加载当前阶段的 SKILL.md 和必要参考。已完成的正文、来源台账、图片和用户选择通过路径交接，不复制整份技能指令，不重复生成已验收产物。

## 内容生产

| 输入 → 目标 | 主技能 | 按需交接 |
|---|---|---|
| 音视频 → 转录 | video-transcriber | 要文章才交 source-to-public-article；要导图才交 mindmap-builder |
| 原始来源 → 新文章 | technical-source-to-public-article | article.md + source-notes；已有成稿无需再次改写 |
| 现有文章 → 术语与表达修订 | technical-article-polisher | 最终 Markdown + 修改表；无需自动再走来源改写 |
| 成稿 → 正文配图及落位 | technical-article-visual-director | article-with-visuals.md + visual-plan + images |
| 成稿 → 单页信息图 | article-infographic | ImageGen 图片 + 提纲 + 提示词；横竖版按选择，不要求先排版 |
| 成稿 → 微信 HTML | wechat-format | 已审核正文用 preserve-content；按用户需要调用信息图或封面 |
| 封面需求 → 封面 | wechat-cover | 返回封面资产，不代替正文图解 |
| 历史文章 → 归档 | wechat-history-article-archive | 归档内容与本地图片；重新排版才交 wechat-format |
| Office 文件操作 | office-cli-skill | 通用文档/表格/演示；公文规范排版选 official-format-pro |

所有交接均以用户目标为条件。缺少证据时回查具体主张，不重跑整条链；下游仅在相关正文或数据变化时重做对应产物。

## 其他场景的边界

| 目标 | 选择与关系 |
|---|---|
| 技术概念理解 | technical-cognition-framework；需要可视成果再选下列图形技能 |
| 代码依赖图 / 通用架构流程 / 离线思维导图 | 分别选择 drawio-skill / excalidraw / mindmap-builder，三者是替代入口 |
| 发布已有导图 | mindmap-publisher，仅显式发布需求触发 |
| 日常记忆 / 系统清洗 | obsidian-memory / obsidian-memory-cleanup，清洗不作为日常检索必经步骤 |
| Dify 本地 DSL / 远端操作 | dify-dsl-app-builder / dify-console-admin-api；仅远端交付才衔接 |
| 后端契约诊断 / 数据验证 | backend-log-contract-trace；需要查库时调用 python-db-query |
| 网站重建 / Python 离线依赖 | website-rebuild / python-offline-dependency-packager，各自独立 |
| Docker 应用升级或隔离演练 | docker-app-upgrade，保留现有配置与持久化数据 |
| 直连、SSH 或 VPS 代理排障 | network-troubleshooting，沿实际路径定位并复测 |
| 航天云课堂连播 | casic-course-autoplay，按用户明确要求播放、检查进度或恢复 |
| 个股技术分析 / 隔夜板块影响 | stock-analysis-system / us-sector-index-impact-report，两条独立路径 |
| 技能维护验收 | skill-linter，检查结构与路由，不是普通业务任务的前置步骤 |

## 路由验收例

- “这篇文章排版，不改内容”：wechat-format 保留正文；不自动润色、配图或生信息图。
- “生成横版单页概览”：article-infographic，复用横版选择，无需运行 wechat-format。
- “给文章配三张图并插入”：technical-article-visual-director Produce，不转成单页概览。
- “把论文写成公众号文章”：来源成文；只有要求 HTML 时进入排版。
- “画仓库 import 依赖”：drawio-skill；一般业务流程选 excalidraw。
- “生成本地 Dify DSL”：builder 完成本地交付，不自动调用远端管理。

地图源文件为 `images/skills-map.svg`；新增或迁移技能时同时核对目录数量、节点、箭头条件和本表。`images/skills-map.png` 从同版 SVG 导出，两者同步更新。
