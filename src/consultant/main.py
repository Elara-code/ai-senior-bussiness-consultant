from fastapi import FastAPI

from consultant.config import Settings, get_settings


def create_app(settings: Settings | None = None) -> FastAPI:
    active_settings = settings or get_settings()
    application = FastAPI(
        title="AI Senior Business Consultant API",
        version="0.1.0",
    )

    @application.get("/health", tags=["system"])
    async def health() -> dict[str, str]:
        return {"status": "ok", "service": active_settings.service_name}

    return application


app = create_app()
