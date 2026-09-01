#!/usr/bin/env python3
"""
Converte o traçado dos rios (bruto do OpenStreetMap, via Overpass) em GeoJSON
para o mapa geográfico do site.

ENTRADA  data/brutos/tracado-rios-osm.json — resposta `out geom;` do Overpass,
         com os ways de `waterway=river` nomeados. Baixado na VPS (o egress do
         ambiente de dev não alcança o Overpass); a query está no próprio bruto
         pela procedência, e o comando fica em docs/.
SAÍDA    data/rios/itajai-acu.geojson e itajai-mirim.geojson — um MultiLineString
         por rio, em [lon, lat] (ordem GeoJSON), com atribuição ODbL.

POR QUE JUNTAR OESTE COM AÇU
----------------------------
No OSM, a calha principal do Açu troca de nome na confluência de Rio do Sul: a
montante dela chama-se "Rio Itajaí do Oeste" (a vinda de Taió). Para a linha do
mapa cobrir o diagrama inteiro (Taió → foz), o Açu do site é os dois juntos. O
Itajaí do Sul (de Ituporanga) é a OUTRA cabeceira e fica de fora por enquanto:
o diagrama do Açu segue o eixo Taió → Rio do Sul.

Uso:
    python3 scripts/converter_tracado_rios.py
"""

import json
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
BRUTO = RAIZ / "data/brutos/tracado-rios-osm.json"
SAIDA = RAIZ / "data/rios"

ATRIBUICAO = "© OpenStreetMap contributors, ODbL (openstreetmap.org/copyright)"

#: Cada rio do site e os nomes de way do OSM que o compõem, de montante a jusante.
RIOS = {
    "itajai-acu": ["Rio Itajaí do Oeste", "Rio Itajaí-Açu"],
    "itajai-mirim": ["Rio Itajaí-Mirim"],
}


def ways_por_nome(elementos: list[dict]) -> dict[str, list[dict]]:
    por_nome: dict[str, list[dict]] = {}
    for e in elementos:
        if e.get("type") != "way" or "geometry" not in e:
            continue
        nome = (e.get("tags") or {}).get("name")
        if nome:
            por_nome.setdefault(nome, []).append(e)
    return por_nome


def linha_do_way(way: dict) -> list[list[float]]:
    """Geometria de um way em [lon, lat] (GeoJSON), como o OSM devolve em lat/lon."""
    return [[p["lon"], p["lat"]] for p in way["geometry"]
            if isinstance(p.get("lon"), (int, float)) and isinstance(p.get("lat"), (int, float))]


def geojson_do_rio(rio_id: str, nomes: list[str], por_nome: dict[str, list[dict]]) -> dict:
    linhas = []
    faltando = []
    for nome in nomes:
        ways = por_nome.get(nome) or []
        if not ways:
            faltando.append(nome)
        for w in ways:
            linha = linha_do_way(w)
            if len(linha) >= 2:
                linhas.append(linha)
    if faltando:
        # Nome esperado que não veio: o bruto mudou ou a query pegou coisa
        # diferente. Grita, não emite um rio pela metade em silêncio.
        raise SystemExit(f"{rio_id}: nomes ausentes no bruto: {faltando}")
    return {
        "type": "Feature",
        "properties": {
            "rio": rio_id,
            "fonte": ATRIBUICAO,
            "trechos": len(linhas),
        },
        "geometry": {"type": "MultiLineString", "coordinates": linhas},
    }


def main() -> int:
    if not BRUTO.exists():
        raise SystemExit(f"falta o bruto {BRUTO} — baixe na VPS (ver docs)")
    dados = json.loads(BRUTO.read_text(encoding="utf-8"))
    por_nome = ways_por_nome(dados.get("elements") or [])
    SAIDA.mkdir(parents=True, exist_ok=True)
    for rio_id, nomes in RIOS.items():
        feat = geojson_do_rio(rio_id, nomes, por_nome)
        destino = SAIDA / f"{rio_id}.geojson"
        destino.write_text(json.dumps(feat, ensure_ascii=False) + "\n", encoding="utf-8")
        pts = sum(len(l) for l in feat["geometry"]["coordinates"])
        print(f"{rio_id}: {feat['properties']['trechos']} trechos, {pts} pontos -> {destino.name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
