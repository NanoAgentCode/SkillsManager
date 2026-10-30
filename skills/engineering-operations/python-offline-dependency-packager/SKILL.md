---
name: python-offline-dependency-packager
description: Use when preparing Python dependencies for an offline machine. Discovers package versions and bundles wheels, transitive dependencies, hashes, and installers only after an exact package version and target Python minor version are supplied.
---

# Python Offline Dependency Packager

Use `scripts/download_package.py` to resolve one pinned package, download its full dependency closure, and create a portable offline bundle.

## Workflow

1. Collect the package name interactively. If it was not supplied in the request, run the script without `--package` and let it prompt with `Dependency name:`.
2. Require an exact package version and a target Python version in `X.Y` or `X.Y.x` form before downloading. Never infer the target Python version from the current interpreter. When the package version is missing, the script runs `pip index versions --ignore-requires-python` against the configured index, shows the visible versions without filtering them against the current interpreter, and stops. When the target Python version is missing, it explains the accepted format and stops. Neither incomplete path downloads package files.
3. From the repository root, run the downloader with the repository Python launcher. For discovery:

   ```powershell
   .\scripts\run-python.ps1 .\skills\engineering-operations\python-offline-dependency-packager\scripts\download_package.py
   ```

   For a complete download request:

   ```powershell
   .\scripts\run-python.ps1 .\skills\engineering-operations\python-offline-dependency-packager\scripts\download_package.py `
     --package requests --version 2.32.5 --python-version 3.11
   ```

   `--python-version 3.11.x` is equivalent and is normalized to `3.11` before pip runs.

4. Deliver the generated directory under `output/python-offline-dependency-packager/`. It contains:
   - `packages/`: the pinned package and every dependency selected by pip.
   - `requirements.txt`: the exact requested root requirement.
   - `bundle-manifest.json`: target metadata plus SHA-256 hashes for downloaded files.
   - `install.ps1`: one-click PowerShell installer.
   - `install.sh`: one-click POSIX-shell installer.
5. On the offline machine, extract or copy the complete directory, then run one installer:

   ```powershell
   powershell -ExecutionPolicy Bypass -File .\install.ps1
   ```

   ```bash
   sh ./install.sh
   ```

6. Verify the package after installation with the target interpreter, using the import name supplied by the user when it differs from the distribution name.

## Target Compatibility

The target Python minor-version line is always required. The downloader defaults to CPython and derives its ABI tag from that version; for example, `3.11.x` becomes pip target `3.11` with ABI `cp311`. Pip then selects the newest available transitive dependency versions compatible with that Python line and the pinned root package. This does not download Python itself or resolve `3.11.x` to a concrete Python patch release. The current machine supplies the default platform unless `--platform` is provided.

For another platform, pass the target selector explicitly:

```powershell
.\scripts\run-python.ps1 .\skills\engineering-operations\python-offline-dependency-packager\scripts\download_package.py `
  --package cryptography --version 45.0.6 --python-version 3.12 `
  --platform win_amd64
```

Wheel-only mode is required because this skill targets a specific Python and platform and must produce installation-ready bundles. `--allow-source` is rejected: build source distributions in a matching target environment first, then package the resulting wheels. Pip configuration and environment variables may be used for approved private indexes; never embed credentials in the bundle or command examples.

The downloader refuses to overwrite an existing output directory. Choose a new `--output` path or remove the old bundle only after confirming it is safe to do so.
