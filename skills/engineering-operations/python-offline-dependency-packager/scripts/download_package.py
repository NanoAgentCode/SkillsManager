#!/usr/bin/env python3
"""Download a pinned Python distribution and its dependencies for offline install."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
from typing import Sequence


PACKAGE_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*(?:\[[A-Za-z0-9._,-]+\])?$")
VERSION_RE = re.compile(
    r"^(?:[0-9]+!)?[0-9]+(?:\.[0-9]+)*(?:(?:a|b|rc)[0-9]+)?"
    r"(?:\.post[0-9]+)?(?:\.dev[0-9]+)?(?:\+[A-Za-z0-9]+(?:[._-][A-Za-z0-9]+)*)?$",
    re.IGNORECASE,
)
PYTHON_VERSION_RE = re.compile(
    r"^(?P<major>[1-9][0-9]*)\.(?P<minor>0|[1-9][0-9]*)(?:\.x)?$",
    re.IGNORECASE,
)


POWERSHELL_INSTALLER = r'''param(
    [string]$PythonExecutable = ""
)

$ErrorActionPreference = "Stop"
$BundleDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$PackageDir = Join-Path $BundleDir "packages"
$Requirements = Join-Path $BundleDir "requirements.txt"

if (-not $PythonExecutable) {
    if ($env:PYTHON_BIN) {
        $PythonExecutable = $env:PYTHON_BIN
    } else {
        foreach ($Candidate in @("python", "python3", "py")) {
            $Command = Get-Command $Candidate -ErrorAction SilentlyContinue
            if ($Command) {
                $PythonExecutable = $Command.Source
                break
            }
        }
    }
}

if (-not $PythonExecutable) {
    throw "Python was not found. Pass -PythonExecutable or set PYTHON_BIN."
}

& $PythonExecutable -m pip install --no-index --find-links $PackageDir --requirement $Requirements
if ($LASTEXITCODE -ne 0) {
    throw "Offline dependency installation failed with exit code $LASTEXITCODE."
}
'''


SHELL_INSTALLER = r'''#!/bin/sh
set -eu

BUNDLE_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
PACKAGE_DIR="$BUNDLE_DIR/packages"
REQUIREMENTS="$BUNDLE_DIR/requirements.txt"

if [ -n "${PYTHON_BIN:-}" ]; then
    PYTHON_COMMAND=$PYTHON_BIN
elif command -v python3 >/dev/null 2>&1; then
    PYTHON_COMMAND=python3
elif command -v python >/dev/null 2>&1; then
    PYTHON_COMMAND=python
else
    echo "Python was not found. Set PYTHON_BIN to the target interpreter." >&2
    exit 1
fi

"$PYTHON_COMMAND" -m pip install --no-index --find-links "$PACKAGE_DIR" --requirement "$REQUIREMENTS"
'''


def parse_args(argv: Sequence[str] | None = None, *, installed: bool = False) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Interactively inspect versions or download an exact Python package "
            "version and all dependencies."
        )
    )
    if installed:
        commands = parser.add_subparsers(dest="command", required=True)
        versions = commands.add_parser("versions", help="List versions from the configured index")
        versions.add_argument("--package", required=True, help="Distribution name")
        versions.set_defaults(version=None, python_version=None)
        bundle = commands.add_parser("bundle", help="Download wheels and produce offline installers")
        add_bundle_arguments(bundle, required=True)
    else:
        add_bundle_arguments(parser, required=False)
    return parser.parse_args(argv)


def add_bundle_arguments(parser: argparse.ArgumentParser, *, required: bool) -> None:
    parser.add_argument(
        "--package",
        required=required,
        help="Distribution name, optionally with extras" + ("" if required else "; prompted for when omitted"),
    )
    parser.add_argument("--version", required=required, help="Exact distribution version, not a range")
    parser.add_argument("--output", type=Path, help="Bundle directory")
    parser.add_argument("--platform", help="Target platform tag accepted by pip")
    parser.add_argument(
        "--python-version",
        required=required,
        help="Target Python line in X.Y or X.Y.x form, for example 3.11.x",
    )
    parser.add_argument("--implementation", default="cp", help="Target implementation tag (default: cp)")
    parser.add_argument("--abi", action="append", help="Target ABI tag; may be repeated")
    parser.add_argument(
        "--allow-source",
        action="store_true",
        help="Deprecated: rejected for reproducible cross-target bundles; build wheels in the target environment first",
    )


def validate_package(package: str) -> str:
    if not PACKAGE_RE.fullmatch(package):
        raise ValueError(f"Invalid package name or extras: {package!r}")
    return package


def validate_requirement(package: str, version: str) -> str:
    validate_package(package)
    if not VERSION_RE.fullmatch(version):
        raise ValueError(f"Invalid exact version: {version!r}")
    return f"{package}=={version}"


def version_query_package(package: str) -> str:
    validate_package(package)
    return package.split("[", 1)[0]


def list_available_versions(package: str) -> str:
    command = [
        sys.executable,
        "-m",
        "pip",
        "index",
        "versions",
        "--ignore-requires-python",
        version_query_package(package),
    ]
    result = subprocess.run(command, check=False, capture_output=True, text=True)
    if result.returncode != 0:
        detail = (result.stderr or result.stdout).strip()
        suffix = f": {detail}" if detail else ""
        raise RuntimeError(f"Could not list versions for {package!r}{suffix}")
    return result.stdout.strip()


def validate_python_version(version: str) -> tuple[int, int]:
    match = PYTHON_VERSION_RE.fullmatch(version)
    if not match:
        raise ValueError(
            f"Target Python version must be X.Y or X.Y.x, for example 3.11.x: {version!r}"
        )
    return tuple(int(match.group(name)) for name in ("major", "minor"))


def normalized_python_version(version: str) -> str:
    python_major, python_minor = validate_python_version(version)
    return f"{python_major}.{python_minor}"


def target_abis(args: argparse.Namespace) -> list[str]:
    if args.abi:
        return args.abi
    if args.implementation != "cp":
        return []
    python_major, python_minor = validate_python_version(args.python_version)
    return [f"cp{python_major}{python_minor}"]


def safe_path_part(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9._-]+", "-", value).strip("-.")


def default_output(package: str, version: str, python_version: str) -> Path:
    base_name = package.split("[", 1)[0]
    return Path("output") / "python-offline-dependency-packager" / (
        f"{safe_path_part(base_name)}-{safe_path_part(version)}-py"
        f"{normalized_python_version(python_version)}"
    )


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def build_download_command(args: argparse.Namespace, requirement: str, package_dir: Path) -> list[str]:
    python_version = normalized_python_version(args.python_version)
    if args.allow_source:
        raise SystemExit(
            "--allow-source is not supported for reproducible cross-target bundles. "
            "pip requires --only-binary=:all: when target Python/platform selectors are used. "
            "Build source distributions in a matching target environment, then package the resulting wheels."
        )
    command = [
        sys.executable,
        "-m",
        "pip",
        "download",
        "--disable-pip-version-check",
        "--dest",
        str(package_dir),
    ]
    command.append("--only-binary=:all:")
    for flag, value in (
        ("--platform", args.platform),
        ("--python-version", python_version),
        ("--implementation", args.implementation),
    ):
        if value:
            command.extend((flag, value))
    for abi in target_abis(args):
        command.extend(("--abi", abi))
    command.append(requirement)
    return command


def write_bundle_files(bundle_dir: Path, requirement: str, args: argparse.Namespace) -> None:
    package_dir = bundle_dir / "packages"
    (bundle_dir / "requirements.txt").write_text(requirement + "\n", encoding="utf-8")
    (bundle_dir / "install.ps1").write_text(POWERSHELL_INSTALLER, encoding="utf-8", newline="\n")
    shell_path = bundle_dir / "install.sh"
    shell_path.write_text(SHELL_INSTALLER, encoding="utf-8", newline="\n")
    shell_path.chmod(shell_path.stat().st_mode | 0o111)

    downloads = [
        {
            "file": path.name,
            "sha256": sha256_file(path),
            "size": path.stat().st_size,
        }
        for path in sorted(package_dir.iterdir(), key=lambda item: item.name.lower())
        if path.is_file()
    ]
    manifest = {
        "root_requirement": requirement,
        "download_python": sys.version.split()[0],
        "target": {
            "platform": args.platform,
            "requested_python_version": args.python_version,
            "python_version": normalized_python_version(args.python_version),
            "implementation": args.implementation,
            "abi": target_abis(args),
            "wheel_only": not args.allow_source,
        },
        "files": downloads,
    }
    (bundle_dir / "bundle-manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


def create_bundle(args: argparse.Namespace) -> Path:
    requirement = validate_requirement(args.package, args.version)
    validate_python_version(args.python_version)
    output = (
        args.output or default_output(args.package, args.version, args.python_version)
    ).resolve()
    if output.exists():
        raise FileExistsError(f"Output already exists; choose a new path: {output}")

    output.parent.mkdir(parents=True, exist_ok=True)
    temp_dir = Path(tempfile.mkdtemp(prefix=f".{output.name}-", dir=output.parent))
    try:
        package_dir = temp_dir / "packages"
        package_dir.mkdir()
        command = build_download_command(args, requirement, package_dir)
        subprocess.run(command, check=True)
        if not any(package_dir.iterdir()):
            raise RuntimeError("pip completed without downloading any package files")
        write_bundle_files(temp_dir, requirement, args)
        os.replace(temp_dir, output)
    except Exception:
        shutil.rmtree(temp_dir, ignore_errors=True)
        raise
    return output


def main(argv: Sequence[str] | None = None) -> int:
    return run(parse_args(argv))


def cli_main() -> int:
    return run(parse_args(installed=True))


def run(args: argparse.Namespace) -> int:
    command = getattr(args, "command", None)
    if command == "bundle" and not all((args.package, args.version, args.python_version)):
        print("error: package, version and target Python version must be non-empty", file=sys.stderr)
        return 2
    if not args.package:
        try:
            args.package = input("Dependency name: ").strip()
        except EOFError:
            print("error: dependency name is required", file=sys.stderr)
            return 2

    try:
        validate_package(args.package)
        if args.version:
            validate_requirement(args.package, args.version)
        if args.python_version:
            validate_python_version(args.python_version)
        if not args.version or not args.python_version:
            if not args.version:
                versions = list_available_versions(args.package)
                print(f"Available versions for {version_query_package(args.package)}:")
                print(versions)
                if command == "versions":
                    return 0
            if not args.python_version:
                print(
                    "Target Python version is missing. Specify --python-version "
                    "with X.Y or X.Y.x, for example 3.11 or 3.11.x."
                )
            print(
                "No packages were downloaded. Re-run with both --version and "
                "--python-version to create the offline bundle."
            )
            return 0
        output = create_bundle(args)
    except (ValueError, FileExistsError, RuntimeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    except subprocess.CalledProcessError as exc:
        print(f"error: pip download failed with exit code {exc.returncode}", file=sys.stderr)
        return exc.returncode or 1

    print(f"Offline bundle created: {output}")
    print(f"Downloaded files: {len(list((output / 'packages').iterdir()))}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
