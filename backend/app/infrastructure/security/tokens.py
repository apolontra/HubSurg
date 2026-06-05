"""JWT HS256 implementado apenas com a stdlib (sem dependências nativas).

Cobre o necessário para o MVP: assinatura HMAC-SHA256, claims padrão (sub/iat/exp/iss) e
validação de expiração e integridade. Em produção, assinatura assimétrica (RS256) e
rotação de chaves são recomendadas; como isto implementa o port `TokenService`, a troca
não afeta domínio nem aplicação.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import time

from app.domain.errors import AuthenticationError
from app.domain.ports import TokenService


def _b64url_encode(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode("ascii")


def _b64url_decode(segment: str) -> bytes:
    padding = "=" * (-len(segment) % 4)
    return base64.urlsafe_b64decode(segment + padding)


class HmacJwtTokenService(TokenService):
    def __init__(self, *, secret: str, ttl_seconds: int = 3600, issuer: str = "hubsurg") -> None:
        if not secret:
            raise ValueError("segredo do token não pode ser vazio")
        self._secret = secret.encode("utf-8")
        self._ttl = ttl_seconds
        self._issuer = issuer

    def issue(self, *, subject: str, roles: list[str]) -> str:
        now = int(time.time())
        header = {"alg": "HS256", "typ": "JWT"}
        payload = {
            "sub": subject,
            "roles": roles,
            "iat": now,
            "exp": now + self._ttl,
            "iss": self._issuer,
        }
        signing_input = f"{self._encode(header)}.{self._encode(payload)}"
        signature = self._sign(signing_input)
        return f"{signing_input}.{signature}"

    def decode(self, token: str) -> dict:
        try:
            header_b64, payload_b64, signature = token.split(".")
        except ValueError as exc:
            raise AuthenticationError("token malformado") from exc

        expected = self._sign(f"{header_b64}.{payload_b64}")
        if not hmac.compare_digest(expected, signature):
            raise AuthenticationError("assinatura do token inválida")

        try:
            claims = json.loads(_b64url_decode(payload_b64))
        except (ValueError, json.JSONDecodeError) as exc:
            raise AuthenticationError("payload do token inválido") from exc

        if int(claims.get("exp", 0)) < int(time.time()):
            raise AuthenticationError("token expirado")
        return claims

    @staticmethod
    def _encode(data: dict) -> str:
        return _b64url_encode(json.dumps(data, separators=(",", ":")).encode("utf-8"))

    def _sign(self, signing_input: str) -> str:
        digest = hmac.new(self._secret, signing_input.encode("ascii"), hashlib.sha256).digest()
        return _b64url_encode(digest)
