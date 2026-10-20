# Provas do pipeline Altars — 17/10/2026 (Agentes)

Tarefa: TASK-2026-10-17-011 · ADR: ADR-ALT-2026-001 (gate 1 fechado 17/10)

## 1. Recolha (RF-1.1, RF-1.6)

- Fontes: 1 principal + 2 alternativas, todas com robots.txt verificado a 17/10:
  - **Maka Angola** (https://www.makaangola.org/feed/) — robots: só /wp-admin/ bloqueado; feed OK.
  - **Correio Kianda** (https://www.correiokianda.info/feed/) — robots: `Disallow:` vazio (tudo permitido).
  - **ECO** (https://eco.sapo.pt/rss/) — robots: só /wp-admin/, /trackback/, feeds aninhados; /rss/ permitido.
- UA identificável: `AltarsDemoPipeline/0.1 (recolha editorial demo; contacto: ellocene-lda)`.
- Pausa ≥5 s entre pedidos (ADR D3). Log completo: `provas/recolha_2026-10-17.log`.
- Arquivo integral: HTML da página original guardado com sha256 na tabela `arquivo`.

Bug corrigido durante a tarefa: `urllib.robotparser.read()` busca robots.txt com o
UA padrão do Python; alguns sites respondem 403 e o parser passa a bloquear tudo
(falso negativo que saltava Correio Kianda e ECO). Corrigido: robots.txt é buscado
com o nosso UA e parseado explicitamente. Prova: antes 0 feeds alternativos
aceites; depois, os 3 aceites (ver log).

## 2. Classificação (RF-1.3) — heurística rotulada

Regras de palavra-chave nas 6 categorias do PRD; `categoria_metodo` =
`regras-palavra-chave` em todas as linhas (nenhum consumidor confunde com
verdade editorial). Validação: `provas/validacao_classificacao.py` contra
rótulos manuais (`provas/rotulos_manuais.json`) — método e resultado abaixo.

## 3. Busca (RF-1.5)

`busca.py` com filtros combináveis tema/data/palavra-chave/fonte. Provas de
execução real no fim do relatório.

## 4. Redacção (RF-2.1/2.3/2.5)

ADR D5 condiciona o LLM a prova real de inferência. Verificado a 17/10:
- O conector Piramyd disponível é de ADMINISTRAÇÃO (19 ferramentas: providers,
  chaves, analytics) — nenhuma faz inferência.
- Sem chave externa verificada ⇒ **fallback extractivo rotulado**
  (`composer-extractivo-sem-llm`): nenhuma frase inventada, cada parágrafo vem
  literalmente do original; fontes anexadas em todas as peças.
- Os 3 formatos: breve ≤200 palavras · desenvolvida 400–800 · análise (com
  contexto de até 2 artigos do mesmo tema, também extraído).

## 5. Resultados de execução (17/10/2026, corrida final)

**Recolha e arquivo (RF-1.1, RF-1.6)**
- 18 artigos reais: 6 Correio Kianda + 6 Maka Angola + 6 ECO, todos com título, corpo, autor, data, fonte, URL.
- Arquivo integral do HTML servido pela origem, 18/18 com sha256 verificado sobre o conteúdo exatamente arquivado.
- **Bug corrigido nesta corrida:** o hash era calculado sobre os bytes crus mas o arquivo guardava HTML limpo — integridade dava 0/18. Rearquivadas as 18 páginas (HTML como servido) e corrigido `recoletor.py` (hash sobre o conteúdo arquivado). Verificação final: **18/18 íntegros**.

**Classificação (RF-1.3)**
- 18/18 classificados por `regras-palavra-chave` (rotulado; nenhum outro método em uso).
- Validação contra 18 rótulos manuais: **13/18 = 72%**.
- Desvios (todos explicáveis): ids 5 e 6 «Algodão-Doce da AGT» → Economia (a AGT domina o léxico económico, a crítica política é implícita); id 9 dívida de 212,5 M€ → Política (léxico governamental pesa mais que o financeiro); id 14 venda da Visão → Economia (idem); id 18 ECO Quiz TAP → Política (quiz sem corpo denso). É o comportamento esperado de uma heurística lexical e está documentado; correção manual disponível no produto.

**Busca (RF-1.5) — provas de execução**
- `--tema Economia --palavra Sonangol` → 1 resultado (Maka Angola, Fusão Galp-Moeve).
- `--fonte ECO --de 2026-10-01` → resultados com datas ISO corretas.
- `--tema Política --fonte "Maka Angola"` → resultados combinados corretos.

**Redacção (RF-2.1, RF-2.3, RF-2.5)**
- 54 peças geradas (18 artigos × 3 formatos), todas rotuladas `composer-extractivo-sem-llm`.
- Auditoria de limites: **0 de 54 fora de especificação** — breve ≤200 palavras; desenvolvida 400–800; análise com contexto de até 2 artigos do mesmo tema; todas com ≥1 fonte anexada (análises com até 3).
- LLM: o conector Piramyd disponível é de administração (19 ferramentas, nenhuma de inferência) — sem prova de inferência real, o ADR D5 manda usar o fallback extractivo. Foi o que aconteceu. Nenhuma frase é inventada: cada parágrafo vem literalmente do original.

**Estado:** pipeline completa executada de ponta a ponta com dados reais; nada publicado na internet.

