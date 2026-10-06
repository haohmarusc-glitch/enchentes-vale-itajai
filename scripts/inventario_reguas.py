#!/usr/bin/env python3
"""Inventário das réguas do mapa: de onde vem cada ponto e quão longe está da ficha da Defesa Civil de SC.

Pedido do Jefferson em 06/10/2026, com a auditoria visual das 19 cidades do Monitor. A regra é a dela:
- só se compara coordenada de estação com a ficha da MESMA estação (mesmo código DCSC);
- cidade sem código não é "corrigida" pela estação estadual mais próxima. Ela aparece como CANDIDATA,
  com a distância, para alguém conferir na fonte;
- nada aqui altera `estacoes.json`. O script só lê e escreve o relatório.

Fontes lidas:
- `data/estacoes.json`: cadastro das cidades e das réguas de Itajaí;
- `data/brutos/dcsc-estacoes-vale-2026-09-13.csv`: coordenadas e tipo (Hidro/Meteo) da API da DCSC;
- `data/rios/*.geojson`: traçados, para dizer a quantos km do rio da tela o pino ficava antes de 06/10.

Uso:
    python3 scripts/inventario_reguas.py            # imprime
    python3 scripts/inventario_reguas.py --gravar   # escreve docs/INVENTARIO-REGUAS.md
"""
from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
ESTACOES = RAIZ / "data" / "estacoes.json"
DCSC = RAIZ / "data" / "brutos" / "dcsc-estacoes-vale-2026-09-13.csv"
RIOS = RAIZ / "data" / "rios"
SAIDA = RAIZ / "docs" / "INVENTARIO-REGUAS.md"

# Até quantos km uma estação Hidro sem vínculo é listada como candidata.
RAIO_CANDIDATA_KM = 3.0


