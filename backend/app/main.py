"""Fábrica da aplicação FastAPI (composition root da borda HTTP)."""

from __future__ import annotations

from fastapi import FastAPI

from app.config import get_settings
from app.infrastructure.http.container import build_container
from app.infrastructure.http.errors import register_exception_handlers
from app.infrastructure.http.routers import dossier, health, patients


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title=settings.app_name,
        version=settings.version,
        summary="Dossiê Cirúrgico Centralizado — API (arquitetura hexagonal)",
    )

    # Estado da aplicação: container de adaptadores. Trocar in-memory por PostgreSQL
    # é uma mudança localizada em build_container().
    app.state.container = build_container()

    register_exception_handlers(app)
    app.include_router(health.router)
    app.include_router(patients.router)
    app.include_router(dossier.router)
    return app


app = create_app()
