# Consultas API — Lacrei Saúde

API REST de gerenciamento de consultas médicas (desafio Tech Lead / Back-end).

## Quickstart local

```bash
cp .env.example .env
poetry install
poetry run python manage.py migrate
poetry run python manage.py runserver
```

Com Docker (recomendado, Postgres 16):

```bash
cp .env.example .env
make up
make migrate
```

- Liveness: `GET /health/`
- Readiness: `GET /ready/`

Stack e decisões: ver `Tech Lead/roadmap.md` e `.specs/` na raiz do workspace.

**Deploy Render:** pendente (AD-003) — configurar em sessão futura.
