# Rollback Render (plano)

Este documento descreve como **voltar a API** para um commit/release anterior no Render.

Alvo preferencial de ensaio: Web Service `api-staging` (https://api-staging-4gl6.onrender.com). Produção (`api-prod`, https://api-prod-745u.onrender.com) segue o mesmo procedimento.

## Identificador (AD-029)

O alvo do rollback é um **git SHA** (40 hex ou o curto que o Render mostra) e/ou o **deploy id** imutável daquele deploy. Anote os dois antes de clicar.

A tag **`latest` é proibida como único identificador**. `latest` se move. “Rollback para latest” não é reproduzível nem auditável.

## Passos (Dashboard — não executar agora)

1. Abra o Web Service (`api-staging` primeiro).
2. Abra a lista de **Deploys** (histórico).
3. Localize o deploy **anterior ao ruim** pelo SHA (ou pelo deploy id). Confira a data.
4. Dispare **Rollback** nesse deploy, ou **Manual Deploy** fixando o mesmo SHA. Não escolha “latest”.
5. Espere o health check `/health/` passar e confirme `GET /ready/` → 200.
6. Preencha o slot de evidência (seção posterior) após um ensaio real no Dashboard.

Se o deploy anterior **não** estiver na lista (retention curta do free tier), o fallback é um novo deploy **do mesmo SHA** a partir do GitHub, ainda assim identificando o SHA — nunca `latest`.

## Schema: expand/contract

Rollback de **código** só é seguro se a release anterior ainda consegue ler o banco. A política está em [`docs/dominio.md`](dominio.md) (seção Migrations). Resumo operacional:

1. **Expand** — adicionar coluna/índice compatível (nullable ou com default). Deployar. Backfill se precisar. O binário antigo continua funcionando.
2. **Contract** — remover coluna/índice antigo só depois que nenhuma release ativa depende dele. Deploy separado.

Não faça `RemoveField` / `AlterField` destrutivo no mesmo deploy do código que passa a exigir o schema novo. Se fizer, o rollback do app encontra um banco que a versão anterior não sabe ler.

Regra prática: se o incidente é só de código, volte o SHA. Se o incidente é de schema já contraído, o rollback de app **não** desfaz a migration — aí o caminho é uma migration de avanço (forward-fix), não um rewind.

## Evidência

Serviços Live (2026-08-14). Ensaio deliberado de Rollback no Dashboard ainda não executado nesta sessão — preencha SHA/deploy id após o clique real.

| Campo | Valor |
| --- | --- |
| timestamp (ISO-8601, America/Sao_Paulo) | 2026-08-14T17:52:00-03:00 (Live + smoke; sem ensaio Rollback) |
| URL HTTPS de staging | https://api-staging-4gl6.onrender.com |
| URL HTTPS de produção | https://api-prod-745u.onrender.com |
| SHA Live (ambos) | `d5e6664` |
| deploy id produção (primeiro Live) | `dep-d9vnv60jo6nc73au86g0` |
| SHA before / after (ensaio Rollback) | pendente (ação humana no Dashboard) |
| deploy id before / after (ensaio Rollback) | pendente (ação humana no Dashboard) |

## Sentry (opcional)

`SENTRY_DSN` no env do Web Service. Se a variável estiver **ausente ou vazia**, pule: o plano de rollback não depende de error tracking. Se um DSN for fornecido depois, aponte o SDK ao mesmo DSN em staging primeiro.


