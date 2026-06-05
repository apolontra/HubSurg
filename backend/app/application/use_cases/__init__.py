"""Casos de uso do Dossiê Cirúrgico."""

from app.application.use_cases.assemble_dossier import AssembleDossier
from app.application.use_cases.authenticate_user import AuthenticateUser
from app.application.use_cases.generate_perioperative_checklist import (
    ClinicalContext,
    GeneratePerioperativeChecklist,
)
from app.application.use_cases.ingest_diagnostic_report import IngestDiagnosticReport
from app.application.use_cases.record_consent import RecordConsent
from app.application.use_cases.register_patient import AllergyInput, RegisterPatient
from app.application.use_cases.schedule_surgical_case import ScheduleSurgicalCase

__all__ = [
    "AllergyInput",
    "AssembleDossier",
    "AuthenticateUser",
    "ClinicalContext",
    "GeneratePerioperativeChecklist",
    "IngestDiagnosticReport",
    "RecordConsent",
    "RegisterPatient",
    "ScheduleSurgicalCase",
]
