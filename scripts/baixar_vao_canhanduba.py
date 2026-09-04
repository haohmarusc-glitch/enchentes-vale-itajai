#!/usr/bin/env python3
"""
Acha o trecho que falta entre o Ribeirão Canhanduba e o Itajaí-Mirim.

O PROBLEMA
`conferir_afluentes_chegam.py` mede que o traçado do Canhanduba morre a 578 m
do Mirim, na várzea. O pedaço que falta não está em nenhum dos dois brutos já
baixados: as vias perto da ponta são todas "Rio Canhanduba" e já foram
convertidas. Ou seja, o último trecho tem OUTRO NOME no OSM, ou nenhum — e a
consulta por nome não o alcança.

Afluente cortado é pior que afluente ausente: o mapa AFIRMA que a água pára ali.

O QUE ESTE SCRIPT FAZ
Pede ao Overpass TODO curso d'água numa caixa em volta da ponta, sem filtrar
por nome — é justamente o nome que falta. Depois encadeia por CONECTIVIDADE:
partindo da ponta do Canhanduba, segue vias cujas extremidades se tocam, até
chegar ao Mirim. Reporta a cadeia encontrada e, com `--gravar`, salva as vias
num bruto próprio para o `converter_tracado_rios.py`.

O QUE ELE NÃO FAZ
Não desenha nada. Se o Overpass não devolver um caminho que feche o vão, ele
diz isso e sai — uma reta de 578 m entre a ponta e o rio seria geografia
inventada num mapa de enchente.

POR QUE UM SCRIPT E NÃO UM `curl`
A tentativa por linha de comando falhou com "Expecting value: line 1 column 1":
o Overpass devolveu algo que não é JSON (página de erro, limite de uso) e o
`curl` gravou isso no arquivo em silêncio. Aqui a resposta é conferida antes de
ser interpretada, e o que veio aparece na tela.

Uso:
    python3 scripts/baixar_vao_canhanduba.py
    python3 scripts/baixar_vao_canhanduba.py --gravar
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "scripts"))

from comum import USER_AGENT  # noqa: E402

RIOS = RAIZ / "data" / "rios"
SAIDA = RAIZ / "data" / "brutos" / "vao-canhanduba-osm.json"
API = "https://overpass-api.de/api/interpreter"

K_LON = math.cos(math.radians(27))

#: Caixa em volta da ponta de jusante do Canhanduba (sul, oeste, norte, leste).
CAIXA = (-26.945, -48.700, -26.930, -48.688)

#: Duas pontas a menos disto contam como o MESMO ponto (o OSM nem sempre
#: compartilha o nó; 30 m é folga de digitalização, não de geografia).
TOCA_M = 30.0

#: Chegou no rio quando encosta a menos disto — mesmo limite do
#: `conferir_afluentes_chegam.py`.
CHEGOU_M = 100.0

CONSULTA = """
[out:json][timeout:90];
(
  way["waterway"]({sul},{oeste},{norte},{leste});
);
out geom;
"""


def km(a, b):
    return math.hypot((a[0] - b[0]) * K_LON, a[1] - b[1]) * 111.32


def m(a, b):
    return km(a, b) * 1000.0


def vias_do_geojson(rio_id: str) -> list[list[tuple[float, float]]]:
    caminho = RIOS / f"{rio_id}.geojson"
    if not caminho.exists():
        return []
    d = json.loads(caminho.read_text(encoding="utf-8"))
    return [[(c[0], c[1]) for c in l] for l in d["geometry"]["coordinates"]]


def ponta_do_canhanduba() -> tuple[float, float]:
    """A extremidade do Canhanduba mais próxima do Mirim — de onde o vão parte."""
    canh = vias_do_geojson("ribeirao-canhanduba")
    mirim = [p for l in vias_do_geojson("itajai-mirim") for p in l]
    if not canh or not mirim:
        raise SystemExit("faltam data/rios/ribeirao-canhanduba.geojson ou itajai-mirim.geojson")
    return min((p for l in canh for p in (l[0], l[-1])),
               key=lambda p: min(km(p, q) for q in mirim))


def buscar(caixa) -> list[dict]:
    """A resposta do Overpass, CONFERIDA antes de ser interpretada."""
    import requests

    consulta = CONSULTA.format(sul=caixa[0], oeste=caixa[1], norte=caixa[2], leste=caixa[3])
    r = requests.post(API, data={"data": consulta},
                      headers={"User-Agent": USER_AGENT}, timeout=120)
    if r.status_code != 200:
        raise SystemExit(
            f"Overpass respondeu {r.status_code}. Começo do que veio:\n"
            f"{r.text[:400]}\n\n"
            "429/504 é limite de uso ou fila: espere alguns minutos e repita."
        )
    try:
        d = r.json()
    except ValueError:
        raise SystemExit(
            "Overpass respondeu 200 mas o corpo NÃO é JSON — é o que fez o "
            "`curl` gravar lixo no arquivo. Começo do que veio:\n"
            f"{r.text[:400]}"
        )
    return d.get("elements") or []


def pontas(via: dict) -> tuple[tuple[float, float], tuple[float, float]]:
    g = via["geometry"]
    return (g[0]["lon"], g[0]["lat"]), (g[-1]["lon"], g[-1]["lat"])


def encadear(elementos: list[dict], origem, alvo_pts) -> list[dict]:
    """
    Caminho por CONECTIVIDADE, da ponta do Canhanduba até tocar o Mirim.

    Busca em largura sobre as vias: duas se ligam quando uma extremidade de uma
    está a menos de `TOCA_M` de uma extremidade da outra. Devolve a menor cadeia
    que chega — ou lista vazia, e aí NÃO se inventa o vão.
    """
    vias = [e for e in elementos if e.get("type") == "way" and len(e.get("geometry") or []) >= 2]
    fila: list[tuple[tuple[float, float], list[dict]]] = [(origem, [])]
    vistas: set[int] = set()
    while fila:
        ponto, rota = fila.pop(0)
        for v in vias:
            if v["id"] in vistas:
                continue
            a, b = pontas(v)
            if m(ponto, a) <= TOCA_M:
                prox = b
            elif m(ponto, b) <= TOCA_M:
                prox = a
            else:
                continue
            vistas.add(v["id"])
            nova = rota + [v]
            if min(m(prox, q) for q in alvo_pts) <= CHEGOU_M:
                return nova
            fila.append((prox, nova))
    return []


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--gravar", action="store_true",
                    help=f"salva as vias da cadeia em {SAIDA.name}")
    args = ap.parse_args()

    origem = ponta_do_canhanduba()
    mirim = [p for l in vias_do_geojson("itajai-mirim") for p in l]
    print(f"ponta do Canhanduba: {origem[0]:.7f}, {origem[1]:.7f}")
    print(f"distância até o Mirim hoje: {min(m(origem, q) for q in mirim):.0f} m\n")

    els = buscar(CAIXA)
    print(f"Overpass devolveu {len(els)} elemento(s) na caixa.")
    from collections import Counter
    nomes = Counter((e.get("tags") or {}).get("name") or "(SEM NOME)" for e in els)
    tipos = Counter((e.get("tags") or {}).get("waterway") for e in els)
    for nome, n in nomes.most_common(15):
        print(f"   {n:3}x  {nome}")
    print(f"   tipos: {dict(tipos)}\n")

    cadeia = encadear(els, origem, mirim)
    if not cadeia:
        print("NENHUMA cadeia liga a ponta ao Mirim dentro da caixa.")
        print("Ou o vão é maior que a caixa, ou o OSM não mapeia esse trecho.")
        print("NÃO desenhe a reta: o mapa passaria a afirmar geografia inventada.")
        return 1

    total = sum(m(*pontas(v)) for v in cadeia)
    print(f"cadeia encontrada: {len(cadeia)} via(s), ~{total:.0f} m")
    for v in cadeia:
        t = v.get("tags") or {}
        print(f"   id={v['id']:12}  {str(t.get('waterway')):8}  "
              f"{t.get('name') or '(SEM NOME)'}  {len(v['geometry'])} pts")

    if args.gravar:
        SAIDA.parent.mkdir(parents=True, exist_ok=True)
        SAIDA.write_text(json.dumps({"elements": cadeia}, ensure_ascii=False), encoding="utf-8")
        print(f"\ngravado em {SAIDA.relative_to(RAIZ)} — agora rode "
              "converter_tracado_rios.py e conferir_afluentes_chegam.py")
    else:
        print("\n(nada gravado; repita com --gravar)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
