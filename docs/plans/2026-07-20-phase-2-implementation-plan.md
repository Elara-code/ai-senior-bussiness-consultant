# AI 高级业务顾问 Agent 阶段二实施计划

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 交付一个内部顾问团队可试用的业务闭环 Beta，通过 Web 工作台完成从材料导入、需求与方案分析、价值评估、审批、提案、交付计划到知识候选的全过程。

**Architecture:** 保持 FastAPI 模块化单体作为权威业务后端，使用 LangGraph 编排总控及专业 Agent，以版本化领域对象和不可变审批快照承载业务状态；新增 Next.js 工作台通过 REST/SSE 访问后端。Dify 仅通过受控适配器执行低风险可配置流程，Fake 实现保证离线测试和演示。

**Tech Stack:** Python 3.12、FastAPI、Pydantic v2、SQLAlchemy 2、Alembic、PostgreSQL/pgvector、Redis、MinIO、LangGraph、LangChain、Next.js、TypeScript、React、Tailwind CSS、Vitest、Playwright、pytest、Docker Compose。

---

## 0. 完成定义

1. 顾问可以只使用浏览器完成业务闭环演示。
2. 需求、场景、价值测算、提案、交付计划和知识候选均为版本化业务对象。
3. 需求基线、商业测算、对客提案和知识发布必须经过不可变快照审批。
4. AgentRun 支持业务步骤事件、等待审批、失败步骤重试和 SSE 续传。
5. Dify 调用被版本化、可审计、可超时、可降级，并提供离线 Fake。
6. 成果可导出为 Markdown、DOCX 和 PDF，草稿带明确标识。
7. 后端、前端、端到端和安全测试通过，关键事实引用覆盖率不低于 95%。

## 1. 实施顺序

任务沿用阶段一编号，从 Task 15 开始。每个任务遵循 TDD：先写失败测试，再实现最小行为，随后执行局部和相关回归测试，最后独立提交。

### Task 15：阶段二领域对象与状态规则

**Files:**

- Create: `src/consultant/domain/business_loop.py`
- Create: `tests/unit/domain/test_business_loop.py`
- Modify: `src/consultant/domain/__init__.py`

**Step 1: 写失败测试**

覆盖 `RequirementBaseline`、`ScenarioAssessment`、`BusinessCase`、`Proposal`、`DeliveryPlan`、`Approval`、`KnowledgeCandidate` 和 `WorkflowExecution` 的创建、状态转换和不可变规则。

```python
def test_approved_snapshot_is_immutable() -> None:
    approval = ApprovalFixture.approved()
    with pytest.raises(InvalidStateTransition):
        approval.replace_snapshot({"title": "changed"})


def test_business_case_rejects_untraceable_parameter() -> None:
    with pytest.raises(ValidationError):
        BusinessParameter(name="人工成本", value=1000, source=None)
```

**Step 2: 验证失败**

Run: `.venv/bin/pytest tests/unit/domain/test_business_loop.py -v`  
Expected: FAIL，模块或领域类型不存在。

**Step 3: 实现最小领域模型**

统一成果状态为 `draft → awaiting_approval → approved/rejected`，发布状态与审批状态分离。所有对象携带 `organization_id`、`project_id`、`version`、`created_at` 和 `updated_at`。结构化结论复用统一的 `EvidenceStatement`：

```python
class EvidenceStatement(BaseModel):
    text: str
    kind: Literal["fact", "inference", "assumption"]
    citation_ids: list[UUID] = Field(default_factory=list)

    @model_validator(mode="after")
    def require_fact_citation(self) -> Self:
        if self.kind == "fact" and not self.citation_ids:
            raise ValueError("facts require at least one citation")
        return self
```

**Step 4: 验证并提交**

Run: `.venv/bin/pytest tests/unit/domain/test_business_loop.py -v`  
Expected: PASS。

Commit: `feat: define phase two business domain`

### Task 16：数据库迁移与持久化映射

**Files:**

- Create: `migrations/versions/0002_phase_two_business_loop.py`
- Modify: `src/consultant/adapters/db/models.py`
- Create: `tests/unit/db/test_phase_two_metadata.py`
- Modify: `tests/integration/db/test_postgres.py`

**Step 1: 写失败测试**

断言新表、组织/项目复合外键、版本唯一约束、审批快照 JSONB 和常用查询索引存在；集成测试执行迁移并保存、读取一条完整业务链。

