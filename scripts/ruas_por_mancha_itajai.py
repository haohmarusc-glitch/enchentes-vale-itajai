#!/usr/bin/env python3
"""
Cruza as ruas de Itajaí com as manchas de cheia da Prefeitura (pedido do Jefferson, 05/10/2026).

Para cada rua da base de vias da Prefeitura (`data/vias/itajai.geojson`, GeoItajaí) e cada cheia
com mancha de Itajaí no catálogo (`data/manchas/index.json`), calcula:
  - quantos metros (e que % do traçado da rua na base) ficaram dentro da mancha;
  - nas cheias com mapa de lâmina d'água, quantos metros caíram em cada faixa de lâmina.

Grava `data/manchas/itajai/ruas-por-mancha.json`, que o chat lê para "a rua X alagou em 2011?".
É um arquivo DERIVADO: refeito do zero a cada execução, a partir dos dois arquivos de origem, sem
data nem hora dentro (rodar duas vezes dá o mesmo arquivo). Não mexe em `enchentes.json`.

Cuidados, que vão também no `_meta` e na resposta do chat:
  - a mancha é o mapa da área atingida feito pela Prefeitura, não medição em cada casa;
  - ruas com o mesmo nome na base entram juntas (a base não diz se são a mesma rua);
  - a base de vias pode não ter o traçado inteiro de toda rua.

Uso:  python3 scripts/ruas_por_mancha_itajai.py
Dependência: shapely (scripts/requirements-mapas.txt).
"""
from __future__ import annotations

import json
import math
from pathlib import Path

from shapely.geometry import shape
from shapely.ops import transform, unary_union
from shapely.strtree import STRtree

RAIZ = Path(__file__).resolve().parent.parent
DADOS = RAIZ / "data"
VIAS = DADOS / "vias" / "itajai.geojson"
INDICE = DADOS / "manchas" / "index.json"
SAIDA = DADOS / "manchas" / "itajai" / "ruas-por-mancha.json"

MESES = ["janeiro", "fevereiro", "março", "abril", "maio", "junho", "julho", "agosto", "setembro", "outubro", "novembro", "dezembro"]
# Latitude de referência para a projeção local (centro de Itajaí); erro de escala < 0,5% na cidade.
LAT0 = -26.91


def metros(x: float, y: float, z: float | None = None) -> tuple[float, float]:
    """Graus → metros numa projeção local equirretangular (basta para comprimentos de rua)."""
    return (x * 111_320.0 * math.cos(math.radians(LAT0)), y * 110_574.0)


def rotulo(evento: str) -> str:
    partes = evento.split("-")
    return f"{MESES[int(partes[1]) - 1]} de {partes[0]}" if len(partes) > 1 else partes[0]


def carregar_geo(caminho: Path):
    return json.loads(caminho.read_text(encoding="utf-8"))["features"]


def eventos_de_itajai() -> list[dict]:
    """Uma entrada por cheia: a mancha total (se houver) e o mapa de lâmina (se houver)."""
    indice = json.loads(INDICE.read_text(encoding="utf-8"))
    por_evento: dict[str, dict] = {}
    for m in indice["manchas"]:
        if m.get("cidade") != "itajai" or "vias-alagadas" in m["arquivo"]:
            continue
        e = por_evento.setdefault(m["evento"], {"evento": m["evento"], "rotulo": rotulo(m["evento"]), "total": None, "lamina": None, "classes": []})
        if m.get("tem_lamina"):
            e["lamina"] = m["arquivo"]
            e["classes"] = [c["rotulo"] for c in m.get("classes_lamina", [])]
        else:
            e["total"] = m["arquivo"]
        e.setdefault("fonte", m.get("fonte"))
    return sorted(por_evento.values(), key=lambda e: e["evento"])


