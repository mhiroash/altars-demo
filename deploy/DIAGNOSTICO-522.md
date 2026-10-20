# Diagnóstico — Preview Altars (522) · TASK-2026-10-18-011

**Data:** 18/10/2026 · **Responsável:** DevOps · **Prioridade:** P0

## 1. Causa raiz do 522 (confirmada)

O hostname `altars-demo-preview.tivrai.dev` **não termina em `-sites`**, logo não casa com a rota
`*-sites.tivrai.dev/*` do Worker `tivra-sites`. Sem rota, o Cloudflare tenta a origem
(apex `100::`, blackhole) → **HTTP 522** (origin unreachable).

Provas:
```
$ curl -sI https://altars-demo-preview.tivrai.dev/
HTTP/2 522   (content-type: text/plain; content-length: 16)

$ curl -sI https://altars-demo-preview-sites.tivrai.dev/
HTTP/2 404   (content-type: text/html; link: <https://tivrai.dev/abuso>)
              ^^^^^^^^ o Worker responde — a rota apanha o hostname com -sites
```
O hostname antigo **nem registo DNS tem** (`getent hosts` → vazio). Foi inventado fora da via
oficial `tivra-publish`, que gera sempre `<slug>-sites.tivrai.dev`.

## 2. Bloqueio da republicação (novo, real)

A via oficial `tivra-publish` recusa com:
```
tivra-publish: recusado — falha de rede ou do servidor:
  limite de 25 sites atingido; apaga um site ou pede mais capacidade
```
Tentado com nome novo (`--name altars-demo-preview`) **e** com nome existente
(`--name devops-probe-006-x2da`) — recusa nos dois casos.

A API (`https://api.tivrai.dev/v1`) só expõe `POST /sites/drafts` ao token da sessão:
```
$ curl -s .../v1/sites        -> HTTP 404 {"error":"rota não encontrada"}
$ curl -s .../v1/sites/drafts -> HTTP 404 {"error":"rota não encontrada"}
```
**Não há rota de listagem nem de eliminação** → não consigo libertar um slot sozinho.

## 3. Estado dos entregáveis (verificado por HTTP, agora)

| Entregável | HTTP | Estado |
|---|---|---|
| Preview `altars-demo-preview.tivrai.dev` | **522** | **DOWN** — bloqueado pelo limite de 25 sites |
| Repo `github.com/mhiroash/altars-demo` | **200** | **UP** |
| README `raw.../main/README.md` | **200** | **UP** — mas aponta para o hostname morto |

O 404 que o chefe viu no repo **já não se verifica** — o repo está acessível (200) e o README
também. O conteúdo do repo está completo: README, adr/, app/, design/, escritor/, pipeline/,
qa/, seguranca/, plano-execucao.md.

## 4. Conteúdo pronto a publicar

`/workspace/altars/preview/` — 11 ficheiros, ~1.1 MB:
- `index.html` (24 KB), `styles.css` (30 KB), `app.js` (7 KB)
- `verificacao/` — 8 capturas de QA (desktop + mobile, 4 ecrãs)

A plataforma Tivra injecta `x-robots-tag: noindex, nofollow` automaticamente em todos os
`*-sites.tivrai.dev` (confirmado no `noticias-ia`), o que satisfaz o requisito de noindex
sem configuração adicional.

## 5. O que falta (depende do dono)

1. **Libertar um slot de site** (apagar um dos 25 ou aumentar capacidade) — é a única coisa
   que desbloqueia o preview. Candidato natural: `devops-probe-006-x2da` (sonda de diagnóstico
   minha, 264 bytes, zero valor de produto).
2. Depois disso, republico com `tivra-publish /workspace/altars/preview --name altars-demo-preview`
   e confirmo `curl -sI` → 200 + `X-Robots-Tag: noindex, nofollow`.
3. **Actualizar o README do repo** para o novo URL (tenho acesso de escrita via conector GitHub).

## 6. O que NÃO fiz

- Não publiquei nada (a plataforma recusou; não contornei).
- Não apaguei nenhum site (não tenho rota; e apagar é acção irreversível que exige aprovação).
- Não mexi nas rotas do Worker `tivra-sites` (infra partilhada, exige aprovação).
