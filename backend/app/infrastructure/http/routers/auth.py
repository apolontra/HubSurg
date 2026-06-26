"""Endpoint de autenticação: emissão de token de acesso."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.application.use_cases import AuthenticateUser
from app.infrastructure.http.dependencies import get_authenticate_user

router = APIRouter(prefix="/auth", tags=["auth"])


class TokenRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


@router.post("/token", response_model=TokenResponse)
def issue_token(
    payload: TokenRequest,
    use_case: AuthenticateUser = Depends(get_authenticate_user),
) -> TokenResponse:
    token = use_case.execute(username=payload.username, password=payload.password)
    return TokenResponse(access_token=token)
