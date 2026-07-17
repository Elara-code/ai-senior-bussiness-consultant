from datetime import UTC, datetime
from uuid import UUID, uuid4


def new_id() -> UUID:
    return uuid4()


def utc_now() -> datetime:
    return datetime.now(UTC)


class DomainError(Exception):
    """Base class for expected business failures."""


class InvalidStateTransition(DomainError):
    pass


class NotFound(DomainError):
    pass


class Forbidden(DomainError):
    pass


class Conflict(DomainError):
    pass


class ValidationFailure(DomainError):
    pass


class ExternalServiceFailure(DomainError):
    pass
