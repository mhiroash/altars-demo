#!/usr/bin/env python3
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
"""Altars — validação do classificador heurístico contra rótulos manuais.

Método (honesto e declarado): um leitor (o agente) atribui a categoria correta
a uma amostra lendo título + corpo; compara-se com a saída do classificador de
regras. Não é ground truth independente — é uma verificação de coerência da
heurística, rotulada como tal no relatório.
"""
import json
import sqlite3
import sys

from db import DB_PATH
from classificador import classifica

# Rótulos manuais: {id_artigo: categoria_manual}
# Preenchidos pela leitura de título + corpo de cada artigo da amostra.
ROTULOS = json.load(open("provas/rotulos_manuais.json"))


def main():
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    acertos, total = 0, 0
    linhas = []
    for r in con.execute("SELECT id, titulo, corpo_texto, categoria FROM artigos ORDER BY id"):
        sid = str(r["id"])
        if sid not in ROTULOS:
            continue
        cat_prev, _, _ = classifica(r["titulo"], r["corpo_texto"] or "")
        cat_real = ROTULOS[sid]
        ok = cat_prev == cat_real
        acertos += ok
        total += 1
        linhas.append((r["id"], ok, cat_real, cat_prev, r["titulo"][:60]))
    print(f"{'id':>4} {'ok':>3}  {'manual':<15} {'classificador':<15} titulo")
    for i, ok, real, prev, t in linhas:
        print(f"{i:>4} {'✓' if ok else '✗':>3}  {real:<15} {prev:<15} {t}")
    if total:
        print(f"\nAcertos: {acertos}/{total} = {100*acertos/total:.0f}%")
    else:
        print("SEM AMOSTRA ROTULADA", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
