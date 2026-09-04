#!/usr/bin/env python3
"""
Quanto do rio desenhado está VIVO no mapa — e quem responde por cada km cinza.

POR QUE EXISTE (04/09/2026)
Relato recorrente de quem olha o mapa: "muitas áreas sem animação". Está certo,
e a resposta "falta dado" é verdadeira e inútil: não diz quanto, nem onde, nem
o que destrava.

Este script mede. Para cada rio, distribui o comprimento do traçado entre as
cidades do eixo (cada trecho pertence à cidade A MONTANTE, a mesma regra que o
mapa usa para a cor) e diz, por cidade, quantos quilômetros ela pinta e por que
não pinta quando é o caso:

  sem leitura            — tem cota cadastrada, a fonte não publica
  sem cota               — tem leitura ao vivo, falta o limiar
  sem leitura e sem cota — não há nem um nem outro

A diferença importa porque as três se destravam de formas diferentes: leitura é
ofício à Defesa Civil do município; cota é tabela do Plano de Contingência. E o
número em km diz qual pedido acende mais mapa.

CINZA NÃO É DEFEITO. É o site se recusando a afirmar o que não mediu. O que
este script mede é o TAMANHO dessa recusa, para priorizar quem procurar.

Uso:
    python3 scripts/conferir_cobertura.py --arquivo /tmp/ultimo.json
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
K_LON = math.cos(math.radians(27))
ORDEM = ["monitoramento", "atencao", "alerta", "inundacao", "emergencia"]

#: Mesma folga do mapa: a régua pode estar a até 5 km do traçado e ainda ser
#: desta cidade (a de Blumenau fica a 3,0 km, porque a coordenada é da ESTAÇÃO).
LIMITE_ANCORA_KM = 5.0


def km(a, b):
    return math.hypot((a[0] - b[0]) * K_LON, a[1] - b[1]) * 111.32


def dist2_seg(p, a, b):
    abx, aby = (b[0] - a[0]) * K_LON, b[1] - a[1]
    apx, apy = (p[0] - a[0]) * K_LON, p[1] - a[1]
    l2 = abx * abx + aby * aby
    t = 0.0 if l2 == 0 else max(0.0, min(1.0, (apx * abx + apy * aby) / l2))
    return (abx * t - apx) ** 2 + (aby * t - apy) ** 2


def avaliar(rio_id: str, estacoes: dict, leituras: list[dict]) -> dict | None:
    caminho = RAIZ / "data" / "rios" / f"{rio_id}.geojson"
    if not caminho.exists():
        return None
    linhas = [[(c[0], c[1]) for c in l]
              for l in json.loads(caminho.read_text(encoding="utf-8"))["geometry"]["coordinates"]]
    pontos = [p for l in linhas for p in l]

    rio = estacoes["rios"][rio_id]
    topo = rio.get("_topologia") or {}
    eixo = (topo.get("tronco_sequencia") or []) + (topo.get("cabeceiras_paralelas") or [])

    por_cidade: dict[str, list[dict]] = {}
    for l in leituras:
        if l.get("usar_para_cota") is False or l.get("rio") != rio_id:
            continue
        por_cidade.setdefault(l.get("cidade"), []).append(l)

    ancoras = []
    for c in rio["cidades"]:
        co = c.get("coordenadas")
        if not co:
            continue
        if eixo and c["id"] not in eixo:
            continue  # afluente lateral: não pinta o tronco (ver mapaMotor)
        alvo = (co[1], co[0])
        ponto = min(pontos, key=lambda q: km(alvo, q))
        if km(alvo, ponto) > LIMITE_ANCORA_KM:
            continue  # cabeceira cujo rio não foi desenhado
        ls = por_cidade.get(c["id"]) or []
        cotas = {k: v for k, v in (c.get("cotas_m") or {}).items() if k in ORDEM}
        pinta = bool(ls) and bool(cotas)
        if pinta:
            causa = ""
        elif cotas:
            causa = "sem leitura"
        elif ls:
            causa = "sem cota"
        else:
            causa = "sem leitura e sem cota"
        ancoras.append({"cidade": c["id"], "ponto": ponto, "pinta": pinta,
                        "causa": causa, "km": 0.0})

    espinha = [a["ponto"] for a in ancoras]
    total = 0.0
    for l in linhas:
        for a, b in zip(l, l[1:]):
            comp = km(a, b)
            total += comp
            if len(espinha) < 2:
                continue
            meio = ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)
            i = min(range(len(espinha) - 1),
                    key=lambda i: dist2_seg(meio, espinha[i], espinha[i + 1]))
            ancoras[i]["km"] += comp

    vivo = sum(a["km"] for a in ancoras if a["pinta"])
    return {"rio": rio_id, "km_total": total, "km_vivo": vivo, "ancoras": ancoras}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--arquivo", required=True, help="ultimo.json (publicado ou local)")
    args = ap.parse_args()

    caminho = Path(args.arquivo)
    if not caminho.exists():
        print(f"ERRO: {caminho} não existe", file=sys.stderr)
        return 1
    leituras = json.loads(caminho.read_text(encoding="utf-8")).get("leituras") or []
    estacoes = json.loads((RAIZ / "data" / "estacoes.json").read_text(encoding="utf-8"))

    faltas: dict[str, float] = {}
    for rio_id in estacoes["rios"]:
        r = avaliar(rio_id, estacoes, leituras)
        if not r:
            continue
        print(f"=== {r['rio']}: {r['km_total']:.0f} km desenhados")
        for a in r["ancoras"]:
            marca = "" if a["pinta"] else f"   <- {a['causa']}"
            print(f"   {a['cidade']:16} pinta {a['km']:6.1f} km{marca}")
            if not a["pinta"]:
                faltas[a["causa"]] = faltas.get(a["causa"], 0.0) + a["km"]
        pct = r["km_vivo"] / r["km_total"] if r["km_total"] else 0
        print(f"   ANIMADO: {r['km_vivo']:.0f} de {r['km_total']:.0f} km = {pct:.0%}\n")

    if faltas:
        print("km de rio cinza, por causa — é o que ordena os pedidos:")
        for causa, k in sorted(faltas.items(), key=lambda t: -t[1]):
            print(f"   {k:7.1f} km  {causa}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
