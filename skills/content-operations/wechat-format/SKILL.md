---
name: wechat-format
description: Use when turning an article into WeChat-compatible HTML, running a source-to-WeChat production workflow, or explicitly requesting covers, draft publishing, or comment replies. Routes source rewriting and visual production to sibling skills; preserves approved Markdown.
---

# wechat-format

公众号一键排版技能。把任意文本内容（Markdown、纯文本、格式粗糙的笔记）转成微信公众号兼容的排版 HTML，AI 自动理解内容结构并增强排版，可视化选择主题后一键复制粘贴到微信后台。可选生成封面图、推送草稿箱。

## 脚本目录

`{baseDir}` = 本 SKILL.md 所在目录。执行脚本时用 `{baseDir}/scripts/xxx.py` 替换为实际绝对路径。

| 脚本 | 用途 |
|------|------|
| `scripts/article_workflow.py` | 默认一命令文章包装流程：上游台账与视觉资产交接、术语检查、结构化、增强、画廊、最终主题输出、可选封面 |
| `scripts/check_dependencies.py` | 检测依赖；带 `--install` 时安装缺失 Python 包 |
| `scripts/format.py` | 排版：Markdown → 微信兼容 HTML |
| `scripts/publish.py` | 推送：HTML → 公众号草稿箱 |
| `scripts/comment_reply.py` | 评论自动回复（可选） |
| `scripts/generate.py` | 封面生成脚本（需配合同级 `../wechat-cover/config.json`） |

## Python 调用约定

Windows 不要假设全局 `python` alias 可用。优先使用 Codex bundled runtime：

```powershell
$Python = Join-Path $env:USERPROFILE ".cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
& $Python --version
```

下面的 PowerShell 示例都使用 `& $Python`。在 Linux/macOS 或可移植 shell 中使用 `python3`。

## 配置

纯排版无需创建 `config.json`。如果文件不存在，脚本会使用内置默认配置：

- 输出目录：`{repoRoot}/output/wechat-format/tmp`
- 默认 workflow 产物根目录：`{repoRoot}/output/wechat-format/article-workflows`
- Vault 根目录：当前用户主目录
- 默认主题：`newspaper`

发布草稿箱、评论回复、封面生成或自定义输出目录时，再创建 `config.json`（参考 `config.example.json`）：

```json
{
  "output_dir": "../../../output/wechat-format/tmp",
  "vault_root": "/path/to/your/obsidian/vault",
  "image_search_paths": [],
  "settings": {
    "default_theme": "newspaper",
    "auto_open_browser": true
  },
  "wechat": {
    "app_id": "YOUR_APP_ID",
    "app_secret": "YOUR_APP_SECRET",
    "author": "作者名"
  },
  "cover": {
    "output_dir": "../../../output/wechat-cover",
    "image_generation_script": ""
  },
  "ai": {
    "url": "",
    "api_key": "",
    "model": ""
  }
}
```

- `wechat` 部分仅推送或评论回复时需要，纯排版可不填
- `cover` 部分仅生成封面时需要
- `config.json` 已在 `.gitignore` 中，不会被提交

## Instructions

### 完整工作流

#### 第 0 步：先选择简单润色类型（强制门禁）

只要本次流程会执行文章简单润色，就必须先让用户二选一：

1. **专业文章**（`professional`）：面向具备相关背景的读者，保留专业深度和标准术语，表达严谨、简洁、克制。
2. **科普文章**（`popular-science`）：面向感兴趣的非专业读者，降低术语密度，对无法避免的术语做简短语境解释，提升可读性但不扩写事实。

这是一个无默认值的阻塞选择：

- 不根据文章题材、用户身份或历史偏好自行推断。
- 不把任一选项标为默认或推荐项。
- 用户未明确选择时，不读取正文、不检测依赖、不创建输出目录，也不进入结构化、增强、选主题、封面或发布步骤；只询问这一个选择并等待回复。
- 用户选择后，把结果通过 `--polish-style professional` 或 `--polish-style popular-science` 传给 `article_workflow.py`。
- 如果使用 `--non-interactive`，必须同时显式提供 `--polish-style`，否则脚本立即失败。
- `--skip-ai`、`--preserve-content` 或 `--skip-terminology` 明确跳过简单润色时，不要求此选择。

#### 第 0.5 步：依赖检测

首次使用，或用户环境不确定时，先检测依赖：

```powershell
& $Python {baseDir}/scripts/check_dependencies.py
```

Portable shell:

```bash
python3 {baseDir}/scripts/check_dependencies.py
```

如果提示缺少依赖，先询问用户是否允许安装。用户同意后执行：

```powershell
& $Python {baseDir}/scripts/check_dependencies.py --install
```

Portable shell:

```bash
python3 {baseDir}/scripts/check_dependencies.py --install
```

不要在未获得用户确认时自动安装依赖。安装完成后再继续排版或发布流程。

#### 第 1 步：确认文章

1. 如果用户给了文件路径，直接读取
2. 如果没给路径，问用户要文章路径
3. 读取文章内容，确认标题和字数

#### 第 1.0 步：技术来源到公众号的集成链路

