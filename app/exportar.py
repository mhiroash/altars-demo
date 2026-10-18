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


def gerar_png(peca: dict, template_saida: str | None = None) -> bytes:
    """Gera PNG usando imagemagick (convert). Retorna bytes."""
    try:
        import subprocess
        import tempfile
    except Exception as exc:
        raise ImportError("imagemagick/convert não instalado") from exc

    pdf_bytes = gerar_pdf(peca, template_saida=template_saida)

    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp_pdf:
        tmp_pdf.write(pdf_bytes)
        tmp_pdf_path = tmp_pdf.name

    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp_png:
        tmp_png_path = tmp_png.name

    try:
        subprocess.run(
            ["convert", "-density", "300", tmp_pdf_path, "-quality", "90", tmp_png_path],
            check=True,
            capture_output=True,
        )
        with open(tmp_png_path, "rb") as f:
            return f.read()
    finally:
        for path in (tmp_pdf_path, tmp_png_path):
            if os.path.exists(path):
                os.unlink(path)