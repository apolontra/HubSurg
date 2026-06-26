"""Testes do motor de risco baseado em regras (determinístico)."""

from __future__ import annotations

from uuid import uuid4

from app.domain.perioperative import Complication, RiskInputs
from app.infrastructure.risk.rule_based import RuleBasedRiskEngine

ENGINE = RuleBasedRiskEngine()


def _assess(**inputs):
    base = {
        "age": 45,
        "asa_class": 1,
        "creatinine": 0.8,
        "anticoagulated": False,
        "urgent": False,
        "diabetic": False,
    }
    base.update(inputs)
    return ENGINE.assess(case_id=uuid4(), inputs=RiskInputs(**base))


def test_all_complications_scored_with_bounded_probabilities():
    assessment = _assess()
    assert {s.complication for s in assessment.scores} == set(Complication)
    assert all(0.0 < s.probability < 1.0 for s in assessment.scores)


def test_low_risk_below_module_thresholds():
    assessment = _assess()
    assert assessment.probability_of(Complication.AKI) < 0.15
    assert assessment.probability_of(Complication.SEPSIS) < 0.10


def test_high_risk_raises_aki_and_reports_factors():
    assessment = _assess(age=78, asa_class=3, creatinine=2.1, urgent=True)
    aki = next(s for s in assessment.scores if s.complication is Complication.AKI)

    assert aki.probability > 0.15
    assert "creatinina elevada (>1.5)" in aki.contributing_factors
    assert "idade ≥ 70" in aki.contributing_factors


def test_engine_is_deterministic():
    a = _assess(age=78, asa_class=4, urgent=True)
    b = _assess(age=78, asa_class=4, urgent=True)
    assert [s.probability for s in a.scores] == [s.probability for s in b.scores]


def test_higher_acuity_monotonically_increases_mortality():
    low = _assess().probability_of(Complication.MORTALITY_30D)
    high = _assess(age=80, asa_class=4, urgent=True).probability_of(Complication.MORTALITY_30D)
    assert high > low
