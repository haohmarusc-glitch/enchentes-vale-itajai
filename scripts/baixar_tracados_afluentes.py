#!/usr/bin/env python3
"""
Baixa do OpenStreetMap o traçado do Benedito, do Rio dos Cedros, do Itajaí do Sul, do Trombudo e do Ribeirão
Guabiruba.

POR QUE (pedido do Jefferson, 06/10/2026). Desde a auditoria das réguas, o pino de cada cidade fica na régua,
mas cidades ainda aparecem sem o rio delas no mapa:
  - Timbó, no Benedito (o Benedito também recebe o Rio dos Cedros);
  - Ituporanga, no Itajaí do Sul — hoje só há 10,5 km dele, da Defesa Civil de Rio do Sul (Asthon),
    perto da confluência;
  - Trombudo Central, no Trombudo.
Na mesma data, a inspeção visual do Jefferson acrescentou Rio dos Cedros (Rio dos Cedros) e Guabiruba
(Ribeirão Guabiruba). A causa dos cinco é a mesma: o arquivo do rio não existia em data/rios/ — o Monitor
desenha todo traçado que existe, em cinza, sem depender de leitura, cota ou faixa.

O QUE CONFERE ANTES DE GRAVAR CADA RIO (o que falha não grava; os outros seguem):
  - o nome exato veio;
  - o traçado chega a um rio já desenhado (o Açu; o Trombudo também pode chegar ao Itajaí do Sul baixado
    na mesma rodada): alguma ponta a menos de `chega_km`;
  - o traçado passa pela régua da cidade: o pino do cadastro a menos de `passa_km`.
Chegar a um rio é GEOMETRIA, não topologia: a árvore da bacia (`_topologia` em estacoes.json) não muda por
causa disto. O Trombudo continua sem posição na árvore até uma fonte dizer a confluência.

Gravado, `converter_tracado_rios.py` gera `data/rios/<id>.geojson`. Fonte: © OpenStreetMap contributors,
ODbL. Roda onde o Overpass responde: na VPS ou no Actions (`baixar-tracados-afluentes.yml`).

Uso:
    python3 scripts/baixar_tracados_afluentes.py            # baixa e confere, não grava
    python3 scripts/baixar_tracados_afluentes.py --gravar   # grava data/brutos/tracado-<id>-osm.json
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "scripts"))

from baixar_tracado_hercilio import buscar_consulta, comprimento_km, km, tracado  # noqa: E402

BRUTOS = RAIZ / "data" / "brutos"

#: Um rio por entrada. `caixa` = (sul, oeste, norte, leste), larga de propósito: quem filtra é o nome.
#: `chega_a` são os traçados (ids de data/rios ou desta rodada) a que a ponta tem de chegar.
RIOS = {
    "benedito": {
        "nomes": ("Rio Benedito",),
        "caixa": (-27.00, -49.60, -26.35, -49.10),
        "chega_a": ("itajai-acu",),
        "chega_km": 1.0,
        "cidade": "timbo",
        # 1 km, não 0,5 (06/10/2026): a primeira rodada achou o Benedito a 0,63 km do pino. A coordenada de
        # Timbó ("Rio Benedito, Rua Equador") não tem fonte declarada no cadastro — o mesmo caso do Trombudo.
        "passa_km": 1.0,
    },
    "rio-dos-cedros": {
        # Inspeção de 06/10/2026: pino de Rio dos Cedros sem o rio dele. Desce de Rio dos Cedros para o Benedito.
        "nomes": ("Rio dos Cedros",),
        "caixa": (-26.95, -49.55, -26.45, -49.15),
        "chega_a": ("benedito",),
        "chega_km": 1.0,
        "cidade": "rio-dos-cedros",
        # 1 km: coordenada do cadastro ("Régua da Praça Matriz") sem fonte declarada, como Timbó.
        "passa_km": 1.0,
    },
    "itajai-do-sul": {
        "nomes": ("Rio Itajaí do Sul",),
        "caixa": (-27.90, -49.80, -27.15, -49.10),
        "chega_a": ("itajai-acu",),
        "chega_km": 1.0,
        "cidade": "ituporanga",
        "passa_km": 0.5,
    },
    "trombudo": {
        "nomes": ("Rio Trombudo",),
        "caixa": (-27.60, -50.05, -27.10, -49.55),
        "chega_a": ("itajai-acu", "itajai-do-sul"),
        "chega_km": 1.0,
        "cidade": "trombudo-central",
        # 1 km, não 0,5: a coordenada de Trombudo Central não tem fonte declarada no cadastro, e a estação
        # estadual mais perto (DCSC-00035, equivalência não confirmada) fica a 0,9 km dela.
        "passa_km": 1.0,
    },
    "guabiruba": {
        # Inspeção de 06/10/2026: pino de Guabiruba sem o curso dele. A DCSC-00029 mede o ribeirão que passa
        # pela cidade; o cadastro o chama de Ribeirão Guabiruba (afluente lateral do Mirim, perto de Brusque).
        # O OSM pode tê-lo como rio ou ribeirão: os dois nomes entram, e quem confere é a passagem pela estação.
        "nomes": ("Ribeirão Guabiruba", "Rio Guabiruba"),
        "waterway": ("river", "stream"),
        "caixa": (-27.20, -49.10, -27.00, -48.85),
        "chega_a": ("itajai-mirim",),
        "chega_km": 1.0,
        "cidade": "guabiruba",
        # 0,5 km: o pino é a coordenada da estação DCSC-00029.
        "passa_km": 0.5,
    },
}


def consulta(rio_id: str) -> str:
    c = RIOS[rio_id]
    s, o, n, l = c["caixa"]
    nomes = "|".join(c["nomes"])
    # Ribeirão costuma ser `stream` no OSM; rio, `river`. Quem filtra é o nome exato.
    tipos = "|".join(c.get("waterway", ("river",)))
    return (f'[out:json][timeout:120];\nway["waterway"~"^({tipos})$"]["name"~"^({nomes})$"]'
            f"({s},{o},{n},{l});\nout geom;")


def linhas(elementos: list[dict], nomes: tuple[str, ...]) -> list[list[tuple[float, float]]]:
    out = []
    for e in elementos:
        if e.get("type") != "way" or (e.get("tags") or {}).get("name") not in nomes:
            continue
        pts = [(p["lon"], p["lat"]) for p in e.get("geometry") or []
               if isinstance(p.get("lon"), (int, float)) and isinstance(p.get("lat"), (int, float))]
        if len(pts) >= 2:
            out.append(pts)
    return out


def pino(cidade_id: str) -> tuple[float, float]:
    e = json.loads((RAIZ / "data" / "estacoes.json").read_text(encoding="utf-8"))
    c = next(c for r in e["rios"].values() for c in r["cidades"] if c["id"] == cidade_id)
    lat, lon = c["coordenadas"]
    return (lon, lat)


def conferir(rio_id: str, ls: list, alvos: dict[str, list], pino_cidade: tuple[float, float]) -> list[str]:
    """Problemas que impedem gravar este rio. Vazio = pode gravar."""
    c = RIOS[rio_id]
    if not ls:
        return [f"não veio nenhum way chamado {' / '.join(c['nomes'])}"]
    problemas = []
    pontos_alvo = [p for a in c["chega_a"] for p in alvos.get(a) or []]
    if not pontos_alvo:
        problemas.append(f"nenhum traçado de {', '.join(c['chega_a'])} para conferir a chegada")
    else:
        pontas = [p for l in ls for p in (l[0], l[-1])]
        d = min(km(p, q) for p in pontas for q in pontos_alvo)
        if d > c["chega_km"]:
            problemas.append(f"não chega a {' / '.join(c['chega_a'])}: a ponta mais perto fica a {d:.2f} km "
                             f"(limite {c['chega_km']} km)")
    d = distancia_ao_pino(ls, pino_cidade)
    if d > c["passa_km"]:
        problemas.append(f"não passa pela régua de {c['cidade']}: fica a {d:.2f} km do pino (limite {c['passa_km']} km)")
    return problemas


ORDEM = ("benedito", "rio-dos-cedros", "itajai-do-sul", "trombudo", "guabiruba")


def distancia_ao_pino(ls: list, pino_cidade: tuple[float, float]) -> float:
    return min(km(pino_cidade, p) for l in ls for p in l)


def consulta_arredores(cidade_id: str, raio_m: int = 1500) -> str:
    lon, lat = pino(cidade_id)
    return f'[out:json][timeout:120];\nway["waterway"](around:{raio_m},{lat},{lon});\nout geom;'


def diagnosticar(rio_id: str, resposta: dict, texto: str) -> None:
    """Rio recusado: grava o que veio pelo nome e os cursos d'água a 1,5 km da régua, e lista no resumo."""
    cidade = RIOS[rio_id]["cidade"]
    resposta["_consulta"] = {"overpass": texto, "recusado": True,
                             "baixado_em": datetime.now(timezone.utc).isoformat(timespec="seconds")}
    (BRUTOS / f"recusado-{rio_id}-osm.json").write_text(json.dumps(resposta, ensure_ascii=False) + "\n", encoding="utf-8")
    texto_a = consulta_arredores(cidade)
    arredores, _ = buscar_consulta(texto_a)
    arredores["_consulta"] = {"overpass": texto_a, "baixado_em": datetime.now(timezone.utc).isoformat(timespec="seconds")}
    (BRUTOS / f"arredores-{rio_id}-osm.json").write_text(json.dumps(arredores, ensure_ascii=False) + "\n", encoding="utf-8")
    p = pino(cidade)
    print(f"   cursos d'água a 1,5 km da régua de {cidade}:")
    achados = []
    for e in arredores.get("elements") or []:
        pts = [(q["lon"], q["lat"]) for q in e.get("geometry") or []]
        if pts:
            achados.append((distancia_ao_pino([pts], p), e.get("id"), e.get("tags") or {}))
    for d, wid, t in sorted(achados, key=lambda x: x[0]):
        print(f"     way {wid} {t.get('waterway')} {t.get('name')!r}: {d:.2f} km do pino")


