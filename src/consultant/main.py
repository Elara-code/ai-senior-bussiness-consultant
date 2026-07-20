from fastapi import FastAPI

from consultant.adapters.events.memory import InMemoryEventStore
from consultant.adapters.llm.fake_embeddings import FakeEmbeddingProvider
from consultant.adapters.retrieval.fake_reranker import TokenOverlapReranker
from consultant.adapters.storage.memory import InMemoryObjectStore
from consultant.api.errors import install_error_handlers
from consultant.api.middleware import install_security_middleware
from consultant.api.v1.router import router as api_v1_router
from consultant.application.agent_service import AgentRunService
from consultant.application.audit import InMemoryAuditLog
from consultant.application.business_loop import InMemoryBusinessObjectRepository
from consultant.application.deliverables import InMemoryDeliverableStore
from consultant.application.demo import DemoAgentExecutor
from consultant.application.ingestion import InMemoryDocumentCatalog
from consultant.application.pipeline import DocumentPipeline
from consultant.application.projects import InMemoryProjectStore
from consultant.application.retrieval import RetrievalService
from consultant.config import Settings, get_settings


def create_app(settings: Settings | None = None) -> FastAPI:
    active_settings = settings or get_settings()
    application = FastAPI(
        title="AI Senior Business Consultant API",
        version="0.1.0",
    )
    application.state.settings = active_settings
    application.state.project_store = InMemoryProjectStore()
    application.state.document_catalog = InMemoryDocumentCatalog()
    application.state.object_store = InMemoryObjectStore()
    application.state.embedding_provider = FakeEmbeddingProvider(dimensions=16)
    application.state.reranker = TokenOverlapReranker()
    application.state.document_pipeline = DocumentPipeline(
        catalog=application.state.document_catalog,
        object_store=application.state.object_store,
        embeddings=application.state.embedding_provider,
    )
    application.state.demo_agent_executor = DemoAgentExecutor(
        RetrievalService(
            projects=application.state.project_store,
            catalog=application.state.document_catalog,
            embeddings=application.state.embedding_provider,
            reranker=application.state.reranker,
        )
    )
    application.state.agent_run_service = AgentRunService(
        projects=application.state.project_store,
        events=InMemoryEventStore(),
    )
    application.state.deliverable_store = InMemoryDeliverableStore()
    application.state.business_object_repository = InMemoryBusinessObjectRepository()
    application.state.audit_log = InMemoryAuditLog()
    application.include_router(api_v1_router)
    install_error_handlers(application)
    install_security_middleware(application)

    @application.get("/health", tags=["system"])
    async def health() -> dict[str, str]:
        return {"status": "ok", "service": active_settings.service_name}

    return application


app = create_app()
