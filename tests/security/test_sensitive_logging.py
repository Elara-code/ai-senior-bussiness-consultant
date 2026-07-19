from consultant.api.middleware import redact_sensitive


def test_sensitive_values_are_redacted() -> None:
    message = "Authorization: Bearer token-123 api_key=secret-456 password=hunter2"
    redacted = redact_sensitive(message)

    assert "token-123" not in redacted
    assert "secret-456" not in redacted
    assert "hunter2" not in redacted
    assert redacted.count("[REDACTED]") == 3
