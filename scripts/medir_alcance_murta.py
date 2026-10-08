#!/usr/bin/env python3
"""
Mede, no traçado do Ribeirão da Murta, a continuidade entre a DC-07 e a foz e o trecho do futuro vínculo da DC-07.

Jefferson, 08/10/2026: "destravar a DC-07 exige também conferir a continuidade do traçado e delimitar o trecho do
novo vínculo". Este script faz as duas contas e imprime; NÃO cria vínculo (ver docs/VAO-MURTA.md).

  - continuidade: quantos vértices do traçado são alcançáveis a partir do ponto da DC-07, andando só por arestas
    existentes (dois vértices são o mesmo nó quando ficam a menos de `MESMO_NO_M`);
  - alcance: o comprimento pelo traçado da DC-07 até a DC-09 (a próxima régua rio abaixo, que é onde o vínculo da
    DC-07 pararia, pela regra de `VINCULOS_DE_REGUA`) e até a foz no Itajaí-Açu.

Uso: python3 scripts/medir_alcance_murta.py [--json]
"""
from __future__ import annotations

import argparse
import heapq
import json
import math
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
TRACADO = RAIZ / "data" / "rios" / "ribeirao-murta.geojson"
ESTACOES = RAIZ / "data" / "estacoes.json"

#: Dois vértices são o mesmo nó do traçado quando ficam a menos disto (as emendas do OSM compartilham o nó: 0 m).
MESMO_NO_M = 1.0
K_LON = math.cos(math.radians(26.9))

Ponto = tuple[float, float]


def m(a: Ponto, b: Ponto) -> float:
    return math.hypot((a[0] - b[0]) * K_LON, a[1] - b[1]) * 111_320.0


def linhas_do_tracado(caminho: Path = TRACADO) -> list[list[Ponto]]:
    d = json.loads(caminho.read_text(encoding="utf-8"))
    return [[(c[0], c[1]) for c in l] for l in d["geometry"]["coordinates"]]


def reguas_da_murta(caminho: Path = ESTACOES) -> dict[str, Ponto]:
    """{código: (lon, lat)} das réguas de Itajaí cadastradas no `ribeirao-murta`."""
    dados = json.loads(caminho.read_text(encoding="utf-8"))
    return {r["codigo"]: (r["lon"], r["lat"]) for r in dados.get("estacoes_tempo_real") or []
            if r.get("cidade") == "itajai" and r.get("rio") == "ribeirao-murta" and r.get("lon") is not None}


class Grafo:
    """Vértices do traçado como nós (fundidos a `MESMO_NO_M`), segmentos como arestas com o comprimento em metros."""

    def __init__(self, linhas: list[list[Ponto]]):
        self.nos: list[Ponto] = []
        self.adj: dict[int, list[tuple[int, float]]] = {}
        for linha in linhas:
            for a, b in zip(linha, linha[1:]):
                self._liga(self._no(a), self._no(b), m(a, b))

    def _no(self, p: Ponto) -> int:
        for i, q in enumerate(self.nos):
            if m(p, q) <= MESMO_NO_M:
                return i
        self.nos.append(p)
        return len(self.nos) - 1

    def _liga(self, i: int, j: int, d: float) -> None:
        self.adj.setdefault(i, []).append((j, d))
        self.adj.setdefault(j, []).append((i, d))

    def projetar(self, p: Ponto, linhas: list[list[Ponto]]) -> tuple[float, int]:
        """Insere o ponto do traçado mais próximo de `p` como nó; devolve (distância de p a ele em m, índice)."""
        melhor = None
        for linha in linhas:
            for a, b in zip(linha, linha[1:]):
                ax, ay, bx, by, px, py = a[0] * K_LON, a[1], b[0] * K_LON, b[1], p[0] * K_LON, p[1]
                dx, dy = bx - ax, by - ay
                t = 0.0 if dx == dy == 0 else max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / (dx * dx + dy * dy)))
                q = (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)
                d = m(p, q)
                if melhor is None or d < melhor[0]:
                    melhor = (d, q, a, b)
        assert melhor is not None
        d, q, a, b = melhor
        i = self._no(q)
        if i == len(self.nos) - 1:   # nó novo no meio do segmento: liga aos dois extremos
            self._liga(i, self._no(a), m(q, a))
            self._liga(i, self._no(b), m(q, b))
        return d, i

    def distancias(self, origem: int) -> dict[int, float]:
        dist = {origem: 0.0}
        fila = [(0.0, origem)]
        while fila:
            d, u = heapq.heappop(fila)
            if d > dist[u]:
                continue
            for v, w in self.adj.get(u, []):
                if d + w < dist.get(v, math.inf):
                    dist[v] = d + w
                    heapq.heappush(fila, (d + w, v))
        return dist


