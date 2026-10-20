# Relatório de segurança — Demo Editorial Altars

**Tarefa:** TASK-2026-10-18-008 — Gate 2 (antes de publicar)
**Data:** 2026-10-18
**Autor:** Segurança (Tivra)
**Alvo:** `/workspace/altars/` — app (`app/`), coletor (`pipeline/`), UI (`design/`, `deploy/`, `preview/`)
**Versão do estado auditado:** código em disco + PoCs reproduzíveis

---

## Veredicto: CORRIGIR ANTES DE PUBLICAR

Dois achados de severidade **alta** (A1, A2) e um de **média** (A3). Não há token do Telegram em código nem em ficheiro versionado, não há segredos, e os erros do servidor não expõem caminhos internos. O modo de leitura do Esteves não está implementado (Fase 2+), por isso não pode ser verificado.

---

## Achados

### A1 — Coletor não sanitiza o `conteudo_html` do feed (ALTA)

**Onde:** `pipeline/recoletor.py:149`, função `recolher_feed()`

```python
conteudo_html = campo("content:encoded") or campo("description")
corpo = html_para_texto(conteudo_html)     # linha 149 — sem sanitização
```

**O que está errado:** o `conteudo_html` vem directamente do feed RSS (campo `content:encoded` ou `description`) — conteúdo de terceiros. A função `limpar_html_conteudo()` (linhas 105-109), que remove `<script>`, `<iframe>` e atributos de evento `on*`, **não é aplicada** a este campo; só é aplicada ao arquivo integral (`bruto_txt`, linha 142). O texto extraído entra em `corpo_texto` e é depois consumido pelo compositor (`compositor.py:34`) sem nova limpeza.

**PoC (corrido com o código real importado; saída em `seguranca/poc-sanitizacao.txt`):**

```
payload = '<p>Normal</p><script>alert(document.cookie)</script><img src=x onerror="fetch(...)">'

html_para_texto(payload)      = 'Normal'
limpar_html_conteudo(payload) = '<p>Normal</p><img src=x>'
```

Variantes que `limpar_html_conteudo()` **não** remove (regex só apanha `on*="..."` com aspas duplas):

```
onerror sem aspas      IN: <img src=x onerror=alert(1)>     OUT: <img src=x onerror=alert(1)>
onerror aspas simples  IN: <img src=x onerror='alert(1)'>   OUT: <img src=x onerror='alert(1)'>
javascript: em href    IN: <a href="javascript:alert(1)">   OUT: <a href="javascript:alert(1)">
```

**Impacto:** a app guarda e serve conteúdo de terceiros não sanitizado. No demo actual o frontend usa `textContent` (ver «O que está bem»), pelo que não há execução agora — mas o vetor fica aberto a qualquer passo futuro que renderize HTML, e compromete a integridade dos dados arquivados (RF-1.6).

**Remédio:**
```python
# recoletor.py, linhas 128 e 149
titulo = html.unescape(limpar_html_conteudo(campo("title")))
...
conteudo_html = campo("content:encoded") or campo("description")
corpo = html_para_texto(limpar_html_conteudo(conteudo_html))
```
E reforçar `limpar_html_conteudo()` para cobrir `on*` sem aspas, com aspas simples, e esquemas `javascript:`/`data:` em `href`/`src` — idealmente com uma biblioteca de sanitização (`bleach`/`nh3`) em vez de regex.

---

### A2 — Preview em `design/` sem noindex (ALTA)

**Onde:** `design/index.html:1-10` (falta a meta robots)

**O que está errado:** o ADR-ALT-2026-001 (D8) exige «meta noindex + header X-Robots-Tag: noindex enquanto não houver APR do dono». O `design/index.html` **não tem** a meta. O `deploy/index.html` e o `preview/index.html` **têm**:

```html
<meta name="robots" content="noindex, nofollow, noarchive, nosnippet, noimageindex">
```

Mas o servidor que está a correr serve o `design/`, não o `deploy/`:

```
ss -tlnp → LISTEN 0.0.0.0:8099  python3 -m http.server 8099   (cwd: /workspace/altars/design)
```

**Prova:** os três ficheiros são diferentes (sha256):
```
design/index.html  fe0889ec...
deploy/index.html  ef69c478...
```
O que está exposto no porto 8099 é o `design/` — sem noindex.

**Impacto:** a superfície de preview fica indexável e sem o gate de robots exigido pelo ADR antes da aprovação do dono.

**Remédio (um dos dois):**
1. Adicionar a meta robots ao `design/index.html`; ou
2. Servir o `deploy/` em vez do `design/`: `python3 -m http.server 8099 --directory /workspace/altars/deploy`.

---

### A3 — Servidor de demo escuta em `0.0.0.0` (MÉDIA)

**Onde:** processo `python3 -m http.server 8099`, `cwd=/workspace/altars/design`, bind `0.0.0.0:8099`.

**O que está errado:** o bind em `0.0.0.0` expõe o preview a todas as interfaces de rede, não só a `localhost`. Combinado com A2 (sem noindex), amplia a exposição. Não consegui confirmar alcance externo (o teste de resposta externa deu timeout), pelo que o risco real depende do firewall do host — **não verificado**.

