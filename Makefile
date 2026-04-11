SHELL := /bin/bash

.PHONY: help install test api frontend run security audit load-test clean

API_HOST ?= 127.0.0.1
API_PORT ?= 8000
STREAMLIT_PORT ?= 8501
DATABASE_PATH ?= data/team_mood_tracker.sqlite3
API_URL ?= http://$(API_HOST):$(API_PORT)

help:
	@echo "Available commands:"
	@echo "  make install   Install Poetry dependencies"
	@echo "  make test      Run pytest"
	@echo "  make api       Run FastAPI backend"
	@echo "  make frontend  Run Streamlit frontend"
	@echo "  make run       Run backend and frontend together"
	@echo "  make security  Run bandit on src/"
	@echo "  make audit     Run pip-audit inside the Poetry environment"
	@echo "  make load-test Run the Locust performance smoke test"
	@echo "  make clean     Remove local caches"

install:
	poetry install

test:
	poetry run pytest

api:
	TEAM_MOOD_DATABASE_PATH="$(DATABASE_PATH)" poetry run uvicorn team_mood_tracker.backend.app:app --reload --host "$(API_HOST)" --port "$(API_PORT)"

frontend:
	TEAM_MOOD_API_URL="$(API_URL)" poetry run streamlit run src/team_mood_tracker/frontend/app.py --server.address "$(API_HOST)" --server.port "$(STREAMLIT_PORT)"

run:
	@echo "Backend:  $(API_URL)"
	@echo "Frontend: http://$(API_HOST):$(STREAMLIT_PORT)"
	@TEAM_MOOD_DATABASE_PATH="$(DATABASE_PATH)" poetry run uvicorn team_mood_tracker.backend.app:app --reload --host "$(API_HOST)" --port "$(API_PORT)" & \
	api_pid=$$!; \
	TEAM_MOOD_API_URL="$(API_URL)" poetry run streamlit run src/team_mood_tracker/frontend/app.py --server.address "$(API_HOST)" --server.port "$(STREAMLIT_PORT)" & \
	ui_pid=$$!; \
	trap 'kill $$api_pid $$ui_pid 2>/dev/null || true' INT TERM EXIT; \
	wait -n $$api_pid $$ui_pid; \
	status=$$?; \
	kill $$api_pid $$ui_pid 2>/dev/null || true; \
	wait $$api_pid $$ui_pid 2>/dev/null || true; \
	exit $$status

security:
	poetry run bandit -r src

audit:
	poetry run pip-audit

load-test:
	@echo "Load testing $(API_URL)"
	@TEAM_MOOD_DATABASE_PATH="$(DATABASE_PATH)" poetry run uvicorn team_mood_tracker.backend.app:app --host "$(API_HOST)" --port "$(API_PORT)" & \
	api_pid=$$!; \
	trap 'kill $$api_pid 2>/dev/null || true' INT TERM EXIT; \
	until curl -fsS "$(API_URL)/health" >/dev/null; do sleep 1; done; \
	poetry run locust -f locustfile.py --host "$(API_URL)" --headless -u 10 -r 1 -t 30s; \
	status=$$?; \
	kill $$api_pid 2>/dev/null || true; \
	wait $$api_pid 2>/dev/null || true; \
	exit $$status

clean:
	find . -name __pycache__ -type d -prune -exec rm -rf {} +
	rm -rf .pytest_cache .ruff_cache .mypy_cache htmlcov .coverage
