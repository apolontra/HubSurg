# ADR-0007 — Consentimento LGPD e tags de confidencialidade FHIR

- **Status:** Aceito
- **Data:** 2026-06-05

## Contexto

Sob a LGPD, processar dados de saúde exige **base legal** — tipicamente o **consentimento**
explícito do titular para finalidades específicas. O plano de segurança pede captura de
consentimento, gestão por escopo e marcação de confidencialidade por recurso
(`Patient.meta.security`). O backend já tinha autenticação e RBAC, mas autorizava o acesso
sem verificar consentimento.

## Decisão

Adicionar uma camada de **autorização por consentimento**, ortogonal ao RBAC:

- **Modelo:** entidade `Consent` (paciente, `status`, `scopes` no formato `acao:Recurso`,
  validade), com a regra `permits(resource_type, action, now)`.
- **Ports:** `ConsentRepository` (persistência) e `ConsentValidatorPort` (validação). O
  adaptador `RepositoryConsentValidator` lança o **erro de domínio** `ConsentError` (a borda
  HTTP traduz para **403**) — diferente do esboço, que levantava `HTTPException` dentro do
  adapter, acoplando-o ao framework.
- **Captura:** `POST /patients/{id}/consent` (papel `surgeon`) registra o consentimento.
- **Aplicação:** dependência `require_consent(resource_type, action)` protege os endpoints
  por paciente (leitura/escrita de Patient e do dossiê). A barreira roda **antes** da
  verificação de existência, então um paciente sem consentimento recebe 403 sem revelar se
  o registro existe.
- **Confidencialidade:** `Patient.confidentiality` (HL7 v3: N/R/V) é emitida como
  `Patient.meta.security`, base para controle de acesso por recurso.

## Alternativas consideradas

- **Consentimento embutido nas claims do JWT** (como no esboço) — simples, mas acopla
  consentimento ao ciclo de vida do token e dificulta revogação. Optou-se por consultá-lo
  de um repositório.
- **Misturar consentimento com RBAC** — confunde *quem pode* (papel) com *para que há base
  legal* (consentimento). Mantidos como camadas separadas.

## Consequências

- **Positivas:** base legal verificada por recurso/ação; revogação imediata (mudar status);
  separação clara RBAC × consentimento; tags FHIR de confidencialidade. 14 testes cobrindo
  unidade e API.
- **Negativas / próximos passos:** consentimento *seed*/in-memory — falta UI de captura,
  versionamento e o recurso FHIR **Consent** completo; integrar com `meta.security` para
  decisões ABAC mais ricas; trilha de auditoria das decisões de acesso (ELK/append-only).
