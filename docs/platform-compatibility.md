# Platform Compatibility

Every model or client uses the same skill implementation: the selected skill's `SKILL.md` plus its bundled resources. Root-level compatibility files exist only as discovery entrypoints and should stay short.

## Shared Workflow

1. Read the root `AGENTS.md` for repository rules.
2. Choose a skill from `docs/skill-index.md`.
3. Read the selected `SKILL.md` completely.
4. Load linked scripts, references, assets, or templates only when required.
5. Preserve the skill workflow and report the verification performed.
6. For an independently installed skill, run its scripts from the business project root or pass an absolute destination under that project's `output/<skill-name>/`.

Direct invocation pattern:

```text
Read AGENTS.md, then read <skill-path>/SKILL.md, and follow that skill for this task.
```

## Codex

- Uses `AGENTS.md` for repository instructions.
- May discover a skill through `SKILL.md` and optional `agents/openai.yaml` UI metadata.
- Treats `SKILL.md` as the workflow source of truth.

## Claude

- Starts from `CLAUDE.md`, then follows `AGENTS.md` and the selected `SKILL.md`.
- Can ignore `agents/openai.yaml` unless cross-platform metadata is relevant.

## Gemini

- Starts from `GEMINI.md` and `AGENTS.md`.
- Translates PowerShell commands to the current shell when necessary while preserving behavior.
- Inspects bundled script arguments before execution.

## GLM

- Starts from `GLM.md`.
- When automatic skill discovery is unavailable, explicitly selects a path from `docs/skill-index.md` and reads its `SKILL.md`.

## Root Entrypoints

The following files remain in the repository root because clients look for them there:

- `README.md`: human-facing repository landing page.
- `AGENTS.md`: shared agent instructions.
- `CLAUDE.md`: Claude discovery entrypoint.
- `GEMINI.md`: Gemini discovery entrypoint.
- `GLM.md`: GLM discovery entrypoint.

Do not move these files into `docs/`; move detailed explanations here instead.
