#!/usr/bin/env python3
"""Altars — acesso a dados da app (camada fina sobre o SQLite do pipeline).

Reutiliza o esquema criado por pipeline/db.py e acrescenta as tabelas que a
app precisa: alertas (MIREX) e aprovacoes (gate humano).
"""
import os
import sqlite3
import sys

PIPELINE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "pipeline")
if PIPELINE not in sys.path:
    sys.path.insert(0, PIPELINE)

DB_PATH = os.environ.get(
    "ALTARS_DB",
    os.path.join(PIPELINE, "data", "altars.db"),
)


def connect():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    try:
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "pipeline_db", os.path.join(PIPELINE, "db.py"))
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        con.create_function("date_iso", 1, mod._date_iso)
    except Exception:
        pass
    con.execute("PRAGMA foreign_keys = ON")
    return con


def init(con):
    """Tabelas do esquema partilhado (pipeline/db.py) + tabelas da app.

    Alias mantido com o nome que o pipeline importa (`from db import connect, init`),
    para que compositor.py/busca.py resolvam para este módulo sem colisão.
    """
    # Esquema base do pipeline (artigos, arquivo, pecas).
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "pipeline_db", os.path.join(PIPELINE, "db.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    mod.init(con)
    # Tabelas exclusivas da app.
    init_app(con)


def init_app(con):
    """Tabelas exclusivas da app. Idempotente."""
    con.executescript(
        """
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
        CREATE TABLE IF NOT EXISTS exportacoes (
          id INTEGER PRIMARY KEY,
          peca_id INTEGER NOT NULL REFERENCES pecas(id),
          template TEXT NOT NULL,
          pdf_path TEXT,
          png_path TEXT,
          criado_em TEXT NOT NULL
        );
        """
    )
    con.commit()
