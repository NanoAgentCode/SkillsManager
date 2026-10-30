---
name: drawio-skill
description: Use when analyzing Python, JavaScript/TypeScript, Go, or Rust import/module/package dependencies where an editable .drawio graph helps. Supports local image export; excludes general architecture, flowchart, UML, ERD, and other visualization requests.
---

# Draw.io Code Dependencies

Upstream: https://github.com/Agents365-ai/drawio-skill · License: MIT.

Generate editable code import/module/package dependency graphs. Other bundled generators remain available for upstream maintenance but do not expand this skill's trigger scope.

## Inputs and tools

Identify the repository/package boundary, language, dependency direction, and requested formats. Ask only for missing choices that change the graph. Default to `output/drawio-skill/` and PNG plus editable `.drawio`; honor an explicit output path.

- Use the matching `scripts/pyimports.py`, `scripts/jsimports.py`, `scripts/goimports.py`, or `scripts/rustimports.py` importer. Check its `--help` for input and filtering options.
- Graphviz (`dot`) is required by `scripts/autolayout.py`.
- Resolve the installed desktop CLI as `drawio`, `draw.io`, or its OS-specific application path; remember the exact binary and version. CLI export supports PNG/SVG/PDF/JPG.
- If CLI execution crashes or produces no output, stop repeating the same invocation. Use the fallback below; an external host retry is an option only when the environment permits it.

## Workflow

1. **Resolve style when relevant.** Use an explicitly named preset, otherwise a user preset marked `default`, otherwise built-in styling. Lowercase preset names. Search `~/.drawio-skill/styles/<name>.json`, then `styles/built-in/<name>.json`. An unknown explicit preset needs clarification, not silent substitution. Read [style-presets.md](references/style-presets.md) when applying or managing presets.
2. **Extract and lay out.** Generate the import graph with the matching importer; use `--group` where supported for package containers. Read [autolayout.md](references/autolayout.md) before running `scripts/autolayout.py`; prefer it for dense or roughly 15-plus-node graphs, with `--tune` when useful. Preserve dependency direction and report unresolved/dynamic import limits rather than inventing edges.
3. **Author only what extraction cannot express.** Read [xml-authoring.md](references/xml-authoring.md) before hand-writing XML. IDs `0` and `1` are reserved; every edge needs `<mxGeometry relative="1" as="geometry" />`. For a simple dependency graph using Mermaid conversion or ELK, read [mermaid-authoring.md](references/mermaid-authoring.md); these CLI features require version 30 or newer. Do not apply ELK again to a Mermaid-converted graph.
4. **Validate.** Run `scripts/validate.py` on the `.drawio` file before export. Check dangling edges, duplicate IDs, parents, and overlap; `--score` can compare layout variants.
5. **Preview and inspect.** Export a clean PNG without `-e`, normally using `--width 2000` and a suitable height limit for tall graphs. Read [export-guide.md](references/export-guide.md) for commands. Inspect clipping, card/label overlap, edge routing, title/footer space, and arrowheads. Fix and re-export up to two times; report remaining defects. If vision is unavailable, state that visual verification was skipped.
6. **Deliver.** Export requested final formats. Use `-e` for editable PNG/SVG/PDF and `.drawio.png` for embedded PNG. Run `scripts/repair_png.py` after every embedded PNG export; its guard is safe for already-valid files. Report source/export paths and validation limits. Incorporate requested feedback with targeted XML edits; regenerate only for layout-wide changes.

Keep cards, titles, notes, and legends out of each other's bounds. Route edges around unrelated shapes and move long labels into adjacent whitespace. Do not rely on z-order to hide collisions.

## Optional operations

Read only the resource needed for the current dependency graph:

| Need | Resource |
|---|---|
| Choose an importer or postprocessor | [toolbox.md](references/toolbox.md) |
| Package/repository shapes or brand icons | [shapes.md](references/shapes.md), `scripts/shapesearch.py`, `scripts/aiicons.py` |
| Compare dependency snapshots or show history | `scripts/drawiodiff.py`, `scripts/timelapse.py` |
| Explain, share, animate, or convert the graph | `scripts/explain.py`, `scripts/drawiohtml.py`, `scripts/svgflow.py`, `scripts/drawio2mermaid.py`, `scripts/drawio2pptx.py` |
| Overlay metrics | `scripts/heatmap.py` |
| Export failure or rendering defect | [troubleshooting.md](references/troubleshooting.md) |

## Fallback

If the CLI is missing or unusable, deliver `.drawio` XML and, when Python is available, use `scripts/encode_drawio_url.py` for a viewer URL (`--edit` for the editor). Do not claim PNG/SVG/PDF export succeeded. On Windows/WSL, consult [troubleshooting.md](references/troubleshooting.md) before opening fragment-bearing URLs. For Linux display failures, consult the export guide's headless options before retrying.
