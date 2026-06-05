"""Composition root: monta os adaptadores concretos e os expõe como um container.

Trocar implementações (ex.: in-memory → PostgreSQL) acontece apenas aqui; o resto da
aplicação depende somente dos ports.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.domain.ports import (
    DiagnosticReportRepository,
    FhirGateway,
    PatientRepository,
    SurgicalCaseRepository,
)
from app.infrastructure.fhir.gateway import LocalFhirGateway
from app.infrastructure.persistence.memory import (
    InMemoryDiagnosticReportRepository,
    InMemoryPatientRepository,
    InMemorySurgicalCaseRepository,
)


@dataclass(frozen=True)
class Container:
    patients: PatientRepository
    cases: SurgicalCaseRepository
    reports: DiagnosticReportRepository
    fhir: FhirGateway


def build_container() -> Container:
    return Container(
        patients=InMemoryPatientRepository(),
        cases=InMemorySurgicalCaseRepository(),
        reports=InMemoryDiagnosticReportRepository(),
        fhir=LocalFhirGateway(),
    )
