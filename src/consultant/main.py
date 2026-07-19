from fastapi import FastAPI

from consultant.adapters.storage.memory import InMemoryObjectStore
from consultant.api.errors import install_error_handlers
from consultant.api.v1.router import router as api_v1_router
from consultant.application.ingestion import InMemoryDocumentCatalog
from consultant.application.projects import InMemoryProjectStore
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
    application.include_router(api_v1_router)
    install_error_handlers(application)

    @application.get("/health", tags=["system"])
    async def health() -> dict[str, str]:
        return {"status": "ok", "service": active_settings.service_name}

    return application


app = create_app()
