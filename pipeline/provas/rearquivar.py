#!/usr/bin/env python3
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
"""Re-arquiva páginas originais (RF-1.6) com o código corrigido (sha256 sobre bytes)."""
import hashlib, sqlite3, time
from recoletor import pedir, limpar_html_conteudo
from db import DB_PATH

con = sqlite3.connect(DB_PATH); con.row_factory = sqlite3.Row
rows = con.execute("SELECT a.id, a.url FROM artigos a JOIN arquivo ar ON ar.artigo_id=a.id WHERE ar.sha256='indisponivel'").fetchall()
print(f"a re-arquivar: {len(rows)}")
for r in rows:
    try:
        bruto = pedir(r["url"])
        sha = hashlib.sha256(bruto).hexdigest()
        html = limpar_html_conteudo(bruto.decode("utf-8", errors="replace"))
        con.execute("UPDATE arquivo SET html=?, sha256=? WHERE artigo_id=?", (html, sha, r["id"]))
        con.commit()
        print(f"  ok id={r['id']} sha={sha[:12]} len={len(html)}")
    except Exception as e:
        print(f"  FALHOU id={r['id']}: {type(e).__name__}: {e}")
    time.sleep(5)
print("fim")
