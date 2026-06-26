"""Testes de integração dos controles de segurança da API."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app
from tests.conftest import auth_headers

_PATIENT = {
    "given_name": "Ana",
    "family_name": "Souza",
    "birth_date": "1980-05-01",
    "mrn": "MRN-1",
}


def test_unauthenticated_request_is_rejected(client):
    assert client.get("/patients").status_code == 401
    assert client.post("/patients", json=_PATIENT).status_code == 401


def test_invalid_token_is_rejected(client):
    response = client.get("/patients", headers={"Authorization": "Bearer not.a.token"})
    assert response.status_code == 401


def test_assistant_cannot_register_patient(client, assistant_headers):
    # Assistente tem papel clínico, mas registrar paciente exige cirurgião (RBAC).
    response = client.post("/patients", headers=assistant_headers, json=_PATIENT)
    assert response.status_code == 403


def test_assistant_can_read_patients(client, assistant_headers):
    assert client.get("/patients", headers=assistant_headers).status_code == 200


def test_security_headers_present(client):
    headers = client.get("/health").headers
    assert headers["X-Content-Type-Options"] == "nosniff"
    assert headers["X-Frame-Options"] == "DENY"
    assert "Content-Security-Policy" in headers
    assert "Strict-Transport-Security" in headers


def test_rate_limit_returns_429_when_exceeded():
    settings = Settings(rate_limit_requests=3, rate_limit_window_seconds=60)
    client = TestClient(create_app(settings))

    statuses = [client.get("/health").status_code for _ in range(4)]
    assert statuses[:3] == [200, 200, 200]
    assert statuses[3] == 429


def test_token_grants_only_assigned_roles(client):
    # Admin não tem papel clínico → não pode ler pacientes.
    headers = auth_headers(client, "admin", "admin-pass")
    assert client.get("/patients", headers=headers).status_code == 403


@pytest.mark.parametrize(
    "bad",
    [{"username": "dra.souza", "password": "x"}, {"username": "no", "password": "x"}],
)
def test_token_endpoint_rejects_bad_credentials(client, bad):
    assert client.post("/auth/token", json=bad).status_code == 401
