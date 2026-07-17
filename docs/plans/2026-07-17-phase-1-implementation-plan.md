# AI 高级业务顾问 Agent 阶段一实施计划

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 在 3–4 周内交付一个可演示、可评测的内部 MVP，支持项目空间、文档入库、混合 RAG 与重排、SSE 对话、需求分析 Agent、方案设计 Agent，以及带引用的结构化成果。

**Architecture:** 采用模块化单体作为首期服务边界：FastAPI 提供 REST/SSE，LangGraph 编排 Agent，PostgreSQL/pgvector 保存业务和向量数据，Redis 保存事件流和任务协调，对象存储保存文档。所有外部能力通过 Protocol/Adapter 隔离，测试默认使用本地 Fake，不依赖真实模型和 Dify。

**Tech Stack:** Python 3.12、FastAPI、Pydantic v2、SQLAlchemy 2、Alembic、PostgreSQL 16 + pgvector、Redis、S3/MinIO、LangGraph、LangChain、pytest、Ruff、mypy、Docker Compose。

---

## 0. 阶段范围与完成定义

阶段一只实现：

- 单组织内部使用的项目空间与项目成员权限
- PDF、DOCX、Markdown、TXT 文档上传及异步解析
- 章节感知切分、Embedding、pgvector 与 PostgreSQL 全文混合检索
- 可替换重排器和严格的项目 ACL 过滤
- 需求分析 Agent 与场景/方案 Agent
- Agent 运行、检查点、SSE 断线续传和取消
- 结构化需求基线、场景矩阵、方案初稿与引用
- Fake 模型端到端演示及真实模型配置接口
- 自动化测试、离线最小评测集和 Docker Compose

阶段一不实现：完整 SSO、价值测算、提案导出、交付 Agent、知识脱敏发布、CRM 写回、Kubernetes 和 Dify 可视化工作流。Dify 仅保留适配接口，第二阶段接入。

完成定义：

1. 新环境执行一条命令可启动依赖和 API。
2. Fake 模式不使用外网即可跑通完整演示。
3. 两个项目之间的文档与检索结果严格隔离。
4. 需求分析及方案成果中的事实均可追溯到文档、版本和页码。
5. SSE 重连不重复执行 Agent，并能从事件 ID 续传。
6. 单元、集成、契约、权限及最小端到端测试通过。

## 1. 目标仓库结构

```text
.
├── .env.example
├── .github/workflows/ci.yml
├── Makefile
├── README.md
├── docker-compose.yml
├── pyproject.toml
├── alembic.ini
├── migrations/
│   ├── env.py
│   └── versions/
├── src/consultant/
│   ├── main.py
│   ├── config.py
│   ├── api/
│   │   ├── dependencies.py
│   │   ├── errors.py
│   │   └── v1/
│   │       ├── router.py
│   │       ├── projects.py
│   │       ├── documents.py
│   │       ├── retrieval.py
│   │       ├── agent_runs.py
│   │       └── deliverables.py
│   ├── domain/
│   │   ├── common.py
│   │   ├── projects.py
│   │   ├── documents.py
│   │   ├── retrieval.py
│   │   ├── agent_runs.py
│   │   └── deliverables.py
│   ├── application/
│   │   ├── projects.py
│   │   ├── ingestion.py
│   │   ├── retrieval.py
│   │   ├── agent_service.py
│   │   └── deliverables.py
│   ├── agents/
│   │   ├── state.py
│   │   ├── supervisor.py
│   │   ├── requirement_agent.py
│   │   ├── solution_agent.py
│   │   ├── nodes.py
│   │   └── prompts/
│   ├── ports/
│   │   ├── repositories.py
│   │   ├── model.py
│   │   ├── embeddings.py
│   │   ├── reranker.py
│   │   ├── object_store.py
│   │   └── event_store.py
│   └── adapters/
│       ├── db/
│       ├── llm/
│       ├── retrieval/
│       ├── storage/
│       └── events/
├── tests/
│   ├── unit/
│   ├── integration/
│   ├── contract/
│   ├── security/
│   ├── e2e/
│   └── fixtures/
└── evals/
    ├── datasets/
    └── run.py
```

