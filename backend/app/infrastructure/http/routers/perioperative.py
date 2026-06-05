"""Endpoint de orquestração perioperatória: risco + checklist dinâmico de um caso."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends

from app.application.use_cases import ClinicalContext, GeneratePerioperativeChecklist
from app.domain.entities import Role
from app.infrastructure.http.consent import require_consent
from app.infrastructure.http.dependencies import get_generate_perioperative_checklist
from app.infrastructure.http.schemas_perioperative import ClinicalContextIn, PerioperativeOut
from app.infrastructure.http.security import require_roles

router = APIRouter(prefix="/patients/{patient_id}/cases/{case_id}", tags=["perioperative"])


@router.post(
    "/checklist",
    response_model=PerioperativeOut,
    dependencies=[
        Depends(require_roles(Role.SURGEON, Role.ASSISTANT)),
        Depends(require_consent("Patient", "read")),
    ],
)
def generate_checklist(
    patient_id: UUID,
    case_id: UUID,
    payload: ClinicalContextIn,
    use_case: GeneratePerioperativeChecklist = Depends(get_generate_perioperative_checklist),
) -> PerioperativeOut:
    assessment, checklist = use_case.execute(
        patient_id=patient_id,
        case_id=case_id,
        context=ClinicalContext(
            asa_class=payload.asa_class,
            creatinine=payload.creatinine,
            anticoagulated=payload.anticoagulated,
            urgent=payload.urgent,
            diabetic=payload.diabetic,
        ),
    )
    return PerioperativeOut.build(assessment, checklist)
