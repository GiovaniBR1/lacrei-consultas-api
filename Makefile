.PHONY: up down test test-cov lint migrate seed check-deploy

PYTHON ?= .venv/Scripts/python.exe
RUFF ?= .venv/Scripts/ruff.exe

up:
	docker compose up --build -d

down:
	docker compose down

test:
	$(PYTHON) manage.py test --settings=config.settings.local

test-cov:
	$(PYTHON) -m coverage run manage.py test --settings=config.settings.local
	$(PYTHON) -m coverage report

lint:
	$(RUFF) check .
	$(RUFF) format --check .

migrate:
	$(PYTHON) manage.py migrate --settings=config.settings.local

seed:
	$(PYTHON) manage.py seed --settings=config.settings.local

# Valores dummy: o alvo só exercita os settings de produção, nunca toca no ambiente real.
check-deploy: export SECRET_KEY=check-deploy-dummy-0123456789abcdefghijklmnopqrstuvwxyz-0123456789
check-deploy: export ALLOWED_HOSTS=example.com
check-deploy:
	$(PYTHON) manage.py check --deploy --settings=config.settings.production
