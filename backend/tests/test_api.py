"""Testes de integração da API via TestClient (fluxo ponta a ponta, autenticado)."""

from __future__ import annotations


def _create_patient(client, headers) -> str:
    response = client.post(
        "/patients",
        headers=headers,
        json={
            "given_name": "Ana",
            "family_name": "Souza",
            "birth_date": "1980-05-01",
            "mrn": "MRN-1",
            "allergies": [{"substance": "Penicilina", "criticality": "high"}],
        },
    )
    assert response.status_code == 201, response.text
    return response.json()["id"]


def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def _record_consent(client, headers, patient_id, scopes=("read:Patient", "write:Patient")):
    response = client.post(
        f"/patients/{patient_id}/consent",
        headers=headers,
        json={"scopes": list(scopes)},
    )
    assert response.status_code == 201, response.text


def test_full_dossier_flow_and_fhir_export(client, surgeon_headers):
    patient_id = _create_patient(client, surgeon_headers)
    _record_consent(client, surgeon_headers, patient_id)

    case_resp = client.post(
        f"/patients/{patient_id}/cases",
        headers=surgeon_headers,
        json={"procedure_code": "80146002", "scheduled_at": "2026-06-10T08:00:00Z"},
    )
    assert case_resp.status_code == 201, case_resp.text
    case_id = case_resp.json()["id"]

    report_resp = client.post(
        f"/patients/cases/{case_id}/reports",
        headers=surgeon_headers,
        json={"extracted": {"conclusion": "sem alterações"}, "status": "final"},
    )
    assert report_resp.status_code == 201, report_resp.text

    dossier = client.get(f"/patients/{patient_id}/dossier", headers=surgeon_headers).json()
    assert dossier["patient"]["mrn"] == "MRN-1"
    assert len(dossier["cases"]) == 1
    assert len(dossier["reports"]) == 1

    bundle = client.get(f"/patients/{patient_id}/dossier/fhir", headers=surgeon_headers).json()
    assert bundle["resourceType"] == "Bundle"
    types = [e["resource"]["resourceType"] for e in bundle["entry"]]
    assert types == ["Patient", "AllergyIntolerance", "Procedure", "DiagnosticReport"]


def test_schedule_case_for_unknown_patient_is_blocked_by_consent_gate(client, surgeon_headers):
    # A barreira de consentimento roda antes da verificação de existência: um paciente sem
    # consentimento (inclusive inexistente) recebe 403, sem revelar se o registro existe.
    response = client.post(
        "/patients/00000000-0000-0000-0000-000000000000/cases",
        headers=surgeon_headers,
        json={"procedure_code": "80146002", "scheduled_at": "2026-06-10T08:00:00Z"},
    )
    assert response.status_code == 403


def test_state_is_isolated_between_clients(client, surgeon_headers):
    # Garante que cada instância de app tem container próprio (sem vazar estado entre testes).
    assert client.get("/patients", headers=surgeon_headers).json() == []
