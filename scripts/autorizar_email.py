#!/usr/bin/env python3
"""
Autoriza, revoga e lista os e-mails que entram no site (Cloudflare Access).

O site fica atrás do Cloudflare Access (docs/PUBLICACAO-E-ACESSO.md): só entra
quem está na regra "Emails" da política da aplicação `enchentes`. Pelo painel
são quatro telas; aqui é um comando, na VPS:

    python3 scripts/autorizar_email.py fulano@gmail.com          # autoriza
    python3 scripts/autorizar_email.py --revogar fulano@gmail.com
    python3 scripts/autorizar_email.py --listar
    python3 scripts/autorizar_email.py --renomear Autorizados    # nome da política

CREDENCIAIS, no .env (nunca no código, nunca no chat):

    CLOUDFLARE_API_TOKEN=     token com a permissão de conta
                              "Access: Apps and Policies — Edit", e nada mais
    CLOUDFLARE_ACCOUNT_ID=    o Account ID (painel da Cloudflare, coluna da direita)
    CLOUDFLARE_ACCESS_POLICY_ID=   opcional; sem ele, a política é achada pelo
                              NOME ("Autorizados" ou "Só eu")

A API é a das políticas REUTILIZÁVEIS do Access:
GET/PUT /accounts/{conta}/access/policies/{politica}. Se a política não estiver
lá (política antiga, criada DENTRO da aplicação), o script a procura na
aplicação `enchentes` e grava por /accounts/{conta}/access/apps/{app}/policies/{politica}. O PUT substitui a
política inteira, então o script lê a política, muda SÓ a lista de e-mails (ou
o nome) e devolve o resto como veio — decisão, exclusões, exigências e duração
da sessão não são tocados. Depois do PUT, lê de novo e confere: resposta 200
não é prova de que o e-mail entrou (a mesma lição do painel, que já mostrou
"erro" e "sucesso" na mesma tela).
"""
from __future__ import annotations

import argparse
import os
import re
import sys
from collections.abc import Callable
from typing import Any

import requests

from comum import USER_AGENT, carrega_env

API = "https://api.cloudflare.com/client/v4"
NOMES_DA_POLITICA = ("Autorizados", "Só eu")
NOME_DA_APLICACAO = "enchentes"
#: Campos que a API devolve no GET e que não são da política em si: mandá-los de
#: volta no PUT seria, no melhor caso, ignorado; no pior, recusado.
SO_LEITURA = {"id", "uid", "created_at", "updated_at", "app_count", "reusable", "apps"}
EMAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

Chamada = Callable[[str, str, "dict[str, Any] | None"], dict[str, Any]]


class ErroAcesso(Exception):
    """Erro com mensagem para quem roda o script — nunca carrega o token."""


def chamada_http(token: str) -> Chamada:
    def chamar(metodo: str, caminho: str, corpo: dict[str, Any] | None = None) -> dict[str, Any]:
        r = requests.request(
            metodo, API + caminho, json=corpo, timeout=30,
            headers={"Authorization": f"Bearer {token}", "User-Agent": USER_AGENT},
        )
        try:
            dados = r.json()
        except ValueError as exc:
            raise ErroAcesso(f"{metodo} {caminho}: HTTP {r.status_code}, resposta não é JSON") from exc
        if not r.ok or not dados.get("success", False):
            erros = "; ".join(f"{e.get('code')}: {e.get('message')}" for e in dados.get("errors") or [])
            raise ErroAcesso(f"{metodo} {caminho}: HTTP {r.status_code} — {erros or 'sem detalhe'}")
        return dados
    return chamar


def normaliza(email: str) -> str:
    e = email.strip().lower()
    if not EMAIL.match(e):
        raise ErroAcesso(f"não parece um e-mail: {email!r}")
    return e


def emails_da_politica(pol: dict[str, Any]) -> list[str]:
    return [r["email"]["email"] for r in pol.get("include") or []
            if isinstance(r, dict) and isinstance(r.get("email"), dict) and r["email"].get("email")]


def _pelo_nome(pols: list[dict[str, Any]]) -> dict[str, Any] | None:
    for nome in NOMES_DA_POLITICA:
        achadas = [p for p in pols if p.get("name") == nome]
        if len(achadas) > 1:
            raise ErroAcesso(f"há {len(achadas)} políticas chamadas {nome!r}; "
                             "ponha o id certo em CLOUDFLARE_ACCESS_POLICY_ID")
        if achadas:
            return achadas[0]
    return None


def acha_politica(chamar: Chamada, conta: str, politica_id: str | None) -> dict[str, Any]:
    """A política, com `_caminho` (onde ler e gravar) — reutilizável primeiro, depois a da aplicação."""
    base = f"/accounts/{conta}/access/policies"
    if politica_id:
        return {**chamar("GET", f"{base}/{politica_id}", None)["result"], "_caminho": f"{base}/{politica_id}"}
    todas = chamar("GET", base, None)["result"] or []
    pol = _pelo_nome(todas)
    if pol:
        return {**pol, "_caminho": f"{base}/{pol['id']}"}
    apps = [a for a in chamar("GET", f"/accounts/{conta}/access/apps", None)["result"] or []
            if a.get("name") == NOME_DA_APLICACAO]
    for app in apps:
        caminho_app = f"/accounts/{conta}/access/apps/{app['id']}/policies"
        pol = _pelo_nome(chamar("GET", caminho_app, None)["result"] or [])
        if pol:
            return {**pol, "_caminho": f"{caminho_app}/{pol['id']}"}
    nomes = ", ".join(repr(p.get("name")) for p in todas) or "nenhuma"
    raise ErroAcesso(f"nenhuma política chamada {' ou '.join(map(repr, NOMES_DA_POLITICA))} "
                     f"(reutilizáveis na conta: {nomes}; aplicação {NOME_DA_APLICACAO!r}: "
                     f"{'achada' if apps else 'não achada'}). Ponha o id em CLOUDFLARE_ACCESS_POLICY_ID.")


