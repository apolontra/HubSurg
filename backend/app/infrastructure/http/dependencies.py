"""Injeção de dependências: liga os casos de uso aos adaptadores do container.

Os casos de uso são montados por requisição a partir do container guardado em
`app.state` (criado em `create_app`), o que dá estado isolado por instância de app —
útil para testes.
"""

from __future__ import annotations

from fastapi import Depends, Request

from app.application.use_cases import (
    AssembleDossier,
    IngestDiagnosticReport,
    RegisterPatient,
    ScheduleSurgicalCase,
)
from app.infrastructure.http.container import Container


def get_container(request: Request) -> Container:
    return request.app.state.container


def get_register_patient(container: Container = Depends(get_container)) -> RegisterPatient:
    return RegisterPatient(patients=container.patients)


def get_schedule_surgical_case(
    container: Container = Depends(get_container),
) -> ScheduleSurgicalCase:
    return ScheduleSurgicalCase(patients=container.patients, cases=container.cases)


def get_ingest_diagnostic_report(
    container: Container = Depends(get_container),
) -> IngestDiagnosticReport:
    return IngestDiagnosticReport(cases=container.cases, reports=container.reports)


def get_assemble_dossier(container: Container = Depends(get_container)) -> AssembleDossier:
    return AssembleDossier(
        patients=container.patients,
        cases=container.cases,
        reports=container.reports,
    )
