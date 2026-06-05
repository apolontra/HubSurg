"""Testes dos casos de uso contra repositórios in-memory."""

from __future__ import annotations

from datetime import UTC, date, datetime
from uuid import uuid4

import pytest

from app.application.use_cases import (
    AssembleDossier,
    IngestDiagnosticReport,
    RegisterPatient,
    ScheduleSurgicalCase,
)
from app.application.use_cases.register_patient import AllergyInput
from app.domain.entities import Criticality, ReportStatus
from app.domain.errors import EntityNotFound


def _register(patients) -> object:
    return RegisterPatient(patients=patients).execute(
        given_name="Ana",
        family_name="Souza",
        birth_date=date(1980, 5, 1),
        mrn="MRN-1",
        allergies=(AllergyInput("Penicilina", Criticality.HIGH),),
    )


def test_register_patient_persists_with_allergies(patients):
    patient = _register(patients)
    stored = patients.get(patient.id)

    assert stored is not None
    assert stored.mrn == "MRN-1"
    assert [a.substance for a in stored.allergies] == ["Penicilina"]


def test_schedule_case_requires_existing_patient(patients, cases):
    use_case = ScheduleSurgicalCase(patients=patients, cases=cases)
    with pytest.raises(EntityNotFound):
        use_case.execute(
            patient_id=uuid4(),
            procedure_code="80146002",
            scheduled_at=datetime.now(UTC),
        )


def test_ingest_report_requires_existing_case(cases, reports):
    use_case = IngestDiagnosticReport(cases=cases, reports=reports)
    with pytest.raises(EntityNotFound):
        use_case.execute(
            surgical_case_id=uuid4(),
            extracted={"conclusion": "x"},
        )


def test_assemble_dossier_aggregates_cases_and_reports(patients, cases, reports):
    patient = _register(patients)
    case = ScheduleSurgicalCase(patients=patients, cases=cases).execute(
        patient_id=patient.id,
        procedure_code="80146002",
        scheduled_at=datetime.now(UTC),
    )
    IngestDiagnosticReport(cases=cases, reports=reports).execute(
        surgical_case_id=case.id,
        extracted={"conclusion": "sem alterações"},
        status=ReportStatus.FINAL,
    )

    dossier = AssembleDossier(patients=patients, cases=cases, reports=reports).execute(
        patient_id=patient.id
    )

    assert dossier.patient.id == patient.id
    assert len(dossier.cases) == 1
    assert len(dossier.reports) == 1
    assert dossier.reports[0].status is ReportStatus.FINAL
