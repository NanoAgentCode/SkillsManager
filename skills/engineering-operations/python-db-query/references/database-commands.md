# Database Commands And Drivers

Run these examples from the `python-db-query` skill directory. On Windows, the repository launcher resolves Python without relying on `python` or `py` on PATH. Override the interpreter with `SKILLS_MANAGER_PYTHON` when needed. In other shells, use the active `python3` and forward-slash paths.

## Local Setup

Use [config.md](config.md) for backend fields. Keep active config files and native clients under ignored paths. For Oracle 11g, point the config to the compatible client directory under `dependencies/` or to an existing installation.

```powershell
..\..\..\scripts\run-python.ps1 .\scripts\init_config.py --type oracle11g --host db.example.test --port 1521 --service-name ORCL --user readonly_user --password-env DB_PASSWORD --client-lib-dir .\dependencies\instantclient_11_2
..\..\..\scripts\run-python.ps1 .\scripts\check_dependencies.py --config .\config.json
```

```bash
python3 ./scripts/check_dependencies.py --config ./config.json
python3 ./scripts/query_db.py --config ./config.json --list-tables
```

When offline installation is approved, use the bundled Windows installer from the skill directory.

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\install_offline_dependencies.ps1
```

## Query Examples

For local exports, set `$ProjectRoot` to the absolute business project root before running the PowerShell examples.

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
..\..\..\scripts\run-python.ps1 .\scripts\query_db.py --config .\config.json --sql "select id, name from users" --format json --out "$ProjectRoot\output\python-db-query\users.json"
```

Export CSV:

```powershell
..\..\..\scripts\run-python.ps1 .\scripts\query_db.py --config .\config.json --sql "select * from orders limit 100" --format csv --out "$ProjectRoot\output\python-db-query\orders.csv"
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

## Driver Notes

- SQLite uses Python's built-in `sqlite3`.
- PostgreSQL requires either `psycopg` or `psycopg2`.
- MySQL requires either `pymysql` or `mysql-connector-python`.
- SQL Server requires `pyodbc`.
- Oracle 11g requires `oracledb==2.5.1` in Thick mode with Oracle Instant Client 11.2 or another compatible client, or the legacy `cx_Oracle` driver.
- MongoDB requires `pymongo`.
- Redis requires `redis`.