**Step 2: 验证失败**

Run: `.venv/bin/pytest tests/unit/db/test_phase_two_metadata.py -v`  
Expected: FAIL，新表不存在。

**Step 3: 实现迁移与 Row 映射**

创建：`requirement_baselines`、`scenario_assessments`、`business_cases`、`proposals`、`delivery_plans`、`approvals`、`knowledge_candidates`、`workflow_executions`。结构化正文使用 JSONB，检索与列表所需字段使用普通列和复合索引。

**Step 4: 验证并提交**

Run: `.venv/bin/pytest tests/unit/db/test_phase_two_metadata.py tests/integration/db/test_postgres.py -v`  
Expected: PASS。

Commit: `feat: persist phase two business objects`

### Task 17：业务对象仓储与应用服务

**Files:**

- Create: `src/consultant/ports/business_loop.py`
- Create: `src/consultant/application/business_loop.py`
- Create: `src/consultant/adapters/db/business_loop_repository.py`
- Create: `tests/unit/application/test_business_loop.py`
- Create: `tests/security/test_business_loop_acl.py`

**Step 1: 写失败测试**

覆盖创建修订、读取最新版、列出项目对象、乐观锁冲突和跨项目拒绝访问。

```python
async def test_update_rejects_stale_version(service: BusinessLoopService) -> None:
    item = await service.create_requirement(...)
    await service.revise_requirement(item.id, expected_version=1, payload={...})
    with pytest.raises(Conflict):
        await service.revise_requirement(item.id, expected_version=1, payload={...})
```

**Step 2: 实现仓储 Protocol、内存实现和 SQLAlchemy 实现**

所有方法显式接收 `organization_id` 和 `project_id`，应用服务先验证项目成员权限。修改通过 `expected_version` 执行乐观锁，禁止静默覆盖。

**Step 3: 验证并提交**

Run: `.venv/bin/pytest tests/unit/application/test_business_loop.py tests/security/test_business_loop_acl.py -v`  
Expected: PASS。

Commit: `feat: add versioned business loop services`

### Task 18：阶段二业务 API

**Files:**

- Create: `src/consultant/api/v1/requirements.py`
- Create: `src/consultant/api/v1/scenarios.py`
- Create: `src/consultant/api/v1/business_cases.py`
- Create: `src/consultant/api/v1/proposals.py`
- Create: `src/consultant/api/v1/delivery_plans.py`
- Modify: `src/consultant/api/v1/router.py`
- Modify: `src/consultant/api/dependencies.py`
- Create: `tests/contract/test_business_loop_api.py`

**Step 1: 写 API 契约测试**

覆盖项目内列表、详情、创建修订、`If-Match` 乐观锁、错误语义、组织与项目隔离。

**Step 2: 实现路由**

所有 URL 以 `/api/v1/projects/{project_id}/...` 为项目边界。写操作返回最新版本和 ETag；版本冲突返回 `409`，无权限资源继续使用 `404` 防止枚举。

**Step 3: 验证并提交**

Run: `.venv/bin/pytest tests/contract/test_business_loop_api.py -v`  
Expected: PASS。

Commit: `feat: expose phase two business APIs`

### Task 19：审批工作流与上游变更影响

**Files:**

- Create: `src/consultant/application/approvals.py`
- Create: `src/consultant/api/v1/approvals.py`
- Modify: `src/consultant/application/deliverables.py`
- Modify: `src/consultant/api/v1/router.py`
- Create: `tests/unit/application/test_approvals.py`
- Create: `tests/contract/test_approvals_api.py`

**Step 1: 写失败测试**

测试提交审批时保存不可变快照，只有 reviewer/owner 可批准或退回；批准后修改上游对象会将依赖对象标记为 `stale`，原审批记录保持不变。

**Step 2: 实现审批服务与路由**

提供提交、批准、退回和历史记录接口。审批动作要求 `expected_target_version`；目标版本变化时返回冲突。

**Step 3: 验证并提交**

Run: `.venv/bin/pytest tests/unit/application/test_approvals.py tests/contract/test_approvals_api.py -v`  
Expected: PASS。

Commit: `feat: add immutable approval workflow`

### Task 20：总控 Agent 计划与人工审批中断

**Files:**

