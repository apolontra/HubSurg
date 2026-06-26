"""Eventos de domínio para a orquestração event-driven.

Cirurgia é uma sequência de eventos críticos; o sistema reage publicando/assinando eventos.
Estes tipos são o contrato; o transporte (in-memory hoje, Kafka/EventBridge no futuro) é um
adaptador do port `EventBus`.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar
from uuid import UUID

from app.domain.perioperative import RiskAssessment


@dataclass(frozen=True)
class DomainEvent:
    """Base de todos os eventos de domínio. `name` identifica o tipo no barramento."""

    name: ClassVar[str] = "domain_event"


@dataclass(frozen=True)
class RiskAssessed(DomainEvent):
    name: ClassVar[str] = "risk_assessed"
    case_id: UUID
    assessment: RiskAssessment


@dataclass(frozen=True)
class ChecklistGenerated(DomainEvent):
    name: ClassVar[str] = "checklist_generated"
    case_id: UUID
    item_count: int
