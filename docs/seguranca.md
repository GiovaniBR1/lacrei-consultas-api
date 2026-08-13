# Segurança e privacidade

Postura da Fase 3: a borda da API fecha por padrão. Tudo que não é probe de infraestrutura ou emissão de token exige Bearer JWT válido.

## Autenticação

| Item | Valor |
| --- | --- |
| Esquema | JWT Bearer (SimpleJWT) |
| Emissão | `POST /api/v1/auth/token/` (`username`, `password`) |
| Renovação | `POST /api/v1/auth/token/refresh/` (`refresh`) |
| TTL do access | 30 minutos |
| TTL do refresh | 1 dia, com rotação |
| Revogação | `ROTATE_REFRESH_TOKENS` + `BLACKLIST_AFTER_ROTATION` |

Fluxo:

```bash
# 1. Trocar credenciais por par de tokens
curl -sX POST https://<host>/api/v1/auth/token/ \
  -H 'Content-Type: application/json' \
  -d '{"username":"operadora","password":"..."}'
# -> {"access":"eyJhbGciOi...","refresh":"eyJhbGciOi..."}

# 2. Usar o access em toda chamada de domínio
curl -s https://<host>/api/v1/profissionais/ \
  -H 'Authorization: Bearer eyJhbGciOi...'
```

Cada refresh bem-sucedido devolve um par novo e coloca o refresh anterior na blacklist. Reapresentar um refresh já rotacionado devolve 401 — isso limita a janela de um token vazado e é coberto por teste (`apps/accounts/tests/test_auth.py`).

O usuário de bootstrap sai do `make seed`; não há cadastro público (AD-006).

## Autorização

`DEFAULT_PERMISSION_CLASSES = ["rest_framework.permissions.IsAuthenticated"]`. Sem token, qualquer rota de domínio devolve o envelope padrão com 401:

```json
{ "code": "not_authenticated", "detail": "...", "errors": {} }
```

Ficam abertas de propósito apenas:

| Rota | Motivo |
| --- | --- |
| `POST /api/v1/auth/token/` e `/refresh/` | É onde a credencial vira token |
| `GET /health/`, `GET /ready/` | Probes de liveness/readiness do Render (AD-011) |
| `POST /webhooks/asaas/` | O Asaas não envia JWT; autentica pelo header `asaas-access-token` |

**Single-tenant, declarado honestamente (AD-006)**: todo usuário autenticado enxerga todos os profissionais e consultas. Não há isolamento por clínica nem RBAC fino — é uma API administrativa interna. Multi-tenant é non-goal consciente desta entrega, não um esquecimento.

## Rate limiting

| Escopo | Taxa | Aplica a |
| --- | --- | --- |
| `auth_token` | 5/min | `POST /api/v1/auth/token/` (`ScopedRateThrottle`) |
| `asaas_webhook` | 60/min | `POST /webhooks/asaas/` (`ScopedRateThrottle`) |
| `user` | 120/min | Tráfego autenticado, por usuário |
| `anon` | 20/min | Tráfego anônimo, por IP |

Estourar o limite devolve 429 com `code=throttled`. O endpoint de credenciais tem escopo próprio, mais estrito, porque é o alvo natural de brute force — e a contagem dele é independente do CRUD.

`/health/` e `/ready/` são isentos de throttle (`throttle_classes = []`). Sem essa isenção, probes a cada poucos segundos vindos do mesmo IP interno estourariam a taxa `anon` e o Render leria a API como fora do ar (AD-020).

**Limitação honesta**: o throttle usa o cache default do Django (`LocMemCache`), que é por processo. Com mais de um worker Gunicorn ou mais de uma instância no Render, o limite efetivo é a taxa multiplicada pelo número de processos. Resolver de verdade exige cache compartilhado (Redis), que está fora do escopo do desafio; o comportamento e o custo estão registrados aqui em vez de escondidos.

## CORS e hardening por ambiente

| Setting | local | staging | production |
| --- | --- | --- | --- |
| `DEBUG` | `True` | `False` | `False` |
| `CORS_ALLOW_ALL_ORIGINS` | `True` | `False` | `False` |
| `CORS_ALLOWED_ORIGINS` | — | env allowlist | env allowlist |
| `SECURE_PROXY_SSL_HEADER` | — | `("HTTP_X_FORWARDED_PROTO", "https")` | idem |
| `SECURE_SSL_REDIRECT` / cookies `Secure` | — | `True` | `True` |
| HSTS | — | — | 1 ano, `includeSubDomains`, `preload` |

A allowlist vem de `CORS_ALLOWED_ORIGINS` no ambiente; origem fora da lista faz o preflight do browser falhar e a chamada não sai. `CORS_ALLOW_CREDENTIALS = False`: o token viaja em header, não em cookie, então não há necessidade de credenciais cross-origin nem superfície de CSRF na API.

`config/tests/test_settings.py` trava esses valores por teste — se alguém reabrir CORS ou religar `DEBUG` em staging/produção, a suíte quebra.

### `check --deploy`

```bash
make check-deploy
# System check identified no issues (0 silenced).
```

O alvo roda `manage.py check --deploy --settings=config.settings.production` com `SECRET_KEY` e `ALLOWED_HOSTS` dummy — ele valida os settings, nunca toca no ambiente real. **Não há waivers**: os três avisos que existiam foram resolvidos na origem (`SECURE_HSTS_PRELOAD` ligado; probes com `@extend_schema`, que silencia o fallback de serializer do drf-spectacular). Na Fase 7 esse alvo entra no CI.

`SECRET_KEY`, `DATABASE_URL` e credenciais Asaas só existem como variáveis de ambiente. Nenhum segredo está versionado; `.env` está no `.gitignore` e o repositório carrega apenas `.env.example`.