## 2. 领域与接口契约摘要

完整契约见 [阶段一技术契约](2026-07-17-phase-1-technical-contracts.md)。实施中若契约变化，先修改契约和对应测试，再修改实现。

## 3. 任务拆解

### Task 1：建立 Python 工程与质量门禁

**Files:**

- Create: `pyproject.toml`
- Create: `src/consultant/__init__.py`
- Create: `src/consultant/main.py`
- Create: `src/consultant/config.py`
- Create: `tests/unit/test_health.py`
- Create: `.env.example`
- Create: `.gitignore`
- Create: `Makefile`

**Step 1: 写失败测试**

```python
from fastapi.testclient import TestClient
from consultant.main import create_app


def test_health_returns_service_status() -> None:
    response = TestClient(create_app()).get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "ai-business-consultant"}
```

**Step 2: 验证失败**

Run: `pytest tests/unit/test_health.py -v`

Expected: FAIL，提示 `consultant.main` 或 `create_app` 不存在。

**Step 3: 实现最小应用工厂**

在 `main.py` 创建 `create_app()`，注册 `/health`；在 `config.py` 使用 `pydantic-settings` 声明环境配置，不在导入阶段连接外部服务。

**Step 4: 增加质量配置**

在 `pyproject.toml` 配置 Ruff、mypy 和 pytest；锁定 Python 3.12，生产和开发依赖分组。

**Step 5: 验证**

Run: `ruff check . && mypy src && pytest tests/unit/test_health.py -v`

Expected: 全部 PASS。

**Step 6: Commit**

```bash
git add pyproject.toml src tests .env.example .gitignore Makefile
git commit -m "chore: bootstrap FastAPI service"
```

### Task 2：定义领域对象与错误语义

**Files:**

- Create: `src/consultant/domain/common.py`
- Create: `src/consultant/domain/projects.py`
- Create: `src/consultant/domain/documents.py`
- Create: `src/consultant/domain/retrieval.py`
- Create: `src/consultant/domain/agent_runs.py`
- Create: `src/consultant/domain/deliverables.py`
- Create: `src/consultant/api/errors.py`
- Test: `tests/unit/domain/test_models.py`

**Step 1: 写失败测试**

覆盖 UUID、UTC 时间、状态枚举、项目状态转换、DocumentVersion 不可变性、Citation 页码范围和 AgentRun 终态不可逆。

```python
def test_completed_run_cannot_return_to_running() -> None:
    run = AgentRunFixture.completed()
    with pytest.raises(InvalidStateTransition):
        run.transition_to(AgentRunStatus.RUNNING)
```

**Step 2: 验证失败**

Run: `pytest tests/unit/domain -v`

Expected: FAIL，领域类型尚未定义。

**Step 3: 实现领域类型**

使用 Pydantic DTO 处理 API 数据，核心领域状态转换使用显式方法；统一定义 `NotFound`、`Forbidden`、`Conflict`、`ValidationFailure` 和 `ExternalServiceFailure`。

**Step 4: 验证**

Run: `pytest tests/unit/domain -v`

Expected: PASS。

**Step 5: Commit**

```bash
git add src/consultant/domain src/consultant/api/errors.py tests/unit/domain
git commit -m "feat: define phase one domain model"
```

### Task 3：建立 PostgreSQL/pgvector 数据层与迁移

**Files:**

- Create: `alembic.ini`
- Create: `migrations/env.py`
- Create: `migrations/versions/0001_initial_schema.py`
- Create: `src/consultant/adapters/db/base.py`
- Create: `src/consultant/adapters/db/models.py`
- Create: `src/consultant/adapters/db/repositories.py`
- Create: `src/consultant/ports/repositories.py`
- Test: `tests/integration/db/test_migrations.py`
- Test: `tests/integration/db/test_project_scope.py`

