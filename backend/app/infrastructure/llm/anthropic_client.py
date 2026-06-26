"""Adaptador LlmClient sobre a API da Anthropic (Claude).

Usa structured outputs (output_config.format) para garantir JSON puro — sem texto extra,
um dos critérios de sucesso do COFRE — e cacheia o SYSTEM (estável) via prompt caching.
O import de `anthropic` é tardio: o pacote só é exigido quando o motor está configurado,
mantendo o caminho enxuto (testes/dev) livre da dependência.

NOTA: este adaptador não é exercido nos testes unitários (requer API key + rede). É validado
indiretamente pelo mesmo parser/validador de contrato que o caso de uso aplica.
"""

from __future__ import annotations

from app.domain.errors import LlmUnavailable
from app.domain.ports import LlmClient

# JSON Schema do formato de saída do COFRE (mantém o modelo dentro do contrato).
_COFRE_OUTPUT_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "codigos_sugeridos": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "codigo": {"type": "string"},
                    "descricao": {"type": "string"},
                    "sustentado_por": {"type": "string"},
                    "confianca": {"type": "string", "enum": ["alta", "media", "baixa"]},
                },
                "required": ["codigo", "descricao", "sustentado_por", "confianca"],
            },
        },
        "codigos_recusados": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "codigo": {"type": "string"},
                    "descricao": {"type": "string"},
                    "motivo": {"type": "string"},
                    "fato_faltante": {"type": "string"},
                },
                "required": ["codigo", "descricao", "motivo", "fato_faltante"],
            },
        },
        "lacunas_documentais": {"type": "array", "items": {"type": "string"}},
        "pergunta_ao_cirurgiao": {"type": ["string", "null"]},
    },
    "required": [
        "codigos_sugeridos",
        "codigos_recusados",
        "lacunas_documentais",
        "pergunta_ao_cirurgiao",
    ],
}


class AnthropicLlmClient(LlmClient):
    def __init__(
        self,
        *,
        api_key: str,
        model: str = "claude-opus-4-8",
        max_tokens: int = 4096,
    ) -> None:
        self._api_key = api_key
        self._model = model
        self._max_tokens = max_tokens
        self._client = None

    def _ensure_client(self):
        if self._client is None:
            import anthropic  # import tardio: só quando o motor é realmente usado

            self._client = anthropic.Anthropic(api_key=self._api_key)
        return self._client

    def complete(self, *, system: str, message: str) -> str:
        client = self._ensure_client()
        response = client.messages.create(
            model=self._model,
            max_tokens=self._max_tokens,
            thinking={"type": "adaptive"},
            output_config={"format": {"type": "json_schema", "schema": _COFRE_OUTPUT_SCHEMA}},
            system=[{"type": "text", "text": system, "cache_control": {"type": "ephemeral"}}],
            messages=[{"role": "user", "content": message}],
        )
        return next((block.text for block in response.content if block.type == "text"), "")


class UnavailableLlmClient(LlmClient):
    """Usado quando nenhum LLM está configurado: falha explicitamente em vez de adivinhar."""

    def complete(self, *, system: str, message: str) -> str:
        raise LlmUnavailable(
            "motor de codificação não configurado (defina HUBSURG_ANTHROPIC_API_KEY)"
        )
