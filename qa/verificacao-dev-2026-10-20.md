# Verificação da app do demo Altars — pós-correcções (Dev)

**Data:** 2026-10-20
**Responsável:** Dev
**Tarefas:** TASK-2026-10-18-006 (app), TASK-2026-10-17-007 (entrega)
**Base:** relatório QA v2 (`qa/relatorio-qa-demo-v2.md`) — 6 problemas listados

## Sumário

| # | Problema QA v2 | Sev. | Estado | Prova |
|---|---|---|---|---|
| 1 | `import db` resolvia para `pipeline/db.py` → 500 em todos os endpoints de BD | P0 | **CORRIGIDO** | 4 endpoints a 200; `server.py:27-38` |
| 2 | UI não ligada ao backend (botões só davam `toast`) | P1 | **CORRIGIDO** | download real no browser: PDF 4.504 B, PNG 458.464 B |
| 3 | PNG/JPG falhavam por policy do ImageMagick | P1 | **CORRIGIDO** | `exportar.py` usa `pdftoppm`; 3 formatos a 200 |
| 4 | Sanitização A1 aberta (`recoletor.py:149`) | P2 | **CORRIGIDO** | `limpar_html_conteudo` aplicado nas linhas 159/173/180/182 |
| 5 | Sem JPG no módulo de exportação | P2 | **CORRIGIDO** | `gerar_jpg` + rota `/exportar.jpg` |
| 6 | Telegram desligado (falta env) | P3/config | **PENDENTE DO DONO** | `/api/health` → `telegram_ativo:false` |

## Provas executadas

### Arranque e endpoints (porta 5055)

```
GET /api/health   -> 200
GET /api/inbox    -> 200   (19 artigos)
GET /api/pecas    -> 200   (67 peças)
GET /api/alertas  -> 200   (1 alerta)
```

`{"ok":true,"telegram_ativo":false,"exportacao":true}`

### Ciclo completo (RF-2.x / RF-4.4 / RF-5.3)

1. **Gerar** os 3 formatos sobre o artigo 1 (Maka Angola, real, arquivado):
   - `breve` → peça 69
   - `desenvolvida` → peça 70
   - `analise` → peça 71
   Todas com `antetitulo`, `titulo`, `lead`, `corpo`, `rotulo` e fontes reais.
2. **Aprovar** a peça 69 → `estado: revista`, `estado_rotulo: "Revista — aprovada por humano. Pode ser composta."`
3. **Exportar** a peça 69 → PDF 200 (2.452 B), PNG 200 (121.717 B), JPG 200 (127.845 B).
4. **Gate humano** → peça 2 (não revista) devolve **HTTP 409** `{"detail":"exportação bloqueada: a peça ainda não foi revista"}`.

**Fontes anexadas** (peça 69, `GET /api/pecas/69/preview`): 1 fonte com `fonte`, `url` (makaangola.org), `autor`, `data` e `titulo` — extraída do arquivo, não inventada.

### Browser real (Playwright, Chromium)

- **4 ecrãs operacionais:** Inbox (19 itens), Redigir, Alertas (1), Compor (lista de revistas).
- **Erros de consola: 0.** Erros JS: 0.
- **`<meta name="robots" content="noindex, nofollow, noarchive, nosnippet, noimageindex">`** presente no HTML servido.
- **Mobile 390×844:** sem overflow horizontal.
- **Exportação pela UI:** clicar «Exportar PDF» → ficheiro `altars-58.pdf` (4.504 B, magic `%PDF-1.4`); «Exportar PNG» → `altars-58.png` (458.464 B, magic `\x89PNG`). Toast: «Exportado: altars-58.png».
- Capturas: `exports/verif-inbox.png`, `verif-redigir.png`, `verif-alertas.png`, `verif-compor.png`, `verif-compor-export.png`, `verif-mobile.png`.

### Testes automáticos

```
cd /workspace/altars/app && python3 -m pytest tests/ -q
........                                                                 [100%]
8 passed in 0.60s
```

## O que NÃO está verificado

- **Telegram real:** sem `TELEGRAM_BOT_TOKEN`/`TELEGRAM_CHAT_ID`, não há envio nem medição de latência. Código existe (`app/telegram_notify.py`), é chamado no poll, e o alerta está rotulado como simulado na UI. É configuração de deploy, não código.
- **Peça proposta do alerta:** o alerta activo é do MIREX e **não tem artigo correspondente no arquivo**, por isso `peca_proposta` vem `null`. Isto é o comportamento correcto (o código não inventa peça sem fonte), mas o critério RF-3.4 «alerta com peça proposta» só é demonstrável com um alerta cujo título case com um artigo arquivado.
- **Gate 2 do QA e da Segurança sobre esta versão:** ainda não re-auditado depois destas correcções.

## Bloqueio de publicação

`tivra-publish preview --name altars-demo-preview` → **recusado: «limite de 25 sites atingido»**. Não há rota API de listagem/eliminação (`/v1/sites`, `/v1/sites/drafts` → 404). Depende do dono libertar um slot ou aumentar capacidade.

**Nada foi publicado.** O repo de leitura `github.com/mhiroash/altars-demo` está UP (200), mas o README aponta para o hostname morto `altars-demo-preview.tivrai.dev` (sem `-sites`, dá 522).
