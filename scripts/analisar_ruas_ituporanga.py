#!/usr/bin/env python3
"""
O que os 60 pontos de cota de rua de Ituporanga dizem — e o que NÃO dizem.

Fonte: Google My Maps "Cotas de cheias ruas - Ituporanga" (Prefeitura, 07/10/2023),
congelado na VPS em 09/09/2026 e transcrito em
`data/brutos/ituporanga-mymaps-ruas-2026-09-09-transcricao.tsv`.

O que este script responde:

1. Quantos pontos há, e entre que cotas. Um ponto — "Prefeitura Garagem",
   27,77 m — está fora de qualquer nível de rio desta bacia: é digitação ou
   altitude na coluna errada. Sai da contagem e vai para a lista de recusas.
2. Quantos pontos ficam ACIMA do teto do mapa de manchas (6,50 m). O mapa de
   manchas vai de 3,00 a 6,50; as ruas vão até 10,48. Ou seja, o mapa de manchas
   não cobre a parte de cima do cadastro de ruas — quem procurar a própria rua
   acima de 6,50 m acha a cota e não acha a mancha.
3. Que cotas CERCAM os 3,25 m que o secretário de Planejamento chamou de
   "primeira cota crítica": a menor cota de rua é 3,38 m, a primeira mancha
   começa em 3,00 m. Os três se encaixam — e nenhum é faixa de acionamento.
4. Se os pontos estão todos no perímetro urbano (a menos de poucos km do
   centroide): protege contra um ponto de outra cidade no mesmo mapa.

O que este script NÃO faz: gravar nada em `cotas-ruas.json`. Estas cotas são
de uma régua que a fonte não nomeia (provavelmente a da Ponte Vitório Sens),
e a leitura ao vivo de Ituporanga é a DCSC-00039, em datum estadual bruto, com
`usar_para_cota: false`. Importar seria casar cota de uma régua com leitura de
outra — a regra nº 1 do projeto. Quando a Defesa Civil de Ituporanga disser a
régua e o zero, a importação é meia hora.

Uso:
    python3 scripts/analisar_ruas_ituporanga.py
"""

from __future__ import annotations

import math
import sys
from pathlib import Path

from comum import DADOS, NIVEL_MAXIMO_M

BRUTO = DADOS / "brutos" / "ituporanga-mymaps-ruas-2026-09-09-transcricao.tsv"

#: Teto do mapa de manchas por cota do mesmo município (camadas COTA 3,00 … 6,50).
TETO_DAS_MANCHAS_M = 6.5

#: "Primeira cota considerada crítica para alagamentos" — secretário de
#: Planejamento Vilmar Schwambach, Rádio Educadora 90.3 (relatado em 09/09/2026).
PRIMEIRA_COTA_CRITICA_M = 3.25

#: Raio dentro do qual um ponto ainda é "a cidade". Ituporanga é pequena; um
#: ponto a mais de 5 km do centroide não é rua do centro.
RAIO_URBANO_KM = 5.0


def carregar(caminho: Path = BRUTO) -> list[dict]:
    """Lê o TSV transcrito; linhas com `#` são proveniência, não dado."""
    pontos = []
    for linha in caminho.read_text(encoding="utf-8").splitlines():
        if not linha.strip() or linha.startswith("#") or linha.startswith("cota_m\t"):
            continue
        cota, local, lat, lon = linha.split("\t")
        pontos.append({"cota_m": float(cota), "local": local, "lat": float(lat), "lon": float(lon)})
    return pontos


def separar_lixo(pontos: list[dict], teto: float = NIVEL_MAXIMO_M) -> tuple[list[dict], list[dict]]:
    """(válidos, recusados): recusa o que não é nível de rio desta bacia."""
    validos = [p for p in pontos if 0 < p["cota_m"] <= teto]
    lixo = [p for p in pontos if not (0 < p["cota_m"] <= teto)]
    return validos, lixo


