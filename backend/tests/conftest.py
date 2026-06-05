"""Fixtures de teste."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.infrastructure.http.container import build_container
from app.infrastructure.persistence.memory import (
    InMemoryDiagnosticReportRepository,
    InMemoryPatientRepository,
    InMemorySurgicalCaseRepository,
)
from app.main import create_app


@pytest.fixture
def patients() -> InMemoryPatientRepository:
    return InMemoryPatientRepository()


@pytest.fixture
def cases() -> InMemorySurgicalCaseRepository:
    return InMemorySurgicalCaseRepository()


@pytest.fixture
def reports() -> InMemoryDiagnosticReportRepository:
    return InMemoryDiagnosticReportRepository()


@pytest.fixture
def container():
    return build_container()


@pytest.fixture
def client() -> TestClient:
    # create_app() monta um container novo a cada app → estado isolado por teste.
    return TestClient(create_app())


def auth_headers(client: TestClient, username: str, password: str) -> dict[str, str]:
    response = client.post("/auth/token", json={"username": username, "password": password})
    assert response.status_code == 200, response.text
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


@pytest.fixture
def surgeon_headers(client: TestClient) -> dict[str, str]:
    return auth_headers(client, "dra.souza", "surgeon-pass")


@pytest.fixture
def assistant_headers(client: TestClient) -> dict[str, str]:
    return auth_headers(client, "assist.lima", "assistant-pass")
