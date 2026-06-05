"""Endpoints de pacientes e seus casos cirúrgicos e laudos."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from app.application.use_cases import (
    IngestDiagnosticReport,
    RegisterPatient,
    ScheduleSurgicalCase,
)
from app.application.use_cases.register_patient import AllergyInput
from app.infrastructure.http.container import Container
from app.infrastructure.http.dependencies import (
    get_container,
    get_ingest_diagnostic_report,
    get_register_patient,
    get_schedule_surgical_case,
)
from app.infrastructure.http.schemas import (
    DiagnosticReportCreate,
    DiagnosticReportOut,
    PatientCreate,
    PatientOut,
    SurgicalCaseCreate,
    SurgicalCaseOut,
)

router = APIRouter(prefix="/patients", tags=["patients"])


@router.post("", response_model=PatientOut, status_code=status.HTTP_201_CREATED)
def register_patient(
    payload: PatientCreate,
    use_case: RegisterPatient = Depends(get_register_patient),
) -> PatientOut:
    patient = use_case.execute(
        given_name=payload.given_name,
        family_name=payload.family_name,
        birth_date=payload.birth_date,
        mrn=payload.mrn,
        allergies=tuple(
            AllergyInput(substance=a.substance, criticality=a.criticality)
            for a in payload.allergies
        ),
    )
    return PatientOut.from_entity(patient)


@router.get("", response_model=list[PatientOut])
def list_patients(container: Container = Depends(get_container)) -> list[PatientOut]:
    return [PatientOut.from_entity(p) for p in container.patients.list()]


@router.get("/{patient_id}", response_model=PatientOut)
def get_patient(patient_id: UUID, container: Container = Depends(get_container)) -> PatientOut:
    patient = container.patients.get(patient_id)
    if patient is None:
        raise HTTPException(status_code=404, detail="paciente não encontrado")
    return PatientOut.from_entity(patient)


@router.post(
    "/{patient_id}/cases",
    response_model=SurgicalCaseOut,
    status_code=status.HTTP_201_CREATED,
)
def schedule_case(
    patient_id: UUID,
    payload: SurgicalCaseCreate,
    use_case: ScheduleSurgicalCase = Depends(get_schedule_surgical_case),
) -> SurgicalCaseOut:
    case = use_case.execute(
        patient_id=patient_id,
        procedure_code=payload.procedure_code,
        scheduled_at=payload.scheduled_at,
    )
    return SurgicalCaseOut.from_entity(case)


@router.post(
    "/cases/{case_id}/reports",
    response_model=DiagnosticReportOut,
    status_code=status.HTTP_201_CREATED,
)
def ingest_report(
    case_id: UUID,
    payload: DiagnosticReportCreate,
    use_case: IngestDiagnosticReport = Depends(get_ingest_diagnostic_report),
) -> DiagnosticReportOut:
    report = use_case.execute(
        surgical_case_id=case_id,
        extracted=payload.extracted,
        status=payload.status,
        presented_form_url=payload.presented_form_url,
    )
    return DiagnosticReportOut.from_entity(report)
