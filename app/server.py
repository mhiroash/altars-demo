#!/usr/bin/env python3
"""Altars — servidor do demo (FastAPI).

Serve a UI do Product Designer (design/) e expoe a API do ciclo completo:
Inbox (recolha/pesquisa) -> Redigir peca -> Rever/aprovar -> Compor ->
Exportar PDF/PNG. Alertas do MIREX aparecem no painel.
"""
import json
import os
import sys
from datetime import datetime, timezone

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
PIPELINE = os.path.join(ROOT, "pipeline")
DESIGN = os.path.join(ROOT, "design")
# A ordem importa: app/ tem de vir ANTES de pipeline/ no sys.path, senão
# `import db` resolve para pipeline/db.py (que não tem init_app) e todos os
# endpoints que tocam a BD dão 500. Bug P0 confirmado pelo QA.
for _p in (PIPELINE, HERE):
    while _p in sys.path:
        sys.path.remove(_p)
    sys.path.insert(0, _p)

import db as appdb  # noqa: E402
import mirex  # noqa: E402
import telegram_notify  # noqa: E402

try:
    import exportar  # noqa: E402
except Exception:  # pragma: no cover
    exportar = None

app = FastAPI(title="Altars — Demo Editorial", version="1.0")


def _con():
    con = appdb.connect()
    appdb.init_app(con)
    return con


def _row(r):
    return {k: r[k] for k in r.keys()} if r is not None else None


# --------------------------------------------------------------------------
# Inbox — recolha e pesquisa (RF-1.x)
# --------------------------------------------------------------------------
@app.get("/api/inbox")
def inbox(q: str | None = None, fonte: str | None = None, tema: str | None = None,
          data: str | None = None, limite: int = Query(50, le=200)):
    con = _con()
    sql = "SELECT id, fonte, url, titulo, autor, data_publicacao, categoria FROM artigos WHERE 1=1"
    args: list = []
    if fonte:
        sql += " AND fonte=?"
        args.append(fonte)
    if tema:
        sql += " AND categoria=?"
        args.append(tema)
    if data:
        sql += " AND date_iso(data_publicacao)=?"
        args.append(data)
    if q:
        sql += " AND (titulo LIKE ? OR corpo_texto LIKE ?)"
        args += [f"%{q}%", f"%{q}%"]
    sql += " ORDER BY data_publicacao DESC LIMIT ?"
    args.append(limite)
    rows = con.execute(sql, args).fetchall()
    return {"total": len(rows), "itens": [_row(r) for r in rows]}


@app.get("/api/inbox/{artigo_id}")
def artigo(artigo_id: int):
    con = _con()
    r = con.execute("SELECT * FROM artigos WHERE id=?", (artigo_id,)).fetchone()
    if not r:
        raise HTTPException(404, "artigo não encontrado")
    d = _row(r)
    arq = con.execute("SELECT sha256, coletado_em FROM arquivo WHERE artigo_id=?", (artigo_id,)).fetchone()
    d["arquivo"] = _row(arq)
    return d


# --------------------------------------------------------------------------
# Redigir — gerar peca (RF-2.x)
# --------------------------------------------------------------------------
class GerarPedido(BaseModel):
    artigo_id: int
    formato: str = "breve"  # breve | desenvolvida | analise


@app.post("/api/gerar")
def gerar(pedido: GerarPedido):
    con = _con()
    a = con.execute("SELECT * FROM artigos WHERE id=?", (pedido.artigo_id,)).fetchone()
    if not a:
        raise HTTPException(404, "artigo não encontrado")
    try:
        import compositor
    except Exception as exc:
        raise HTTPException(500, f"compositor indisponível: {exc}") from exc

    if pedido.formato == "breve":
        peca = compositor.compor_breve(a)
    elif pedido.formato == "desenvolvida":
        peca = compositor.compor_desenvolvida(a)
    elif pedido.formato == "analise":
        peca = compositor.compor_analise(a, con)
    else:
        raise HTTPException(400, "formato inválido")
    pid = compositor.guardar_peca(con, a["id"], peca)
    con.commit()
    return {"peca_id": pid, **peca, "rotulo": compositor.ROTULO}


@app.get("/api/pecas")
def pecas(estado: str | None = None):
    con = _con()
    sql = ("SELECT p.*, (SELECT COUNT(*) FROM aprovacoes ap WHERE ap.peca_id=p.id) AS aprovada "
           "FROM pecas p")
    rows = con.execute(sql).fetchall()
    out = []
    for r in rows:
        d = _row(r)
        d["estado"] = "revista" if d.get("aprovada") else "gerada"
        if estado and d["estado"] != estado:
            continue
        out.append(d)
    return {"total": len(out), "pecas": out}


