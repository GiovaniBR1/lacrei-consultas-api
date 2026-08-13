# Deploy Render (plano)

Este documento é o runbook da topologia **2 Web Services + 1 Postgres free**. **Não execute** os passos de create enquanto AD-003 estiver ativo. Não há `render.yaml` na raiz de propósito (AD-028): um Blueprint ligado ao Git provisionaria recursos.

URLs reais de staging e produção: **pendentes (AD-003)**. Não invente hostname `onrender.com`.

Health check da plataforma: `GET /health/` (liveness, sem DB). Smoke pós-deploy: `GET /ready/` (readiness com `SELECT 1`) — só depois de AD-003.

## 0. Pré-requisitos (quando desbloquear)

1. Repositório GitHub público (`lacrei-consultas-api`, AD-013) com o `Dockerfile` na raiz do repo da API.
2. Conta no [Render](https://dashboard.render.com) (região `oregon` ou a mais próxima; anote a escolhida).
3. Branch `main` para produção. Staging pode usar a mesma branch com serviço separado e `DJANGO_SETTINGS_MODULE` diferente, ou uma branch `staging` se existir.

## 1. Criar o Postgres free

No Dashboard: **New → PostgreSQL**.

| Campo | Valor |
| --- | --- |
| Name | `consultas-db` |
| Database | `consultas` |
| User | gerado pelo Render |
| Region | a mesma dos Web Services |
| Plan | **Free** |

Copie a **Internal Database URL** (não a External) para colar em `DATABASE_URL` dos dois serviços. Os dois Web Services apontam para **este único** banco.

## 2. Criar `api-staging`

**New → Web Service** → conecte o repo → runtime **Docker**.

| Campo | Valor |
| --- | --- |
| Name | `api-staging` |
| Language/Runtime | Docker (`Dockerfile` na raiz) |
| Branch | `main` (ou `staging`, se existir) |
| Health Check Path | `/health/` |
| Docker Command / Start | ver §4 |

Env vars **deste** serviço (Dashboard → Environment; `sync: false` mental: valores nunca no git):

| Chave | Valor de staging |
| --- | --- |
| `DJANGO_SETTINGS_MODULE` | `config.settings.staging` |
| `SECRET_KEY` | gerar no Dashboard; único; ≠ produção |
| `DEBUG` | `False` (o módulo staging já força False) |
| `ALLOWED_HOSTS` | hostname do serviço, quando existir |
| `DATABASE_URL` | Internal URL do `consultas-db` |
| `CORS_ALLOWED_ORIGINS` | origens reais do front de staging, ou vazio se só API |
| `ASAAS_MODE` | `mock` |
| `ASAAS_WEBHOOK_TOKEN` | token de staging, distinto do de prod |
| `ASAAS_WALLET_PLATFORM` | `wlt_platform_mock` |
| `ASAAS_API_KEY` | vazio no mock |
| `SPECTACULAR_ENABLED` | `True` (schema útil para o avaliador) |

Não use `ENVIRONMENT` como setting Django: o código lê `DJANGO_SETTINGS_MODULE`.

## 3. Criar `api-prod`

Repita o Web Service Docker com nome `api-staging` trocado por **`api-prod`**.

| Chave | Valor de produção |
| --- | --- |
| `DJANGO_SETTINGS_MODULE` | `config.settings.production` |
| `SECRET_KEY` | outro valor, gerado no Dashboard |
| `ALLOWED_HOSTS` | hostname de produção, quando existir |
| `DATABASE_URL` | **a mesma** Internal URL do `consultas-db` |
| `CORS_ALLOWED_ORIGINS` | allowlist de produção |
| `ASAAS_WEBHOOK_TOKEN` | token **distinto** do staging |
| `SPECTACULAR_ENABLED` | `False` (default de production.py, AD-025) |

`DEBUG` em produção é `False` no código. HSTS e cookies Secure já vêm de `config.settings.production`.

## 4. Migrate e collectstatic no release

O `Dockerfile` não roda migrate nem `collectstatic`. No Web Service, defina o **Start Command** (ou Pre-Deploy Command, se o plano oferecer) para:

```bash
sh -c "python manage.py migrate --noinput && python manage.py collectstatic --noinput && gunicorn config.wsgi:application --bind 0.0.0.0:${PORT:-8000} --workers 2 --timeout 60"
```

WhiteNoise serve `STATIC_ROOT`. Sem `collectstatic`, o deploy Docker sobe a API mas os estáticos de admin/schema podem faltar.

O processo escuta `0.0.0.0:$PORT` (Render injeta `PORT`).

## 5. Smoke `/ready/` (bloqueado)

Quando AD-003 for limpo e os hostnames existirem:

```bash
curl -sfS "https://<hostname-staging>/ready/"
curl -sfS "https://<hostname-prod>/ready/"
```

Esperado: HTTP 200. Não cole URL inventada no README. JWT não é exigido em `/ready/` (probe). Um smoke autenticado extra (`POST /api/v1/auth/token/` + listagem) é opcional e usa o usuário do `make seed` **somente em staging**.

## 6. Trade-offs do free tier (honestos)

Staging e produção **compartilham o mesmo Postgres free**. Não há isolamento de dados entre ambientes: um `make seed` em staging suja o mesmo banco que a API de produção usa. Isso cabe no desafio (~30 dias de avaliação) e não cabe em produto real.

O plano Free do Postgres na Render **expira em cerca de 30 dias**. Caminho de upgrade: (1) migrar o mesmo serviço para um plano pago **antes** do expiry, ou (2) provisionar um segundo banco e apontar só produção para ele. O blueprint AWS (ADR-0002) isola RDS por ambiente e elimina esse atalho.

Web Service free **hiberna depois de ~15 min idle** (cold start). A primeira request após o sono pode levar dezenas de segundos. O health check `/health/` não consulta o banco: a plataforma não deve marcar o serviço como morto só porque o Postgres ainda não respondeu. O smoke `/ready/` é que prova o DB; espere o wake-up.
