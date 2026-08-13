# ADR-0001: Asaas mock-first

- **Date**: 2026-08-13
- **Status**: Accepted
- **Deciders**: Tech Lead (desafio Back-end Lacrei Saúde)
- **Tags**: payments, asaas, integration

## Context and Problem Statement

O bônus do desafio pede split Asaas ligado a consultas e profissionais. KYC, subconta e liquidação real não cabem no prazo. O mock precisa ser fiel o bastante para um avaliador reconhecer o contrato oficial: campo de split, webhook autenticado, CONFIRMED ≠ RECEIVED e idempotência.

## Decision Drivers

- Entrega em 5 dias sem depender de conta Asaas aprovada
- Contrato observável em testes (não um stub vazio)
- Credenciais só em secrets/env
- Isolar o provedor atrás de uma porta (AD-001)

## Considered Options

- Mock contratual agora; sandbox/prod como flag (`ImproperlyConfigured`)
- Cliente HTTP sandbox nesta entrega
- Sem pagamentos (só CRUD)

## Decision Outcome

Chosen option: **mock contratual agora**, because AD-004/AD-012. `PaymentGateway` em `apps/payments/`; `ASAAS_MODE=mock` é o único modo implementado. Sandbox e produção existem como flag e falham cedo.

O campo canônico de request é **`split`** (OpenAPI de criar cobrança). A documentação narrativa às vezes usa `splits`. O mock fala `split`. Split do MVP é só `percentualValue`. A wallet da conta emissora (`ASAAS_WALLET_PLATFORM`) não entra no array. `netValue` fictício é 95% do bruto.

Webhook em `POST /webhooks/asaas/`, fora do JWT. Auth pelo header `asaas-access-token` comparado com `ASAAS_WEBHOOK_TOKEN` (`compare_digest`). Token vazio é fail-closed (401). Replay do `event.id` devolve 200 e não reaplica transição. Corpo do evento não é persistido.

`Cobranca.consulta` usa `PROTECT` para qualquer status (AD-026). DELETE vira 409 `consulta_com_cobranca` / `profissional_com_cobranca`.

### Positive Consequences

- A suíte prova o contrato sem rede e sem KYC
- Trocar o mock por um cliente HTTP no futuro não muda as views

### Negative Consequences

- Sem liquidação real; drift se o OpenAPI Asaas mudar
- Staging/prod com `ASAAS_MODE` diferente de `mock` não sobem até existir cliente real

## Pros and Cons of the Options

### Mock contratual agora ✅ Chosen

- ✅ Demonstra porta hexagonal, webhook e split no prazo
- ✅ Segredos ficam fora do repo
- ❌ Não liquida dinheiro de verdade

### Cliente HTTP sandbox nesta entrega

- ✅ Exercitaria TLS e payload real
- ❌ KYC/subconta bloqueiam; `httpx` fica reservado

### Sem pagamentos

- ✅ Menos código
- ❌ Perde o diferencial de Tech Lead pedido no enunciado

## Links

- Split: [docs.asaas.com/docs/split-de-pagamentos](https://docs.asaas.com/docs/split-de-pagamentos) e [payment-split-overview](https://docs.asaas.com/docs/payment-split-overview)
- Ambiguidade `split` / `splits`: o guia de split cita o array `splits`; o OpenAPI de criar cobrança usa `split`. Esta API envia `split` (AD-012)
- Webhook: [receive events](https://docs.asaas.com/docs/receive-asaas-events-at-your-webhook-endpoint) (`asaas-access-token`, entrega at-least-once)
- Idempotência de webhook: [how-to-implement-idempotence-in-webhooks](https://docs.asaas.com/docs/how-to-implement-idempotence-in-webhooks)
- AD-001, AD-004, AD-012, AD-026 em `.specs/STATE.md`
