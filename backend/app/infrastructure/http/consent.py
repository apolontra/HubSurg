"""Dependência de borda que exige consentimento LGPD para acessar dados de um paciente.

Extrai o `patient_id` do path e delega ao `ConsentValidatorPort`. O escopo é expresso como
`acao:Recurso` (ex.: read:Patient), o mesmo formato dos escopos de consentimento.
"""

from __future__ import annotations

from uuid import UUID

from fastapi import Depends

from app.infrastructure.http.container import Container
from app.infrastructure.http.dependencies import get_container


def require_consent(resource_type: str, action: str):
    def dependency(patient_id: UUID, container: Container = Depends(get_container)) -> None:
        container.consent_validator.validate(
            patient_id=str(patient_id),
            resource_type=resource_type,
            action=action,
        )

    return dependency
