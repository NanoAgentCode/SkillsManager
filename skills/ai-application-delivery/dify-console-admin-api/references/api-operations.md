> Read only for the mode linked from SKILL.md. Unless stated otherwise, command and resource paths are relative to the skill directory, not this references directory.

## 推荐变量模板

让用户先在 shell 中设置变量，再执行后续命令：

```bash
export DIFY_BASE_URL="https://dify.example.com"
export ADMIN_API_KEY="your-admin-key"
export WORKSPACE_ID="your-workspace-id"
```

如果用户明确是在本地开发环境测试，`DIFY_BASE_URL` 常见值是：

```bash
export DIFY_BASE_URL="http://127.0.0.1:5001"
```

## 请求头规则

所有通过 admin key 鉴权的 Console API 请求都要带：

```text
Authorization: Bearer ${ADMIN_API_KEY}
X-WORKSPACE-ID: ${WORKSPACE_ID}
```

admin key 生效时不需要 `X-CSRF-Token`，也不需要登录 cookie。API 会在指定 workspace 中找到一个 owner 账号，并以该账号身份执行。

## 可选：查询 workspace id

如果用户不知道 `WORKSPACE_ID`，最简单的方式是在 Dify 网页上按 F12 打开开发者工具，找到 `/console/api/workspaces` 接口的响应，其中 `id` 字段即为 `WORKSPACE_ID`：

```json
{
  "workspaces": [
    {
      "id": "d4e26a01-162f-4366-9a25-1c2c1bdd15dz",
      "name": "admin's Workspace",
      "current": true
    }
  ]
}
```

## 创建工作流应用

先确认：

```bash
export APP_NAME="admin-key-test-workflow"
export APP_DESCRIPTION="created by admin api key test"
```

```bash
curl -i -X POST "${DIFY_BASE_URL}/console/api/apps" \
  -H "Authorization: Bearer ${ADMIN_API_KEY}" \
  -H "X-WORKSPACE-ID: ${WORKSPACE_ID}" \
  -H "Content-Type: application/json" \
  -d "{
    \"name\": \"${APP_NAME}\",
    \"mode\": \"workflow\",
    \"description\": \"${APP_DESCRIPTION}\"
  }"
```

成功时应返回：

```text
HTTP/1.1 201 CREATED
```

## 导出应用或工作流 DSL

先确认：

```bash
export APP_ID="your-app-id"
export INCLUDE_SECRET="false"
```

```bash
curl -sS -X GET \
  "${DIFY_BASE_URL}/console/api/apps/${APP_ID}/export?include_secret=${INCLUDE_SECRET}" \
  -H "Authorization: Bearer ${ADMIN_API_KEY}" \
  -H "X-WORKSPACE-ID: ${WORKSPACE_ID}"
```

如果要导出指定草稿 workflow，追加 `workflow_id`：

```bash
export WORKFLOW_ID="your-workflow-id"

curl -sS -X GET \
  "${DIFY_BASE_URL}/console/api/apps/${APP_ID}/export?include_secret=${INCLUDE_SECRET}&workflow_id=${WORKFLOW_ID}" \
  -H "Authorization: Bearer ${ADMIN_API_KEY}" \
  -H "X-WORKSPACE-ID: ${WORKSPACE_ID}"
```

响应结构：

```json
{
  "data": "version: 0.6.0\nkind: app\n..."
}
```

## 导入 DSL

从 YAML 内容导入：

```bash
export YAML_CONTENT="$(cat /path/to/workflow.yml)"

curl -i -X POST "${DIFY_BASE_URL}/console/api/apps/imports" \
  -H "Authorization: Bearer ${ADMIN_API_KEY}" \
  -H "X-WORKSPACE-ID: ${WORKSPACE_ID}" \
  -H "Content-Type: application/json" \
  --data-binary @- <<JSON
{
  "mode": "yaml-content",
  "yaml_content": $(python3 -c 'import json, os; print(json.dumps(os.environ["YAML_CONTENT"]))')
}
JSON
```

从 URL 导入：

```bash
export YAML_URL="https://example.com/workflow.yml"

curl -i -X POST "${DIFY_BASE_URL}/console/api/apps/imports" \
  -H "Authorization: Bearer ${ADMIN_API_KEY}" \
  -H "X-WORKSPACE-ID: ${WORKSPACE_ID}" \
  -H "Content-Type: application/json" \
  -d "{
    \"mode\": \"yaml-url\",
    \"yaml_url\": \"${YAML_URL}\"
  }"
```

如果要覆盖已有 workflow 或 advanced-chat 应用，传入 `app_id`：

```bash
export APP_ID="existing-app-id"
export YAML_CONTENT="$(cat /path/to/workflow.yml)"

curl -i -X POST "${DIFY_BASE_URL}/console/api/apps/imports" \
  -H "Authorization: Bearer ${ADMIN_API_KEY}" \
  -H "X-WORKSPACE-ID: ${WORKSPACE_ID}" \
  -H "Content-Type: application/json" \
  --data-binary @- <<JSON
{
  "mode": "yaml-content",
  "yaml_content": $(python3 -c 'import json, os; print(json.dumps(os.environ["YAML_CONTENT"]))'),
  "app_id": "${APP_ID}"
}
JSON
```

如果导入返回 `202` 且 `status: pending`，需要确认导入：

```bash
export IMPORT_ID="your-import-id"

curl -i -X POST "${DIFY_BASE_URL}/console/api/apps/imports/${IMPORT_ID}/confirm" \
  -H "Authorization: Bearer ${ADMIN_API_KEY}" \
  -H "X-WORKSPACE-ID: ${WORKSPACE_ID}" \
  -H "Content-Type: application/json" \
  -d '{}'
```

## 排查

- `201 CREATED`：创建应用成功。
- `200 OK`：导出或导入完成，或已返回数据。
- `202 ACCEPTED`：导入进入 pending，需要调用 confirm 接口。
- `401 Invalid token`：admin key 缺失、未启用、值不正确，或配置变更后 API 进程未重启。
- Connection refused：`DIFY_BASE_URL` 不可达，或 API 服务未运行。
- `ModuleNotFoundError: werkzeug.utils`：`.venv` 里的 Werkzeug 安装损坏；重装 `Werkzeug==3.1.6` 或重建 `api/.venv`。
