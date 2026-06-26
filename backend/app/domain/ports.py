"""Ports: interfaces que o domínio/aplicação exigem da infraestrutura.

A regra de dependência aponta para dentro: a infraestrutura implementa estes contratos;
o domínio nunca conhece SQL, FHIR cru ou fornecedores. Ver docs/architecture/overview.md.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING
from uuid import UUID

from app.domain.entities import (
    Consent,
    DiagnosticReport,
    Dossier,
    Patient,
    SurgicalCase,
    User,
)
from app.domain.perioperative import RiskAssessment, RiskInputs

if TYPE_CHECKING:
    from app.domain.events import DomainEvent


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


class UserRepository(ABC):
    @abstractmethod
    def get_by_username(self, username: str) -> User | None: ...


class PasswordHasher(ABC):
    """Port de hashing de senha. A implementação (PBKDF2, bcrypt, argon2) é detalhe de infra."""

    @abstractmethod
    def hash(self, plain: str) -> str: ...

    @abstractmethod
    def verify(self, plain: str, hashed: str) -> bool: ...


class TokenService(ABC):
    """Port de emissão/validação de tokens de acesso (ex.: JWT)."""

    @abstractmethod
    def issue(self, *, subject: str, roles: list[str]) -> str: ...

    @abstractmethod
    def decode(self, token: str) -> dict:
        """Valida e retorna as claims. Lança AuthenticationError se inválido/expirado."""


class ConsentRepository(ABC):
    @abstractmethod
    def add(self, consent: Consent) -> None: ...

    @abstractmethod
    def get_for_patient(self, patient_id: str) -> Consent | None: ...


class ConsentValidatorPort(ABC):
    """Valida o consentimento LGPD para uma ação sobre um recurso de um paciente.

    Implementações lançam ConsentError quando o consentimento está ausente, não cobre
    a ação/recurso ou está inativo/expirado.
    """

    @abstractmethod
    def validate(self, *, patient_id: str, resource_type: str, action: str) -> None: ...


class RiskEngine(ABC):
    """Calcula o risco perioperatório de um caso.

    A implementação padrão é baseada em regras; um modelo de ML (ex.: MySurgeryRisk) pode
    substituí-la sem afetar domínio/aplicação.
    """

    @abstractmethod
    def assess(self, *, case_id: UUID, inputs: RiskInputs) -> RiskAssessment: ...


class EventBus(ABC):
    """Barramento de eventos de domínio. In-memory hoje; Kafka/EventBridge no futuro."""

    @abstractmethod
    def publish(self, event: DomainEvent) -> None: ...


class LlmClient(ABC):
    """Port para um modelo de linguagem. Recebe SYSTEM (estável) + MENSAGEM (por caso).

    A implementação concreta (Anthropic Claude, etc.) é detalhe de infraestrutura; deve
    retornar SOMENTE o texto da resposta do modelo.
    """

    @abstractmethod
    def complete(self, *, system: str, message: str) -> str: ...
