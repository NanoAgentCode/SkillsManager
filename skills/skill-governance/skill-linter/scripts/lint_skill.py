#!/usr/bin/env python3
"""Lint multi-model skill folders for structural and quality issues."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

MAX_DESCRIPTION_LENGTH = 1024
SKIP_DIRS = {
    ".git",
    ".hg",
    ".svn",
    ".idea",
    ".tmp",
    "__pycache__",
    "node_modules",
    ".venv",
    "venv",
    "dist",
    "build",
    "output",
    "outputs",
    "test-output",
}

SAFE_SECRET_FILENAMES = {
    "config.example.json",
    "example.env",
    ".env.example",
    "README.md",
    "README_CN.md",
    "SKILL.md",
}

SECRET_ASSIGNMENT_RE = re.compile(
    r"(?i)\b(api[_-]?key|app[_-]?secret|access[_-]?token|secret[_-]?key|password|passwd|pwd|authorization)\b\s*[:=]\s*['\"]?([^'\"\s,;]+)"
)

REPOSITORY_ENTRYPOINTS = {
    "CLAUDE.md": "Claude",
    "GEMINI.md": "Gemini",
    "GLM.md": "GLM",
}
REPOSITORY_GUIDE = "AGENTS.md"
REPOSITORY_CATALOGS = ("docs/skill-index.md", "README.md")


def looks_like_real_secret(value: str) -> bool:
    value = value.strip().strip('"').strip("'")
    lower = value.lower()
    placeholders = {
        "",
        "...",
        "your-api-key",
        "your_app_id",
        "your_app_secret",
        "your-admin-key",
        "your-password",
        "password",
        "secret",
        "token",
        "none",
        "null",
    }
    if lower in placeholders:
        return False
    if value.startswith(("{", "$", "<")):
        return False
    if "(" in value or "config.get" in value or "os.environ" in value:
        return False
    if len(value) < 16 and not re.search(r"(?i)^bearer", value):
        return False
    return bool(re.search(r"[A-Za-z]", value) and re.search(r"[0-9_\-./+=]", value))


@dataclass
class Finding:
    severity: str
    code: str
    message: str
    path: str


def rel(path: Path, base: Path) -> str:
    try:
        return str(path.resolve().relative_to(base.resolve()))
    except ValueError:
        return str(path)


def parse_frontmatter(skill_md: Path) -> tuple[dict[str, str], str, str | None]:
    text = skill_md.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        return {}, text, "SKILL.md must start with YAML frontmatter"
    match = re.match(r"^---\n(.*?)\n---\n?(.*)$", text, re.DOTALL)
    if not match:
        return {}, text, "SKILL.md frontmatter must be closed with ---"

    frontmatter_text, body = match.groups()
    data: dict[str, str] = {}
    for line in frontmatter_text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if ":" not in line:
            return data, body, f"Invalid frontmatter line: {line}"
        key, value = line.split(":", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        data[key] = value
    return data, body, None


def walk_files(root: Path) -> Iterable[Path]:
    for path in root.rglob("*"):
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        if path.is_file():
            yield path


def find_skill_dirs(target: Path) -> list[Path]:
    target = target.resolve()
    if target.is_file() and target.name == "SKILL.md":
        return [target.parent]
    if (target / "SKILL.md").exists():
        return [target]

    skill_dirs: list[Path] = []
    for skill_md in target.rglob("SKILL.md"):
        if any(part in SKIP_DIRS for part in skill_md.parts):
            continue
        skill_dirs.append(skill_md.parent)
    return sorted(skill_dirs)


def check_frontmatter(skill_dir: Path, base: Path) -> tuple[list[Finding], dict[str, str], str]:
    findings: list[Finding] = []
    skill_md = skill_dir / "SKILL.md"
    if not skill_md.exists():
        return [
            Finding("error", "missing-skill-md", "Missing SKILL.md", rel(skill_dir, base))
        ], {}, ""

    frontmatter, body, parse_error = parse_frontmatter(skill_md)
    if parse_error:
        findings.append(Finding("error", "frontmatter-format", parse_error, rel(skill_md, base)))
        return findings, frontmatter, body

    allowed = {"name", "description"}
    unexpected = sorted(set(frontmatter) - allowed)
    if unexpected:
        findings.append(
            Finding(
                "warning",
                "frontmatter-extra-keys",
                f"Unexpected frontmatter key(s): {', '.join(unexpected)}",
                rel(skill_md, base),
            )
        )

    name = frontmatter.get("name", "").strip()
    description = frontmatter.get("description", "").strip()
    if not name:
        findings.append(Finding("error", "missing-name", "Frontmatter must include name", rel(skill_md, base)))
    elif not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", name):
        findings.append(
            Finding("error", "bad-name", "Skill name must be lowercase hyphen-case", rel(skill_md, base))
        )
    elif name != skill_dir.name:
        findings.append(
            Finding(
                "warning",
                "name-folder-mismatch",
                f"Skill name '{name}' does not match folder '{skill_dir.name}'",
                rel(skill_md, base),
            )
        )

    if not description:
        findings.append(
            Finding("error", "missing-description", "Frontmatter must include description", rel(skill_md, base))
        )
    else:
        lower_desc = description.lower()
        if "todo" in lower_desc or "complete and informative" in lower_desc:
            findings.append(
                Finding("error", "placeholder-description", "Description still contains template text", rel(skill_md, base))
            )
        if len(description) < 80:
            findings.append(
                Finding("warning", "short-description", "Description is probably too short to trigger reliably", rel(skill_md, base))
            )
        if len(description) > MAX_DESCRIPTION_LENGTH:
            findings.append(
                Finding("error", "long-description", "Description exceeds 1024 characters", rel(skill_md, base))
            )
        if not re.search(r"(?i)\b(use when|when|trigger|asks?|creating|updating|reviewing|validating)\b", description):
            findings.append(
                Finding("warning", "weak-trigger-language", "Description should include explicit trigger/use context", rel(skill_md, base))
            )

    if "[TODO" in body or "TODO:" in body or "Structuring This Skill" in body:
        findings.append(
            Finding("error", "placeholder-body", "Skill body still contains template TODO text", rel(skill_md, base))
        )
    if len(body.strip()) < 300:
        findings.append(
            Finding("warning", "thin-body", "Skill body is very short; add workflow and resource guidance", rel(skill_md, base))
        )
    if re.search(r"(?i)^##\s+when to use", body, re.MULTILINE):
        findings.append(
            Finding(
                "warning",
                "trigger-rules-in-body",
                "Trigger rules belong in description; body loads only after trigger",
                rel(skill_md, base),
            )
        )
    return findings, frontmatter, body


def extract_candidate_refs(body: str) -> set[str]:
    refs: set[str] = set()
    for match in re.finditer(r"\[[^\]]+\]\(([^)]+)\)", body):
        if match.start() > 0 and body[match.start() - 1] == "!":
            continue
        target = match.group(1).strip()
        if target and not re.match(r"^[a-z]+://|^#", target):
            clean_target = target.split("#", 1)[0]
            if "/" in clean_target or re.search(r"\.(md|ya?ml|json|py|ps1|sh|txt)$", clean_target, re.I):
                refs.add(clean_target)

    for match in re.finditer(r"`([^`]+)`", body):
        value = match.group(1).strip()
        if re.match(r"^(scripts|references|assets|agents)/[\w./\\-]+$", value):
            refs.add(value)
    return refs


def check_references(skill_dir: Path, body: str, base: Path) -> list[Finding]:
    findings: list[Finding] = []
    for raw in sorted(extract_candidate_refs(body)):
        normalized = raw.replace("\\", "/")
        if normalized.startswith("."):
            candidate = (skill_dir / normalized).resolve()
        else:
            candidate = (skill_dir / normalized).resolve()
        if not candidate.exists():
            findings.append(
                Finding(
                    "error",
                    "broken-reference",
                    f"Referenced resource does not exist: {raw}",
                    rel(skill_dir / "SKILL.md", base),
                )
            )
    return findings


def parse_simple_yaml(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    if not path.exists():
        return values
    for line in path.read_text(encoding="utf-8").splitlines():
        if ":" not in line or line.lstrip().startswith("#"):
            continue
        key, value = line.split(":", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key in {"display_name", "short_description", "default_prompt"}:
            values[key] = value
    return values


def check_agents_metadata(skill_dir: Path, skill_name: str, base: Path) -> list[Finding]:
    findings: list[Finding] = []
    openai_yaml = skill_dir / "agents" / "openai.yaml"
    if not openai_yaml.exists():
        findings.append(
            Finding("warning", "missing-openai-yaml", "Missing agents/openai.yaml UI metadata", rel(skill_dir, base))
        )
        return findings

    values = parse_simple_yaml(openai_yaml)
    for key in ["display_name", "short_description", "default_prompt"]:
        if not values.get(key):
            findings.append(
                Finding("warning", "openai-yaml-missing-field", f"agents/openai.yaml missing interface.{key}", rel(openai_yaml, base))
            )

    default_prompt = values.get("default_prompt", "")
    if skill_name and f"${skill_name}" not in default_prompt:
        findings.append(
            Finding(
                "warning",
                "default-prompt-missing-skill",
                f"default_prompt should mention ${skill_name}",
                rel(openai_yaml, base),
            )
        )
    if "TODO" in openai_yaml.read_text(encoding="utf-8"):
        findings.append(
            Finding("error", "openai-yaml-placeholder", "agents/openai.yaml contains TODO text", rel(openai_yaml, base))
        )
    return findings


def check_repository_entrypoints(repo_root: Path, base: Path) -> list[Finding]:
    findings: list[Finding] = []
    guide = repo_root / REPOSITORY_GUIDE
    if not guide.exists():
        findings.append(
            Finding(
                "warning",
                "missing-agents-guide",
                "Missing AGENTS.md repository skill index and platform guide",
                rel(guide, base),
            )
        )
    else:
        guide_text = guide.read_text(encoding="utf-8")
        missing_guide_terms = [
            term
            for term in ("SKILL.md", *REPOSITORY_ENTRYPOINTS)
            if term.lower() not in guide_text.lower()
        ]
        if missing_guide_terms:
            findings.append(
                Finding(
                    "warning",
                    "stale-agents-guide",
                    f"AGENTS.md should mention repository compatibility surface: {', '.join(missing_guide_terms)}",
                    rel(guide, base),
                )
            )

    for filename, platform in REPOSITORY_ENTRYPOINTS.items():
        entrypoint = repo_root / filename
        if not entrypoint.exists():
            findings.append(
                Finding(
                    "warning",
                    "missing-platform-entrypoint",
                    f"Missing {platform} repository compatibility entrypoint {filename}",
                    rel(entrypoint, base),
                )
            )
            continue

        text = entrypoint.read_text(encoding="utf-8")
        missing_terms = [
            term
            for term in ("AGENTS.md", "SKILL.md")
            if term.lower() not in text.lower()
        ]
        if missing_terms:
            findings.append(
                Finding(
                    "warning",
                    "stale-platform-entrypoint",
                    f"{filename} should direct {platform} users to read {', '.join(missing_terms)}",
                    rel(entrypoint, base),
                )
            )
        if "TODO" in text or "[TODO" in text:
            findings.append(
                Finding(
                    "error",
                    "platform-entrypoint-placeholder",
                    f"{filename} contains TODO placeholder text",
                    rel(entrypoint, base),
                )
            )
    return findings


def git_ignores(path: Path) -> bool:
    try:
        result = subprocess.run(
            ["git", "check-ignore", "--quiet", "--", path.name],
            cwd=path.parent,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
        )
    except OSError:
        return False
    return result.returncode == 0


def check_secret_hygiene(skill_dir: Path, base: Path) -> list[Finding]:
    findings: list[Finding] = []
    for path in walk_files(skill_dir):
        relative_name = path.name
        rel_path = rel(path, base)
        if relative_name == "config.json":
            if git_ignores(path):
                continue
            findings.append(
                Finding("warning", "local-config-file", "Local config.json appears inside the skill folder", rel_path)
            )
        if path.suffix.lower() in {".png", ".jpg", ".jpeg", ".gif", ".ico", ".pdf", ".pptx", ".docx", ".xlsx"}:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for line in text.splitlines():
            match = SECRET_ASSIGNMENT_RE.search(line)
            if match and looks_like_real_secret(match.group(2)):
                severity = "warning" if relative_name in SAFE_SECRET_FILENAMES else "error"
                findings.append(
                    Finding(severity, "possible-secret", "File contains a possible credential or token", rel_path)
                )
                break
    return findings


def check_repo_catalog(skill_dir: Path, repo_root: Path | None, frontmatter: dict[str, str], base: Path) -> list[Finding]:
    if not repo_root:
        return []
    catalogs = [repo_root / relative_path for relative_path in REPOSITORY_CATALOGS]
    existing_catalogs = [path for path in catalogs if path.exists()]
    if not existing_catalogs:
        return [
            Finding(
                "warning",
                "missing-repo-catalog",
                "Repository skill catalog not found; expected docs/skill-index.md or README.md",
                rel(repo_root, base),
            )
        ]
    text = "\n".join(path.read_text(encoding="utf-8") for path in existing_catalogs).lower()
    skill_name = frontmatter.get("name", skill_dir.name).lower()
    relative_skill_path = rel(skill_dir, repo_root).replace("\\", "/").lower()
    if skill_name not in text and relative_skill_path not in text:
        return [
            Finding(
                "warning",
                "catalog-not-synced",
                "Repository skill catalog does not mention this skill name or path",
                rel(existing_catalogs[0], base),
            )
        ]
    return []


def lint_skill(skill_dir: Path, repo_root: Path | None, base: Path) -> list[Finding]:
    findings, frontmatter, body = check_frontmatter(skill_dir, base)
    if body:
        findings.extend(check_references(skill_dir, body, base))
    findings.extend(check_agents_metadata(skill_dir, frontmatter.get("name", skill_dir.name), base))
    findings.extend(check_secret_hygiene(skill_dir, base))
    findings.extend(check_repo_catalog(skill_dir, repo_root, frontmatter, base))
    return findings


def print_text_report(results: dict[str, list[Finding]]) -> None:
    total_errors = sum(1 for findings in results.values() for item in findings if item.severity == "error")
    total_warnings = sum(1 for findings in results.values() for item in findings if item.severity == "warning")
    print(f"Skill lint: {total_errors} error(s), {total_warnings} warning(s)")
    for skill, findings in results.items():
        print(f"\n{skill}")
        if not findings:
            print("  OK")
            continue
        for finding in findings:
            print(f"  [{finding.severity.upper()}] {finding.code}: {finding.message}")
            print(f"    {finding.path}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Lint one skill folder or all skills under a target directory.")
    parser.add_argument("target", help="Skill folder, SKILL.md file, or repository root to scan")
    parser.add_argument("--repo-root", help="Repository root used for catalog and compatibility entrypoint checks")
    parser.add_argument("--json", action="store_true", help="Output JSON")
    parser.add_argument("--strict", action="store_true", help="Exit non-zero on warnings as well as errors")
    args = parser.parse_args()

    target = Path(args.target)
    repo_root = Path(args.repo_root).resolve() if args.repo_root else None
    base = repo_root or target.resolve()
    skill_dirs = find_skill_dirs(target)
    if not skill_dirs:
        print(f"No SKILL.md files found under {target}", file=sys.stderr)
        return 2

    results: dict[str, list[Finding]] = {}
    for skill_dir in skill_dirs:
        results[rel(skill_dir, base)] = lint_skill(skill_dir, repo_root, base)
    if repo_root:
        repo_findings = check_repository_entrypoints(repo_root, base)
        if repo_findings:
            results[rel(repo_root, base)] = repo_findings

    if args.json:
        payload = {
            skill: [finding.__dict__ for finding in findings]
            for skill, findings in results.items()
        }
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print_text_report(results)

    has_errors = any(f.severity == "error" for findings in results.values() for f in findings)
    has_warnings = any(f.severity == "warning" for findings in results.values() for f in findings)
    if has_errors or (args.strict and has_warnings):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
