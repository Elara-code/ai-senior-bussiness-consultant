import base64
import hashlib
import hmac
import json
from typing import Annotated, Any, cast
from uuid import UUID

from fastapi import Depends, Header, HTTPException, Request

from consultant.adapters.storage.memory import InMemoryObjectStore
from consultant.application.ingestion import InMemoryDocumentCatalog
from consultant.application.projects import Identity, InMemoryProjectStore
from consultant.config import Settings


def encode_development_token(identity: Identity, secret: str) -> str:
    payload = {
        "organization_id": str(identity.organization_id),
        "user_id": str(identity.user_id),
        "display_name": identity.display_name,
    }
    encoded = _b64encode(json.dumps(payload, separators=(",", ":")).encode())
    signature = _b64encode(hmac.new(secret.encode(), encoded.encode(), hashlib.sha256).digest())
    return f"{encoded}.{signature}"


def decode_development_token(token: str, secret: str) -> Identity:
    try:
        encoded, signature = token.split(".", maxsplit=1)
        expected = _b64encode(hmac.new(secret.encode(), encoded.encode(), hashlib.sha256).digest())
        if not hmac.compare_digest(signature, expected):
            raise ValueError("invalid signature")
        data: dict[str, Any] = json.loads(_b64decode(encoded))
        return Identity(
            organization_id=UUID(data["organization_id"]),
            user_id=UUID(data["user_id"]),
            display_name=str(data["display_name"]),
        )
    except (KeyError, TypeError, ValueError, json.JSONDecodeError) as error:
        raise HTTPException(status_code=401, detail="Invalid development token") from error


def _b64encode(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).rstrip(b"=").decode()


def _b64decode(value: str) -> bytes:
    return base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))


def get_settings_from_request(request: Request) -> Settings:
    return cast(Settings, request.app.state.settings)


def get_project_store(request: Request) -> InMemoryProjectStore:
    return cast(InMemoryProjectStore, request.app.state.project_store)


def get_document_catalog(request: Request) -> InMemoryDocumentCatalog:
    return cast(InMemoryDocumentCatalog, request.app.state.document_catalog)


def get_object_store(request: Request) -> InMemoryObjectStore:
    return cast(InMemoryObjectStore, request.app.state.object_store)


RequestSettings = Annotated[Settings, Depends(get_settings_from_request)]


def get_identity(
    settings: RequestSettings,
    authorization: Annotated[str | None, Header()] = None,
) -> Identity:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Authentication required")
    if settings.auth_mode != "development":
        raise HTTPException(status_code=503, detail="OIDC identity provider is not configured")
    return decode_development_token(
        authorization.removeprefix("Bearer "), settings.development_auth_secret
    )


CurrentIdentity = Annotated[Identity, Depends(get_identity)]
ProjectStore = Annotated[InMemoryProjectStore, Depends(get_project_store)]
DocumentCatalog = Annotated[InMemoryDocumentCatalog, Depends(get_document_catalog)]
MemoryObjectStore = Annotated[InMemoryObjectStore, Depends(get_object_store)]
