"""Ports: interfaces que o domínio/aplicação exigem da infraestrutura.

A regra de dependência aponta para dentro: a infraestrutura implementa estes contratos;
o domínio nunca conhece SQL, FHIR cru ou fornecedores. Ver docs/architecture/overview.md.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from uuid import UUID

from app.domain.entities import DiagnosticReport, Dossier, Patient, SurgicalCase


class PatientRepository(ABC):
    @abstractmethod
    def add(self, patient: Patient) -> None: ...

    @abstractmethod
    def get(self, patient_id: UUID) -> Patient | None: ...

    @abstractmethod
    def list(self) -> list[Patient]: ...


class SurgicalCaseRepository(ABC):
    @abstractmethod
    def add(self, case: SurgicalCase) -> None: ...

    @abstractmethod
    def get(self, case_id: UUID) -> SurgicalCase | None: ...

    @abstractmethod
    def list_for_patient(self, patient_id: UUID) -> list[SurgicalCase]: ...


class DiagnosticReportRepository(ABC):
    @abstractmethod
    def add(self, report: DiagnosticReport) -> None: ...

    @abstractmethod
    def list_for_case(self, case_id: UUID) -> list[DiagnosticReport]: ...


class FhirGateway(ABC):
    """Camada anticorrupção FHIR. Traduz o canônico interno para recursos FHIR R4.

    Hoje exporta o dossiê como Bundle; um adaptador futuro pode publicá-lo num
    servidor FHIR hospitalar sem que o domínio mude.
    """

    @abstractmethod
    def export_dossier(self, dossier: Dossier) -> dict: ...