**Step 1: 写迁移测试**

测试空数据库 upgrade 到 head 后存在 `vector` 扩展及契约中全部表、索引和外键；downgrade 后可重新 upgrade。

**Step 2: 写隔离失败测试**

创建两个项目和各自文档，使用项目范围 Repository 查询，断言不能返回另一个项目的数据。

**Step 3: 验证失败**

Run: `pytest tests/integration/db -v`

Expected: FAIL，数据库模型和迁移不存在。

**Step 4: 实现迁移与 Repository**

创建组织、用户、项目、成员、文档、版本、片段、运行、事件、交付物、版本、引用和审计表。所有项目资源使用复合索引 `(organization_id, project_id, ...)`。Embedding 列使用明确维度，维度由首期模型配置固定并在启动时校验。

**Step 5: 验证**

Run: `pytest tests/integration/db -v`

Expected: PASS。

**Step 6: Commit**

```bash
git add alembic.ini migrations src/consultant/adapters/db src/consultant/ports/repositories.py tests/integration/db
git commit -m "feat: add PostgreSQL persistence and migrations"
```

### Task 4：项目空间、临时身份与权限依赖

**Files:**

- Create: `src/consultant/api/dependencies.py`
- Create: `src/consultant/api/v1/router.py`
- Create: `src/consultant/api/v1/projects.py`
- Create: `src/consultant/application/projects.py`
- Modify: `src/consultant/main.py`
- Test: `tests/contract/test_projects_api.py`
- Test: `tests/security/test_project_authorization.py`

**Step 1: 写 API 契约测试**

覆盖创建项目、列表、详情、更新阶段、添加成员；验证 401、403、404、409 和 422 的 Problem Details 响应。

**Step 2: 写越权测试**

使用测试身份头模拟项目负责人、项目成员和非成员。非成员请求项目详情、文档和运行接口均应返回 404，避免泄露资源存在性。

**Step 3: 验证失败**

Run: `pytest tests/contract/test_projects_api.py tests/security/test_project_authorization.py -v`

Expected: FAIL。

**Step 4: 实现**

阶段一使用可替换 `IdentityProvider`，开发模式读取签名测试令牌，不允许直接信任任意用户 ID Header；生产配置未提供身份适配器时拒绝启动。

**Step 5: 验证并提交**

Run: `pytest tests/contract/test_projects_api.py tests/security/test_project_authorization.py -v`

```bash
git add src/consultant/api src/consultant/application/projects.py src/consultant/main.py tests/contract tests/security
git commit -m "feat: add project workspace and authorization"
```

### Task 5：对象存储与文档上传

**Files:**

- Create: `src/consultant/ports/object_store.py`
- Create: `src/consultant/adapters/storage/s3.py`
- Create: `src/consultant/adapters/storage/memory.py`
- Create: `src/consultant/api/v1/documents.py`
- Create: `src/consultant/application/ingestion.py`
- Test: `tests/unit/application/test_upload_document.py`
- Test: `tests/contract/test_documents_api.py`

**Step 1: 写失败测试**

覆盖允许的文件类型、大小限制、文件名清洗、流式哈希、重复上传、对象存储失败补偿和项目权限。

**Step 2: 验证失败**

Run: `pytest tests/unit/application/test_upload_document.py tests/contract/test_documents_api.py -v`

Expected: FAIL。

**Step 3: 实现上传事务**

API 以流方式读取文件并计算 SHA-256，不将大文件完整载入内存。先创建 `PENDING` 版本，再写对象存储和任务；失败时标记 `FAILED` 并清理孤立对象。返回 `202 Accepted`。

**Step 4: 验证并提交**

Run: `pytest tests/unit/application/test_upload_document.py tests/contract/test_documents_api.py -v`

