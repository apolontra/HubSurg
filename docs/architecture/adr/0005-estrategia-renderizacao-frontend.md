# ADR-0005 — Estratégia de renderização do frontend

- **Status:** Aceito
- **Data:** 2026-06-05

## Contexto

O frontend (Next.js/React) serve dois tipos de conteúdo: **checklists e relatórios críticos**,
que precisam de consistência e correção no primeiro carregamento, e **conteúdo assíncrono**
(painéis, listas que atualizam), onde latência de interação importa mais que o primeiro paint.

## Decisão

Usar a renderização híbrida do Next.js conforme o caso:

- **SSR (Server-Side Rendering)** para **checklists e relatórios críticos** — dados corretos e
  completos no primeiro paint, sem flicker de carregamento em telas clínicas sensíveis.
- **CSR (Client-Side Rendering)** para **conteúdo assíncrono** e interações que não devem
  bloquear o carregamento inicial.

Componentização segue **Atomic Design**. Toda comunicação com o backend ocorre via **HTTPS com
TLS 1.3**.

## Consequências

- **Positivas:** equilíbrio entre confiabilidade (telas clínicas) e responsividade (painéis);
  aproveita os recursos nativos do Next.js.
- **Negativas:** exige disciplina para classificar cada tela na estratégia correta; SSR adiciona
  carga ao servidor para as telas críticas.
