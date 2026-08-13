# Decision log

Pivôs de arquitetura com data. O catálogo normativo é `.specs/STATE.md` (AD-NNN) e `docs/adr/`. Este arquivo é a narrativa curta para o revisor.

## 2026-08-12 — Render no lugar da AWS no caminho crítico

O aceite diz “AWS ou serviço equivalente”. Provisionar App Runner+ECR+RDS no prazo de 5 dias era networking, não produto. Deploy oficial = Render (2 Web + 1 Postgres free). AWS ficou blueprint (ADR-0002, AD-002).

## 2026-08-12 — Asaas mock-first, não sandbox no Dia 1

KYC e subconta bloqueiam liquidação real. O diferencial de TL é o contrato (`split`, webhook, CONFIRMED≠RECEIVED), não a TED. Mock atrás de `PaymentGateway` (AD-004, ADR-0001).

## 2026-08-12 — Hexagonal só em `payments/`

Hexagonal em todo o monólito atrasaria o CRUD. Porta só onde o provedor externo muda (AD-001).

## 2026-08-12 — SQLite no host, Postgres 16 obrigatório no CI

Docker ausente na máquina de desenvolvimento. O índice parcial do anti–double booking funciona no SQLite. Dialeto de produção entra no GitHub Actions (AD-017, AD-024 fechado na Fase 7).

## 2026-08-13 — Um Postgres free compartilhado entre staging e produção

O free tier Render permite um DB free. Isolar ambientes exigiria plano pago ou AWS. Trade-off explícito: ~30 dias, seed de staging suja produção, upgrade documentado (AD-002, AD-028).

## 2026-08-13 — Gitleaks allowlist só `.env.example`

Placeholders honestos (`SECRET_KEY=dev-only-...`) disparavam o detector. Esconder o scan seria pior. Allowlist mínima (AD-027).
