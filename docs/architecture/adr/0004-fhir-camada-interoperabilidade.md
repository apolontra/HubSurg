# ADR-0004 — HL7 FHIR como camada de interoperabilidade

- **Status:** Aceito
- **Data:** 2026-06-05

## Contexto

O dossiê cirúrgico só tem valor se conversar com os sistemas hospitalares (Tasy, MV e outros
EHRs). Esses sistemas têm graus distintos de maturidade: alguns expõem FHIR; outros, apenas
HL7 v2 ou exports legados (CSV).

## Decisão

Adotar **HL7 FHIR R4** como o **contrato de troca** com sistemas externos:

- O modelo de persistência interno é canônico próprio, **mapeável** para recursos FHIR
  (Patient, Procedure, DiagnosticReport, Observation, AllergyIntolerance, CarePlan,
  DocumentReference) — ver [mapeamento FHIR](../../fhir/resource-mapping.md).
- A tradução FHIR ↔ canônico fica num *port* `FhirGateway` (camada anticorrupção); o domínio
  nunca manipula JSON FHIR cru.
- Hospitais sem FHIR são integrados via camada intermediária (ex.: **Mirth Connect**) que
  traduz HL7 v2/CSV → FHIR, mantendo o HubSurg falando um único protocolo.

## Alternativas consideradas

- **Integração ponto a ponto por sistema** — rápido para o primeiro cliente, insustentável a
  cada novo hospital.
- **Persistir diretamente em FHIR** (servidor FHIR como banco primário) — forte na
  interoperabilidade, mas engessa o modelo interno e complica consultas/relatórios próprios.

## Consequências

- **Positivas:** integração padronizada e reusável; desacoplamento via anticorrupção; caminho
  claro para hospitais com e sem FHIR.
- **Negativas:** custo de manter mapeadores e lidar com perfis/variações de conformidade entre
  fornecedores; necessidade de testes de contrato por integração.
