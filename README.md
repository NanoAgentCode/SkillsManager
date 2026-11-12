# skills-manager

按业务场景组织的可复用 AI agent skills 仓库，兼容 Codex、Claude、Gemini 和 GLM。技能执行流程以各自的 `SKILL.md` 为准，根目录只保留项目入口，详细说明统一维护在 `docs/`。

![Skills 业务场景地图](images/skills-map.svg)

[技能路由与交接关系](docs/skill-relationships.md) · SVG 为当前地图，按交付目标选择技能，连线不代表强制流水线。

## 快速开始

1. 从 [技能索引](docs/skill-index.md) 选择最接近业务目标的 skill。
2. 完整阅读目标 `SKILL.md`。
3. 按 skill 要求加载 `scripts/`、`references/`、`assets/` 或模板。
4. 默认把生成产物写入 `output/<skill-name>/`。

通用调用方式：

```text
请先阅读 AGENTS.md，再阅读 <skill-path>/SKILL.md，并严格按该 skill 的流程完成任务。
```

## 业务场景

| 场景 | 目录 | 主要能力 |
|---|---|---|
| 内容运营 | `skills/content-operations/` | 转写、技术来源成文、文章润色、视觉策划、Office 文档处理、公文排版、公众号排版、封面与历史文章归档 |
| 知识可视化 | `skills/knowledge-visualization/` | 支持检索、候选归档和全量语义清洗的 Obsidian 外部记忆、技术认知框架、draw.io、Excalidraw、离线思维导图与静态发布 |
| AI 应用交付 | `skills/ai-application-delivery/` | Dify 应用创建、DSL 设计、导入、更新与验证 |
| 工程运维 | `skills/engineering-operations/` | 授权网站的取证式镜像与高保真重建、Python 依赖版本交互查询与离线打包、数据库安全查询、Windows/Linux MinIO 对象检查、元数据/执行计划检查、后端日志与数据契约追踪、直连与 VPS 网络排障 |
| 市场研究 | `skills/market-intelligence/` | 股票技术分析、美股行业复盘与跨市场影响研究 |
| 技能治理 | `skills/skill-governance/` | skill 结构、元数据、链接、兼容入口与敏感信息检查 |

完整目录树和迁移映射见 [业务场景目录说明](docs/directory-structure.md)。

## 文档

- [技能索引](docs/skill-index.md)：正式的仓库技能目录和使用场景。
- [业务场景目录说明](docs/directory-structure.md)：目录树、场景边界和维护规则。
- [仓库操作指南](docs/repository-operations.md)：调用、Python 启动器、校验、输出和安全约定。
- [平台兼容说明](docs/platform-compatibility.md)：Codex、Claude、Gemini、GLM 的入口和差异。

## 常用入口

- 航天云课堂课程连播：[技能说明](skills/engineering-operations/casic-course-autoplay/SKILL.md)，含进度检查与异常恢复；Windows 上的 Bash 脚本需要 Git Bash / WSL。

- [Docker 应用升级](skills/engineering-operations/docker-app-upgrade/SKILL.md)，含 [MaxKB 升级示例](skills/engineering-operations/docker-app-upgrade/examples/maxkb.md)
- [网络故障排查与修复](skills/engineering-operations/network-troubleshooting/SKILL.md)，涵盖直连、SSH、VPS 代理及 FlClash 分流。


- 技术来源转公众文章：[`skills/content-operations/technical-source-to-public-article`](skills/content-operations/technical-source-to-public-article/SKILL.md)
- 技术文章视觉策划：[`skills/content-operations/technical-article-visual-director`](skills/content-operations/technical-article-visual-director/SKILL.md)
- 微信公众号排版：[`skills/content-operations/wechat-format`](skills/content-operations/wechat-format/SKILL.md)
- Office 文档 CLI：[`skills/content-operations/office-cli-skill`](skills/content-operations/office-cli-skill/SKILL.md)
- 党政机关公文排版：[`skills/content-operations/official-format-pro`](skills/content-operations/official-format-pro/SKILL.md)
- Obsidian 外部记忆：[`skills/knowledge-visualization/obsidian-memory`](skills/knowledge-visualization/obsidian-memory/SKILL.md)，支持多关键词 All/Any 匹配与相关度排序
- Obsidian 记忆清洗：[`skills/knowledge-visualization/obsidian-memory-cleanup`](skills/knowledge-visualization/obsidian-memory-cleanup/SKILL.md)，支持正式记忆去重、碎片合并、事实核验、分类调整和索引验收
- 技术认知框架：[`skills/knowledge-visualization/technical-cognition-framework`](skills/knowledge-visualization/technical-cognition-framework/SKILL.md)
- Dify Console API：[`skills/ai-application-delivery/dify-console-admin-api`](skills/ai-application-delivery/dify-console-admin-api/SKILL.md)
- Dify DSL Builder：[`skills/ai-application-delivery/dify-dsl-app-builder`](skills/ai-application-delivery/dify-dsl-app-builder/SKILL.md)
- Dify DSL 导入规则：[`skills/ai-application-delivery/dify-dsl-app-builder/dsl-import-rules.md`](skills/ai-application-delivery/dify-dsl-app-builder/dsl-import-rules.md)
- 网站取证式重建：[`skills/engineering-operations/website-rebuild`](skills/engineering-operations/website-rebuild/SKILL.md)，支持授权公开网站的镜像存档、bundle 逆向、WebGL/滚动动画恢复与量化对拍验收
- Python 离线依赖打包：[`skills/engineering-operations/python-offline-dependency-packager`](skills/engineering-operations/python-offline-dependency-packager/SKILL.md)，支持交互输入依赖名；缺少精确版本或目标 Python 时只展示候选版本与补充提示，不下载文件
- 数据库查询与元数据检查：[`skills/engineering-operations/python-db-query`](skills/engineering-operations/python-db-query/SKILL.md)

## 根目录入口

`README.md` 和 `AGENTS.md` 是共享入口；`CLAUDE.md`、`GEMINI.md`、`GLM.md` 为对应客户端保留自动发现入口。详细平台规则不在根目录重复维护，统一见 [平台兼容说明](docs/platform-compatibility.md)。

## 校验

```powershell
.\scripts\run-python.ps1 .\skills\skill-governance\skill-linter\scripts\lint_skill.py . --repo-root .
.\scripts\run-python.ps1 .\skills\ai-application-delivery\quick_validate.py
```

更多校验命令见 [仓库操作指南](docs/repository-operations.md)。
