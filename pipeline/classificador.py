#!/usr/bin/env python3
"""Altars — classificador por regras de palavra-chave (RF-1.3).

ROTULADO: heurística lexical, não semântica. `categoria_metodo` regista sempre
como foi classificado, para que nenhum consumidor trate o resultado como
verdade editorial.
"""
import re
import sqlite3
import unicodedata

from db import connect, init

CATEGORIAS = ["Economia", "Política", "Sociedade", "Entretenimento", "Desporto", "Outros"]

REGRAS = {
    "Economia": [
        "economia", "financas", "banco", "banca", "inflacao", "kwanza", "sonangol",
        "petroleo", "pib", "orcamento", "imposto", "divida", "exportacao", "importacao",
        "investimento", "mercado", "empresa", "negocios", "preco", "barril", "opep",
        "banco nacional de angola", "dolar", "moeda", "credito", "galp", "moeve",
        "receita", "despesa", "fmi", "banco mundial", "comercio", "bpc", "venda",
        "financiamento", "euros", "privatizacao", "esg",
    ],
    "Política": [
        "presidente", "governo", "ministerio", "ministro", "parlamento",
        "assembleia nacional", "partido", "mpla", "unita", "eleicoes", "eleitoral",
        "diplomacia", "embaixada", "oposicao", "decreto", "soberania", "politica",
        "renova angola", "joao lourenco", "constituicao", "gabinete", "visita oficial",
        "ministra", "lourenco", "carta aberta", "investigacao", "deputado",
        "congresso", "procuradoria", "despacho presidencial", "assembleia",
        "secretario de estado", "agt", "desafia", "exige", "conselho de ministros",
    ],
    "Sociedade": [
        "saude", "educacao", "escola", "universidade", "emprego", "vagas", "habitacao",
        "transporte", "agua", "energia", "seguranca", "crime", "polícia", "tribunal",
        "justica", "familia", "crianca", "mulher", "juventude", "cultura", "sociedade",
        "populacao", "cidade", "municipio", "provincia", "chuva", "seca", "fome",
        "vaticano", "papa", "igreja", "pensoes", "reforma",
        "protesto", "protestos", "manifestacao", "manifestantes", "greve",
    ],
    "Entretenimento": [
        "musica", "cantor", "cantora", "album", "show", "concerto", "festival",
        "cinema", "filme", "serie", "teatro", "famoso", "famosa", "celebridade",
        "premio", "gala", "moda", "beleza", "kuduro", "semba", "novela", "reality",
    ],
    "Desporto": [
        "futebol", "jogo", "golo", "campeonato", "torneio", "selecao", "palancas",
        "atletismo", "basquetebol", "andebol", "patinagem", "mundial", "olimpiadas",
        "liga", "treinador", "jogador", "vitoria", "derrota", "empate", "estadio",
    ],
}

LIMIAR = 2  # ocorrências mínimas para atribuir categoria


def normaliza(txt: str) -> str:
    txt = unicodedata.normalize("NFD", txt or "")
    txt = "".join(c for c in txt if unicodedata.category(c) != "Mn")
    return re.sub(r"\s+", " ", txt).lower()


def _conta(texto: str, termo: str) -> int:
    """Ocorrências de palavra inteira (bordas de palavra), não substring."""
    return len(re.findall(r"(?<![\w])" + re.escape(termo) + r"(?![\w])", texto))


def classifica(titulo: str, corpo: str):
    texto = normaliza(f"{titulo} {titulo} {corpo or ''}")  # título pesa 2x
    melhor, melhor_n = None, 0
    contagens = {}
    for cat, termos in REGRAS.items():
        n = sum(_conta(texto, normaliza(t)) for t in termos)
        contagens[cat] = n
        if n > melhor_n:
            melhor, melhor_n = cat, n
    if melhor_n >= LIMIAR:
        return melhor, "regras-palavra-chave", contagens
    return "Outros", "regras-palavra-chave", contagens


def main():
    con = connect()
    init(con)
    rows = con.execute(
        "SELECT id, titulo, corpo_texto FROM artigos WHERE categoria IS NULL"
    ).fetchall()
    n = 0
    for r in rows:
        cat, metodo, _ = classifica(r["titulo"], r["corpo_texto"] or "")
        con.execute(
            "UPDATE artigos SET categoria=?, categoria_metodo=?, categoria_fonte=? WHERE id=?",
            (cat, metodo, "classificador-heuristico", r["id"]),
        )
        n += 1
    con.commit()
    print(f"classificados: {n}")


if __name__ == "__main__":
    main()
