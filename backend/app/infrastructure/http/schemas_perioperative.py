"""Schemas da borda HTTP para a orquestração perioperatória."""

from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, Field

from app.domain.perioperative import (
    ChecklistCategory,
    Complication,
    DynamicChecklist,
    RiskAssessment,
    SurgicalPhase,
)


class ClinicalContextIn(BaseModel):
    asa_class: int = Field(default=2, ge=1, le=4)
    creatinine: float | None = Field(default=None, ge=0)
    anticoagulated: bool = False
    urgent: bool = False
    diabetic: bool = False


class RiskScoreOut(BaseModel):
    complication: Complication
    probability: float
    contributing_factors: list[str]


class RiskAssessmentOut(BaseModel):
    case_id: UUID
    scores: list[RiskScoreOut]

    @classmethod
    def from_entity(cls, assessment: RiskAssessment) -> RiskAssessmentOut:
        return cls(
            case_id=assessment.case_id,
            scores=[
                RiskScoreOut(
                    complication=s.complication,
                    probability=s.probability,
                    contributing_factors=list(s.contributing_factors),
                )
                for s in assessment.scores
            ],
        )


class ChecklistItemOut(BaseModel):
    id: str
    description: str
    category: ChecklistCategory
    phase: SurgicalPhase
    source: str


class PerioperativeOut(BaseModel):
    assessment: RiskAssessmentOut
    checklist: list[ChecklistItemOut]
    tasks_by_role: dict[ChecklistCategory, list[ChecklistItemOut]]

    @classmethod
    def build(cls, assessment: RiskAssessment, checklist: DynamicChecklist) -> PerioperativeOut:
        def to_out(item) -> ChecklistItemOut:
            return ChecklistItemOut(
                id=item.id,
                description=item.description,
                category=item.category,
                phase=item.phase,
                source=item.source,
            )

        return cls(
            assessment=RiskAssessmentOut.from_entity(assessment),
            checklist=[to_out(i) for i in checklist.items],
            tasks_by_role={
                role: [to_out(i) for i in items] for role, items in checklist.by_role().items()
            },
        )
