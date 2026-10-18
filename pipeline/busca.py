#!/usr/bin/env python3
"""Altars — busca combinável (RF-1.5): tema, data, palavra-chave e fonte."""
import argparse
import json

from db import connect, init


def buscar(con, tema=None, de=None, ate=None, palavra=None, fonte=None, limite=20):
    sql = "SELECT id, fonte, url, titulo, autor, data_publicacao, categoria FROM artigos WHERE 1=1"
    args = []
    if tema:
        sql += " AND categoria=?"
        args.append(tema)
    if de:
        sql += " AND date_iso(data_publicacao) >= date(?)"
        args.append(de)
    if ate:
        sql += " AND date_iso(data_publicacao) <= date(?)"
        args.append(ate)
    if fonte:
        sql += " AND fonte=?"
        args.append(fonte)
    if palavra:
        sql += " AND (titulo LIKE ? OR corpo_texto LIKE ?)"
        args.extend([f"%{palavra}%"] * 2)
    sql += " ORDER BY data_publicacao DESC LIMIT ?"
    args.append(limite)
    return [dict(r) for r in con.execute(sql, args).fetchall()]


def main():
    ap = argparse.ArgumentParser(description="Busca combinável no repositório Altars")
    ap.add_argument("--tema", choices=["Economia", "Política", "Sociedade", "Entretenimento", "Desporto", "Outros"])
    ap.add_argument("--de", help="data ISO início (ex.: 2026-10-01)")
    ap.add_argument("--ate", help="data ISO fim")
    ap.add_argument("--palavra")
    ap.add_argument("--fonte")
    ap.add_argument("--limite", type=int, default=20)
    a = ap.parse_args()
    con = connect()
    init(con)
    res = buscar(con, a.tema, a.de, a.ate, a.palavra, a.fonte, a.limite)
    print(json.dumps(res, ensure_ascii=False, indent=2))
    print(f"\n{len(res)} resultado(s)", file=__import__('sys').stderr)


if __name__ == "__main__":
    main()
