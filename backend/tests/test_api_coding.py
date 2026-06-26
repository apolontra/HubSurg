"""Testes de integração do endpoint de codificação TUSS."""

from __future__ import annotations

import json

from app.application.use_cases import CodeOperativeReport
from app.domain.ports import LlmClient
from app.infrastructure.http.dependencies import get_code_operative_report

REPORT = "Colecistectomia videolaparoscópica. Clipagem e secção de ducto e artéria cística."

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


class _FakeLlm(LlmClient):
    def __init__(self, response: str) -> None:
        self._response = response

    def complete(self, *, system: str, message: str) -> str:
        return self._response


def _override_engine(app, response: str) -> None:
    app.dependency_overrides[get_code_operative_report] = lambda: CodeOperativeReport(
        llm=_FakeLlm(response)
    )


def test_requires_authentication(client):
    assert client.post("/coding/tuss", json={"report": REPORT}).status_code == 401


def test_unconfigured_engine_returns_503(client, surgeon_headers):
    # Container padrão sem HUBSURG_ANTHROPIC_API_KEY → UnavailableLlmClient → 503.
    response = client.post("/coding/tuss", headers=surgeon_headers, json={"report": REPORT})
    assert response.status_code == 503


def test_successful_coding(client, surgeon_headers):
    _override_engine(client.app, CLEAN_OUTPUT)
    response = client.post("/coding/tuss", headers=surgeon_headers, json={"report": REPORT})

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["codigos_sugeridos"][0]["codigo"] == "31003079"
    assert body["codigos_sugeridos"][0]["sustentado_por"] in REPORT


def test_fabricated_support_returns_422(client, surgeon_headers):
    fabricated = json.dumps(
        {
            "codigos_sugeridos": [
                {
                    "codigo": "999",
                    "descricao": "inventado",
                    "sustentado_por": "colangiografia que não consta no relato",
                    "confianca": "alta",
                }
            ],
            "codigos_recusados": [],
            "lacunas_documentais": [],
            "pergunta_ao_cirurgiao": None,
        }
    )
    _override_engine(client.app, fabricated)
    response = client.post("/coding/tuss", headers=surgeon_headers, json={"report": REPORT})
    assert response.status_code == 422
