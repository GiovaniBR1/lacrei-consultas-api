# ADR-0002: Render agora e blueprint AWS App Runner

- **Date**: 2026-08-13
- **Status**: Accepted
- **Deciders**: Tech Lead (desafio Back-end Lacrei Saúde)
- **Tags**: deploy, render, aws, app-runner

## Context and Problem Statement

O aceite pede staging e produção na AWS ou serviço equivalente. O prazo é de cinco dias úteis e o free tier importa. Provisionar App Runner, ECR e RDS agora adiciona conta AWS, IAM, networking e custo sem ganho no critério de aceite. O Postgres free da Render expira em cerca de 30 dias: o plano precisa dizer o que acontece depois.

## Decision Drivers

- Aceite permite equivalente à AWS
- Sem conta AWS e sem custo nesta entrega
- Isolamento real de dados entre staging e produção no futuro
- Caminho de upgrade quando o Postgres free expirar
- AD-003: Render provisionado em 2026-08-14 (URLs em README / deploy-render.md)

## Considered Options

- Render agora (2 Web Services + 1 Postgres free compartilhado); AWS só como blueprint
- Provisionar AWS App Runner + ECR + RDS ×2 nesta entrega
- Um único ambiente Render (sem staging)

## Decision Outcome

Chosen option: **Render agora; AWS só blueprint**, because AD-002. Deploy oficial: dois Web Services Docker (`api-staging`, `api-prod`) e um Postgres free compartilhado. Passos no runbook `docs/deploy-render.md`. Sem `render.yaml` na raiz (AD-028). AWS continua **não** provisionada.

Evolução AWS (documentada, não criada):

1. **ECR** — uma imagem por SHA (o job `build` do CI já tagueia `consultas-api:${{ github.sha }}`).
2. **App Runner** — um serviço por ambiente, apontando para a imagem no ECR.
3. **RDS** — um PostgreSQL **por ambiente** (RDS ×2). Isola dados. Elimina o atalho do Postgres compartilhado.

Quando o Postgres free expirar (~30 dias): (1) upgrade do mesmo serviço Render para plano pago **antes** do expiry, ou (2) segundo banco pago só para produção, ou (3) migrar para o blueprint AWS acima. O caminho (3) é o único que isola staging e produção de verdade.

O Django lê `DJANGO_SETTINGS_MODULE` (`config.settings.staging` / `production`). Não existe setting `ENVIRONMENT`.

### Positive Consequences

- Entrega cabe no free tier e no prazo
- Staging e produção Live com smoke `/ready/` 200 (2026-08-14)
- O blueprint AWS deixa claro o isolamento que o free tier não dá

### Negative Consequences

- Staging e produção compartilham o mesmo banco até o upgrade
- Cold start ~15 min idle no Web Service free
- Ensaio deliberado de Rollback no Dashboard permanece opcional pós-Live

## Pros and Cons of the Options

### Render agora + blueprint AWS ✅ Chosen

- ✅ Equivale ao aceite sem conta AWS
- ✅ Runbook e CI já existem
- ❌ Um Postgres compartilhado; expiry ~30 dias

### Provisionar App Runner + ECR + RDS agora

- ✅ Isolamento RDS por ambiente desde o dia 1
- ❌ Conta, IAM, VPC e custo fora do caminho crítico
- ❌ Viola a decisão de não provisionar AWS nesta entrega

### Um único ambiente Render

- ✅ Menos superfície operacional
- ❌ Não atende staging + produção do enunciado

## Links

- Runbook: [docs/deploy-render.md](../deploy-render.md)
- AD-002, AD-003, AD-011, AD-028 em `.specs/STATE.md`
- App Runner: [docs.aws.amazon.com/apprunner](https://docs.aws.amazon.com/apprunner/latest/dg/what-is-apprunner.html)
- ECR: [docs.aws.amazon.com/ecr](https://docs.aws.amazon.com/AmazonECR/latest/userguide/what-is-ecr.html)
- RDS: [docs.aws.amazon.com/rds](https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/CHAP_PostgreSQL.html)
