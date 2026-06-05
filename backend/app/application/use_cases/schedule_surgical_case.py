"""Caso de uso: agendar um caso cirúrgico para um paciente existente."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from app.domain.entities import SurgicalCase
from app.domain.errors import EntityNotFound
from app.domain.ports import PatientRepository, SurgicalCaseRepository


@dataclass(frozen=True)
class ScheduleSurgicalCase:
    patients: PatientRepository
    cases: SurgicalCaseRepository

    def execute(
        self, *, patient_id: UUID, procedure_code: str, scheduled_at: datetime
    ) -> SurgicalCase:
        if self.patients.get(patient_id) is None:
            raise EntityNotFound(f"paciente {patient_id} não encontrado")
        case = SurgicalCase(
            patient_id=patient_id,
            procedure_code=procedure_code,
            scheduled_at=scheduled_at,
        )
        self.cases.add(case)
        return case
