# Altars — Plano de Execução do Demo (PRD-ALT-2026-002)

**Projecto:** Altars — Demo Editorial · **Líder:** Dev
**Objectivo:** demo funcional que prova a pipeline completa ao Esteves Francisco (sócio da Ellocene)
**Prazo final:** 24/10/2026 · **Escrito:** 17/10/2026
**Fonte de âmbito:** `altars-demo-contexto` (Mhiro Ash) + PRD-ALT-2026-002 v1.0

---

## 1. O que o demo tem de provar (âmbito fechado)

Pipeline completa, ponta a ponta, em 1 portal real e 1 perfil real:

| # | Capacidade | Requisito PRD | Prova no demo |
|---|---|---|---|
| 1 | Recolha de 1 portal real | RF-1.1, RF-1.3, RF-1.5, RF-1.6 | Itens arquivados de Angop **ou** VerAngola, com robots.txt e rate limit respeitados |
| 2 | Redacção assistida, 3 tipos de peça | RF-2.1, RF-2.3, RF-2.5 | Breve + desenvolvida + análise, cada uma com lista de fontes anexada |
| 3 | Alerta de 1 perfil público | RF-3.2, RF-3.4 | Publicação detetada → alerta no painel **e** no Telegram, com peça proposta, <3 min |
| 4 | Composição e exportação | RF-4.4, RF-5.3 | Peça composta em 1 template editorial, exportada em PDF e PNG |

**Fora do demo (não construir agora):** perfis Facebook/Instagram, agrupamento de histórias, tendências, variações por destino, WordPress/publicação direta a redes.

---

## 2. Factos técnicos verificados (17/10, por Dev)

Estes não são pressupostos — foram confirmados agora e mudam decisões do plano.

### 2.1 Portais — recolha

| Portal | robots.txt (verificado) | Estrutura | Decisão |
|---|---|---|---|
| **Angop** (`angop.ao`) | `User-agent: *` / `Crawl-delay: 5` / sitemaps `sitemap_news.xml`, `sitemap.xml` | HTML server-rendered; artigo com `<h1>`, parágrafos, assinatura `AG/CS`; sitemap de notícias disponível | **Escolhido.** `Crawl-delay: 5` é explícito e fácil de respeitar; o sitemap dá descoberta limpa |
| **VerAngola** (`verangola.net`) | `User-agent: *` / `Allow: /` / `Disallow: /va/_statistics/`, `/va/admin*/`, `/va/api*/` | — | Alternativa. `verangola.com` não resolve; o domínio vivo é `.net` |

**Decisão:** recolher da **Angop**. Motivo: `Crawl-delay: 5` explícito (baixo risco de bloqueio), sitemap de notícias para descoberta, HTML estável e server-rendered (sem browser headless). Nota operacional: a Angop devolveu **503 transitório** na primeira visita do dia e 200 na segunda — o coletor tem de ter retry com backoff, não pode falhar ao primeiro erro.

### 2.2 Perfil monitorizado — alerta

| Candidato | Verificação | Decisão |
|---|---|---|
| **MIREX** (`mirex.gov.ao`) | Portal SPA com **API JSON pública**: `GET /Componentes/api/publicacao/listarPublico` (lista) e `GET /Componentes/api/publicacao/buscar/{id}` (peça completa, devolve `descricao` em HTML + metadados). `robots.txt` devolve 404 (sem restrições declaradas). | **Escolhido.** |
| Ministério da Cultura (`mincult.gov.ao`) | Devolve a página por omissão do Nginx Proxy Manager — **portal não está no ar** | Descartado |
| Ministério do Interior (`mint.gov.ao`) | DNS não resolve | Descartado |

**Decisão:** monitorizar o **MIREX** via API JSON, não por scraping. É mais robusto, mais rápido e não depende de renderizar a SPA (que emite 43 erros de consola). O `robots.txt` a 404 significa que não há regras declaradas; ainda assim, o coletor identifica-se e limita a frequência — recolhas mínima e proporcional, como manda o PRD.

### 2.3 Modelos de redacção — "o mais barato suficiente"

Dados de uso real do Piramyd (últimos 7 dias), consultados por Dev:

| Modelo | Provider | Pedidos 7d | Sucesso | Custo médio/pedido | Latência média |
|---|---|---|---|---|---|
| `glm-5.3-flash` | xeribot | 1.623 | 100% | **$0,0024** | 22,1 s |
| `deepseek-v4.1-flash` | xeribot | 25.008 | 100% | $0,0033 | 11,7 s |
| `glm-5.2` | xeribot | 3.999 | 100% | — | 8,0 s |
| `deepseek-v4.1-flash` | inception | 903 | 98,5% | $0,0037 | — |
| `kairos` | workers-ai | 5.979 | 99,8% | $0,0000 (grátis) | — (sem dados de latência) |

**Decisão de custo/qualidade:** usar **`deepseek-v4.1-flash` (xeribot)** como modelo principal de redacção. É o mais barato *com latência comprovada* (11,7 s, alinhado com o requisito de <20 s do PRD) e tem 25.008 pedidos a 100% de sucesso — fiabilidade provada. O `glm-5.3-flash` é marginalmente mais barato por pedido mas a 22 s de média arrisca estourar o limite de 20 s. O `kairos` (grátis) fica como **fallback** se o custo apertar. Esta escolha é do Agentes (camada de modelos), que a pode ajustar com prova.

---

## 3. Entregáveis

