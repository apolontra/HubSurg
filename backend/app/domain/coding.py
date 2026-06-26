"""Domínio da codificação TUSS (COFRE): tipos, montagem da mensagem, parsing e contrato.

Lógica pura: não chama LLM nem rede. O acesso ao modelo é um port (`LlmClient`); aqui ficam
os tipos do resultado, a montagem da MENSAGEM por caso, o parser da saída e — o coração do
COFRE — a verificação de contrato (a checklist de regressão como código executável).
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from enum import StrEnum

from app.domain.errors import CodingContractError


class Confidence(StrEnum):
    ALTA = "alta"
    MEDIA = "media"
    BAIXA = "baixa"


@dataclass(frozen=True)
class CodeSuggestion:
    codigo: str
    descricao: str
    sustentado_por: str  # deve ser um trecho LITERAL do relato
    confianca: Confidence


@dataclass(frozen=True)
class CodeRefusal:
    codigo: str
    descricao: str
    motivo: str
    fato_faltante: str


@dataclass(frozen=True)
class CodingResult:
    codigos_sugeridos: tuple[CodeSuggestion, ...]
    codigos_recusados: tuple[CodeRefusal, ...]
    lacunas_documentais: tuple[str, ...]
    pergunta_ao_cirurgiao: str | None


def build_coding_message(*, report: str, template: str | None = None) -> str:
    """Monta a MENSAGEM por caso (relato do Telegram + template autoral do Supabase)."""
    if template and template.strip():
        template_block = template.strip()
    else:
        template_block = "(nenhum template fornecido)"
    return (
        "RELATO OPERATÓRIO:\n"
        f"{report.strip()}\n\n"
        "TEMPLATE AUTORAL PREENCHIDO (campos que afetam código, confirmados pelo cirurgião):\n"
        f"{template_block}\n\n"
        "Codifique conforme suas regras."
    )


def parse_coding_result(raw: str) -> CodingResult:
    """Parseia a saída do modelo. Lança CodingContractError se não for JSON do schema esperado."""
    try:
        data = json.loads(raw.strip())
    except json.JSONDecodeError as exc:
        raise CodingContractError("saída do modelo não é JSON válido (texto extra?)") from exc
    if not isinstance(data, dict):
        raise CodingContractError("saída do modelo não é um objeto JSON")

    try:
        suggested = tuple(
            CodeSuggestion(
                codigo=str(item["codigo"]),
                descricao=str(item["descricao"]),
                sustentado_por=str(item["sustentado_por"]),
                confianca=Confidence(item["confianca"]),
            )
            for item in data.get("codigos_sugeridos", [])
        )
        refused = tuple(
            CodeRefusal(
                codigo=str(item["codigo"]),
                descricao=str(item["descricao"]),
                motivo=str(item["motivo"]),
                fato_faltante=str(item["fato_faltante"]),
            )
            for item in data.get("codigos_recusados", [])
        )
    except (KeyError, ValueError, TypeError) as exc:
        raise CodingContractError(f"saída não segue o schema esperado: {exc}") from exc

    lacunas = tuple(str(x) for x in data.get("lacunas_documentais", []))
    pergunta = data.get("pergunta_ao_cirurgiao")
    return CodingResult(
        codigos_sugeridos=suggested,
        codigos_recusados=refused,
        lacunas_documentais=lacunas,
        pergunta_ao_cirurgiao=str(pergunta) if pergunta else None,
    )


def _normalize(text: str) -> str:
    """Colapsa espaços e ignora caixa — tolera diferenças triviais sem deixar passar invenção."""
    return " ".join(text.split()).casefold()


def check_coding_contract(result: CodingResult, *, report: str) -> list[str]:
    """Verifica o contrato de defensabilidade. Retorna a lista de violações (vazia = OK).

    Implementa a checklist de regressão do COFRE:
    - todo código sugerido tem 'sustentado_por' que é trecho LITERAL do relato;
    - nenhum código sugerido sem sustentação;
    - todo código recusado nomeia o 'fato_faltante'.
    """
    violations: list[str] = []
    normalized_report = _normalize(report)

    for suggestion in result.codigos_sugeridos:
        if not suggestion.sustentado_por.strip():
            violations.append(f"código {suggestion.codigo}: sugerido sem trecho de sustentação")
        elif _normalize(suggestion.sustentado_por) not in normalized_report:
            violations.append(
                f"código {suggestion.codigo}: 'sustentado_por' não é trecho literal do relato"
            )

    for refusal in result.codigos_recusados:
        if not refusal.fato_faltante.strip():
            violations.append(f"código recusado {refusal.codigo}: sem 'fato_faltante'")

    return violations
