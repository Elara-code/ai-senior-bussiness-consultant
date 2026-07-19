#!/usr/bin/env bash
set -euo pipefail

api_url="${API_URL:-http://localhost:8000}"
organization_id="00000000-0000-4000-8000-000000000001"
user_id="00000000-0000-4000-8000-000000000002"
token="$(docker compose exec -T api python -m consultant.cli dev-token --organization-id "$organization_id" --user-id "$user_id")"
auth_header="Authorization: Bearer $token"

project_id="$(curl -fsS -X POST "$api_url/api/v1/projects" -H "$auth_header" -H 'Content-Type: application/json' -d '{"name":"演示客户 AI 项目"}' | python -c 'import json,sys; print(json.load(sys.stdin)["id"])')"

document_file="$(mktemp)"
trap 'rm -f "$document_file"' EXIT
printf '# 当前流程\n\n每周经营报告由三名员工手工汇总。\n' > "$document_file"
curl -fsS -X POST "$api_url/api/v1/projects/$project_id/documents" -H "$auth_header" -F "file=@$document_file;filename=interview.md;type=text/markdown" >/dev/null

run_id="$(curl -fsS -X POST "$api_url/api/v1/projects/$project_id/agent-runs" -H "$auth_header" -H 'Idempotency-Key: demo-request-0001' -H 'Content-Type: application/json' -d '{"agent":"requirement_analysis","input":{"objective":"分析经营报告现状并形成需求基线"}}' | python -c 'import json,sys; print(json.load(sys.stdin)["id"])')"

curl -fsS -N "$api_url/api/v1/agent-runs/$run_id/events" -H "$auth_header"
