# ADR-0004: Timezone America/Sao_Paulo

- **Date**: 2026-08-13
- **Status**: Accepted
- **Deciders**: Tech Lead (desafio Back-end Lacrei Saúde)
- **Tags**: timezone, domain

## Context and Problem Statement

Consultas têm `data_hora`. Sem timezone explícito, “15h” muda de significado entre UTC e horário de Brasília e o anti–double booking compara instantes errados.

## Decision Drivers

- Público da Lacrei é Brasil
- Django `USE_TZ=True` é o default saudável
- Testes precisam de relógio determinístico

## Considered Options

- `TIME_ZONE=America/Sao_Paulo` + `USE_TZ=True` (AD-008)
- Tudo em UTC na API, conversão só no cliente
- Naive datetime sem tz

## Decision Outcome

Chosen option: **`America/Sao_Paulo` com `USE_TZ=True`**. O banco guarda UTC. A API devolve offset `-03:00` (ou `-02:00` no horário de verão, se voltar a vigorar). Consulta `agendada` rejeita `data_hora` no passado.

### Positive Consequences

- Slot de agenda é um instante, não um relógio de parede ambíguo
- OpenAPI e testes compartilham o mesmo relógio

### Negative Consequences

- Consumidor precisa respeitar offset; um cliente naive quebra

## Pros and Cons of the Options

### America/Sao_Paulo + USE_TZ ✅ Chosen

- ✅ Combina com o domínio e com inclusão (nome social Unicode no mesmo stack)
- ❌ Offset muda se o Brasil retomar DST

### UTC na borda

- ✅ Canônico para sistemas distribuídos
- ❌ Empurra a regra de negócio para o front, que esta entrega não tem

### Naive datetime

- ✅ Menos código
- ❌ Double booking mentiroso

## Links

- AD-008 em `.specs/STATE.md`
- `docs/dominio.md` § Timezone
