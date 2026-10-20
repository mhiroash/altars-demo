# Altars — Microcopy dos 4 ecrãs + alerta + template (RF-1.x, RF-2.x, RF-3.x, RF-4.x, RF-5.3)

Idioma: português de Angola (PT-AO). Tom: editorial sóbrio — a Altars fala como uma redação, não como uma app de consumo. Autor: Escritor, 17/10/2026. Para o Product Designer: os nomes de ecrã, estados e rótulos aqui definidos são os oficiais da demo; qualquer divergência, vale este ficheiro.

## Voz e tom (regras transversais)

- Frases de até 20 palavras. Zero voz passiva. Zero jargão de sistema («processar», «sincronizar»).
- A máquina nunca fala na primeira pessoa («encontrei», «gerei») — diz «a peça está pronta», não «eu gerei a peça».
- «A IA escreve, o humano publica» é a regra do produto: toda a copy distingue o que a máquina fez do que falta ao humano decidir.
- Números com unidade sempre: «212,5 milhões de euros», não «212,5M».
- Datas por extenso curto: «17 de Outubro de 2026», não «17/10/26».
- Erros: dizer o que aconteceu, porquê e o que fazer — nesta ordem. Nunca culpar o utilizador.

## Glossário oficial (usar sempre estes termos, nunca sinónimos)

| Termo oficial | Nunca escrever |
|---|---|
| peça | artigo, post, conteúdo |
| fonte | origem, referência |
| redigir / redação | gerar, gerado (na interface visível) |
| rever / revisão | validar, aprovar (reservado a «publicar») |
| arquivo | histórico, repositório |
| perfil monitorizado | fonte social, conta |
| alerta | notificação, aviso |
| exportar | download, guardar |
| rascunho | draft, esboço |

---

## Ecrã 1 — Inbox (recolha e pesquisa)

**Cabeçalho e navegação:**
- Nome do produto: **Altars** (sozinho, sem «plataforma»).
- Separadores: **Inbox · Redigir · Alertas · Compor** (nesta ordem; é o fluxo do PRD).
- Subtítulo da Inbox: «O que chegou das suas fontes hoje.»

**Lista de itens recolhidos (RF-1.1, RF-1.3):**
- Rótulo de cada item: fonte em maiúsculas pequenas (ECO · MAKa ANGOLA · CORREIO KIANDA), título, hora «há 12 minutos», tema como etiqueta.
- Etiquetas de tema (RF-1.3, as 6 oficiais): **Economia e Finanças · Política · Sociedade · Entretenimento · Desporto · Outros**.
- Estado do arquivo: «Arquivado integralmente» quando o original está guardado (RF-1.6).

**Pesquisa (RF-1.5):**
- Placeholder do campo: «Pesquise por palavra, pessoa, tema ou fonte.»
- Botão: **Pesquisar**
- Filtros (etiquetas dos controlos): **Tema · Fonte · Data · Palavra-chave**
- Estado vazio da pesquisa: «Nada corresponde a esta pesquisa. Experimente alargar a data ou limpar um filtro.» + botão **Limpar filtros**
- Resultados: «X peças correspondem.» (nunca «resultados encontrados»)

**Estado vazio da Inbox (primeira visita):** «As suas fontes ainda não enviaram nada hoje. A recolha corre a cada 30 minutos.»
**Ação principal do item:** **Redigir peça** (leva ao Ecrã 2 com o item pré-selecionado).

---

## Ecrã 2 — Redigir (editor)

**Cabeçalho do ecrã:** **Redigir** · subtítulo: «Escolha o formato, o tom e a peça sai pronta a rever.»

**Painel de configuração (RF-2.3, RF-2.4):**
- Secção **Formato**: **Breve** (até 200 palavras) · **Desenvolvida** (400–800) · **Análise** (com contexto)
- Secção **Tom**: **Informativo neutro** · **Institucional** · **Institucional-promocional** — cada um com uma linha de ajuda:
  - Informativo neutro: «Factos e números, sem avaliação. Para notícia pura.»
  - Institucional: «Voz de organização: formal, ponderada, sem promoção.»
  - Institucional-promocional: «Voz de organização que destaca as próprias conquistas.»
- Botão principal: **Redigir peça**
- Estado a processar (RF: <20 s): «A redigir a partir de X fontes…» (barra de progresso; nunca «a pensar» nem «a processar»)

