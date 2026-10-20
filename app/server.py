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


@app.middleware("http")
async def _noindex_header(request, call_next):
    """ADR-ALT-2026-001 (D8): noindex também no header, além da meta."""
    resp = await call_next(request)
    resp.headers["X-Robots-Tag"] = "noindex, nofollow, noarchive, nosnippet, noimageindex"
    return resp


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


ESTADO_ROTULO = {
    "gerada": "Rascunho — redigida pela IA. Falta a sua revisão.",
    "revista": "Revista — aprovada por humano. Pode ser composta.",
}


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
    return {"peca_id": pid, **peca, "rotulo": compositor.ROTULO,
            "estado": "gerada", "estado_rotulo": ESTADO_ROTULO["gerada"]}


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
        d["estado_rotulo"] = ESTADO_ROTULO[d["estado"]]
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
    return {"peca_id": peca_id, "estado": "revista",
            "estado_rotulo": ESTADO_ROTULO["revista"], "revisor": pedido.revisor}


# --------------------------------------------------------------------------
# Alertas — MIREX (RF-3.x)
# --------------------------------------------------------------------------
@app.get("/api/alertas")
def alertas():
    con = _con()
    rows = con.execute("SELECT * FROM alertas ORDER BY detetado_em DESC").fetchall()
    out = []
    for r in rows:
        d = _row(r)
        d["peca_proposta"] = _peca_proposta(con, d)
        out.append(d)
    return {"total": len(out), "alertas": out}


def _peca_proposta(con, alerta: dict) -> dict | None:
    """Peca proposta para um alerta (RF-3.4).

    Ordem: (1) peca ja ligada ao alerta; (2) peca gerada sobre artigo arquivado
    cujo titulo coincide; (3) geracao na hora a partir desse artigo e ligacao
    persistida no alerta. Sem artigo correspondente devolve None — nunca se
    inventa uma peca sem fonte.
    """
    pid = alerta.get("peca_proposta_id")
    if pid:
        r = con.execute("SELECT id, formato, rotulo, titulo, lead FROM pecas WHERE id=?", (pid,)).fetchone()
        if r:
            return _row(r)
    titulo_alerta = (alerta.get("titulo") or "").strip()
    if not titulo_alerta:
        return None
    art = con.execute(
        "SELECT * FROM artigos WHERE titulo=? OR ? LIKE '%' || titulo || '%' LIMIT 1",
        (titulo_alerta, titulo_alerta),
    ).fetchone()
    if not art:
        return None
    pec = con.execute(
        "SELECT id, formato, rotulo, titulo, lead FROM pecas WHERE artigo_id=? "
        "ORDER BY CASE formato WHEN 'desenvolvida' THEN 0 WHEN 'analise' THEN 1 ELSE 2 END, id LIMIT 1",
        (art["id"],),
    ).fetchone()
    if not pec:
        try:
            import compositor
            gerada = compositor.compor_desenvolvida(art)
            novo_id = compositor.guardar_peca(con, art["id"], gerada)
            con.commit()
            pec = con.execute(
                "SELECT id, formato, rotulo, titulo, lead FROM pecas WHERE id=?", (novo_id,)
            ).fetchone()
        except Exception:  # noqa: BLE001 — sem compositor, o alerta fica sem peca
            return None
    if pec:
        con.execute("UPDATE alertas SET peca_proposta_id=? WHERE id=?", (pec["id"], alerta["id"]))
        con.commit()
        return _row(pec)
    return None


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


def _registar_exportacao(con, peca_id, formato, caminho):
    con.execute(
        "INSERT INTO exportacoes (peca_id, template, pdf_path, png_path, criado_em) "
        "VALUES (?,?,?,?,datetime('now'))",
        (peca_id, formato,
         caminho if formato == "pdf" else None,
         caminho if formato in ("png", "jpg") else None),
    )
    con.commit()


def _exportar(peca_id: int, formato: str):
    if exportar is None:
        raise HTTPException(500, "módulo de exportação indisponível")
    con = _con()
    p = _peca_aprovada(con, peca_id)
    try:
        caminho, dados = exportar.exportar_para_disco(_row(p), formato)
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
    _registar_exportacao(con, peca_id, formato, caminho)
    return Response(
        content=dados,
        media_type=exportar.media_type(formato),
        headers={
            "Content-Disposition": f'inline; filename="altars-{peca_id}.{formato}"',
            "X-Export-Path": caminho,
        },
    )


@app.get("/api/pecas/{peca_id}/exportar.pdf")
def exportar_pdf(peca_id: int):
    return _exportar(peca_id, "pdf")


@app.get("/api/pecas/{peca_id}/exportar.png")
def exportar_png(peca_id: int):
    return _exportar(peca_id, "png")


@app.get("/api/pecas/{peca_id}/exportar.jpg")
def exportar_jpg(peca_id: int):
    return _exportar(peca_id, "jpg")


@app.get("/api/health")
def health():
    return {"ok": True, "telegram_ativo": telegram_notify.ativo(),
            "exportacao": exportar is not None}


# --------------------------------------------------------------------------
# UI estática (design do Product Designer)
# --------------------------------------------------------------------------
if os.path.isdir(DESIGN):
    app.mount("/", StaticFiles(directory=DESIGN, html=True), name="ui")
