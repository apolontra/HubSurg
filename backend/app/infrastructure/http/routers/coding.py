"""Endpoint de codificação TUSS (COFRE)."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from app.application.use_cases import CodeOperativeReport
from app.domain.entities import Role
from app.infrastructure.http.dependencies import get_code_operative_report
from app.infrastructure.http.schemas_coding import TussCodingRequest, TussCodingResponse
from app.infrastructure.http.security import require_roles

router = APIRouter(prefix="/coding", tags=["coding"])


@router.post(
    "/tuss",
    response_model=TussCodingResponse,
    dependencies=[Depends(require_roles(Role.SURGEON, Role.ASSISTANT))],
)
def code_tuss(
    payload: TussCodingRequest,
    use_case: CodeOperativeReport = Depends(get_code_operative_report),
) -> TussCodingResponse:
    result = use_case.execute(report=payload.report, template=payload.template)
    return TussCodingResponse.from_result(result)
