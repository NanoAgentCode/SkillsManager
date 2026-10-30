---
name: office-cli-skill
description: Use when creating, inspecting, editing, or validating local DOCX, XLSX, or PPTX artifacts with officecli, including template-based PowerPoint reconstruction. Requires an Office artifact, not a text-only answer.
---

# Office CLI Skill

Use `officecli` for structured Office-document work while preserving the user's requested content and output location.

## Prerequisite

Resolve `officecli` from `OFFICECLI_BIN` when that variable is set; otherwise use the executable on `PATH`. Verify availability with `officecli --version` before editing a document.

If it is unavailable, stop and report the prerequisite. Installing or downloading the tool requires the user's approval. Do not use or commit credentials, private upload endpoints, or environment files.

### Install on Windows

After the user approves installation, download the official installer to a temporary file, review it, and then run it:

```powershell
$officeCliInstaller = Join-Path $env:TEMP 'officecli-install.ps1'
Invoke-WebRequest https://raw.githubusercontent.com/iOfficeAI/OfficeCLI/main/install.ps1 -OutFile $officeCliInstaller
Get-Content -LiteralPath $officeCliInstaller
& $officeCliInstaller
officecli --version
```

The official installer selects x64 or ARM64, verifies the release checksum when available, installs under the current user's profile, and updates the user `PATH`. Its current implementation may also copy the vendor-provided OfficeCLI skill into detected agent directories; inspect the script first when only the executable should be installed.

### Install on Linux

After the user approves installation, download and review the official shell installer before running it:

```bash
officecli_installer="$(mktemp)"
curl -fsSL https://raw.githubusercontent.com/iOfficeAI/OfficeCLI/main/install.sh -o "$officecli_installer"
less "$officecli_installer"
bash "$officecli_installer"
officecli --version
```

The project also publishes versioned binaries on its official GitHub Releases page. Prefer a versioned asset plus the release `SHA256SUMS` file when a pinned or unattended installation is required.

For command syntax and supported document elements, read [references/officecli-command-reference.md](references/officecli-command-reference.md). Query `officecli help <format> <element>` instead of guessing a property name.

## Workflow

1. Confirm the input artifact, requested changes, and output path. Work on a copy unless the user explicitly asks to overwrite the source.
2. Inspect before changing: use `view`, `get`, `query`, and `validate` as appropriate.
3. Prefer structured operations in this order: read/inspect, DOM-level `add` or `set`, then raw XML only when the higher-level interface cannot express the change.
4. For a longer edit session, run `officecli open <file>` first. Address elements by stable IDs when the tool returns them.
5. Run the requested changes sequentially when positions or slide indices can shift.
6. Run `officecli close <file>` before another program reads the output or before delivery.
7. Validate the result and inspect relevant text or issues. For visual work, also render or open the result with an available viewer.

Keep generated artifacts under `output/office-cli-skill/` unless the user gives another path.

## Template-based PowerPoint

When rebuilding a presentation from an existing template, read [references/template-based-pptx.md](references/template-based-pptx.md). The bundled [scripts/pptx_master_analysis.py](scripts/pptx_master_analysis.py) reports slide-to-layout relationships and then removes existing slides from the working copy, so never run it against the only copy of a user's template.
