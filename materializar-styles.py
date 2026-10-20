#!/usr/bin/env python3
"""Materializa styles.css a partir de styles.css.gz.b64 (que ja existe neste ramo).

Porque existe este script: o styles.css real tem 29 513 bytes e nao passa pelo
conector de escrita do GitHub (limite de payload). Os mesmos bytes estao aqui ao
lado, comprimidos em gzip+base64, em `styles.css.gz.b64` (7 584 caracteres).
O conteudo descodificado e byte-a-byte identico ao original.

Uso (na raiz do ramo preview-gate2):
    python3 materializar-styles.py

Verifica o md5 e ABORTA se nao bater. Nunca escreve um ficheiro errado.
"""
import base64
import gzip
import hashlib
import pathlib
import sys

ALVO_MD5 = "5a3600663bf2b03cd02568da34ca4dc9"
ALVO_SIZE = 29513

fonte = pathlib.Path(__file__).with_name("styles.css.gz.b64")
if not fonte.exists():
    sys.exit("ERRO: styles.css.gz.b64 nao existe nesta pasta")

dados = gzip.decompress(base64.b64decode(fonte.read_text().strip()))
md5 = hashlib.md5(dados).hexdigest()
print(f"bytes: {len(dados)}  md5: {md5}")

if md5 != ALVO_MD5 or len(dados) != ALVO_SIZE:
    sys.exit(f"ERRO: nao bate com o alvo ({ALVO_SIZE} bytes / {ALVO_MD5})")

pathlib.Path(__file__).with_name("styles.css").write_bytes(dados)
print("OK: styles.css escrito e verificado")
