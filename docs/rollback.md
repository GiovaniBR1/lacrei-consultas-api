# Rollback Render (plano)

Este documento descreve como **voltar a API** para um commit/release anterior no Render. **Não execute** enquanto AD-003 estiver ativo. Não há evidência real nesta sessão.

Alvo preferencial de ensaio: Web Service `api-staging`. Produção (`api-prod`) segue o mesmo procedimento só depois de staging comprovado.

## Identificador (AD-029)

O alvo do rollback é um **git SHA** (40 hex ou o curto que o Render mostra) e/ou o **deploy id** imutável daquele deploy. Anote os dois antes de clicar.

A tag **`latest` é proibida como único identificador**. `latest` se move. “Rollback para latest” não é reproduzível nem auditável.

## Passos (Dashboard — não executar agora)

1. Abra o Web Service (`api-staging` primeiro).
2. Abra a lista de **Deploys** (histórico).
3. Localize o deploy **anterior ao ruim** pelo SHA (ou pelo deploy id). Confira a data.
4. Dispare **Rollback** nesse deploy, ou **Manual Deploy** fixando o mesmo SHA. Não escolha “latest”.
5. Espere o health check `/health/` passar. O smoke `/ready/` só depois de AD-003 (Fase 8).
6. Preencha o slot de evidência (seção posterior; valores `pendente` até existir URL real).

Se o deploy anterior **não** estiver na lista (retention curta do free tier), o fallback é um novo deploy **do mesmo SHA** a partir do GitHub, ainda assim identificando o SHA — nunca `latest`.
