import json
import os
import shutil
import subprocess
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path


@unittest.skipUnless(shutil.which("dify-console"), "Install dify-console")
class DifyConsoleTests(unittest.TestCase):
    def test_admin_operations_and_pending_import(self):
        requests = []

        class Handler(BaseHTTPRequestHandler):
            def reply(self):
                length = int(self.headers.get("Content-Length", "0"))
                body = json.loads(self.rfile.read(length)) if length else None
                requests.append((self.command, self.path, body, self.headers["Authorization"],
                                 self.headers["X-WORKSPACE-ID"]))
                if self.path.startswith("/console/api/apps/demo/export?"):
                    status, result = 200, {"data": "kind: app\n"}
                elif self.path == "/console/api/apps":
                    status, result = 201, {"id": "demo"}
                elif self.path == "/console/api/apps/imports":
                    status, result = 202, {"status": "pending", "id": "pending-demo"}
                elif self.path == "/console/api/apps/imports/pending-demo/confirm":
                    status, result = 200, {"status": "completed", "app_id": "demo"}
                else:
                    status, result = 401, {"message": "Invalid token"}
                self.send_response(status)
                self.end_headers()
                self.wfile.write(json.dumps(result).encode())

            do_POST = do_GET = reply

        with ThreadingHTTPServer(("127.0.0.1", 0), Handler) as server, tempfile.TemporaryDirectory() as temp:
            worker = threading.Thread(target=server.serve_forever)
            worker.start()
            env = {**os.environ, "DIFY_BASE_URL": f"http://127.0.0.1:{server.server_port}",
                   "ADMIN_API_KEY": "fixture-key", "WORKSPACE_ID": "demo-workspace", "NO_PROXY": "127.0.0.1"}

            def run(*args, expected=0):
                result = subprocess.run(["dify-console", *args], env=env, capture_output=True, timeout=30)
                self.assertEqual(result.returncode, expected, result.stderr or result.stdout)
                return json.loads(result.stdout)

            try:
                self.assertEqual(run("create", "--name", "Demo")["http_status"], 201)
                yaml = Path(temp) / "app.yml"
                run("export", "demo", "--workflow-id", "draft", "--output", str(yaml))
                self.assertEqual(yaml.read_text(encoding="utf-8"), "kind: app\n")
                pending = run("import", "--file", str(yaml), "--app-id", "demo", expected=3)
                self.assertEqual(pending["http_status"], 202)
                self.assertEqual(len(requests), 3)
                self.assertEqual(run("confirm", pending["response"]["id"])["response"]["status"], "completed")
                run("import", "--url", "https://example.test/app.yml", expected=3)
                self.assertEqual(run("export", "unknown", expected=1)["http_status"], 401)
            finally:
                server.shutdown()
                worker.join()

        self.assertEqual(requests[0][2], {"name": "Demo", "mode": "workflow", "description": ""})
        self.assertEqual(requests[1][1], "/console/api/apps/demo/export?include_secret=false&workflow_id=draft")
        self.assertEqual(requests[2][2], {"mode": "yaml-content", "yaml_content": "kind: app\n", "app_id": "demo"})
        self.assertEqual(requests[3][2], {})
        self.assertEqual(requests[4][2], {"mode": "yaml-url", "yaml_url": "https://example.test/app.yml"})
        self.assertTrue(all(request[3:] == ("Bearer fixture-key", "demo-workspace") for request in requests))
