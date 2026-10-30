---
name: excalidraw
description: Use when creating or editing editable .excalidraw flowcharts, architecture diagrams, or relationship sketches with PNG/SVG export. Use proactively when a diagram clarifies complex relationships; skip simple answers better served by prose or a table.
---

# Excalidraw Diagrams

Upstream: https://github.com/Agents365-ai/excalidraw-skill

License: MIT. This local copy is integrated under `skills/knowledge-visualization/excalidraw/`.

## Overview

Generate `.excalidraw` JSON files and export to PNG/SVG.

**Two export options:**
- **Kroki API** (`curl`) — zero install, SVG output only
- **excalidraw-brute-export-cli** — local Firefox-based, PNG + SVG

**Supported formats:** PNG (local CLI only), SVG (both options). PDF is NOT supported.

## Routing Guidance

**Explicit request phrases:** user says "画图", "diagram", "visualize", "flowchart", "draw", "架构图", "流程图"

**Proactive use cases:**
- Explaining a system with 3+ interacting components
- Describing a multi-step process or decision tree
- Comparing architectures or approaches side by side

**Skip when:** a simple list or table suffices, or user is in a quick Q&A flow

**When NOT to use it — route elsewhere:**
- Code import/module/package dependency analysis needing an editable `.drawio` graph → **drawio-skill**.
- Diagrams-as-code in git, auto-laid-out from text → **mermaid** (general) or **plantuml** (UML).
- An infinite-canvas whiteboard or programmatic freehand strokes → **tldraw**.

## Prerequisites

### Option A: Kroki API (recommended — zero install, SVG only)

```bash
# Just needs curl (pre-installed on macOS/Linux/Windows Git Bash)
curl --version
```

No additional setup. SVG rendered via `https://kroki.io`.

### Option B: Local CLI (required for PNG)

The CLI uses **Firefox** (not Chromium). Check and install:

```bash
npm install -g excalidraw-brute-export-cli
npx playwright install firefox
```

**macOS patch (one-time, required):**
```bash
CLI_MAIN=$(npm root -g)/excalidraw-brute-export-cli/src/main.js
sed -i '' 's/keyboard.press("Control+O")/keyboard.press("Meta+O")/' "$CLI_MAIN"
sed -i '' 's/keyboard.press("Control+Shift+E")/keyboard.press("Meta+Shift+E")/' "$CLI_MAIN"
```

**Windows/Linux:** No patch needed.

## Workflow

1. **Check deps** — use Kroki (curl) for SVG; use local CLI for PNG
2. **Plan** — pick the visual metaphor (see **Relationship-to-layout map**), then the diagram type and color palette
3. **Generate** — write `.excalidraw` JSON file (section-by-section for large diagrams)
4. **Export** — run Kroki or CLI command
5. **Verify the render** — view the exported PNG, fix any defects, re-export (see **Verify the Render**)
6. **Review loop** — show the image to the user, apply the minimal `.excalidraw` edit per request, re-export until approved (see **Review Loop**)
7. **Report** — tell user the output file path

## Authoring

Before creating or changing scene geometry, read [authoring-guide.md](references/authoring-guide.md) for style, JSON fields, bindings, layout patterns, and section construction. For a label-only edit, preserve existing geometry and bindings.

Keep labels readable, reserve title/footer space, route arrows edge-to-edge, and set explicit text colors. Preserve editable JSON alongside exports.

## Export

### Option A: Kroki API (SVG only — zero install)

```bash
# SVG via Kroki API
curl -s -X POST https://kroki.io/excalidraw/svg \
  -H "Content-Type: text/plain" \
  --data-binary "@diagram.excalidraw" \
  -o diagram.svg

# Via local Kroki Docker (offline)
curl -s -X POST http://localhost:8000/excalidraw/svg \
  -H "Content-Type: text/plain" \
  --data-binary "@diagram.excalidraw" \
  -o diagram.svg
```

### Option B: Local CLI (PNG + SVG)

