"""Dependências de autenticação e autorização (RBAC) da borda HTTP."""

from __future__ import annotations

from dataclasses import dataclass

from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer

from app.domain.entities import Role
from app.domain.errors import AuthenticationError, AuthorizationError
from app.infrastructure.http.container import Container
from app.infrastructure.http.dependencies import get_container

# auto_error=False: a ausência de token vira AuthenticationError (401) tratada pelo handler
# de domínio, mantendo o formato de erro uniforme.
_oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token", auto_error=False)


@dataclass(frozen=True)
class AuthenticatedUser:
    username: str
    roles: frozenset[Role]


def get_current_user(
    token: str | None = Depends(_oauth2_scheme),
    container: Container = Depends(get_container),
) -> AuthenticatedUser:
    if not token:
        raise AuthenticationError("token de acesso ausente")
    claims = container.tokens.decode(token)
    roles = frozenset(Role(role) for role in claims.get("roles", []))
    return AuthenticatedUser(username=claims["sub"], roles=roles)


def require_roles(*required: Role):
    """Fábrica de dependência que exige pelo menos um dos papéis informados."""

    def dependency(user: AuthenticatedUser = Depends(get_current_user)) -> AuthenticatedUser:
        if not set(required) & user.roles:
            raise AuthorizationError("permissão insuficiente para esta operação")
        return user

    return dependency
