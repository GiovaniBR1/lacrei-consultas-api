# Entrega Tech Lead — respostas (template)

**Destino futuro:** `desenvolvimento.humano@lacreisaude.com.br`  
**Repo proposto:** `lacrei-consultas-api` (AD-013)  
**Nota:** o texto original das 6 perguntas do e-mail **não está neste repositório**. Este documento segue o template do roadmap. Se o e-mail divergir, atualizar aqui **antes** de enviar (AD-013). **Não enviar automaticamente.**

URLs:

- Staging: https://api-staging-4gl6.onrender.com
- Produção: https://api-prod-745u.onrender.com

Repo público: https://github.com/GiovaniBR1/lacrei-consultas-api

---

## 1. Por que Tech Lead / voluntariado

Quero o desafio de Back-end porque o aceite pede engenharia de produto (domínio, segurança, operação), não só CRUD. Voluntariar na Lacrei Saúde é aplicar essa engenharia onde o dado é sensível por padrão: nome social, minimização, logs sem PII. O prazo de 5 dias força escolhas; as escolhas estão nos ADRs, não em slide.

## 2. Arquitetura

Monólito modular Django (DRF). Porta hexagonal **somente** em `apps/payments/` para isolar Asaas. O restante é ViewSet → Serializer → Model. Webhook é borda síncrona com idempotência, sem bus interno. Detalhe em [`docs/arquitetura.md`](arquitetura.md) e ADR-0001 / ADR-0002.

## 3. Qualidade e testes

`APITestCase` cobre sucesso, 401, 409 de agenda, replay de webhook e privacidade de campos. Gate local: 75% de cobertura em `apps/` (real ~97%). CI: ruff → `check --deploy` + gitleaks + pip-audit → Postgres 16 → `docker build` com tag SHA. Suíte local em SQLite (AD-017); dialeto de produção no CI.

## 4. Segurança e LGPD-light

JWT single-tenant (ADR-0003). Só `nome_social`; sem CPF, orientação, nome civil. Hard-delete com trilha financeira em PROTECT (ADR-0005). Checklist honesta em [`docs/seguranca.md`](seguranca.md): isolamento stg/prod está ❌ porque o Postgres free é compartilhado.

## 5. Deploy e rollback

Deploy oficial: Render Live (staging + produção), 2 Web Services + 1 Postgres free. AWS: blueprint App Runner + ECR + RDS ×2, **não provisionado**. Runbooks: [`docs/deploy-render.md`](deploy-render.md), [`docs/rollback.md`](rollback.md). Rollback por git SHA / deploy id (AD-029); `latest` sozinho é proibida. Smoke `/health/` + `/ready/` 200 nos dois hosts (2026-08-14). Ensaio de Rollback no Dashboard: opcional (procedimento documentado).

## 6. Alinhamento com a missão LGBTQIAPN+

A API trata profissional pelo **nome social**. Não coleta dado que oute. Timezone de Brasília (ADR-0004) e Unicode no nome não são “detalhe de i18n”: são o mínimo para a pessoa aparecer como ela se nomeia. Non-goals (prontuário, CID, orientação) estão escritos para ninguém “completar” o modelo por curiosidade.

---

## Rascunho de e-mail (não enviar)

Para: `desenvolvimento.humano@lacreisaude.com.br`  
Assunto: Desafio Tech Lead Back-end — API de consultas (`lacrei-consultas-api`)

```
Olá,

Segue o desafio de Back-end (Tech Lead / voluntariado).

- Repositório: https://github.com/GiovaniBR1/lacrei-consultas-api
- Staging HTTPS: https://api-staging-4gl6.onrender.com
- Produção HTTPS: https://api-prod-745u.onrender.com
- Docs de entrega: docs/entrega-tech-lead.md
- Rollback: docs/rollback.md

Smoke: GET /health/ e GET /ready/ → 200 em staging e produção.

Atenciosamente,
```

Este rascunho **não deve ser enviado** por agente ou script. Envio é ação humana.
