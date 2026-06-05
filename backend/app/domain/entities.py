"""Entidades e regras do domínio clínico-cirúrgico.

Tipos puros (dataclasses), sem conhecimento de banco, HTTP ou FHIR. As correspondências
com recursos FHIR vivem na infraestrutura — ver docs/fhir/resource-mapping.md.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, field
from datetime import UTC, date, datetime
from enum import StrEnum
from uuid import UUID, uuid4

from app.domain.errors import InvalidState


def _new_id() -> UUID:
    return uuid4()


def _now() -> datetime:
    return datetime.now(UTC)


class Criticality(StrEnum):
    LOW = "low"
    HIGH = "high"


class CaseStatus(StrEnum):
    PLANNED = "planned"
    IN_PROGRESS = "in-progress"
    COMPLETED = "completed"


class ReportStatus(StrEnum):
    """Reflete a confiança/completude da extração (ver mapeamento FHIR DiagnosticReport)."""

    PRELIMINARY = "preliminary"
    PARTIAL = "partial"
    FINAL = "final"


class Role(StrEnum):
    """Papéis do RBAC — ver docs/security/privacy-and-security.md."""

    SURGEON = "surgeon"
    ASSISTANT = "assistant"
    ADMIN = "admin"


@dataclass
class User:
    username: str
    password_hash: str  # credencial opaca; o algoritmo é detalhe de infraestrutura
    roles: frozenset[Role]
    two_factor_enabled: bool = False
    id: UUID = field(default_factory=_new_id)

    def has_any_role(self, roles: Iterable[Role]) -> bool:
        return any(role in self.roles for role in roles)


@dataclass
class Allergy:
    substance: str
    criticality: Criticality = Criticality.LOW
    id: UUID = field(default_factory=_new_id)


@dataclass
class Patient:
    given_name: str
    family_name: str
    birth_date: date
    mrn: str  # identificador hospitalar (pseudonimizado)
    allergies: list[Allergy] = field(default_factory=list)
    id: UUID = field(default_factory=_new_id)
    created_at: datetime = field(default_factory=_now)

    def add_allergy(self, allergy: Allergy) -> None:
        """Adiciona uma alergia, ignorando duplicatas pela substância (idempotente)."""
        if any(a.substance.casefold() == allergy.substance.casefold() for a in self.allergies):
            return
        self.allergies.append(allergy)


@dataclass
class SurgicalCase:
    patient_id: UUID
    procedure_code: str  # ex.: SNOMED CT / TUSS
    scheduled_at: datetime
    status: CaseStatus = CaseStatus.PLANNED
    id: UUID = field(default_factory=_new_id)


@dataclass
class DiagnosticReport:
    surgical_case_id: UUID
    status: ReportStatus
    extracted: dict  # saída estruturada do OCR
    code: str = "11502-2"  # LOINC: laboratory report
    presented_form_url: str | None = None
    id: UUID = field(default_factory=_new_id)
    created_at: datetime = field(default_factory=_now)

    def finalize(self) -> None:
        """Promove o laudo a 'final'. Um laudo sem conteúdo extraído não pode ser finalizado."""
        if not self.extracted:
            raise InvalidState("não é possível finalizar um laudo sem conteúdo extraído")
        self.status = ReportStatus.FINAL


@dataclass
class Dossier:
    """Visão agregada (read model) do dossiê de um paciente."""

    patient: Patient
    cases: list[SurgicalCase]
    reports: list[DiagnosticReport]
