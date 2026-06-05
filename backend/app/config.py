"""Configuração da aplicação via variáveis de ambiente (prefixo HUBSURG_)."""

from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="HUBSURG_", env_file=".env", extra="ignore")

    app_name: str = "HubSurg API"
    environment: str = "dev"
    version: str = "0.1.0"

    # Segurança. Em produção, defina HUBSURG_JWT_SECRET com um segredo forte.
    jwt_secret: str = "dev-insecure-change-me"
    jwt_ttl_seconds: int = 3600

    # Rate limiting (janela fixa por IP).
    rate_limit_requests: int = 100
    rate_limit_window_seconds: int = 60


@lru_cache
def get_settings() -> Settings:
    return Settings()
