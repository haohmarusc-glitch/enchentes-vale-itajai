#!/usr/bin/env python3
"""Baixa séries históricas de cota das estações da ANA (HidroWeb / SNIRH).

Estado: **o acesso à API ainda não foi concedido** (pendência do README). O
script está pronto para rodar assim que as credenciais chegarem, e por isso
todo detalhe do endpoint é configurável — nada aqui foi confirmado contra a
API real, e sair chutando caminho de URL só geraria dado silenciosamente
errado.

Configuração (`.env` na raiz, já ignorado pelo git):

    ANA_IDENTIFICADOR=seu_identificador
    ANA_SENHA=sua_senha
    # opcionais, para ajustar quando a documentação for confirmada:
    ANA_BASE_URL=https://www.ana.gov.br/hidrowebservice
    ANA_ROTA_AUTENTICACAO=/EstacoesTelemetricas/OAUth/v1
    ANA_ROTA_SERIE=/EstacoesTelemetricas/HidroSerieCotas/v1

Uso:

    python3 scripts/ana_hidroweb.py --verificar          # testa a autenticação
    python3 scripts/ana_hidroweb.py                      # baixa todas as estações
    python3 scripts/ana_hidroweb.py --estacao 83800002   # só uma

As séries brutas vão para `data/series/<codigo>.json` (fora do git, são
grandes). Este script **não escreve** em `enchentes.json`: transformar série
bruta em pico histórico é decisão que passa por conferência humana.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import date, datetime
from pathlib import Path

try:
    import requests
except ImportError:  # pragma: no cover - ambiente sem dependências
    print("Falta a dependência: pip install -r scripts/requirements.txt", file=sys.stderr)
    raise SystemExit(2)

from comum import DADOS, USER_AGENT, carrega_env, cidades, espera_turno

SERIES = DADOS / "series"


def base_url() -> str:
    return os.environ.get("ANA_BASE_URL", "https://www.ana.gov.br/hidrowebservice").rstrip("/")


def autentica(sessao: requests.Session) -> str:
    """Devolve o token da API. Levanta RuntimeError com mensagem legível se falhar."""
    identificador = os.environ.get("ANA_IDENTIFICADOR")
    senha = os.environ.get("ANA_SENHA")
    if not identificador or not senha:
        raise RuntimeError(
            "ANA_IDENTIFICADOR e ANA_SENHA não estão no ambiente. "
            "Peça acesso em hidro@ana.gov.br e preencha o .env."
        )

    rota = os.environ.get("ANA_ROTA_AUTENTICACAO", "/EstacoesTelemetricas/OAUth/v1")
    espera_turno()
    resposta = sessao.get(
        f"{base_url()}{rota}",
        headers={"Identificador": identificador, "Senha": senha},
        timeout=30,
    )
    if resposta.status_code != 200:
        raise RuntimeError(
            f"autenticação falhou (HTTP {resposta.status_code}). "
            "Confira credenciais e, se a API tiver mudado, ajuste ANA_ROTA_AUTENTICACAO."
        )
    corpo = resposta.json()
    token = (corpo.get("items") or {}).get("tokenautenticacao") or corpo.get("token")
    if not token:
        raise RuntimeError(f"a resposta não trouxe token reconhecível: {json.dumps(corpo)[:300]}")
    return token


def baixa_serie(
    sessao: requests.Session, token: str, codigo: str, inicio: str, fim: str
) -> dict:
    rota = os.environ.get("ANA_ROTA_SERIE", "/EstacoesTelemetricas/HidroSerieCotas/v1")
    espera_turno()
    resposta = sessao.get(
        f"{base_url()}{rota}",
        headers={"Authorization": f"Bearer {token}"},
        params={
            "Código da Estação": codigo,
            "Tipo Filtro Data": "DATA_LEITURA",
            "Data Inicial (yyyy-MM-dd)": inicio,
            "Data Final (yyyy-MM-dd)": fim,
        },
        timeout=120,
    )
    if resposta.status_code != 200:
        raise RuntimeError(f"estação {codigo}: HTTP {resposta.status_code}")
    return resposta.json()


def grava_serie(codigo: str, conteudo: dict) -> Path:
    """Idempotente: reescrever a mesma janela não duplica nada."""
    SERIES.mkdir(parents=True, exist_ok=True)
    destino = SERIES / f"{codigo}.json"
    temporario = destino.with_suffix(".json.tmp")
    temporario.write_text(
        json.dumps(
            {
                "codigo_ana": codigo,
                "baixado_em": datetime.now().astimezone().isoformat(timespec="seconds"),
                "fonte": "ANA / HidroWeb (SNIRH)",
                "resposta": conteudo,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    temporario.replace(destino)
    return destino


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--estacao", help="baixa só o código informado")
    ap.add_argument("--inicio", default="1930-01-01", help="data inicial (AAAA-MM-DD)")
    ap.add_argument("--fim", default=date.today().isoformat(), help="data final (AAAA-MM-DD)")
    ap.add_argument("--verificar", action="store_true", help="só testa a autenticação e sai")
    args = ap.parse_args()

    carrega_env()
    sessao = requests.Session()
    sessao.headers["User-Agent"] = USER_AGENT

    try:
        token = autentica(sessao)
    except RuntimeError as e:
        print(f"ERRO: {e}", file=sys.stderr)
        return 1

    print("Autenticado na API da ANA.")
    if args.verificar:
        return 0

    if args.estacao:
        alvos = [{"codigo_ana": args.estacao, "nome": args.estacao}]
    else:
        alvos = [c for c in cidades() if c.get("codigo_ana")]
        sem_codigo = [c["nome"] for c in cidades() if not c.get("codigo_ana")]
        if sem_codigo:
            print(f"Sem código ANA (pendência): {', '.join(sem_codigo)}")

    if not alvos:
        print("Nenhuma estação com codigo_ana preenchido em estacoes.json.")
        return 0

    falhas = 0
    for alvo in alvos:
        codigo = str(alvo["codigo_ana"])
        try:
            conteudo = baixa_serie(sessao, token, codigo, args.inicio, args.fim)
        except (RuntimeError, requests.RequestException) as e:
            print(f"falhou {alvo['nome']} ({codigo}): {e}", file=sys.stderr)
            falhas += 1
            continue
        destino = grava_serie(codigo, conteudo)
        print(f"{alvo['nome']} ({codigo}) -> {destino.relative_to(DADOS.parent)}")

    return 1 if falhas else 0


if __name__ == "__main__":
    raise SystemExit(main())
