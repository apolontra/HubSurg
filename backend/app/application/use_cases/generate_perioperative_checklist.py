"""Caso de uso: avaliar risco perioperatório e gerar checklist dinâmico para um caso.

Orquestra o seam event-driven: calcula o risco (port RiskEngine), gera o checklist dinâmico
(domínio) e publica os eventos `risk_assessed` e `checklist_generated` no EventBus.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from uuid import UUID

from app.domain.errors import EntityNotFound
from app.domain.events import ChecklistGenerated, RiskAssessed
from app.domain.perioperative import (
    ChecklistOrchestrator,
    DynamicChecklist,
    RiskAssessment,
    RiskInputs,
)
from app.domain.ports import (
    EventBus,
    PatientRepository,
    RiskEngine,
    SurgicalCaseRepository,
)


@dataclass(frozen=True)
class ClinicalContext:
    """Dados clínicos pontuais informados no momento da avaliação (proxy de FHIR Observation)."""

    asa_class: int = 2
    creatinine: float | None = None
    anticoagulated: bool = False
    urgent: bool = False
    diabetic: bool = False


def _age_on(birth_date: date, reference: date) -> int:
    years = reference.year - birth_date.year
    if (reference.month, reference.day) < (birth_date.month, birth_date.day):
        years -= 1
    return years


@dataclass(frozen=True)
class GeneratePerioperativeChecklist:
    patients: PatientRepository
    cases: SurgicalCaseRepository
    risk_engine: RiskEngine
    events: EventBus
    orchestrator: ChecklistOrchestrator = ChecklistOrchestrator()

    def execute(
        self,
        *,
        patient_id: UUID,
        case_id: UUID,
        context: ClinicalContext,
        today: date | None = None,
    ) -> tuple[RiskAssessment, DynamicChecklist]:
        case = self.cases.get(case_id)
        if case is None or case.patient_id != patient_id:
            raise EntityNotFound(f"caso {case_id} não encontrado para o paciente {patient_id}")
        patient = self.patients.get(patient_id)
        if patient is None:
            raise EntityNotFound(f"paciente {patient_id} não encontrado")

        age = _age_on(patient.birth_date, today or date.today())
        inputs = RiskInputs(
            age=age,
            asa_class=context.asa_class,
            creatinine=context.creatinine,
            anticoagulated=context.anticoagulated,
            urgent=context.urgent,
            diabetic=context.diabetic,
        )
        assessment = self.risk_engine.assess(case_id=case_id, inputs=inputs)
        self.events.publish(RiskAssessed(case_id=case_id, assessment=assessment))

        checklist = self.orchestrator.generate(
            case_id=case_id,
            assessment=assessment,
            anticoagulated=context.anticoagulated,
            age=age,
        )
        self.events.publish(ChecklistGenerated(case_id=case_id, item_count=len(checklist.items)))
        return assessment, checklist
