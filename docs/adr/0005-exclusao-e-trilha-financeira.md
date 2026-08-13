# ADR-0005: Exclusão hard-delete e trilha financeira

- **Date**: 2026-08-13
- **Status**: Accepted
- **Deciders**: Tech Lead (desafio Back-end Lacrei Saúde)
- **Tags**: privacy, deletion, payments

## Context and Problem Statement

LGPD pede eliminação. Saúde LGBTQIAPN+ pede não acumular dado que oute. Ao mesmo tempo, cobrança Asaas precisa de trilha: apagar a consulta depois do split apaga o contexto financeiro.

## Decision Drivers

- Minimização (só `nome_social`, sem CPF/orientação)
- Direito de eliminação sem lixeira cosmética
- Integridade da cobrança (AD-010, AD-026)

## Considered Options

- Hard-delete; `Cobranca.consulta` com `PROTECT` para qualquer status
- Soft-delete + lixeira
- PROTECT só para CONFIRMADA/RECEBIDA

## Decision Outcome

Chosen option: **hard-delete** of profissional/consulta, blocked by `ProtectedError` → HTTP 409 (`profissional_com_cobranca` / `consulta_com_cobranca`) when any `Cobranca` exists. Django não oferece PROTECT condicional; a trilha começa no create (AD-026). Sem cobrança, `Consulta.profissional` continua `CASCADE` (AD-015).

Não há soft-delete. Eliminação é definitiva.

### Positive Consequences

- Menos PII parado
- Teste de 409 é a prova, não um comentário

### Negative Consequences

- Cobrança PENDENTE também impede apagar
- Sem restore

## Pros and Cons of the Options

### Hard-delete + PROTECT amplo ✅ Chosen

- ✅ Simples de provar; honesto com LGPD-light
- ❌ PENDENTE trava o delete

### Soft-delete

- ✅ Restore
- ❌ Dado sensível continua no disco; fora do non-goal consciente

### PROTECT só após CONFIRMED

- ✅ Mais permissivo
- ❌ Django não expressa isso sem duplicar regra na view

## Links

- AD-010, AD-015, AD-026
- `docs/seguranca.md` § Privacidade
