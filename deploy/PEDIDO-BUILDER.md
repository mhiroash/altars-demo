# Pedido de construção/publicação — Altars Demo Editorial

**Para:** Kora / Tivra Builder
**De:** Dev (líder do projecto «Altars — Demo Editorial»)
**Data:** 2026-10-20
**Objetivo:** publicar o demo num URL público com `noindex`, para o Esteves Francisco poder ver a plataforma a funcionar.

---

## 1. O que é o demo

Plataforma editorial de notícias com IA. Pipeline completo: recolha de notícias de portais reais → redacção assistida de 3 tipos de peça → alerta de perfil → composição → exportação PDF/PNG. Todos os factos das peças têm fonte anexada e todas as peças exigem aprovação humana antes de sair.

## 2. Estado actual (verificado em disco, 20/10)

| Componente | Estado | Onde |
|---|---|---|
| App Flask + SQLite | funcional, 4 ecrãs, endpoints a 200 | `app/` (server.py 340 l., exportar.py 145 l., db.py 88 l., mirex.py 141 l.) |
| Dados reais | 19 artigos (Correio Kianda 6, ECO 6, Maka Angola 6, MINFIN 1), 67 peças, 1 alerta | `pipeline/` (SQLite) |
| Design system + UI | completo, contraste verificado | `design/` |
| Preview estático | `preview/index.html` (24.083 B, md5 `92e4fa22cdcff7230b065b59c9332959`) + `app.js` (7.008 B) + `styles.css` (29.513 B), `noindex` confirmado no `<meta>` da linha 4 | `preview/` |
| ADR | aprovado | `adr/ADR-ALT-2026-001-demo-editorial.md` |
| Gate QA | aprovado v3 | `qa/verificacao-qa-gate2-v3.md` |
| Gate Segurança | 2 altas corrigidas (A1 sanitização, A2) | `seguranca/relatorio-seguranca-demo.md` |

## 3. O que eu preciso do Builder

**Opção A — Build completo (preferida, se o Builder suportar).** A app Flask com API e SQLite, a correr a sério, com os dados reais.

**Opção B — Só o preview estático (mais rápido e mais seguro).** `preview/index.html` + `preview/app.js` + `preview/styles.css` servidos como site estático. A demo mostra Inbox, Redacção (com geração simulada), Alertas e Composição com exportação simulada. Não precisa de backend nenhum. **É o que recomendo para a primeira publicação** — o objectivo é o Esteves ver o conceito, não testar infraestrutura.

## 4. Especificação técnica para a Opção A

- Python 3.10, Flask, Jinja2, SQLite (ficheiro local), Pillow + `pdftoppm` para exportação.
- Arranque: `python3 serve.py` (127.0.0.1:8099 por omissão — no servidor de publicação, escutar em 0.0.0.0 com porta da plataforma).
- Entrada da app: `app/server.py`, factory `create_app()`.
- Base de dados: criar com o script de `pipeline/` e semear com os 19 artigos (ou um subconjunto de 6, se o espaço for limitado).
- Rotas exigidas: `/api/health`, `/api/inbox`, `/api/inbox/<id>`, `/api/gerar`, `/api/pecas`, `/api/pecas/<id>/aprovar`, `/api/alertas`, `/api/pecas/<id>/preview`, `/api/pecas/<id>/exportar.{pdf,png,jpg}` e a raiz `/` a servir a UI.
- A UI está em `design/` e `preview/`; tem de ficar ligada às rotas acima (o `preview/app.js` actual é simulado).

## 5. Requisitos não negociáveis

1. **`noindex`**: ou cabeçalho `X-Robots-Tag: noindex, nofollow` ou `<meta name="robots" content="noindex, nofollow">`. Os dois, de preferência.
2. **Nada de segredos**: sem tokens do Telegram, sem chaves, sem `.env`. O Telegram fica desligado (`telegram_ativo: false`).
3. **Sem listagem pública** e sem link a partir de nenhum site nosso.
4. **Sanitização activa**: o HTML de terceiros nunca entra no corpo da peça sem passar por `limpar_html_conteudo` (achado A1).
5. **Rótulo de honestidade**: cada peça gerada mostra «Redigida pela IA. Falta a sua revisão.» até alguém a aprovar. Peças do modo extractivo (sem LLM) mostram «Compilação extractiva — sem LLM».

## 6. O que devolves quando acabares

Um relatório de estado **real**, não uma declaração de sucesso:
- árvore de ficheiros publicados, com contagem de linhas por ficheiro;
- URL final + prova de `noindex` (`curl -I` com o cabeçalho, ou o `<meta>` no HTML servido);
- resultado de `GET /api/health` (se Opção A) ou prova de que o HTML servido tem o conteúdo do demo;
- captura de ecrã do demo a abrir no browser.

**Não copiar o caso Finanças Pro:** o Builder declarou app construída quando só existia o esqueleto (index.html 81 linhas, zero JS). Se só houver esqueleto, diz que só há esqueleto.

## 7. Quem aprova a publicação

O Belmiro (dono). Nada é publicado sem a aprovação dele. O pedido de aprovação descreve marca fictícia, `noindex`, e que o demo está fechado.
