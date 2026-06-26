"""Testes de contrato dos mapeadores FHIR."""

from __future__ import annotations

from datetime import UTC, date, datetime
from uuid import uuid4

from app.domain.entities import (
    CaseStatus,
    DiagnosticReport,
    Dossier,
    Patient,
    ReportStatus,
    SurgicalCase,
)
from app.infrastructure.fhir.mappers import (
    diagnostic_report_to_fhir,
    dossier_to_bundle,
    patient_to_fhir,
    surgical_case_to_fhir,
)


def test_patient_maps_to_fhir_patient():
    patient = Patient(
        given_name="Ana", family_name="Souza", birth_date=date(1980, 5, 1), mrn="MRN-1"
    )
    resource = patient_to_fhir(patient)

    assert resource["resourceType"] == "Patient"
    assert resource["identifier"][0]["value"] == "MRN-1"
    assert resource["name"][0]["family"] == "Souza"
    assert resource["birthDate"] == "1980-05-01"
    # Confidencialidade default (normal) emitida como tag de segurança.
    assert resource["meta"]["security"][0]["code"] == "N"


def test_patient_confidentiality_maps_to_meta_security():
    from app.domain.entities import Confidentiality

    patient = Patient(
        given_name="Ana",
        family_name="Souza",
        birth_date=date(1980, 5, 1),
        mrn="MRN-1",
        confidentiality=Confidentiality.RESTRICTED,
    )
    resource = patient_to_fhir(patient)
    assert resource["meta"]["security"][0]["code"] == "R"


def test_case_status_maps_to_procedure_status():
    case = SurgicalCase(
        patient_id=uuid4(),
        procedure_code="80146002",
        scheduled_at=datetime.now(UTC),
        status=CaseStatus.COMPLETED,
    )
    resource = surgical_case_to_fhir(case)

    assert resource["resourceType"] == "Procedure"
    assert resource["status"] == "completed"
    assert resource["code"]["coding"][0]["code"] == "80146002"


def test_report_includes_conclusion_and_presented_form():
    report = DiagnosticReport(
        surgical_case_id=uuid4(),
        status=ReportStatus.FINAL,
        extracted={"conclusion": "sem alterações"},
        presented_form_url="https://storage/laudo.pdf",
    )
    resource = diagnostic_report_to_fhir(report)

    assert resource["status"] == "final"
    assert resource["conclusion"] == "sem alterações"
    assert resource["presentedForm"][0]["url"] == "https://storage/laudo.pdf"


def test_dossier_renders_as_collection_bundle():
    patient = Patient(
        given_name="Ana", family_name="Souza", birth_date=date(1980, 5, 1), mrn="MRN-1"
    )
    case = SurgicalCase(
        patient_id=patient.id, procedure_code="80146002", scheduled_at=datetime.now(UTC)
    )
    report = DiagnosticReport(
        surgical_case_id=case.id, status=ReportStatus.PARTIAL, extracted={"conclusion": "x"}
    )
    bundle = dossier_to_bundle(Dossier(patient=patient, cases=[case], reports=[report]))

    assert bundle["resourceType"] == "Bundle"
    assert bundle["type"] == "collection"
    resource_types = [entry["resource"]["resourceType"] for entry in bundle["entry"]]
    assert resource_types == ["Patient", "Procedure", "DiagnosticReport"]