def main() -> int:
    ap = argparse.ArgumentParser(description="Baixa o traçado dos afluentes sem rio no Monitor (OSM).")
    ap.add_argument("--gravar", action="store_true", help="grava data/brutos/tracado-<id>-osm.json dos que passarem")
    ap.add_argument("--so", choices=sorted(RIOS), action="append", help="só este rio (repetível)")
    a = ap.parse_args()

    alvos = {"itajai-acu": tracado("itajai-acu"), "itajai-mirim": tracado("itajai-mirim")}
    gravados, recusados = [], []
    # Ordem: quem recebe antes de quem chega (o Rio dos Cedros chega ao Benedito; o Trombudo pode chegar ao Sul).
    for rio_id in [r for r in ORDEM if not a.so or r in a.so]:
        texto = consulta(rio_id)
        resposta, espelho = buscar_consulta(texto)
        ls = linhas(resposta.get("elements") or [], RIOS[rio_id]["nomes"])
        print(f"{rio_id}: {len(ls)} way(s), {comprimento_km(ls):.1f} km")
        problemas = conferir(rio_id, ls, alvos, pino(RIOS[rio_id]["cidade"]))
        if problemas:
            for p in problemas:
                print(f"   RECUSADO: {p}", file=sys.stderr)
            recusados.append(rio_id)
            if a.gravar:
                # Para decidir à mão, sem adivinhar: o que veio pelo nome e os cursos d'água em volta da régua.
                diagnosticar(rio_id, resposta, texto)
            continue
        alvos[rio_id] = [p for l in ls for p in l]
        d = distancia_ao_pino(ls, pino(RIOS[rio_id]["cidade"]))
        print(f"   conferido: chega a {' / '.join(RIOS[rio_id]['chega_a'])} e passa a {d:.2f} km do pino de "
              f"{RIOS[rio_id]['cidade']}")
        if a.gravar:
            resposta["_consulta"] = {
                "overpass": texto,
                "espelho": espelho,
                "baixado_em": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                "script": "scripts/baixar_tracados_afluentes.py",
            }
            destino = BRUTOS / f"tracado-{rio_id}-osm.json"
            destino.write_text(json.dumps(resposta, ensure_ascii=False) + "\n", encoding="utf-8")
            print(f"   gravado: {destino.relative_to(RAIZ)}")
        gravados.append(rio_id)
    print(f"\nconferidos: {', '.join(gravados) or 'nenhum'} · recusados: {', '.join(recusados) or 'nenhum'}")
    return 0 if gravados else 1


if __name__ == "__main__":
    raise SystemExit(main())
