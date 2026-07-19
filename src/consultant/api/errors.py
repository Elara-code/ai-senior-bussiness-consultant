from dataclasses import dataclass

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from consultant.domain.common import (
    Conflict,
    DomainError,
    ExternalServiceFailure,
    Forbidden,
    NotFound,
    ValidationFailure,
)


@dataclass(frozen=True, slots=True)
class ProblemSpec:
    status: int
    code: str
    title: str


_PROBLEMS: dict[type[DomainError], ProblemSpec] = {
    NotFound: ProblemSpec(404, "NOT_FOUND", "Resource not found"),
    Forbidden: ProblemSpec(403, "FORBIDDEN", "Operation forbidden"),
    Conflict: ProblemSpec(409, "CONFLICT", "Resource conflict"),
    ValidationFailure: ProblemSpec(422, "VALIDATION_FAILED", "Validation failed"),
    ExternalServiceFailure: ProblemSpec(503, "EXTERNAL_SERVICE_FAILED", "Service unavailable"),
}


def problem_for(error: DomainError) -> ProblemSpec:
    for error_type, problem in _PROBLEMS.items():
        if isinstance(error, error_type):
            return problem
    return ProblemSpec(409, "DOMAIN_ERROR", "Domain rule rejected the operation")


def install_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(DomainError)
    async def handle_domain_error(request: Request, error: DomainError) -> JSONResponse:
        problem = problem_for(error)
        return JSONResponse(
            status_code=problem.status,
            media_type="application/problem+json",
            content={
                "type": f"https://internal.example/problems/{problem.code.lower()}",
                "title": problem.title,
                "status": problem.status,
                "detail": str(error),
                "instance": request.url.path,
                "request_id": getattr(request.state, "request_id", None),
                "code": problem.code,
            },
        )
