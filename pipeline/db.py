#!/usr/bin/env python3
"""Altars — esquema SQLite partilhado (RF-1.1, RF-1.3, RF-1.5, RF-1.6, RF-2.x)."""
import os
import sqlite3

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "altars.db")


def _date_iso(s):
    """Converte datas RFC 2822 ('Fri, 16 Oct 2026 ...') ou ISO para YYYY-MM-DD."""
    if not s:
        return None
    s = str(s).strip()
    try:
        from email.utils import parsedate_to_datetime
        return parsedate_to_datetime(s).date().isoformat()
    except Exception:
        pass
    try:
        from datetime import datetime
        return datetime.fromisoformat(s.replace("Z", "+00:00")).date().isoformat()
    except Exception:
        return None


def connect():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    con.create_function("date_iso", 1, _date_iso)
    return con


def init(con):
    con.executescript(
        """
        CREATE TABLE IF NOT EXISTS artigos (
          id INTEGER PRIMARY KEY,
          fonte TEXT NOT NULL,
          url TEXT NOT NULL UNIQUE,
          titulo TEXT NOT NULL,
          autor TEXT,
          data_publicacao TEXT,
          categoria TEXT,
          categoria_metodo TEXT,
          categoria_fonte TEXT,
          corpo_texto TEXT,
          coletado_em TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS arquivo (
          id INTEGER PRIMARY KEY,
          artigo_id INTEGER NOT NULL REFERENCES artigos(id),
          origem TEXT NOT NULL,
          html TEXT NOT NULL,
          sha256 TEXT NOT NULL,
          coletado_em TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS pecas (
          id INTEGER PRIMARY KEY,
          artigo_id INTEGER NOT NULL REFERENCES artigos(id),
          formato TEXT NOT NULL,
          rotulo TEXT NOT NULL,
          antetitulo TEXT,
          titulo TEXT,
          lead TEXT,
          corpo TEXT,
          n_palavras INTEGER,
          fontes TEXT,
          criado_em TEXT NOT NULL
        );
        """
    )
    con.commit()
