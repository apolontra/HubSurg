# ADR-0008 — Orquestração perioperatória: seam event-driven, risco e checklist dinâmico

- **Status:** Aceito
- **Data:** 2026-06-05

## Contexto

A visão de produto (Plataforma de Orquestração Perioperatória) propõe traduzir **predição de
risco** em **ações coordenadas da equipe**, com checklists que se adaptam ao risco individual,
sobre uma arquitetura **event-driven**. O backend já modelava paciente/caso/dossiê, mas não
tinha nenhum desses elementos.

Restrições do ambiente: não há dados nem modelos de ML treinados, nem infraestrutura de
streaming (Kafka), aprendizado federado ou monitoramento fisiológico em tempo real.

## Decisão

Implementar o **núcleo determinístico** da orquestração, atrás de ports, mantendo a fundação
enxuta e testável:

- **Risco:** port `RiskEngine` com adaptador `RuleBasedRiskEngine` — modelo aditivo
  transparente (intercepto + contribuições → logística) para 4 complicações (AKI, sepse, VTE,
  mortalidade 30d), reportando os **fatores contribuintes**. Um modelo de ML (ex.:
  MySurgeryRisk) substitui o adaptador sem mudar domínio/aplicação.
- **Checklist dinâmico:** serviço de domínio `ChecklistOrchestrator` — base WHO SSC + módulos
  (AKI, infecção, coagulação, geriátrico) ativados por limiares de risco e por contexto.
- **Seam event-driven:** port `EventBus` + adaptador `InMemoryEventBus` (síncrono, com
  histórico e assinatura por nome). O caso de uso publica `risk_assessed` e
  `checklist_generated`. Kafka/EventBridge entram como adaptador futuro.
- **Coordenação de equipe (parcial):** o checklist carrega `category` (papel) e a saída expõe
  `tasks_by_role`, base para o Team Coordinator multimodal — sem notificações push/wearables
  nesta fase.
- **API:** `POST /patients/{id}/cases/{case_id}/checklist` (papel clínico + consentimento
  `read:Patient`) recebe um contexto clínico pontual e devolve avaliação de risco + checklist.

## Honestidade de escopo (NÃO implementado)

- **Modelo de ML com AUROC 0.82–0.94** — exige dados/modelos; o motor atual é regra,
  explicitamente uma linha de base, sem alegar AUROC.
- **Monitoramento intraoperatório em tempo real (LSTM multimodal)**, **streaming Kafka**,
  **aprendizado federado** e **marketplace** — infra/ML fora do alcance deste ambiente.

## Consequências

- **Positivas:** demonstra o diferencial (checklist adaptado ao risco) ponta a ponta, com
  arquitetura event-driven e pontos de extensão claros; 16 testes (motor, orquestrador,
  barramento, API).
- **Negativas / próximos passos:** integrar features reais via FHIR (Observation/MedicationStatement)
  em vez de contexto pontual; Team Coordinator com notificações; adaptador de ML; transporte
  de eventos durável.
