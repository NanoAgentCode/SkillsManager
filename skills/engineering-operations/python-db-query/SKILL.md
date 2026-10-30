---
name: python-db-query
description: Use when querying databases, inspecting schemas or execution plans, or listing and downloading MinIO/S3 objects through bundled Python wrappers. Uses local configuration, read-only defaults, and explicit write/overwrite controls.
---

# Python DB Query

## Overview

Use this skill to run database queries through `scripts/query_db.py` or read MinIO object storage through `scripts/minio_mc.py`, while keeping connection settings in a local config file.

Do not commit real credentials. Create an ignored local `config.json` with `scripts/init_config.py`, or use another ignored config path.

## Workflow

1. Confirm the query goal and target database or MinIO endpoint.
2. Look for a config file in this order:
   - User-provided `--config` path.
   - `skills/engineering-operations/python-db-query/config.json`.
   - A project-local config path the user names.
3. If no config exists, ask the user for the required connection fields:
   - `type`: `sqlite`, `postgres`, `mysql`, `sqlserver`, `oracle`, `oracle11g`, `mongo`, `redis`, or `minio`.
   - Host/port/database/user/password for server databases, or `path` for SQLite.
   - Endpoint plus access/secret-key environment variable names for MinIO, or confirm anonymous access.
   - Optional schema and SSL/options if needed.
4. Save real settings only to an ignored local config file after the user provides them.
5. Optionally run `scripts/check_dependencies.py --config .\config.json` before the first connection.
6. Run database work with `scripts/query_db.py`. For `type=minio`, read [references/minio.md](references/minio.md), then use `scripts/minio_mc.py`.
7. Summarize results without exposing credentials.

For an unfamiliar relational database, discover structure in this order: schemas, tables/views, columns, keys/indexes, then a small query or execution plan. Skip steps when the user already supplied the relevant schema.

## Safety Rules

- Default to read-only SQL. The script blocks write statements, multi-statements, `SELECT ... INTO`, and state-changing SQLite pragmas unless `--allow-write` is explicitly passed. It rolls back read-only queries and opens a read-only transaction where the server supports one; use a database account with only the permissions it needs, especially for SQL Server.
- Do not print passwords, tokens, DSNs with credentials, or full config contents in final answers.
- Prefer credential environment-variable references over literal secrets in config.
- Ask before running potentially expensive queries, broad table scans, or write operations.
- Prefer `--limit` for exploratory queries.
- For unknown schemas, first query metadata tables or run small sample queries.
- MinIO operations in this skill are read-only except for downloading to a user-selected local path. Never overwrite a local destination unless `--overwrite` is explicit.
- Do not run `mc alias set`; the wrapper uses a temporary `MC_HOST_skillsmanager` child-process environment variable so credentials do not persist in the user's global mc config.

## Config

Start from:

```powershell
Copy-Item .\config.example.json .\config.json
```

Then edit `config.json` locally. See `references/config.md` for config examples and field descriptions.

On Windows, do not assume a global `python` alias is available. Use the repository launcher:

```powershell
..\..\..\scripts\run-python.ps1 -c "import sys; print(sys.executable)"
```

The skill `.gitignore` ignores:

- `config.json`
- `config.*.json`
- `.env`
- `outputs/`

Native client binaries can be placed under `dependencies/`. That directory ignores everything except its README and `.gitignore`, so Oracle Instant Client or other local database clients do not get committed.

Initialize a config without echoing the password:

```powershell
..\..\..\scripts\run-python.ps1 .\scripts\init_config.py --type oracle11g --host oracle-dev.lark.com --port 1521 --service-name ORCL --user LARK_MASTER --client-lib-dir "D:/lark-projects/skills-manager/skills/engineering-operations/python-db-query/dependencies/instantclient_11_2"
```

Or use an environment variable instead of writing a password:

```powershell
$env:DB_PASSWORD="..."
..\..\..\scripts\run-python.ps1 .\scripts\init_config.py --type oracle11g --host oracle-dev.lark.com --port 1521 --service-name ORCL --user LARK_MASTER --password-env DB_PASSWORD --client-lib-dir "D:/lark-projects/skills-manager/skills/engineering-operations/python-db-query/dependencies/instantclient_11_2"
```

