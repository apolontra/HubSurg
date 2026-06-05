# ADR-0001 — Registrar decisões de arquitetura

- **Status:** Aceito
- **Data:** 2026-06-05

## Contexto

O HubSurg é um produto de saúde com requisitos regulatórios e técnicos que evoluirão. Decisões
estruturais (escolha de banco, padrão de arquitetura, protocolo de interoperabilidade) precisam
ser rastreáveis: por que foram tomadas, quais alternativas existiam e quais trade-offs se
aceitaram.

## Decisão

Adotar **Architecture Decision Records (ADRs)** no formato de Michael Nygard, versionados no
repositório em `docs/architecture/adr/`. Cada decisão com impacto estrutural gera um ADR
numerado e imutável. Revisões criam um novo ADR que supersede o anterior.

## Consequências

- **Positivas:** histórico de decisões auditável; onboarding mais rápido; trade-offs explícitos
  — útil inclusive para due diligence regulatória.
- **Negativas:** disciplina adicional para registrar decisões.
