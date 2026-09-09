#!/usr/bin/env python3
"""Lê os brutos da série telemétrica da ANA e acha a crista sem inventar pico.

POR QUE EXISTE (09/09/2026)
A sonda (`sonda_ana_api.py --gravar`) deixa um JSON por (estação, janela) em
`data/brutos/ana-telemetria-<código>-<data>-<intervalo>.json`. A janela de
DIAS_7 termina na data pedida, e a cheia de novembro de 2023 em Taió cruzou a
fronteira entre duas janelas: 10,32 m às 21:00 de 17/11 na primeira, 10,31 m
às 00:00 de 18/11 na segunda. Ler uma janela só diria "pico 10,32 m" com o rio
ainda subindo. Este script JUNTA as janelas de cada estação e só então procura
a crista — e diz se ela está na borda do que se tem, caso em que é piso.

⚠️ O QUE ELE NÃO FAZ: não escreve em enchentes.json nem em estacoes.json. A
crista de uma estação da ANA é a crista DAQUELA RÉGUA; se ela é a régua da
cidade é outra conferência (`codigo_ana`, `codigo_ana_nao_e`).

⚠️ `Cota_Adotada` vem em CENTÍMETROS, como string, ou `null`. Null é leitura
ausente, não zero — e a Barragem Taió Montante ficou muda de 17/11 02:15 até o
fim de novembro de 2023, bem no meio da cheia.

Uso:
    python3 scripts/analisar_telemetria_ana.py data/brutos/ana-telemetria-83050000-*.json
    python3 scripts/analisar_telemetria_ana.py data/brutos/ana-telemetria-*.json --curva
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timedelta
from pathlib import Path

#: Leituras a esta distância do máximo contam como o mesmo platô de crista.
TOLERANCIA_PLATO_M = 0.02

#: Buraco (leituras ausentes) que vale a pena listar.
BURACO_MINIMO = timedelta(hours=1)

PASSO = timedelta(minutes=15)


def cota_m(item: dict) -> float | None:
    bruto = item.get("Cota_Adotada")
    if bruto in (None, ""):
        return None
    try:
        return round(float(bruto) / 100, 2)
    except (TypeError, ValueError):
        return None


def quando(item: dict) -> datetime | None:
    texto = item.get("Data_Hora_Medicao")
    if not texto:
        return None
    try:
        return datetime.strptime(texto[:19], "%Y-%m-%d %H:%M:%S")
    except ValueError:
        return None


def serie_do_bruto(corpo: dict) -> dict[str, list[tuple[datetime, float | None]]]:
    """{código: [(hora, metros|None), …]} de UM bruto da sonda."""
    por_estacao: dict[str, list] = {}
    for item in corpo.get("items") or []:
        t = quando(item)
        if t is None:
            continue
        codigo = str(item.get("codigoestacao") or "?")
        por_estacao.setdefault(codigo, []).append((t, cota_m(item)))
    return por_estacao


def juntar(series: list[list[tuple[datetime, float | None]]]) -> tuple[list, int]:
    """Une janelas da MESMA estação: ordena, tira carimbo repetido.

    Carimbo repetido com valores diferentes conta em `conflitos` e fica com o
    primeiro que apareceu — divergência entre janelas é coisa a olhar, não a
    esconder.
    """
    vistos: dict[datetime, float | None] = {}
    conflitos = 0
    for serie in series:
        for t, c in serie:
            if t in vistos:
                if vistos[t] != c and c is not None and vistos[t] is not None:
                    conflitos += 1
                if vistos[t] is None:
                    vistos[t] = c
            else:
                vistos[t] = c
    return sorted(vistos.items()), conflitos


def crista(serie: list[tuple[datetime, float | None]],
           tolerancia: float = TOLERANCIA_PLATO_M) -> dict | None:
    """Máximo, platô em torno dele e se ele está na borda do que se tem."""
    com_valor = [(t, c) for t, c in serie if c is not None]
    if not com_valor:
        return None
    maximo = max(c for _, c in com_valor)
    idx = next(i for i, (_, c) in enumerate(com_valor) if c == maximo)
    ini = idx
    while ini > 0 and com_valor[ini - 1][1] >= maximo - tolerancia:
        ini -= 1
    fim = idx
    while fim + 1 < len(com_valor) and com_valor[fim + 1][1] >= maximo - tolerancia:
        fim += 1
    return {
        "maximo_m": maximo,
        "quando": com_valor[idx][0],
        "plato_inicio": com_valor[ini][0],
        "plato_fim": com_valor[fim][0],
        "plato_leituras": fim - ini + 1,
        "na_borda": idx == 0 or idx == len(com_valor) - 1,
        "primeira": com_valor[0],
        "ultima": com_valor[-1],
        "n_cota": len(com_valor),
    }


def buracos(serie: list[tuple[datetime, float | None]],
            minimo: timedelta = BURACO_MINIMO) -> list[tuple[datetime, datetime]]:
    """Trechos sem cota (null OU carimbo faltando) com duração >= `minimo`."""
    achados = []
    inicio = None
    anterior = None
    for t, c in serie:
        if anterior is not None and t - anterior > PASSO and inicio is None:
            inicio = anterior + PASSO
        if c is None:
            if inicio is None:
                inicio = t
        else:
            if inicio is not None and t - inicio >= minimo:
                achados.append((inicio, t - PASSO))
            inicio = None
        anterior = t
    if inicio is not None and serie and serie[-1][0] - inicio + PASSO >= minimo:
        achados.append((inicio, serie[-1][0]))
    return achados


def curva_horaria(serie, centro: datetime, horas: int = 12) -> list[tuple[datetime, float | None]]:
    ini, fim = centro - timedelta(hours=horas), centro + timedelta(hours=horas)
    return [(t, c) for t, c in serie if ini <= t <= fim and t.minute == 0]


def _f(t: datetime) -> str:
    return t.strftime("%d/%m/%Y %H:%M")


def relatorio(por_estacao: dict[str, tuple[list, int]], curva: bool) -> None:
    for codigo, (serie, conflitos) in sorted(por_estacao.items()):
        print(f"\n{'=' * 70}\n{codigo}\n{'=' * 70}")
        if not serie:
            print("   sem linhas")
            continue
        print(f"   cobertura: {_f(serie[0][0])} → {_f(serie[-1][0])}, {len(serie)} carimbos")
        if conflitos:
            print(f"   ⚠️ {conflitos} carimbo(s) com valor DIFERENTE entre janelas — olhar antes de citar")
        c = crista(serie)
        if c is None:
            print("   0 linhas com cota. Ausente não é zero: a estação pode ter ficado muda.")
            continue
        print(f"   com cota: {c['n_cota']} de {len(serie)}")
        print(f"   primeira: {c['primeira'][1]:.2f} m em {_f(c['primeira'][0])}")
        print(f"   última:   {c['ultima'][1]:.2f} m em {_f(c['ultima'][0])}")
        print(f"   CRISTA:   {c['maximo_m']:.2f} m em {_f(c['quando'])}"
              f" — platô (±{TOLERANCIA_PLATO_M:.2f} m) de {_f(c['plato_inicio'])} a "
              f"{_f(c['plato_fim'])}, {c['plato_leituras']} leitura(s)")
        if c["na_borda"]:
            print("   ⚠️ A CRISTA ESTÁ NA BORDA do que se tem: é PISO, não pico. Falta a janela "
                  "vizinha (--data uma semana antes ou depois, na sonda).")
        for ini, fim in buracos(serie):
            dur = fim - ini + PASSO
            print(f"   buraco: {_f(ini)} → {_f(fim)} ({dur.total_seconds() / 3600:.1f} h sem cota)")
        if curva:
            print("   curva horária em torno da crista:")
            for t, v in curva_horaria(serie, c["quando"]):
                print(f"      {_f(t)}  {'—' if v is None else f'{v:.2f} m'}")


def carregar(caminhos: list[Path]) -> dict[str, tuple[list, int]]:
    por_estacao: dict[str, list[list]] = {}
    for caminho in caminhos:
        corpo = json.loads(caminho.read_text(encoding="utf-8"))
        for codigo, serie in serie_do_bruto(corpo).items():
            por_estacao.setdefault(codigo, []).append(serie)
    return {codigo: juntar(series) for codigo, series in por_estacao.items()}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("brutos", nargs="+", type=Path,
                    help="data/brutos/ana-telemetria-*.json (várias janelas da mesma estação são unidas)")
    ap.add_argument("--curva", action="store_true", help="imprime a curva horária ±12 h da crista")
    args = ap.parse_args()
    faltando = [p for p in args.brutos if not p.exists()]
    if faltando:
        print("não existe: " + ", ".join(map(str, faltando)), file=sys.stderr)
        return 2
    relatorio(carregar(args.brutos), args.curva)
    print("\nNada foi gravado. Crista de estação da ANA é crista DAQUELA régua.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
