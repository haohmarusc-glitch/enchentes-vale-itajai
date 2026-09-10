#!/usr/bin/env python3
"""Baixa o histórico das estações da API pública da Asthon para CSV, e ACUMULA.

ORIGEM (09/09/2026, script do Jefferson; revisado em 10/09/2026 para as
convenções do repo). O que existe de fato na API: cerca de SEIS SEMANAS. Em
09/09/2026 o histórico das estações começava em 28/07/2026 (a Barragem Sul,
em 17/07). Não há acervo profundo — este script pega a janela disponível e,
rodado periodicamente, guarda o que a API descartaria. Arquivos existentes são
MESCLADOS por carimbo, nunca sobrescritos.

O QUE ELE NÃO FAZ: não vincula estação a cidade nem escreve em estacoes.json.
Das cidades sem cor no site, só Vidal Ramos está neste conjunto; Ilhota,
Indaial, Ibirama, Ascurra e Lontras não pertencem à lista de Rio do Sul.
E guarda o valor CRU, sem `nivel_plausivel`: é acervo, não tela — o filtro é
de quem for ler.

FUSO: a API entrega UTC. `medido_em` sai em hora de Brasília SEM fuso (regra
do CLAUDE.md), convertido por `coleta_asthon.de_utc_para_brasilia`; o carimbo
UTC original fica na coluna ao lado.

Destino padrão: `data/brutos/asthon-historico/<estacao>.csv`. Uma estação a
10 min por seis semanas dá ~6 mil linhas (~200 KB); 26 estações, ~5 MB por
rodada, crescendo devagar. Commitar da VPS de tempos em tempos.

Uso:
    python3 scripts/baixar_historico_asthon.py
    python3 scripts/baixar_historico_asthon.py --dias 90 --resolucao hourly
    python3 scripts/baixar_historico_asthon.py --estacoes f6360951-219f-4859-935f-b2e2d13962f1
"""

from __future__ import annotations

import argparse
import csv
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

from coleta_asthon import BASE, CITY_ID, de_utc_para_brasilia
from comum import DADOS, USER_AGENT, espera_turno

PADRAO_SAIDA = DADOS / "brutos" / "asthon-historico"
COLUNAS = ["medido_em", "medido_em_utc", "nivel_m", "datum"]


def limpar(nome: str) -> str:
    """Nome de arquivo seguro (também no Windows): 'Ponte Dom Tito Buss' -> 'ponte_dom_tito_buss'."""
    fora = '<>:"/\\|?*'
    saida = "".join("-" if c in fora else c for c in nome).strip()
    return "_".join(saida.split()).lower() or "estacao"


def para_local(iso_utc: str) -> str:
    """'2026-09-09T22:56:45.871Z' -> '2026-09-09 19:56:45' (Brasília, sem fuso).

    Ler UTC como local desloca a série em 3 h — num rio, vira tempo de
    trânsito errado. Carimbo que não se converte fica como veio, visível.
    """
    convertido = de_utc_para_brasilia(iso_utc)
    return convertido.replace("T", " ") if convertido else iso_utc


def historico(sessao, station_id: str, dias: int, resolucao: str) -> tuple[list, str]:
    fim = datetime.now(timezone.utc)
    ini = fim - timedelta(days=dias)
    espera_turno()
    r = sessao.get(
        f"{BASE}station-history",
        params={
            "station_id": station_id,
            "start": ini.strftime("%Y-%m-%dT%H:%M:%S.000Z"),
            "end": fim.strftime("%Y-%m-%dT%H:%M:%S.000Z"),
            "fields": "level",
            "resolution": resolucao,
        },
        timeout=60,
    )
    r.raise_for_status()
    corpo = r.json()
    return corpo.get("level") or [], corpo.get("level_datum", "?")


def mesclar(destino: Path, novas: list[dict], datum: str) -> int:
    """Junta com o que já existe no arquivo, por carimbo local; devolve o total gravado.

    Leitura nova para um carimbo já gravado SUBSTITUI a antiga (a API pode
    corrigir); `value` None é pulado, não vira 0.
    """
    linhas: dict[str, dict] = {}
    if destino.exists():
        with destino.open(encoding="utf-8", newline="") as f:
            for linha in csv.DictReader(f):
                linhas[linha["medido_em"]] = linha
    for p in novas:
        if p.get("value") is None or not p.get("timestamp"):
            continue
        local = para_local(p["timestamp"])
        linhas[local] = {"medido_em": local, "medido_em_utc": p["timestamp"],
                         "nivel_m": p["value"], "datum": datum}
    ordenadas = [linhas[k] for k in sorted(linhas)]
    destino.parent.mkdir(parents=True, exist_ok=True)
    with destino.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=COLUNAS)
        w.writeheader()
        w.writerows(ordenadas)
    return len(ordenadas)


def main() -> int:
    import requests

    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--saida", type=Path, default=PADRAO_SAIDA, help="pasta de destino")
    ap.add_argument("--dias", type=int, default=120, help="janela pedida (a API tem ~6 semanas)")
    ap.add_argument("--resolucao", choices=["raw", "hourly"], default="raw", help="raw = 10 em 10 min")
    ap.add_argument("--estacoes", default=None, help="station_ids separados por vírgula (padrão: todas)")
    args = ap.parse_args()

    sessao = requests.Session()
    sessao.headers["User-Agent"] = USER_AGENT
    espera_turno()
    try:
        estacoes = sessao.get(f"{BASE}stations/list", params={"city_id": CITY_ID}, timeout=60).json()
    except Exception as e:  # rede, HTTP, JSON inesperado
        print(f"Falha ao listar estações: {e}", file=sys.stderr)
        return 1
    if not isinstance(estacoes, list) or not estacoes:
        print("A API não devolveu estações.", file=sys.stderr)
        return 1
    if args.estacoes:
        so = {s.strip() for s in args.estacoes.split(",") if s.strip()}
        estacoes = [e for e in estacoes if e.get("station_id") in so]

    print(f"{len(estacoes)} estação(ões) | destino: {args.saida}\n")
    total, vazias = 0, []
    for e in estacoes:
        nome = e.get("name") or e.get("station_id", "?")
        try:
            pontos, datum = historico(sessao, e["station_id"], args.dias, args.resolucao)
        except Exception as erro:
            print(f"  {nome:<32} ERRO: {erro}", file=sys.stderr)
            continue
        if not pontos:
            vazias.append(nome)
            print(f"  {nome:<32} sem nível (pluviômetro, ou estação sem sensor)")
            continue
        n = mesclar(args.saida / f"{limpar(nome)}.csv", pontos, datum)
        total += len(pontos)
        print(f"  {nome:<32} {len(pontos):>5} novos | {n:>6} no arquivo | desde {pontos[0]['timestamp'][:10]} | datum {datum}")

    print(f"\n{total} pontos baixados nesta rodada.")
    if vazias:
        print(f"{len(vazias)} estação(ões) sem série de nível: {', '.join(vazias)}")
    print("Rode de novo periodicamente: as leituras antigas ficam mesmo depois que a API as descartar.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
