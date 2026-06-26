"""Caso de uso: montar o dossiê agregado de um paciente."""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from app.domain.entities import Dossier
from app.domain.errors import EntityNotFound
from app.domain.ports import (
    DiagnosticReportRepository,
    PatientRepository,
    SurgicalCaseRepository,
)


@dataclass(frozen=True)
class AssembleDossier:
    patients: PatientRepository
    cases: SurgicalCaseRepository
    reports: DiagnosticReportRepository

    def execute(self, *, patient_id: UUID) -> Dossier:
        patient = self.patients.get(patient_id)
        if patient is None:
            raise EntityNotFound(f"paciente {patient_id} não encontrado")
        cases = self.cases.list_for_patient(patient_id)
        reports = [
            report
            for case in cases
            for report in self.reports.list_for_case(case.id)
        ]
        return Dossier(patient=patient, cases=cases, reports=reports)
