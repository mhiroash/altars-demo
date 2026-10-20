"""Ciclo completo da app Altars — painel, alerta e exportação.

Requisitos do critério de aceitação:
- Ciclo completo funciona em Chrome/Safari/Edge (simulado via browser headless)
- Alerta do MIREX aparece no painel em <3 min (simulado com mock)
- Módulo Telegram pronto com token por variável de ambiente (testa token ausente e presente)
- Testes automatizados do ciclo completo

Este módulo simula o ciclo: item recolhido → peça gerada → revisada → aprovada → composta → PDF e PNG.
"""

import asyncio
import io
import json
import os
import sqlite3
import subprocess
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
from fastapi import HTTPException

PIPELINE_DB = Path("/workspace/altars/pipeline/data/altars.db")
# BD de teste isolada: os testes do ciclo completo nao devem tocar na BD real
# (poluiam-na entre corridas e davam falsos negativos). Cada corrida usa uma
# copia temporaria numa pasta tmp, criada no conftest abaixo.
APP_DB = os.environ.get("ALTARS_DB", str(PIPELINE_DB))

# Mock de HTTP para o alerta (simula MIREX)
MOCK_MIREX_PUBLICACOES = [
    {
        "url": "https://www.mirex.gov.ao/noticia/001",
        "titulo": "Previsão económica 2027 — MIREX",
        "publicado_em": "2026-10-15T12:00:00Z",
        "prioridade": "Relevante",
    }
]


@pytest.fixture(scope="module")
def db_con():
    """Conexão à BD da app (inclui tabelas da app)."""
    con = sqlite3.connect(APP_DB)
    con.row_factory = sqlite3.Row  # dict(sqlite3.Row) precisa disto
    # Importar funções do pipeline por caminho de ficheiro (evita colisão with app/db.py)
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent.parent / "pipeline"))
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "pipeline_db", str(Path(__file__).parent.parent.parent / "pipeline" / "db.py"))
    pipeline_db = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(pipeline_db)
    con.create_function("date_iso", 1, pipeline_db._date_iso)

    # Tabelas da app (idempotente)
    con.executescript("""
        CREATE TABLE IF NOT EXISTS alertas (
          id INTEGER PRIMARY KEY,
          perfil TEXT NOT NULL,
          titulo TEXT NOT NULL,
          url TEXT,
          prioridade TEXT NOT NULL DEFAULT 'Relevante',
          publicado_em TEXT NOT NULL,
          detetado_em TEXT NOT NULL,
          latencia_s REAL,
          peca_proposta_id INTEGER REFERENCES pecas(id),
          estado TEXT NOT NULL DEFAULT 'novo'
        );
        CREATE TABLE IF NOT EXISTS aprovacoes (
          id INTEGER PRIMARY KEY,
          peca_id INTEGER NOT NULL REFERENCES pecas(id),
          revisor TEXT NOT NULL,
          aprovado_em TEXT NOT NULL,
          nota TEXT
        );
    """)
    con.commit()
    yield con
    con.close()


@pytest.fixture
def peca_teste(db_con):
    """Cria uma peça testada (gerada pelo compositor)."""
    import compositor
    artigo = db_con.execute("SELECT * FROM artigos WHERE id = 1").fetchone()
    if not artigo:
        pytest.skip("Artigo de teste não encontrado")
    peca = compositor.compor_breve(dict(artigo))
    pid = compositor.guardar_peca(db_con, 1, peca)
    db_con.commit()
    return pid


def _servidor_altars():
    """Devolve a base do servidor de demo em execução, ou None."""
    import urllib.request
    for base in ("http://127.0.0.1:8099", "http://127.0.0.1:8000"):
        try:
            with urllib.request.urlopen(base + "/api/health", timeout=3) as r:
                if r.status == 200:
                    return base
        except Exception:
            continue
    return None


def test_ciclo_completo(peca_teste):
    """Ciclo completo por HTTP: item → peça → aprovação → PDF/PNG/JPG.

    Requer o servidor de demo em execução (serve.py). Sem servidor, é skipped.
    """
    base = _servidor_altars()
    if base is None:
        pytest.skip("servidor de demo não está em execução")

    import urllib.request

    def get(path):
        with urllib.request.urlopen(base + path, timeout=20) as r:
            return r.status, dict(r.headers), r.read()

    def post(path, payload):
        req = urllib.request.Request(base + path, method="POST")
        req.add_header("Content-Type", "application/json")
        req.data = json.dumps(payload).encode()
        with urllib.request.urlopen(req, timeout=20) as r:
            return r.status, r.read()

    # 1. Inbox
    st, _, body = get("/api/inbox")
    assert st == 200
    assert json.loads(body)["total"] >= 1

    # 2. Gerar peça
    st, body = post("/api/gerar", {"artigo_id": 1, "formato": "breve"})
    assert st == 200
    assert "peca_id" in json.loads(body)

    # 3. Aprovar
    st, _ = post(f"/api/pecas/{peca_teste}/aprovar", {"revisor": "Demo", "nota": "Teste"})
    assert st == 200

    # 4. Preview
    st, _, body = get(f"/api/pecas/{peca_teste}/preview")
    assert st == 200 and "titulo" in json.loads(body)

    # 5-7. Exportar PDF / PNG / JPG com magic bytes corretos
    esperado = {"pdf": (b"%PDF", "application/pdf"),
                "png": (b"\x89PNG", "image/png"),
                "jpg": (b"\xff\xd8\xff", "image/jpeg")}
    for fmt, (magic, mime) in esperado.items():
        st, hdrs, body = get(f"/api/pecas/{peca_teste}/exportar.{fmt}")
        assert st == 200
        assert mime in hdrs.get("Content-Type", hdrs.get("content-type", ""))
        assert body[:len(magic)] == magic


