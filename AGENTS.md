# Skills Manager Agent Guide

This repository is a reusable skills library. Treat each selected `SKILL.md` as the source of truth, regardless of model provider.

## How To Use A Skill

1. Read `docs/skill-index.md` and choose the closest skill for the user's business outcome.
2. Open that skill's `SKILL.md` completely before acting.
3. Follow its workflow and load linked scripts, references, assets, or templates only when needed.
4. Prefer bundled scripts for repeatable or fragile operations.
5. Keep real credentials private; use example configs for documentation.

Skills live under `skills/<business-scenario>/<skill-name>/`. Directory boundaries and maintenance rules are documented in `docs/directory-structure.md`.

## Output Directory

- Resolve the active business project from the request and workspace. Ask for the project directory only when several roots are plausible or none is known.
- Write generated files, retained intermediate artifacts, and run reports under `<project-root>/output/<skill-name>/`. Use the `SKILL.md` name for the folder. This rule also applies to independently installed skills.
- Run scripts from the business project root or pass an absolute output path. Resolve the skill installation path separately. An explicit user-supplied destination takes precedence for the requested files or deployment.

## Documentation

- `docs/skill-index.md`: canonical skill catalog.
- `docs/directory-structure.md`: business-scenario directory design.
- `docs/repository-operations.md`: invocation, validation, output, and security conventions.
- `docs/platform-compatibility.md`: model and client compatibility details.

## Platform Entrypoints

Codex uses this `AGENTS.md`. Compatibility entrypoints for other clients remain at the repository root as `CLAUDE.md`, `GEMINI.md`, and `GLM.md`. Every entrypoint must direct the client back to `AGENTS.md` and the selected `SKILL.md`.

## Portability Rules

- Keep skill names lowercase hyphen-case and match the concrete skill folder name.
- Keep platform-specific metadata outside `SKILL.md`; use `agents/openai.yaml` for Codex/OpenAI UI metadata.
- Include PowerShell and portable command examples when adding scripts.
- State clearly when a command is Windows-only.
- Do not assume Codex-specific tools, MCP servers, or browser automation exist unless the current environment exposes them.
