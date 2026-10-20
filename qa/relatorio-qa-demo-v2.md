# Relatório de QA — Demo Editorial Altars (Gate 2 — antes de publicar) — v2

**Tarefa:** TASK-2026-10-18-007 (P0)  
**Data:** 2026-10-18  
**Autor:** QA (Tivra)  
**Veredicto:** **CORRIGIR ANTES DE PUBLICAR** (revisto — substitui a v1, rejeitada por classificar o Telegram como bloqueador P1)

---

## Correcções face à v1 (motivo da rejeição)

1. **Telegram deixou de ser bloqueador.** Está **implementado** (`app/telegram_notify.py`, 43 linhas, chamado por `server.py` em `/api/alertas/poll`), mas em modo desligado por falta de `TELEGRAM_BOT_TOKEN`/`TELEGRAM_CHAT_ID` — dependência externa que só o Belmiro tem. É Fase 2+ / configuração de deploy, **não** correção de código. A v1 classificava-o como P1; é **P3/config**.
2. **Exportação já existe no backend** (a v1 avaliava só a UI): `app/exportar.py` (95 linhas) + endpoints `/api/pecas/{id}/exportar.pdf` e `/exportar.png` com gate humano (`_peca_aprovada` → 409 sem aprovação). **PDF gera ficheiro real** (testado: 1.707 bytes, magic `%PDF-`). **PNG falha** — mas por causa da política de segurança do ImageMagick do sistema (`/etc/ImageMagick-6/policy.xml:97`, `rights="none" pattern="PDF"`), não por código em falta: `pdftoppm` gera o mesmo PNG sem problema (9.396 bytes, testado).
3. **Novo achado P0:** `server.py` dá **500 em todos os endpoints que tocam a BD** — causa raiz confirmada: o `sys.path` põe `pipeline/` à frente, `import db` resolve para `pipeline/db.py` (não tem `init_app`) em vez de `app/db.py` (tem). `/api/health` responde (não toca BD), `/api/inbox`, `/api/pecas`, `/api/alertas` e ambas as exportações dão 500. O demo não arranca como está.

---

## Critérios de Aceitação Avaliados

### 1. Utilizador produz e exporta uma peça completa em menos de 10 minutos

| Critério | Estado | Evidência no disco |
|----------|--------|-------------------|
| Tempo de geração <10 min | ✅ PASS | `design/app.js`: `btnGerar` → setTimeout 2400ms → `abrirEditor()`. |
| Fluxo recolha → redigir → revisar → exportar | ❌ FAIL | UI (`app.js:183-191`) chama só `toast()` — não liga aos endpoints reais do backend. Backend tem os endpoints; a UI não os usa. |
| Exportação gera ficheiro | ⚠️ PARCIAL | PDF real via backend (testado, 1.707 bytes). PNG falha por policy do ImageMagick (sistema), `pdftoppm` funciona. UI não ligada. |

### 2. Peça identifica fontes com precisão

| Critério | Estado | Evidência no disco |
|----------|--------|-------------------|
| Fontes anexadas | ✅ PASS | `pipeline/provas/relatorio-pipeline.md`: 54 peças com fontes. |
| Fontes extraídas do campo correto | ❌ FAIL | `recoletor.py:149` chama `html_para_texto(conteudo_html)` **sem** `limpar_html_conteudo` antes (testado agora: `limpar_html_conteudo('<p>Texto util.</p><script>alert(1)</script><img src=x onerror=alert(2)>')` → `'<p>Texto util.</p><img src=x onerror=alert(2)>'` — o `<img onerror>` sobrevive). A1 continua aberta. |
| Nenhuma frase inventada | ✅ PASS | Fallback extractivo, frases literais do original. |

### 3. Alerta do perfil chega ao Telegram em menos de 3 minutos

| Critério | Estado | Evidência no disco |
|----------|--------|-------------------|
| Alerta no painel | ✅ PASS | `server.py` `/api/alertas` + `design/app.js` (secção Alertas). |
| Telegram implementado | ✅ PASS (código) | `app/telegram_notify.py` (43 linhas) + `server.py:181` chama `telegram_notify.enviar(...)` no poll. |
| Telegram funcional (envio real) | ⚠️ CONFIG | `telegram_ativo:false` no `/api/health` — faltam env vars (só o Belmiro as tem). Fase 2+/deploy, não bloqueia o demo. |
| Latência <3 min | ❌ N/A | Sem token não há envio real para medir. |

### 4. Template gera PNG e JPG prontos a publicar