def _km(a: dict, b: dict) -> float:
    lat = math.radians((a["lat"] + b["lat"]) / 2)
    dx = math.radians(a["lon"] - b["lon"]) * math.cos(lat) * 6371
    dy = math.radians(a["lat"] - b["lat"]) * 6371
    return math.hypot(dx, dy)


def centroide(pontos: list[dict]) -> dict:
    n = len(pontos)
    return {"lat": sum(p["lat"] for p in pontos) / n, "lon": sum(p["lon"] for p in pontos) / n}


def fora_do_perimetro(pontos: list[dict], raio_km: float = RAIO_URBANO_KM) -> list[tuple[dict, float]]:
    c = centroide(pontos)
    return [(p, _km(p, c)) for p in pontos if _km(p, c) > raio_km]


def acima_do_teto(pontos: list[dict], teto: float = TETO_DAS_MANCHAS_M) -> list[dict]:
    return [p for p in pontos if p["cota_m"] > teto]


def cercam(pontos: list[dict], valor: float = PRIMEIRA_COTA_CRITICA_M) -> tuple[dict | None, dict | None]:
    """A maior cota abaixo e a menor cota acima de `valor`."""
    abaixo = [p for p in pontos if p["cota_m"] < valor]
    acima = [p for p in pontos if p["cota_m"] >= valor]
    return (max(abaixo, key=lambda p: p["cota_m"]) if abaixo else None,
            min(acima, key=lambda p: p["cota_m"]) if acima else None)


def resumo(pontos: list[dict]) -> dict:
    validos, lixo = separar_lixo(pontos)
    cotas = sorted(p["cota_m"] for p in validos)
    return {
        "total": len(pontos),
        "validos": len(validos),
        "lixo": [(p["local"], p["cota_m"]) for p in lixo],
        "min_m": cotas[0] if cotas else None,
        "max_m": cotas[-1] if cotas else None,
        "mediana_m": cotas[len(cotas) // 2] if cotas else None,
        "acima_do_teto_das_manchas": len(acima_do_teto(validos)),
        "fora_do_perimetro": [(p["local"], round(d, 1)) for p, d in fora_do_perimetro(validos)],
        "cercam_3_25": tuple((p["local"], p["cota_m"]) if p else None for p in cercam(validos)),
        "outro_curso_dagua": [p["local"] for p in validos if "gabiroba" in p["local"].lower()],
    }


def main() -> int:
    if not BRUTO.exists():
        print(f"não achei {BRUTO}", file=sys.stderr)
        return 1
    r = resumo(carregar())
    print(f"{r['total']} pontos no mapa; {r['validos']} são cota de rio plausível.")
    for local, cota in r["lixo"]:
        print(f"  RECUSADO: '{local}' = {cota:.2f} m — não é nível de rio desta bacia (teto {NIVEL_MAXIMO_M:.0f} m); "
              "digitação ou altitude na coluna errada. Avisar a Defesa Civil.")
    print(f"cotas de {r['min_m']:.2f} a {r['max_m']:.2f} m (mediana {r['mediana_m']:.2f}).")
    print(f"{r['acima_do_teto_das_manchas']} pontos ACIMA de {TETO_DAS_MANCHAS_M:.2f} m, o teto do mapa de manchas: "
          "para essas ruas há cota e não há mancha.")
    a, b = r["cercam_3_25"]
    print(f"os {PRIMEIRA_COTA_CRITICA_M:.2f} m do secretário ficam entre "
          f"{'nada' if not a else f'{a[1]:.2f} ({a[0]})'} e {'nada' if not b else f'{b[1]:.2f} ({b[0]})'}.")
    if r["fora_do_perimetro"]:
        print("fora do perímetro urbano:", r["fora_do_perimetro"])
    else:
        print(f"todos os pontos a menos de {RAIO_URBANO_KM:.0f} km do centroide — é uma cidade só.")
    if r["outro_curso_dagua"]:
        print("pontos que citam outro curso d'água (Rio Gabiroba):", r["outro_curso_dagua"])
    print("\nNADA foi gravado em cotas-ruas.json: a régua destas cotas não está nomeada, e a leitura ao vivo "
          "de Ituporanga é a estadual, em outro datum.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
