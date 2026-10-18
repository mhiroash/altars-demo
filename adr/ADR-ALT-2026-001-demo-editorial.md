# ADR-ALT-2026-001 — Arquitetura do demo editorial Altars

Data: 2026-10-17 · Autor: Arquiteto (Tivra) · Estado: APROVADO — gate 1 fechado a 17/10/2026 pelo Dev (líder do projecto); o código pode arrancar dentro das decisões D1–D8
Fonte de verdade: PRD-ALT-2026-002 (rascunho v1.0, em /workspace/altars/) · Prazo do demo: 24/10/2026

## 1. Contexto

Demo funcional para provar ao Esteves Francisco a pipeline completa do PRD:
recolha de 1 portal real → redacção assistida (3 formatos, fontes anexadas) →
alerta de perfil (simulado) → composição em template → exportação PDF/PNG/HTML.
Sete dias, equipa pequena, nada publicado sem aprovação do dono.
O demo NÃO é o produto V1: prova o conceito, não a escala (40 fontes / 200 perfis
do PRD ficam para a Fase 1 real).

## 2. Decisões

### D1 — Stack da app: Python + Flask + Jinja, server-rendered
Flask 3.1.3 verificado instalado na nuvem (17/10). Sem framework JS, sem build step.
Código em /workspace/altars/app/. Justificação: 4 ecrãs, 1 utilizador, 7 dias —
o custo de um SPA (build, estado, API JSON) não se paga; abstração sem segundo
caso de uso. Rejeitado: Next/React (build + complexidade sem retorno); Django
(admin/ORM que não vamos usar).

### D2 — Dados: SQLite num único ficheiro (WAL)
sqlite3 3.37.2 verificado. Tabelas: fonte, item, peca, alerta, perfil.
Justificação: a busca combinável (RF-1.5) é SQL; arquivo integral e peças na
mesma base — backup é copiar 1 ficheiro; zero operação. Rejeitado: Postgres
(um serviço para gerir que o demo não justifica); ficheiros JSON (sem busca
indexada). Escala do demo ~10³ itens: 3 ordens abaixo do limite prático do SQLite.

### D3 — Recolha: VerAngola primário, fetch respeitoso, arquivo integral
Verificado a 17/10: robots.txt do VerAngola permite tudo (excepto /va/admin*,
/va/api*, /va/_statistics/); as páginas servem com curl normal (HTTP 200).
Regras: UA identificável («AltarsDemo/0.1 + contacto»), intervalo ≥5 s entre
pedidos, backfill inicial + refresco agendado leve (cron 15 min); guardar HTML
integral + texto extraído + metadados (título, autor, data, fonte, URL) — RF-1.1/1.6.
RSS do VerAngola NÃO verificado (os caminhos testados devolvem HTML): o Agentes
valida o feed real ou a recolha por listagem HTML antes de fechar — é o risco 1.
Angop como alternativa: robots OK com Crawl-delay 5, mas as páginas HTML estão
atrás de challenge de JS (503 verificado) — exigiria fetch via browser
(Playwright disponível). Só se o VerAngola falhar.

### D4 — Classificador: regras de palavras-chave nas 6 categorias do PRD
Rotulado na UI como «heurística». Justificação: auditável, corre no mesmo
processo, custo zero; no demo, uma classificação errada corrigível à mão custa
menos do que manter e medir um modelo. Rejeitado: classificador por embeddings
(bge-m3 disponível no Piramyd) — mais uma peça de pipeline para provar uma
qualidade que este demo não mede.

