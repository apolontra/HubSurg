"""Testes das regras de domínio (sem I/O)."""

from __future__ import annotations

from datetime import date
from uuid import uuid4

import pytest

from app.domain.entities import (
    Allergy,
    Criticality,
    DiagnosticReport,
    Patient,
    ReportStatus,
)
from app.domain.errors import InvalidState


def _patient() -> Patient:
    return Patient(given_name="Ana", family_name="Souza", birth_date=date(1980, 5, 1), mrn="MRN-1")


def test_add_allergy_is_idempotent_by_substance():
    patient = _patient()
    patient.add_allergy(Allergy(substance="Penicilina", criticality=Criticality.HIGH))
    patient.add_allergy(Allergy(substance="penicilina"))  # mesma substância, caixa diferente

    assert len(patient.allergies) == 1
    assert patient.allergies[0].criticality is Criticality.HIGH


def test_finalize_report_with_content():
    report = DiagnosticReport(
        surgical_case_id=uuid4(),
        status=ReportStatus.PARTIAL,
        extracted={"conclusion": "sem alterações"},
    )
    report.finalize()
    assert report.status is ReportStatus.FINAL


def test_finalize_empty_report_is_rejected():
    report = DiagnosticReport(surgical_case_id=uuid4(), status=ReportStatus.PARTIAL, extracted={})
    with pytest.raises(InvalidState):
        report.finalize()
