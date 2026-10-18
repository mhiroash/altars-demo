#!/usr/bin/env python3
"""Altars — motor de redacção extractivo, ROTULADO como tal.

Sem chave LLM verificada com prova de funcionamento, este compositor gera as
três peças (RF-2.1/2.3/2.5) por extração estruturada do próprio artigo:
antetítulo/título/lead/corpo montados a partir do texto da fonte, com a
lista de fontes anexada. Nenhuma frase é inventada: cada parágrafo do corpo
vem literalmente do original (frases completas, sem reescrita).
"""
import json
import re

from db import connect, init

ROTULO = "composer-extractivo-sem-llm"


def frases(txt: str):
    txt = re.sub(r"\s+", " ", (txt or "")).strip()
    return [f.strip() for f in re.split(r"(?<=[.!?…])\s+", txt) if len(f.strip()) > 25]


def palavras(txt: str) -> int:
    return len(re.findall(r"\w+", txt or ""))


def fonte_do_artigo(a) -> dict:
    return {"fonte": a["fonte"], "url": a["url"], "autor": a["autor"],
            "data": a["data_publicacao"], "titulo": a["titulo"]}


def compor_breve(a) -> dict:
    """Notícia breve ≤200 palavras: lead + 2 parágrafos extraídos."""
    fs = frases(a["corpo_texto"])
    lead = fs[0] if fs else a["titulo"]
    paragrafos = fs[1:5]
    corpo = "\n\n".join(paragrafos)
    while palavras(lead + " " + corpo) > 200 and paragrafos:
        paragrafos.pop()
        corpo = "\n\n".join(paragrafos)
    titulo = a["titulo"]
    if len(titulo) > 90:
        titulo = titulo[:87].rstrip(",;: ") + "…"
    return {"formato": "breve", "antetitulo": a["fonte"], "titulo": titulo,
            "lead": lead, "corpo": corpo, "fontes": [fonte_do_artigo(a)]}


def compor_desenvolvida(a) -> dict:
    """Notícia desenvolvida 400–800 palavras: lead + parágrafos temáticos."""
    fs = frases(a["corpo_texto"])
    lead = fs[0] if fs else a["titulo"]
    blocos, atual, n = [], [], 0
    for f in fs[1:]:
        n += palavras(f)
        atual.append(f)
        if n >= 90:
            blocos.append(" ".join(atual))
            atual, n = [], 0
    if atual:
        blocos.append(" ".join(atual))
    corpo = "\n\n".join(blocos)
    # corta para respeitar o limite superior da PEÇA (lead + corpo <= 800)
    while palavras(lead + " " + corpo) > 780 and blocos:
        blocos.pop()
        corpo = "\n\n".join(blocos)
    # se ficou curto (<400), acrescenta mais frases por bloco
    if palavras(corpo) < 400:
        blocos2, atual, n = [], [], 0
        for f in fs[1:]:
            n += palavras(f)
            atual.append(f)
            if n >= 55:
                blocos2.append(" ".join(atual))
                atual, n = [], 0
        if atual:
            blocos2.append(" ".join(atual))
        corpo = "\n\n".join(blocos2)
        while palavras(lead + " " + corpo) > 780 and blocos2:
            blocos2.pop()
            corpo = "\n\n".join(blocos2)
    return {"formato": "desenvolvida", "antetitulo": f"{a['fonte']} · {a['categoria']}",
            "titulo": a["titulo"], "lead": lead, "corpo": corpo,
            "fontes": [fonte_do_artigo(a)]}


def compor_analise(a, con) -> dict:
    """Análise com contexto: artigo principal + até 2 do mesmo tema como contexto."""
    outros = con.execute(
        "SELECT * FROM artigos WHERE categoria=? AND id<>? ORDER BY id LIMIT 2",
        (a["categoria"], a["id"]),
    ).fetchall()
    fs = frases(a["corpo_texto"])
    lead = fs[0] if fs else a["titulo"]
    contexto = "\n\n".join(
        f"Contexto relacionado ({o['fonte']}): " + " ".join(frases(o["corpo_texto"])[:3])
        for o in outros
    )
    corpo = "\n\n".join(fs[1:9])
    if contexto:
        corpo += "\n\n" + contexto
    fontes = [fonte_do_artigo(a)] + [fonte_do_artigo(o) for o in outros]
    return {"formato": "analise", "antetitulo": f"Análise · {a['categoria']}",
            "titulo": a["titulo"], "lead": lead, "corpo": corpo, "fontes": fontes}


def guardar_peca(con, artigo_id: int, peca: dict) -> int:
    texto = f"{peca['lead']} {peca['corpo']}"
    cur = con.execute(
        """INSERT INTO pecas (artigo_id, formato, rotulo, antetitulo, titulo, lead,
           corpo, n_palavras, fontes, criado_em)
           VALUES (?,?,?,?,?,?,?,?,?,datetime('now'))""",
        (artigo_id, peca["formato"], ROTULO, peca["antetitulo"], peca["titulo"],
         peca["lead"], peca["corpo"], palavras(texto), json.dumps(peca["fontes"], ensure_ascii=False)),
    )
    return cur.lastrowid


def main():
    con = connect()
    init(con)
    arts = con.execute(
        "SELECT * FROM artigos WHERE corpo_texto IS NOT NULL AND length(corpo_texto)>200 "
        "AND id NOT IN (SELECT DISTINCT artigo_id FROM pecas)"
    ).fetchall()
    n = 0
    for a in arts:
        for peca in (compor_breve(a), compor_desenvolvida(a), compor_analise(a, con)):
            pid = guardar_peca(con, a["id"], peca)
            print(f"peça #{pid} [{peca['formato']}] {palavras(peca['lead']+' '+peca['corpo'])} palavras | "
                  f"fontes={len(peca['fontes'])} | rotulo={ROTULO}")
        n += 1
    con.commit()
    print(f"\nartigos redigidos: {n}")


if __name__ == "__main__":
    main()
