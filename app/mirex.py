#!/usr/bin/env python3
"""Altars — cliente MIREX (perfil unico) para o alerta do demo.

O MIREX e a fonte de perfil do demo (ADR D4): polling a cada 60 s, deteta
publicacao nova no perfil e cria um alerta com a latencia medida.

O endpoint real do MIREX pode nao estar disponivel no ambiente de demo; por
isso o cliente aceita um `fetcher` injetavel. Em producao usa HTTP; nos testes
usa fixtures offline (sem rede).
"""
from __future__ import annotations

import json
import os
import time
import urllib.request
from datetime import datetime, timezone

MIREX_BASE = os.environ.get("MIREX_BASE", "https://www.mirex.gov.ao")
POLL_INTERVAL_S = int(os.environ.get("MIREX_POLL_INTERVAL_S", "60"))


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def http_fetcher(url: str, timeout: float = 20.0) -> dict:
    req = urllib.request.Request(url, headers={"User-Agent": "Altars-Demo/1.0 (+contacto)"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:  # noqa: S310
        return json.loads(resp.read().decode("utf-8"))


def perfil_url(perfil_id: str) -> str:
    return f"{MIREX_BASE}/api/perfis/{perfil_id}"


def listar_publicacoes(perfil_id: str, fetcher=http_fetcher) -> list[dict]:
    """Devolve a lista de publicacoes do perfil. Contrato fixado no teste."""
    data = fetcher(perfil_url(perfil_id))
    return data.get("publicacoes", [])


def detetar_novas(con, perfil_id: str, fetcher=http_fetcher) -> list[dict]:
    """Compara as publicacoes do perfil com as ja conhecidas e cria alertas.

    Devolve a lista de alertas criados (com latencia em segundos).
    """
    try:
        import app.db as _db  # pacote
    except Exception:
        import db as _db  # modulo no diretorio da app

    _db.init_app(con)
    novas = []
    for pub in listar_publicacoes(perfil_id, fetcher=fetcher):
        url = pub.get("url")
        if not url:
            continue
        ja = con.execute("SELECT 1 FROM alertas WHERE url=?", (url,)).fetchone()
        if ja:
            continue
        publicado_em = pub.get("publicado_em") or _now()
        detetado_em = _now()
        latencia = _latencia_s(publicado_em, detetado_em)
        cur = con.execute(
            """INSERT INTO alertas
               (perfil, titulo, url, prioridade, publicado_em, detetado_em, latencia_s, estado)
               VALUES (?,?,?,?,?,?,?, 'novo')""",
            (
                perfil_id,
                pub.get("titulo", "(sem titulo)"),
                url,
                pub.get("prioridade", "Relevante"),
                publicado_em,
                detetado_em,
                latencia,
            ),
        )
        novas.append({"id": cur.lastrowid, "url": url, "latencia_s": latencia,
                      "titulo": pub.get("titulo", "")})
    con.commit()
    return novas


def _latencia_s(publicado_em: str, detetado_em: str) -> float | None:
    try:
        a = datetime.fromisoformat(publicado_em.replace("Z", "+00:00"))
        b = datetime.fromisoformat(detetado_em.replace("Z", "+00:00"))
        return round((b - a).total_seconds(), 1)
    except Exception:
        return None


def correr_polling(con, perfil_id: str, fetcher=http_fetcher, interval_s: int = POLL_INTERVAL_S,
                   max_ciclos: int | None = None, on_alerta=None):
    """Loop de polling. max_ciclos=None corre indefinidamente (producao)."""
    ciclo = 0
    while max_ciclos is None or ciclo < max_ciclos:
        try:
            novas = detetar_novas(con, perfil_id, fetcher=fetcher)
            if novas and on_alerta:
                for n in novas:
                    on_alerta(n)
        except Exception as exc:  # noqa: BLE001 — o loop nao pode morrer por uma falha de rede
            print(f"[mirex] ciclo {ciclo}: erro {exc}")
        ciclo += 1
        if max_ciclos is None or ciclo < max_ciclos:
            time.sleep(interval_s)

# ---------------------------------------------------------------------------
# Simulacao rotulada do perfil (ADR D6): o endpoint /api/perfis/... nao existe
# no MIREX real. Usamos uma publicacao REAL arquivada em coletor/provas/ e
# convertemo-la no contrato {"publicacoes": [...]} que listar_publicacoes espera.
# ---------------------------------------------------------------------------
FIXTURE_PATH = os.environ.get(
    "MIREX_FIXTURE",
    os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                 "coletor", "provas", "mirex-id5000-raw.json"),
)


def _limpar_html(txt: str) -> str:
    import re
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", txt or "")).strip()


def fixture_fetcher(url: str, timeout: float = 20.0) -> dict:
    """Devolve a publicacao real arquivada, no contrato do perfil."""
    with open(FIXTURE_PATH, encoding="utf-8") as fh:
        raw = json.load(fh)
    d = raw.get("data") or {}
    pub = {
        "url": f"https://www.mirex.gov.ao/PortalMIREX/publicacao/{d.get('cdPublicacao')}",
        "titulo": d.get("titulo") or "(sem titulo)",
        "sumario": _limpar_html(d.get("sumario") or d.get("descricao") or "")[:400],
        "autor": d.get("autor") or "MIREX",
        "publicado_em": _now(),
        "prioridade": "Relevante",
        "rotulo": "simulado-fonte-real",
    }
    return {"publicacoes": [pub], "rotulo": "simulado-fonte-real"}
