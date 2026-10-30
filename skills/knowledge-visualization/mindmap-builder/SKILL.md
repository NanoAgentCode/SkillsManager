---
name: mindmap-builder
description: Use when turning documents or notes into a self-contained offline HTML mindmap or markmap Markdown. Supports overview-first long documents and conversational chapter expansion (总览图、章节展开、按需展开). Publishing is handled by mindmap-publisher.
---

# Mindmap Builder

## Overview

Use this skill to turn user intent, notes, documents, or workflow outputs into Markdown that renders well as a markmap mindmap, then generate an offline local `.html` file that the user can open directly.

Prefer offline local HTML generation for desktop/client use. The skill bundles markmap browser assets in `assets/markmap/` and embeds their JS/CSS into each generated HTML. The final HTML must work independently, without a sibling asset folder or CDN access.

## Workflow

1. Identify the desired output:
   - Markdown only: produce clean markmap-oriented Markdown.
   - Offline local HTML: generate a single `.html` file with bundled JS/CSS embedded inline; this is the default.
2. Normalize the content into a mindmap hierarchy:
   - Use one `#` root title.
   - Use `##` for primary branches and `###` / list items for details.
   - Keep labels short; move long explanations into child bullets.
   - Preserve user-provided terminology unless it is clearly noisy or duplicated.
   - For long documents, default to an overview-first map, not a full-detail map.
3. Keep generated Markdown render-safe:
   - Prefer concise hierarchical outlines over long prose.
   - For large inputs, summarize before rendering.
   - Keep labels short enough to read after rendering.
   - Avoid huge flat lists; group details under meaningful branches.
4. Check local dependencies before rendering:
   - Check `node --version`, `npm --version`, and `markmap --version`.
   - If `markmap` is missing but Node/npm exist, ask the user to approve installing `markmap-cli`.
   - If approved, install with `npm install -g markmap-cli`, then re-check `markmap --version`.
   - If Node/npm are missing, tell the user Node.js must be installed first.
5. Generate local output:
   - Save generated Markdown and HTML under the repository root `output/mindmap-builder/` by default, unless the user specifies another path.
   - Save the Markdown next to the desired output when useful for iteration.
   - Prefer `scripts/render_offline_mindmap.ps1 -InputMarkdown input.md -OutputHtml output/mindmap-builder/output.html`.
   - This script runs `markmap`, embeds the four bundled runtime assets inline, and fails if separate resource dependencies remain. Keep source links as links; do not mistake citations for runtime dependencies. Use text-only nodes by default; embed requested images as data URLs if a single-file result is required. Write formulas as plain Unicode text unless math rendering dependencies can also be embedded; raw LaTeX may trigger extra KaTeX assets that this renderer rejects.
   - Give the user the local HTML path and state that it can be shared alone and opened offline.
6. Verify outputs:
   - Confirm the `.html` file exists and has non-trivial size.
   - Check the generated HTML contains the root title.
   - Confirm the HTML has inline scripts/styles and no script `src`, stylesheet `href`, or separate media/CSS resource dependencies.
   - Copy only the HTML to an empty verification directory and open it when browser tools are available; check nodes, expand/collapse, zoom, and toolbar without companion files.

## Long Document Mode

Read [long-document-mode.md](references/long-document-mode.md) for overview-first or conversational chapter expansion, books/manuals, or documents over roughly 25 pages, 20,000 English words, or 30,000 Chinese characters. Keep a stable section index and create separate maps for requested sections; an explicit single-map request takes precedence.

## Markdown Shape

Prefer this structure:

```markdown
# Topic

## Branch A
- Key point
- Key point
  - Supporting detail

## Branch B
### Sub-branch
- Detail
```

Avoid flat bullet dumps, table-heavy Markdown, deeply nested prose, embedded HTML, and code blocks unless the user explicitly wants those details preserved.

## Workflow Node Pattern

For local desktop/client use, no service is required:

```text
source content
  -> mindmap Markdown
  -> render_offline_mindmap.ps1
  -> self-contained single HTML file
  -> double-click/open in browser
```

## Troubleshooting

- Dependency checks fail: read `references/mindmap-service.md` for exact check/install commands.
- `markmap command not found`: install `markmap-cli` and ensure `markmap` is on PATH.
- HTML still references CDN: render with `scripts/render_offline_mindmap.ps1`, not raw `markmap`.
- Unsupported CLI output or separate media dependencies: inspect the reported resource; update the supported runtime mapping or embed media. Do not silently deliver a dependent HTML as a single file.
- Blank or unreadable HTML: reduce Markdown size or simplify nested content.
