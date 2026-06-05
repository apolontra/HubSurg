"""Tradução de erros de domínio para respostas HTTP."""

from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.domain.errors import DomainError, EntityNotFound, InvalidState

_STATUS_BY_ERROR: list[tuple[type[DomainError], int]] = [
    (EntityNotFound, 404),
    (InvalidState, 409),
    (DomainError, 400),
]


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(DomainError)
    async def _handle_domain_error(_: Request, exc: DomainError) -> JSONResponse:
        status_code = next(
            code for error_type, code in _STATUS_BY_ERROR if isinstance(exc, error_type)
        )
        return JSONResponse(status_code=status_code, content={"detail": str(exc)})
