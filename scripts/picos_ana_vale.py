#!/usr/bin/env python3
"""
Picos das séries convencionais da ANA no Itajaí-Açu e afluentes (HidroWeb, TXT).

O QUE É A FONTE
---------------
Em 24/09/2026 o Jefferson exportou do HidroWeb, pelo navegador, as estações da
ANA das cidades sem pico no cadastro (lista em docs/PICOS-FALTANTES.md). Os zips
estão como vieram em `data/brutos/pesquisa-picos-2026-09-24/ana/`: 20 pacotes,
3 vazios (83145140, 83301000, 83664000). É o mesmo formato largo que
`hidroweb_csv.py` lê, com extensão `.txt`.

O QUE ESTE SCRIPT FAZ
---------------------
Para cada estação com cota, monta um valor por dia e acha os eventos:

* Dia com leitura das 07h/17h (bruto): a maior das duas, sem as duvidosas
  (status 3) e sem o dedo do digitador (`hidroweb_csv.implausiveis`).
* Dia sem leitura instantânea: a MÉDIA DIÁRIA, consistida quando houver. Várias
  estações só têm média por décadas (Ilhota 1927–1988, Timbó 1929–1999, Trombudo
  Central 1942–1967). Média diária fica ainda mais longe da crista que a leitura.
* Evento = corrida de dias acima do limiar da estação, separada por mais de 5
  dias; fica o maior dia da corrida. Limiar = o N-ésimo maior máximo anual, para
  cada estação dar os seus ~N maiores eventos sem limiar inventado à mão.

Tudo sai em cm, NO ZERO DA ANA. Leitura de 07h/17h é PISO da crista, nunca a
crista (docs/HIDROWEB-MIRIM-2026-09-22.md mostrou em Brusque: nas cheias grandes
a crista cai entre leituras). Média diária é piso mais baixo ainda.

O QUE NÃO FAZ
-------------
NÃO escreve em `enchentes.json`. A régua da ANA não é a régua da Defesa Civil de
nenhuma destas cidades até alguém provar o contrário, e em Taió a decisão (b) de
09/09/2026 já disse que as cristas da ANA não viram registro. O que entra no
cadastro é decisão do Jefferson, estação por estação — este script só põe a
lista na mesa, em `picos_ana_vale.json`, e compara com o cadastro onde há
evento dos dois lados, que é a única pista sobre o zero.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import date, timedelta
from pathlib import Path

from hidroweb_csv import HORAS, Leitura, implausiveis, ler_cotas

RAIZ = Path(__file__).resolve().parent.parent
DIR = RAIZ / "data" / "brutos" / "pesquisa-picos-2026-09-24"
SAIDA = DIR / "picos_ana_vale.json"

# Nome, rio e área do inventário público da ANA (data/brutos/ana-inventario-api-2026-09-08.json).
# `cidade` é o id em estacoes.json do município onde a estação fica — não quer dizer
# que seja a régua da Defesa Civil daquela cidade.
ESTACOES = {
    "83050000": {"nome": "TAIÓ", "rio": "Itajaí do Oeste", "cidade": "taio", "area_km2": 1570},
    "83070000": {"nome": "TROMBUDO CENTRAL", "rio": "Trombudo", "cidade": "trombudo-central", "area_km2": 561},
    "83250000": {"nome": "ITUPORANGA", "rio": "Itajaí do Sul", "cidade": "ituporanga", "area_km2": 1650},
    "83440000": {"nome": "IBIRAMA", "rio": "Itajaí do Norte (Hercílio)", "cidade": "ibirama", "area_km2": 3330},
    "83500000": {"nome": "APIÚNA - RÉGUA NOVA", "rio": "Itajaí-Açu", "cidade": "apiuna", "area_km2": 9070},
    "83680000": {"nome": "TIMBÓ", "rio": "Benedito", "cidade": "timbo", "area_km2": 1600},
    "83677000": {"nome": "TIMBÓ NOVO", "rio": "Benedito", "cidade": "timbo", "area_km2": 1600},
    "83860000": {"nome": "ILHOTA", "rio": "Itajaí-Açu", "cidade": "ilhota", "area_km2": 12700},
    "83859998": {"nome": "ILHOTA - MONTANTE", "rio": "Itajaí-Açu", "cidade": "ilhota", "area_km2": 12700},
    "83870000": {"nome": "ILHOTA-JUSANTE", "rio": "Itajaí-Açu", "cidade": "ilhota", "area_km2": 12357},
    "83920000": {"nome": "PORTO ITAJAÍ", "rio": "Itajaí-Açu", "cidade": "itajai", "area_km2": 15200},
}
SEPARACAO = timedelta(days=5)


def carregar(codigo: str, pasta: Path = DIR / "ana") -> list[Leitura]:
    zips = sorted(pasta.glob(f"Estacao_{codigo}_TXT_*.zip"))
    return ler_cotas(zips[0], "_Cotas.txt") if zips else []


def serie_diaria(leituras: list[Leitura]) -> dict[date, tuple[float, str]]:
    """`{dia: (cm, origem)}`, origem "07:00"/"17:00" (leitura, bruto) ou "media_consistida"/"media_bruta"."""
    ruins = {(date.fromisoformat(d), h) for _c, d, h, _v, _m in implausiveis(leituras)}
    inst: dict[date, tuple[float, str]] = {}
    med: dict[date, dict[int, float]] = {}
    for x in leituras:
        if x.valor is None or x.status == 3:
            continue
        if x.leitura in HORAS and x.nivel == 1 and (x.data, x.leitura) not in ruins:
            if x.data not in inst or x.valor > inst[x.data][0]:
                inst[x.data] = (x.valor, x.leitura)
        elif x.leitura == "media_diaria":
            med.setdefault(x.data, {})[x.nivel] = x.valor
    saida: dict[date, tuple[float, str]] = {}
    for d in set(inst) | set(med):
        if d in inst:
            saida[d] = inst[d]
        else:
            m = med[d]
            saida[d] = (m[2], "media_consistida") if 2 in m else (m[1], "media_bruta")
    return saida


def maximos_anuais(serie: dict[date, tuple[float, str]]) -> dict[int, float]:
    anos: dict[int, float] = {}
    for d, (v, _o) in serie.items():
        anos[d.year] = max(anos.get(d.year, 0.0), v)
    return anos


def eventos(serie: dict[date, tuple[float, str]], limiar: float) -> list[tuple[date, float, str]]:
    """Maior dia de cada corrida de dias ≥ limiar; corridas separadas por mais de 5 dias."""
    cand = sorted((d, v, o) for d, (v, o) in serie.items() if v >= limiar)
    grupos: list[list[tuple[date, float, str]]] = []
    for c in cand:
        if grupos and c[0] - grupos[-1][-1][0] <= SEPARACAO:
            grupos[-1].append(c)
        else:
            grupos.append([c])
    return [max(g, key=lambda c: (c[1], -c[0].toordinal())) for g in grupos]


def maiores(codigo: str, n: int = 15, pasta: Path = DIR / "ana") -> dict:
    leit = carregar(codigo, pasta)
    serie = serie_diaria(leit)
    if not serie:
        return {"codigo": codigo, **ESTACOES[codigo], "vazia": True, "eventos": []}
    anuais = sorted(maximos_anuais(serie).values(), reverse=True)
    limiar = anuais[min(n, len(anuais)) - 1]
    evs = sorted(eventos(serie, limiar), key=lambda e: -e[1])[:n]
    dias = sorted(serie)
    return {
        "codigo": codigo,
        **ESTACOES[codigo],
        "periodo": [dias[0].isoformat(), dias[-1].isoformat()],
        "dias_com_valor": len(serie),
        "dias_com_leitura_07h_17h": sum(1 for v in serie.values() if v[1] in HORAS),
        "limiar_cm": limiar,
        "eventos": [{"data": d.isoformat(), "cm": v, "origem": o} for d, v, o in evs],
    }


def comparar_com_cadastro(res: dict, enchentes: list[dict], janela: int = 3) -> list[dict]:
    """Pares (registro do cadastro da mesma cidade, maior valor da ANA no mesmo evento).

    Data completa: janela de ±`janela` dias. Só mês ou só ano: o mês/ano inteiro — par mais
    frouxo, marcado em `granularidade`. É a única pista sobre o zero: se a diferença fosse
    constante evento a evento, as réguas poderiam ser a mesma com deslocamento; se varia
    muito, não são — ou a leitura das 07h/17h perdeu a crista.
    """
    serie = serie_diaria(carregar(res["codigo"]))
    saida = []
    for r in enchentes:
        if r["cidade"] != res["cidade"] or "picos_ana_vale" in r["fonte"]:
            continue  # o que veio daqui não é pista sobre o zero: seria a ANA contra ela mesma
        if len(r["data"]) == 10:
            d0 = date.fromisoformat(r["data"])
            dias = [d0 + timedelta(days=k) for k in range(-janela, janela + 1)]
            gran = "dia"
        else:
            dias = [d for d in serie if d.isoformat().startswith(r["data"])]
            gran = "mes" if len(r["data"]) == 7 else "ano"
        perto = [(d, *serie[d]) for d in dias if d in serie]
        if not perto:
            continue
        d, v, o = max(perto, key=lambda x: x[1])
        saida.append({"cadastro_data": r["data"], "cadastro_m": r["pico_m"], "granularidade": gran,
                      "ana_data": d.isoformat(), "ana_m": round(v / 100, 2), "ana_origem": o,
                      "diferenca_m": round(r["pico_m"] - v / 100, 2)})
    return sorted(saida, key=lambda c: c["cadastro_data"])


def tudo(n: int = 15) -> dict:
    enchentes = json.loads((RAIZ / "data" / "enchentes.json").read_text(encoding="utf-8"))["eventos"]
    estacoes = []
    for cod in ESTACOES:
        r = maiores(cod, n)
        if r["eventos"]:
            r["comparacao_com_cadastro"] = comparar_com_cadastro(r, enchentes)
        estacoes.append(r)
    return {
        "gerado_por": "scripts/picos_ana_vale.py",
        "fonte": "ANA/HidroWeb, exportação TXT de 24/09/2026 — data/brutos/pesquisa-picos-2026-09-24/ana/",
        "unidade": "cm, no zero da ANA",
        "aviso": "Leitura 07h/17h e média diária são PISO da crista. Régua da ANA ≠ régua da Defesa Civil "
                 "até prova em contrário. Nada daqui está em enchentes.json.",
        "estacoes": estacoes,
    }


def _cli(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    p.add_argument("--n", type=int, default=15, help="eventos por estação (padrão 15)")
    p.add_argument("--gravar", action="store_true", help=f"grava {SAIDA.relative_to(RAIZ)}")
    a = p.parse_args(argv)
    res = tudo(a.n)
    for e in res["estacoes"]:
        if not e["eventos"]:
            print(f"{e['codigo']} {e['nome']}: sem cota")
            continue
        print(f"{e['codigo']} {e['nome']} ({e['rio']}) {e['periodo'][0]}–{e['periodo'][1]}, limiar {e['limiar_cm']:.0f} cm")
        for ev in e["eventos"]:
            print(f"   {ev['data']}  {ev['cm']:6.0f} cm  {ev['origem']}")
        for c in e.get("comparacao_com_cadastro", []):
            print(f"   cadastro {c['cadastro_data']} ({c['granularidade']}) {c['cadastro_m']} m × ANA {c['ana_data']} {c['ana_m']} m "
                  f"({c['ana_origem']}): {c['diferenca_m']:+.2f} m")
    if a.gravar:
        SAIDA.write_text(json.dumps(res, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print("gravado:", SAIDA.relative_to(RAIZ))
    return 0


if __name__ == "__main__":
    sys.exit(_cli())
