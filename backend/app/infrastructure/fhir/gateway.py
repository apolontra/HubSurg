"""Adaptador local do FhirGateway.

Implementa o port `FhirGateway` mapeando o dossiê canônico para um FHIR Bundle. Um
adaptador futuro (ex.: cliente REST para um servidor FHIR hospitalar, ou Mirth Connect
para hospitais sem FHIR) implementa o mesmo port sem afetar domínio ou aplicação.
"""

from __future__ import annotations

from app.domain.entities import Dossier
from app.domain.ports import FhirGateway
from app.infrastructure.fhir.mappers import dossier_to_bundle


class LocalFhirGateway(FhirGateway):
    def export_dossier(self, dossier: Dossier) -> dict:
        return dossier_to_bundle(dossier)
