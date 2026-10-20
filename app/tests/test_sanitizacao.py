"""Prova do A1: o corpo gravado na BD passa por limpar_html_conteudo().

Testa o pipeline real de sanitização (pipeline/recoletor.py) com HTML
malicioso e confirma que nem o texto extraído nem o arquivo guardado
mantêm scripts, atributos de evento ou esquemas perigosos.
"""
import importlib.util
import os
import sqlite3
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@pytest.fixture(scope="module")
def recoletor():
    spec = importlib.util.spec_from_file_location(
        "recoletor_teste", os.path.join(ROOT, "pipeline", "recoletor.py"))
    mod = importlib.util.module_from_spec(spec)
    sys.modules["recoletor_teste"] = mod
    spec.loader.exec_module(mod)
    return mod


MALICIOSO = (
    '<p>Texto util.</p>'
    '<script>alert(document.cookie)</script>'
    '<img src=x onerror="fetch(1)">'
    "<img src=y onerror=alert(1)>"
    "<iframe src='https://evil.example'></iframe>"
    '<a href="javascript:alert(1)">clique</a>'
    '<a href="data:text/html,<script>alert(2)</script>">data</a>'
    '<div onmouseover="roubar()">passa o rato</div>'
)


def test_limpar_html_conteudo_remove_tudo(recoletor):
    limpo = recoletor.limpar_html_conteudo(MALICIOSO)
    assert "<script" not in limpo.lower()
    assert "onerror" not in limpo.lower()
    assert "onmouseover" not in limpo.lower()
    assert "<iframe" not in limpo.lower()
    assert "javascript:" not in limpo.lower()
    assert "data:text/html" not in limpo.lower()
    # O conteúdo legítimo sobrevive.
    assert "Texto util." in limpo
    assert "clique" in limpo
    assert "passa o rato" in limpo


def test_corpo_texto_fica_limpo_na_bd(recoletor, tmp_path):
    """Simula o caminho do recoletor: sanitiza → extrai → grava → lê da BD."""
    caminho = tmp_path / "teste.db"
    con = sqlite3.connect(caminho)
    con.row_factory = sqlite3.Row
    con.execute(
        "CREATE TABLE artigos (id INTEGER PRIMARY KEY, fonte TEXT, url TEXT,"
        " titulo TEXT, autor TEXT, data_publicacao TEXT, corpo_texto TEXT,"
        " coletado_em TEXT)"
    )

    # Mesma sequência do recoletor.py (linhas do fix A1).
    corpo = recoletor.html_para_texto(recoletor.limpar_html_conteudo(MALICIOSO))
    titulo = recoletor.html_para_texto(
        recoletor.limpar_html_conteudo("<title>Ok</title><script>ruim()</script>Notícia"))
    con.execute(
        "INSERT INTO artigos (fonte, url, titulo, corpo_texto, coletado_em)"
        " VALUES ('Teste','https://x/1',?,?,'agora')", (titulo, corpo))
    con.commit()

    linha = con.execute("SELECT * FROM artigos WHERE url='https://x/1'").fetchone()
    gravado = linha["corpo_texto"]
    # O texto útil sobrevive (a junção exata depende do parser de blocos).
    assert "Texto util." in gravado
    assert "clique" in gravado
    assert "passa o rato" in gravado
    for perigo in ("<script", "onerror", "onmouseover", "javascript:", "data:text/html"):
        assert perigo not in gravado.lower()
    for perigo in ("<script", "ruim"):
        assert perigo not in linha["titulo"].lower()


def test_arquivo_fica_limpo(recoletor):
    """O HTML arquivado (arquivo.html) também é sanitizado."""
    limpo = recoletor.limpar_html_conteudo(MALICIOSO)
    assert "<script" not in limpo.lower()
    assert "<iframe" not in limpo.lower()