**Remédio:** servir em `127.0.0.1` enquanto for preview interno, ou pôr atrás do proxy da plataforma com o gate de acesso.

---

## O que está bem

- **Token do Telegram:** não está em código nem em ficheiro versionado. Vem de `os.environ.get("TELEGRAM_BOT_TOKEN")` (`app/telegram_notify.py:14`), com modo desligado se ausente. As únicas ocorrências de `TELEGRAM_BOT_TOKEN` no repo são o próprio código, um teste que a define como `"123:ABC"` (fictícia) e a nota do QA. **Foco 2 limpo.**
- **Segredos:** varredura de 10 padrões (bot token, `glpat-`, `ghp_`, `sk-`, AWS, `xox`, chave PEM, etc.) sobre todo o repo → **zero ocorrências**.
- **Erros não expõem caminhos internos:** `GET /api/pecas/99999/exportar.pdf` → `Internal Server Error` (genérico); rota inexistente → `{"detail":"Not Found"}`. O traceback com caminhos fica no log do servidor, não na resposta. **Foco 3 limpo.**
- **Frontend sem XSS:** `design/app.js` usa `textContent` em todas as escritas de DOM; zero `innerHTML`/`outerHTML`/`insertAdjacentHTML`/`document.write`.
- **Gate de publicação:** o ADR exige APR do dono antes de publicar; o `deploy/README.md` e o `preview/` estão marcados como internos. Nada indica publicação para fora sem aprovação.

---

## Não verificado

- **Modo de leitura do Esteves:** não há implementação de autenticação/perfis no demo (Fase 2+, conforme `plano-execucao.md:136`). Não existe ficheiro de configuração, script de publicação nem middleware de autorização — logo não há nada para verificar. **Foco 4: NÃO VERIFICÁVEL no estado actual.**
- **Alcance externo do porto 8099:** teste de resposta externa deu timeout; não confirmei se o firewall bloqueia. **NÃO VERIFICADO.**
- **Servidor de demo (uvicorn:8000):** o processo do DevOps tem um erro de importação (`AttributeError: module 'db' has no attribute 'init_app'`) que faz `/api/inbox` devolver 500. Não é segurança, é bug de integração — registado para o Dev.
- **Headers HTTP de produção:** não há URL de preview a responder no momento da auditoria (o DevOps registou 522 no `altars-demo-preview.tivrai.dev`), pelo que a verificação de `X-Robots-Tag` no ar não foi possível.

---

## Recomendação

**CORRIGIR ANTES DE PUBLICAR:**
1. **C1 (A1):** aplicar `limpar_html_conteudo()` ao `conteudo_html` e ao `titulo` em `pipeline/recoletor.py` (linhas 128 e 149), e reforçar a função de limpeza (aspas simples/sem aspas, `javascript:`, `data:`).
2. **C2 (A2):** pôr a meta robots noindex no `design/index.html` **ou** servir o `deploy/` (que já a tem) em vez do `design/`.
3. **C3 (A3):** passar o preview para `127.0.0.1` enquanto for interno.

Depois de C1 e C2 corrigidos, volto a verificar e o veredicto passa a APROVADO.

---

## Verificação de actualização (01:30, mesmo dia)

Re-validado o estado em disco e em execução após o trabalho do DevOps/QA:

- **A1 mantém-se:** `pipeline/recoletor.py:149` continua `corpo = html_para_texto(conteudo_html)` sem `limpar_html_conteudo()`. C1 **não aplicada**.
- **A2 mantém-se:** `design/index.html` continua sem meta robots; e o servidor local no porto 8099 (pid 18335, `cwd=/workspace/altars/design`) serve esse ficheiro — confirmado por HTTP: a resposta não contém `robots`. C2 **não aplicada**.
- **A3 mantém-se:** o porto 8099 escuta em `0.0.0.0:8099` (verificado com `ss -tlnp`).
- **Foco 2 re-verificado:** token do Telegram só por `os.environ.get("TELEGRAM_BOT_TOKEN")` (`app/telegram_notify.py:16`); varredura de padrões de segredo sobre o repo → zero ocorrências fora do próprio relatório. **Limpo.**
- **Foco 3 re-verificado:** o servidor de demo em `127.0.0.1:8000` está agora saudável (`/api/health` → `{"ok":true}`, `/api/inbox` → 200); o erro de importação registado antes foi corrigido. Erros genéricos sem caminhos.
- **Foco 4:** sem implementação de acesso de leitura para o Esteves (sem auth/perfis em `app/`); nada para verificar — não verificável no estado actual.
- **Foco 5:** o preview externo `altars-demo-preview.tivrai.dev` responde **522** (indisponível — nada exposto ao público neste momento); o `deploy/index.html` e o `preview/index.html` têm noindex; o `design/index.html` (servido no 8099) não tem. Nada publicado sem aprovação.

**Veredicto mantém-se: CORRIGIR ANTES DE PUBLICAR** (C1 e C2 pendentes).

---

*Relatório por Segurança (Tivra) — 2026-10-18. Cada achado com ficheiro:linha, PoC reproduzível e remédio concreto. Achados genéricos omitidos.*
