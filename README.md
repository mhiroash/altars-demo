# Altars — Demo Editorial (repositório de leitura)

Demo de plataforma editorial com IA que prova a pipeline completa:
**recolha de portais reais → classificação → redacção assistida → alerta de perfil → composição → exportação PDF/PNG.**

Preparado para o **Esteves Francisco** avaliar o conceito. Uso restrito à equipa Tivra e ao Esteves.

## O que está aqui

| Pasta | Conteúdo |
|---|---|
| `app/` | Aplicação Flask + SQLite: `server.py` (4 ecrãs e API), `exportar.py` (PDF/PNG), `db.py`, `mirex.py` (cliente do portal MIREX), `telegram_notify.py`, `tests/` |
| `pipeline/` | Recolha e redacção: `recoletor.py`, `busca.py`, `classificador.py`, `compositor.py`, `db.py`, provas de recolha |
| `adr/` | `ADR-ALT-2026-001-demo-editorial.md` — decisões de arquitectura |
| `design/` | Design system, UI e verificador de contraste (`check_contrast.py`) |
| `escritor/` | Microcopy da interface e estruturas editoriais |
| `qa/` | Relatórios de auditoria (Gate 2) e verificação final |
| `seguranca/` | Relatório de segurança e provas de sanitização |
| `deploy/` | Guia de deploy e especificação de publicação |
| `plano-execucao.md` | Plano de execução e mapeamento aos requisitos do PRD |
| `PRD-ALT-2026-002.txt` | PRD do demo |

## O que **não** está aqui

- **Base de dados** (dados recolhidos): não é publicada neste repositório.
- **Segredos**: zero tokens, zero chaves, zero `.env`. Verificado com varrimento de padrões (bot token Telegram, `glpat-`, `ghp_`, `sk-`, AWS, `xox`, chave PEM) — nenhuma ocorrência.

## Como ler o demo

O demo a funcionar está num URL próprio com `noindex` (não indexado por motores de busca), publicado após aprovação dos gates de QA e Segurança e do dono do projecto.

## O que o demo prova (e o que não prova)

**Prova:** recolha real de portais angolanos; três tipos de peça (breve, desenvolvida, análise) cada uma com fontes anexadas; alerta de perfil com peça proposta; composição num template editorial; exportação em PDF e PNG.

**Não prova (fora do âmbito desta fase):** perfis Facebook/Instagram, agrupamento de histórias, tendências, variações por destino, publicação directa em WordPress ou redes.

**Honestidade do rótulo:** peças redigidas por IA mostram «Redigida pela IA. Falta a sua revisão.» até aprovação humana. Peças do modo extractivo (sem LLM) mostram «Compilação extractiva — sem LLM». Nenhuma peça é publicada sem revisão humana.

## Licença

Uso restrito — demo privado da equipa Tivra. Todos os direitos reservados.
