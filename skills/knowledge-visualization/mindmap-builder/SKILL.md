---
name: mindmap-builder
description: Create self-contained single-file offline mindmap HTML files from notes, documents, PDFs, reports, papers, books, outlines, or workflow outputs using bundled markmap assets. Use when the user asks to generate a mind map, convert content into a mindmap, produce a double-clickable HTML mindmap, create an overview-first mindmap for long documents, interactively expand chapters/sections into separate mindmaps, use a default overview then expand selected chapters/sections, use a conversational section-expansion mode, or render markmap output without relying on network/CDN access. Also trigger when the user explicitly asks for this mode in Chinese, such as 总览图, 章节展开, 对话式展开, 默认只展示总览, 用户可选章节, or 按需展开.
---

# Mindmap Builder

## Overview

Use this skill to turn user intent, notes, documents, or workflow outputs into Markdown that renders well as a markmap mindmap, then generate an offline local `.html` file that the user can open directly.

Prefer offline local HTML generation for desktop/client use. The skill bundles markmap browser assets in `assets/markmap/` and embeds their JS/CSS into each generated HTML. The final HTML must work independently, without a sibling asset folder or CDN access.

## Workflow

1. Identify the desired output:
   - Markdown only: produce clean markmap-oriented Markdown.
   - Offline local HTML: generate a single `.html` file with bundled JS/CSS embedded inline; this is the default.
   - Markdown only: produce clean markmap-oriented Markdown when the user does not need HTML yet.
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

Use this mode for books, long reports, papers, manuals, transcripts, research packs, or any input too large or too detailed for one readable map.

Default mode selection:

- If the user explicitly asks for overview-first, chapter/section expansion, conversational expansion, or on-demand expansion, use Long Document Mode regardless of page count.
- For papers up to 25 pages, default to a single paper overview mindmap unless the user asks for interactive expansion.
- For English text up to roughly 20,000 words, default to a single overview mindmap unless the user asks for interactive expansion.
- For Chinese text up to roughly 30,000 characters, default to a single overview mindmap unless the user asks for interactive expansion.
- For papers over 25 pages, default to Long Document Mode.
- For English text over roughly 20,000 words or Chinese text over roughly 30,000 characters, default to Long Document Mode when the content has document-like structure.
- For books, manuals, long reports, research packs, or documents over roughly 25 pages, default to Long Document Mode.
- If a document is 25 pages or fewer but has unusually dense structure, many appendices, many experiments, or many nested sections, prefer a compact overview and mention that sections can be expanded on request.
- If a long document user explicitly asks for one complete map, generate a compressed single overview and note that fine detail will be omitted.

Enter this mode when the user explicitly asks for any of these patterns:

- "overview first, then expand selected sections"
- "default overview only"
- "interactive chapter expansion"
- "conversational expansion"
- "section-by-section mindmap"
- "总览图"
- "默认只展示总览"
- "用户可选章节"
- "章节展开"
- "对话式展开"
- "按需展开"

Default behavior:

1. Build a compact overview map first.
   - Show the document title, purpose, major parts/chapters/sections, key themes, and important conclusions.
   - Do not include paragraph-level detail in the overview.
   - Keep each top-level branch selectable by name in the conversation, for example `Chapter 3`, `Methods`, or `Risk Analysis`.
   - Use the same section labels in the overview, section index, and detail maps.
   - If the overview is thematic, put original chapter/section labels under each theme so follow-up expansion has a clear target.
2. Preserve an internal section index in the conversation or a sibling Markdown file when useful.
   - Include stable section labels, source page/heading hints when available, and a one-line summary.
   - Use this index to answer follow-up requests such as "expand chapter 2" or "show the methods section".
3. On user selection, generate a separate detail mindmap for that chapter or section.
   - The detail map should use the selected section as the root.
   - Include local structure, key claims, evidence, examples, formulas, figures, risks, or terms as appropriate to the source type.
   - Keep it separate from the overview instead of appending everything into one giant map.
   - Make the detail root exactly match the selected overview/index label unless the user asks for a renamed concept map.
4. For nested follow-ups, repeat the pattern.
   - Section detail map -> subsection detail map -> concept map when needed.
   - Stop expanding when the requested level is readable and useful.

Recommended output structure:

```text
output/mindmap-builder/
  overview.md
  overview.html
  sections/
    chapter-01.md
    chapter-01.html
    methods.md
    methods.html
```

Name files with short stable slugs. If generating only one selected section, it is fine to create just the overview plus that section map.

Interaction pattern:

```text
source document
  -> section index
  -> overview mindmap using the same labels
  -> user selects an overview/index label in chat
  -> selected-section mindmap with the same root label
```

For papers:

- Overview branches usually include `Question`, `Method`, `Data`, `Findings`, `Limitations`, and `Implications`.
- Detail branches should preserve technical terms, definitions, datasets, metrics, equations, and experiment names when they matter.

For reports:

- Overview branches usually include `Background`, `Current State`, `Findings`, `Risks`, `Recommendations`, and `Next Steps`.
- Detail branches should preserve decision points, owners, numbers, timelines, and dependencies when present.

For books:

- Overview branches usually include `Part/Chapter Structure`, `Core Argument`, `Key Concepts`, `Characters/Actors` when relevant, and `Takeaways`.
- Detail branches should summarize chapter arcs, important scenes/examples, concepts, and cross-chapter links.

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
