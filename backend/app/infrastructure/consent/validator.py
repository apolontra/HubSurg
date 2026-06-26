"""Validador de consentimento LGPD baseado em repositório.

Implementa `ConsentValidatorPort`. Diferente do esboço que levantava HTTPException dentro
do adapter, aqui lançamos um erro de domínio (`ConsentError`); a borda HTTP o traduz para
403, mantendo o domínio livre de framework.
"""

from __future__ import annotations

from datetime import UTC, datetime

from app.domain.errors import ConsentError
from app.domain.ports import ConsentRepository, ConsentValidatorPort


class RepositoryConsentValidator(ConsentValidatorPort):
    def __init__(self, consents: ConsentRepository) -> None:
        self._consents = consents

    def validate(self, *, patient_id: str, resource_type: str, action: str) -> None:
        consent = self._consents.get_for_patient(patient_id)
        if consent is None:
            raise ConsentError("consentimento LGPD ausente para este paciente")
        if not consent.permits(resource_type=resource_type, action=action, now=datetime.now(UTC)):
            raise ConsentError(
                f"consentimento LGPD não cobre {action}:{resource_type} "
                "(inativo, expirado ou fora de escopo)"
            )
