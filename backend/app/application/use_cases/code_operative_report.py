"""Caso de uso: codificar um relato operatório em códigos TUSS (COFRE).

Orquestra: monta a MENSAGEM, chama o LLM (port), parseia e — antes de devolver — verifica
o contrato de defensabilidade. Qualquer violação (ex.: sustentação inventada) ABORTA: nunca
servimos um resultado que falharia em auditoria.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.domain.coding import (
    CodingResult,
    build_coding_message,
    check_coding_contract,
    parse_coding_result,
)
from app.domain.coding_prompt import COFRE_SYSTEM_PROMPT
from app.domain.errors import CodingContractError
from app.domain.ports import LlmClient


@dataclass(frozen=True)
class CodeOperativeReport:
    llm: LlmClient
    system_prompt: str = COFRE_SYSTEM_PROMPT

    def execute(self, *, report: str, template: str | None = None) -> CodingResult:
        if not report.strip():
            raise CodingContractError("relato operatório vazio")
        message = build_coding_message(report=report, template=template)
        raw = self.llm.complete(system=self.system_prompt, message=message)
        result = parse_coding_result(raw)
        violations = check_coding_contract(result, report=report)
        if violations:
            raise CodingContractError("; ".join(violations))
        return result
