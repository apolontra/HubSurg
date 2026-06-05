"""Endpoints do dossiê agregado: visão interna e exportação FHIR."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends

from app.application.use_cases import AssembleDossier
from app.domain.entities import Role
from app.infrastructure.http.container import Container
from app.infrastructure.http.dependencies import get_assemble_dossier, get_container
from app.infrastructure.http.schemas import (
    DiagnosticReportOut,
    DossierOut,
    PatientOut,
    SurgicalCaseOut,
)
from app.infrastructure.http.security import require_roles

router = APIRouter(
    prefix="/patients/{patient_id}/dossier",
    tags=["dossier"],
    dependencies=[Depends(require_roles(Role.SURGEON, Role.ASSISTANT))],
)


@router.get("", response_model=DossierOut)
def get_dossier(
    patient_id: UUID,
    use_case: AssembleDossier = Depends(get_assemble_dossier),
) -> DossierOut:
    dossier = use_case.execute(patient_id=patient_id)
    return DossierOut(
        patient=PatientOut.from_entity(dossier.patient),
        cases=[SurgicalCaseOut.from_entity(c) for c in dossier.cases],
        reports=[DiagnosticReportOut.from_entity(r) for r in dossier.reports],
    )


@router.get("/fhir")
def get_dossier_as_fhir(
    patient_id: UUID,
    use_case: AssembleDossier = Depends(get_assemble_dossier),
    container: Container = Depends(get_container),
) -> dict:
    """Exporta o dossiê como um FHIR R4 Bundle (interoperabilidade by design)."""
    dossier = use_case.execute(patient_id=patient_id)
    return container.fhir.export_dossier(dossier)
