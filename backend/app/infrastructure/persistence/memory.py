"""Repositórios in-memory.

Adaptadores leves que implementam os ports de persistência sem exigir um banco — ideais
para o MVP, testes e desenvolvimento local. O adaptador PostgreSQL + pgvector (ver
docs/architecture/data-model.md) é uma substituição futura que implementa os mesmos ports.
"""

from __future__ import annotations

from uuid import UUID

from app.domain.entities import DiagnosticReport, Patient, SurgicalCase
from app.domain.ports import (
    DiagnosticReportRepository,
    PatientRepository,
    SurgicalCaseRepository,
)


class InMemoryPatientRepository(PatientRepository):
    def __init__(self) -> None:
        self._items: dict[UUID, Patient] = {}

    def add(self, patient: Patient) -> None:
        self._items[patient.id] = patient

    def get(self, patient_id: UUID) -> Patient | None:
        return self._items.get(patient_id)

    def list(self) -> list[Patient]:
        return list(self._items.values())


class InMemorySurgicalCaseRepository(SurgicalCaseRepository):
    def __init__(self) -> None:
        self._items: dict[UUID, SurgicalCase] = {}

    def add(self, case: SurgicalCase) -> None:
        self._items[case.id] = case

    def get(self, case_id: UUID) -> SurgicalCase | None:
        return self._items.get(case_id)

    def list_for_patient(self, patient_id: UUID) -> list[SurgicalCase]:
        return [c for c in self._items.values() if c.patient_id == patient_id]


class InMemoryDiagnosticReportRepository(DiagnosticReportRepository):
    def __init__(self) -> None:
        self._items: dict[UUID, DiagnosticReport] = {}

    def add(self, report: DiagnosticReport) -> None:
        self._items[report.id] = report

    def list_for_case(self, case_id: UUID) -> list[DiagnosticReport]:
        return [r for r in self._items.values() if r.surgical_case_id == case_id]
