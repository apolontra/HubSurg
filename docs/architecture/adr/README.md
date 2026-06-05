# Architecture Decision Records (ADRs)

Registro das decisões de arquitetura do HubSurg, no formato de
[Michael Nygard](https://cognitect.com/blog/2011/11/15/documenting-architecture-decisions).
Cada ADR é imutável; mudanças de rumo criam um novo ADR que **supersede** o anterior.

## Índice

| # | Título | Status |
|---|--------|--------|
| [0001](0001-registrar-decisoes-de-arquitetura.md) | Registrar decisões de arquitetura | Aceito |
| [0002](0002-arquitetura-hexagonal-backend.md) | Arquitetura hexagonal no backend | Aceito |
| [0003](0003-postgresql-pgvector.md) | PostgreSQL com pgvector e esquema híbrido | Aceito |
| [0004](0004-fhir-camada-interoperabilidade.md) | HL7 FHIR como camada de interoperabilidade | Aceito |
| [0005](0005-estrategia-renderizacao-frontend.md) | Estratégia de renderização do frontend | Aceito |
| [0006](0006-camada-de-seguranca.md) | Camada de segurança (auth, RBAC, rate limiting) | Aceito |
| [0007](0007-consentimento-lgpd-e-meta-security.md) | Consentimento LGPD e tags de confidencialidade FHIR | Aceito |
| [0008](0008-orquestracao-perioperatoria.md) | Orquestração perioperatória (event-driven, risco, checklist dinâmico) | Aceito |

## Status possíveis

- **Proposto** — em discussão.
- **Aceito** — decisão vigente.
- **Substituído** — superado por outro ADR (com link).
- **Obsoleto** — não mais aplicável.
