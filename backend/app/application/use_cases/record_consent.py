"""Caso de uso: registrar (capturar) o consentimento LGPD de um paciente."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID

from app.domain.entities import Consent, ConsentStatus
from app.domain.errors import EntityNotFound
from app.domain.ports import ConsentRepository, PatientRepository


@dataclass(frozen=True)
class RecordConsent:
    patients: PatientRepository
    consents: ConsentRepository

    def execute(
        self,
        *,
        patient_id: UUID,
        scopes: frozenset[str],
        status: ConsentStatus = ConsentStatus.ACTIVE,
        expiration: datetime | None = None,
    ) -> Consent:
        if self.patients.get(patient_id) is None:
            raise EntityNotFound(f"paciente {patient_id} não encontrado")
        # Normaliza datas ingênuas para UTC, evitando comparação aware/naive.
        if expiration is not None and expiration.tzinfo is None:
            expiration = expiration.replace(tzinfo=UTC)
        consent = Consent(
            patient_id=str(patient_id),
            status=status,
            scopes=scopes,
            expiration=expiration,
        )
        self.consents.add(consent)
        return consent