```bash
git add src/consultant/ports/object_store.py src/consultant/adapters/storage src/consultant/api/v1/documents.py src/consultant/application/ingestion.py tests
git commit -m "feat: add secure document upload"
```

### Task 6：文档解析、切分与异步入库

**Files:**

- Create: `src/consultant/application/parsing.py`
- Create: `src/consultant/application/chunking.py`
- Create: `src/consultant/ports/embeddings.py`
- Create: `src/consultant/adapters/llm/fake_embeddings.py`
- Create: `src/consultant/adapters/llm/provider_embeddings.py`
- Create: `src/consultant/worker.py`
- Test: `tests/unit/application/test_chunking.py`
- Test: `tests/integration/ingestion/test_ingestion_pipeline.py`

**Step 1: 写切分测试**

Fixtures 覆盖 PDF 页码、DOCX 标题、Markdown 标题、表格、空白页、中英文混合和超长段落。断言每个片段有稳定 ID、来源页/章节、token 范围及内容哈希。

**Step 2: 写管道测试**

验证状态从 `PENDING → PARSING → EMBEDDING → READY`；任何阶段失败进入 `FAILED` 并记录可公开错误码，不记录文件内容。

**Step 3: 验证失败**

Run: `pytest tests/unit/application/test_chunking.py tests/integration/ingestion -v`

Expected: FAIL。

**Step 4: 实现**

解析器使用端口隔离具体库。切分优先尊重标题、段落、表格和页边界，再按 token 上限递归切分，并保留小幅重叠。重复内容按项目、文档版本和哈希幂等写入。

**Step 5: 验证并提交**

Run: `pytest tests/unit/application/test_chunking.py tests/integration/ingestion -v`

```bash
git add src/consultant/application src/consultant/ports/embeddings.py src/consultant/adapters/llm src/consultant/worker.py tests
git commit -m "feat: add asynchronous document ingestion"
```

### Task 7：混合检索、ACL 和重排

**Files:**

- Create: `src/consultant/ports/reranker.py`
- Create: `src/consultant/adapters/retrieval/hybrid.py`
- Create: `src/consultant/adapters/retrieval/rrf.py`
- Create: `src/consultant/adapters/retrieval/fake_reranker.py`
- Create: `src/consultant/application/retrieval.py`
- Create: `src/consultant/api/v1/retrieval.py`
- Test: `tests/unit/retrieval/test_rrf.py`
- Test: `tests/integration/retrieval/test_hybrid_retrieval.py`
- Test: `tests/security/test_retrieval_acl.py`

**Step 1: 写失败测试**

使用固定语料测试向量召回、全文召回、Reciprocal Rank Fusion、去重、重排和引用元数据。恶意请求即使传入其他项目 ID，也不得检索到未授权片段。

**Step 2: 验证失败**

Run: `pytest tests/unit/retrieval tests/integration/retrieval tests/security/test_retrieval_acl.py -v`

Expected: FAIL。

**Step 3: 实现检索链路**

权限范围由服务端身份和项目成员关系得出，绝不接受客户端传入的 ACL。先过滤组织、项目、文档状态和有效版本，再执行向量及全文召回；RRF 合并后取候选集交给重排器。

**Step 4: 验证并提交**

Run: `pytest tests/unit/retrieval tests/integration/retrieval tests/security/test_retrieval_acl.py -v`

```bash
git add src/consultant/ports/reranker.py src/consultant/adapters/retrieval src/consultant/application/retrieval.py src/consultant/api/v1/retrieval.py tests
git commit -m "feat: add project-scoped hybrid retrieval"
```

### Task 8：定义模型端口、结构化输出与 Fake 模型

**Files:**

- Create: `src/consultant/ports/model.py`
- Create: `src/consultant/adapters/llm/fake_model.py`
- Create: `src/consultant/adapters/llm/openai_compatible.py`
- Create: `src/consultant/agents/prompts/requirement_system.md`
- Create: `src/consultant/agents/prompts/solution_system.md`
- Test: `tests/unit/llm/test_structured_output.py`
- Test: `tests/contract/test_model_adapter.py`

