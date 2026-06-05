# HubSurg — Backend

API do **Dossiê Cirúrgico Centralizado** em **FastAPI**, seguindo a **arquitetura hexagonal**
descrita em [`docs/architecture/overview.md`](../docs/architecture/overview.md).

## Estado

Scaffold funcional do MVP. A persistência usa **repositórios in-memory** (adaptadores que
implementam os ports do domínio); o adaptador **PostgreSQL + pgvector** é uma substituição
futura localizada em `build_container()`, sem impacto no domínio. Ver
[ADR-0003](../docs/architecture/adr/0003-postgresql-pgvector.md).

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
│   └── http/               # FastAPI: routers, schemas, DI, container
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
pytest          # 15 testes: domínio, casos de uso, FHIR, API
ruff check .    # lint
```

## Endpoints principais

| Método | Rota | Descrição |
|--------|------|-----------|
| `GET` | `/health` | Liveness |
| `POST` | `/patients` | Registrar paciente |
| `GET` | `/patients` · `/patients/{id}` | Listar / obter paciente |
| `POST` | `/patients/{id}/cases` | Agendar caso cirúrgico |
| `POST` | `/patients/cases/{case_id}/reports` | Ingerir laudo (saída de OCR) |
| `GET` | `/patients/{id}/dossier` | Dossiê agregado (modelo interno) |
| `GET` | `/patients/{id}/dossier/fhir` | Dossiê como **FHIR R4 Bundle** |

## Exemplo rápido

```bash
# 1) criar paciente
curl -s -X POST localhost:8000/patients -H 'content-type: application/json' \
  -d '{"given_name":"Ana","family_name":"Souza","birth_date":"1980-05-01","mrn":"MRN-1"}'

# 2) exportar dossiê em FHIR
curl -s localhost:8000/patients/<PATIENT_ID>/dossier/fhir
```
