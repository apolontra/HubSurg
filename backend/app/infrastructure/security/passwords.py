"""Hashing de senha com PBKDF2-HMAC-SHA256 (apenas stdlib).

PBKDF2 é um KDF de senha legítimo (com sal e fator de trabalho), ao contrário de SHA-256
"cru". Em produção, bcrypt/argon2 são preferíveis; trocar é localizado, pois esta classe
implementa o port `PasswordHasher`. Ver docs/security/privacy-and-security.md.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import os

from app.domain.ports import PasswordHasher

_ALGORITHM = "pbkdf2_sha256"


def _b64encode(raw: bytes) -> str:
    return base64.b64encode(raw).decode("ascii")


def _b64decode(text: str) -> bytes:
    return base64.b64decode(text.encode("ascii"))


class Pbkdf2PasswordHasher(PasswordHasher):
    def __init__(self, iterations: int = 240_000, salt_bytes: int = 16) -> None:
        self._iterations = iterations
        self._salt_bytes = salt_bytes

    def hash(self, plain: str) -> str:
        salt = os.urandom(self._salt_bytes)
        derived = self._derive(plain, salt, self._iterations)
        return f"{_ALGORITHM}${self._iterations}${_b64encode(salt)}${_b64encode(derived)}"

    def verify(self, plain: str, hashed: str) -> bool:
        try:
            algorithm, iterations, salt_b64, derived_b64 = hashed.split("$")
            if algorithm != _ALGORITHM:
                return False
            expected = _b64decode(derived_b64)
            candidate = self._derive(plain, _b64decode(salt_b64), int(iterations))
        except (ValueError, TypeError):
            return False
        return hmac.compare_digest(candidate, expected)

    @staticmethod
    def _derive(plain: str, salt: bytes, iterations: int) -> bytes:
        return hashlib.pbkdf2_hmac("sha256", plain.encode("utf-8"), salt, iterations)
