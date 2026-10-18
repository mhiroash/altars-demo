# Altars — Demo Editorial

Este repository contains the source code and documentation for Altars, an editorial demo that proves the complete pipeline (collect → classify → draft → alert → compose) to Esteves Francisco.

## What is here
- **Design system + UI:** `design/` (index.html, styles.css, app.js, design-system.md, check_contrast.py)
- **Texts and microcopy:** `escritor/` (microcopy-ui.md, estruturas-editoriais.md, export-artigos-pipeline.md, 01-microcopy-interface.md)
- **Architecture and plan:** `adr/` (ADR-ALT-2026-001-demo-editorial.md), `plano-execucao.md`
- **Implementation documentation:** `pipeline/` (recoletor.py, busca.py, classificador.py, compositor.py, db.py)

## What is NOT here
- **Database** (4.5 MB): `pipeline/data/altars.db` — archived collection data, not public in this repo.
- **Credentials and tokens:** Telegram bot token, API keys of external sources — only text reference in `plano-execucao.md` (see §6).

## How to use this repo
This repo is **read-only**. The complete and functional demo (including the panel, alerts and exports) is published only **after approval of Gates 2 (QA + Security)** and of the owner (Belmiro). Until then, this repo serves as technical reference and documentation.

## Links
- **Internal preview (noindex):** pending publication — the hosting platform hit the 25-site limit. The URL will be `https://altars-demo-preview-sites.tivrai.dev/` when the slot is freed (see `deploy/DIAGNOSTICO-522.md`).
- **Final demo (after approval):** URL will be defined by the Tivra platform after owner approval.

## License
This project is part of the Altars editorial demo (PRD-ALT-2026-02) — restricted to the Tivra team and Esteves Francisco.