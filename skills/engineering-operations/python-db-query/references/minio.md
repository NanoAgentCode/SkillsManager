# MinIO Through `mc`

Use the official MinIO Client (`mc`) for MinIO and other S3-compatible object stores. The wrapper is read-only with one local-output exception: `download` writes a named local file and refuses to overwrite it unless `--overwrite` is explicit.

The wrapper supplies a temporary `MC_HOST_skillsmanager` environment variable to the child process. It does not run `mc alias set`, modify `~/.mc/config.json`, or put access/secret keys in command-line arguments.

## Bundled `mc`

The skill includes official MinIO Client `RELEASE.2025-08-13T08-35-41Z` binaries for Windows AMD64 and Linux AMD64. The wrapper selects the matching dependency before checking `PATH`, so those platforms do not need a separate installation.

### Windows x64

The bundled client is:

```powershell
.\dependencies\mc.exe --version
```

The wrapper searches `dependencies/mc.exe` and then `PATH`. A custom path can be set in config.

### Linux

For AMD64, the bundled executable can be checked with:

```bash
./dependencies/mc --version
```

Linux ARM64 is not bundled. After explicit user approval, download the official `linux-arm64/mc` binary to another local path and select it with `mc_path`. Do not replace the tracked AMD64 binary with a different architecture under the same filename.

When updating either bundled binary, download it only from the official URLs in the MinIO Client Quickstart, verify its published SHA-256 value, rerun Windows/Linux connection tests, and update the recorded release version in this reference and `dependencies/README.md`.

## Config

Prefer environment-variable references so credentials are not stored in JSON:

```json
{
  "type": "minio",
  "endpoint": "https://minio.example.com",
  "access_key_env": "MINIO_ACCESS_KEY",
  "secret_key_env": "MINIO_SECRET_KEY",
  "mc_path": "dependencies/mc.exe"
}
```

`mc_path` is optional and resolves relative to the config file. Omit it when the binary is in the skill `dependencies/` directory or on `PATH`. On Linux a local value is normally `dependencies/mc`.

Optional fields:

- `session_token_env`: environment variable holding an STS session token.
- `anonymous`: use anonymous access; cannot be combined with credentials.
- `insecure`: disable TLS certificate verification. Use only when the user explicitly accepts that risk.
- Literal `access_key`, `secret_key`, and `session_token` are supported for compatibility but environment variables are preferred.

Initialize the config on Windows without writing credentials:

```powershell
..\..\..\scripts\run-python.ps1 .\scripts\init_config.py `
  --type minio `
  --endpoint https://minio.example.com `
  --access-key-env MINIO_ACCESS_KEY `
  --secret-key-env MINIO_SECRET_KEY `
  --mc-path .\dependencies\mc.exe
```

Linux equivalent:

```bash
python3 ./scripts/init_config.py \
  --type minio \
  --endpoint https://minio.example.com \
  --access-key-env MINIO_ACCESS_KEY \
  --secret-key-env MINIO_SECRET_KEY \
  --mc-path ./dependencies/mc
```

## Commands

Windows examples use the repository launcher. Set `$ProjectRoot` to the absolute business project root before running the download:

```powershell
..\..\..\scripts\run-python.ps1 .\scripts\minio_mc.py --config .\config.json test-connection
..\..\..\scripts\run-python.ps1 .\scripts\minio_mc.py --config .\config.json list-buckets
..\..\..\scripts\run-python.ps1 .\scripts\minio_mc.py --config .\config.json list-objects assets --prefix images/ --recursive
..\..\..\scripts\run-python.ps1 .\scripts\minio_mc.py --config .\config.json stat assets images/logo.png
..\..\..\scripts\run-python.ps1 .\scripts\minio_mc.py --config .\config.json download assets images/logo.png "$ProjectRoot\output\python-db-query\logo.png"
```

On Linux, replace the launcher prefix with `python3`:

```bash
python3 ./scripts/minio_mc.py --config ./config.json list-buckets
python3 ./scripts/minio_mc.py --config ./config.json list-objects assets --prefix images/ --recursive
```

All remote operation output is JSON Lines from `mc`. The wrapper adds `--json`, `--no-color`, `--quiet`, and `--disable-pager` for deterministic non-interactive use.

This wrapper intentionally does not expose upload, delete, mirroring, policy, or admin commands. Run mutating `mc` commands only as a separately authorized workflow.

Official references:

- [MinIO Client Quickstart and platform binaries](https://github.com/minio/mc/blob/master/README.md)
- [MinIO Client environment settings and `MC_HOST_<ALIAS>`](https://docs.min.io/aistor/reference/cli/aistor-client-settings/)
