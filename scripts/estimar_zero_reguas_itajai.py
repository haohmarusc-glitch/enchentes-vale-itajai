#!/usr/bin/env python3
"""Estima onde fica o zero de cada régua de Itajaí em relação ao mar, e cruza com o terreno.

Uso:
    python3 scripts/estimar_zero_reguas_itajai.py <pasta com os .ndjson de data/tempo-real>

Somente leitura. É uma ESTIMATIVA HIDRÁULICA, não a altitude oficial do zero.
Nada daqui entra em data/; o número oficial vem de levantamento (RN do IBGE)
publicado pela Defesa Civil ou pela prefeitura. Método e limites em
docs/ANALISE-CHEGADA-ITAJAI-2026.md, seção "Altitude do zero".

Como se estima
--------------
Nas réguas que sentem a maré (correlação ≥ 0,8 em analisar_chegada_itajai.py),
com o rio baixo (Blumenau < 3,5 m), a leitura é regredida na maré da tábua
(com o atraso da régua) e no nível de Blumenau:

    régua = c0 + c1 · maré_NR + c2 · Blumenau

A leitura com a maré no NÍVEL MÉDIO (0,60 m sobre o NR, cabeçalho da tábua da
Marinha) e Blumenau em 2,5 m (rio baixo) é a leitura de quando a água ali está
no nível médio do mar MAIS o empilhamento do rio. Esse empilhamento é ≥ 0 e
cresce rio acima, então "cota − leitura" é um LIMITE INFERIOR da altura da cota
sobre o nível médio do mar: perto da foz é quase exato; na DC-11, não.

Terreno: os pontos cotados do ArcGIS de Itajaí
(data/brutos/itajai-pontos-cotados-altimetricos.geojson.json). O datum vertical
deles não está declarado (docs/ITAJAI-ARCGIS-INVENTARIO.md). Pontos de ~0,6 m
junto ao rio parecem ser a lâmina d'água no dia do levantamento.
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from datetime import datetime
from pathlib import Path

from analisar_chegada_itajai import ajuste_mare, atrasar, curva_mare, horas, ler, serie
from comum import DADOS

NIVEL_MEDIO_NR_M = 0.60  # "Nível Médio" do cabeçalho da tábua 2026 do porto de Itajaí (CHM/DHN)
BLUMENAU_RIO_BAIXO_M = 2.5
BLUMENAU_MAX_M = 3.5
CORRELACAO_MIN = 0.8
RAIO_M = 300
PONTOS_COTADOS = DADOS / "brutos" / "itajai-pontos-cotados-altimetricos.geojson.json"


def minimos_quadrados(linhas: list[list[float]], y: list[float]) -> list[float]:
    """Resolve as equações normais por eliminação de Gauss (sem numpy)."""
    n = len(linhas[0])
    a = [[sum(r[i] * r[j] for r in linhas) for j in range(n)] + [sum(r[i] * v for r, v in zip(linhas, y))]
         for i in range(n)]
    for i in range(n):
        p = max(range(i, n), key=lambda k: abs(a[k][i]))
        a[i], a[p] = a[p], a[i]
        for k in range(i + 1, n):
            f = a[k][i] / a[i][i]
            a[k] = [x - f * z for x, z in zip(a[k], a[i])]
    c = [0.0] * n
    for i in reversed(range(n)):
        c[i] = (a[i][n] - sum(a[i][j] * c[j] for j in range(i + 1, n))) / a[i][i]
    return c


def leitura_no_nivel_medio(regua, mare, blu, atraso_h: int) -> dict | None:
    m = atrasar(mare, atraso_h)
    trios = [(t, b, r) for r, t, b in zip(regua, m, blu)
             if r is not None and t is not None and b is not None and b < BLUMENAU_MAX_M]
    if len(trios) < 100:
        return None
    c0, c1, c2 = minimos_quadrados([[1.0, t, b] for t, b, _ in trios], [r for _, _, r in trios])
    return {"horas": len(trios), "c": (c0, c1, c2),
            "leitura_m": c0 + c1 * NIVEL_MEDIO_NR_M + c2 * BLUMENAU_RIO_BAIXO_M}


def distancia_m(lat1, lon1, lat2, lon2) -> float:
    return math.hypot((lon2 - lon1) * 111_320 * math.cos(math.radians(lat1)), (lat2 - lat1) * 110_540)


def terreno_perto(pontos, lat, lon, raio=RAIO_M) -> dict | None:
    v = sorted(c for la, lo, c in pontos if distancia_m(lat, lon, la, lo) <= raio)
    if not v:
        return None
    return {"n": len(v), "min": v[0], "p25": v[len(v) // 4], "mediana": v[len(v) // 2]}


def reguas_de_itajai(estacoes: dict) -> dict:
    out = {}

    def andar(o):
        if isinstance(o, dict):
            if str(o.get("codigo", "")).startswith("DC-") and isinstance(o.get("lat"), (int, float)):
                out[o["codigo"]] = o
            for v in o.values():
                andar(v)
        elif isinstance(o, list):
            for v in o:
                andar(v)

    andar(estacoes)
    return out


def analisar(pasta: Path, mare_json: Path, estacoes_json: Path, pontos_json: Path) -> list[dict]:
    niveis, _ = ler(pasta)
    todos = [t for d in niveis.values() for t in d]
    eixo = horas(min(todos), max(todos))
    m = json.loads(mare_json.read_text(encoding="utf-8"))
    altura = curva_mare([(datetime.fromisoformat(e["quando"][:19]), e["altura_m"])
                         for e in m["preamares"] + m["baixamares"] if e.get("altura_m") is not None])
    mare = [altura(h) for h in eixo]
    blu = [a if a is not None else b for a, b in
           zip(serie(niveis["blumenau"], eixo), serie(niveis["blumenau-portal"], eixo))]
    g = json.loads(pontos_json.read_text(encoding="utf-8"))
    pontos = [(f["geometry"]["coordinates"][1], f["geometry"]["coordinates"][0], f["properties"]["cota"])
              for c in g["camadas"] for f in c["feicoes"] if f.get("geometry") and f["properties"].get("cota") is not None]
    cad = reguas_de_itajai(json.loads(estacoes_json.read_text(encoding="utf-8")))

    out = []
    for codigo in sorted(cad):
        r = cad[codigo]
        linha = {"codigo": codigo, "titulo": r.get("titulo", codigo), "cotas": r.get("cotas_m") or {},
                 "terreno": terreno_perto(pontos, r["lat"], r["lon"])}
        s = serie(niveis.get(codigo, {}), eixo)
        aj = ajuste_mare(s, mare) if any(v is not None for v in s) else None
        linha["mare"] = aj
        if aj and aj["r"] >= CORRELACAO_MIN:
            linha["nivel_medio"] = leitura_no_nivel_medio(s, mare, blu, aj["atraso_h"])
        out.append(linha)
    return out


def relatorio(linhas: list[dict]) -> str:
    out = ["Leitura com a água no nível médio do mar (rio baixo) e a cota de emergência acima do mar",
           "| régua | maré (r) | leitura no nível médio | emergência acima do mar (≥) | terreno ≤300 m: mín · p25 · mediana |",
           "|---|---|---|---|---|"]
    for x in linhas:
        t = x["terreno"]
        terreno = "sem pontos" if not t else f"{t['min']:.2f} · {t['p25']:.2f} · {t['mediana']:.2f} (n={t['n']})"
        r = "—" if not x["mare"] else f"{x['mare']['r']:.2f}"
        nm = x.get("nivel_medio")
        emerg = x["cotas"].get("emergencia")
        if nm:
            leit = f"{nm['leitura_m']:.2f} m"
            acima = f"{emerg - nm['leitura_m']:+.2f} m" if emerg is not None else "—"
        else:
            leit, acima = "não estimável (não sente a maré)", "—"
        out.append(f"| {x['codigo']} | {r} | {leit} | {acima} | {terreno} |")
    return "\n".join(out)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("pasta", type=Path)
    p.add_argument("--mare", type=Path, default=DADOS / "mare-itajai-chm.json")
    p.add_argument("--estacoes", type=Path, default=DADOS / "estacoes.json")
    p.add_argument("--pontos", type=Path, default=PONTOS_COTADOS)
    a = p.parse_args(argv)
    if not a.pasta.is_dir():
        print(f"pasta não encontrada: {a.pasta}", file=sys.stderr)
        return 2
    print(relatorio(analisar(a.pasta, a.mare, a.estacoes, a.pontos)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
