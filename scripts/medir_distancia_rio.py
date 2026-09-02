#!/usr/bin/env python3
"""
Distância AO LONGO DO RIO entre as cidades do tronco, pelo traçado do OSM.

Por que existe: o `transito.json` tem tempos de literatura (JICA) e, para
contexto, a distância. Até agora só havia a distância em LINHA RETA, que
subestima o percurso real (o rio serpenteia). Este script mede a distância
seguindo o traçado (`data/rios/*.geojson`), montando os segmentos soltos do
OSM num grafo e caminhando de uma cidade à outra (Dijkstra) — a distância do
caminho mais curto pela ÁGUA, não pela reta.

O que ele NÃO faz: mudar os tempos de chegada. Os `horas_min/max` continuam os
do estudo JICA — dividir distância por uma velocidade suposta seria inventar
precisão que a fonte não tem. A distância entra como CONTEXTO (`km_rio`), e a
velocidade implícita (km_rio ÷ horas JICA) sai só no relatório, para conferência.

Uma cidade longe do traçado (afastamento grande) NÃO recebe km_rio: sinal de
que ela não está nesse desenho (cabeceira fora do trecho baixado, braço não
mapeado). Melhor um campo ausente que um número sem sentido.

Uso:
    python3 scripts/medir_distancia_rio.py            # relatório
    python3 scripts/medir_distancia_rio.py --gravar   # grava km_rio no transito.json
"""

import argparse
import heapq
import json
import math
import sys

from comum import DADOS

#: Cidade a mais que isto do traçado não está nele — km_rio fica null.
AFASTAMENTO_MAX_KM = 1.5
#: Ponto do traçado arredondado a isto vira o mesmo nó do grafo (junta segmentos
#: que compartilham vértice; ~1 m em 5 casas).
CASAS = 5
#: Furo do OSM entre duas pontas soltas até isto é costurado (o rio é contínuo;
#: o desenho é que tem lacuna). Acima disto, não: seria inventar leito.
PONTA_MAX_KM = 0.3


def _hav(a: tuple[float, float], b: tuple[float, float]) -> float:
    """Distância em km entre dois [lon, lat]."""
    lon1, lat1 = a
    lon2, lat2 = b
    r = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlmb = math.radians(lon2 - lon1)
    h = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlmb / 2) ** 2
    return 2 * r * math.asin(min(1.0, math.sqrt(h)))


def carrega_grafo(rio: str):
    """Grafo do traçado: nó = vértice arredondado, aresta = vértices vizinhos."""
    g = json.loads((DADOS / "rios" / f"{rio}.geojson").read_text(encoding="utf-8"))
    coords = g["geometry"]["coordinates"]
    grafo: dict[tuple, list[tuple]] = {}
    pos: dict[tuple, tuple[float, float]] = {}

    def no(v):
        k = (round(v[0], CASAS), round(v[1], CASAS))
        pos.setdefault(k, (v[0], v[1]))
        grafo.setdefault(k, [])
        return k

    for seg in coords:
        for i in range(len(seg) - 1):
            a, b = no(seg[i]), no(seg[i + 1])
            if a == b:
                continue
            w = _hav(pos[a], pos[b])
            grafo[a].append((b, w))
            grafo[b].append((a, w))

    # Costura os furos do OSM: ponta solta (grau 1) ligada à ponta solta mais
    # perto, se estiver a menos de PONTA_MAX_KM. São poucas (a rede quase toda já
    # conecta); costurar só pontas soltas evita criar atalho falso no meio.
    soltas = [k for k, viz in grafo.items() if len(viz) == 1]
    for a in soltas:
        melhor, dist = None, PONTA_MAX_KM
        for b in soltas:
            if b == a or b in {v for v, _ in grafo[a]}:
                continue
            d = _hav(pos[a], pos[b])
            if d < dist:
                melhor, dist = b, d
        if melhor is not None:
            grafo[a].append((melhor, dist))
            grafo[melhor].append((a, dist))
    return grafo, pos


def no_mais_perto(pos: dict, ponto: tuple[float, float]):
    melhor, dist = None, math.inf
    for k, v in pos.items():
        d = _hav(v, ponto)
        if d < dist:
            melhor, dist = k, d
    return melhor, dist


def dijkstra(grafo: dict, origem, destino) -> float | None:
    fila = [(0.0, origem)]
    visto: dict = {}
    while fila:
        d, u = heapq.heappop(fila)
        if u in visto:
            continue
        visto[u] = d
        if u == destino:
            return d
        for v, w in grafo.get(u, ()):
            if v not in visto:
                heapq.heappush(fila, (d + w, v))
    return None


def km_rio_entre(grafo, pos, a: tuple, b: tuple) -> tuple[float | None, float, float]:
    """(km pelo rio ou None, afastamento de a, afastamento de b)."""
    na, da = no_mais_perto(pos, a)
    nb, db = no_mais_perto(pos, b)
    if da > AFASTAMENTO_MAX_KM or db > AFASTAMENTO_MAX_KM:
        return None, da, db
    return dijkstra(grafo, na, nb), da, db


