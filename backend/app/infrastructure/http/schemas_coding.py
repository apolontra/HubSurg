"""Schemas da borda HTTP para a codificação TUSS (COFRE)."""

from __future__ import annotations

from pydantic import BaseModel, Field

from app.domain.coding import CodingResult, Confidence


class TussCodingRequest(BaseModel):
    report: str = Field(min_length=1, description="Relato operatório do cirurgião")
    template: str | None = Field(
        default=None, description="Template autoral preenchido (campos que afetam código)"
    )


class CodeSuggestionOut(BaseModel):
    codigo: str
    descricao: str
    sustentado_por: str
    confianca: Confidence


class CodeRefusalOut(BaseModel):
    codigo: str
    descricao: str
    motivo: str
    fato_faltante: str


class TussCodingResponse(BaseModel):
    codigos_sugeridos: list[CodeSuggestionOut]
    codigos_recusados: list[CodeRefusalOut]
    lacunas_documentais: list[str]
    pergunta_ao_cirurgiao: str | None

    @classmethod
    def from_result(cls, result: CodingResult) -> TussCodingResponse:
        return cls(
            codigos_sugeridos=[
                CodeSuggestionOut(
                    codigo=s.codigo,
                    descricao=s.descricao,
                    sustentado_por=s.sustentado_por,
                    confianca=s.confianca,
                )
                for s in result.codigos_sugeridos
            ],
            codigos_recusados=[
                CodeRefusalOut(
                    codigo=r.codigo,
                    descricao=r.descricao,
                    motivo=r.motivo,
                    fato_faltante=r.fato_faltante,
                )
                for r in result.codigos_recusados
            ],
            lacunas_documentais=list(result.lacunas_documentais),
            pergunta_ao_cirurgiao=result.pergunta_ao_cirurgiao,
        )