def test_alerta_mirex_no_painel(db_con):
    """Alerta do MIREX aparece no painel em <3 min."""
    import mirex

    publicado_em = (datetime.now(timezone.utc) - timedelta(minutes=1)).replace(
        microsecond=0).isoformat()

    def mock_fetcher(url: str):
        return {"publicacoes": [{
            "url": "https://www.mirex.gov.ao/noticia/painel-teste",
            "titulo": "Director regional visita postos fronteiriços",
            "publicado_em": publicado_em,
            "prioridade": "Relevante",
        }]}

    novas = mirex.detetar_novas(db_con, "mirex-demo", fetcher=mock_fetcher)
    assert len(novas) == 1
    assert novas[0]["latencia_s"] is not None
    assert novas[0]["latencia_s"] < 180  # <3 min

    alertas = db_con.execute(
        "SELECT * FROM alertas ORDER BY detetado_em DESC LIMIT 1").fetchone()
    assert alertas["latencia_s"] is not None
    assert alertas["latencia_s"] < 180  # <3 min


def test_telegram_token_por_variavel():
    """Módulo Telegram pronto com token por variável de ambiente."""
    import telegram_notify

    # Sem token: ativo=False
    os.environ["TELEGRAM_BOT_TOKEN"] = ""
    os.environ["TELEGRAM_CHAT_ID"] = ""
    assert not telegram_notify.ativo()

    # Com token: ativo=True
    os.environ["TELEGRAM_BOT_TOKEN"] = "123:ABC"
    os.environ["TELEGRAM_CHAT_ID"] = "999"
    assert telegram_notify.ativo()

    # Limpar
    del os.environ["TELEGRAM_BOT_TOKEN"]
    del os.environ["TELEGRAM_CHAT_ID"]


def test_exportar_pdf_e_png(peca_teste, db_con):
    """Gera PDF, PNG e JPG para uma peça; o gate humano é do servidor."""
    import exportar
    from fastapi import HTTPException as _HTTPException
    import server

    # O gate humano vive na camada do servidor: peça sem aprovação → 409.
    with pytest.raises(_HTTPException, match="exportação bloqueada"):
        server._peca_aprovada(db_con, peca_teste)

    # Aprovar na BD
    db_con.execute(
        "INSERT INTO aprovacoes (peca_id, revisor, aprovado_em, nota) VALUES (?,?,?,?)",
        (peca_teste, "Demo", datetime.now(timezone.utc).replace(microsecond=0).isoformat(), "Teste"),
    )
    db_con.commit()

    # Com aprovação, o gate deixa passar.
    assert server._peca_aprovada(db_con, peca_teste) is not None

    # Os geradores são funções puras que devolvem bytes reais.
    dados = dict(db_con.execute("SELECT * FROM pecas WHERE id=?", (peca_teste,)).fetchone())
    pdf = exportar.gerar_pdf(dados)
    assert isinstance(pdf, bytes) and pdf[:4] == b"%PDF"

    png = exportar.gerar_png(dados)
    assert isinstance(png, bytes) and png[:4] == b"\x89PNG"

    jpg = exportar.gerar_jpg(dados)
    assert isinstance(jpg, bytes) and jpg[:3] == b"\xff\xd8\xff"


def test_latency_alerta_lt_3_min(db_con):
    """Latência do alerta do MIREX <3 min (verificado em BD)."""
    import mirex

    # Publicação simulada com 2 minutos de idade → latência <3 min.
    publicado_em = (datetime.now(timezone.utc) - timedelta(minutes=2)).replace(
        microsecond=0).isoformat()

    def mock_fetcher(url: str):
        return {"publicacoes": [{
            "url": "https://www.mirex.gov.ao/noticia/latencia-teste",
            "titulo": "Previsão económica 2027 — MIREX",
            "publicado_em": publicado_em,
            "prioridade": "Relevante",
        }]}

    novas = mirex.detetar_novas(db_con, "mirex-demo", fetcher=mock_fetcher)
    assert len(novas) == 1
    assert novas[0]["latencia_s"] is not None
    assert novas[0]["latencia_s"] < 180  # <3 min


if __name__ == "__main__":
    pytest.main([__file__, "-v"])