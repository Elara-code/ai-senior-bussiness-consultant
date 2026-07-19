# AI 高级业务顾问 Agent

面向企业内部售前、咨询与项目交付团队的多智能体业务顾问平台。

阶段一 MVP 已实现，相关设计与实施依据：

- [产品与系统设计蓝图](docs/plans/2026-07-17-ai-senior-business-consultant-design.md)
- [阶段一实施计划](docs/plans/2026-07-17-phase-1-implementation-plan.md)
- [阶段一技术契约](docs/plans/2026-07-17-phase-1-technical-contracts.md)

## 建设目标

- 辅助客户需求分析、AI 场景识别与解决方案设计
- 生成有事实依据、可追溯的项目提案和业务文档
- 支持需求细化、培训、上线和验收等交付活动
- 将项目实践脱敏并沉淀为可复用的企业知识资产

## 推荐技术方向

FastAPI、SSE、LangGraph、LangChain、Dify、PostgreSQL、pgvector、Redis、对象存储、混合检索与重排。

## 已实现能力

- 客户项目空间、成员角色和项目级数据隔离
- PDF、DOCX、Markdown、TXT 上传、解析、切分和向量化
- 向量与关键词混合检索、RRF 合并和重排
- 需求分析 Agent、方案设计 Agent 和引用质量门
- AgentRun 生命周期、Redis Stream 适配与 SSE 事件
- 不可变成果修订、证据引用和上游变更影响
- 安全响应头、请求审计、敏感日志脱敏和提示注入隔离
- 20 条离线评测集、Fake 模式演示和 CI

## 本地运行

要求安装 Docker Desktop。

```bash
cp .env.example .env
docker compose up -d --build
curl http://localhost:8000/health
./scripts/demo.sh
```

演示脚本会建立项目、上传访谈材料、完成索引、运行需求分析 Agent，并通过 SSE 输出运行事件。Compose 环境使用确定性的离线 Fake 模型，不需要外部模型密钥。

停止服务：

```bash
docker compose down
```

如需同时删除本地演示数据：

```bash
docker compose down -v
```

## 开发验证

```bash
python3.12 -m venv .venv
.venv/bin/pip install -e '.[dev]'
.venv/bin/ruff check .
.venv/bin/mypy src evals
.venv/bin/pytest -q
.venv/bin/python -m evals.run --provider fake
```

真实模型通过 OpenAI-compatible 适配器接入。Dify 工作流、企业 SSO 和外部系统写回属于后续阶段；核心权限、业务状态和审批不会交由 Dify 保存。
