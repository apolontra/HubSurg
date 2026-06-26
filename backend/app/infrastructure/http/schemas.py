"""Schemas Pydantic da borda HTTP.

Modelos de entrada/saída ficam aqui, isolados das entidades de domínio. A tradução
entidade ↔ schema é explícita (métodos `from_entity`), evitando vazar o modelo interno.
"""

from __future__ import annotations

from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.domain.entities import (
    Allergy,
    CaseStatus,
    Confidentiality,
    Consent,
    ConsentStatus,
    Criticality,
    DiagnosticReport,
    Patient,
    ReportStatus,
    SurgicalCase,
)


class AllergyIn(BaseModel):
    substance: str
    criticality: Criticality = Criticality.LOW


class AllergyOut(BaseModel):
    id: UUID
    substance: str
    criticality: Criticality

    @classmethod
    def from_entity(cls, allergy: Allergy) -> AllergyOut:
        return cls(id=allergy.id, substance=allergy.substance, criticality=allergy.criticality)


class PatientCreate(BaseModel):
    given_name: str = Field(min_length=1)
    family_name: str = Field(min_length=1)
    birth_date: date
    mrn: str = Field(min_length=1)
    confidentiality: Confidentiality = Confidentiality.NORMAL
    allergies: list[AllergyIn] = Field(default_factory=list)


class PatientOut(BaseModel):
    id: UUID
    given_name: str
    family_name: str
    birth_date: date
    mrn: str
    confidentiality: Confidentiality
    allergies: list[AllergyOut]

    @classmethod
    def from_entity(cls, patient: Patient) -> PatientOut:
        return cls(
            id=patient.id,
            given_name=patient.given_name,
            family_name=patient.family_name,
            birth_date=patient.birth_date,
            mrn=patient.mrn,
            confidentiality=patient.confidentiality,
            allergies=[AllergyOut.from_entity(a) for a in patient.allergies],
        )


class ConsentCreate(BaseModel):
    scopes: list[str] = Field(min_length=1)  # ex.: ["read:Patient", "write:Patient"]
    status: ConsentStatus = ConsentStatus.ACTIVE
    expiration: datetime | None = None


class ConsentOut(BaseModel):
    id: UUID
    patient_id: str
    status: ConsentStatus
    scopes: list[str]
    expiration: datetime | None

    @classmethod
    def from_entity(cls, consent: Consent) -> ConsentOut:
        return cls(
            id=consent.id,
            patient_id=consent.patient_id,
            status=consent.status,
            scopes=sorted(consent.scopes),
            expiration=consent.expiration,
        )


class SurgicalCaseCreate(BaseModel):
    procedure_code: str = Field(min_length=1)
    scheduled_at: datetime


class SurgicalCaseOut(BaseModel):
    id: UUID
    patient_id: UUID
    procedure_code: str
    scheduled_at: datetime
    status: CaseStatus

    @classmethod
    def from_entity(cls, case: SurgicalCase) -> SurgicalCaseOut:
        return cls(
            id=case.id,
            patient_id=case.patient_id,
            procedure_code=case.procedure_code,
            scheduled_at=case.scheduled_at,
            status=case.status,
        )


class DiagnosticReportCreate(BaseModel):
    extracted: dict
    status: ReportStatus = ReportStatus.PARTIAL
    presented_form_url: str | None = None


class DiagnosticReportOut(BaseModel):
    id: UUID
    surgical_case_id: UUID
    status: ReportStatus
    code: str
    extracted: dict
    presented_form_url: str | None

    @classmethod
    def from_entity(cls, report: DiagnosticReport) -> DiagnosticReportOut:
        return cls(
            id=report.id,
            surgical_case_id=report.surgical_case_id,
            status=report.status,
            code=report.code,
            extracted=report.extracted,
            presented_form_url=report.presented_form_url,
        )


class DossierOut(BaseModel):
    patient: PatientOut
    cases: list[SurgicalCaseOut]
    reports: list[DiagnosticReportOut]
