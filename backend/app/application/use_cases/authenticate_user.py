"""Caso de uso: autenticar usuário e emitir token de acesso."""

from __future__ import annotations

from dataclasses import dataclass

from app.domain.errors import AuthenticationError
from app.domain.ports import PasswordHasher, TokenService, UserRepository

# Hash descartável usado para equalizar o tempo de resposta quando o usuário não existe,
# mitigando enumeração de usuários por timing.
_DUMMY_HASH = "pbkdf2_sha256$1$AAAAAAAAAAAAAAAAAAAAAA$AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"


@dataclass(frozen=True)
class AuthenticateUser:
    users: UserRepository
    hasher: PasswordHasher
    tokens: TokenService

    def execute(self, *, username: str, password: str) -> str:
        user = self.users.get_by_username(username)
        if user is None:
            self.hasher.verify(password, _DUMMY_HASH)  # consome tempo equivalente
            raise AuthenticationError("credenciais inválidas")
        if not self.hasher.verify(password, user.password_hash):
            raise AuthenticationError("credenciais inválidas")
        return self.tokens.issue(
            subject=user.username,
            roles=sorted(role.value for role in user.roles),
        )
