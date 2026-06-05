"""Endpoint de captura de consentimento LGPD."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, status

from app.application.use_cases import RecordConsent
from app.domain.entities import Role
from app.infrastructure.http.dependencies import get_record_consent
from app.infrastructure.http.schemas import ConsentCreate, ConsentOut
from app.infrastructure.http.security import require_roles

router = APIRouter(prefix="/patients/{patient_id}/consent", tags=["consent"])


@router.post(
    "",
    response_model=ConsentOut,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_roles(Role.SURGEON))],
)
def record_consent(
    patient_id: UUID,
    payload: ConsentCreate,
    use_case: RecordConsent = Depends(get_record_consent),
) -> ConsentOut:
    consent = use_case.execute(
        patient_id=patient_id,
        scopes=frozenset(payload.scopes),
        status=payload.status,
        expiration=payload.expiration,
    )
    return ConsentOut.from_entity(consent)
