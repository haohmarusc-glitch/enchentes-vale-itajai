#!/usr/bin/env python3
"""
Acha onde cada afluente entra no tronco do Açu — SEM Overpass, só com os GeoJSON.

Resolve a pendência "entrada do Benedito e do Luís Alves" (ver
docs/TOPOLOGIA-CANONICA.md e estacoes.json._topologia.afluentes_rios). A
confluência é, por definição, o ponto onde o traçado do afluente chega mais
perto do traçado do tronco — com os dois GeoJSON, é geometria pura.

MÉTODO
1. Carrega o traçado do tronco (data/rios/itajai-acu.geojson).
2. Projeta cada cidade do tronco (por `coordenadas`) para achar sua posição ao
   longo do traçado.
3. Para cada afluente, o ponto do afluente mais perto do tronco é a confluência;
   descobre entre quais cidades ela cai.
4. `--gravar` atualiza o `ponto_exato` da entrada correspondente em
   `_topologia.afluentes_rios`, PRESERVANDO o formato do arquivo.

HONESTIDADE
- Se o toque for grande (> LIMITE_TOQUE_M), os traçados NÃO se encontram no
  GeoJSON (falta trecho, ou o afluente baixado é só o alto curso): AVISA e não
  grava. Melhor sem resposta que com resposta errada.
- Os GeoJSON dos afluentes (benedito.geojson, luiz-alves.geojson) NÃO estão no
  repositório — rode onde eles existem (a VPS). Sem eles, o script pula o
  afluente e não inventa nada.

Uso:
    python3 scripts/achar_confluencias.py            # relatório
    python3 scripts/achar_confluencias.py --gravar   # grava ponto_exato
"""
import argparse
import json
import math
import re
import sys
from pathlib import Path

from medir_distancia_rio import carrega_grafo, dijkstra, no_mais_perto

RAIZ = Path(__file__).resolve().parent.parent
RIOS = RAIZ / "data" / "rios"
ESTACOES = RAIZ / "data" / "estacoes.json"
TRONCO = "itajai-acu"  # base do arquivo em data/rios/

#: arquivo do afluente -> (nome legível, cidade do tronco cuja entrada ele marca).
#: A cidade casa com a entrada em _topologia.afluentes_rios[*].entra_perto_de.
AFLUENTES = {
    "benedito.geojson": ("Rio Benedito", "indaial"),
    "luiz-alves.geojson": ("Rio Luís Alves", "ilhota"),
}
#: Toque acima disto = traçados não se encontram: geometria incompleta, não grava.
LIMITE_TOQUE_M = 300.0


def carregar(nome: str) -> list[tuple[float, float]] | None:
    """Vértices do afluente como (lon, lat) — a mesma convenção do medir_distancia_rio."""
    f = RIOS / nome
    if not f.exists():
        return None
    g = json.loads(f.read_text(encoding="utf-8"))
    pts: list[tuple[float, float]] = []
    for ft in g.get("features", [g]):
        geom = ft.get("geometry", ft)
        t, c = geom.get("type"), geom.get("coordinates", [])
        if t == "LineString":
            pts += [(x, y) for x, y, *_ in c]
        elif t == "MultiLineString":
            for parte in c:
                pts += [(x, y) for x, y, *_ in parte]
    return pts or None


