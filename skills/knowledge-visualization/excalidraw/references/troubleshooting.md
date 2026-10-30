> Read only for the mode linked from SKILL.md. Unless stated otherwise, command and resource paths are relative to the skill directory, not this references directory.

## Anti-Patterns

**Never put `text` on large background/zone rectangles.** Excalidraw centers text in the middle of the shape, overlapping contained elements. Instead, use a free-standing `text` element positioned at the top of the zone.

**Avoid cross-zone arrows.** Long diagonal arrows create visual spaghetti. Route arrows within zones or along zone edges. If a cross-zone connection is unavoidable, route it along the perimeter.

**Use arrow labels sparingly.** Bind labels to the arrow (see **Arrow labels**) so the line is masked behind the text instead of striking through it — but keep the label `width` to the text, never the arrow length. Keep labels to ≤12 characters and ensure ≥120px clear space between connected shapes. Omit labels when the connection meaning is obvious from context.

**Don't use filled backgrounds on containers that hold other elements.** Use `opacity: 30` (or 25-40 range) for zone/container rectangles so contained elements remain visible.

**Always set explicit `strokeColor` on text elements.** Text `strokeColor` is the rendered text color. If omitted, text may inherit the parent shape's background color and become invisible. Use `#1e293b` (title), `#334155` (label), or `#64748b` (description) from the text color palette.

## Common Mistakes

| Mistake | Fix |
|---------|-----|
| Kroki returns HTTP 400 | Send `-H "Content-Type: text/plain"` (NOT `application/json`, which Kroki reads as a `{"diagram_source": ...}` wrapper and rejects); ensure valid JSON with `"type": "excalidraw"` and `"elements"` array |
| Kroki only outputs SVG | Use local CLI (`excalidraw-brute-export-cli`) for PNG |
| Export fails with "Missing required flag" | Always pass `-f png` and `-s 2` |
| Export fails with "Executable doesn't exist" | Run `npx playwright install firefox` |
| macOS: timeout waiting for file chooser | Apply the macOS Meta patch above |
| Arrow `points` not relative to origin | `points` always start at `[0,0]` |
| Missing `id` on elements | Use descriptive string IDs per element |
| Overlapping elements | Use spacing reference table; minimum 40px gap |
| Arrows not interactive in excalidraw.com | Add `boundElements` to shapes referencing all bound arrows/text |
| Arrow/line cuts straight through the shapes | Compute endpoints at the shape borders, not centers — bindings don't clip the static export |
| Arrow invisible — only its label shows | Bound label `width` spans the whole arrow and masks the line; set label `width` to fit the text (`charCount * 9`) |
| Exported PNG/SVG has no background | CLI export is transparent by default; pass `-b true` to bake in `viewBackgroundColor` |
| Text not centered in shape | Set `containerId` on text AND add text to shape's `boundElements` |
| All text same size | Use font size hierarchy: 28 → 24 → 20 → 16 → 14 |
| Diagram looks monotone | Apply semantic colors from the palette, follow 60-30-10 rule |
| Text invisible / same color as background | Always set `strokeColor` on text elements to a dark color (`#1e293b`, `#334155`, or `#64748b`) |
| Text overlaps inside zone/container | Don't bind text to zone rectangles; use free-standing text at top |
| Text truncated in shapes | Use width formula: `max(160, charCount * 9)`, double for CJK |
| `boundElements: []` causes issues | Use `null` for empty boundElements, never `[]` |
