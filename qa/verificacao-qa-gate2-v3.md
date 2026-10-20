# Gate 2 Altars — re-auditoria v3 (QA)
**Data:** 20/10/2026 · **Servidor:** uvicorn server:app em 127.0.0.1:5055 · **Método:** disco + HTTP real + Playwright headless

## Resultado das 6 verificações (replicadas por mim)

| # | Achado v2 | Estado | Evidência |
|---|---|---|---|
| 1 | P0 import db | **PASS** | `server.py:31-38` — `for _p in (PIPELINE, HERE): remove + insert(0)` => app/ primeiro. `/api/health` 200, `/api/inbox` 200 (19), `/api/pecas` 200 (71), `/api/alertas` 200 (1) |
| 2 | P1 UI desligada | **PASS** | Playwright: clique "Exportar PDF" descarrega `altars-1.pdf` 2.452 B magic `255044462d312e34`; "Exportar PNG" `altars-1.png` 121.717 B magic `89504e47`. Zero pageerrors |
| 3 | P1 PNG/JPG ImageMagick | **PASS** | `exportar.py:75-100` usa `pdftoppm` (subprocess). HTTP: PDF 2.452 B, PNG 121.717 B, JPG 127.845 B, todos 200. PIL: 1241×1754 RGB |
| 4 | P2 A1 sanitização | **PASS** | `recoletor.py:159/173/180/182` aplica `limpar_html_conteudo`. PoC `<img src=x onerror=alert(2)>` => `<img src=x>`; script e `javascript:` removidos |
| 5 | P2 rota JPG | **PASS** | `server.py:325-327` `/api/pecas/{id}/exportar.jpg` 200 · `image/jpeg` |
| 6 | Telegram | **config** | `/api/health` => `telegram_ativo:false` (faltam env vars). Não é código |

## Gate humano
`/api/pecas/2/exportar.pdf` (estado `gerada`) => **HTTP 409** `"exportação bloqueada: a peça ainda não foi revista"`. OK.

## Browser — 4 ecrãs
Título "Altars — Demo Editorial", h1 "Inbox". Inbox: 20 itens, artigos reais dos feeds. Redigir: tipos Breve/Desenvolvida/Análise, 3 tons, editor presente. Alertas: 1 alerta, fonte mirex real, aviso "simulado nesta demonstração". Compor: 14 peças revistas no selector. **overflow-x: 0 px · erros de consola: 0**.

## noindex
`X-Robots-Tag: noindex, nofollow, noarchive, nosnippet, noimageindex` no header **e** `<meta name="robots">` no HTML.

## pytest
`8 passed in 0.70s`

## Bloqueadores P0
**Nenhum.** Restam menores, não bloqueantes:
- Nota: o Dev reportou 67 peças; no disco há **71**.
- Não existe botão "Exportar JPG" na UI (a rota existe e responde). Gap de UI, P3.
- `server.py.bak-0816` e `app.js.bak-0817` convivem com os originais — limpar antes de publicar.

## Veredicto
**APROVADO** para o Gate 2. A publicação continua dependente de aprovação do Belmiro e da quota de sites (429).
