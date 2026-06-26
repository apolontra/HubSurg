"""Usuários de desenvolvimento (seed).

ATENÇÃO: credenciais apenas para desenvolvimento/teste local. Em produção, usuários vêm
de um diretório/IdP e senhas nunca são versionadas.
"""

from __future__ import annotations

from app.domain.entities import Role, User
from app.domain.ports import PasswordHasher

# username -> (senha em texto, papéis)
DEV_CREDENTIALS: dict[str, tuple[str, frozenset[Role]]] = {
    "dra.souza": ("surgeon-pass", frozenset({Role.SURGEON})),
    "assist.lima": ("assistant-pass", frozenset({Role.ASSISTANT})),
    "admin": ("admin-pass", frozenset({Role.ADMIN})),
}


def seed_users(hasher: PasswordHasher) -> list[User]:
    return [
        User(username=username, password_hash=hasher.hash(password), roles=roles)
        for username, (password, roles) in DEV_CREDENTIALS.items()
    ]