```bash
# PNG at 2x scale, with background baked in (recommended)
excalidraw-brute-export-cli -i diagram.excalidraw -o diagram.png -f png -s 2 -b true

# PNG at 1x scale
excalidraw-brute-export-cli -i diagram.excalidraw -o diagram.png -f png -s 1 -b true

# SVG
excalidraw-brute-export-cli -i diagram.excalidraw -o diagram.svg -f svg -s 1 -b true
```

**Required flags:** `-f` (format: `png` or `svg`) and `-s` (scale: `1`, `2`, or `3`).

**Optional flags:** `-b true` bakes the `viewBackgroundColor` into the image — **the export is transparent by default**, so omit `-b` (or pass `-b false`) only when you want a transparent background. `-d true` exports dark mode; `-e true` embeds the scene so the PNG/SVG reopens as an editable drawing in excalidraw.com. (Long forms also work: `--background`, `--dark-mode`, `--embed-scene`, `--format`, `--scale`, `--input`, `--output`.)

## Verify the Render

**You cannot judge a diagram from its JSON.** The JSON can look perfect while the image has clipped text, overlapping boxes, or an arrow slicing through a shape. After exporting, *look at the result and fix it* — this is the single highest-leverage step.

1. **Render to PNG** (the image must be viewable — PNG, not SVG, even if the user ultimately wants SVG):
   ```bash
   excalidraw-brute-export-cli -i diagram.excalidraw -o /tmp/check.png -f png -s 2 -b true
   ```
   View `/tmp/check.png` (Claude can read PNGs directly). *Visual audit needs the local CLI; with Kroki-only (SVG), fall back to the structural checks below.*
2. **Audit the image:**

   | Look for | Fix |
   |----------|-----|
   | Text clipped / overflowing its shape | Widen the shape (`max(160, charCount * 9)`, ×2 for CJK) or pre-wrap with `\n` |
   | Boxes or labels overlapping | Re-space using the Spacing Reference (≥40px gap) |
   | Card covers another card | Move one card into a free area or enlarge the canvas; never use z-order to hide the overlap |
   | Card overlaps title/subtitle/footer note | Move the card below or away from the reserved text zone |
   | Line or arrowhead crosses text | Move endpoints to card edges, add waypoints, or route the line around the text zone |
   | Arrow cutting straight through a shape | Move endpoints to the shape borders, not centers |
   | Arrow invisible — only its label shows | Shrink the label `width` to fit the text |
   | Element off-canvas or floating with no connection | Reposition / connect it |
   | **Isomorphism Test:** mentally delete all text — does the structure alone still convey the idea? | If not, the *layout* is wrong, not the labels — restructure |

3. **Fix the JSON and re-export.** Repeat until clean — typically 1–3 passes. Skip only for trivial 2–3 element diagrams.

## Review Loop

Verify-the-render fixes *defects*; the review loop incorporates *the user's* wishes. After the render is clean, show it and collect feedback, then apply the **minimal `.excalidraw` edit** for each request and re-export:

| User request | Edit action |
|---|---|
| Change a label | Edit the `text` (or the bound label element) |
| Change a color | Update `backgroundColor` / `strokeColor` on the element |
| Add / remove an element | Append or delete the element (fix any `boundElements` / binding refs) |
| Move / resize | Update `x` / `y` / `width` / `height` |
| Restructure / re-route | Re-apply the pattern's spacing & routing rules, or regenerate |

- Overwrite the same `diagram.excalidraw` / output file each round — don't create `v1`, `v2`, …
- Re-run **Verify the Render** after each edit (a change can introduce a new clip / overlap).
- **Safety valve:** after 5 rounds, suggest the user fine-tune in [excalidraw.com](https://excalidraw.com) — the output preserves arrow binding, so it opens fully editable.

## Troubleshooting

For export errors, invisible arrows/text, clipping, or binding defects, read [troubleshooting.md](references/troubleshooting.md).
