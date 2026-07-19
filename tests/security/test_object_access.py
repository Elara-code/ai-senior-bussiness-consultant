from uuid import uuid4

from fastapi.testclient import TestClient

from consultant.api.dependencies import encode_development_token
from consultant.application.projects import Identity
from consultant.config import Settings
from consultant.main import create_app

SECRET = "test-development-secret"


def test_security_headers_request_id_and_audit_are_applied() -> None:
    identity = Identity(organization_id=uuid4(), user_id=uuid4(), display_name="User")
    app = create_app(Settings(environment="test", development_auth_secret=SECRET))
    token = encode_development_token(identity, SECRET)
    response = TestClient(app).get(
        "/api/v1/projects",
        headers={"Authorization": f"Bearer {token}", "X-Request-ID": "request-test-1"},
    )

    assert response.status_code == 200
    assert response.headers["X-Request-ID"] == "request-test-1"
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers["X-Frame-Options"] == "DENY"
    assert app.state.audit_log.events[-1].request_id == "request-test-1"


def test_error_response_does_not_expose_internal_stack_or_paths() -> None:
    response = TestClient(create_app()).get("/api/v1/projects")

    assert response.status_code == 401
    assert "/Users/" not in response.text
    assert "Traceback" not in response.text
