"""Testes de unidade do COFRE: montagem da mensagem, parsing e contrato."""

from __future__ import annotations

import json

import pytest

from app.application.use_cases import CodeOperativeReport
from app.domain.coding import (
    CodeRefusal,
    CodingResult,
    build_coding_message,
    check_coding_contract,
    parse_coding_result,
)
from app.domain.errors import CodingContractError
from app.domain.ports import LlmClient

REPORT = (
    "Colecistectomia videolaparoscópica. Vesícula com cálculos, dissecção do trígono "
    "cístico sem intercorrências. Clipagem e secção de ducto e artéria cística."
)

CLEAN_OUTPUT = json.dumps(
    {
        "codigos_sugeridos": [
            {
                "codigo": "31003079",
                "descricao": "Colecistectomia videolaparoscópica",
                "sustentado_por": "Colecistectomia videolaparoscópica",
                "confianca": "alta",
            }
        ],
        "codigos_recusados": [],
        "lacunas_documentais": [],
        "pergunta_ao_cirurgiao": None,
    }
)


class FakeLlmClient(LlmClient):
    def __init__(self, response: str) -> None:
        self._response = response
        self.last_system: str | None = None
        self.last_message: str | None = None

    def complete(self, *, system: str, message: str) -> str:
        self.last_system = system
        self.last_message = message
        return self._response


def test_build_message_includes_report_and_template_placeholder():
    msg = build_coding_message(report=REPORT, template=None)
    assert "RELATO OPERATÓRIO:" in msg
    assert "Colecistectomia videolaparoscópica" in msg
    assert "(nenhum template fornecido)" in msg


def test_parse_rejects_non_json():
    with pytest.raises(CodingContractError):
        parse_coding_result("desculpe, aqui vai o resultado: {…}")


def test_parse_rejects_bad_schema():
    with pytest.raises(CodingContractError):
        parse_coding_result(json.dumps({"codigos_sugeridos": [{"codigo": "1"}]}))


def test_parse_valid_output():
    result = parse_coding_result(CLEAN_OUTPUT)
    assert len(result.codigos_sugeridos) == 1
    assert result.codigos_sugeridos[0].codigo == "31003079"


def test_contract_passes_with_literal_support():
    result = parse_coding_result(CLEAN_OUTPUT)
    assert check_coding_contract(result, report=REPORT) == []


def test_contract_flags_fabricated_support():
    fabricated = json.dumps(
        {
            "codigos_sugeridos": [
                {
                    "codigo": "31003079",
                    "descricao": "Colangiografia intraoperatória",
                    "sustentado_por": "colangiografia intraoperatória realizada com contraste",
                    "confianca": "alta",
                }
            ],
            "codigos_recusados": [],
            "lacunas_documentais": [],
            "pergunta_ao_cirurgiao": None,
        }
    )
    violations = check_coding_contract(parse_coding_result(fabricated), report=REPORT)
    assert any("não é trecho literal" in v for v in violations)


def test_contract_flags_refusal_without_fato_faltante():
    result = CodingResult(
        codigos_sugeridos=(),
        codigos_recusados=(
            CodeRefusal(codigo="123", descricao="x", motivo="y", fato_faltante="  "),
        ),
        lacunas_documentais=(),
        pergunta_ao_cirurgiao=None,
    )
    violations = check_coding_contract(result, report=REPORT)
    assert any("fato_faltante" in v for v in violations)


def test_use_case_happy_path():
    use_case = CodeOperativeReport(llm=FakeLlmClient(CLEAN_OUTPUT))
    result = use_case.execute(report=REPORT)
    assert result.codigos_sugeridos[0].confianca.value == "alta"


def test_use_case_aborts_on_fabricated_support():
    fabricated = json.dumps(
        {
            "codigos_sugeridos": [
                {
                    "codigo": "999",
                    "descricao": "inventado",
                    "sustentado_por": "trecho que não existe no relato",
                    "confianca": "alta",
                }
            ],
            "codigos_recusados": [],
            "lacunas_documentais": [],
            "pergunta_ao_cirurgiao": None,
        }
    )
    use_case = CodeOperativeReport(llm=FakeLlmClient(fabricated))
    with pytest.raises(CodingContractError):
        use_case.execute(report=REPORT)


def test_use_case_rejects_empty_report():
    use_case = CodeOperativeReport(llm=FakeLlmClient(CLEAN_OUTPUT))
    with pytest.raises(CodingContractError):
        use_case.execute(report="   ")