- Modify: `src/consultant/agents/state.py`
- Modify: `src/consultant/agents/supervisor.py`
- Modify: `src/consultant/application/agent_service.py`
- Create: `src/consultant/agents/planning.py`
- Create: `tests/unit/agents/test_supervisor_planning.py`
- Modify: `tests/integration/agents/test_run_lifecycle.py`

**Step 1: 写失败测试**

覆盖总控根据项目阶段生成有依赖的步骤计划、在关键成果后进入 `awaiting_approval`、批准后恢复、失败后从检查点重试。

**Step 2: 扩展 AgentRun 状态和事件**

新增 `AWAITING_APPROVAL` 和业务事件：`plan.created`、`step.started`、`step.completed`、`approval.required`、`run.resumed`。检查点只保存业务状态和工具结果摘要，不保存私有思维链。

**Step 3: 验证并提交**

Run: `.venv/bin/pytest tests/unit/agents/test_supervisor_planning.py tests/integration/agents/test_run_lifecycle.py -v`  
Expected: PASS。

Commit: `feat: orchestrate resumable consultant plans`

### Task 21：价值与风险 Agent

**Files:**

- Create: `src/consultant/agents/value_risk_agent.py`
- Create: `src/consultant/agents/prompts/value_risk_system.md`
- Modify: `src/consultant/agents/schemas.py`
- Create: `tests/unit/agents/test_value_risk_agent.py`

**Step 1: 写失败测试**

测试成本收益公式、区间、参数来源、风险台账和资料不足时的拒绝编造。关键商业参数无来源时质量门必须失败。

**Step 2: 实现结构化输出与确定性计算**

模型只提取参数和解释，金额计算由 Python 纯函数完成。输出包含基准、保守、乐观三种情景和每项参数的引用或人工确认状态。

**Step 3: 验证并提交**

Run: `.venv/bin/pytest tests/unit/agents/test_value_risk_agent.py -v`  
Expected: PASS。

Commit: `feat: add evidence based value risk agent`

### Task 22：提案、交付和知识 Agent

**Files:**

- Create: `src/consultant/agents/proposal_agent.py`
- Create: `src/consultant/agents/delivery_agent.py`
- Create: `src/consultant/agents/knowledge_agent.py`
- Create: `src/consultant/agents/prompts/proposal_system.md`
- Create: `src/consultant/agents/prompts/delivery_system.md`
- Create: `src/consultant/agents/prompts/knowledge_system.md`
- Modify: `src/consultant/agents/schemas.py`
- Create: `tests/unit/agents/test_phase_two_agents.py`
- Create: `tests/security/test_knowledge_redaction.py`

**Step 1: 写失败测试**

提案 Agent 不得新增未批准承诺；交付 Agent 必须保持需求到验收标准的追溯；知识 Agent 必须移除客户名称、联系人、账号及项目专属数字，并只接受已审批输入。

**Step 2: 实现三个专业 Agent 与质量门**

输出继续遵守事实、推断、假设、引用和质量问题协议。脱敏规则先采用确定性模式匹配和允许字段映射，模型仅辅助发现候选。

**Step 3: 验证并提交**

Run: `.venv/bin/pytest tests/unit/agents/test_phase_two_agents.py tests/security/test_knowledge_redaction.py -v`  
Expected: PASS。

Commit: `feat: add proposal delivery knowledge agents`

### Task 23：Dify 受控适配器

**Files:**

- Create: `src/consultant/ports/workflow.py`
- Create: `src/consultant/adapters/workflows/dify.py`
- Create: `src/consultant/adapters/workflows/fake.py`
- Create: `src/consultant/adapters/workflows/__init__.py`
- Modify: `src/consultant/config.py`
- Modify: `.env.example`
- Create: `tests/contract/test_dify_adapter.py`
- Create: `tests/integration/workflows/test_workflow_fallback.py`

**Step 1: 写失败测试**

使用 `httpx.MockTransport` 覆盖认证头、版本化 JSON 输入输出、超时、非成功响应、幂等键和敏感日志脱敏；集成测试验证摘要回退与提案稍后重试策略。

**Step 2: 实现 Protocol 和适配器**

```python
class WorkflowRunner(Protocol):
    async def run(
        self, *, workflow: WorkflowRef, input: dict[str, Any], idempotency_key: str
    ) -> WorkflowResult: ...
```

密钥仅从环境读取。应用服务持久化 `WorkflowExecution`，Dify 不直接访问项目数据库。

