# ADR 0001 - Monorepo e Estrategia Hibrida

Status: Aprovado
Data: 2026-03-22

## Contexto
O produto precisa nascer com capacidade Desktop + SaaS, preservando paridade com Excel e integrando CQT, tracao e CAD.

## Decisao
Adotar monorepo com separacao por apps e packages:
- apps/api
- apps/web
- apps/desktop
- packages/domain
- packages/application
- packages/infrastructure
- packages/shared

## Consequencias
- Facilita compartilhamento de tipos e regras de dominio.
- Exige governanca forte para evitar acoplamento indevido.
- Permite evolucao incremental de single-user local para colaboracao cloud.