def calcular() -> dict:
    """A tabela inteira, como vai para o arquivo (o teste compara com o arquivo salvo)."""
    ruas: dict[str, list] = {}
    for f in carregar_geo(VIAS):
        nome = (f.get("properties") or {}).get("nome")
        if nome and f.get("geometry"):
            ruas.setdefault(nome.strip(), []).append(shape(f["geometry"]))
    geom = {nome: transform(metros, unary_union(gs)) for nome, gs in ruas.items()}
    comprimento = {nome: g.length for nome, g in geom.items()}

    eventos = eventos_de_itajai()
    resultado: dict[str, dict] = {nome: {"m": round(comprimento[nome]), "ev": {}} for nome in sorted(geom)}
    nomes = list(geom)
    arvore = STRtree([geom[n] for n in nomes])

    for ev in eventos:
        principal = ev["total"] or ev["lamina"]
        area = transform(metros, unary_union([shape(x["geometry"]).buffer(0) for x in carregar_geo(DADOS / principal) if x.get("geometry")]))
        classes = []
        if ev["lamina"]:
            for x in carregar_geo(DADOS / ev["lamina"]):
                if x.get("geometry"):
                    classes.append(((x.get("properties") or {}).get("situa"), transform(metros, shape(x["geometry"]).buffer(0))))
        for i in arvore.query(area):
            nome = nomes[int(i)]
            dentro = geom[nome].intersection(area).length
            if dentro < 1:
                continue
            item: dict = {"m": round(dentro), "pct": round(100 * dentro / comprimento[nome]) if comprimento[nome] else 0}
            if classes:
                lam = {}
                for rot, poli in classes:
                    d = geom[nome].intersection(poli).length
                    if rot and d >= 1:
                        lam[rot] = lam.get(rot, 0) + round(d)
                if lam:
                    item["lamina"] = {k: lam[k] for k in ev["classes"] if k in lam} | {k: v for k, v in lam.items() if k not in ev["classes"]}
            resultado[nome]["ev"][ev["evento"]] = item

    return {
        "_meta": {
            "descricao": "Metros (e % do traçado na base de vias) de cada rua de Itajaí dentro de cada mancha de cheia da Prefeitura; faixas de lâmina d'água quando há mapa de lâmina.",
            "gerado_por": "scripts/ruas_por_mancha_itajai.py (arquivo derivado; refazer rodando o script)",
            "vias": "data/vias/itajai.geojson — GeoItajaí / Prefeitura de Itajaí",
            "manchas": "data/manchas/index.json (cidade itajai) — GeoItajaí / Prefeitura de Itajaí",
            "metodo": "Interseção de linhas (ruas) com polígonos (manchas), em projeção local métrica. Ruas com o mesmo nome na base entram juntas. Com mancha total e mapa de lâmina na mesma cheia, a % vem da mancha total e as faixas, do mapa de lâmina.",
            "cuidados": [
                "A mancha é o mapa da área atingida feito pela Prefeitura, não medição em cada casa.",
                "Lâmina d'água em faixas, não número exato.",
                "A base de vias pode não ter o traçado inteiro de toda rua; ruas com o mesmo nome entram juntas.",
                "Em setembro de 2011, a mancha total e o mapa de lâmina da Prefeitura não coincidem exatamente: a soma das faixas pode passar um pouco do trecho dentro da mancha.",
            ],
            "eventos": [{k: v for k, v in e.items() if v not in (None, [])} for e in eventos],
        },
        "ruas": {n: r for n, r in resultado.items()},
    }


def serializar(tabela: dict) -> str:
    return json.dumps(tabela, ensure_ascii=False, separators=(",", ":")) + "\n"


def main() -> None:
    tabela = calcular()
    SAIDA.write_text(serializar(tabela), encoding="utf-8")
    ruas = tabela["ruas"]
    com = sum(1 for r in ruas.values() if r["ev"])
    print(f"{len(ruas)} ruas, {com} em alguma mancha, {len(tabela['_meta']['eventos'])} cheias → {SAIDA.relative_to(RAIZ)} ({SAIDA.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    main()
