#!/usr/bin/env python3
"""Altars — recolector de portais via RSS (RF-1.1 + RF-1.6).

Fetch respeitoso: User-Agent identificável, robots.txt verificado antes de
cada anfitrião, rate-limit entre pedidos. O original integral (HTML) fica
arquivado com sha256, mesmo que a fonte o altere depois.
"""
import hashlib
import html
import re
import sys
import time
import urllib.robotparser
import urllib.request
from html.parser import HTMLParser
from urllib.parse import urlparse

from db import connect, init

UA = "AltarsDemoPipeline/0.1 (recolha editorial demo; contacto: ellocene-lda)"
PAUSA_ENTRE_PEDIDOS = 5.0  # segundos (ADR D3: intervalo ≥5 s entre pedidos)

# 1 principal + 2 alternativas, todos validados a 17/10/2026 (ver provas/).
FEEDS = [
    {"nome": "Correio Kianda", "url": "https://www.correiokianda.info/feed/", "pais": "AO"},
    {"nome": "Maka Angola", "url": "https://www.makaangola.org/feed/", "pais": "AO"},
    {"nome": "ECO", "url": "https://eco.sapo.pt/rss/", "pais": "PT"},
]

_ENTIDADES_SEGURAS = {"amp", "lt", "gt", "quot", "apos", "nbsp", "mdash", "ldquo", "rdquo"}


class ExtratorTexto(HTMLParser):
    """Extrai texto visível de HTML, ignorando script/style."""

    def __init__(self):
        super().__init__()
        self.pedacos = []
        self.ignorar = 0

    def handle_starttag(self, tag, attrs):
        if tag in ("script", "style"):
            self.ignorar += 1
        if tag in ("p", "br", "div", "h1", "h2", "h3", "li"):
            self.pedacos.append("\n")

    def handle_endtag(self, tag):
        if tag in ("script", "style") and self.ignorar > 0:
            self.ignorar -= 1

    def handle_data(self, data):
        if not self.ignorar and data.strip():
            self.pedacos.append(data)


def html_para_texto(bruto: str) -> str:
    p = ExtratorTexto()
    try:
        p.feed(bruto)
    except Exception:
        pass
    txt = "".join(p.pedacos)
    txt = re.sub(r"[ \t]+", " ", txt)
    txt = re.sub(r"\n{3,}", "\n\n", txt)
    return txt.strip()


def xml_tolerante(data: bytes) -> str:
    txt = data.decode("utf-8", errors="replace")

    def repl(m):
        e = m.group(1)
        if e in _ENTIDADES_SEGURAS or re.fullmatch(r"#\d+", e) or re.fullmatch(r"#x[0-9a-fA-F]+", e):
            return m.group(0)
        return " "

    return re.sub(r"&(\w+);", repl, txt)


def robots_permite(url: str) -> bool:
    """Busca robots.txt com o NOSSO UA (o parser por omissão usa o UA do Python,
    que alguns sites respondem com 403 — e aí o parser bloqueia tudo, falso negativo)."""
    rp = urllib.robotparser.RobotFileParser()
    raiz = f"{urlparse(url).scheme}://{urlparse(url).netloc}"
    try:
        bruto = pedir(f"{raiz}/robots.txt").decode("utf-8", errors="replace")
        rp.parse(bruto.splitlines())
    except Exception as e:
        print(f"  [robots] {raiz}: não legível ({e}) — a recolher com rate-limit conservador")
        return True
    ok = rp.can_fetch(UA, url) and rp.can_fetch("*", url)
    delay = rp.crawl_delay(UA) or rp.crawl_delay("*")
    if delay:
        global PAUSA_ENTRE_PEDIDOS
        PAUSA_ENTRE_PEDIDOS = max(PAUSA_ENTRE_PEDIDOS, float(delay))
    return ok