| Critério | Estado | Evidência no disco |
|----------|--------|-------------------|
| Exportação em PDF | ✅ PASS (backend) | `app/exportar.py:gerar_pdf` — testado: 1.707 bytes, magic `%PDF-`, guardado em `/tmp/qa_export.pdf`. |
| Exportação em PNG | ⚠️ PARCIAL | `gerar_png` falha: `convert` bloqueado pela policy do ImageMagick (`policy.xml:97`). Alternativa validada: `pdftoppm -png -r 150` → 9.396 bytes OK. Correção = trocar `convert` por `pdftoppm` em `exportar.py` OU ajustar a policy (root). |
| Exportação em JPG | ❌ FAIL | Não há caminho JPG no `exportar.py` (só PDF→PNG). Com `pdftoppm -jpeg` resolve-se na mesma correção. |
| UI ligada à exportação | ❌ FAIL | `app.js:183-191`: botões chamam `toast()` apenas. |

### 5. Plataforma funciona em Chrome/Safari/Edge

| Critério | Estado | Evidência no disco |
|----------|--------|-------------------|
| Acessibilidade (ARIA, teclado) | ✅ PASS | `app.js`: aria-selected, tabindex, keydown (Arrow/Home/End). |
| Viewports | ✅ PASS | `design/verificacao/` desktop 1280 + mobile 390. |
| Sem erros de consola | ⚠️ NÃO VERIFICADO | Playwright não corrido neste turno (servidor nem arranca com os endpoints de BD em 500). |

### 6. Coletor respeita o Crawl-delay: 5 da Angop

| Critério | Estado | Evidência no disco |
|----------|--------|-------------------|
| robots.txt lido | ✅ PASS | `plano-execucao.md:33` + `relatorio-pipeline.md`. |
| Pausa aplicada | ✅ PASS | `recoletor.py:46` `PAUSA_ENTRE_PEDIDOS = 5.0`. |
| Arquivo integral + sha256 | ✅ PASS | 18/18 artigos, hashes verificados. |

---

## Problemas Encontrados (Severidade | Descrição | Como Reproduzir)

| # | Severidade | Descrição | Como Reproduzir |
|---|-----------|-----------|-----------------|
| 1 | **P0** | `server.py` → 500 em todos os endpoints de BD: `import db` resolve para `pipeline/db.py` (sem `init_app`) porque `pipeline/` está à frente no `sys.path`. | `uvicorn server:app` + `curl /api/inbox` → 500; log: `AttributeError: module 'db' has no attribute 'init_app'`. Correção: `import db as appdb` → import explícito de `app/db.py` (ex.: `importlib` ou renomear). |
| 2 | **P1** | UI não ligada ao backend: botões de exportar/rever/compor chamam `toast()` e nunca os endpoints reais. | `design/app.js:183-191` (e 156, 162-164, 170-172, 179). |
| 3 | **P1** | PNG/JPG falham no servidor: policy do ImageMagick bloqueia PDF. | `convert` → `security policy 'PDF'` erro; `pdftoppm` funciona. Corrigir `exportar.py` (usar `pdftoppm`) ou a policy. |
| 4 | **P2** | Sanitização A1 aberta: `recoletor.py:149` não passa `conteudo_html` por `limpar_html_conteudo`; `<img onerror>` sobrevive (testado). | Payload de teste acima; aplicar `limpar_html_conteudo` antes de `html_para_texto` (e ao título). |
| 5 | **P2** | Sem JPG no módulo de exportação. | `exportar.py` só tem PDF e PNG; `pdftoppm -jpeg` cobre. |
| 6 | **P3/config** | Telegram em modo desligado (env vars em falta — só o Belmiro as tem). Não é bloqueador. | `/api/health` → `telegram_ativo:false`. |

---

## Veredicto Final

**CORRIGIR ANTES DE PUBLICAR** — mas a lista mudou face à v1:

- **Bloqueadores reais (P0/P1):** (1) bug de import no `server.py` (demo não arranca), (2) UI não ligada aos endpoints reais, (3) PNG/JPG por policy do ImageMagick (trocar por `pdftoppm`, já validado).
- **Não bloqueadores:** Telegram (implementado, aguarda env vars — Fase 2+/deploy), sanitização A1 (P2, corrigir antes do Gate 2 mas não impede o arranque), regressão de browsers (P2, após o servidor arrancar).

Após corrigir #1-#3, re-auditar (arranque + fluxo completo no browser + exportação PDF/PNG/JPG reais) e só então Gate 2.

**Relatório gerado por QA — 2026-10-18 (v2).**
