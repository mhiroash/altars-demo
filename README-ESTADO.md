# TASK-028 - ponte GitHub para o Builder buscar

Verificado por HTTP publico (raw) em 2026-10-20. Todos os ficheiros abaixo foram reconstruidos a partir do raw e comparados com a origem em disco.

## Ramo `prd-v2` - COMPLETO

### PRD v2.0 (55646 bytes, md5 `d765e3018fff93ad6534d30d6957ac93`, 693 linhas)

Dois caminhos, ambos verificados:

```
# via principal (7 fragmentos)
for i in 1 2 3 4 5 6 7; do curl -sSO https://raw.githubusercontent.com/mhiroash/altars-demo/prd-v2/PRD-v2.0.part$i.b64; done
cat PRD-v2.0.part{1,2,3,4,5,6,7}.b64 | base64 -d | gunzip > PRD-de-produto-v2.0.md
```

```
# via alternativa (4 fragmentos)
for i in 01 02 03 04; do curl -sSO https://raw.githubusercontent.com/mhiroash/altars-demo/prd-v2/PRD.part$i.b64; done
cat PRD.part0{1,2,3,4}.b64 | base64 -d | gunzip > PRD-de-produto-v2.0.md
```

### Prototipo (21048 bytes, md5 `c6ee3a15944c4b0b8a271532fea1fb04`)

```
curl -sSO https://raw.githubusercontent.com/mhiroash/altars-demo/prd-v2/prototipo.html.b64
base64 -d prototipo.html.b64 | gunzip > prototipo.html
```

`proto.part1.b64` + `proto.part2.b64` dao o mesmo resultado.

## Ramo `preview-gate2` - COMPLETO

| Ficheiro | Bytes | md5 |
|---|---|---|
| `index.html` | 24083 | `92e4fa22cdcff7230b065b59c9332959` |
| `app.js` | 7008 | `b446824c333c10396e7e450c7c12266e` |
| `styles.css.gz.b64` | 7584 (b64) | descomprime para `5a3600663bf2b03cd02568da34ca4dc9` (29513 bytes) |

```
base64 -d styles.css.gz.b64 | gunzip > styles.css
```

`index.html` contem `<meta name="robots" content="noindex, nofollow, noarchive, nosnippet, noimageindex">`.

## Pendente: pasta `verificacao/` (8 PNG, 891 KB)

NAO publicada. Em base64 seriam ~300 chamadas de 4000 caracteres ao conector de escrita, cada uma a verificar - inviavel por esta via. Fica para uma execucao com credencial git (clone + push) ou upload manual.

## Limite do conector de escrita (medido)

- 4000 caracteres: chega intacto
- 5000 caracteres: chega intacto
- 14000 caracteres: chega TRUNCADO e CORROMPIDO (6074 bytes, divergencia no char 5994)

Regra: fragmentos <= 4000 caracteres e confirmar sempre o `size` devolvido.

## Divergencia com o pedido original

O pedido indicava PRD com 54973 bytes e 684 linhas; o ficheiro em disco tem 55646 bytes e 693 linhas. Publicou-se o que existe em disco.
