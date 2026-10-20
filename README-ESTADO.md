# TASK-028 - estado da ponte GitHub

Gerado por DevOps em 2026-10-20. Este ramo existe para o Builder conseguir buscar o PRD v2.0 e o prototipo.

## O que esta pronto e verificado

### Ramo `preview-gate2` - COMPLETO

Os tres ficheiros do preview estao no ramo e foram verificados por HTTP publico (raw), com md5 igual a origem em disco:

| Ficheiro | Bytes | md5 | Nota |
|---|---|---|---|
| `index.html` | 24083 | `92e4fa22cdcff7230b065b59c9332959` | contem meta robots noindex |
| `app.js` | 7008 | `b446824c333c10396e7e450c7c12266e` | |
| `styles.css.gz.b64` | 7584 (b64) | descomprime para `5a3600663bf2b03cd02568da34ca4dc9` | ver abaixo |

O CSS esta comprimido porque o conector de escrita trunca payloads grandes. Para obter o `styles.css` real (29513 bytes):

```
base64 -d styles.css.gz.b64 | gunzip > styles.css
```

Resta publicar a pasta `verificacao/` (8 capturas PNG, 888 KB): NAO esta no ramo. Cada PNG ocupa 50 a 210 KB em base64 e o limite seguro do conector e de 5000 caracteres por chamada, o que daria cerca de 45 chamadas.

### Ramo `prd-v2`

- `proto.part1.b64` + `proto.part2.b64` -> `cat proto.part1.b64 proto.part2.b64 | base64 -d | gunzip > prototipo.html` = 21048 bytes, md5 `c6ee3a15944c4b0b8a271532fea1fb04`, igual a origem. VERIFICADO.
- `PRD-de-produto-v2.0.md` (55646 bytes, md5 `d765e3018fff93ad6534d30d6957ac93`): em publicacao por fragmentos.

## Limite do conector de escrita (medido)

- 4000 caracteres: chega intacto
- 5000 caracteres: chega intacto
- 14000 caracteres: chega TRUNCADO e CORROMPIDO (6074 bytes, divergencia no char 5994)

Regra: fragmentos de no maximo 4000 caracteres, e confirmar sempre o `size` devolvido pela ferramenta.

## Divergencia com o pedido original

O pedido indicava PRD com 54973 bytes e 684 linhas; o ficheiro em disco tem 55646 bytes e 693 linhas. Publica-se o que existe em disco.
