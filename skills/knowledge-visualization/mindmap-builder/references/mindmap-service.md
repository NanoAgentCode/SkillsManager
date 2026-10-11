# Mindmap Offline Local Reference

The renderer uses the static markmap assets bundled with this skill; no machine-specific source directory is needed.

## Default Local Client Flow

Use this path for desktop/client usage. It does not require FastAPI, `/preview`, `/html`, a running server, or CDN access.

```text
PDF/text/outline
  -> compact markmap Markdown
  -> bundled script generates offline HTML
  -> user double-clicks the HTML file
```

Command from the repository root (PowerShell):

```powershell
.\skills\knowledge-visualization\mindmap-builder\scripts\render_offline_mindmap.ps1 -InputMarkdown input.md -OutputHtml output/mindmap-builder/output.html
```

The script:

- Runs `markmap input.md --output <repo-root>/output/mindmap-builder/output.html --no-open`.
- Replaces supported CDN script/link tags with inline JS/CSS from bundled assets.
- Rejects remaining separate resource dependencies; citation hyperlinks are allowed.
- Outputs one self-contained HTML without creating `markmap-assets/`.

Portable PowerShell 7 invocation (Windows, macOS, or Linux with `pwsh` and markmap on PATH):

```sh
pwsh -File skills/knowledge-visualization/mindmap-builder/scripts/render_offline_mindmap.ps1 -InputMarkdown input.md -OutputHtml output/mindmap-builder/output.html
```

Bundled assets:

- `assets/markmap/d3.min.js`
- `assets/markmap/markmap-view.js`
- `assets/markmap/markmap-toolbar.js`
- `assets/markmap/markmap-toolbar.css`

## Dependency Check and Install

Before rendering local HTML, check dependencies:

```powershell
node --version
npm --version
markmap --version
```

Expected:

- `node` exists.
- `npm` exists.
- `markmap` exists.

If `markmap` is missing and Node/npm are available, ask the user for approval before installing because npm may access the network:

```powershell
npm install -g markmap-cli
```

After installation, verify again:

```powershell
markmap --version
```

If Node/npm are missing, do not try to install `markmap-cli` first. Tell the user Node.js is required, then install `markmap-cli` after Node/npm are available.

Validation:

- The output `.html` file exists.
- The file has non-trivial size.
- The root title appears in the generated HTML.
- Runtime scripts and toolbar styles are embedded inline.
- No separate script, stylesheet, media, or CSS resource dependencies remain.
- Copying only the HTML into an empty directory preserves rendering and interaction.
- Opening via `file:///.../output/mindmap-builder/output.html` works in a browser.

## Markdown Generation Rules

- Use a single root `#` heading.
- Use `##` for top-level branches.
- Use `###` for secondary clusters.
- Use bullets for leaves.
- Keep node labels compact, ideally under 20 Chinese characters or 8 English words.
- Convert paragraphs into parent-child relationships instead of preserving prose blocks.
- Remove repeated section titles, navigation text, boilerplate, and irrelevant metadata.
- For long source material, summarize first, then render the summary as Markdown.

Example:

```markdown
# 产品方案

## 用户目标
- 快速理解项目结构
- 生成可分享的预览链接

## 核心流程
- 收集输入
- 整理层级
- 调用 mindmap 服务
- 返回 HTML 预览

## 集成方式
- Dify HTTP 节点
- 自研 workflow adapter
- 手动 curl 调用
```

## curl Examples

Not applicable for the default local client flow. Use the PowerShell render script instead of HTTP calls.

## Common Failures

- `markmap command not found`: install Node.js and `markmap-cli`, then verify `markmap --version`.
- Local HTML is blank or too dense: reduce content length or simplify deeply nested Markdown.
- Browser shows blank while offline: inspect browser errors and verify the renderer embedded all four runtime assets.
- Legacy HTML depends on `markmap-assets/`: rerender its Markdown with the current script to produce a single file.
- Markdown contains images or external CSS: embed media as data URLs or simplify the map before rendering.
