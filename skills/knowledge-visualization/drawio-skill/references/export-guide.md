> Commands use paths relative to the skill directory. Use the resolved CLI binary and the requested output directory.

## Export

### Commands

There are **two** export modes:

- **Preview / self-check** (the preview stage) — no `-e`. Output `diagram.png`. Required for vision self-check; using `-e` here triggers a 400 "Could not process image" error from the vision API (issue #8).
- **Final / deliverable** (the final export stage) — pass `-e`. Output `diagram.drawio.png`. The embedded XML keeps the file editable in draw.io.

> All commands below write `drawio` as a placeholder for the binary you resolved in binary discovery. If your binary is on PATH as `draw.io` (with dot — some older or distro-packaged installs), substitute `draw.io` throughout. If only the macOS `.app` or Windows `.exe` is available, use the full path variant shown a few lines down.

```bash
# Preview PNG (use this in step 4, before self-check) — NO -e, width-capped to stay under vision's 2576px ceiling
drawio -x -f png --width 2000 -o diagram.png input.drawio

# Final PNG (the final export stage, after validation) — WITH -e, double extension
drawio -x -f png -e -s 2 -o diagram.drawio.png input.drawio

# macOS — full path (if not in PATH); preview / final variants
/Applications/draw.io.app/Contents/MacOS/draw.io -x -f png --width 2000 -o diagram.png input.drawio
/Applications/draw.io.app/Contents/MacOS/draw.io -x -f png -e -s 2 -o diagram.drawio.png input.drawio

# Windows PowerShell (run separately from this Bash block)
& "C:\Program Files\draw.io\draw.io.exe" -x -f png -e -s 2 -o diagram.drawio.png input.drawio

# Linux (headless — requires xvfb-run; on servers add HOME and --disable-gpu)
xvfb-run -a --server-args="-screen 0 1280x1024x24" \
  drawio -x -f png -e -s 2 -o diagram.drawio.png input.drawio --disable-gpu
# Running as root (CI / Docker)? Append --no-sandbox AT THE END (placing it earlier makes drawio treat it as the input filename)

# SVG export (final — -e is safe; SVG is text)
drawio -x -f svg -e -o diagram.svg input.drawio

# PDF export (final)
drawio -x -f pdf -e -o diagram.pdf input.drawio

# Custom output directory (e.g. CI artifacts dir) — create if missing, then export there
mkdir -p ./artifacts && drawio -x -f png -e -s 2 -o ./artifacts/diagram.drawio.png input.drawio
```

### Post-export PNG repair (required after `-e` PNG export)

draw.io CLI truncates the IEND chunk when emitting `-e` PNGs — the file ends with the 4-byte IEND length field but the `IEND` type + CRC (8 bytes) are missing. Result: vision APIs return 400 "Could not process image" and strict PNG decoders error out. SVG/PDF are unaffected.

Run this immediately after every `-e` PNG export:

```bash
python3 <this-skill-dir>/scripts/repair_png.py diagram.drawio.png
```

The script's `endswith(IEND)` guard makes it a no-op once draw.io fixes the bug upstream — safe to run unconditionally.

**Key flags:**
- `-x` — export mode (required)
- `-f` — format: `png`, `svg`, `pdf`, `jpg`
- `-e` — embed diagram XML in output (PNG, SVG, PDF) — exported file remains editable in draw.io. **Skip for the preview PNG used in visual self-check** — `-e` PNGs have a truncated IEND chunk that vision APIs reject (issue #8). For final PNG export, keep `-e` and run `scripts/repair_png.py` (see Post-export PNG repair). SVG/PDF unaffected.
- `-s` — scale: `1`, `2`, `3` (2 recommended for final PNG; do NOT use for the preview — see `--width`)
- `--width <px>` — target width in pixels (no short form; `-w` does **not** exist and silently breaks the input-file parser). Use `--width 2000` for the preview to keep the PNG under Claude's 2576×2576 vision ceiling. There's also a `--height <px>` flag for tall-narrow diagrams. Don't combine `--width` with `-s`.
- `-o` — output file path; accepts any directory (e.g. `./artifacts/diagram.drawio.png`) — `mkdir -p` the target dir first. Use `.drawio.png` double extension when embedding.
- `--layout <preset|json>` — **CLI ≥ v30 only** — ELK auto-layout pass on XML input (`verticalFlow`, `horizontalFlow`, `verticalTree`, `horizontalTree`, `radialTree`, `organic`, or a custom ELK JSON array). Alternative to `autolayout.py` when Graphviz is missing; never combine with Mermaid-converted files (already laid out). On ≤ 29 this flag breaks argument parsing — don't emit it. See `references/mermaid-authoring.md`
- `-b` — border width around diagram (default: 0, recommend 10)
- `-t` — transparent background (PNG only)
- `--page-index <n>` — export one page of a multi-page file. **1-based** in current drawio-desktop (verified on 29.7.8: `--page-index 2` exports the second page; older docs claimed 0-based). Default: first page. `--page-range 2..3` also works

### Browser fallback (no CLI needed)

When the draw.io desktop CLI is unavailable, generate a client-side URL:

```bash
python3 <this-skill-dir>/scripts/encode_drawio_url.py input.drawio          # read-only viewer
python3 <this-skill-dir>/scripts/encode_drawio_url.py --edit input.drawio    # opens in the editor
```

Default prints a `https://viewer.diagrams.net/...#R…` viewer URL; `--edit` prints a `https://app.diagrams.net/...#create=…` URL that opens straight into the editable editor. Either way the diagram XML is `encodeURIComponent`-encoded, deflate-compressed, and base64'd into the URL fragment — the fragment (after `#`) is never sent to the server, so nothing is uploaded. The `encodeURIComponent` step is mandatory: without it, any diagram containing a literal `%` or non-ASCII (e.g. CJK) label makes the browser throw "URI malformed" and the diagram never opens.

Open the URL with `open "$URL"` (macOS) / `xdg-open "$URL"` (Linux). On **WSL2 / Windows**, `cmd.exe` drops the `#fragment` — write a `.url` shortcut file and open that instead (see `references/troubleshooting.md` → "WSL2 / Windows specifics").

### Fallback chain

When tools are unavailable, degrade gracefully:

| Scenario | Behavior |
|----------|----------|
| draw.io CLI missing, Python available | Use browser fallback (diagrams.net URL) |
| draw.io CLI missing, Python missing | Generate `.drawio` XML only; instruct user to open in draw.io desktop or diagrams.net manually |
| draw.io CLI crashes / no output in macOS sandbox isolation | Treat CLI as unavailable in-sandbox; use browser fallback / XML-only; ask user to run CLI exports in a non-sandboxed host environment |
| Vision unavailable for self-check | Skip self-check (step 5); proceed directly to showing user the exported PNG |
| Export fails (Chromium/display issues) | On Linux, retry with `xvfb-run -a`; if still failing, deliver `.drawio` XML and suggest manual export |
| Export fails on Linux server (headless) | Try in order: (1) `xvfb-run -a`, (2) append `--no-sandbox` at the very end if root, (3) add `--disable-gpu`, (4) check the session home-directory permissions, (5) install apt deps (`libgtk-3-0 libnotify4 libnss3 libgbm1 libasound2t64` etc.), (6) fall back to [tomkludy/drawio-renderer](https://hub.docker.com/r/tomkludy/drawio-renderer) Docker (REST API for headless export) |

### Checking if drawio is in PATH

```bash
# Prefer the Homebrew / Linux-package binary name (no dot)
if command -v drawio &>/dev/null; then
  DRAWIO="drawio"
# Fall back to the dot-named binary (older installs, manual symlinks)
elif command -v draw.io &>/dev/null; then
  DRAWIO="draw.io"
# macOS .app bundle (binary inside the bundle keeps the dot)
elif [ -f "/Applications/draw.io.app/Contents/MacOS/draw.io" ]; then
  DRAWIO="/Applications/draw.io.app/Contents/MacOS/draw.io"
# WSL2: the CLI is the Windows desktop exe, reached via /mnt/c (note the space)
elif grep -qi microsoft /proc/version 2>/dev/null && [ -f "/mnt/c/Program Files/draw.io/draw.io.exe" ]; then
  DRAWIO="/mnt/c/Program Files/draw.io/draw.io.exe"
else
  echo "drawio not found — install from https://github.com/jgraph/drawio-desktop/releases (Homebrew: brew install --cask drawio)"
fi
```

On **WSL2 / native Windows**, opening exported files and browser-fallback URLs needs path conversion + a `.url`-file workaround (`cmd.exe` drops URL `#fragment`s) — see the "WSL2 / Windows specifics" section in `references/troubleshooting.md`.
