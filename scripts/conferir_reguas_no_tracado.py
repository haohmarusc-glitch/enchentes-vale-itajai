#!/usr/bin/env python3
"""
Cada régua cai em cima de algum rio desenhado? Sai 0 se sim, 1 se não.

POR QUE EXISTE (04/09/2026)
O mapa passou a mostrar as onze réguas da Defesa Civil de Itajaí como pontos.
Olhando a tela, três pareciam flutuar fora de qualquer rio — e "parecer" não
resolve: ou se mede, ou se discute aparência. Medido, o quadro era este:

    DC-03 SEMASA       2,32 km   (canal retificado do Mirim, não desenhado)
    DC-07 Portal I     2,25 km   (Ribeirão da Murta, não desenhado)
    DC-08 Rio do Meio  4,41 km   (Rio Canhanduba, não desenhado)
    DC-09 Bairro Murta 0,87 km   (Ribeirão da Murta, não desenhado)

As outras sete estavam a menos de 0,2 km. Ou seja: o traçado do TRONCO estava
certo — inclusive o meandro da Volta de Cima, onde a DC-11 cai a 0,12 km — e o
que faltava eram os cursos MENORES, que a consulta original do Overpass não
pediu porque só buscou `waterway=river`.

O QUE ESTE NÚMERO NÃO É
Distância de régua a traçado não mede erro de coordenada da régua. Uma régua
pode estar corretamente longe do talvegue: a de Blumenau fica ~3 km dele porque
a coordenada publicada é a da ESTAÇÃO, não a do ponto de medição. Por isso o
limite aqui é generoso e o script fala em "curso não desenhado", não em
"coordenada errada" — a conclusão contrária exigiria conferir a fonte, não o
mapa.

Uso:
    python3 scripts/conferir_reguas_no_tracado.py
    python3 scripts/conferir_reguas_no_tracado.py --limite 0.5
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
RIOS = RAIZ / "data" / "rios"
ESTACOES = RAIZ / "data" / "estacoes.json"

#: Acima disto, a régua provavelmente está num curso que o mapa não desenha.
#:
#: Generoso de propósito: 500 m cobre imprecisão de coordenada e a largura do
#: próprio traçado sem acusar régua boa. Quem passou disto em 04/09 estava a
#: 0,87 km ou mais — bem acima de qualquer folga.
LIMITE_KM = 0.5

#: Longitude encolhe com a latitude; a mesma escala que o site usa.
K_LON = math.cos(math.radians(27))


def linhas_do_geojson(caminho: Path) -> list[list[tuple[float, float]]]:
    """As POLILINHAS do arquivo, e não uma nuvem solta de vértices.

    A distinção importa: medir só até os vértices faria a resposta depender do
    espaçamento com que o OSM amostrou aquele trecho. Num traçado denso o erro é
    de metros; num trecho reto e longo, amostrado com dois pontos, uma régua no
    meio dele apareceria a quilômetros de distância — e o script acusaria um
    curso faltando que está ali, desenhado.
    """
    dados = json.loads(caminho.read_text(encoding="utf-8"))
    linhas: list[list[tuple[float, float]]] = []

    def anda(c) -> None:
        if not isinstance(c, list) or not c:
            return
        if isinstance(c[0], (int, float)):
            return  # posição solta: quem trata é o nível de cima
        if isinstance(c[0], list) and c[0] and isinstance(c[0][0], (int, float)):
            linhas.append([(p[0], p[1]) for p in c if len(p) >= 2])
            return
        for x in c:
            anda(x)

    for feat in dados.get("features") or [dados]:
        anda((feat.get("geometry") or {}).get("coordinates") or [])
    return [l for l in linhas if len(l) >= 2]


def km(a: tuple[float, float], b: tuple[float, float]) -> float:
    return math.hypot((a[0] - b[0]) * K_LON, a[1] - b[1]) * 111.32


def tracados() -> dict[str, list[list[tuple[float, float]]]]:
    return {f.stem: linhas_do_geojson(f) for f in sorted(RIOS.glob("*.geojson"))}


def km_ao_segmento(p: tuple[float, float], a: tuple[float, float],
                   b: tuple[float, float]) -> float:
    """Distância do ponto ao SEGMENTO a–b, em km (não à reta infinita)."""
    abx, aby = (b[0] - a[0]) * K_LON, b[1] - a[1]
    apx, apy = (p[0] - a[0]) * K_LON, p[1] - a[1]
    len2 = abx * abx + aby * aby
    t = 0.0 if len2 == 0 else max(0.0, min(1.0, (apx * abx + apy * aby) / len2))
    return math.hypot(apx - abx * t, apy - aby * t) * 111.32


def mais_proximo(
    ponto: tuple[float, float], tr: dict[str, list[list[tuple[float, float]]]]
) -> tuple[str, float]:
    """(rio mais próximo, distância em km à LINHA). ('', inf) sem traçado."""
    melhor, dist = "", math.inf
    for nome, linhas in tr.items():
        for linha in linhas:
            for i in range(len(linha) - 1):
                d = km_ao_segmento(ponto, linha[i], linha[i + 1])
                if d < dist:
                    dist, melhor = d, nome
    return melhor, dist


def avaliar(estacoes: list[dict], tr: dict[str, list[list[tuple[float, float]]]],
            limite: float = LIMITE_KM) -> list[dict]:
    """Uma linha por régua com coordenada, da mais longe para a mais perto."""
    saida = []
    for e in estacoes:
        if not isinstance(e.get("lat"), (int, float)):
            continue
        if not isinstance(e.get("lon"), (int, float)):
            continue
        if e.get("tipo") == "pluviometro":
            continue
        rio, d = mais_proximo((e["lon"], e["lat"]), tr)
        nome = (e.get("nome_no_plano") or e.get("titulo") or "")
        saida.append({
            "codigo": e.get("codigo") or "",
            "lugar": nome.rsplit(" - ", 1)[-1],
            "rio_cadastro": e.get("rio"),
            "rio_mais_proximo": rio,
            "km": d,
            "longe": d > limite,
        })
    saida.sort(key=lambda r: -r["km"])
    return saida


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--limite", type=float, default=LIMITE_KM,
                    help=f"km acima do qual acusa (padrão {LIMITE_KM})")
    args = ap.parse_args()

    tr = tracados()
    if not tr:
        print(f"ERRO: nenhum traçado em {RIOS}", file=sys.stderr)
        return 1
    est = json.loads(ESTACOES.read_text(encoding="utf-8")).get("estacoes_tempo_real") or []
    linhas = avaliar(est, tr, args.limite)

    print(f"traçados desenhados: {', '.join(sorted(tr))}\n")
    for r in linhas:
        marca = "  <<<" if r["longe"] else ""
        print(f"{r['codigo']:7} {r['lugar'][:30]:30} cadastro={str(r['rio_cadastro']):22}"
              f" mais perto={r['rio_mais_proximo']:24} {r['km']:6.2f} km{marca}")

    longe = [r for r in linhas if r["longe"]]
    print()
    if not longe:
        print(f"todas as {len(linhas)} réguas caem a menos de {args.limite:g} km de um "
              "curso desenhado.")
        return 0
    print(f"{len(longe)} de {len(linhas)} réguas a mais de {args.limite:g} km de qualquer "
          "curso desenhado:")
    for r in longe:
        # Duas causas diferentes, e confundi-las manda consertar a coisa errada:
        # o rio do cadastro pode nem estar desenhado (falta o traçado inteiro),
        # ou estar desenhado e mesmo assim longe — aí é um BRAÇO dele que falta,
        # como o canal retificado do Mirim, onde fica a DC-03.
        if r["rio_cadastro"] in tr:
            print(f"  {r['codigo']} ({r['lugar']}) — cadastrada em "
                  f"'{r['rio_cadastro']}', que É desenhado: falta um braço dele "
                  "(canal, curso antigo) por onde a régua fica")
        else:
            print(f"  {r['codigo']} ({r['lugar']}) — cadastrada em "
                  f"'{r['rio_cadastro']}', que o mapa não desenha")
    print("\nIsto é curso FALTANDO no mapa, não coordenada errada da régua. "
          "Ver docs/tracado-ribeiroes.md.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
