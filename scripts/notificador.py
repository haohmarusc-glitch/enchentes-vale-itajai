#!/usr/bin/env python3
"""
Envio de aviso por Telegram. Só envia — não recebe comando, não tem menu.

Existe porque o site é *pull*: só serve para quem abre a página. Ninguém abre
uma página às três da manhã, que é justamente quando várias das cheias
históricas do Vale atingiram o pico. O aviso vai atrás da pessoa.

Credencial nunca entra em código nem em JSON: `TELEGRAM_BOT_TOKEN` e
`TELEGRAM_CHAT_ID` vêm do ambiente ou do `.env` (que está no `.gitignore`).
O token nunca aparece em log — nem em mensagem de erro, porque o Telegram
devolve a URL inteira no corpo do erro e a URL carrega o token.

Uso:
    python3 scripts/notificador.py --teste       # manda uma mensagem de teste
"""

from __future__ import annotations

import argparse
import html
import os
import sys

from comum import carrega_env

TIMEOUT_S = 15

#: O Telegram recusa mensagem acima de 4096 caracteres, e recusa é silêncio —
#: o pior resultado possível num aviso de cheia. Cortamos antes, com marca, em
#: vez de descobrir na hora que a mensagem não saiu.
LIMITE_CARACTERES = 4096
CORTE = "\n\n<i>[mensagem cortada por limite do Telegram]</i>"


def _credenciais() -> tuple[str, str]:
    carrega_env()
    return os.environ.get("TELEGRAM_BOT_TOKEN", ""), os.environ.get("TELEGRAM_CHAT_ID", "")


def configurado() -> bool:
    token, chat = _credenciais()
    return bool(token and chat)


def esc(texto: object) -> str:
    """
    Escapa para o parse_mode HTML do Telegram.

    Obrigatório em qualquer texto vindo da fonte. Um nome de estação com `&`
    cru — "Rio Itajaí-Açu - ICMBio & CEPSUL" — faz o Telegram responder 400 e
    a mensagem simplesmente não sai. Um aviso de cheia que não sai é pior que
    um aviso feio.
    """
    return html.escape(str(texto), quote=False)


def _sem_token(texto: str, token: str) -> str:
    """Tira o token de qualquer texto antes de ele virar log."""
    return texto.replace(token, "***") if token else texto


def enviar_para(chat_id: str, mensagem: str) -> bool:
    """
    Manda a mensagem para um chat específico.

    Existe para o bot de consulta responder a quem perguntou, que não é
    necessariamente o dono do `TELEGRAM_CHAT_ID` — esse continua sendo o
    destino dos avisos automáticos de cota.
    """
    return _postar(chat_id, mensagem)


def enviar(mensagem: str) -> bool:
    """Manda a mensagem para o chat do dono. Devolve True se o Telegram aceitou."""
    _, chat = _credenciais()
    return _postar(chat, mensagem)


def encurtar(mensagem: str) -> str:
    """Corta no limite do Telegram, preservando a marca de que houve corte."""
    if len(mensagem) <= LIMITE_CARACTERES:
        return mensagem
    return mensagem[: LIMITE_CARACTERES - len(CORTE)] + CORTE


def _postar(chat: str, mensagem: str) -> bool:
    mensagem = encurtar(mensagem)
    token, _ = _credenciais()
    if not (token and chat):
        print(
            "Telegram não configurado (TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID). "
            "Mensagem que teria sido enviada:\n" + mensagem,
            file=sys.stderr,
        )
        return False

    import requests  # só no caminho que usa rede

    try:
        resposta = requests.post(
            f"https://api.telegram.org/bot{token}/sendMessage",
            json={
                "chat_id": chat,
                "text": mensagem,
                "parse_mode": "HTML",
                "disable_web_page_preview": True,
            },
            timeout=TIMEOUT_S,
        )
    except Exception as exc:  # rede caindo não pode derrubar a coleta
        print(f"falha ao enviar Telegram: {_sem_token(str(exc), token)}", file=sys.stderr)
        return False

    if resposta.status_code != 200:
        print(
            f"Telegram HTTP {resposta.status_code}: "
            f"{_sem_token(resposta.text[:300], token)}",
            file=sys.stderr,
        )
        return False
    return True


def main() -> int:
    ap = argparse.ArgumentParser(description="Envia uma mensagem de teste.")
    ap.add_argument("--teste", action="store_true", help="manda uma mensagem de teste")
    ap.add_argument("--texto", default="Teste do aviso de cheias do Vale do Itajaí.")
    args = ap.parse_args()
    if not args.teste:
        ap.print_help()
        return 0
    if not configurado():
        print("Configure TELEGRAM_BOT_TOKEN e TELEGRAM_CHAT_ID no .env.", file=sys.stderr)
        return 1
    ok = enviar(esc(args.texto))
    print("enviado." if ok else "não enviado.")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