def coords_das_cidades(rio: str) -> dict[str, tuple[float, float]]:
    d = json.loads((DADOS / "estacoes.json").read_text(encoding="utf-8"))
    saida = {}
    for c in d["rios"][rio]["cidades"]:
        co = c.get("coordenadas")
        if co:
            saida[c["id"]] = (co[1], co[0])  # [lat,lon] -> [lon,lat]
    return saida, d["rios"][rio].get("_topologia")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--gravar", action="store_true", help="grava km_rio nos trechos do transito.json")
    args = ap.parse_args()

    transito = json.loads((DADOS / "transito.json").read_text(encoding="utf-8"))
    grafos: dict = {}
    km_por_trecho: dict[tuple[str, str, str], float] = {}

    print(f"{'trecho':38} {'reta':>6} {'rio':>7} {'fator':>5} {'h JICA':>7} {'km/h':>6}")
    for t in transito["trechos"]:
        rio = t["rio"]
        try:
            if rio not in grafos:
                grafos[rio] = carrega_grafo(rio)
                grafos[rio + "_cid"] = coords_das_cidades(rio)
        except FileNotFoundError:
            continue
        grafo, pos = grafos[rio]
        cidades, _ = grafos[rio + "_cid"]
        de, para = t["de"], t["para"]
        if de not in cidades or para not in cidades:
            continue
        reta = _hav(cidades[de], cidades[para])
        km, da, db = km_rio_entre(grafo, pos, cidades[de], cidades[para])
        rotulo = f"{rio.split('-')[-1]} {de}->{para}"
        if km is None:
            if da > AFASTAMENTO_MAX_KM or db > AFASTAMENTO_MAX_KM:
                motivo = f"fora do traçado (afast. {da:.1f}/{db:.1f} km)"
            else:
                motivo = "sem caminho contínuo (furo/braço separado no OSM)"
            print(f"{rotulo:38} {reta:6.1f} {'—':>7}   ({motivo})")
            continue
        fator = km / reta if reta else float("nan")
        hmed = (t["horas_min"] + t["horas_max"]) / 2
        vel = km / hmed if hmed else float("nan")
        print(f"{rotulo:38} {reta:6.1f} {km:7.1f} {fator:5.2f} {t['horas_min']:>3}-{t['horas_max']:<3} {vel:6.1f}")
        km_por_trecho[(rio, de, para)] = round(km, 1)

    if args.gravar:
        gravar_km_rio(km_por_trecho)
        print(f"\ngravado km_rio em {len(km_por_trecho)} trechos (formato preservado).")
    else:
        print("\n(relatório; use --gravar para escrever km_rio)")
    return 0


def gravar_km_rio(km_por_trecho: dict[tuple[str, str, str], float]) -> None:
    """Insere km_rio nos trechos SEM reformatar o arquivo (inserção de texto).

    O transito.json guarda cada trecho numa linha compacta; um json.dump
    reescreveria o arquivo inteiro e sujaria o diff. Aqui só se acrescenta o
    campo na linha certa, e o campo de _meta uma vez.
    """
    import re
    caminho = DADOS / "transito.json"
    raw = caminho.read_text(encoding="utf-8")

    for (rio, de, para), k in km_por_trecho.items():
        # A linha do trecho: contém "de": "<de>" e "para": "<para>". Idempotente:
        # remove km_rio antigo antes de inserir.
        padrao = re.compile(
            r'(\{[^\n]*"de":\s*"' + re.escape(de) + r'"[^\n]*"para":\s*"' + re.escape(para) + r'"[^\n]*?)'
            r'(,\s*"km_rio":\s*[\d.]+)?(\s*\})')
        def repl(m: re.Match) -> str:
            return f'{m.group(1)}, "km_rio": {k}{m.group(3)}'
        raw, n = padrao.subn(repl, raw, count=1)
        if n == 0:
            print(f"  aviso: não achei o trecho {rio} {de}->{para} para gravar", file=sys.stderr)

    if '"km_rio":' not in raw.split('"trechos"')[0]:
        # ainda não há o campo em _meta.campos: insere após "confianca".
        campo = ('      "km_rio": "Distância AO LONGO DO RIO (traçado OSM, ODbL), em km, por '
                 'scripts/medir_distancia_rio.py. Contexto/QA — NÃO é usada para calcular tempo; '
                 'os horas_min/max continuam do estudo JICA."')
        raw = re.sub(r'(\n(\s*)"confianca":\s*"[^"]*"[^\n]*)(\n\s*\},\s*\n\s*"origem_das_faixas")',
                     lambda m: f'{m.group(1)},\n{campo}{m.group(3)}', raw, count=1)

    json.loads(raw)  # trava: nunca grava JSON inválido
    caminho.write_text(raw, encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