| # | Entregável | Ficheiro/pasta | Responsável |
|---|---|---|---|
| E1 | ADR do demo (desenho aprovado antes de código) | `/workspace/altars/adr-demo.md` | Arquiteto |
| E2 | Coletor Angop + arquivo + cliente MIREX | `/workspace/altars/coletor/` | Agentes |
| E3 | Camada de redacção (3 tipos + fontes anexadas) | `/workspace/altars/redacao/` | Agentes |
| E4 | Design system + template editorial | `/workspace/altars/design/` | Product Designer |
| E5 | App (painel, alerta, exportação PDF/PNG) | `/workspace/altars/app/` | Agentes |
| E6 | Textos do demo (peças de exemplo, microcopy) | `/workspace/altars/escritor/` | Escritor |
| E7 | Preview noindex + repositório de leitura | `/workspace/altars/deploy/` | DevOps |
| E8 | Relatório de auditoria QA | `/workspace/altars/qa/` | QA |
| E9 | Relatório de segurança | `/workspace/altars/seguranca/` | Segurança |
| E10 | Este plano + lista de tarefas na fila | este ficheiro | Dev |

---

## 4. Ordem de execução e gates

Gates do Builders, aplicados a este demo:
- **Gate 1 (antes de código):** ADR do Arquiteto aprovado pelo líder.
- **Gate 2 (antes de publicar):** QA **e** Segurança verificam.
- **Gate 3 (antes de sair para fora):** aprovação explícita do Belmiro. Nada é publicado sem ela.

```
[17/10]  ADR do Arquiteto (E1) ──────────────┐
                                              ▼
[18–19/10]  Coletor + Redacção (E2, E3) ──► App (E5) ◄── Design (E4) + Textos (E6)
                                              │
[20–21/10]                                    ▼
                              Auditoria QA (E8) + Segurança (E9)
                                              │
[21–22/10]                                    ▼
                              Preview noindex + repo leitura (E7)
                                              │
[23/10]                                       ▼
                              Aprovação do Belmiro (Gate 3) → demo ao Esteves
```

**Caminho crítico:** E1 → E2/E3 → E5 → E8/E9 → E7 → aprovação do Belmiro.
**Paralelizável com o caminho crítico:** E4 (design) e E6 (textos) arrancam já, sem esperar pelo ADR, desde que respeitem os requisitos não funcionais já extraídos (`altars-prd-extracto-design`).

---

## 5. Riscos

| Risco | Probabilidade | Impacto | Mitigação |
|---|---|---|---|
| Angop bloqueia ou degrada a recolha | Média | Alto | `Crawl-delay: 5` respeitado; retry com backoff (o 503 observado prova que é preciso); arquivo integral em disco para o demo não depender de rede ao vivo |
| API do MIREX muda ou cai | Média | Alto | Contrato testado e fixado em teste; arquivo da publicação original para validar o alerta offline |
| Latência de redacção > 20 s | Média | Médio | Modelo escolhido mede 11,7 s; `kairos` como fallback; geração em streaming para o painel |
| Alerta não chega em <3 min | Média | Alto | Token do bot Telegram é dependência externa (ver §6); polling do MIREX a 60 s; medição real no ensaio |
| Exportação PDF/PNG com cortes de texto | Média | Médio | Critério de aceitação explícito do PRD; QA verifica com peças de comprimento extremo |
| Nada publicado sem aprovação do Belmiro | — | Crítico | Preview em `noindex`; repositório privado de leitura; pedido de aprovação formal antes de qualquer URL público |

---

## 6. Dependências externas (a desbloquear, não é trabalho de código)

1. **Token do bot Telegram** — sem ele o alerta não sai para o Telegram (RF-3.4). É um dado que só o Belmiro tem. Sinalizado ao chefe de equipa; o resto do alerta (painel) não depende disto.
2. **Aprovação do Belmiro** para publicar o URL do demo (Gate 3).

---

## 7. Decisões tomadas neste plano (âmbito ambíguo do PRD)

O PRD descreve o produto completo; o demo prova só a pipeline. Onde o PRD era ambíguo para o demo, decidi e documento:

1. **Portal único:** Angop (não os 20 da Fase 1). O demo prova o *mecanismo* de recolha, não a escala.
2. **Perfil único:** MIREX via API JSON. Prova o alerta sem tocar em Facebook/Instagram (fora do âmbito).
3. **Modelo de redacção:** `deepseek-v4.1-flash` (xeribot), com prova de custo e latência acima.
4. **Persistência do demo:** arquivo em disco (ficheiros + SQLite), não a base de 24 meses do produto. O demo prova o fluxo, não o repositório histórico.
5. **Autenticação:** o demo corre em modo de leitura para o Esteves; autenticação multi-utilizador com perfis de acesso é Fase 2+, fora do demo.

---

## 8. Tarefas criadas na fila do projecto

Ver secção seguinte, sincronizada com a fila (`tivra-team tasks`). Cada tarefa tem responsável, prioridade e prazo.

| Tarefa | Responsável | Prioridade | Prazo |
|---|---|---|---|
| ADR do demo | Arquiteto | P0 | 18/10 |
| Coletor Angop + cliente MIREX | Agentes | P0 | 19/10 |
| Camada de redacção (3 tipos) | Agentes | P0 | 19/10 |
| Design system + template editorial | Product Designer | P1 | 19/10 |
| Textos e peças de exemplo | Escritor | P1 | 20/10 |
| App (painel, alerta, exportação) | Agentes | P0 | 21/10 |
| Auditoria QA | QA | P0 | 22/10 |
| Gate de segurança | Segurança | P0 | 22/10 |
| Preview noindex + repo de leitura | DevOps | P1 | 22/10 |