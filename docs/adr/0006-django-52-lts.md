# ADR-0006: Django 5.2 LTS

- **Date**: 2026-08-13
- **Status**: Accepted
- **Deciders**: Tech Lead (desafio Back-end Lacrei Saúde)
- **Tags**: stack, django, lts

## Context and Problem Statement

O desafio pede Django. Latest (6.x) muda o contrato no meio da janela de avaliação. LTS comunica estabilidade num review de Tech Lead.

## Decision Drivers

- Pin do roadmap §7, validado no PyPI em 2026-08-12
- Suporte de segurança até ~2028
- DRF 3.18.0 compatível

## Considered Options

- Django **5.2.17** LTS (AD-005)
- Django 6.1 latest
- Django 4.2 LTS anterior

## Decision Outcome

Chosen option: **Django 5.2 LTS** (`Django==5.2.17` no pin). Python 3.12 no Poetry; o host local pode ser 3.13 no `.venv` sem mudar o pin. Postgres 16 no CI e no Compose.

Não sobe para 6.x nesta entrega.

### Positive Consequences

- Sinal de LTS no README
- Menos surpresa de breaking change durante a avaliação (~30 dias do Postgres free)

### Negative Consequences

- Não usa o latest; features novas do 6.x ficam de fora

## Pros and Cons of the Options

### Django 5.2 LTS ✅ Chosen

- ✅ Estabilidade vs prazo de 5 dias
- ❌ Não é a linha de frente

### Django 6.1

- ✅ Novidades
- ❌ Risco de churn no meio do desafio

### Django 4.2 LTS

- ✅ Ainda suportado um tempo
- ❌ Já é geração anterior; o pin 5.2 é o LTS corrente

## Links

- AD-005 em `.specs/STATE.md`
- `pyproject.toml`