def grava(chamar: Chamada, conta: str, pol: dict[str, Any], **mudanca: Any) -> dict[str, Any]:
    caminho = pol["_caminho"]
    corpo = {k: v for k, v in pol.items() if k not in SO_LEITURA and k != "_caminho"}
    corpo.update(mudanca)
    chamar("PUT", caminho, corpo)
    # Confere lendo de novo: é a leitura, não o 200 do PUT, que diz o que ficou.
    return {**chamar("GET", caminho, None)["result"], "_caminho": caminho}


def autorizar(chamar: Chamada, conta: str, pol: dict[str, Any], email: str) -> str:
    e = normaliza(email)
    if e in (x.lower() for x in emails_da_politica(pol)):
        return f"{e} já estava autorizado — nada mudou."
    novo = grava(chamar, conta, pol, include=[*(pol.get("include") or []), {"email": {"email": e}}])
    if e not in (x.lower() for x in emails_da_politica(novo)):
        raise ErroAcesso(f"a Cloudflare aceitou o pedido, mas {e} não aparece na política ao reler")
    return f"{e} autorizado na política {novo.get('name')!r}. Ele entra pelo código que chega no e-mail."


def revogar(chamar: Chamada, conta: str, pol: dict[str, Any], email: str) -> str:
    e = normaliza(email)
    include = pol.get("include") or []
    resto = [r for r in include
             if not (isinstance(r, dict) and isinstance(r.get("email"), dict)
                     and str(r["email"].get("email", "")).lower() == e)]
    if len(resto) == len(include):
        return f"{e} não estava na lista — nada mudou."
    if not emails_da_politica({"include": resto}):
        # Sem nenhum e-mail na regra, ou ninguém entra (inclusive você), ou a
        # Cloudflare recusa a política vazia. Nos dois casos, não é pelo script.
        raise ErroAcesso(f"{e} é o último e-mail da política; tirá-lo trancaria o site para todo mundo. "
                         "Se é isso mesmo, faça pelo painel.")
    novo = grava(chamar, conta, pol, include=resto)
    if e in (x.lower() for x in emails_da_politica(novo)):
        raise ErroAcesso(f"a Cloudflare aceitou o pedido, mas {e} continua na política ao reler")
    return f"{e} revogado. Sessões já abertas duram até expirar ({pol.get('session_duration') or 'duração padrão'})."


def renomear(chamar: Chamada, conta: str, pol: dict[str, Any], nome: str) -> str:
    nome = nome.strip()
    if not nome:
        raise ErroAcesso("nome vazio")
    if pol.get("name") == nome:
        return f"a política já se chama {nome!r} — nada mudou."
    antigo = pol.get("name")
    novo = grava(chamar, conta, pol, name=nome)
    if novo.get("name") != nome:
        raise ErroAcesso(f"a Cloudflare aceitou o pedido, mas a política continua {novo.get('name')!r} ao reler")
    return f"política renomeada: {antigo!r} → {nome!r}. Quem entra não muda."


def listar(pol: dict[str, Any]) -> str:
    emails = sorted(emails_da_politica(pol), key=str.lower)
    outras = len(pol.get("include") or []) - len(emails)
    linhas = [f"política {pol.get('name')!r} ({pol.get('decision')}): {len(emails)} e-mail(s)"]
    linhas += [f"  {x}" for x in emails]
    if outras:
        linhas.append(f"  + {outras} regra(s) que não são e-mail (grupo, domínio…) — não mexo nelas")
    return "\n".join(linhas)


def principal(argv: list[str] | None = None, chamar: Chamada | None = None) -> int:
    p = argparse.ArgumentParser(description="Autoriza e revoga e-mails no Cloudflare Access do site.")
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("email", nargs="?", help="e-mail a autorizar")
    g.add_argument("--revogar", metavar="EMAIL")
    g.add_argument("--listar", action="store_true")
    g.add_argument("--renomear", metavar="NOME", help="novo nome da política")
    a = p.parse_args(argv)

    carrega_env()
    conta = os.environ.get("CLOUDFLARE_ACCOUNT_ID", "").strip()
    token = os.environ.get("CLOUDFLARE_API_TOKEN", "").strip()
    if not conta or (chamar is None and not token):
        print("falta CLOUDFLARE_ACCOUNT_ID e/ou CLOUDFLARE_API_TOKEN no .env "
              "(ver o cabeçalho de scripts/autorizar_email.py)", file=sys.stderr)
        return 2
    chamar = chamar or chamada_http(token)
    try:
        pol = acha_politica(chamar, conta, os.environ.get("CLOUDFLARE_ACCESS_POLICY_ID", "").strip() or None)
        if a.listar:
            print(listar(pol))
        elif a.renomear is not None:
            print(renomear(chamar, conta, pol, a.renomear))
        elif a.revogar:
            print(revogar(chamar, conta, pol, a.revogar))
        else:
            print(autorizar(chamar, conta, pol, a.email))
    except ErroAcesso as exc:
        print(f"erro: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(principal())