## Logs

Uma linha INFO por requisição, emitida pelo `RequestIdMiddleware`:

```
INFO request_id=6f1c... apps.core.request method=GET path=/api/v1/consultas/ status=200 duration_ms=12
```

O que **não** entra no log, por construção: headers (portanto nenhum `Authorization`), corpo da requisição, corpo da resposta e query string. O `request_id` correlaciona a linha com o header `X-Request-ID` devolvido ao cliente — dá para rastrear uma chamada ponta a ponta sem carregar dado pessoal para o agregador de logs.

O teste `AccessLogTests.test_authorization_nao_aparece_no_log` envia um Bearer e falha se o token ou a palavra `Bearer` aparecerem na saída.

## Privacidade e política de exclusão

O modelo `Profissional` guarda apenas nome social, profissão, endereço, contato e a wallet opcional do Asaas. Não existe nome civil, CPF, data de nascimento, gênero ou orientação — minimização de dado é a principal defesa contra outing involuntário (AD-010).

`apps/profissionais/tests/test_privacidade.py` congela esse conjunto de campos: acrescentar coluna nova ao modelo quebra o teste e força uma revisão de privacidade consciente, em vez de o campo entrar de carona num PR de feature.

Exclusão: `DELETE` de profissional ou consulta com cobrança vinculada (qualquer status) devolve 409 `profissional_com_cobranca` / `consulta_com_cobranca` (AD-026). Sem cobrança, excluir profissional cascateia as consultas (AD-015). A trilha financeira começa no create: uma cobrança PENDENTE já trava o delete.

Não há soft-delete nem lixeira: exclusão é definitiva, o que atende ao direito de eliminação da LGPD e é registrado como trade-off (perda de histórico).

## Mapa OWASP API Security Top 10

| Risco | Situação nesta entrega |
| --- | --- |
| API1 Broken Object Level Authorization | Não aplicável por desenho: single-tenant, todo autenticado vê tudo (AD-006). Vira risco real no dia em que houver multi-tenant |
| API2 Broken Authentication | JWT com TTL curto, rotação e blacklist; throttle dedicado no endpoint de credenciais |
| API3 Broken Object Property Level Authorization | Serializers com campos explícitos; `contato` sai da listagem e só aparece no detalhe |
| API4 Unrestricted Resource Consumption | Throttle por usuário/anônimo **e** paginação com teto de 100 por página (Fase 5). Resíduo: cache de throttle por processo |
| API5 Broken Function Level Authorization | Permissão default fail-closed; exceções (token, probes, webhook Asaas) são explícitas e testadas. O webhook não aceita JWT no lugar do `asaas-access-token` |
| API6 Unrestricted Access to Sensitive Business Flows | Anti–double booking no banco (`UniqueConstraint` parcial) impede corrida de agendamento |
| API7 SSRF | Nenhuma URL fornecida pelo cliente é buscada pelo servidor. O webhook é inbound: validamos o token, não fazemos fetch. Extra JSON é ignorado; o body não é persistido |
| API8 Security Misconfiguration | `check --deploy` sem issues, settings por ambiente travados por teste, `DEBUG=False` fora do local |
| API9 Improper Inventory Management | Rotas versionadas em `/api/v1/`; OpenAPI em local/staging; webhook documentado fora de `/api/v1/` |
| API10 Unsafe Consumption of APIs | Mock não chama rede. Webhook: `compare_digest` no token, UNIQUE em `event.id`, máquina monotônica CONFIRMED≠RECEIVED. Replay devolve 200 sem reaplicar |

## Limitações honestas desta fase

| Limitação | Onde resolve |
| --- | --- |
| Throttle conta por processo (`LocMemCache`) | Redis, fora do escopo do desafio |
| Documentação (`/api/docs/`, `/api/schema/`) é inventário de API; fica desligada em produção por `SPECTACULAR_ENABLED` (AD-025) | Decisão consciente |
| Sem RBAC/multi-tenant (AD-006) | Non-goal declarado |
| ~~Bloqueio de exclusão com cobrança~~ — 409 `profissional_com_cobranca` / `consulta_com_cobranca` (AD-026) | Fase 6 ✔ |
| Suíte roda em SQLite no host local (AD-017) | Fase 7 (CI em Postgres 16) |

## Checklist de segurança (honesta)

Itens desta entrega, não um ASVS completo. ❌ não é esquecimento: é limite consciente.

| Controle | Status | Nota |
| --- | --- | --- |
| JWT + refresh com rotação/blacklist | ✅ | AD-006, ADR-0003 |
| Serializers explícitos (sem `__all__` em write) | ✅ | |
| Secrets só em env; `.env` gitignored | ✅ | `.env.example` sem segredos |
| `check --deploy` sem waivers | ✅ | CI job security |
| Logs sem PII/tokens + `X-Request-ID` | ✅ | |
| Minimização: só `nome_social`, sem CPF/orientação | ✅ | AD-010 |
| Webhook `compare_digest` + idempotência | ✅ | |
| CORS allowlist fora do local | ✅ | |
| Isolamento de dados staging vs produção | ❌ | Um Postgres free compartilhado (AD-002); ~30 dias |
| Multi-tenant / RBAC fino | ❌ | Non-goal (AD-006) |
| Redis para throttle compartilhado | ❌ | LocMemCache por processo (AD-022) |
| Soft-delete / lixeira | ❌ | Hard-delete (ADR-0005) |
| URLs Render com `/ready/` 200 | ❌ | Bloqueado AD-003 |
| Sentry | ❌ | Opcional; DSN ausente = pular |

