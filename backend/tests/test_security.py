"""Testes de unidade da camada de segurança (hashing, tokens, autenticação)."""

from __future__ import annotations

import time

import pytest

from app.application.use_cases import AuthenticateUser
from app.domain.entities import Role, User
from app.domain.errors import AuthenticationError
from app.infrastructure.persistence.memory import InMemoryUserRepository
from app.infrastructure.security.passwords import Pbkdf2PasswordHasher
from app.infrastructure.security.tokens import HmacJwtTokenService


def test_password_hash_roundtrip():
    hasher = Pbkdf2PasswordHasher(iterations=1_000)  # iterações baixas só para teste
    hashed = hasher.hash("s3nha-forte")

    assert hashed != "s3nha-forte"
    assert hasher.verify("s3nha-forte", hashed) is True
    assert hasher.verify("errada", hashed) is False


def test_password_verify_rejects_malformed_hash():
    hasher = Pbkdf2PasswordHasher(iterations=1_000)
    assert hasher.verify("x", "not-a-valid-hash") is False


def test_token_issue_and_decode_roundtrip():
    tokens = HmacJwtTokenService(secret="segredo", ttl_seconds=60)
    token = tokens.issue(subject="dra.souza", roles=["surgeon"])
    claims = tokens.decode(token)

    assert claims["sub"] == "dra.souza"
    assert claims["roles"] == ["surgeon"]


def test_token_tampering_is_rejected():
    tokens = HmacJwtTokenService(secret="segredo", ttl_seconds=60)
    token = tokens.issue(subject="dra.souza", roles=["surgeon"])
    header, payload, _signature = token.split(".")

    with pytest.raises(AuthenticationError):
        tokens.decode(f"{header}.{payload}.assinaturafalsa")


def test_token_with_different_secret_is_rejected():
    issued = HmacJwtTokenService(secret="segredo-a").issue(subject="x", roles=[])
    with pytest.raises(AuthenticationError):
        HmacJwtTokenService(secret="segredo-b").decode(issued)


def test_expired_token_is_rejected():
    tokens = HmacJwtTokenService(secret="segredo", ttl_seconds=-1)
    token = tokens.issue(subject="x", roles=[])
    time.sleep(0.01)
    with pytest.raises(AuthenticationError):
        tokens.decode(token)


def test_authenticate_user_success_and_failure():
    hasher = Pbkdf2PasswordHasher(iterations=1_000)
    users = InMemoryUserRepository(
        [
            User(
                username="dra.souza",
                password_hash=hasher.hash("pw"),
                roles=frozenset({Role.SURGEON}),
            )
        ]
    )
    tokens = HmacJwtTokenService(secret="segredo")
    use_case = AuthenticateUser(users=users, hasher=hasher, tokens=tokens)

    token = use_case.execute(username="dra.souza", password="pw")
    assert tokens.decode(token)["roles"] == ["surgeon"]

    with pytest.raises(AuthenticationError):
        use_case.execute(username="dra.souza", password="errada")
    with pytest.raises(AuthenticationError):
        use_case.execute(username="inexistente", password="pw")
