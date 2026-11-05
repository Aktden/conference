PYTHON ?= python3
VENV_PY := .venv/bin/python
.PHONY: help setup run check test format build release-check api-test quality-check performance security-check deps-check backup restore ports-check logs-check docker-build docker-up docker-down deploy restart check-deploy logs clean
help:
	@echo "setup run check test format build release-check api-test quality-check performance security-check deps-check backup restore ports-check logs-check docker-build docker-up docker-down deploy restart check-deploy logs clean"
setup:
	$(PYTHON) -m venv .venv
	$(VENV_PY) -m pip install -r requirements-dev.txt
	@test -f .env || cp .env.example .env
run:
	$(VENV_PY) main.py
check:
	$(VENV_PY) scripts/manage.py check
test api-test:
	$(VENV_PY) scripts/manage.py test
format:
	$(VENV_PY) scripts/manage.py format
build:
	$(VENV_PY) scripts/manage.py build
release-check: check build
quality-check: check
performance:
	$(VENV_PY) scripts/manage.py performance
security-check:
	$(VENV_PY) scripts/manage.py security
deps-check:
	$(VENV_PY) scripts/manage.py deps
backup:
	$(VENV_PY) scripts/manage.py backup
restore:
	$(VENV_PY) scripts/manage.py restore "$(FILE)" --target "$(TARGET)" --confirm RESTORE
ports-check:
	$(VENV_PY) scripts/manage.py ports
logs-check:
	$(VENV_PY) scripts/manage.py logs
docker-build:
	docker compose build
docker-up deploy:
	docker compose up --build -d
docker-down:
	docker compose down
restart:
	docker compose restart app
check-deploy:
	$(VENV_PY) scripts/manage.py health
logs:
	docker compose logs --tail=100 -f
clean:
	$(PYTHON) -c "import pathlib,shutil; [shutil.rmtree(p) for p in (pathlib.Path('.pytest_cache'),pathlib.Path('.ruff_cache')) if p.exists()]"