**Step 1: 写失败测试**

测试结构化响应 Schema、超时、限流、无效 JSON、未知引用、令牌预算和重试语义。Fake 模型根据 Fixture 返回确定性结果。

**Step 2: 验证失败**

Run: `pytest tests/unit/llm tests/contract/test_model_adapter.py -v`

Expected: FAIL。

**Step 3: 实现端口与适配器**

模型端口不泄露具体供应商类型。OpenAI-compatible 适配器实现超时、有限重试、request ID、usage 记录和结构化输出校验；日志只保存哈希、长度、模型和用量。

**Step 4: 验证并提交**

Run: `pytest tests/unit/llm tests/contract/test_model_adapter.py -v`

```bash
git add src/consultant/ports/model.py src/consultant/adapters/llm src/consultant/agents/prompts tests
git commit -m "feat: add model abstraction and structured outputs"
```

### Task 9：实现 Agent 状态、专业 Agent 与质量门

**Files:**

- Create: `src/consultant/agents/state.py`
- Create: `src/consultant/agents/nodes.py`
- Create: `src/consultant/agents/requirement_agent.py`
- Create: `src/consultant/agents/solution_agent.py`
- Create: `src/consultant/agents/supervisor.py`
- Test: `tests/unit/agents/test_state.py`
- Test: `tests/unit/agents/test_requirement_agent.py`
- Test: `tests/unit/agents/test_solution_agent.py`

**Step 1: 写状态测试**

覆盖状态 Schema、最大步骤、证据去重、信息不足分支、质量门重试次数和终止条件。

**Step 2: 写 Agent 行为测试**

需求 Agent 必须区分事实、推断和假设；方案 Agent 只能消费已确认或明确标注状态的需求。引用不存在时质量门拒绝成果。

**Step 3: 验证失败**

Run: `pytest tests/unit/agents -v`

Expected: FAIL。

**Step 4: 实现 LangGraph**

节点包括：分类、计划、检索、信息缺口检查、专业分析、引用验证、质量审查和完成。所有循环有最大次数，状态只保存业务所需摘要与 ID，不无限累积消息。

**Step 5: 验证并提交**

Run: `pytest tests/unit/agents -v`

```bash
git add src/consultant/agents tests/unit/agents
git commit -m "feat: add requirement and solution agent graphs"
```

### Task 10：Agent Run 持久化、后台执行与 SSE

**Files:**

- Create: `src/consultant/ports/event_store.py`
- Create: `src/consultant/adapters/events/redis_stream.py`
- Create: `src/consultant/adapters/events/memory.py`
- Create: `src/consultant/application/agent_service.py`
- Create: `src/consultant/api/v1/agent_runs.py`
- Test: `tests/integration/agents/test_run_lifecycle.py`
- Test: `tests/contract/test_agent_sse.py`

**Step 1: 写生命周期测试**

覆盖创建、幂等重试、排队、运行、等待输入、完成、失败、取消和检查点恢复。

**Step 2: 写 SSE 测试**

验证事件格式、递增 ID、心跳、`Last-Event-ID` 续传、终态关闭和慢客户端处理；断线重连不得新建 AgentRun。

**Step 3: 验证失败**

Run: `pytest tests/integration/agents/test_run_lifecycle.py tests/contract/test_agent_sse.py -v`

Expected: FAIL。

**Step 4: 实现**

POST 创建任务返回 `202` 与 `run_id`；Worker 领取任务后执行图并发布业务事件。Redis Stream 保存短期事件，PostgreSQL 保存运行摘要与关键审计事件。SSE 发送注释心跳，响应头禁止代理缓冲。

**Step 5: 验证并提交**

Run: `pytest tests/integration/agents/test_run_lifecycle.py tests/contract/test_agent_sse.py -v`

