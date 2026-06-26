"""Testes do barramento de eventos in-memory."""

from __future__ import annotations

from uuid import uuid4

from app.domain.events import ChecklistGenerated, RiskAssessed
from app.domain.perioperative import RiskAssessment
from app.infrastructure.events.bus import InMemoryEventBus


def test_publish_records_history():
    bus = InMemoryEventBus()
    bus.publish(ChecklistGenerated(case_id=uuid4(), item_count=12))

    assert len(bus.published) == 1
    assert bus.published[0].name == "checklist_generated"


def test_subscribers_receive_matching_events_only():
    bus = InMemoryEventBus()
    received: list[str] = []
    bus.subscribe("risk_assessed", lambda e: received.append(e.name))

    case_id = uuid4()
    assessment = RiskAssessment(case_id=case_id, scores=())
    bus.publish(RiskAssessed(case_id=case_id, assessment=assessment))
    bus.publish(ChecklistGenerated(case_id=case_id, item_count=12))  # outro nome, ignorado

    assert received == ["risk_assessed"]
