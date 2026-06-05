"""Configuração da aplicação via variáveis de ambiente (prefixo HUBSURG_)."""

from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="HUBSURG_", env_file=".env", extra="ignore")

    app_name: str = "HubSurg API"
    environment: str = "dev"
    version: str = "0.1.0"


@lru_cache
def get_settings() -> Settings:
    return Settings()
