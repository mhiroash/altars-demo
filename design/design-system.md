# Altars — Design System do Demo (TASK-2026-10-17-009)

Produto: plataforma editorial "da descoberta da notícia à matéria pronta a publicar".
Princípio estruturante do produto: **"A IA escreve, o humano publica"** — toda a UI torna visível quem decide. Estados «gerado» e «revisto» nunca se misturam visualmente.
Idioma: português de Angola (PT-AO). Tom: editorial sóbrio. Microcopy: `../escritor/microcopy-ui.md`.

## 1. Identidade

Editorial, não SaaS genérico: papel quente, tinta profunda, um acento terracota. A tipografia faz o trabalho — serifada editorial para conteúdo de peças, sans humanista para a interface.

## 2. Cores (tokens CSS custom properties)

### Neutros (papel e tinta)
| Token | Valor | Uso |
|---|---|---|
| `--paper` | `#faf9f7` | fundo da aplicação |
| `--surface` | `#ffffff` | cartões, painéis |
| `--surface-sunken` | `#f3f1ed` | áreas afundadas, código, corpo do editor |
| `--ink-900` | `#1c1917` | texto primário |
| `--ink-700` | `#44403c` | texto secundário |
| `--ink-500` | `#57534e` | texto terciário, metadados (4.6:1 sobre papel) |
| `--ink-300` | `#d6d3d1` | bordas suaves |
| `--ink-200` | `#e7e5e4` | bordas, divisores |

### Acento (marca e ações primárias)
| Token | Valor | Uso |
|---|---|---|
| `--accent-700` | `#7c2d12` | hover de ações primárias |
| `--accent-600` | `#9a3412` | primário: botões, ligações, foco (5.5:1 sobre branco) |
| `--accent-100` | `#ffedd5` | fundo de destaque suave |
| `--accent-50` | `#fff7ed` | fundo de destaque muito suave |

### Semânticas (chips de estado do fluxo editorial)
| Token | Valor | Uso |
|---|---|---|
| `--generated-fg` | `#92400e` | chip `Gerada — requer revisão` (sobre `#fffbeb`) |
| `--generated-bg` | `#fffbeb` | idem |
| `--reviewed-fg` | `#166534` | chip `Revista — pronta a compor` (sobre `#f0fdf4`) |
| `--reviewed-bg` | `#f0fdf4` | idem |
| `--danger-fg` | `#991b1b` | avisos, afirmações sem fonte (sobre `#fef2f2`) |
| `--danger-bg` | `#fef2f2` | idem |
| `--info-fg` | `#1e40af` | notas informativas, demo simulada (sobre `#eff6ff`) |
| `--info-bg` | `#eff6ff` | idem |

Prioridades de alerta: `Urgente` usa `--danger-*`, `Relevante` usa `--generated-*` (âmbar), `Rotina` usa neutro.

## 3. Tipografia

- **Inter** (interface): pesos 400/500/600/700. `font-feature-settings: "cv11","ss01"`.
- **Source Serif 4** (conteúdo de peças, pré-visualização, logótipo): pesos 400/600/700 + itálico.
- Escala (1.25): 12 · 14 · 16 · 20 · 25 · 31 · 39 px. Corpo da UI 14–16; corpo de peça 17/1.7 serifado.
- Datas «17 de outubro», horas «14:32», números «13 000», moeda por extenso «212,5 milhões de euros».

## 4. Espaçamento, raios, sombras

- Grelha 8pt: 4 · 8 · 12 · 16 · 24 · 32 · 48.
- Raios: 6 (chips, inputs) · 10 (cartões) · 14 (painéis) · 999 (pills).
- Sombras multicamadas: `0 1px 2px rgba(28,25,23,.06), 0 1px 3px rgba(28,25,23,.08)` (cartão); `0 4px 12px rgba(28,25,23,.08), 0 12px 32px rgba(28,25,23,.10)` (modal).
- Borda padrão 1px `--ink-200`; foco: anel 2px `--accent-600` + offset 2px.

## 5. Componentes

- **App bar**: logótipo serifado "Altars", separadores (Inbox · Redigir · Alertas · Compor), pesquisa, ação global `Nova peça`.
- **Separador ativo**: texto tinta + sublinhado 2px acento; inativo `--ink-500`.
- **Item da Inbox**: cartão com fonte · data · tema · `Arquivado integralmente`; tema sugerido com ligação `Corrigir`; ação principal `Redigir peça`.
- **Chip de estado**: pill 6px; `Rascunho` (etiqueta cinzenta, "Redigida pela IA. Falta a sua revisão.") e `Revista` (etiqueta verde, "Revista por [nome] às 14:32. Pronta a exportar.") — nunca a mesma cor.
- **Bloco de peça**: bloco nomeado (Antetítulo/Título/Linha fina/Corpo) em `--surface-sunken`, serifado; contagem de palavras por bloco.
- **Painel lateral** (editor): Formato (Breve/Desenvolvida/Análise), Tom, `Redigir peça`, fontes com `Ver original`, instrução de edição.
- **Alerta**: cartão com prioridade, «[Perfil] publicou há [X] min», peça proposta, nota de demo visível («Demo: este alerta é uma simulação com uma fonte real. A monitorização contínua não está ativa.»).
- **Pré-visualização**: cartão com proporção de imagem, «É exatamente isto que sai.»
- **Estados obrigatórios**: vazio (por ecrã, copy do Escritor), loading («A escrever… normalmente leva menos de 20 segundos.»), erro («A geração falhou. Nada se perdeu — tente outra vez.»), desativado (exportação sem revisão + explicação).

## 6. Micro-interações

- Curvas: `cubic-bezier(.2,0,0,1)` (entrada), `cubic-bezier(.4,0,.2,1)` (transição), durações 120–240ms.
- Hover de cartão: elevação 1px + sombra média; nunca transformação de escala em listas.
- Toast de confirmação (arquivo, cópia): 4s, canto inferior.
- `prefers-reduced-motion`: transições desligadas.

## 7. Acessibilidade (WCAG 2.1 AA)

- Todos os pares texto/fundo ≥ 4.5:1 (verificado por `check_contrast.py` neste directório).
- Navegação por teclado: separadores com setas, `aria-selected`, foco visível em tudo.
- Chips de estado têm texto, não só cor; prioridades idem.
- Alvos de toque ≥ 44px em mobile.

## 8. Ficheiros

- `index.html` — os 4 ecrãs numa navegação por separadores (demo clicável).
- `styles.css` — tokens + componentes.
- `app.js` — interações do demo (tabs, gerar, revisão, bloqueio de exportação, copiar).
- `check_contrast.py` — verificação de contraste.
- `verificacao/` — capturas de ecrã.