### D5 — Motor de redacção: LLM do Piramyd (provider interno), CONDICIONADO a prova real
Verificado a 17/10 no Piramyd: provider interno «workers-ai» corre no binding da
própria plataforma — sem chave, sem chamada HTTP externa, 1000 rpm; modelos de
chat activos: claude-haiku-5.5 (ctx 1M) e deepseek-v4-flash (ctx 1M), ambos beta.
Cumpre a regra do contexto: modelo mais barato suficiente, sem chamadas externas
de custo. CONDIÇÃO DE GATE: o log de pedidos reais está vazio hoje — antes de a
redacção depender disto, o Agentes prova 1 inferência real end-to-end
(prompt → texto → registo no live_requests). Sem essa prova, entra o fallback.
Fallback (já desenhado): compositor extractivo — lead = primeira frase da fonte,
corpo = parágrafos selecionados da fonte com citação, rotulado na UI como
«compilação extractiva — não gerado por IA». Nunca fabricar texto.
Os 3 formatos (breve ≤200 / desenvolvida 400–800 / análise) são controlo de
comprimento e estrutura sobre o mesmo motor; fontes anexadas (RF-2.5) são
obrigatórias nos dois caminhos. Tom (RF-2.4) entra como parâmetro do prompt,
se o tempo deixar — não é critério do demo.

### D6 — Alerta de perfil: simulado com fonte real, rotulado
1 perfil público (ministério/instituição) semeado com publicação real arquivada;
o alerta dispara do item arquivado, com latência apresentada como simulação e
rotulado «SIMULAÇÃO» no painel (RF-3.2/3.4). Telegram via bot com token de teste
(RF-3.3). Rejeitado: monitorização real de FB/IG — fora do demo (o PRD marca o
acesso restringido; a validação técnica é da Fase 2).

### D7 — Template + exportação: Jinja fixo → HTML; PDF/PNG por Playwright
Template único de composição fixa (antetítulo, título, imagem, corpo, assinatura)
— RF-4.4. Exportação: HTML nativo; PDF e PNG por Playwright + Chromium
(verificado: chromium-1248 em ~/.cache/ms-playwright). Rejeitado: weasyprint
(dependências extra, fidelidade pior); serviço externo de render (custo + dados
do cliente para fora).

### D8 — UI e publicação: 4 ecrãs server-rendered em PT-AO, noindex até aprovação
Ecrãs: arquivo/busca · item + redacção · alertas · peça composta + exportação.
Meta noindex + header X-Robots-Tag: noindex enquanto não houver APR do dono.
O visual é do Product Designer; este ADR fixa só a moldura técnica.

## 3. Riscos e mitigação
1. Feed/portal instável → Agentes valida 1 principal + 2 alternativas antes de fechar (plano).
2. Prova de inferência LLM falhar → fallback extractivo rotulado; o demo continua honesto.
3. Angop inacessível sem browser → Playwright como fetch de último recurso, ou ficar no VerAngola.
4. Fidelidade do PDF/PNG → testar exportação no dia 1 do Dev, não no fim.
5. Escopo cresce → a lista «fora do demo» é fechada; pedidos novos vão para pós-demo.
6. Publicação sem aprovação → noindex + APR do dono antes de qualquer URL público.

## 4. Fora do demo (vinculativo)
Perfis FB/IG reais, agrupamento de histórias, tendências, variações por destino,
publicação automática, CMS de terceiros, apps nativas, fluxos de aprovação.

## 5. Verificações feitas (provas de 17/10/2026)
- pip install flask feedparser → OK (Flask 3.1.3, feedparser 6.0.14).
- Python 3.10.12 · Node 22.23.3 · sqlite3 3.37.2.
- Playwright: chromium-1248 presente em ~/.cache/ms-playwright.
- robots.txt VerAngola (Allow: /) e Angop (Crawl-delay: 5) lidos.
- Angop /angop/index.php e /angop/rss/ → 503 com challenge de JS.
- VerAngola /rss/, /rss.xml, /feed/, /rss/news/ → HTML (feed não encontrado nos caminhos testados).
- Piramyd: 20 providers, 94 chaves; workers-ai interno sem chave; 2 modelos de chat activos; live_requests vazio.

## 6. Próximo passo
Aprovação deste ADR (gate 1) → Dev integra; Agentes fecha portal + prova LLM;
Product Designer e Escritor trabalham contra as 4 telas do D8.