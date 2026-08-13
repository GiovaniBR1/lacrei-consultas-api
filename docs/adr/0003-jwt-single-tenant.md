# ADR-0003: JWT single-tenant administrativo

- **Date**: 2026-08-13
- **Status**: Accepted
- **Deciders**: Tech Lead (desafio Back-end Lacrei Saúde)
- **Tags**: auth, jwt, authorization

## Context and Problem Statement

O enunciado pede autenticação básica. Multi-tenant e RBAC fino não cabem no prazo e não estão no aceite. A API é administrativa: a operadora da clínica vê o conjunto inteiro.

## Decision Drivers

- Auth observável em OpenAPI e testes (401 sem token)
- Bootstrap sem cadastro público
- Menor superfície no MVP

## Considered Options

- JWT SimpleJWT + `IsAuthenticated` em todo o domínio (AD-006)
- API keys estáticas
- RBAC por papel (admin / profissional / paciente)

## Decision Outcome

Chosen option: **JWT Bearer (SimpleJWT)** with default `IsAuthenticated`. Emissão em `POST /api/v1/auth/token/`. Refresh com rotação e blacklist. Usuário inicial via `make seed`. Probes e webhook Asaas ficam de fora de propósito.

Não há isolamento por clínica. Todo autenticado lê e escreve o mesmo conjunto. Isso é single-tenant declarado, não IDOR esquecido.

### Positive Consequences

- Contrato 401/refresh testável
- Sem cadastro aberto na internet

### Negative Consequences

- Sem RBAC; o dia do multi-tenant exige reescrita de permissão

## Pros and Cons of the Options

### JWT single-tenant ✅ Chosen

- ✅ Atende o enunciado sem teatro de papéis
- ❌ Qualquer leak de credencial da operadora vê tudo

### API keys

- ✅ Simples
- ❌ Sem expiração/rotação nativa

### RBAC fino

- ✅ Prepararia produto
- ❌ Fora do prazo e do aceite

## Links

- AD-006, AD-022 em `.specs/STATE.md`
- `docs/seguranca.md`
