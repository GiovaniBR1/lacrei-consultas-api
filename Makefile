.PHONY: up down test lint migrate seed

PYTHON ?= .venv/Scripts/python.exe
RUFF ?= .venv/Scripts/ruff.exe

up:
	docker compose up --build -d

down:
	docker compose down

test:
	$(PYTHON) manage.py test --settings=config.settings.local

lint:
	$(RUFF) check .
	$(RUFF) format --check .

migrate:
	$(PYTHON) manage.py migrate --settings=config.settings.local

seed:
	$(PYTHON) manage.py seed --settings=config.settings.local
