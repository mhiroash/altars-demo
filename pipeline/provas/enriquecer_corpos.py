#!/usr/bin/env python3
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
"""Enriquece corpo_texto a partir do HTML integral arquivado (RF-1.6 -> RF-1.1).

Os corpos vindos do RSS (content:encoded / description) são limpos mas truncados.
O HTML da página original tem o artigo completo. Método conservador:
1. extrai texto visível da página;
2. localiza o início do corpo RSS dentro desse texto (âncora = primeiros 60 chars);
3. a partir da âncora, toma até ~6000 chars, cortando na última frase completa;
4. só substitui se o novo corpo for >= 1.5x o antigo E começar pelo mesmo conteúdo
   (garante que classificação e rótulos manuais continuam válidos).
"""
import re
import sqlite3

from db import DB_PATH
from recoletor import html_para_texto

def cortar_frase(txt: str, maximo: int) -> str:
    if len(txt) <= maximo:
        return txt
    corte = txt[:maximo]
    # última frase completa dentro do limite
    m = None
    for m in re.finditer(r"[.!?…][""»\"]?\s", corte):
        pass
    return corte[: m.end()].strip() if m else corte.strip()

def main():
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    rows = con.execute(
        "SELECT a.id, a.corpo_texto, ar.html FROM artigos a JOIN arquivo ar ON ar.artigo_id=a.id"
    ).fetchall()
    n = 0
    for r in rows:
        velho = (r["corpo_texto"] or "").strip()
        if not r["html"] or not velho:
            continue
        pagina = html_para_texto(r["html"])
        pagina = re.sub(r"\s+", " ", pagina)
        ancora = re.sub(r"\s+", " ", velho)[:60]
        pos = pagina.find(ancora)
        if pos < 0:
            print(f"  id={r['id']}: âncora não encontrada — corpo mantido")
            continue
        novo = cortar_frase(pagina[pos:], 6000)
        if len(novo) >= 1.5 * len(velho) and novo.startswith(ancora[:40]):
            con.execute("UPDATE artigos SET corpo_texto=? WHERE id=?", (novo, r["id"]))
            print(f"  id={r['id']}: {len(velho)} -> {len(novo)} chars")
            n += 1
        else:
            print(f"  id={r['id']}: sem ganho claro ({len(velho)} -> {len(novo)}) — mantido")
    con.commit()
    print(f"corpos enriquecidos: {n}")

if __name__ == "__main__":
    main()
