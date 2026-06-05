"""Testes de integração da aplicação do consentimento LGPD na API."""

from __future__ import annotations

_PATIENT = {
    "given_name": "Ana",
    "family_name": "Souza",
    "birth_date": "1980-05-01",
    "mrn": "MRN-1",
}


def _create_patient(client, headers) -> str:
    response = client.post("/patients", headers=headers, json=_PATIENT)
    assert response.status_code == 201, response.text
    return response.json()["id"]


def _record_consent(client, headers, patient_id, scopes):
    return client.post(
        f"/patients/{patient_id}/consent",
        headers=headers,
        json={"scopes": scopes},
    )


def test_read_patient_without_consent_is_forbidden(client, surgeon_headers):
    patient_id = _create_patient(client, surgeon_headers)
    response = client.get(f"/patients/{patient_id}", headers=surgeon_headers)
    assert response.status_code == 403
    assert "consentimento" in response.json()["detail"].lower()


def test_read_patient_with_consent_succeeds(client, surgeon_headers):
    patient_id = _create_patient(client, surgeon_headers)
    assert _record_consent(client, surgeon_headers, patient_id, ["read:Patient"]).status_code == 201

    response = client.get(f"/patients/{patient_id}", headers=surgeon_headers)
    assert response.status_code == 200


def test_read_consent_does_not_grant_write(client, surgeon_headers):
    patient_id = _create_patient(client, surgeon_headers)
    _record_consent(client, surgeon_headers, patient_id, ["read:Patient"])

    # Consentimento cobre apenas leitura → agendar caso (write) deve ser negado.
    response = client.post(
        f"/patients/{patient_id}/cases",
        headers=surgeon_headers,
        json={"procedure_code": "80146002", "scheduled_at": "2026-06-10T08:00:00Z"},
    )
    assert response.status_code == 403


def test_dossier_requires_consent(client, surgeon_headers):
    patient_id = _create_patient(client, surgeon_headers)

    assert client.get(f"/patients/{patient_id}/dossier", headers=surgeon_headers).status_code == 403

    _record_consent(client, surgeon_headers, patient_id, ["read:Patient"])
    assert client.get(f"/patients/{patient_id}/dossier", headers=surgeon_headers).status_code == 200


def test_recording_consent_requires_surgeon(client, assistant_headers, surgeon_headers):
    patient_id = _create_patient(client, surgeon_headers)
    response = _record_consent(client, assistant_headers, patient_id, ["read:Patient"])
    assert response.status_code == 403
