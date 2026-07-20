#!/usr/bin/env bash
set -euo pipefail

api_url="${API_URL:-http://localhost:8000}"
organization_id="00000000-0000-4000-8000-000000000001"
user_id="00000000-0000-4000-8000-000000000002"
token="${CONSULTANT_DEV_TOKEN:-$(docker compose exec -T api python -m consultant.cli dev-token --organization-id "$organization_id" --user-id "$user_id")}" 
auth_header="Authorization: Bearer $token"

request() {
  curl --fail-with-body -sS "$@"
}

json_id() {
  python -c 'import json,sys
raw=sys.stdin.read()
try:
    print(json.loads(raw)["id"])
except Exception:
    print(raw, file=sys.stderr)
    raise'
}

project_id="$(request -X POST "$api_url/api/v1/projects" -H "$auth_header" -H 'Content-Type: application/json' -d '{"name":"阶段二闭环演示","description":"脱敏的日企经营报告自动化试点"}' | json_id)"
echo "[1/8] 项目已创建: $project_id"

document_file="$(mktemp)"
trap 'rm -f "$document_file"' EXIT
printf '# 脱敏访谈\n\n每周经营报告由三名员工手工汇总，目标是将初稿时间缩短 50%%，必须保留人工审批。\n' > "$document_file"
request -X POST "$api_url/api/v1/projects/$project_id/documents" -H "$auth_header" -F "file=@$document_file;filename=sanitized-interview.md;type=text/markdown" >/dev/null
echo "[2/8] 脱敏材料已上传"

create_object() {
  local path="$1" title="$2" payload="$3"
  request -X POST "$api_url/api/v1/projects/$project_id/$path" -H "$auth_header" -H 'Content-Type: application/json' -d "{\"title\":\"$title\",\"payload\":$payload,\"statements\":[]}" | json_id
}

requirement_id="$(create_object requirements '需求基线 v1' '{"objective":"报告初稿提效 50%","constraints":["人工审批","不使用真实客户数据"]}')"
scenario_id="$(create_object scenarios '智能报告方案' '{"workflow":["材料解析","证据检索","报告生成","人工审批"]}')"
business_case_id="$(create_object business-cases '价值与风险分析' '{"baseline_hours":24,"target_hours":12,"formula":"(24-12)/24=50%","risks":["幻觉","敏感信息泄露"]}')"
echo "[3/8] 需求、方案和价值分析已形成: $requirement_id / $scenario_id / $business_case_id"

approval_id="$(request -X POST "$api_url/api/v1/projects/$project_id/approvals" -H "$auth_header" -H 'Content-Type: application/json' -d "{\"target_kind\":\"requirement_baseline\",\"target_id\":\"$requirement_id\",\"target_version\":1}" | json_id)"
request -X POST "$api_url/api/v1/projects/$project_id/approvals/$approval_id/decision" -H "$auth_header" -H 'Content-Type: application/json' -d '{"decision":"approved","expected_target_version":1,"comment":"演示验收通过"}' >/dev/null
echo "[4/8] 需求快照已审批"

proposal_id="$(create_object proposals 'AI 经营报告项目提案' '{"scope":["报告生成","证据追溯"],"acceptance":["引用覆盖率不少于95%","所有导出经过审批"]}')"
delivery_id="$(create_object delivery-plans '试点交付计划' '{"milestones":["环境准备","历史项目验证","用户培训","试运行"]}')"
proposal_approval_id="$(request -X POST "$api_url/api/v1/projects/$project_id/approvals" -H "$auth_header" -H 'Content-Type: application/json' -d "{\"target_kind\":\"proposal\",\"target_id\":\"$proposal_id\",\"target_version\":1}" | json_id)"
request -X POST "$api_url/api/v1/projects/$project_id/approvals/$proposal_approval_id/decision" -H "$auth_header" -H 'Content-Type: application/json' -d '{"decision":"approved","expected_target_version":1,"comment":"批准导出演示提案"}' >/dev/null
echo "[5/8] 提案和交付计划已形成: $proposal_id / $delivery_id"

run_id="$(request -X POST "$api_url/api/v1/projects/$project_id/agent-runs" -H "$auth_header" -H "Idempotency-Key: phase2-$project_id" -H 'Content-Type: application/json' -d '{"agent":"knowledge","input":{"objective":"总结可复用场景方案"}}' | json_id)"
request -N "$api_url/api/v1/agent-runs/$run_id/events" -H "$auth_header"
echo "[6/8] Agent 总控运行完成: $run_id"

knowledge_id="$(create_object knowledge-candidates '知识候选：经营报告自动化' '{"pattern":"证据检索 + 受控生成 + 人工审批","publication_status":"candidate"}')"
echo "[7/8] 知识候选已登记: $knowledge_id"

export_result="$(request -X POST "$api_url/api/v1/projects/$project_id/exports" -H "$auth_header" -H 'Content-Type: application/json' -d "{\"item_id\":\"$proposal_id\",\"format\":\"markdown\",\"citation_lines\":[\"来源：脱敏访谈\"]}")"
echo "[8/8] 提案已导出: $export_result"
echo "阶段二业务闭环演示成功。项目: $project_id"