**Step 3: 验证并提交**

Run: `.venv/bin/pytest tests/contract/test_dify_adapter.py tests/integration/workflows -v`  
Expected: PASS。

Commit: `feat: integrate controlled Dify workflows`

### Task 24：成果导出服务

**Files:**

- Create: `src/consultant/ports/exporter.py`
- Create: `src/consultant/application/exports.py`
- Create: `src/consultant/adapters/export/markdown.py`
- Create: `src/consultant/adapters/export/docx.py`
- Create: `src/consultant/adapters/export/pdf.py`
- Create: `src/consultant/api/v1/exports.py`
- Modify: `src/consultant/api/v1/router.py`
- Create: `tests/unit/application/test_exports.py`
- Create: `tests/contract/test_exports_api.py`

**Step 1: 写失败测试**

验证三种格式、文件名净化、审批信息、引用附录、草稿水印和对象存储元数据。PDF/DOCX 测试读取生成文件并检查关键文本，不只断言文件存在。

**Step 2: 实现导出适配器和异步 API**

导出基于指定不可变修订，写入 MinIO 后返回短期下载引用。未审批成果始终带“草稿/未经审批”标识。

**Step 3: 验证并提交**

Run: `.venv/bin/pytest tests/unit/application/test_exports.py tests/contract/test_exports_api.py -v`  
Expected: PASS。

Commit: `feat: export governed consultant deliverables`

### Task 25：Next.js 工作台基础与项目看板

**Files:**

- Create: `web/package.json`
- Create: `web/next.config.ts`
- Create: `web/tsconfig.json`
- Create: `web/app/layout.tsx`
- Create: `web/app/page.tsx`
- Create: `web/app/globals.css`
- Create: `web/lib/api.ts`
- Create: `web/lib/auth.ts`
- Create: `web/components/app-shell.tsx`
- Create: `web/components/project-card.tsx`
- Create: `web/tests/project-dashboard.test.tsx`

**Step 1: 写失败的组件测试**

测试加载态、空状态、错误态、项目卡片、阶段标签和键盘可访问导航。

**Step 2: 实现视觉基础与 API 客户端**

使用中文业务文案、清晰的信息层级和响应式布局。开发模式令牌通过服务端边界生成或注入，禁止写入浏览器源码仓库。

**Step 3: 验证并提交**

Run: `cd web && npm test && npm run lint && npm run build`  
Expected: PASS。

Commit: `feat: add consultant project workspace`

### Task 26：项目业务页面、编辑与审批 UI

**Files:**

- Create: `web/app/projects/[projectId]/layout.tsx`
- Create: `web/app/projects/[projectId]/page.tsx`
- Create: `web/app/projects/[projectId]/materials/page.tsx`
- Create: `web/app/projects/[projectId]/requirements/page.tsx`
- Create: `web/app/projects/[projectId]/solution/page.tsx`
- Create: `web/app/projects/[projectId]/approvals/page.tsx`
- Create: `web/app/projects/[projectId]/delivery/page.tsx`
- Create: `web/components/versioned-editor.tsx`
- Create: `web/components/citation-drawer.tsx`
- Create: `web/components/approval-panel.tsx`
- Create: `web/tests/business-pages.test.tsx`

**Step 1: 写失败测试**

覆盖结构化编辑、Markdown 编辑、引用抽屉、版本冲突提示、提交审批、批准/退回确认和 stale 标记。

**Step 2: 实现页面和组件**

所有编辑提交携带服务端版本；收到 `409` 时保留用户草稿并显示差异处理入口。破坏性或对外动作必须二次确认。

**Step 3: 验证并提交**

Run: `cd web && npm test && npm run build`  
Expected: PASS。

Commit: `feat: add governed consultant workbench pages`

### Task 27：Agent 运行中心与 SSE 恢复

**Files:**

- Create: `web/app/projects/[projectId]/runs/page.tsx`
- Create: `web/hooks/use-agent-events.ts`
- Create: `web/components/run-timeline.tsx`
- Create: `web/components/run-controls.tsx`
- Modify: `src/consultant/api/v1/agent_runs.py`
- Create: `web/tests/agent-run-center.test.tsx`
- Modify: `tests/contract/test_agent_sse.py`

**Step 1: 写失败测试**

