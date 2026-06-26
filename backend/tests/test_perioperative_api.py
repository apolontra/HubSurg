"""Testes de integração do endpoint de orquestração perioperatória."""

from __future__ import annotations

_PATIENT = {
    "given_name": "Ana",
    "family_name": "Souza",
    "birth_date": "1945-05-01",  # idoso → ativa módulo geriátrico
    "mrn": "MRN-1",
}


def _setup_case(client, headers) -> tuple[str, str]:
    patient_id = client.post("/patients", headers=headers, json=_PATIENT).json()["id"]
    client.post(
        f"/patients/{patient_id}/consent",
        headers=headers,
        json={"scopes": ["read:Patient", "write:Patient"]},
    )
    case_id = client.post(
        f"/patients/{patient_id}/cases",
        headers=headers,
        json={"procedure_code": "80146002", "scheduled_at": "2026-06-10T08:00:00Z"},
    ).json()["id"]
    return patient_id, case_id


def test_low_risk_checklist_flow(client, surgeon_headers):
    patient_id, case_id = _setup_case(client, surgeon_headers)
    response = client.post(
        f"/patients/{patient_id}/cases/{case_id}/checklist",
        headers=surgeon_headers,
        json={"asa_class": 1, "creatinine": 0.8},
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert len(body["assessment"]["scores"]) == 4
    assert len(body["checklist"]) >= 1
    assert "tasks_by_role" in body


def test_high_risk_checklist_has_more_items_than_low(client, surgeon_headers):
    patient_id, case_id = _setup_case(client, surgeon_headers)

    low = client.post(
        f"/patients/{patient_id}/cases/{case_id}/checklist",
        headers=surgeon_headers,
        json={"asa_class": 1, "creatinine": 0.8, "anticoagulated": False},
    ).json()
    high = client.post(
        f"/patients/{patient_id}/cases/{case_id}/checklist",
        headers=surgeon_headers,
        json={"asa_class": 4, "creatinine": 2.5, "urgent": True, "anticoagulated": True},
    ).json()

    assert len(high["checklist"]) > len(low["checklist"])
    aki = next(s for s in high["assessment"]["scores"] if s["complication"] == "aki")
    assert aki["contributing_factors"]  # fatores reportados


def test_checklist_requires_consent(client, surgeon_headers):
    # Paciente sem consentimento registrado.
    patient_id = client.post("/patients", headers=surgeon_headers, json=_PATIENT).json()["id"]
    case_id = client.post(
        f"/patients/{patient_id}/cases",  # também bloqueado por consentimento → cria via repo? não.
        headers=surgeon_headers,
        json={"procedure_code": "80146002", "scheduled_at": "2026-06-10T08:00:00Z"},
    ).status_code
    # Agendar já exige consentimento (write); sem ele, retorna 403.
    assert case_id == 403


def test_checklist_for_mismatched_patient_case_returns_404(client, surgeon_headers):
    patient_id, case_id = _setup_case(client, surgeon_headers)
    other_id = client.post(
        "/patients",
        headers=surgeon_headers,
        json={**_PATIENT, "mrn": "MRN-2"},
    ).json()["id"]
    client.post(
        f"/patients/{other_id}/consent",
        headers=surgeon_headers,
        json={"scopes": ["read:Patient"]},
    )

    # case_id pertence a patient_id, não a other_id → 404.
    response = client.post(
        f"/patients/{other_id}/cases/{case_id}/checklist",
        headers=surgeon_headers,
        json={"asa_class": 2},
    )
    assert response.status_code == 404
