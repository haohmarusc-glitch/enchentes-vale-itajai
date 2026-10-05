#!/usr/bin/env python3
"""
Lista (e guarda) todos os cursos d'água com nome que passam por um município, pelo OpenStreetMap.

POR QUE EXISTE (05/10/2026). O Jefferson pediu os rios que passam por Ibirama na tela, como nas outras
cidades. Antes de desenhar, é preciso saber quais são — e isso se mede no mapa, não de memória. A consulta
pede ao Overpass todo `waterway` river/stream/canal COM NOME dentro do limite administrativo do município
(admin_level 8). Nada aqui decide o que vai para a tela: o script lista e guarda o bruto.

Uso (onde o Overpass responde: VPS ou o workflow `baixar-rios-municipio.yml`):
    python3 scripts/baixar_rios_municipio.py --municipio Ibirama
    python3 scripts/baixar_rios_municipio.py --municipio Ibirama --gravar
"""
from __future__ import annotations

import argparse
import json
import math
import sys
import unicodedata
from datetime import datetime, timezone
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "scripts"))

from baixar_tracado_hercilio import buscar_consulta  # noqa: E402

CONSULTA = """[out:json][timeout:180];
area["boundary"="administrative"]["admin_level"="8"]["name"="{municipio}"]->.a;
way["waterway"~"^(river|stream|canal)$"]["name"](area.a);
out geom;"""

K_LON = math.cos(math.radians(27))


def km(a, b) -> float:
    return math.hypot((a[0] - b[0]) * K_LON, a[1] - b[1]) * 111.32


def slug(texto: str) -> str:
    t = "".join(c for c in unicodedata.normalize("NFD", texto) if unicodedata.category(c) != "Mn").lower()
    return "-".join("".join(c if c.isalnum() else " " for c in t).split())


def resumo(elementos: list[dict]) -> list[dict]:
    """Um item por nome: tipo, número de ways e km dentro da consulta, do mais longo ao mais curto."""
    por_nome: dict[str, dict] = {}
    for e in elementos:
        tags = e.get("tags") or {}
        nome = tags.get("name")
        if e.get("type") != "way" or not nome:
            continue
        pts = [(p["lon"], p["lat"]) for p in e.get("geometry") or [] if "lon" in p and "lat" in p]
        item = por_nome.setdefault(nome, {"nome": nome, "id": slug(nome), "tipos": set(), "ways": 0, "km": 0.0})
        item["tipos"].add(tags.get("waterway"))
        item["ways"] += 1
        item["km"] += sum(km(a, b) for a, b in zip(pts, pts[1:]))
    itens = sorted(por_nome.values(), key=lambda i: -i["km"])
    for i in itens:
        i["tipos"] = sorted(t for t in i["tipos"] if t)
        i["km"] = round(i["km"], 1)
    return itens


def main() -> int:
    ap = argparse.ArgumentParser(description="Cursos d'água com nome dentro de um município (OSM).")
    ap.add_argument("--municipio", default="Ibirama")
    ap.add_argument("--gravar", action="store_true")
    a = ap.parse_args()
    consulta = CONSULTA.format(municipio=a.municipio)
    resposta, espelho = buscar_consulta(consulta)
    itens = resumo(resposta.get("elements") or [])
    if not itens:
        print(f"nenhum curso d'água com nome em {a.municipio} — conferir o nome do município no OSM", file=sys.stderr)
        return 1
    print(f"{len(itens)} curso(s) com nome em {a.municipio}:")
    for i in itens:
        print(f"   {i['km']:6.1f} km  {i['ways']:3d} way(s)  {'/'.join(i['tipos']):14s} {i['nome']}")
    if a.gravar:
        saida = RAIZ / "data" / "brutos" / f"rios-{slug(a.municipio)}-osm.json"
        resposta["_consulta"] = {"overpass": consulta, "espelho": espelho,
                                 "baixado_em": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                                 "script": "scripts/baixar_rios_municipio.py", "resumo": itens}
        saida.write_text(json.dumps(resposta, ensure_ascii=False) + "\n", encoding="utf-8")
        print(f"gravado: {saida.relative_to(RAIZ)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
