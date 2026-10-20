#!/usr/bin/env python3
"""Altars — exportacao de peças em PDF e PNG.

Requisitos (instalados em /workspace/altars/):
- reportlab para PDF
- imagemagick (convert) para PNG
- reportlab/cairo para geração de PNG (se disponivel)
"""
from __future__ import annotations

import io
import os
import re
from datetime import datetime, timezone

PDF_FONT = "Helvetica"
PNG_FONT = "Helvetica"


def slug_para_nome_completo(slug: str) -> str:
    """Slug (ex.: 123-abc) → arquivo (ex.: 123_ab_eco)."""
    return re.sub(r"[-_]", "_", slug)


def gerar_pdf(peca: dict, template_saida: str | None = None) -> bytes:
    """Gera PDF usando reportlab. Retorna bytes."""
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import mm
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
    except Exception as exc:
        raise ImportError("reportlab não instalado") from exc

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, leftMargin=20 * mm, rightMargin=20 * mm, topMargin=20 * mm, bottomMargin=20 * mm)

    styles = getSampleStyleSheet()
    styles["Normal"].fontName = "Helvetica"
    styles["Normal"].fontSize = 10
    styles["Normal"].spaceAfter = 6 * mm

    p = []
    for campo in ["antetitulo", "titulo", "corpo"]:
        if campo not in peca:
            continue
        texto = str(peca[campo]).strip()
        if not texto:
            continue
        if campo == "antetitulo":
            styles["Heading5"].fontName = "Helvetica-Bold"
            styles["Heading5"].fontSize = 11
            p.append(Paragraph(texto, styles["Heading5"]))
        elif campo == "titulo":
            styles["Heading4"].fontName = "Helvetica-Bold"
            styles["Heading4"].fontSize = 12
            p.append(Paragraph(texto, styles["Heading4"]))
        elif campo == "corpo":
            p.append(Paragraph(texto, styles["Normal"]))
        p.append(Spacer(1, 3 * mm))

    doc.build(p)
    return buffer.getvalue()


def _pdf_para_imagem(peca: dict, fmt: str, dpi: int = 150) -> bytes:
    """Converte o PDF da peça para PNG ou JPG via pdftoppm (poppler-utils).

    Nota: o ImageMagick do sistema bloqueia PDF na security policy
    (/etc/ImageMagick-6/policy.xml), por isso o `convert` não serve.
    `pdftoppm` é a via validada pelo QA (relatorio-qa-demo-v2.md).
    """
    import subprocess
    import tempfile

    pdf_bytes = gerar_pdf(peca, template_saida=None)

    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp_pdf:
        tmp_pdf.write(pdf_bytes)
        tmp_pdf_path = tmp_pdf.name

    try:
        flag = "-png" if fmt == "png" else "-jpeg"
        out_prefix = tmp_pdf_path + "_img"
        subprocess.run(
            ["pdftoppm", flag, "-r", str(dpi), tmp_pdf_path, out_prefix],
            check=True,
            capture_output=True,
        )
        # pdftoppm nomeia a saída prefix-1.png (ou -1.jpg); página única.
        for ext in (".png", ".jpg"):
            path = out_prefix + "-1" + ext
            if os.path.exists(path):
                with open(path, "rb") as f:
                    data = f.read()
                os.unlink(path)
                return data
        raise RuntimeError(f"pdftoppm não gerou o ficheiro esperado: {out_prefix}-1.*")
    finally:
        if os.path.exists(tmp_pdf_path):
            os.unlink(tmp_pdf_path)


def gerar_png(peca: dict, template_saida: str | None = None) -> bytes:
    """Gera PNG da peça (via pdftoppm). Retorna bytes."""
    return _pdf_para_imagem(peca, "png")


def gerar_jpg(peca: dict, template_saida: str | None = None) -> bytes:
    """Gera JPG da peça (via pdftoppm). Retorna bytes."""
    return _pdf_para_imagem(peca, "jpg")


# ---------------------------------------------------------------------------
# Persistência em disco (RF-5.3): cada exportação fica em EXPORT_DIR e é
# registada na tabela `exportacoes`. O QA/Segurança verificam ficheiros reais.
# ---------------------------------------------------------------------------
EXPORT_DIR = os.environ.get(
    "ALTARS_EXPORT_DIR",
    os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "exports"),
)

_GERADORES = {"pdf": gerar_pdf, "png": gerar_png, "jpg": gerar_jpg}
_MEDIA = {"pdf": "application/pdf", "png": "image/png", "jpg": "image/jpeg"}


def media_type(formato: str) -> str:
    return _MEDIA.get(formato, "application/octet-stream")


def exportar_para_disco(peca: dict, formato: str) -> tuple[str, bytes]:
    """Gera a peça no formato pedido, grava em EXPORT_DIR e devolve
    (caminho, bytes). Levanta ValueError se o formato for desconhecido."""
    gerador = _GERADORES.get(formato)
    if gerador is None:
        raise ValueError(f"formato inválido: {formato}")
    os.makedirs(EXPORT_DIR, exist_ok=True)
    dados = gerador(peca)
    peca_id = peca.get("id", "sem-id")
    caminho = os.path.join(EXPORT_DIR, f"altars-{peca_id}.{formato}")
    with open(caminho, "wb") as fh:
        fh.write(dados)
    return caminho, dados