# --------------------------------------------------------------------------
# Aprovar — gate humano ("a IA escreve, o humano publica")
# --------------------------------------------------------------------------
class AprovarPedido(BaseModel):
    revisor: str = "Demo"
    nota: str | None = None


@app.post("/api/pecas/{peca_id}/aprovar")
def aprovar(peca_id: int, pedido: AprovarPedido):
    con = _con()
    p = con.execute("SELECT id FROM pecas WHERE id=?", (peca_id,)).fetchone()
    if not p:
        raise HTTPException(404, "peça não encontrada")
    con.execute(
        "INSERT INTO aprovacoes (peca_id, revisor, aprovado_em, nota) VALUES (?,?,?,?)",
        (peca_id, pedido.revisor,
         datetime.now(timezone.utc).replace(microsecond=0).isoformat(), pedido.nota),
    )
    con.commit()
    return {"peca_id": peca_id, "estado": "revista", "revisor": pedido.revisor}


# --------------------------------------------------------------------------
# Alertas — MIREX (RF-3.x)
# --------------------------------------------------------------------------
@app.get("/api/alertas")
def alertas():
    con = _con()
    rows = con.execute("SELECT * FROM alertas ORDER BY detetado_em DESC").fetchall()
    return {"total": len(rows), "alertas": [_row(r) for r in rows]}


class PollPedido(BaseModel):
    perfil_id: str = "mirex-demo"


@app.post("/api/alertas/poll")
def alertas_poll(pedido: PollPedido):
    con = _con()
    try:
        try:
            novas = mirex.detetar_novas(con, pedido.perfil_id)
        except Exception:
            # Endpoint MIREX indisponivel: usa a publicacao real arquivada
            # (simulacao rotulada, ADR D6).
            novas = mirex.detetar_novas(con, pedido.perfil_id, fetcher=mirex.fixture_fetcher)
    except Exception as exc:  # noqa: BLE001
        return JSONResponse(status_code=502, content={"erro": str(exc), "novas": []})
    enviados = []
    for n in novas:
        enviados.append(telegram_notify.enviar(telegram_notify.formatar_alerta(n)))
    return {"novas": novas, "telegram": enviados}


# --------------------------------------------------------------------------
# Compor e exportar (RF-4.4 / RF-5.3)
# --------------------------------------------------------------------------
@app.get("/api/pecas/{peca_id}/preview")
def preview(peca_id: int):
    con = _con()
    p = con.execute("SELECT * FROM pecas WHERE id=?", (peca_id,)).fetchone()
    if not p:
        raise HTTPException(404, "peça não encontrada")
    d = _row(p)
    d["fontes"] = json.loads(d.get("fontes") or "[]")
    return d


def _peca_aprovada(con, peca_id):
    p = con.execute("SELECT * FROM pecas WHERE id=?", (peca_id,)).fetchone()
    if not p:
        raise HTTPException(404, "peça não encontrada")
    if not con.execute("SELECT 1 FROM aprovacoes WHERE peca_id=?", (peca_id,)).fetchone():
        raise HTTPException(409, "exportação bloqueada: a peça ainda não foi revista")
    return p


@app.get("/api/pecas/{peca_id}/exportar.pdf")
def exportar_pdf(peca_id: int):
    if exportar is None:
        raise HTTPException(500, "módulo de exportação indisponível")
    con = _con()
    p = _peca_aprovada(con, peca_id)
    pdf = exportar.gerar_pdf(_row(p))
    return Response(content=pdf, media_type="application/pdf",
                    headers={"Content-Disposition": f'inline; filename="altars-{peca_id}.pdf"'})


@app.get("/api/pecas/{peca_id}/exportar.png")
def exportar_png(peca_id: int):
    if exportar is None:
        raise HTTPException(500, "módulo de exportação indisponível")
    con = _con()
    p = _peca_aprovada(con, peca_id)
    png = exportar.gerar_png(_row(p))
    return Response(content=png, media_type="image/png",
                    headers={"Content-Disposition": f'inline; filename="altars-{peca_id}.png"'})


@app.get("/api/health")
def health():
    return {"ok": True, "telegram_ativo": telegram_notify.ativo(),
            "exportacao": exportar is not None}


# --------------------------------------------------------------------------
# UI estática (design do Product Designer)
# --------------------------------------------------------------------------
if os.path.isdir(DESIGN):
    app.mount("/", StaticFiles(directory=DESIGN, html=True), name="ui")
