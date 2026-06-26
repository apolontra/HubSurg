# ADR-0003 — PostgreSQL com pgvector e esquema híbrido

- **Status:** Aceito
- **Data:** 2026-06-05

## Contexto

O HubSurg combina dados altamente relacionais (pacientes, exames, agendamentos, checklists)
com dados semiestruturados e variáveis (saída de OCR, payload FHIR bruto) e necessidade de
**busca semântica** sobre laudos. Precisamos de integridade transacional e, ao mesmo tempo, de
flexibilidade de esquema e de vetores.

## Decisão

Adotar **PostgreSQL** como banco primário, com:

- **Esquema híbrido** — tabelas normalizadas para o relacional; colunas **JSONB** para
  metadados/payloads variáveis.
- Extensão **pgvector** para *embeddings* e busca por similaridade.
- Índices: **B-Tree** (relacional), **GIN** (JSONB), **HNSW/IVFFlat** (vetorial). A
  documentação original cita GiST; a escolha final do índice vetorial depende da versão do
  pgvector.

## Alternativas consideradas

- **Banco relacional + banco vetorial dedicado** (ex.: Pinecone/Milvus) — mais infraestrutura
  e consistência distribuída para gerenciar no MVP.
- **NoSQL documento** (ex.: MongoDB) — flexível, mas perde garantias transacionais e joins que
  os dados clínicos exigem.

## Consequências

- **Positivas:** uma única tecnologia cobre relacional, documento e vetorial; transações ACID;
  menos peças móveis no MVP; criptografia em repouso via KMS no volume.
- **Negativas:** busca vetorial em escala muito grande pode exigir, no futuro, um índice/serviço
  dedicado; tuning de índices HNSW requer atenção a recall vs. custo de construção.
