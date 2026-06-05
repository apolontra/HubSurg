"""Composition root: monta os adaptadores concretos e os expõe como um container.

Trocar implementações (ex.: in-memory → PostgreSQL, PBKDF2 → bcrypt) acontece apenas aqui;
o resto da aplicação depende somente dos ports.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.config import Settings, get_settings
from app.domain.ports import (
    ConsentRepository,
    ConsentValidatorPort,
    DiagnosticReportRepository,
    FhirGateway,
    PasswordHasher,
    PatientRepository,
    SurgicalCaseRepository,
    TokenService,
    UserRepository,
)
from app.infrastructure.consent.validator import RepositoryConsentValidator
from app.infrastructure.fhir.gateway import LocalFhirGateway
from app.infrastructure.persistence.memory import (
    InMemoryConsentRepository,
    InMemoryDiagnosticReportRepository,
    InMemoryPatientRepository,
    InMemorySurgicalCaseRepository,
    InMemoryUserRepository,
)
from app.infrastructure.security.passwords import Pbkdf2PasswordHasher
from app.infrastructure.security.seeds import seed_users
from app.infrastructure.security.tokens import HmacJwtTokenService


@dataclass(frozen=True)
class Container:
    patients: PatientRepository
    cases: SurgicalCaseRepository
    reports: DiagnosticReportRepository
    fhir: FhirGateway
    users: UserRepository
    hasher: PasswordHasher
    tokens: TokenService
    consents: ConsentRepository
    consent_validator: ConsentValidatorPort


def build_container(settings: Settings | None = None) -> Container:
    settings = settings or get_settings()
    hasher = Pbkdf2PasswordHasher()
    tokens = HmacJwtTokenService(
        secret=settings.jwt_secret,
        ttl_seconds=settings.jwt_ttl_seconds,
    )
    consents = InMemoryConsentRepository()
    return Container(
        patients=InMemoryPatientRepository(),
        cases=InMemorySurgicalCaseRepository(),
        reports=InMemoryDiagnosticReportRepository(),
        fhir=LocalFhirGateway(),
        users=InMemoryUserRepository(seed_users(hasher)),
        hasher=hasher,
        tokens=tokens,
        consents=consents,
        consent_validator=RepositoryConsentValidator(consents),
    )
