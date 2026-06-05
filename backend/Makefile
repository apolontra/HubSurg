# Ritual de qualidade do backend. Espelha o CI (.github/workflows/backend-ci.yml).
# Invoca as ferramentas via `python -m` para garantir o mesmo interpretador/venv.
# Sobrescreva o interpretador com: make precheck PYTHON=python
PYTHON ?= python3

.PHONY: install typecheck lint test precheck run

install:
	$(PYTHON) -m pip install -e ".[dev]"

typecheck:
	$(PYTHON) -m mypy

lint:
	$(PYTHON) -m ruff check .

test:
	$(PYTHON) -m pytest -q

# Antes do PR: do mais barato/rápido ao mais caro. Para no primeiro erro
# (prerequisites rodam em ordem; make aborta na primeira falha).
precheck: typecheck lint test

run:
	$(PYTHON) -m uvicorn app.main:app --reload
