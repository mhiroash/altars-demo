#!/usr/bin/env python3
"""Materializa prototipo.html a partir de prototipo.html.b64 (neste ramo).

Porque existe este script: o prototipo tem 21 048 bytes e nao passa pelo conector
de escrita do GitHub. Os mesmos bytes estao aqui ao lado, gzip+base64.
O resultado descodificado e byte-a-byte identico ao original.

Uso (na raiz do ramo prd-v2):
    python3 materializar-prototipo.py

Verifica o md5 e ABORTA se nao bater.
"""
import base64
import gzip
import hashlib
import pathlib
import sys

ALVO_MD5 = "c6ee3a15944c4b0b8a271532fea1fb04"
ALVO_SIZE = 21048

raiz = pathlib.Path(__file__).parent
b64 = (raiz / "prototipo.html.b64").read_text().strip()
dados = gzip.decompress(base64.b64decode(b64))
md5 = hashlib.md5(dados).hexdigest()
print(f"bytes: {len(dados)}  md5: {md5}")

if md5 != ALVO_MD5 or len(dados) != ALVO_SIZE:
    sys.exit(f"ERRO: nao bate com o alvo ({ALVO_SIZE} bytes / {ALVO_MD5})")

(raiz / "prototipo.html").write_bytes(dados)
print("OK: prototipo.html escrito e verificado")
