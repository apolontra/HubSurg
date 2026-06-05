"""Testes de unidade do consentimento LGPD."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from app.application.use_cases import RecordConsent
from app.domain.entities import Consent, ConsentStatus, Patient
from app.domain.errors import ConsentError, EntityNotFound
from app.infrastructure.consent.validator import RepositoryConsentValidator
from app.infrastructure.persistence.memory import (
    InMemoryConsentRepository,
    InMemoryPatientRepository,
)


def _consent(**overrides) -> Consent:
    base = {
        "patient_id": "p1",
        "status": ConsentStatus.ACTIVE,
        "scopes": frozenset({"read:Patient"}),
        "expiration": None,
    }
    base.update(overrides)
    return Consent(**base)


def _now() -> datetime:
    return datetime.now(UTC)


def test_permits_active_in_scope():
    assert _consent().permits(resource_type="Patient", action="read", now=_now()) is True


def test_denies_out_of_scope_action():
    assert _consent().permits(resource_type="Patient", action="write", now=_now()) is False


def test_denies_when_inactive():
    consent = _consent(status=ConsentStatus.INACTIVE)
    assert consent.permits(resource_type="Patient", action="read", now=_now()) is False


def test_denies_when_expired():
    consent = _consent(expiration=_now() - timedelta(seconds=1))
    assert consent.permits(resource_type="Patient", action="read", now=_now()) is False


def test_validator_raises_when_no_consent():
    validator = RepositoryConsentValidator(InMemoryConsentRepository())
    with pytest.raises(ConsentError):
        validator.validate(patient_id="p1", resource_type="Patient", action="read")


def test_validator_passes_and_rejects_by_action():
    consents = InMemoryConsentRepository([_consent()])
    validator = RepositoryConsentValidator(consents)

    validator.validate(patient_id="p1", resource_type="Patient", action="read")  # não lança
    with pytest.raises(ConsentError):
        validator.validate(patient_id="p1", resource_type="Patient", action="write")


def test_record_consent_requires_existing_patient():
    use_case = RecordConsent(
        patients=InMemoryPatientRepository(),
        consents=InMemoryConsentRepository(),
    )
    with pytest.raises(EntityNotFound):
        use_case.execute(patient_id=Patient(  # id aleatório, não persistido
            given_name="A", family_name="B", birth_date=datetime(1980, 1, 1).date(), mrn="X"
        ).id, scopes=frozenset({"read:Patient"}))


def test_record_consent_stores_consent():
    patients = InMemoryPatientRepository()
    patient = Patient(
        given_name="A", family_name="B", birth_date=datetime(1980, 1, 1).date(), mrn="X"
    )
    patients.add(patient)
    consents = InMemoryConsentRepository()
    use_case = RecordConsent(patients=patients, consents=consents)

    use_case.execute(patient_id=patient.id, scopes=frozenset({"read:Patient"}))

    stored = consents.get_for_patient(str(patient.id))
    assert stored is not None
    assert "read:Patient" in stored.scopes
