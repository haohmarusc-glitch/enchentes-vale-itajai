#!/usr/bin/env python3
"""
Baixa do OpenStreetMap o traçado do Rio Luiz Alves, o afluente que o Açu recebe em Ilhota.

POR QUE (pendência do README, "Ponto exato onde o Luís Alves entra"). `_topologia.afluentes_rios` diz que o
Luís Alves entra perto de Ilhota, mas "antes ou depois da régua de Ilhota" está "a confirmar por coordenada".
`achar_confluencias.py` responde isso por geometria, e só precisa do `data/rios/luiz-alves.geojson`, que
nunca foi baixado: a consulta original do tronco não pediu o afluente.

O QUE CONFERE ANTES DE GRAVAR
  - veio algum way com um dos nomes (o OSM escreve Luiz, Luís ou Luis);
  - o traçado chega ao Açu: alguma ponta a menos de `CHEGA_AO_ACU_KM` do tronco desenhado;
  - não é um pedaço só: pelo menos `COMPRIMENTO_MIN_KM` de rio.
Não confere régua de cidade: o Luiz Alves não tem régua no cadastro. Por isso ele NÃO ganha cor nem vínculo;
é desenhado em cinza, como todo curso sem vínculo (docs/VINCULOS-DOS-TRACADOS.md).

Gravado, `converter_tracado_rios.py` gera `data/rios/luiz-alves.geojson` (recortado na caixa do mapa) e
`achar_confluencias.py` mede a entrada. Fonte: © OpenStreetMap contributors, ODbL. Roda onde o Overpass
responde: no Actions (`baixar-tracado-luiz-alves.yml`).

Uso:
    python3 scripts/baixar_tracado_luiz_alves.py                    # baixa e confere, não grava
    python3 scripts/baixar_tracado_luiz_alves.py --gravar --relatorio rodada.json
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "scripts"))

from baixar_tracado_hercilio import (  # noqa: E402
    DECISOES, base_do_arquivo, base_osm, buscar_consulta, comparar_bases, comprimento_km, km, tracado,
)

SAIDA = RAIZ / "data" / "brutos" / "tracado-luiz-alves-osm.json"

NOMES = ("Rio Luiz Alves", "Rio Luís Alves", "Rio Luis Alves")

#: (sul, oeste, norte, leste): o município de Luiz Alves e a chegada ao Açu em Ilhota, com folga.
CAIXA = (-27.00, -49.20, -26.55, -48.70)

CHEGA_AO_ACU_KM = 1.0
COMPRIMENTO_MIN_KM = 5.0


def consulta() -> str:
    s, o, n, l = CAIXA
    nomes = "|".join(NOMES)
    return (f'[out:json][timeout:120];\nway["waterway"~"^(river|stream)$"]["name"~"^({nomes})$"]'
            f"({s},{o},{n},{l});\nout geom;")


def linhas(elementos: list[dict]) -> dict[str, list[list[tuple[float, float]]]]:
    """Linhas do rio, por nome do way."""
    por_nome: dict[str, list] = {}
    for e in elementos:
        nome = (e.get("tags") or {}).get("name")
        if e.get("type") != "way" or nome not in NOMES:
            continue
        pts = [(p["lon"], p["lat"]) for p in e.get("geometry") or []
               if isinstance(p.get("lon"), (int, float)) and isinstance(p.get("lat"), (int, float))]
        if len(pts) >= 2:
            por_nome.setdefault(nome, []).append(pts)
    return por_nome


def conferir(por_nome: dict[str, list], acu: list[tuple[float, float]]) -> list[str]:
    """Problemas que impedem gravar. Lista vazia = pode gravar."""
    todas = [l for ls in por_nome.values() for l in ls]
    if not todas:
        return [f"não veio nenhum way chamado {' / '.join(NOMES)}"]
    problemas = []
    total = comprimento_km(todas)
    if total < COMPRIMENTO_MIN_KM:
        problemas.append(f"só {total:.1f} km de rio (mínimo {COMPRIMENTO_MIN_KM} km): pedaço, não o rio")
    if not acu:
        problemas.append("falta data/rios/itajai-acu.geojson para conferir a chegada")
    else:
        d = min(km(p, q) for l in todas for p in (l[0], l[-1]) for q in acu)
        if d > CHEGA_AO_ACU_KM:
            problemas.append(f"não chega ao Açu: a ponta mais perto fica a {d:.2f} km (limite {CHEGA_AO_ACU_KM} km)")
    return problemas


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--gravar", action="store_true", help=f"grava {SAIDA.relative_to(RAIZ)} se passar")
    ap.add_argument("--relatorio", type=Path, help="grava o resumo da rodada em JSON (o Actions publica)")
    a = ap.parse_args()
    relatorio: dict = {"caixa": CAIXA, "nomes": NOMES}

    def fim(codigo: int, situacao: str) -> int:
        relatorio["situacao"] = situacao
        print(situacao)
        if a.relatorio:
            a.relatorio.write_text(json.dumps(relatorio, ensure_ascii=False, indent=1), encoding="utf-8")
        return codigo

    tentativas: list[dict] = []
    relatorio["tentativas"] = tentativas
    try:
        resposta, espelho = buscar_consulta(consulta(), registro=tentativas, arquivo=SAIDA)
    except SystemExit as e:
        return fim(2, f"Overpass sem resposta útil, nada gravado: {str(e).splitlines()[0]}")
    relatorio["espelho"], relatorio["base_osm"] = espelho, base_osm(resposta)

    por_nome = linhas(resposta.get("elements") or [])
    relatorio["por_nome"] = {n: {"ways": len(ls), "km": round(comprimento_km(ls), 1)} for n, ls in por_nome.items()}
    print(json.dumps(relatorio["por_nome"], ensure_ascii=False))
    problemas = conferir(por_nome, tracado("itajai-acu"))
    relatorio["problemas"] = problemas
    if problemas:
        return fim(1, "RECUSADO: " + "; ".join(problemas))

    grava, efeito = DECISOES[comparar_bases(base_osm(resposta), base_do_arquivo(SAIDA), SAIDA.exists())]
    if not a.gravar:
        return fim(0, f"conferido; nada gravado (repita com --gravar). Arquivo: {efeito}")
    if not grava:
        return fim(0, f"conferido; {efeito}")
    resposta["_consulta"] = {
        "overpass": consulta(),
        "espelho": espelho,
        "base_osm": base_osm(resposta),
        "baixado_em": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "script": "scripts/baixar_tracado_luiz_alves.py",
    }
    SAIDA.write_text(json.dumps(resposta, ensure_ascii=False) + "\n", encoding="utf-8")
    return fim(0, f"gravado em {SAIDA.relative_to(RAIZ)} ({efeito})")


if __name__ == "__main__":
    sys.exit(main())
