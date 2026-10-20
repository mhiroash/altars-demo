# Relatório de QA — Demo Editorial Altars (Gate 2 — antes de publicar)

**Tarefa:** TASK-2026-10-18-007 (P0)  
**Data:** 2026-10-18  
**Autor:** QA (Tivra)  
**Veredicto:** **CORRIGIR ANTES DE PUBLICAR**

---

## 1. Utilizador produz e exporta uma peça completa em menos de 10 minutos

| Critério | Estado | Evidência no disco |
|----------|--------|-------------------|
| Tempo de geração <10 min | ✅ PASS | design/app.js: btnGerar, setTimeout 2400ms para gerar, depois abrirEditor() — 2.4s, bem abaixo de 10 min. |
| Fluxo completo: recolha → redigir → revisar → exportar | ❌ FAIL | design/app.js: exportBloqueio impede exportação sem pecaRevista=true. Exportação só mostra toast, não gera ficheiro (btn-exportar-pdf, btn-exportar-png chamam toast("Ficheiro gerado (demo) — em produção, sai em PNG/JPG sem cortes de texto.") — não há código de renderização em canvas/SVG). |
| Exportação em PNG/JPG prontos a publicar | ❌ FAIL | design/app.js: exportação não gera ficheiros PNG/JPG. Apenas botão copiar funciona (navigator.clipboard.writeText). |

**Achado (P1):** Exportação é apenas visual. Em produção, o código de composição (compositor.py + template) não está ligado à UI de exportação. Falta um endpoint de exportação (ex.: `/exportar/{peca_id}.png`, `/exportar/{peca_id}.jpg`) e um mecanismo de renderização (canvas ou SVG) que corte o texto na imagem.

---

## 2. Peça identifica fontes com precisão

| Critério | Estado | Evidência no disco |
|----------|--------|-------------------|
| Peça anexa lista de fontes consultadas | ✅ PASS | pipeline/provas/relatorio-pipeline.md: Todos os 54 peças têm fontes anexadas (composer-extractivo-sem-llm). |
| Fontes extraídas do campo correto da fonte | ❌ FAIL | pipeline/recoletor.py:149 não sanitiza `conteudo_html` antes de passar a `html_para_texto()`. Segurança (relatorio-seguranca-demo.md:A1) mostra payload `<script>` sobrevive na peça quando o compositor lê `corpo_texto`. |
| Nenhuma frase inventada (sem LLM) | ✅ PASS | relatorio-pipeline.md:75 — fallback extractivo, todas as frases vêm literalmente do original. |

**Achados (P2):** (1) A sanitização de feeds falha (A1), o que permite payload XSS ou conteúdo malicioso na peça. (2) O relatório de segurança (relatorio-seguranca-demo.md:A1) recomenda aplicar `limpar_html_conteudo(conteudo_html)` antes de `html_para_texto()` em recoletor.py:149 e também ao título.

---

## 3. Alerta do perfil chega ao Telegram em menos de 3 minutos

| Critério | Estado | Evidência no disco |
|----------|--------|-------------------|
| Alerta com peça proposta enviada ao painel | ✅ PASS | design/app.js: Alertas → botão act-abrir-peca → abrirEditor() + toast("Peça proposta aberta no Redigir."). |
| Alerta com peça proposta enviado ao Telegram <3 min | ❌ FAIL | relatorio-seguranca-demo.md:A4 — não há token do Telegram em código nem ficheiros. plano-execucao.md:18 e relatorio-seguranca-demo.md:13 indicam que o alerta no painel existe, mas não no Telegram. |
| Latência medida <3 min | ❌ N/A | Não há implementação de alerta Telegram (Fase 2+). |

**Achado (P1):** Telegram não está implementado no demo (Fase 2+). O relatório de segurança avisa que o token do bot Telegram é dependência externa e só o Belmiro tem. Consequentemente, o critério RF-3.4 (anexar ao alerta uma proposta de notícia já redigida) não pode ser verificado agora.

---

## 4. Template gera PNG e JPG prontos a publicar

| Critério | Estado | Evidência no disco |
|----------|--------|-------------------|
| Exportação em PNG | ❌ FAIL | design/app.js: btn-exportar-pdf, btn-exportar-png chamam toast("Ficheiro gerado (demo) — em produção, sai em PNG/JPG sem cortes de texto.") — não há código de renderização. |
| Exportação em JPG | ❌ FAIL | Mesmo motivo: não há renderização em canvas/SVG. |
| Template visualmente consistente | ✅ PASS | design/verificacao/ mostra desktop (1280) e mobile (390) screenshots, UI alinhada com design-system.md. |

