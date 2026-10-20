# Altars — Demo Editorial (Repositório de Leitura)

Este repositório contém o código-fonte e documentação do Altars, um demo editorial que prova a pipeline completa (recolha → classificação → redacção → alerta → composição) ao Esteves Francisco.

## O que está aqui

- **Design system + UI:** `design/` (index.html, styles.css, app.js, design-system.md, check_contrast.py)
- **Textos e microcopy:** `escritor/` (microcopy-ui.md, estruturas-editoriais.md, export-artigos-pipeline.md, 01-microcopy-interface.md)
- **Arquitetura e plano:** `adr/` (ADR-ALT-2026-001-demo-editorial.md), `plano-execucao.md`
- **Documentação de implementação:** `pipeline/` (recoletor.py, busca.py, classificador.py, compositor.py, db.py)

## O que NÃO está aqui

- **Banco de dados** (4.5 MB): `pipeline/data/altars.db` — dados arquivados da recolha, não público neste repo.
- **Credenciais e tokens:** Telegram bot token, API keys de fontes externas — apenas referência em texto em `plano-execucao.md` (ver §6).

## Como usar este repo

Este repo é de **leitura apenas**. O demo completo e funcional (incluindo o painel, alertas e exportações) é publicado apenas **após aprovação dos Gates 2 (QA + Segurança)** e do dono (Belmiro). Até lá, este repo serve como referência técnica e documentação.

## Estado do código (20/10/2026)

A app está funcional e verificada: `app/server.py` (FastAPI + SQLite) serve os 4 ecrãs e a API do ciclo completo. Correcções fechadas face à auditoria de QA v2: bug de import (P0), UI ligada à exportação real (P1), PNG/JPG via `pdftoppm` (P1), sanitização A1 (P2), JPG (P2). Telegram fica por configurar (deploy). Provas em `qa/verificacao-dev-2026-10-20.md`.

## Links

- **Preview interno (noindex):** pendente de publicação — a plataforma de hosting atingiu o limite de 25 sites. O URL será `https://altars-demo-preview-sites.tivrai.dev/` quando o slot for libertado (ver `deploy/DIAGNOSTICO-522.md`).
- **Demo final (após aprovação):** URL será definida pela plataforma Tivra após aprovação do dono.

## Licença

Este projeto é parte da demo editorial Altars (PRD-ALT-2026-002) — uso restrito à equipa Tivra e ao Esteves Francisco.
