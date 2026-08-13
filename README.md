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

## CI

O quality gate está em `.github/workflows/ci.yml` (push/PR em `main`):

1. **lint** — `ruff check .` e `ruff format --check .`
2. **security** — `manage.py check --deploy` (settings de produção + env dummy), gitleaks (`--redact`, allowlist só `.env.example`) e `pip-audit` (falha em qualquer advisory)
3. **test** — service `postgres:16` + `DATABASE_URL` + suíte Django
4. **build** — `docker build -t consultas-api:${{ github.sha }} .`
5. **deploy** — só `workflow_dispatch`; se `RENDER_DEPLOY_HOOK` estiver vazio, o job sai 0 (AD-003)

Local continua SQLite (AD-017). Postgres 16 é obrigação do CI.

O badge abaixo usa o nome proposto do repositório público (`lacrei-consultas-api`, AD-013). Só fica verde depois do remote e do primeiro push:

`https://github.com/<owner>/lacrei-consultas-api/actions/workflows/ci.yml/badge.svg`

Smoke de `/ready/` nas URLs Render: ver runbook; execução bloqueada por AD-003.

## Por que Render + blueprint AWS

O aceite pede staging e produção na AWS **ou serviço equivalente**. O deploy oficial desta entrega é o [Render](https://render.com): dois Web Services (`api-staging`, `api-prod`) e **um** Postgres free compartilhado. AWS fica só como evolução: App Runner + ECR + RDS isolado por ambiente. Nada disso é provisionado agora (AD-003).

Passos (Dashboard, sem Blueprint aplicável): [`docs/deploy-render.md`](docs/deploy-render.md). Decisão e caminho AWS: [`docs/adr/0002-render-e-blueprint-aws.md`](docs/adr/0002-render-e-blueprint-aws.md).

| Ambiente | URL HTTPS | Status |
| --- | --- | --- |
| Staging (`api-staging`) | pendente | AD-003 — não inventar host `onrender.com` |
| Produção (`api-prod`) | pendente | AD-003 — não inventar host `onrender.com` |

Trade-offs conscientes do free tier: um único banco entre staging e produção; expiry ~30 dias; cold start após ~15 min idle. Isolamento real de dados entra no blueprint AWS (RDS ×2).

## Documentação

| Documento | Conteúdo |
| --- | --- |
| [`docs/dominio.md`](docs/dominio.md) | Modelo, endpoints, anti–double booking, cobrança/webhook, timezone, política de migrations |
| [`docs/seguranca.md`](docs/seguranca.md) | JWT, throttle, CORS, logs sem PII, privacidade, mapa OWASP API Top 10 |
| [`docs/adr/0001-asaas-mock-first.md`](docs/adr/0001-asaas-mock-first.md) | Asaas mock-first, split `percentualValue`, webhook idempotente |
| [`docs/adr/0002-render-e-blueprint-aws.md`](docs/adr/0002-render-e-blueprint-aws.md) | Render agora; App Runner + ECR + RDS ×2 depois |
| [`docs/deploy-render.md`](docs/deploy-render.md) | Runbook Render (não executar enquanto AD-003) |
| [`docs/testes.md`](docs/testes.md) | Estratégia de teste, rastreabilidade e o gate de cobertura |

Decisões de arquitetura e o histórico do processo ficam em `.specs/` na raiz do workspace.