def km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Distância geodésica (haversine, raio médio de 6371 km)."""
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp, dl = p2 - p1, math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * 6371 * math.asin(math.sqrt(a))


def linhas(geo) -> list[list[list[float]]]:
    saida: list = []

    def anda(o):
        if isinstance(o, list):
            for x in o:
                anda(x)
        elif isinstance(o, dict):
            t = o.get("type")
            if t == "LineString":
                saida.append(o["coordinates"])
            elif t == "MultiLineString":
                saida.extend(o["coordinates"])
            else:
                for v in o.values():
                    anda(v)

    anda(geo)
    return saida


def carregar():
    with open(ESTACOES, encoding="utf-8") as f:
        estacoes = json.load(f)
    with open(DCSC, encoding="utf-8") as f:
        # Estação sem coordenada na API não entra: não há o que comparar.
        dcsc = {r["codigo"]: r for r in csv.DictReader(f) if r["latitude"] and r["longitude"]}
    tracados = {}
    for arq in sorted(RIOS.glob("*.geojson")):
        with open(arq, encoding="utf-8") as f:
            tracados[arq.stem] = linhas(json.load(f))
    return estacoes, dcsc, tracados


def ao_rio(lat: float, lon: float, tracado) -> float:
    return min(km(lat, lon, p[1], p[0]) for linha in tracado for p in linha)


def grau(n: float) -> str:
    return f"{n:.4f}".replace(".", ",")


def grau2(n: float) -> str:
    return f"{n:.2f}".replace(".", ",")


def nao_sao_regua(estacoes) -> dict[str, str]:
    """Estações que o cadastro já declarou que NÃO são régua de rio (ex.: DCSC-00178, de altitude)."""
    saida = {}
    for rio in estacoes["rios"].values():
        for e in (rio.get("_topologia") or {}).get("nao_e_regua_de_rio", []):
            saida[e["id"]] = e.get("motivo", "")
    return saida


def inventario(estacoes, dcsc, tracados) -> list[dict]:
    vistas: dict[str, dict] = {}
    excluidas = nao_sao_regua(estacoes)
    for rio_id, rio in estacoes["rios"].items():
        for c in rio["cidades"]:
            if c["id"] in vistas or not c.get("coordenadas"):
                continue
            lat, lon = c["coordenadas"]
            cod = c.get("codigo_dcsc")
            ficha = dcsc.get(cod) if cod else None
            linha = {
                "id": c["id"],
                "nome": c["nome"],
                "rio_tela": rio_id,
                "regua": c.get("regua") or "",
                "lat": lat,
                "lon": lon,
                "codigo": cod,
                "tipo": ficha["tipo"] if ficha else None,
                "dist_ficha_km": km(lat, lon, float(ficha["latitude"]), float(ficha["longitude"])) if ficha else None,
                "sao_da_regua": c.get("coordenadas_sao_da_regua", None),
                "fonte_coord": c.get("coordenadas_fonte"),
                "status_coord": c.get("coordenadas_status"),
                "equivalencia": c.get("equivalencia_estadual"),
                "antes_km": ao_rio(lat, lon, tracados[rio_id]),
                "candidatas": [],
            }
            if not cod:
                for r in dcsc.values():
                    if r["tipo"] != "Hidro" or r["codigo"] in excluidas:
                        continue
                    d = km(lat, lon, float(r["latitude"]), float(r["longitude"]))
                    if d <= RAIO_CANDIDATA_KM:
                        linha["candidatas"].append((r["codigo"], r["nome"], d))
                linha["candidatas"].sort(key=lambda x: x[2])
            vistas[c["id"]] = linha
    return list(vistas.values())


def situacao(l: dict) -> str:
    if l["fonte_coord"]:
        return f"régua confirmada: {l['fonte_coord']}"
    if l["sao_da_regua"] is False:
        return "**aproximada**: coordenada declarada como não sendo a régua; pino no rio"
    if l["codigo"] and l["tipo"] == "Meteo":
        return "**conferir**: o código é de estação de chuva"
    if l["codigo"] and l["dist_ficha_km"] is not None and l["dist_ficha_km"] < 0.05:
        return "confere com a ficha"
    if l["codigo"]:
        return f"**difere da ficha** em {grau2(l['dist_ficha_km'])} km"
    if l.get("status_coord") == "não confirmada":
        return "**coordenada não confirmada** (decisão de 06/10/2026): pino mantido, sem fonte que situe a régua"
    return "sem código: ponto do cadastro, fonte não confirma"


def relatorio(linhas: list[dict], estacoes) -> str:
    out = [
        "# Inventário das réguas do mapa",
        "",
        "Gerado por `scripts/inventario_reguas.py` (não editar à mão). Pedido do Jefferson em 06/10/2026, com a",
        "auditoria visual das 19 cidades do Monitor.",
        "",
        "- **Ficha DCSC:** coordenada da API da Defesa Civil de SC (`data/brutos/dcsc-estacoes-vale-2026-09-13.csv`).",
        "  Só se compara com a ficha do MESMO código.",
        "- **Antes de 06/10:** a quantos km do traçado do rio da tela a régua fica. Era onde o pino caía, porque",
        "  ele era encaixado no traçado. Agora o pino fica na coordenada (ver `pontoDoPino` em `mapaMotor.ts`).",
        "- **Candidata:** estação Hidro da DCSC a até 3 km de cidade sem código (fora as que o cadastro já",
        "  declarou que não são régua, como a DCSC-00178). Não está vinculada e não foi",
        "  usada para mudar nada: só indica onde conferir.",
        "- Na auditoria, nenhuma coordenada mudou. Depois, por decisão do Jefferson (06/10/2026), Blumenau",
        "  passou para a régua da Ponte Adolfo Konder, confirmada pela Prefeitura (`coordenadas_fonte`).",
        "",
        "## Cidades",
        "",
        "| Cidade | Régua no cadastro | Coordenada (lat, lon) | Código | Tipo na DCSC | Distância à ficha | Antes de 06/10 | Situação |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for l in linhas:
        # Com a coordenada de outra fonte, a distância à ficha do código (de chuva, em Blumenau) não diz nada.
        dist = f"{l['dist_ficha_km'] * 1000:.0f} m" if l["dist_ficha_km"] is not None and not l["fonte_coord"] else "—"
        out.append(
            f"| {l['nome']} | {l['regua'] or '—'} | {grau(l['lat'])}, {grau(l['lon'])} | {l['codigo'] or '—'} | "
            f"{l['tipo'] or '—'} | {dist} | {grau2(l['antes_km'])} km | {situacao(l)} |"
        )
    cand = [l for l in linhas if l["candidatas"]]
    if cand:
        out += [
            "",
            "## Cidades sem código: estações estaduais por perto",
            "",
            "Não vincular por proximidade: a régua municipal e a estação estadual podem ser equipamentos",
            "diferentes, com zeros, seções do rio ou referências diferentes. Decisão do Jefferson (06/10/2026):",
            "fica \"não confirmada\" até existir documento, código comum ou comparação de referência/zero da",
            "régua. A equivalência fica em `equivalencia_estadual` no cadastro, e o validador trava o vínculo.",
            "",
            "| Cidade | Estação | Nome na DCSC | Distância | Equivalência |",
            "|---|---|---|---|---|",
        ]
        for l in cand:
            eq = l["equivalencia"] or {}
            for cod, nome, d in l["candidatas"]:
                status = eq.get("status") if eq.get("codigo") == cod else "não registrada"
                out.append(f"| {l['nome']} | {cod} | {nome} | {grau2(d)} km | {status} |")
    sem_cand = [l["nome"] for l in linhas if not l["codigo"] and not l["candidatas"]]
    if sem_cand:
        out += ["", f"Sem estação Hidro da DCSC a até 3 km: {', '.join(sem_cand)}."]
    reguas = [e for e in estacoes.get("estacoes_tempo_real", []) if e.get("lat") is not None and e.get("tipo") != "pluviometro"]
    out += [
        "",
        "## Réguas com coordenada própria (desenhadas no mapa uma a uma)",
        "",
        "| Código | Cidade | Rio | Coordenada (lat, lon) | Fonte da coordenada |",
        "|---|---|---|---|---|",
    ]
    for e in reguas:
        out.append(
            f"| {e.get('codigo') or '—'} | {e.get('cidade') or '—'} | {e.get('rio') or '—'} | "
            f"{grau(e['lat'])}, {grau(e['lon'])} | {e.get('fonte_coordenada') or '—'} |"
        )
    return "\n".join(out) + "\n"


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--gravar", action="store_true", help=f"escreve {SAIDA.relative_to(RAIZ)}")
    args = ap.parse_args()
    estacoes, dcsc, tracados = carregar()
    texto = relatorio(inventario(estacoes, dcsc, tracados), estacoes)
    if args.gravar:
        SAIDA.write_text(texto, encoding="utf-8")
        print(f"gravado: {SAIDA.relative_to(RAIZ)}")
    else:
        print(texto)


if __name__ == "__main__":
    main()