Install bundled Python wheels offline:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\install_offline_dependencies.ps1
```

Check dependencies:

```powershell
..\..\..\scripts\run-python.ps1 .\scripts\check_dependencies.py --config .\config.json
```

## Query Examples

Run inline SQL:

```powershell
..\..\..\scripts\run-python.ps1 .\scripts\query_db.py --config .\config.json --sql "select * from users limit 10"
```

Run SQL from a file:

```powershell
..\..\..\scripts\run-python.ps1 .\scripts\query_db.py --config .\config.json --sql-file .\queries\active_users.sql --format table
```

Export JSON:

```powershell
..\..\..\scripts\run-python.ps1 .\scripts\query_db.py --config .\config.json --sql "select id, name from users" --format json --out .\outputs\users.json
```

Export CSV:

```powershell
..\..\..\scripts\run-python.ps1 .\scripts\query_db.py --config .\config.json --sql "select * from orders limit 100" --format csv --out .\outputs\orders.csv
```

List tables:

```powershell
..\..\..\scripts\run-python.ps1 .\scripts\query_db.py --config .\config.json --list-tables
```

Describe a table:

```powershell
..\..\..\scripts\run-python.ps1 .\scripts\query_db.py --config .\config.json --describe FLOW_TOOL_NODE
```

List schemas and views:

```powershell
..\..\..\scripts\run-python.ps1 .\scripts\query_db.py --config .\config.json --list-schemas
..\..\..\scripts\run-python.ps1 .\scripts\query_db.py --config .\config.json --list-views
```

Inspect indexes and a primary key. Schema-qualified names are supported:

```powershell
..\..\..\scripts\run-python.ps1 .\scripts\query_db.py --config .\config.json --list-indexes public.users
..\..\..\scripts\run-python.ps1 .\scripts\query_db.py --config .\config.json --primary-key public.users
```

Show a read-only query execution plan without running the query:

```powershell
..\..\..\scripts\run-python.ps1 .\scripts\query_db.py --config .\config.json --explain --sql "select * from users where email = :email" --params '{"email":"a@example.com"}'
```

Execution-plan output is dialect-specific. SQLite uses `EXPLAIN QUERY PLAN`, PostgreSQL and MySQL request JSON plans, SQL Server uses `SHOWPLAN_TEXT`, and Oracle uses `DBMS_XPLAN` with a temporary `PLAN_TABLE` entry that is cleaned up and rolled back. `--explain` accepts only SQL that passes the read-only guard.

Count a table:

```powershell
..\..\..\scripts\run-python.ps1 .\scripts\query_db.py --config .\config.json --count FLOW_TOOL_NODE
```

Test a connection:

```powershell
..\..\..\scripts\run-python.ps1 .\scripts\query_db.py --config .\config.json --test-connection
```

MongoDB examples:

```powershell
..\..\..\scripts\run-python.ps1 .\scripts\query_db.py --config .\config.json --test-connection
..\..\..\scripts\run-python.ps1 .\scripts\query_db.py --config .\config.json --mongo-list-collections
..\..\..\scripts\run-python.ps1 .\scripts\query_db.py --config .\config.json --mongo-count TOPO
..\..\..\scripts\run-python.ps1 .\scripts\query_db.py --config .\config.json --mongo-find TOPO --filter "{}" --limit 5 --format json
```

MongoDB writes require `--allow-write`:

```powershell
..\..\..\scripts\run-python.ps1 .\scripts\query_db.py --config .\config.json --mongo-insert-one TOPO --document "{""name"":""demo""}" --allow-write
```

Redis examples:

```powershell
..\..\..\scripts\run-python.ps1 .\scripts\query_db.py --config .\config.json --test-connection
..\..\..\scripts\run-python.ps1 .\scripts\query_db.py --config .\config.json --redis-dbsize
..\..\..\scripts\run-python.ps1 .\scripts\query_db.py --config .\config.json --redis-scan "*" --limit 20
..\..\..\scripts\run-python.ps1 .\scripts\query_db.py --config .\config.json --redis-get my-key
```

Redis writes require `--allow-write`:

```powershell
..\..\..\scripts\run-python.ps1 .\scripts\query_db.py --config .\config.json --redis-set my-key my-value --allow-write
```

## MinIO

For MinIO or S3-compatible object storage, read [references/minio.md](references/minio.md). The separate cross-platform wrapper discovers `mc.exe` on Windows and `mc` on Linux, then supports connection testing, bucket/object listing, object metadata, and guarded downloads.

Quick connection test:

```powershell
..\..\..\scripts\run-python.ps1 .\scripts\minio_mc.py --config .\config.json test-connection
```

The repository Windows launcher resolves Python without relying on `python` or `py` being on `PATH`. If it cannot find Python, it reports the missing Python interpreter prerequisite and the checked locations. To force a specific interpreter, set `SKILLS_MANAGER_PYTHON` to the full `python.exe` path before running the command.

For non-Windows environments, replace the launcher with the active Python executable for that shell, usually `python3`.

## Driver Notes

- SQLite uses Python's built-in `sqlite3`.
- PostgreSQL requires either `psycopg` or `psycopg2`.
- MySQL requires either `pymysql` or `mysql-connector-python`.
- SQL Server requires `pyodbc`.
- Oracle 11g requires `oracledb==2.5.1` in Thick mode with Oracle Instant Client 11.2 or another compatible client, or the legacy `cx_Oracle` driver.
- MongoDB requires `pymongo`.
- Redis requires `redis`.
- MinIO requires the official MinIO Client binary: `mc.exe` on Windows or `mc` on Linux. It does not require a Python MinIO SDK.

If a driver is missing, do not install automatically. Tell the user which package is required and ask before installing dependencies.
