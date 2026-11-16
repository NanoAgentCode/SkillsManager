"""Manage Dify applications through the Console Admin API."""

import argparse
import json
import os
import sys
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlencode, urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def request_spec(args):
    if args.command == "create":
        return "POST", "/apps", {"name": args.name, "mode": "workflow", "description": args.description}
    if args.command == "export":
        query = {"include_secret": str(args.include_secret).lower()}
        if args.workflow_id:
            query["workflow_id"] = args.workflow_id
        return "GET", f"/apps/{quote(args.app_id, safe='')}/export?{urlencode(query)}", None
    if args.command == "confirm":
        return "POST", f"/apps/imports/{quote(args.import_id, safe='')}/confirm", {}

    if args.file:
        payload = {"mode": "yaml-content", "yaml_content": args.file.read_text(encoding="utf-8-sig")}
    else:
        payload = {"mode": "yaml-url", "yaml_url": args.url}
    if args.app_id:
        payload["app_id"] = args.app_id
    return "POST", "/apps/imports", payload


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    create = commands.add_parser("create", help="Create a workflow app")
    create.add_argument("--name", required=True)
    create.add_argument("--description", default="")
    export = commands.add_parser("export", help="Export an app or workflow DSL")
    export.add_argument("app_id")
    export.add_argument("--workflow-id")
    export.add_argument("--include-secret", action="store_true")
    export.add_argument("--output", type=Path, help="Save the YAML instead of including it in stdout")
    import_dsl = commands.add_parser("import", help="Import a DSL into a new or existing app")
    source = import_dsl.add_mutually_exclusive_group(required=True)
    source.add_argument("--file", type=Path)
    source.add_argument("--url")
    import_dsl.add_argument("--app-id", help="Overwrite an existing workflow or advanced-chat app")
    confirm = commands.add_parser("confirm", help="Confirm a pending import")
    confirm.add_argument("import_id")
    args = parser.parse_args()

    base, key, workspace = (os.environ.get(name, "").strip() for name in
                            ("DIFY_BASE_URL", "ADMIN_API_KEY", "WORKSPACE_ID"))
    if not all((base, key, workspace)):
        parser.error("Set DIFY_BASE_URL, ADMIN_API_KEY and WORKSPACE_ID in the environment.")
    parsed = urlsplit(base)
    if parsed.scheme not in ("http", "https") or not parsed.hostname or parsed.username or parsed.query or parsed.fragment:
        parser.error("DIFY_BASE_URL must be an HTTP(S) base URL without credentials, query or fragment.")

    try:
        method, path, payload = request_spec(args)
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8") if payload is not None else None
        request = Request(base.rstrip("/") + "/console/api" + path, data=body, method=method, headers={
            "Authorization": f"Bearer {key}",
            "X-WORKSPACE-ID": workspace,
            "Content-Type": "application/json",
        })
        opener = build_opener(NoRedirect)
        try:
            response = opener.open(request, timeout=30)
        except HTTPError as error:
            response = error
        with response:
            status = response.code
            raw = response.read().decode("utf-8", errors="replace")
        try:
            result = json.loads(raw)
        except ValueError:
            result = raw

        report = {"http_status": status, "response": result}
        success = 200 <= status < 300
        if success and args.command == "export" and args.output:
            if not isinstance(result, dict) or not isinstance(result.get("data"), str):
                print(json.dumps({"http_status": status, "error": "Response has no YAML data"}))
                return 1
            args.output.write_text(result["data"], encoding="utf-8")
            report = {"http_status": status, "output": str(args.output)}
        print(json.dumps(report))
        if status == 202 or isinstance(result, dict) and result.get("status") == "pending":
            return 3
        if isinstance(result, dict) and result.get("status") == "failed":
            return 1
        return 0 if success else 1
    except (OSError, ValueError, URLError) as error:
        print(f"Dify Console operation failed: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
