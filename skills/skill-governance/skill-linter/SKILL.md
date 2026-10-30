---
name: skill-linter
description: Use when reviewing, updating, or preparing skills for release to check structure, trigger descriptions, bundled links, UI metadata, repository catalogs, compatibility entrypoints, placeholders, and secret hygiene. Combines deterministic lint with workflow review.
---

# Skill Linter

## Overview

Use this skill to inspect one skill folder or a repository of skills before calling work complete. Combine deterministic script checks with a short human review of trigger quality and workflow clarity.

## Quick Start

On Windows, do not assume `python` is on `PATH`. Use the repository launcher:

```powershell
.\scripts\run-python.ps1 .\skills\skill-governance\skill-linter\scripts\lint_skill.py .\skills\knowledge-visualization\mindmap-builder --repo-root .
```

Run it against every `SKILL.md` under the current repository:

```powershell
.\scripts\run-python.ps1 .\skills\skill-governance\skill-linter\scripts\lint_skill.py . --repo-root .
```

Portable shell:

```bash
python3 ./skills/skill-governance/skill-linter/scripts/lint_skill.py ./skills/knowledge-visualization/mindmap-builder --repo-root .
python3 ./skills/skill-governance/skill-linter/scripts/lint_skill.py . --repo-root .
```

Use `--json` when another script or CI step needs machine-readable output. Use `--strict` when warnings should fail the command. The Windows launcher resolves Python without relying on `python` or `py` being on `PATH`; if no interpreter is available, it reports the missing Python prerequisite and the checked locations.

## Review Workflow

1. Identify the target skill folder or repository root.
2. Run `scripts/lint_skill.py` before editing so existing issues are visible.
3. Fix high-signal issues first:
   - invalid or placeholder frontmatter
   - skill name not matching the folder
   - missing or weak trigger language in `description`
   - broken references to `scripts/`, `references/`, `assets/`, or Markdown links
   - missing or stale `agents/openai.yaml`
   - missing or stale repository compatibility entrypoints (`AGENTS.md`, `CLAUDE.md`, `GEMINI.md`, `GLM.md`)
   - committed-looking credentials or local `config.json`
4. Re-run the linter after edits.
5. For release or commit preparation, also check the repository catalog (`docs/skill-index.md`, with `README.md` as a fallback) mentions the skill path and purpose.

## Human Checks

The script catches mechanical failures. Always add a short judgment pass:

- The `description` should say what the skill does and when to use it, because it is the trigger surface.
- The body should explain only the workflow needed after trigger, not bury trigger rules in a "When to use" section.
- Scripts should be the repeatable parts of the workflow; long conceptual material should live in `references/`.
- Configuration examples should be safe to commit. Real tokens, passwords, API keys, local private endpoints, and generated outputs should stay ignored.
- Repository catalog updates should describe user-facing capability, not internal implementation trivia.

For a release-sized change, also run the small request-to-skill acceptance set in [references/acceptance-scenarios.md](references/acceptance-scenarios.md). It checks that ordinary user wording routes to the intended skill and that its stated output contract is observable; this complements structural linting rather than replacing it.

## Script Behavior

`scripts/lint_skill.py` checks:

- `SKILL.md` exists and has valid required frontmatter.
- `name` uses lowercase hyphen-case and matches the folder name.
- `description` is not placeholder text, has enough detail, and includes trigger-oriented wording.
- The skill body has meaningful content and no template TODO placeholders.
- Relative Markdown links and common resource references resolve.
- `agents/openai.yaml` exists, has UI metadata, and its default prompt mentions `$skill-name`.
- Repository-level compatibility entrypoints exist when `--repo-root` is supplied: `AGENTS.md` mentions the compatibility surface, and Claude, Gemini, and GLM entrypoints point users to `AGENTS.md` and `SKILL.md`.
- Example config files do not look like real secrets.
- Local config files, generated outputs, and likely credentials are flagged.
- The repository catalog in `docs/skill-index.md` or `README.md` mentions the skill path or name when `--repo-root` is supplied.

Treat script output as a review checklist: fix errors, evaluate warnings, and leave intentional exceptions only when there is a clear reason.
