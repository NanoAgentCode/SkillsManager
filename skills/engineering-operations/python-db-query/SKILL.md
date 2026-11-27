---
name: python-db-query
description: Use when querying databases, inspecting schemas or execution plans, or listing and downloading MinIO/S3 objects through bundled Python wrappers. Uses local configuration, read-only defaults, and explicit write/overwrite controls.
---

# Python DB Query

Use the selected operation with a local, ignored config file. For requested local exports or downloads, default to `<business-project>/output/python-db-query/` or the user's explicit destination.

1. Identify the target and scope from the request and existing configuration. Prefer the explicit `--config` path, then this skill's `config.json`, then a project-local config path named by the user. If several targets match or required connection fields are missing, ask for just those details together.
2. Select the command for the configured backend.
   - **Relational databases, MongoDB and Redis**. Use `scripts/query_db.py`. Read [config.md](references/config.md) when setup is needed and [database-commands.md](references/database-commands.md) for the applicable command, driver, or offline installation. For unfamiliar relational schemas, start with metadata, then query a small sample or inspect a plan.
   - **MinIO/S3**. Read [minio.md](references/minio.md) for configuration and use `scripts/minio_mc.py` for listing, object metadata and downloads.
3. Use `scripts/check_dependencies.py --config <path>` when checking setup. Ask before installing missing dependencies. Report the observed results or output paths and redact credentials.

## When to ask

- Use an existing suitable config for ordinary reads. If setup is needed, use `scripts/init_config.py` or the relevant example in [config.md](references/config.md) or [minio.md](references/minio.md). Prefer environment-variable references for credentials and confirm before persisting a new local config unless the user already requested it.
- Start with read-only queries and small samples. Before a write or DDL operation, verify authorization for the target and intended changes, then use `--allow-write`. For a potentially expensive query or broad scan, ask about the affected scope if the user has yet to approve it. The SQL runner uses read-only transactions where supported and rolls them back. Prefer an account with the minimum privileges, especially for SQL Server.
- For object downloads, resolve the bucket/key and local destination. If the destination exists, use a new path when it meets the request, or use `--overwrite` only when authorized for that file. Keep MinIO operations within the wrapper's read-only remote capabilities.