```bash
git add src/consultant/ports/event_store.py src/consultant/adapters/events src/consultant/application/agent_service.py src/consultant/api/v1/agent_runs.py tests
git commit -m "feat: add durable agent runs and SSE streaming"
```

### Task 11：成果版本、引用与影响关系

**Files:**

- Create: `src/consultant/application/deliverables.py`
- Create: `src/consultant/api/v1/deliverables.py`
- Test: `tests/unit/application/test_deliverables.py`
- Test: `tests/contract/test_deliverables_api.py`

**Step 1: 写失败测试**

覆盖创建需求基线、场景矩阵和方案初稿；新修订不可覆盖旧版本；引用必须属于同一项目且指向 READY 文档版本；上游文档替换后成果标记 `STALE`。

**Step 2: 验证失败**

Run: `pytest tests/unit/application/test_deliverables.py tests/contract/test_deliverables_api.py -v`

Expected: FAIL。

**Step 3: 实现成果服务**

成果正文保存结构化 JSON 和渲染 Markdown。每个 Revision 为不可变快照，保存生成该成果的 AgentRun、提示词版本、模型标识、来源文档版本和引用关系。

**Step 4: 验证并提交**

Run: `pytest tests/unit/application/test_deliverables.py tests/contract/test_deliverables_api.py -v`

```bash
git add src/consultant/application/deliverables.py src/consultant/api/v1/deliverables.py tests
git commit -m "feat: add versioned deliverables and citations"
```

### Task 12：安全基线与审计

**Files:**

- Create: `src/consultant/application/audit.py`
- Create: `src/consultant/api/middleware.py`
- Create: `tests/security/test_prompt_injection.py`
- Create: `tests/security/test_sensitive_logging.py`
- Create: `tests/security/test_object_access.py`
- Modify: `src/consultant/main.py`

**Step 1: 写失败测试**

验证跨项目下载被拒绝、日志不出现原始文档和 API Key、上传材料中的指令不能改变系统规则、工具参数经过 Schema 校验、错误响应不包含堆栈和内部路径。

**Step 2: 验证失败**

Run: `pytest tests/security -v`

Expected: 至少新增测试 FAIL。

**Step 3: 实现安全策略**

加入请求 ID、安全响应头、统一错误映射、审计事件和日志脱敏。检索内容明确标记为不可信数据；任何文档内“忽略系统指令”等文本都只能作为材料，不能作为控制指令。

**Step 4: 验证并提交**

Run: `pytest tests/security -v`

```bash
git add src/consultant/application/audit.py src/consultant/api src/consultant/main.py tests/security
git commit -m "feat: enforce security and audit baseline"
```

### Task 13：评测集与质量门

**Files:**

- Create: `evals/datasets/phase1.jsonl`
- Create: `evals/run.py`
- Create: `evals/README.md`
- Create: `tests/unit/evals/test_metrics.py`

**Step 1: 创建最小数据集**

至少包含 20 个脱敏样例：事实问答、跨文档问答、资料不足、需求抽取、场景判断、冲突材料、提示注入和越权诱导。每例保存期望证据 ID、必需字段和禁止结论。

**Step 2: 写失败测试**

实现前先定义 Recall@K、MRR、引用准确率、引用覆盖率、Schema 通过率和禁用结论命中率的测试 Fixture。

**Step 3: 验证失败**

Run: `pytest tests/unit/evals -v`

Expected: FAIL。

**Step 4: 实现评测运行器**

支持 Fake 模式和真实模型模式；输出 JSON 与 Markdown 报告。首期门槛：引用准确率 ≥ 95%、引用覆盖率 ≥ 90%、结构化输出成功率 ≥ 98%、越权泄露 0、禁用结论命中 0。

**Step 5: 验证并提交**

Run: `pytest tests/unit/evals -v && python evals/run.py --provider fake`

```bash
git add evals tests/unit/evals
git commit -m "test: add phase one agent evaluation suite"
```

