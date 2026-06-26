"""Testes da geração de checklist dinâmico."""

from __future__ import annotations

from uuid import uuid4

from app.domain.perioperative import (
    WHO_SSC_BASE,
    ChecklistCategory,
    ChecklistOrchestrator,
    Complication,
    RiskAssessment,
    RiskScore,
)

ORCHESTRATOR = ChecklistOrchestrator()
BASE_COUNT = len(WHO_SSC_BASE)


def _assessment(**probs) -> RiskAssessment:
    scores = tuple(
        RiskScore(complication=c, probability=probs.get(c.value, 0.0), contributing_factors=())
        for c in Complication
    )
    return RiskAssessment(case_id=uuid4(), scores=scores)


def test_low_risk_yields_base_checklist_only():
    checklist = ORCHESTRATOR.generate(
        case_id=uuid4(), assessment=_assessment(), anticoagulated=False, age=40
    )
    assert len(checklist.items) == BASE_COUNT


def test_high_aki_adds_aki_module():
    checklist = ORCHESTRATOR.generate(
        case_id=uuid4(), assessment=_assessment(aki=0.5), anticoagulated=False, age=40
    )
    ids = {i.id for i in checklist.items}
    assert {"aki-01", "aki-02", "aki-03"} <= ids


def test_anticoagulated_adds_coagulation_module():
    checklist = ORCHESTRATOR.generate(
        case_id=uuid4(), assessment=_assessment(), anticoagulated=True, age=40
    )
    assert any(i.id.startswith("coa-") for i in checklist.items)


def test_elderly_adds_geriatric_module():
    checklist = ORCHESTRATOR.generate(
        case_id=uuid4(), assessment=_assessment(), anticoagulated=False, age=80
    )
    assert any(i.id.startswith("ger-") for i in checklist.items)


def test_combined_risk_stacks_modules_and_groups_by_role():
    checklist = ORCHESTRATOR.generate(
        case_id=uuid4(),
        assessment=_assessment(aki=0.5, sepsis=0.4),
        anticoagulated=True,
        age=80,
    )
    # base + AKI(3) + infecção(2) + coagulação(2) + geriátrico(2)
    assert len(checklist.items) == BASE_COUNT + 3 + 2 + 2 + 2

    by_role = checklist.by_role()
    assert ChecklistCategory.ICU in by_role  # reserva de leito do módulo AKI
    assert ChecklistCategory.LAB in by_role  # hemocomponentes do módulo coagulação
