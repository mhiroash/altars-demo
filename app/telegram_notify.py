#!/usr/bin/env python3
"""Altars — modulo Telegram (alerta do MIREX no telemovel).

O token NUNCA fica em codigo: vem da variavel de ambiente TELEGRAM_BOT_TOKEN.
O chat id vem de TELEGRAM_CHAT_ID. Sem essas variaveis, o modulo fica em modo
"desligado" e nao faz rede (para o demo correr sem credenciais).
"""
from __future__ import annotations

import json
import os
import urllib.request

def _bot_token() -> str:
    """Lido em runtime (não no import) para os testes poderem definir a env."""
    return os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()


def _chat_id() -> str:
    return os.environ.get("TELEGRAM_CHAT_ID", "").strip()


def ativo() -> bool:
    return bool(_bot_token() and _chat_id())


def enviar(texto: str, fetcher=None) -> dict:
    """Envia mensagem. Devolve {enviado: bool, motivo: str}."""
    if not ativo():
        return {"enviado": False, "motivo": "TELEGRAM_BOT_TOKEN/TELEGRAM_CHAT_ID ausentes — modo desligado"}
    url = f"https://api.telegram.org/bot{_bot_token()}/sendMessage"
    payload = json.dumps({"chat_id": _chat_id(), "text": texto, "parse_mode": "HTML"}).encode("utf-8")
    if fetcher is not None:
        return {"enviado": True, "resposta": fetcher(url, payload)}
    req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=20) as resp:  # noqa: S310
        return {"enviado": True, "resposta": json.loads(resp.read().decode("utf-8"))}


def formatar_alerta(alerta: dict) -> str:
    return (
        "🔔 <b>Alerta de perfil</b>\n"
        f"Perfil: {alerta.get('perfil', '—')}\n"
        f"Título: {alerta.get('titulo', '—')}\n"
        f"Prioridade: {alerta.get('prioridade', '—')}\n"
        f"Latência: {alerta.get('latencia_s', '—')} s\n"
        f"{alerta.get('url', '')}"
    )
