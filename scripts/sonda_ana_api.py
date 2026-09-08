#!/usr/bin/env python3
"""Descobre o FORMATO de duas rotas da API da ANA, sem gravar dado no projeto.

POR QUE UMA SONDA, E NÃO UM COLETOR (08/09/2026)
No mesmo dia em que o acesso saiu, a `HidroSerieCotas` ensinou que o formato da
resposta é o que decide tudo: uma consulta devolve VÁRIAS linhas para o mesmo
mês, e a de rótulo melhor (`nivelconsistencia: 2`) apagava uma cheia de 4 m.
Escrever coletor contra formato suposto seria repetir isso de olhos fechados —
ver `docs/ANA-API-2026-09-08.md`.

Esta sonda chama, mede e IMPRIME. Não escreve em `data/estacoes.json` nem em
`data/enchentes.json`. O único arquivo que ela grava é o bruto do inventário,
em `data/brutos/`, porque bruto é evidência e o projeto tem um guarda que cobra
evidência citada (`valida_brutos_citados`).

DUAS PERGUNTAS, uma execução:

1. `HidroInventarioEstacoes` — quais estações da ANA existem em SC, e o que a
   API diz de cada uma? É o que fecha a pendência do inventário e o que responde
   se a 83800002 e as outras estão nesta rede.

2. `HidroinfoanaSerieTelemetricaAdotada` — a série telemétrica tem NÍVEL AO VIVO
   para estações da bacia? Doze cidades estão com o pino cinza no mapa, e esse é
   o item que mais escurece a tela. Aqui a sonda só olha; quem decide se vira
   fonte é a conferência de régua, que é outra conversa.

⚠️ NÃO RODA DESTE AMBIENTE: `*.ana.gov.br` é bloqueado no proxy (403 no
CONNECT). Rode na VPS, com o `.env` preenchido por `scripts/configurar_ana.sh`.

Uso:
    python3 scripts/sonda_ana_api.py
    python3 scripts/sonda_ana_api.py --uf SC --estacoes 83900000,83870001
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import date

try:
    import requests
except ImportError:  # pragma: no cover - ambiente sem dependências
    print("Falta a dependência: pip install -r scripts/requirements.txt", file=sys.stderr)
    raise SystemExit(2)

from ana_hidroweb import autentica, base_url
from comum import DADOS, USER_AGENT, carrega_env, espera_turno

ROTA_INVENTARIO = "/EstacoesTelemetricas/HidroInventarioEstacoes/v1"
ROTA_TELEMETRIA = "/EstacoesTelemetricas/HidroinfoanaSerieTelemetricaAdotada/v1"

#: Candidatas a nível ao vivo, escolhidas por terem escala ABERTA no nosso
#: cadastro. Não são "as réguas das cidades" — a conferência de régua é outra
#: etapa, e confundir as duas é como o Salseiro quase entrou em Vidal Ramos.
CANDIDATAS = ["83900000", "83870001", "83520000", "83840000", "83800002"]

#: Quantas chaves de exemplo imprimir por item. O objetivo é DESENHAR o
#: coletor, não ler o inventário inteiro na tela.
AMOSTRA = 3


def _pede(sessao: requests.Session, token: str, rota: str, params: dict) -> dict:
    espera_turno()
    r = sessao.get(f"{base_url()}{rota}", headers={"Authorization": f"Bearer {token}"},
                   params=params, timeout=120)
    if r.status_code != 200:
        return {"_erro": f"HTTP {r.status_code}", "_corpo": r.text[:300]}
    return r.json()


def _resumo(corpo: dict) -> tuple[str, list]:
    if "_erro" in corpo:
        return corpo["_erro"] + " — " + corpo.get("_corpo", ""), []
    itens = corpo.get("items")
    if not isinstance(itens, list):
        return f"resposta sem lista 'items' (chaves: {list(corpo)})", []
    return f"{corpo.get('message')!r} — {len(itens)} item(ns)", itens


def sonda_inventario(sessao, token, uf: str) -> list:
    print(f"\n{'=' * 70}\n1. INVENTÁRIO — Unidade Federativa = {uf}\n{'=' * 70}")
    corpo = _pede(sessao, token, ROTA_INVENTARIO, {"Unidade Federativa": uf})
    linha, itens = _resumo(corpo)
    print(f"   {linha}")
    if not itens:
        return []

    print(f"\n   CAMPOS de um item ({len(itens[0])}):")
    for k, v in itens[0].items():
        print(f"      {k} = {v!r}")

    print(f"\n   AMOSTRA de {min(AMOSTRA, len(itens))}:")
    for it in itens[:AMOSTRA]:
        print(f"      {json.dumps(it, ensure_ascii=False)[:200]}")

    destino = DADOS / "brutos" / f"ana-inventario-api-{date.today().isoformat()}.json"
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_text(json.dumps(corpo, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"\n   bruto gravado em {destino.relative_to(DADOS.parent)} "
          f"({destino.stat().st_size // 1024} KB) — COMMITAR: é a evidência que "
          "cinco blocos do estacoes.json citam e que hoje não existe no repo.")
    return itens


def sonda_telemetria(sessao, token, codigos: list[str]) -> None:
    print(f"\n{'=' * 70}\n2. SÉRIE TELEMÉTRICA — nível ao vivo?\n{'=' * 70}")
    for codigo in codigos:
        corpo = _pede(sessao, token, ROTA_TELEMETRIA, {
            "Código da Estação": codigo,
            "Tipo Filtro Data": "DATA_LEITURA",
            "Data de Busca (yyyy-MM-dd)": date.today().isoformat(),
            "Range Intervalo de busca": "HORA_24",
        })
        linha, itens = _resumo(corpo)
        print(f"\n   {codigo}: {linha}")
        if not itens:
            continue
        print(f"      CAMPOS ({len(itens[0])}): {list(itens[0])}")
        print(f"      primeiro: {json.dumps(itens[0], ensure_ascii=False)[:260]}")
        print(f"      ultimo:   {json.dumps(itens[-1], ensure_ascii=False)[:260]}")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--uf", default="SC")
    ap.add_argument("--estacoes", default=",".join(CANDIDATAS),
                    help="códigos separados por vírgula")
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

    sonda_inventario(sessao, token, args.uf)
    sonda_telemetria(sessao, token, [c.strip() for c in args.estacoes.split(",") if c.strip()])

    print(f"\n{'=' * 70}\nSonda terminada. Nada foi gravado em data/estacoes.json "
          "nem em data/enchentes.json.\n" + "=" * 70)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
