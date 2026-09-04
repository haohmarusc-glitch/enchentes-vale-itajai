#!/usr/bin/env python3
"""
Todo afluente desenhado CHEGA no rio que recebe? Sai 0 se sim, 1 se não.

POR QUE EXISTE (04/09/2026)
Relato de quem olhou o mapa: "o Ribeirão Canhanduba tem que ir até o
Itajaí-Mirim". Estava certo, e o número é 578 m: o traçado morre num ponto
qualquer da várzea, sem tocar o rio.

Afluente cortado é pior que afluente ausente. Ausente, quem olha sabe que não
sabe. Cortado, o mapa AFIRMA que a água pára ali — e quem mora entre a ponta do
traçado e o rio conclui que o ribeirão não chega perto de casa.

A causa é sempre a mesma: a consulta ao Overpass casa vias por NOME, e o último
trecho antes da foz costuma ter outro nome, ou nenhum. Não dá para consertar
inventando geometria: só rebaixando o pedaço que falta (ver
`docs/tracado-ribeiroes.md`).

O QUE ELE NÃO FAZ
Não decide em QUAL rio o afluente deságua — só mede a distância até cada tronco
desenhado e diz qual é o mais próximo. A confluência de verdade sai do
`achar_confluencias.py`, que usa geometria e o grafo do tronco.

Uso:
    python3 scripts/conferir_afluentes_chegam.py
    python3 scripts/conferir_afluentes_chegam.py --limite-m 150
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
RIOS = RAIZ / "data" / "rios"

#: Longitude encolhe com a latitude — mesma constante do resto do projeto.
K_LON = math.cos(math.radians(27))

#: Quem é tronco e quem é afluente. Tronco é o que recebe; afluente é o que
#: chega. Um afluente pode encostar em qualquer tronco: o script diz em qual.
TRONCOS = ("itajai-acu", "itajai-mirim", "mirim-canal-retificado")

#: Até onde a ponta pode ficar do tronco e ainda contar como "chega".
#:
#: 100 m é folga honesta: o OSM nem sempre compartilha o vértice da confluência,
#: e a várzea da foz muda de forma. Acima disso é buraco de traçado, não
#: imprecisão de cadastro — a ponta do Canhanduba estava a 578 m.
LIMITE_M = 100.0


def km_ao_segmento(p: tuple[float, float], a: tuple[float, float],
                   b: tuple[float, float]) -> float:
    """
    Distância do ponto ao SEGMENTO a–b, não aos vértices.

    A diferença não é detalhe: o OSM entrega vias com vértices espaçados, e
    medir até o vértice mais próximo diz "cortado" para uma ponta que cai
    exatamente em cima do rio, no meio de um trecho reto. Este mesmo erro já
    custou uma medição errada no `conferir_reguas_no_tracado.py`; aqui ele foi
    pego pelo próprio teste, que punha a ponta no meio de um segmento longo.
    """
    abx, aby = (b[0] - a[0]) * K_LON, b[1] - a[1]
    apx, apy = (p[0] - a[0]) * K_LON, p[1] - a[1]
    len2 = abx * abx + aby * aby
    t = 0.0 if len2 == 0 else max(0.0, min(1.0, (apx * abx + apy * aby) / len2))
    return math.hypot(apx - abx * t, apy - aby * t) * 111.32


def km_a_linhas(p: tuple[float, float],
                linhas: list[list[tuple[float, float]]]) -> float:
    melhor = float("inf")
    for linha in linhas:
        for a, b in zip(linha, linha[1:]):
            d = km_ao_segmento(p, a, b)
            if d < melhor:
                melhor = d
    return melhor


def vias(rio_id: str) -> list[list[tuple[float, float]]]:
    caminho = RIOS / f"{rio_id}.geojson"
    if not caminho.exists():
        return []
    dados = json.loads(caminho.read_text(encoding="utf-8"))
    return [[(c[0], c[1]) for c in linha]
            for linha in dados["geometry"]["coordinates"]]


def _mais_perto(ls: list[list[tuple[float, float]]],
                alvos: dict[str, list[list[tuple[float, float]]]]):
    """
    (distância em km, nome do alvo, ponta) do afluente até o alvo mais próximo.

    A PONTA é o que importa: um curso pode passar perto de outro no meio do
    trajeto e mesmo assim não desaguar nele.
    """
    pontas = [p for l in ls for p in (l[0], l[-1])]
    melhor = None
    for ponta in pontas:
        for nome, linhas in alvos.items():
            d = km_a_linhas(ponta, linhas)
            if melhor is None or d < melhor[0]:
                melhor = (d, nome, ponta)
    return melhor


def avaliar(limite_m: float = LIMITE_M) -> list[dict]:
    """
    Uma linha por afluente desenhado: onde ele encosta, e a que distância.

    Segue CADEIA. O Ribeirão Canhanduba não toca o Mirim: ele deságua no **Rio
    Conceição**, que deságua no Mirim — foi por isso que a busca por nome nunca
    o fechou, e é geografia, não defeito. Então um afluente conta como chegado
    quando alcança um tronco OU outro afluente que, por sua vez, alcança um
    tronco. O caminho inteiro sai no relatório, para ninguém confundir "chega
    pelo vizinho" com "chega direto".
    """
    troncos = {t: ls for t in TRONCOS if (ls := vias(t))}
    afluentes = {c.stem: vias(c.stem) for c in sorted(RIOS.glob("*.geojson"))
                 if c.stem not in TRONCOS and vias(c.stem)}

    #: Quem chega direto no tronco — a base da cadeia.
    direto: dict[str, tuple[float, str, tuple]] = {}
    for rio_id, ls in afluentes.items():
        m = _mais_perto(ls, troncos)
        if m:
            direto[rio_id] = m

    saida = []
    for rio_id, ls in afluentes.items():
        d, nome, ponta = direto[rio_id]
        via = []
        if d * 1000 > limite_m:
            # Não toca tronco: tenta pelos VIZINHOS que tocam.
            vizinhos = {n: afluentes[n] for n, (dv, _, _) in direto.items()
                        if n != rio_id and dv * 1000 <= limite_m}
            m = _mais_perto(ls, vizinhos) if vizinhos else None
            if m and m[0] * 1000 <= limite_m:
                d, intermediario, ponta = m
                via = [intermediario]
                nome = direto[intermediario][1]
        saida.append({
            "rio": rio_id,
            "chega_em": nome,
            "via": via,
            "metros": round(d * 1000, 1),
            "ponta": [round(ponta[0], 7), round(ponta[1], 7)],
            "cortado": d * 1000 > limite_m,
        })
    saida.sort(key=lambda r: -r["metros"])
    return saida


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--limite-m", type=float, default=LIMITE_M,
                    help=f"distância máxima para contar como 'chega' (padrão {LIMITE_M:.0f} m)")
    args = ap.parse_args()

    linhas = avaliar(args.limite_m)
    if not linhas:
        print("Nenhum afluente desenhado em data/rios/.", file=sys.stderr)
        return 1

    for r in linhas:
        marca = "   <<< CORTADO" if r["cortado"] else ""
        caminho = f" (via {' -> '.join(r['via'])})" if r["via"] else ""
        print(f"{r['rio']:24} chega em {r['chega_em']:20}{caminho} "
              f"a {r['metros']:7.0f} m{marca}")

    cortados = [r for r in linhas if r["cortado"]]
    print()
    if not cortados:
        print(f"os {len(linhas)} afluentes desenhados chegam no rio que os recebe "
              f"(a menos de {args.limite_m:.0f} m).")
        return 0

    print(f"{len(cortados)} afluente(s) que o mapa desenha SEM chegar no rio:")
    for r in cortados:
        print(f"  {r['rio']} — para a {r['metros']:.0f} m do {r['chega_em']}, "
              f"na ponta {r['ponta'][0]}, {r['ponta'][1]}")
    print("\nAfluente cortado AFIRMA que a água pára ali. Rebaixe o trecho que falta "
          "pelo Overpass (docs/tracado-ribeiroes.md) — nunca desenhe o vão à mão.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