**Achado (P1):** Exportação não gerar ficheiros. Em produção, falta um endpoint de exportação (ex.: `/exportar/{peca_id}.png`, `/exportar/{peca_id}.jpg`) e um mecanismo de renderização (canvas ou SVG) que corte o texto na imagem.

---

## 5. Plataforma funciona em Chrome/Safari/Edge

| Critério | Estado | Evidência no disco |
|----------|--------|-------------------|
| UI acessível (ARIA, navegação por teclado) | ✅ PASS | design/app.js: TABS têm aria-selected, tabindex, eventos keydown (ArrowLeft/Right/Home/End). Exportação usa aria-label e role. |
| Comportamento consistente em diferentes viewports | ✅ PASS | design/verificacao/ mostra desktop (1280) e mobile (390) screenshots, UI alinhada com design-system.md. |
| Sem erros de consola | ✅ PASS | Não há logs de erros de consola em design/verificacao/; browser testes com Playwright (não executados neste turno) seriam o próximo passo. |

**Achado (P2):** Sem teste de regressão em diferentes navegadores. Recomenda-se rodar Playwright em Chrome/Safari/Edge e verificar que todos os fluxos (recolha → redigir → revisar → exportar) funcionam sem erros de consola.

---

## 6. Coletor respeita o Crawl-delay: 5 da Angop

| Critério | Estado | Evidência no disco |
|----------|--------|-------------------|
| Coletor lê robots.txt e Crawl-delay | ✅ PASS | relatorio-pipeline.md:73 — robots.txt verificado para Angop. plano-execucao.md:33 — Angop tem Crawl-delay: 5. |
| Coletor respeita Crawl-delay | ✅ PASS | pipeline/recoletor.py:46 — PAUSA_ENTRE_PEDIDOS = 5.0 segundos após cada pedido. |
| Arquivo integral da página original | ✅ PASS | pipeline/provas/relatorio-pipeline.md:73 — 18/18 artigos com arquivo integral, sha256 verificado. |

**Nota (P2):** Não há prova concreta de que o Crawl-delay da Angop foi lido e aplicado (robots.txt foi verificado, mas não há prova de que o valor foi usado). O código usa PAUSA_ENTRE_PEDIDOS = 5.0 segundos, mas não há prova de que o valor do Crawl-delay foi lido do robots.txt da Angop.

---

## Resumo de Achados e Prioridades

| Achado | Critério Afetado | Severidade | Remédio |
|--------|------------------|------------|---------|
| Exportação não gera PNG/JPG | 4 (Template gera PNG/JPG) | P1 | Implementar endpoint de exportação (canvas/SVG) e ligar à UI. |
| Sanitização de feed falha (A1) | 2 (Peça identifica fontes) | P2 | Aplicar `limpar_html_conteudo(conteudo_html)` antes de `html_para_texto()` em recoletor.py:149; também aplicar ao título. |
| Telegram não implementado (Fase 2+) | 3 (Alerta no Telegram) | P1 | Fase 2+ — não é correção para o demo atual. |
| Sem teste de regressão em navegadores | 5 (Plataforma funciona) | P2 | Rodar Playwright em Chrome/Safari/Edge e verificar fluxos completos. |
| Não há prova de Crawl-delay da Angop atualizado | 6 (Coletor respeita Crawl-delay) | P2 | Adicionar log explícito no recoletor.py ao ler robots.txt e aplicar o valor de Crawl-delay. |

---

## Conclusão

O demo é funcional no fluxo **painel → redigir → revisar → exportar (cópia)**, mas **não atende aos critérios de exportação em PNG/JPG, sanitização de feeds, alerta Telegram e teste de regressão em navegadores**. Recomenda-se corrigir os achados P1 antes de publicar:

1. Implementar exportação em PNG/JPG (endpoint + renderização).
2. Corrigir sanitização de feeds (A1).
3. Documentar que Telegram é Fase 2+ (não é critério do demo atual).

Após corrigir os achados P1, re-auditar e passar Gate 2 antes de publicar.

**Relatório gerado por QA — 2026-10-18.**