### Task 14：Docker Compose、本地演示与 CI

**Files:**

- Create: `docker-compose.yml`
- Create: `Dockerfile`
- Create: `.dockerignore`
- Create: `.github/workflows/ci.yml`
- Create: `scripts/demo.sh`
- Create: `tests/e2e/test_demo_flow.py`
- Modify: `README.md`

**Step 1: 写端到端失败测试**

Fake 模式创建项目、上传 Fixture、等待索引、创建需求分析 Run、消费 SSE、获取带引用成果，并尝试跨项目访问确认被拒绝。

**Step 2: 验证失败**

Run: `pytest tests/e2e/test_demo_flow.py -v`

Expected: FAIL，部署配置尚未完成。

**Step 3: 实现运行环境**

Compose 包含 API、Worker、PostgreSQL/pgvector、Redis 和 MinIO，并配置健康检查、非 root 用户、持久卷和资源边界。CI 执行 Ruff、mypy、单元、契约、集成、安全、Fake 评测和镜像构建。

**Step 4: 全量验证**

Run: `docker compose up -d --build`

Run: `pytest -v`

Run: `python evals/run.py --provider fake`

Run: `docker compose down`

Expected: 全部 PASS；无孤立容器；README 演示步骤可复现。

**Step 5: Commit**

```bash
git add Dockerfile docker-compose.yml .dockerignore .github scripts tests/e2e README.md
git commit -m "chore: add reproducible demo and CI"
```

## 4. 阶段一验收场景

### 场景 A：需求分析

顾问建立客户项目并上传访谈纪要、现状流程和产品资料。系统完成索引后，顾问启动需求分析。SSE 展示检索、分析和质量检查状态，最终生成结构化需求基线，所有事实均可打开原文来源。

### 场景 B：资料不足

材料只有笼统目标，没有业务量、系统边界或成功指标。Agent 不应补造数据，应生成信息缺口、访谈问题和当前可确认内容。

### 场景 C：方案设计

基于已生成的需求基线，Agent 输出候选场景、优先级、业务流程、技术组件、集成边界、实施阶段、风险及待确认项。方案不得承诺未在材料或用户输入中确认的产品能力。

### 场景 D：权限隔离

用户属于项目 A，不属于项目 B。无论 REST 参数、检索查询、文档引用、对象下载还是 Agent 工具调用，都无法获得项目 B 的存在信息或内容。

### 场景 E：断线恢复

Agent 运行期间关闭 SSE，再携带最后事件 ID 重连。客户端收到缺失事件，任务没有重复启动，最终成果只有一个有效修订版本。

## 5. 研发顺序与并行建议

Task 1–4 必须顺序完成以建立工程、领域、数据和权限基础。Task 5–7 为文档/RAG 主链；Task 8–10 为模型/Agent 主链，可在 Task 4 后由两个开发小组并行。Task 11 依赖两条主链汇合。Task 12–14 在功能完成后收口，但安全测试和评测 Fixture 应从第一周持续积累。

## 6. 进入实施前的默认决策

如企业尚未明确基础设施，阶段一采用以下默认值：

- 模型：OpenAI-compatible 接口 + Fake Provider；具体模型通过环境变量配置。
- Embedding 维度：由选定模型固定，迁移前不得在同一索引混用维度。
- 重排：可插拔 Cross-Encoder 端口；Fake 实现用于测试。
- 身份：可替换 IdentityProvider；本地使用签名开发令牌，禁止任意 Header 冒充。
- 任务：独立 Worker + Redis 协调；AgentRun 状态以 PostgreSQL 为准。
- 文件：S3-compatible；本地 MinIO。
- API：版本前缀 `/api/v1`，错误采用 RFC 9457 Problem Details。

这些默认值都由端口隔离，不阻碍后续接入企业 SSO、私有模型、Dify、Qdrant/Milvus 或企业对象存储。