当输入仍是论文、文档、报告、转录、仓库说明或粗糙技术材料，并且用户要求公众号成稿时，不要直接交给排版脚本：

1. 读取并遵循 [`../technical-source-to-public-article/SKILL.md`](../technical-source-to-public-article/SKILL.md)，生成稳定的 `article.md` 和 `source-notes.md`。
2. 用户要求正文配图、图解或完整视觉时，读取并遵循 [`../technical-article-visual-director/SKILL.md`](../technical-article-visual-director/SKILL.md)。使用 Produce 模式生成 `article-with-visuals.md`、`visual-plan.md` 和 `images/`；仅规划时不要伪称已有视觉资产。
3. 内容、章节、图片路径和图注稳定后，使用本技能的 `article_workflow.py` 完成排版。最终稿必须加 `--preserve-content`，避免再次改写已经核查和配图的正文。
4. 使用 `--source-notes`、`--visual-plan` 和 `--assets-dir` 传递上游产物，并加 `--strict-assets` 阻止缺图文章进入最终渲染。

完整交接命令：

```powershell
& $Python {baseDir}/scripts/article_workflow.py `
  --input "<visual-output>/article-with-visuals.md" `
  --source-notes "<source-output>/source-notes.md" `
  --visual-plan "<visual-output>/visual-plan.md" `
  --assets-dir "<visual-output>/images" `
  --preserve-content `
  --strict-assets `
  --theme apple-code `
  --no-open `
  --non-interactive
```

如果用户不需要正文视觉，直接把 `article.md` 作为 `--input`，传入 `--source-notes` 并省略 `--visual-plan` 与 `--assets-dir`。如果用户已经提供审核通过的最终 Markdown，也可以从本步骤直接进入排版。

#### 第 1.1 步：默认使用一命令文章包装流程

对重复性的文章包装任务，默认使用 `scripts/article_workflow.py`。除非用户明确要求手动控制结构化、主题渲染或只运行单步排版，不要把 `format.py --gallery` 当作首选入口。

`article_workflow.py` 会执行本技能的 repo-local 标准流程：

1. 检测依赖
2. 复制源文，并归档可选来源台账和视觉方案
3. 生成术语润色稿和术语修改表，或保留已审核最终稿
4. 生成 structured / enhanced Markdown，或保留已审核结构
5. 搬运 Markdown 引用的本地图片并重写为稳定的 `render/images/` 路径
6. 打开 26 主题 gallery，或用 `--theme` 直接指定主题
7. 保存最终主题输出、manifest，可选生成 ByteDance 预览和封面

PowerShell：

以下命令以用户已选择“专业文章”为例；选择“科普文章”时改为 `--polish-style popular-science`，不得把示例值当作默认值。

```powershell
$Python = Join-Path $env:USERPROFILE ".cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
$env:PYTHONIOENCODING = 'utf-8'
& $Python {baseDir}/scripts/article_workflow.py --input "文章路径.md" --polish-style professional --bytedance-preview --cover
```

Portable shell：

```bash
PYTHONIOENCODING=utf-8 python3 {baseDir}/scripts/article_workflow.py --input "文章路径.md" --polish-style professional --bytedance-preview --cover
```

常用变体：

```powershell
# 已知主题，跳过交互式主题选择
& $Python {baseDir}/scripts/article_workflow.py --input "文章路径.md" --polish-style professional --theme apple-code

# 不打开浏览器窗口，适合远程或批处理环境
& $Python {baseDir}/scripts/article_workflow.py --input "文章路径.md" --polish-style professional --theme apple-code --no-open

# 没有 ai.url / ai.api_key / ai.model 时，只运行确定性的后续排版步骤
& $Python {baseDir}/scripts/article_workflow.py --input "文章路径.md" --skip-ai
```

默认输出：

```text
{repoRoot}/output/wechat-format/article-workflows/<article-slug>/
  source/
  upstream/
  markdown/
  render/images/
  gallery/
  selection/
  final/<theme>/
  bytedance/
  cover/
  manifest.json
```

使用该脚本完成时，最终回复应给出 `manifest.json`、最终 `preview.html`、`article.html`、术语修改表，以及可选封面路径。脚本已经覆盖第 1.2 步到第 3 步；仅在需要人工改写中间稿或用户要求手动流程时，才按文末链接读取手动步骤。

## 按需操作参考

仅在执行对应操作时读取 [workflow-details.md](references/workflow-details.md) 的相关章节：

- 手动润色、结构化、容器增强或单步排版：第 1.2–4 步。技术稿须保留术语修改记录与不确定项；仅排版时跳过润色。
- 选主题或调整参数：参数说明、可用主题、内置排版增强。
- 用户要求封面或推送：封面图生成、推送到公众号草稿箱。`publish.py --dry-run` 仍会上传图片，不是离线预演。
- 历史归档文章：Archived Article Handoff，优先通过归档技能的桥接脚本暂存图片与元数据。

交付前检查 manifest、最终 HTML、图片路径和术语记录。只有实际执行了封面、上传或草稿创建，才报告相应结果。
