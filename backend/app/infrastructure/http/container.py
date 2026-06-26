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
    EventBus,
    FhirGateway,
    LlmClient,
    PasswordHasher,
    PatientRepository,
    RiskEngine,
    SurgicalCaseRepository,
    TokenService,
    UserRepository,
)
from app.infrastructure.consent.validator import RepositoryConsentValidator
from app.infrastructure.events.bus import InMemoryEventBus
from app.infrastructure.fhir.gateway import LocalFhirGateway
from app.infrastructure.llm.anthropic_client import AnthropicLlmClient, UnavailableLlmClient
from app.infrastructure.persistence.memory import (
    InMemoryConsentRepository,
    InMemoryDiagnosticReportRepository,
    InMemoryPatientRepository,
    InMemorySurgicalCaseRepository,
    InMemoryUserRepository,
)
from app.infrastructure.risk.rule_based import RuleBasedRiskEngine
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
    risk_engine: RiskEngine
    events: EventBus
    llm: LlmClient


def _build_llm_client(settings: Settings) -> LlmClient:
    if settings.anthropic_api_key:
        return AnthropicLlmClient(
            api_key=settings.anthropic_api_key,
            model=settings.anthropic_model,
        )
    return UnavailableLlmClient()


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
        risk_engine=RuleBasedRiskEngine(),
        events=InMemoryEventBus(),
        llm=_build_llm_client(settings),
    )
