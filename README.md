# Consultas API — Lacrei Saúde

API REST de gerenciamento de consultas médicas (desafio Tech Lead / Back-end).

Django 5.2 LTS · DRF · SimpleJWT · PostgreSQL 16 · Poetry · Docker · GitHub Actions

## Avaliando em três comandos

```bash
cp .env.example .env
make migrate          # cria o schema
make seed             # usuário + 2 profissionais + 3 consultas + 1 cobrança PENDENTE
poetry run python manage.py runserver
```

O `seed` imprime as credenciais. Com o servidor no ar:

```bash
# 1. Trocar credenciais por tokens
curl -sX POST http://localhost:8000/api/v1/auth/token/ \
  -H 'Content-Type: application/json' \
  -d '{"username":"operadora","password":"lacrei-local-123"}'

# 2. Listar profissionais com o access token
curl -s http://localhost:8000/api/v1/profissionais/ \
  -H "Authorization: Bearer <access>"
```

Documentação interativa em `http://localhost:8000/api/docs/` · schema em `/api/schema/`.

Com Docker (Postgres 16):

```bash
cp .env.example .env
make up
make migrate
make seed
```

## Contrato em uma tela

| Rota | O que faz |
| --- | --- |
| `POST /api/v1/auth/token/` · `/refresh/` | Emite e renova o par de tokens JWT |
| `/api/v1/profissionais/` | CRUD de profissionais (nome social, profissão, endereço, contato) |
| `/api/v1/consultas/` | CRUD de consultas, busca por profissional, status e janela de data |
| `POST /api/v1/consultas/{id}/cobrancas/` | Cria cobrança mock (JWT + `Idempotency-Key`) |
| `POST /webhooks/asaas/` | Webhook Asaas (`asaas-access-token`, sem JWT) |
| `GET /health/` · `GET /ready/` | Liveness e readiness (abertas, para as probes da plataforma) |
| `GET /api/docs/` · `/api/schema/` | Swagger UI e OpenAPI 3 (desligáveis em produção) |

Listagens são paginadas: `{count, next, previous, results}`, com `page` e `page_size` (default 20, teto 100).

Erros usam sempre o mesmo envelope:

```json
{ "code": "consulta_conflito", "detail": "...", "errors": {} }
```

Regra de agenda: dois agendamentos no mesmo horário para o mesmo profissional colidem no banco e devolvem **409 `consulta_conflito`** — a constraint é a fonte da verdade, não uma checagem em Python.

## Comandos

| Comando | Efeito |
| --- | --- |
| `make test` | Suíte completa (`APITestCase`) |
| `make test-cov` | Suíte + cobertura com gate de 75% |
| `make lint` | `ruff check` + `ruff format --check` |
| `make check-deploy` | `manage.py check --deploy` com settings de produção |
| `make migrate` / `make seed` | Schema e dados de exemplo |
| `make up` / `make down` | Ambiente Docker |

## Documentação

| Documento | Conteúdo |
| --- | --- |
| [`docs/dominio.md`](docs/dominio.md) | Modelo, endpoints, anti–double booking, cobrança/webhook, timezone, política de migrations |
| [`docs/seguranca.md`](docs/seguranca.md) | JWT, throttle, CORS, logs sem PII, privacidade, mapa OWASP API Top 10 |
| [`docs/adr/0001-asaas-mock-first.md`](docs/adr/0001-asaas-mock-first.md) | Asaas mock-first, split `percentualValue`, webhook idempotente |
| [`docs/testes.md`](docs/testes.md) | Estratégia de teste, rastreabilidade e o gate de cobertura |

Decisões de arquitetura e o histórico do processo ficam em `.specs/` na raiz do workspace.

**Deploy Render:** pendente (AD-003) — configurar em sessão futura.
