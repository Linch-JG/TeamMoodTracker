SHELL := /bin/bash

.PHONY: help install test api frontend run fresh seed security audit load-test coverage coverage-html type-check docs-check clean db-clean radon-cc radon-mi quality check

API_HOST ?= 127.0.0.1
API_PORT ?= 8000
STREAMLIT_PORT ?= 8501
DATABASE_PATH ?= data/team_mood_tracker.sqlite3
API_URL ?= http://$(API_HOST):$(API_PORT)

help:
	@echo "Available commands:"
	@echo "  make install      Install Poetry dependencies"
	@echo "  make test         Run pytest"
	@echo "  make coverage     Run pytest with coverage report"
	@echo "  make coverage-html Generate HTML coverage report"
	@echo "  make api          Run FastAPI backend"
	@echo "  make frontend     Run Streamlit frontend"
	@echo "  make run          Run backend and frontend together"
	@echo "  make db-clean     Remove local SQLite DB (fresh schema on next API start)"
	@echo "  make seed         Fill DB with mock mood entries (uses DATABASE_PATH)"
	@echo "  make fresh        db-clean, seed mock data, then run"
	@echo "  make security     Run bandit on src/"
	@echo "  make audit        Run pip-audit inside the Poetry environment"
	@echo "  make load-test    Run the Locust performance smoke test"
	@echo "  make type-check   Run mypy type checking for src/"
	@echo "  make docs-check   Run interrogate docstring coverage gate"
	@echo "  make radon-cc     radon cc -a -s src/"
	@echo "  make radon-mi     radon mi -s src/"
	@echo "  make quality      black + ruff + radon-cc (workflow style-checks)"
	@echo "  make check        all quality gates: style, radon mi, mypy, interrogate, bandit, pip-audit, tests, coverage"
	@echo "  make clean        Remove local caches"

install:
	poetry install

radon-cc:
	poetry run radon cc -a -s src/

radon-mi:
	poetry run radon mi -s src/

quality:
	poetry run black --check src/
	poetry run ruff check src/
	@$(MAKE) radon-cc

# Everything from TeamMoodTracker.pdf / CI except load-test (needs running API + Locust).
check:
	@$(MAKE) quality
	@$(MAKE) radon-mi
	@$(MAKE) type-check
	@$(MAKE) docs-check
	@$(MAKE) security
	@$(MAKE) audit
	@$(MAKE) test
	@$(MAKE) coverage

test:
	poetry run pytest tests/

coverage:
	poetry run pytest --cov=src --cov-report=term-missing --cov-fail-under=80

coverage-html:
	poetry run pytest --cov=src --cov-report=html
	@echo "Coverage report generated in htmlcov/index.html"

api:
	TEAM_MOOD_DATABASE_PATH="$(DATABASE_PATH)" poetry run uvicorn team_mood_tracker.backend.app:app --reload --host "$(API_HOST)" --port "$(API_PORT)"

frontend:
	TEAM_MOOD_API_URL="$(API_URL)" poetry run streamlit run src/team_mood_tracker/frontend/app.py --server.address "$(API_HOST)" --server.port "$(STREAMLIT_PORT)"

db-clean:
	rm -f "$(DATABASE_PATH)"
	@echo "Removed $(DATABASE_PATH)"

seed:
	TEAM_MOOD_DATABASE_PATH="$(DATABASE_PATH)" poetry run python scripts/seed_mock_data.py

fresh: db-clean seed run

run:
	@echo "Backend:  $(API_URL)"
	@echo "Frontend: http://$(API_HOST):$(STREAMLIT_PORT)"
	@TEAM_MOOD_DATABASE_PATH="$(DATABASE_PATH)" poetry run uvicorn team_mood_tracker.backend.app:app --reload --host "$(API_HOST)" --port "$(API_PORT)" & \
	api_pid=$$!; \
	TEAM_MOOD_API_URL="$(API_URL)" poetry run streamlit run src/team_mood_tracker/frontend/app.py --server.address "$(API_HOST)" --server.port "$(STREAMLIT_PORT)" & \
	ui_pid=$$!; \
	trap 'kill $$api_pid $$ui_pid 2>/dev/null || true' INT TERM EXIT; \
	while kill -0 $$api_pid 2>/dev/null && kill -0 $$ui_pid 2>/dev/null; do sleep 1; done; \
	if ! kill -0 $$api_pid 2>/dev/null; then \
		wait $$api_pid; \
		status=$$?; \
	else \
		wait $$ui_pid; \
		status=$$?; \
	fi; \
	kill $$api_pid $$ui_pid 2>/dev/null || true; \
	wait $$api_pid $$ui_pid 2>/dev/null || true; \
	exit $$status

security:
	poetry run bandit -r src/

audit:
	poetry run pip-audit

load-test:
	@echo "Load testing $(API_URL)"
	@TEAM_MOOD_DATABASE_PATH="$(DATABASE_PATH)" poetry run uvicorn team_mood_tracker.backend.app:app --host "$(API_HOST)" --port "$(API_PORT)" & \
	api_pid=$$!; \
	trap 'kill $$api_pid 2>/dev/null || true' INT TERM EXIT; \
	until curl -fsS "$(API_URL)/health" >/dev/null; do sleep 1; done; \
	poetry run locust -f locustfile.py --host "$(API_URL)" --headless -u 10 -r 1 -t 1m; \
	status=$$?; \
	kill $$api_pid 2>/dev/null || true; \
	wait $$api_pid 2>/dev/null || true; \
	exit $$status

type-check:
	poetry run mypy src

docs-check:
	poetry run interrogate -vv src

clean:
	find . -name __pycache__ -type d -prune -exec rm -rf {} +
	rm -rf .pytest_cache .ruff_cache .mypy_cache htmlcov .coverage