前端测试模拟连接中断和 `Last-Event-ID` 恢复；后端测试业务事件顺序、等待审批、取消和重试接口。

**Step 2: 实现运行中心**

页面展示计划、步骤、证据摘要和可操作错误。关闭页面不取消任务；恢复时去重事件。审批节点跳转到对应成果快照。

**Step 3: 验证并提交**

Run: `.venv/bin/pytest tests/contract/test_agent_sse.py -v && cd web && npm test`  
Expected: PASS。

Commit: `feat: stream resumable agent progress in workbench`

### Task 28：Compose 集成与浏览器端到端闭环

**Files:**

- Modify: `docker-compose.yml`
- Create: `web/Dockerfile`
- Create: `web/playwright.config.ts`
- Create: `web/e2e/business-loop.spec.ts`
- Create: `scripts/demo-phase2.sh`
- Modify: `README.md`

**Step 1: 写端到端测试**

在 Fake 模式下通过浏览器：创建项目、上传材料、启动总控、确认需求、生成方案和价值分析、审批、生成提案和交付计划、创建知识候选、导出成果。

**Step 2: 集成 Web 服务与健康检查**

Compose 新增 `web` 服务并将后端地址作为运行时配置。`demo-phase2.sh` 使用每个项目唯一的幂等键，可重复运行且在 HTTP 失败时输出服务端错误正文。

**Step 3: 验证并提交**

Run: `docker compose up -d --build`  
Run: `cd web && npx playwright test`  
Run: `./scripts/demo-phase2.sh`  
Expected: 全部完成，浏览器和脚本均形成业务闭环。

Commit: `feat: deliver phase two browser demo`

### Task 29：阶段二评测、安全与质量门禁

**Files:**

- Create: `evals/datasets/phase2.jsonl`
- Modify: `evals/metrics.py`
- Modify: `evals/run.py`
- Create: `tests/unit/evals/test_phase_two_metrics.py`
- Create: `tests/security/test_phase_two_data_boundaries.py`
- Modify: `.github/workflows/ci.yml`

**Step 1: 建立评测集和门槛测试**

至少覆盖需求、方案、价值、提案、交付和脱敏六类样本。指标包括引用覆盖、公式正确、约束覆盖、新增承诺、需求到验收追溯和敏感信息泄露。

**Step 2: 扩展 CI**

CI 执行后端 Ruff/mypy/pytest、前端 lint/test/build、Fake 离线评测和数据库迁移检查。生产凭据不得用于 CI。

**Step 3: 全量验证并提交**

Run: `.venv/bin/ruff check .`  
Run: `.venv/bin/mypy src evals`  
Run: `.venv/bin/pytest -q`  
Run: `.venv/bin/python -m evals.run --provider fake --dataset phase2`  
Run: `cd web && npm run lint && npm test && npm run build`  
Expected: 全部 PASS，引用覆盖率 ≥ 0.95，敏感泄露和跨项目越权为 0。

Commit: `test: enforce phase two quality gates`

### Task 30：试点验收包与运行手册

**Files:**

- Create: `docs/runbooks/phase-2-local-and-pilot.md`
- Create: `docs/acceptance/phase-2-checklist.md`
- Modify: `README.md`

**Step 1: 编写运行与故障恢复手册**

记录启动、配置真实模型、配置 Dify、Fake/真实模式切换、备份、失败重试、常见 409/401/超时问题和安全注意事项，不写入任何真实密钥。

**Step 2: 编写试点验收清单**

选择一个已脱敏历史项目，记录初稿耗时、引用覆盖、顾问修改比例、审批完整性、导出质量和问题清单。

**Step 3: 最终验证并提交**

Run: `docker compose config`  
Run: `./scripts/demo-phase2.sh`  
Run: 全量后端、前端和评测命令。  
Expected: 阶段二所有退出标准均有可复核证据。

Commit: `docs: add phase two pilot runbook`

## 2. 批次与检查点

- **批次 A（Task 15–19）**：领域对象、持久化、API 和审批。
- **批次 B（Task 20–24）**：总控与专业 Agent、Dify、导出。
- **批次 C（Task 25–27）**：Next.js 工作台和实时运行中心。
- **批次 D（Task 28–30）**：端到端集成、质量门禁和试点验收。

每个批次结束后执行全量回归并检查工作树，只提交该批次范围内的变更。若契约发生变化，先更新本计划或阶段二设计，再修改实现。

