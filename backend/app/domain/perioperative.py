"""Contexto de orquestração perioperatória: risco individual e checklist dinâmico.

Lógica pura de domínio (sem ML, banco ou framework). O cálculo de risco fica atrás do port
`RiskEngine` (ver app/domain/ports.py); aqui ficam os tipos e a geração determinística do
checklist dinâmico (WHO SSC + módulos por risco).

NOTA HONESTA: o motor de risco padrão é uma linha de base **baseada em regras transparentes**,
não um modelo de ML validado. Substituí-lo por um modelo treinado (ex.: MySurgeryRisk) é uma
troca de adaptador do port `RiskEngine`, sem mudar este módulo.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from uuid import UUID


class Complication(StrEnum):
    AKI = "aki"
    SEPSIS = "sepsis"
    VTE = "vte"
    MORTALITY_30D = "mortality_30d"


@dataclass(frozen=True)
class RiskInputs:
    """Variáveis de entrada do motor de risco (derivadas de FHIR Patient/Observation/Procedure)."""

    age: int
    asa_class: int  # 1-4
    creatinine: float | None  # mg/dL
    anticoagulated: bool
    urgent: bool
    diabetic: bool


@dataclass(frozen=True)
class RiskScore:
    complication: Complication
    probability: float  # 0..1
    contributing_factors: tuple[str, ...]


@dataclass(frozen=True)
class RiskAssessment:
    case_id: UUID
    scores: tuple[RiskScore, ...]

    def probability_of(self, complication: Complication) -> float:
        for score in self.scores:
            if score.complication is complication:
                return score.probability
        return 0.0

    def highest(self) -> RiskScore:
        return max(self.scores, key=lambda s: s.probability)


class ChecklistCategory(StrEnum):
    SURGEON = "surgeon"
    ANESTHESIA = "anesthesia"
    NURSING = "nursing"
    LAB = "lab"
    ICU = "icu"


class SurgicalPhase(StrEnum):
    SIGN_IN = "sign-in"
    TIME_OUT = "time-out"
    SIGN_OUT = "sign-out"
    PRE_OP = "pre-op"


@dataclass(frozen=True)
class ChecklistItem:
    id: str
    description: str
    category: ChecklistCategory
    phase: SurgicalPhase
    source: str  # "WHO SSC" ou módulo/diretriz de origem


@dataclass(frozen=True)
class DynamicChecklist:
    case_id: UUID
    items: tuple[ChecklistItem, ...]

    def by_role(self) -> dict[ChecklistCategory, list[ChecklistItem]]:
        grouped: dict[ChecklistCategory, list[ChecklistItem]] = {}
        for item in self.items:
            grouped.setdefault(item.category, []).append(item)
        return grouped


# --- Base WHO Surgical Safety Checklist (subconjunto representativo) -------------------------
# Subconjunto conciso dos 19 itens do WHO SSC, suficiente para demonstrar a base sobre a qual
# os módulos de risco são acrescentados.
_C = ChecklistCategory
_P = SurgicalPhase


def _items(rows: tuple[tuple, ...], source: str) -> tuple[ChecklistItem, ...]:
    """Constrói itens a partir de linhas compactas (id, descrição, categoria, fase)."""
    return tuple(ChecklistItem(i, d, c, p, source) for i, d, c, p in rows)


WHO_SSC_BASE: tuple[ChecklistItem, ...] = _items(
    (
        ("who-01", "Confirmar identidade, sítio e procedimento", _C.NURSING, _P.SIGN_IN),
        ("who-02", "Verificar consentimento assinado", _C.SURGEON, _P.SIGN_IN),
        ("who-03", "Demarcação do sítio cirúrgico", _C.SURGEON, _P.SIGN_IN),
        ("who-04", "Checagem de segurança da anestesia", _C.ANESTHESIA, _P.SIGN_IN),
        ("who-05", "Oxímetro de pulso funcionante", _C.ANESTHESIA, _P.SIGN_IN),
        ("who-06", "Confirmar alergias conhecidas", _C.ANESTHESIA, _P.SIGN_IN),
        ("who-07", "Risco de via aérea difícil avaliado", _C.ANESTHESIA, _P.SIGN_IN),
        ("who-08", "Risco de perda sanguínea >500ml avaliado", _C.SURGEON, _P.SIGN_IN),
        ("who-09", "Apresentação verbal da equipe (time-out)", _C.NURSING, _P.TIME_OUT),
        ("who-10", "Antibiótico profilático nos últimos 60 min", _C.NURSING, _P.TIME_OUT),
        ("who-11", "Imagens essenciais disponíveis", _C.SURGEON, _P.TIME_OUT),
        ("who-12", "Contagem de instrumentos e compressas", _C.NURSING, _P.SIGN_OUT),
    ),
    "WHO SSC",
)


def _aki_module() -> tuple[ChecklistItem, ...]:
    return _items(
        (
            ("aki-01", "Hidratação 1L cristaloide pré-indução", _C.ANESTHESIA, _P.PRE_OP),
            ("aki-02", "Evitar nefrotóxicos (contraste, AINEs)", _C.ANESTHESIA, _P.PRE_OP),
            ("aki-03", "Reservar leito de UTI (risco elevado de AKI)", _C.ICU, _P.PRE_OP),
        ),
        "Módulo AKI",
    )


def _infection_module() -> tuple[ChecklistItem, ...]:
    return _items(
        (
            ("inf-01", "Antibiótico profilático 60 min pré-incisão", _C.NURSING, _P.PRE_OP),
            ("inf-02", "Manter normotermia intraoperatória (>36°C)", _C.ANESTHESIA, _P.TIME_OUT),
        ),
        "Módulo Infecção/Sepse",
    )


def _coagulation_module() -> tuple[ChecklistItem, ...]:
    return _items(
        (
            ("coa-01", "Suspender anticoagulante? Consultar hematologia", _C.SURGEON, _P.PRE_OP),
            ("coa-02", "Reservar hemocomponentes e checar coagulograma", _C.LAB, _P.PRE_OP),
        ),
        "Módulo Coagulação",
    )


def _geriatric_module() -> tuple[ChecklistItem, ...]:
    return _items(
        (
            ("ger-01", "Precauções para delirium pós-operatório", _C.NURSING, _P.PRE_OP),
            ("ger-02", "Revisar polifarmácia e fragilidade", _C.SURGEON, _P.PRE_OP),
        ),
        "Módulo Geriátrico",
    )


# Limiares de ativação dos módulos (alinhados ao documento de produto).
AKI_THRESHOLD = 0.15
SEPSIS_THRESHOLD = 0.10
GERIATRIC_AGE = 75


class ChecklistOrchestrator:
    """Gera um checklist dinâmico: base WHO SSC + módulos ativados pelo risco individual."""

    def generate(
        self,
        *,
        case_id: UUID,
        assessment: RiskAssessment,
        anticoagulated: bool,
        age: int,
    ) -> DynamicChecklist:
        items: list[ChecklistItem] = list(WHO_SSC_BASE)
        if assessment.probability_of(Complication.AKI) > AKI_THRESHOLD:
            items.extend(_aki_module())
        if assessment.probability_of(Complication.SEPSIS) > SEPSIS_THRESHOLD:
            items.extend(_infection_module())
        if anticoagulated:
            items.extend(_coagulation_module())
        if age >= GERIATRIC_AGE:
            items.extend(_geriatric_module())
        return DynamicChecklist(case_id=case_id, items=tuple(items))
