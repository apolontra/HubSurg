"""Mapeadores canônico → FHIR R4.

Funções puras que traduzem entidades internas em recursos FHIR, conforme a tabela em
docs/fhir/resource-mapping.md. Mantê-las puras facilita o teste de contrato.
"""

from __future__ import annotations

from uuid import UUID

from app.domain.entities import (
    Allergy,
    CaseStatus,
    DiagnosticReport,
    Dossier,
    Patient,
    SurgicalCase,
)

MRN_SYSTEM = "urn:hubsurg:mrn"
SNOMED_SYSTEM = "http://snomed.info/sct"
LOINC_SYSTEM = "http://loinc.org"

# Procedure.status usa um vocabulário próprio do FHIR, distinto do nosso CaseStatus.
_CASE_STATUS_TO_FHIR: dict[CaseStatus, str] = {
    CaseStatus.PLANNED: "preparation",
    CaseStatus.IN_PROGRESS: "in-progress",
    CaseStatus.COMPLETED: "completed",
}


def patient_to_fhir(patient: Patient) -> dict:
    return {
        "resourceType": "Patient",
        "id": str(patient.id),
        "identifier": [{"system": MRN_SYSTEM, "value": patient.mrn}],
        "name": [{"family": patient.family_name, "given": [patient.given_name]}],
        "birthDate": patient.birth_date.isoformat(),
    }


def allergy_to_fhir(allergy: Allergy, patient_id: UUID) -> dict:
    return {
        "resourceType": "AllergyIntolerance",
        "id": str(allergy.id),
        "patient": {"reference": f"Patient/{patient_id}"},
        "criticality": allergy.criticality.value,
        "code": {"text": allergy.substance},
    }


def surgical_case_to_fhir(case: SurgicalCase) -> dict:
    return {
        "resourceType": "Procedure",
        "id": str(case.id),
        "status": _CASE_STATUS_TO_FHIR[case.status],
        "subject": {"reference": f"Patient/{case.patient_id}"},
        "code": {"coding": [{"system": SNOMED_SYSTEM, "code": case.procedure_code}]},
        "performedDateTime": case.scheduled_at.isoformat(),
    }


def diagnostic_report_to_fhir(report: DiagnosticReport) -> dict:
    resource: dict = {
        "resourceType": "DiagnosticReport",
        "id": str(report.id),
        "status": report.status.value,
        "code": {"coding": [{"system": LOINC_SYSTEM, "code": report.code}]},
        "basedOn": [{"reference": f"Procedure/{report.surgical_case_id}"}],
    }
    conclusion = report.extracted.get("conclusion") if isinstance(report.extracted, dict) else None
    if conclusion:
        resource["conclusion"] = conclusion
    if report.presented_form_url:
        resource["presentedForm"] = [
            {"contentType": "application/pdf", "url": report.presented_form_url}
        ]
    return resource


def dossier_to_bundle(dossier: Dossier) -> dict:
    """Renderiza o dossiê como um FHIR Bundle do tipo 'collection'."""
    resources: list[dict] = [patient_to_fhir(dossier.patient)]
    resources += [allergy_to_fhir(a, dossier.patient.id) for a in dossier.patient.allergies]
    resources += [surgical_case_to_fhir(c) for c in dossier.cases]
    resources += [diagnostic_report_to_fhir(r) for r in dossier.reports]
    return {
        "resourceType": "Bundle",
        "type": "collection",
        "entry": [{"resource": r} for r in resources],
    }
