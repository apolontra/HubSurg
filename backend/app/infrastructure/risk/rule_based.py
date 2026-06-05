"""Motor de risco baseado em regras transparentes (linha de base, não ML).

Cada complicação tem um intercepto e contribuições aditivas; a soma passa por uma função
logística para gerar uma probabilidade em (0, 1). Os fatores que dispararam são reportados
como `contributing_factors` — papel análogo (e honesto) ao dos "top SHAP factors" de um
modelo de ML, mas sem alegar AUROC que não temos. Implementa o port `RiskEngine`.
"""

from __future__ import annotations

import math
from collections.abc import Callable
from dataclasses import dataclass
from uuid import UUID

from app.domain.perioperative import (
    Complication,
    RiskAssessment,
    RiskInputs,
    RiskScore,
)
from app.domain.ports import RiskEngine


@dataclass(frozen=True)
class _Rule:
    weight: float
    label: str
    applies: Callable[[RiskInputs], bool]


def _logistic(x: float) -> float:
    return 1.0 / (1.0 + math.exp(-x))


def _has_high_creatinine(threshold: float) -> Callable[[RiskInputs], bool]:
    return lambda i: i.creatinine is not None and i.creatinine > threshold


# Modelo aditivo por complicação: (intercepto, regras).
_MODEL: dict[Complication, tuple[float, tuple[_Rule, ...]]] = {
    Complication.AKI: (
        -3.0,
        (
            _Rule(1.1, "creatinina elevada (>1.5)", _has_high_creatinine(1.5)),
            _Rule(0.8, "idade ≥ 70", lambda i: i.age >= 70),
            _Rule(0.7, "cirurgia de urgência", lambda i: i.urgent),
            _Rule(0.6, "ASA ≥ III", lambda i: i.asa_class >= 3),
        ),
    ),
    Complication.SEPSIS: (
        -3.2,
        (
            _Rule(0.9, "cirurgia de urgência", lambda i: i.urgent),
            _Rule(0.7, "ASA ≥ III", lambda i: i.asa_class >= 3),
            _Rule(0.7, "diabetes", lambda i: i.diabetic),
            _Rule(0.5, "idade ≥ 70", lambda i: i.age >= 70),
        ),
    ),
    Complication.VTE: (
        -3.3,
        (
            _Rule(0.8, "idade ≥ 60", lambda i: i.age >= 60),
            _Rule(0.6, "cirurgia de urgência", lambda i: i.urgent),
            _Rule(0.6, "ASA ≥ III", lambda i: i.asa_class >= 3),
        ),
    ),
    Complication.MORTALITY_30D: (
        -4.0,
        (
            _Rule(1.0, "idade ≥ 75", lambda i: i.age >= 75),
            _Rule(1.0, "ASA ≥ IV", lambda i: i.asa_class >= 4),
            _Rule(0.8, "cirurgia de urgência", lambda i: i.urgent),
            _Rule(0.6, "creatinina elevada (>2.0)", _has_high_creatinine(2.0)),
        ),
    ),
}


class RuleBasedRiskEngine(RiskEngine):
    def assess(self, *, case_id: UUID, inputs: RiskInputs) -> RiskAssessment:
        scores: list[RiskScore] = []
        for complication, (intercept, rules) in _MODEL.items():
            total = intercept
            factors: list[str] = []
            for rule in rules:
                if rule.applies(inputs):
                    total += rule.weight
                    factors.append(rule.label)
            scores.append(
                RiskScore(
                    complication=complication,
                    probability=round(_logistic(total), 4),
                    contributing_factors=tuple(factors),
                )
            )
        return RiskAssessment(case_id=case_id, scores=tuple(scores))
