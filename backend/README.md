# HubSurg — Backend

API do **Dossiê Cirúrgico Centralizado** em **FastAPI**, seguindo a **arquitetura hexagonal**
descrita em [`docs/architecture/overview.md`](../docs/architecture/overview.md).

## Estado

Scaffold funcional do MVP. A persistência usa **repositórios in-memory** (adaptadores que
implementam os ports do domínio); o adaptador **PostgreSQL + pgvector** é uma substituição
futura localizada em `build_container()`, sem impacto no domínio. Ver
[ADR-0003](../docs/architecture/adr/0003-postgresql-pgvector.md).

Inclui uma **camada de segurança** (JWT, RBAC, rate limiting, cabeçalhos de proteção)
implementada apenas com a stdlib — ver [ADR-0006](../docs/architecture/adr/0006-camada-de-seguranca.md).

## Estrutura

```
app/
├── domain/                 # núcleo: entidades, regras e ports (sem dependências externas)
│   ├── entities.py
│   ├── errors.py
│   └── ports.py
├── application/            # casos de uso que orquestram os ports
│   └── use_cases/
├── infrastructure/         # adaptadores que implementam os ports
│   ├── persistence/        # repositórios in-memory
│   ├── fhir/               # mapeadores e gateway FHIR R4
│   ├── security/           # PBKDF2 (senhas), JWT HS256 (tokens), seeds
│   ├── consent/            # validador de consentimento LGPD
│   └── http/               # FastAPI: routers, schemas, DI, container, middleware
├── config.py
└── main.py                 # create_app() — composition root
tests/                      # domínio, casos de uso, mapeadores FHIR, API
```

A **regra de dependência** aponta para dentro: `infrastructure → application → domain`.

## Como rodar

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"          # ou: pip install -r requirements.txt

uvicorn app.main:app --reload    # API em http://127.0.0.1:8000
```

Documentação interativa: `http://127.0.0.1:8000/docs`.

## Testes e lint

```bash
pytest          # 45 testes: domínio, casos de uso, FHIR, segurança, consentimento, API
ruff check .    # lint
```

## Segurança

- **Autenticação:** JWT (HS256) emitido em `POST /auth/token`; enviar `Authorization: Bearer <token>`.
- **RBAC:** papéis `surgeon`, `assistant`, `admin`. Registrar/agendar exige `surgeon`;
  leitura do dossiê exige papel clínico (`surgeon`/`assistant`).
- **Consentimento LGPD:** acesso a dados de um paciente exige consentimento por `acao:Recurso`
  (ex.: `read:Patient`), capturado em `POST /patients/{id}/consent`. Ver
  [ADR-0007](../docs/architecture/adr/0007-consentimento-lgpd-e-meta-security.md).
- **Confidencialidade:** `Patient.confidentiality` (N/R/V) → `Patient.meta.security` na saída FHIR.
- **Hashing de senha:** PBKDF2-HMAC-SHA256 (port `PasswordHasher`; trocável por bcrypt/argon2).
- **Rate limiting** e **cabeçalhos de proteção** (CSP, HSTS, X-Frame-Options, nosniff) via middleware.

> Implementado **sem dependências nativas** (apenas stdlib), contornando libs de cripto
> indisponíveis no ambiente. Detalhes e limites em
> [ADR-0006](../docs/architecture/adr/0006-camada-de-seguranca.md).

### Credenciais de desenvolvimento

Apenas para uso local (ver `app/infrastructure/security/seeds.py`):

| Usuário | Senha | Papel |
|---------|-------|-------|
| `dra.souza` | `surgeon-pass` | surgeon |
| `assist.lima` | `assistant-pass` | assistant |
| `admin` | `admin-pass` | admin |

## Endpoints principais

| Método | Rota | Papel exigido | Descrição |
|--------|------|---------------|-----------|
| `GET` | `/health` | — | Liveness |
| `POST` | `/auth/token` | — | Emitir token de acesso |
| `POST` | `/patients` | surgeon | Registrar paciente |
| `POST` | `/patients/{id}/consent` | surgeon | Capturar consentimento LGPD |
| `GET` | `/patients` | surgeon/assistant | Listar pacientes |
| `GET` | `/patients/{id}` | surgeon/assistant + consent `read:Patient` | Obter paciente |
| `POST` | `/patients/{id}/cases` | surgeon + consent `write:Patient` | Agendar caso cirúrgico |
| `POST` | `/patients/cases/{case_id}/reports` | surgeon/assistant | Ingerir laudo (saída de OCR) |
| `GET` | `/patients/{id}/dossier` | surgeon/assistant + consent `read:Patient` | Dossiê agregado |
| `GET` | `/patients/{id}/dossier/fhir` | surgeon/assistant + consent `read:Patient` | Dossiê como **FHIR R4 Bundle** |

## Exemplo rápido

```bash
# 1) autenticar
TOKEN=$(curl -s -X POST localhost:8000/auth/token -H 'content-type: application/json' \
  -d '{"username":"dra.souza","password":"surgeon-pass"}' | python -c 'import sys,json;print(json.load(sys.stdin)["access_token"])')

# 2) criar paciente
PID=$(curl -s -X POST localhost:8000/patients -H "authorization: Bearer $TOKEN" \
  -H 'content-type: application/json' \
  -d '{"given_name":"Ana","family_name":"Souza","birth_date":"1980-05-01","mrn":"MRN-1"}' \
  | python -c 'import sys,json;print(json.load(sys.stdin)["id"])')

# 3) capturar consentimento LGPD (necessário para ler/escrever dados do paciente)
curl -s -X POST localhost:8000/patients/$PID/consent -H "authorization: Bearer $TOKEN" \
  -H 'content-type: application/json' -d '{"scopes":["read:Patient","write:Patient"]}'

# 4) exportar dossiê em FHIR
curl -s -H "authorization: Bearer $TOKEN" localhost:8000/patients/$PID/dossier/fhir
```
