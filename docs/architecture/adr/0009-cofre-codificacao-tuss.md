# ADR-0009 — COFRE: motor conservador de codificação TUSS (LLM)

- **Status:** Aceito
- **Data:** 2026-06-05

## Contexto

O COFRE codifica relatos operatórios em códigos TUSS com um objetivo explícito:
**maximizar defensabilidade em auditoria, não faturamento**. A regra de ouro de produto é
que o SYSTEM é estável (definido uma vez) e a MENSAGEM é montada por caso. O maior risco é o
modelo **inventar sustentação** para um código — uma falha que mata a defensabilidade.

## Decisão

Implementar o motor como uma feature de LLM atrás de ports, com um **contrato de saída
verificado deterministicamente** antes de qualquer resposta sair do backend:

- **Prompt SYSTEM versionado** (`COFRE_SYSTEM_PROMPT`, `COFRE_PROMPT_VERSION`) — estável,
  no domínio. A MENSAGEM por caso é montada por `build_coding_message(report, template)`.
- **Tipos de domínio** para a saída (`CodeSuggestion`, `CodeRefusal`, `CodingResult`) +
  parser (`parse_coding_result`) que rejeita JSON inválido / fora do schema.
- **Validador de contrato** (`check_coding_contract`) — a checklist de regressão como código:
  todo `codigo_sugerido` tem `sustentado_por` que é **trecho literal** do relato (comparação
  normalizada por espaços/caixa); nenhum sugerido sem sustentação; todo recusado nomeia o
  `fato_faltante`.
- **Port `LlmClient`** (`complete(system, message) -> str`) — o acesso ao modelo é detalhe de
  infraestrutura. Caso de uso `CodeOperativeReport` monta → chama → parseia → **valida**.
- **Falha fechada:** qualquer violação de contrato lança `CodingContractError` → **422**. Um
  resultado com sustentação inventada **nunca** é servido (alinhado a "um único caso inválida
  o lote").
- **Adaptador Anthropic** (`AnthropicLlmClient`): modelo `claude-opus-4-8`, **structured
  outputs** (`output_config.format`) para garantir JSON sem texto extra, thinking adaptativo,
  e prompt caching do SYSTEM estável. Import de `anthropic` é tardio (dep opcional `[llm]`).
- **Falha explícita quando não configurado:** sem `HUBSURG_ANTHROPIC_API_KEY`, o container usa
  `UnavailableLlmClient` → `LlmUnavailable` → **503** (não finge resposta).
- **Endpoint:** `POST /coding/tuss` (papel clínico).

## Alternativas consideradas

- **Confiar na saída do LLM sem validação** — inaceitável: é exatamente a falha que o COFRE
  existe para evitar.
- **Levantar HTTPException dentro do adapter** — acoplaria domínio ao framework; mantivemos
  erros de domínio traduzidos na borda (como em ADR-0007).
- **n8n + Supabase + Telegram** (deployment descrito no material de produto) — é uma topologia
  de orquestração externa; aqui materializamos o núcleo reutilizável (prompt + contrato +
  motor) no backend, consumível por qualquer orquestrador.

## Consequências

- **Positivas:** a garantia central do COFRE é **executável e testada** (14 testes:
  parser, contrato, casos de fabricação, API incl. 422/503), independente do LLM/orquestrador;
  troca de modelo/provedor é local ao port.
- **Negativas / próximos passos:** o adaptador Anthropic não é exercido por testes (requer
  API key + rede); a verificação de "trecho literal" usa correspondência normalizada
  (tolerante a espaços/caixa) — não captura paráfrase semântica; o default no menor código em
  ambiguidade depende do prompt, não há checagem determinística para isso; falta base de
  códigos TUSS para validar `codigo`/`descricao`.
