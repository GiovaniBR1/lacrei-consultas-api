# Estratégia de testes

82 testes, 99% de cobertura nos apps, gate em 75%. Este documento explica o que a suíte prova, o que ela ainda não prova e por quê.

## Como rodar

```bash
make test        # suíte completa
make test-cov    # suíte + relatório de cobertura + gate de 75%
make lint        # ruff check + format --check
make check-deploy  # settings de produção sob check --deploy
```

O runner é o `manage.py test` com `APITestCase`, como o enunciado pede — sem pytest, para manter a stack próxima do Django puro.

## Pirâmide adotada

| Camada | O que prova | Onde |
| --- | --- | --- |
| Unidade | Serializers, `__str__`, envelope de erro, schema de privacidade, settings de ambiente | `test_serializers.py`, `test_models.py`, `test_core.py`, `test_privacidade.py`, `config/tests/` |
| Integração de banco | Constraint parcial de agenda direto no banco, sem passar pela view | `apps/consultas/tests/test_models.py` |
| API | CRUD, filtros, códigos de erro, auth e throttle pelo caminho HTTP real | `test_api.py`, `test_filters.py`, `apps/accounts/tests/` |

A base é larga em unidade, mas o **contrato** — status code e envelope — é sempre verificado no nível HTTP. Um teste que só chama o serializer não prova que o cliente recebe 409.

## Rastreabilidade: requisito → teste

| Requisito | Prova executável |
| --- | --- |
| TEST-01 CRUD profissionais | `apps/profissionais/tests/test_api.py::ProfissionalApiTests` (create/list/retrieve/patch/delete + cascade) |
| TEST-02 CRUD e busca de consultas | `apps/consultas/tests/test_api.py` + `test_filters.py` (filtro por profissional, status, janela de data, ordering) |
| TEST-03 400 / 401 / 404 | `test_api.py::test_create_sem_campo_obrigatorio_retorna_400_com_envelope`, `apps/accounts/tests/test_auth.py::PermissaoDefaultTests`, `test_api.py::test_retrieve_de_id_inexistente_retorna_404_com_envelope` |
| TEST-04 409 double booking | `apps/consultas/tests/test_api.py` (HTTP) + `test_models.py` (constraint) + `test_views.py` (o `IntegrityError` que **não** é conflito sobe intacto) |
| TEST-05 Postgres | ✅ Job `test` do GHA com service `postgres:16` (host local continua SQLite, AD-017) |
| TEST-06 Cobertura ≥ 75% | `make test-cov` → 99% real, gate em 75% |

## Cobertura

Medida com `coverage.py` sobre `apps/`, **omitindo** testes, migrations e `apps.py`: medir o próprio teste infla o número e um gate que se auto-satisfaz não protege nada.

O piso é 75% (número da spec), com folga grande sobre os 99% atuais. A folga é intencional: o gate existe para pegar regressão, não para virar meta a ser perseguida com teste cosmético.

Única linha descoberta: `apps/core/exceptions.py:57`, fallback defensivo para um `detail` que não é dict nem list — forma que o DRF não produz no contrato atual.

**Cobertura não é garantia.** A prova de que a suíte discrimina defeito vem do sensor do Verifier, que injeta falhas reais (reabrir permissão, desligar blacklist, vazar `Authorization` no log, acrescentar `cpf` ao modelo) e confirma que a suíte fica vermelha. Está registrado nos `validation.md` de cada fase.

## TEST-05: Postgres no CI

A suíte local continua em **SQLite** (AD-017). O quality gate real usa Postgres 16:

- Host: `make test` sem `DATABASE_URL` → SQLite. A unique parcial de agenda continua sendo honrada.
- CI: job `test` em `.github/workflows/ci.yml` sobe `postgres:16` e exporta `DATABASE_URL`. É aí que o dialeto (tipos, transação) entra.

O comando de teste já respeita `DATABASE_URL`; no GitHub Actions a variável aponta para o service container.

Smoke de `/ready/` contra URLs Render **não** entra neste gate local. Verificado em 2026-08-14: staging e produção → HTTP 200.

## Convenções

- Nomes de teste em pt-BR descrevendo o comportamento esperado, não o método chamado.
- Asserts sobre `response.json()`, nunca sobre o objeto interno do DRF: é o cliente que importa.
- Testes de erro conferem `code` **e** o shape do envelope `{code, detail, errors}`.
- Testes que dependem de cache (throttle) limpam o cache no `setUp`.