def pedir(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept-Language": "pt-PT,pt;q=0.9"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read()


_TAG_PERIGOSO = re.compile(
    r"<\s*(script|iframe|object|embed|style|link|meta|base|form)\b[^>]*>.*?<\s*/\s*\1\s*>",
    re.S | re.I,
)
_TAG_PERIGOSO_ORFAO = re.compile(
    r"<\s*/?\s*(script|iframe|object|embed|style|link|meta|base|form)\b[^>]*>", re.I
)
_ATRIBUTO_EVENTO = re.compile(r"\son[a-z]+\s*=\s*(\"[^\"]*\"|'[^']*'|[^\s>]+)", re.I)
_ATRIBUTO_SRCDOC = re.compile(r"\ssrcdoc\s*=\s*(\"[^\"]*\"|'[^']*'|[^\s>]+)", re.I)
_URL_ATRIBUTO = re.compile(
    r"\s(href|src|xlink:href|action|formaction)\s*=\s*(\"[^\"]*\"|'[^']*'|[^\s>]+)", re.I
)
_ESQUEMA_PERIGOSO = re.compile(r"^\s*(javascript|vbscript|data)\s*:", re.I)


def _url_seguro(valor: str) -> bool:
    v = valor.strip()
    if len(v) >= 2 and v[0] in "\"'" and v[-1] == v[0]:
        v = v[1:-1]
    return not _ESQUEMA_PERIGOSO.match(v)


def limpar_html_conteudo(conteudo: str) -> str:
    """Remove scripts/iframes/objetos, atributos de evento (on*) e URLs
    perigosas (javascript:/data:/vbscript:) antes de arquivar ou extrair texto.
    Cobre on* com aspas duplas, aspas simples e sem aspas."""
    if not conteudo:
        return conteudo
    conteudo = _TAG_PERIGOSO.sub("", conteudo)
    conteudo = _TAG_PERIGOSO_ORFAO.sub("", conteudo)
    conteudo = _ATRIBUTO_EVENTO.sub("", conteudo)
    conteudo = _ATRIBUTO_SRCDOC.sub("", conteudo)
    conteudo = _URL_ATRIBUTO.sub(
        lambda m: "" if not _url_seguro(m.group(2)) else m.group(0), conteudo
    )
    return conteudo


def recolher_feed(feed: dict, con, max_artigos: int = 8):
    import xml.etree.ElementTree as ET

    print(f"== {feed['nome']} ({feed['url']})")
    if not robots_permite(feed["url"]):
        print("  [robots] bloqueado — a saltar")
        return 0
    data = pedir(feed["url"])
    raiz = ET.fromstring(xml_tolerante(data))
    itens = raiz.findall(".//item")[:max_artigos]
    n = 0
    for it in itens:
        def campo(tag):
            el = it.find(tag)
            return (el.text or "").strip() if el is not None else ""

        titulo = html.unescape(limpar_html_conteudo(campo("title")))
        link = campo("link")
        autor = campo("dc:creator") or campo("author") or feed["nome"]
        data_pub = campo("pubDate")
        conteudo_html = campo("content:encoded") or campo("description")
        cats = [c.text.strip() for c in it.findall("category") if c.text]
        if not titulo or not link:
            continue
        ja = con.execute("SELECT id FROM artigos WHERE url=?", (link,)).fetchone()
        if ja:
            continue
        # Arquivo integral da página original (RF-1.6)
        try:
            bruto = pedir(link)  # bytes
            bruto_txt = limpar_html_conteudo(bruto.decode("utf-8", errors="replace"))
            # O hash cobre EXATAMENTE o que fica arquivado (senão a verificação
            # de integridade nunca bate certo — bug corrigido a 17/10).
            sha = hashlib.sha256(bruto_txt.encode("utf-8")).hexdigest()
        except Exception as e:
            print(f"  [arquivo] falhou {link}: {e}")
            bruto_txt, sha = "", "indisponivel"
        corpo = html_para_texto(limpar_html_conteudo(conteudo_html))
        if not corpo and bruto_txt:
            corpo = html_para_texto(limpar_html_conteudo(bruto_txt))[:8000]
        cur = con.execute(
            """INSERT INTO artigos (fonte, url, titulo, autor, data_publicacao,
               categoria, categoria_metodo, categoria_fonte, corpo_texto, coletado_em)
               VALUES (?,?,?,?,?,NULL,NULL,NULL,?,datetime('now'))""",
            (feed["nome"], link, titulo, autor, data_pub, corpo),
        )
        con.execute(
            """INSERT INTO arquivo (artigo_id, origem, html, sha256, coletado_em)
               VALUES (?,?,?,?,datetime('now'))""",
            (cur.lastrowid, link, bruto_txt or "", sha),
        )
        con.commit()
        print(f"  + [{feed['nome']}] {titulo[:70]} | autor={autor[:30]} | cats={cats[:3]}")
        n += 1
        time.sleep(PAUSA_ENTRE_PEDIDOS)
    return n


def main():
    max_artigos = int(sys.argv[1]) if len(sys.argv) > 1 else 8
    con = connect()
    init(con)
    total = 0
    for feed in FEEDS:
        try:
            total += recolher_feed(feed, con, max_artigos)
        except Exception as e:
            print(f"  ERRO em {feed['nome']}: {type(e).__name__} {e}")
    print(f"\nTOTAL novos artigos: {total}")


if __name__ == "__main__":
    main()