**Editor (RF-2.1, RF-2.5, RF-2.6):**
- Campos por ordem: **Antetítulo · Título · Linha fina · Corpo** (nomes do PRD; a «linha fina» é o lead).
- Etiqueta do painel de fontes: **Fontes desta peça** — cada fonte com título, data e ligação «Ver original».
- Sugestões de edição (RF-2.6): placeholder «Peça uma alteração…» + exemplos clicáveis: «Encurta» · «Mais formal» · «Acrescenta o contexto de ontem»
- Contador: «X palavras · dentro da faixa» / «X palavras · acima da faixa (máx. 800)»
- Sinalização RF-2.8: frase sem fonte marcada a amarelo com etiqueta «Sem fonte — confirme ou remova antes de publicar.»

**Estados da peça (os dois estados do produto, visualmente distintos):**
- **Rascunho** — «Redigida pela IA. Falta a sua revisão.» (etiqueta cinzenta)
- **Revista** — «Revista por [nome] às 14:32. Pronta a exportar.» (etiqueta verde)
- Botão que muda o estado: **Marcar como revista** (nunca «Aprovar» — reservado ao publicar).

**Ações do editor:** **Guardar rascunho** · **Redigir de novo** · **Marcar como revista**

---

## Ecrã 3 — Alertas (RF-3.2, RF-3.4; demo simulado)

**Cabeçalho:** **Alertas** · subtítulo: «O que os perfis monitorizados publicaram, em minutos.»

**Aviso de demo (visível e permanente):** «Demo: este alerta é uma simulação com uma fonte real. A monitorização contínua não está ativa.» — em faixa discreta no topo do ecrã.

**Cartão de alerta:**
- Cabeça do cartão: **[Perfil]** publicou há **X minutos** · etiqueta de prioridade: **Rotina · Relevante · Urgente** (RF-3.6)
- Corpo: **Peça proposta** — a peça já redigida (RF-3.4), nos mesmos campos do editor, com estado «Rascunho».
- Ações: **Abrir no editor** · **Ver publicação original** · **Silenciar este perfil** (RF-3.5)
- Estado vazio: «Nada dos seus perfis nas últimas 24 horas.»

**Mensagem de Telegram (RF-3.3, versão curta):**
> **Altars — alerta**
> [Perfil] publicou há X minutos.
> [Título da peça proposta]
> Rever no painel: [ligação]

---

## Ecrã 4 — Compor e exportar (RF-4.4, RF-5.3)

**Cabeçalho:** **Compor** · subtítulo: «A peça revista, pronta no modelo editorial.»

**Bloqueio de segurança (regra do produto):** se a peça ainda é rascunho, o ecrã mostra: «Esta peça ainda não foi revista. Revise-a antes de compor.» + botão **Ir para o editor**. A composição só abre em peça revista.

**Template (RF-4.4) — rótulos dos campos:** **Antetítulo · Título · Imagem · Corpo · Assinatura**
- Sobre a imagem: «Imagem sugerida» + crédito «Fotografia: [autor/licença]» (RF-4.7). Botões: **Usar sugerida** · **Carregar própria**
- Assinatura: «Fonte: [nome da fonte] · Redigido com assistência de IA · Revisto por [nome]» — esta linha é obrigatória em todas as peças compostas.

**Pré-visualização e exportação (RF-5.2, RF-5.3):**
- Etiqueta: **Pré-visualização** (nunca «preview»)
- Botões de exportação: **Exportar PDF** · **Exportar PNG** · **Copiar texto**
- Confirmação: «PDF exportado.» / «PNG exportado.» / «Texto copiado.»
- Estado vazio (sem peça selecionada): «Escolha uma peça revista para compor.» + botão **Ver peças revistas**

---

## Mensagens de erro (padrão único)

Padrão: [o que aconteceu]. [porquê, em meia linha]. [o que fazer].

| Situação | Mensagem |
|---|---|
| Fonte indisponível na recolha | «Não foi possível ler [fonte] nesta ronda. O site pode estar fora do ar. Tentamos de novo na próxima ronda.» |
| Pesquisa sem resultados | «Nada corresponde a esta pesquisa. Experimente alargar a data ou limpar um filtro.» |
| Redação falhou | «A redação não concluiu. As fontes estão guardadas — tente de novo sem sair desta peça.» |
| Exportação falhou | «A exportação falhou. A peça continua guardada e revista. Tente novamente.» |
| Peça sem fontes anexadas | «Esta peça não tem fontes anexadas. Nenhuma peça sai sem fontes.» |
| Frase sem fonte (RF-2.8) | «Sem fonte — confirme ou remova antes de publicar.» |

## Confirmações (padrão único)

Verbo no particípio + ponto. Sem exclamação, sem emoji.
- «Rascunho guardado.» · «Peça marcada como revista.» · «PDF exportado.» · «PNG exportado.» · «Texto copiado.» · «Perfil silenciado.» · «Filtros limpos.»
