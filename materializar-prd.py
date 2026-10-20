#!/usr/bin/env python3
"""Materializa PRD-de-produto-v2.0.md a partir de PRD.part01..04.b64 (neste ramo).

Porque existe este script: o PRD tem 55 646 bytes e nao passa pelo conector de
escrita do GitHub. Os mesmos bytes estao aqui ao lado, gzip+base64, em quatro
partes de 7 500/4 916 caracteres. O resultado descodificado e byte-a-byte
identico ao original.

Uso (na raiz do ramo prd-v2):
    python3 materializar-prd.py

Verifica o md5 e ABORTA se nao bater.
"""
import base64
import gzip
import hashlib
import pathlib
import sys

ALVO_MD5 = "d765e3018fff93ad6534d30d6957ac93"
ALVO_SIZE = 55646
PARTES = [f"PRD.part{i:02d}.b64" for i in range(1, 5)]

raiz = pathlib.Path(__file__).parent
b64 = "".join((raiz / p).read_text().strip() for p in PARTES)
dados = gzip.decompress(base64.b64decode(b64))
md5 = hashlib.md5(dados).hexdigest()
print(f"bytes: {len(dados)}  md5: {md5}")

if md5 != ALVO_MD5 or len(dados) != ALVO_SIZE:
    sys.exit(f"ERRO: nao bate com o alvo ({ALVO_SIZE} bytes / {ALVO_MD5})")

(raiz / "PRD-de-produto-v2.0.md").write_bytes(dados)
print("OK: PRD-de-produto-v2.0.md escrito e verificado")
