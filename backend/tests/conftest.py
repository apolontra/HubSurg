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
