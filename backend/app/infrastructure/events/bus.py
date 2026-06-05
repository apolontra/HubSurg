"""Barramento de eventos in-memory (síncrono).

Implementa `EventBus`. Despacha eventos a handlers inscritos por nome e mantém um histórico
dos eventos publicados (útil para testes e auditoria local). Em produção, o adaptador
equivalente publicaria em Kafka/EventBridge.
"""

from __future__ import annotations

from collections.abc import Callable

from app.domain.events import DomainEvent
from app.domain.ports import EventBus

Handler = Callable[[DomainEvent], None]


class InMemoryEventBus(EventBus):
    def __init__(self) -> None:
        self._handlers: dict[str, list[Handler]] = {}
        self.published: list[DomainEvent] = []

    def subscribe(self, event_name: str, handler: Handler) -> None:
        self._handlers.setdefault(event_name, []).append(handler)

    def publish(self, event: DomainEvent) -> None:
        self.published.append(event)
        for handler in self._handlers.get(event.name, ()):
            handler(event)