def medir(linhas: list[list[Ponto]], reguas: dict[str, Ponto], foz: Ponto) -> dict:
    g = Grafo(linhas)
    vertices = len(g.nos)
    d07, i07 = g.projetar(reguas["DC-07"], linhas)
    d09, i09 = g.projetar(reguas["DC-09"], linhas)
    dfoz, ifoz = g.projetar(foz, linhas)
    dist = g.distancias(i07)
    alcancaveis = sum(1 for i in range(vertices) if i in dist)
    return {
        "vertices": vertices,
        "alcancaveis_da_dc07": alcancaveis,
        "continuo": alcancaveis == vertices,
        "dc07": {"distancia_ao_tracado_m": round(d07), "ponto_no_tracado": [round(c, 6) for c in g.nos[i07]]},
        "dc09": {"distancia_ao_tracado_m": round(d09), "ponto_no_tracado": [round(c, 6) for c in g.nos[i09]]},
        "foz": {"distancia_ao_tracado_m": round(dfoz)},
        "dc07_ate_dc09_km": round(dist[i09] / 1000, 2) if i09 in dist else None,
        "dc07_ate_foz_km": round(dist[ifoz] / 1000, 2) if ifoz in dist else None,
        "dc09_ate_foz_km": round(g.distancias(i09).get(ifoz, math.nan) / 1000, 2),
    }


def foz_da_murta() -> Ponto:
    """O vértice do traçado da Murta mais próximo do Itajaí-Açu (o fim do curso no OSM)."""
    acu = [p for l in linhas_do_tracado(RAIZ / "data" / "rios" / "itajai-acu.geojson") for p in l]
    return min((p for l in linhas_do_tracado() for p in (l[0], l[-1])), key=lambda p: min(m(p, q) for q in acu))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--json", action="store_true", help="imprime só o JSON")
    args = ap.parse_args()
    medidas = medir(linhas_do_tracado(), reguas_da_murta(), foz_da_murta())
    if args.json:
        print(json.dumps(medidas, ensure_ascii=False, indent=1))
        return 0
    print(f"Traçado da Murta: {medidas['vertices']} vértices, {medidas['alcancaveis_da_dc07']} alcançáveis a partir "
          f"da DC-07 — {'CONTÍNUO' if medidas['continuo'] else 'PARTIDO'}")
    print(f"DC-07 a {medidas['dc07']['distancia_ao_tracado_m']} m do traçado, em {medidas['dc07']['ponto_no_tracado']}")
    print(f"DC-09 a {medidas['dc09']['distancia_ao_tracado_m']} m do traçado, em {medidas['dc09']['ponto_no_tracado']}")
    print(f"DC-07 → DC-09: {medidas['dc07_ate_dc09_km']} km (o alcance do futuro vínculo da DC-07; NÃO ativado)")
    print(f"DC-09 → foz no Açu: {medidas['dc09_ate_foz_km']} km · DC-07 → foz: {medidas['dc07_ate_foz_km']} km")
    return 0


if __name__ == "__main__":
    sys.exit(main())
