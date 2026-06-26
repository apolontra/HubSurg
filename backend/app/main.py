"""Fábrica da aplicação FastAPI (composition root da borda HTTP)."""

from __future__ import annotations

from fastapi import FastAPI

from app.config import Settings, get_settings
from app.infrastructure.http.container import build_container
from app.infrastructure.http.errors import register_exception_handlers
from app.infrastructure.http.middleware import (
    RateLimitMiddleware,
    SecurityHeadersMiddleware,
)
from app.infrastructure.http.routers import (
    auth,
    coding,
    consent,
    dossier,
    health,
    patients,
    perioperative,
)


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or get_settings()
    app = FastAPI(
        title=settings.app_name,
        version=settings.version,
        summary="Dossiê Cirúrgico Centralizado — API (arquitetura hexagonal)",
    )

    # Estado da aplicação: container de adaptadores. Trocar in-memory por PostgreSQL
    # é uma mudança localizada em build_container().
    app.state.settings = settings
    app.state.container = build_container(settings)

    register_exception_handlers(app)

    # Middlewares: RateLimit é adicionado primeiro (mais interno); SecurityHeaders por
    # último (mais externo), garantindo cabeçalhos de proteção em todas as respostas.
    app.add_middleware(
        RateLimitMiddleware,
        limit=settings.rate_limit_requests,
        window_seconds=settings.rate_limit_window_seconds,
    )
    app.add_middleware(SecurityHeadersMiddleware)

    app.include_router(health.router)
    app.include_router(auth.router)
    app.include_router(patients.router)
    app.include_router(consent.router)
    app.include_router(perioperative.router)
    app.include_router(dossier.router)
    app.include_router(coding.router)
    return app


app = create_app()
