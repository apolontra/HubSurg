# ADR-0002 — Arquitetura hexagonal no backend

- **Status:** Aceito
- **Data:** 2026-06-05

## Contexto

O backend (FastAPI/Python) precisa integrar fornecedores que tendem a mudar — OCR (AWS
Textract), clientes FHIR, mensageria (RabbitMQ hoje, possivelmente Kafka depois) e múltiplos
sistemas hospitalares. As **regras clínicas** (validação de checklists, montagem do dossiê)
não podem ficar acopladas a esses detalhes, sob pena de retrabalho a cada troca de fornecedor.

## Decisão

Adotar **arquitetura hexagonal (Ports & Adapters)** com três camadas:

- **Domínio** — entidades e regras clínicas; define *ports* (interfaces). Sem dependências
  externas.
- **Aplicação** — casos de uso que orquestram *ports* e transações.
- **Infraestrutura** — *adapters* que implementam os *ports*: HTTP (FastAPI), persistência
  (SQLAlchemy/PostgreSQL), OCR, FHIR, mensageria.

Regra de dependência: dependências apontam **para dentro**; a infraestrutura conhece o domínio,
nunca o inverso.

## Alternativas consideradas

- **Camadas em N tiers tradicional** — simples, mas tende a vazar detalhes de infraestrutura
  para a lógica de negócio.
- **CRUD direto sobre o ORM** — rápido para começar, custoso para evoluir e testar regras
  clínicas isoladamente.

## Consequências

- **Positivas:** domínio testável sem I/O; troca de fornecedores via novos adapters; alinhado a
  SOLID (DIP). Suporta a substituição RabbitMQ→Kafka sem tocar no domínio.
- **Negativas:** mais cerimônia inicial (interfaces, mapeadores); curva de aprendizado para
  quem vem de frameworks "fat controller".