def analisar() -> dict[str, dict]:
    """
    Para cada afluente com GeoJSON, entre quais cidades do tronco ele entra.

    A posição ao longo do tronco NÃO é distância acumulada na ordem do arquivo (o
    traçado do OSM é um MultiLineString de segmentos SOLTOS — somar na ordem dá
    número sem sentido). É a distância pela ÁGUA de Rio do Sul (início do tronco)
    até o ponto, no grafo do traçado (mesmo Dijkstra do medir_distancia_rio.py).
    """
    try:
        grafo, pos = carrega_grafo(TRONCO)
    except FileNotFoundError:
        sys.exit(f"ERRO: data/rios/{TRONCO}.geojson não encontrado.")
    dados = json.loads(ESTACOES.read_text(encoding="utf-8"))
    cidades = [c for c in dados["rios"]["itajai-acu"]["cidades"]
               if c.get("ramo") == "tronco_acu" and c.get("coordenadas")]

    # Origem do tronco = vértice mais perto de Rio do Sul (ordem_no_ramo 1).
    # coordenadas é [lat, lon]; o grafo trabalha em (lon, lat).
    inicio = min(cidades, key=lambda c: c.get("ordem_no_ramo") or 99)
    no_origem, _ = no_mais_perto(pos, (inicio["coordenadas"][1], inicio["coordenadas"][0]))

    def km_no_tronco(lon: float, lat: float) -> tuple[float | None, float]:
        no, af = no_mais_perto(pos, (lon, lat))
        return dijkstra(grafo, no_origem, no), af

    # Distância pela água de cada cidade do tronco até a origem.
    km_cidade = {}
    for c in cidades:
        km, _ = km_no_tronco(c["coordenadas"][1], c["coordenadas"][0])
        if km is not None:
            km_cidade[c["id"]] = (km, c["nome"])
    ordenadas = sorted(km_cidade.items(), key=lambda kv: kv[1][0])

    saida: dict[str, dict] = {}
    for arq, (nome, cidade_alvo) in AFLUENTES.items():
        aflu = carregar(arq)
        if not aflu:
            saida[cidade_alvo] = {"nome": nome, "status": "sem_geojson",
                                  "texto": f"{arq} não está no repositório — rode na VPS."}
            continue
        # Ponto do afluente mais perto do tronco = confluência (afastamento mínimo).
        melhor = (math.inf, None)
        for p in aflu:
            _, af = no_mais_perto(pos, p)
            if af < melhor[0]:
                melhor = (af, p)
        afast, ponto = melhor
        if afast > LIMITE_TOQUE_M / 1000:  # no_mais_perto devolve km
            saida[cidade_alvo] = {"nome": nome, "status": "nao_toca",
                                  "texto": f"traçados não se encontram (mín. {afast * 1000:.0f} m); geometria incompleta"}
            continue
        km_conf, _ = km_no_tronco(ponto[0], ponto[1])
        if km_conf is None:
            saida[cidade_alvo] = {"nome": nome, "status": "nao_toca",
                                  "texto": "confluência fora do trecho conectado do traçado"}
            continue
        antes = [n for _, (d, n) in ordenadas if d <= km_conf]
        depois = [n for _, (d, n) in ordenadas if d > km_conf]
        entre = f"depois de {antes[-1]}" if antes else "antes da 1ª cidade do tronco"
        if depois:
            entre += f" e antes de {depois[0]}"
        saida[cidade_alvo] = {
            "nome": nome, "status": "ok",
            "texto": f"entra {entre} — confluência medida no traçado OSM "
                     f"(toque {afast * 1000:.0f} m, {km_conf:.1f} km de Rio do Sul pela água)",
        }
    return saida


def gravar(resultado: dict[str, dict]) -> int:
    """Atualiza o ponto_exato das entradas medidas, preservando o formato do arquivo."""
    raw = ESTACOES.read_text(encoding="utf-8")
    gravadas = 0
    for cidade_alvo, r in resultado.items():
        if r["status"] != "ok":
            continue
        # A entrada compacta de afluentes_rios com este entra_perto_de.
        padrao = re.compile(
            r'(\{[^\n]*"entra_perto_de":\s*"' + re.escape(cidade_alvo) + r'"[^\n]*"ponto_exato":\s*)"(?:[^"\\]|\\.)*"')
        novo, n = padrao.subn(lambda m: m.group(1) + json.dumps(r["texto"], ensure_ascii=False), raw, count=1)
        if n:
            raw, gravadas = novo, gravadas + 1
        else:
            print(f"  aviso: não achei entrada afluentes_rios com entra_perto_de={cidade_alvo}", file=sys.stderr)
    json.loads(raw)  # trava: nunca grava JSON inválido
    ESTACOES.write_text(raw, encoding="utf-8")
    return gravadas


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--gravar", action="store_true", help="grava ponto_exato em estacoes.json")
    args = ap.parse_args()

    resultado = analisar()
    for cidade_alvo, r in resultado.items():
        print(f"[{r['nome']}] ({cidade_alvo}) {r['status']}: {r['texto']}")

    if args.gravar:
        n = gravar(resultado)
        print(f"\ngravado ponto_exato em {n} afluente(s) (formato preservado).")
    elif any(r["status"] == "ok" for r in resultado.values()):
        print("\n(relatório; use --gravar para escrever o ponto_exato)")
    else:
        print("\nNada medido (faltam os GeoJSON dos afluentes) — nada a gravar.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
