# Deploy Render (plano)

Este documento é o runbook da topologia **2 Web Services + 1 Postgres free**. Serviços provisionados em 2026-08-14 (Oregon). Não há `render.yaml` na raiz de propósito (AD-028): um Blueprint ligado ao Git provisionaria recursos.

| Ambiente | URL HTTPS |
| --- | --- |
| Staging (`api-staging`) | https://api-staging-4gl6.onrender.com |
| Produção (`api-prod`) | https://api-prod-745u.onrender.com |

Health check da plataforma: `GET /health/` (liveness, sem DB). Smoke pós-deploy: `GET /ready/` (readiness com `SELECT 1`).

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

O `CMD` do `Dockerfile` já roda `migrate --noinput`, `collectstatic --noinput` e sobe o gunicorn (workers = `WEB_CONCURRENCY`, default 1).

**Docker Command no Dashboard: deixe vazio.** Override do CMD é incomum no Render e é a causa mais comum de `Exited with status 128` sem traceback Python (quoting/`sh -c` mal colado). O build pode estar OK e o start morrer na hora.

Se precisar override (não recomendado), use **uma** linha no formato da [doc Render](https://render.com/docs/docker):

```bash
/bin/sh -c "python manage.py migrate --noinput && python manage.py collectstatic --noinput && gunicorn config.wsgi:application --bind 0.0.0.0:$PORT --workers ${WEB_CONCURRENCY:-1} --timeout 60"
```

Alternativa: Pre-Deploy Command só com migrate/collectstatic e Docker Command vazio (CMD do Dockerfile sobe o gunicorn). Confirme no plano se Pre-Deploy está disponível.

WhiteNoise serve `STATIC_ROOT`. Sem `collectstatic`, a API sobe mas estáticos de admin/schema podem faltar.

O processo escuta `0.0.0.0:$PORT` (Render injeta `PORT`).

## 5. Smoke `/ready/`

```bash
curl -sfS "https://api-staging-4gl6.onrender.com/ready/"
curl -sfS "https://api-prod-745u.onrender.com/ready/"
```

Esperado: HTTP 200. Verificado em 2026-08-14 (também `/health/`, 2 rodadas). JWT não é exigido em `/ready/` (probe). Smoke autenticado (`POST /api/v1/auth/token/` + listagem) é opcional e depende do usuário do `make seed` **somente em staging** (401 se o seed ainda não rodou no Postgres compartilhado).

## 6. Trade-offs do free tier (honestos)

Staging e produção **compartilham o mesmo Postgres free**. Não há isolamento de dados entre ambientes: um `make seed` em staging suja o mesmo banco que a API de produção usa. Isso cabe no desafio (~30 dias de avaliação) e não cabe em produto real.

O plano Free do Postgres na Render **expira em cerca de 30 dias**. Caminho de upgrade: (1) migrar o mesmo serviço para um plano pago **antes** do expiry, ou (2) provisionar um segundo banco e apontar só produção para ele. O blueprint AWS (ADR-0002) isola RDS por ambiente e elimina esse atalho.

Web Service free **hiberna depois de ~15 min idle** (cold start). A primeira request após o sono pode levar dezenas de segundos. O health check `/health/` não consulta o banco: a plataforma não deve marcar o serviço como morto só porque o Postgres ainda não respondeu. O smoke `/ready/` é que prova o DB; espere o wake-up.
