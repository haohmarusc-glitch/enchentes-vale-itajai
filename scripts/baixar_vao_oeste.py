#!/usr/bin/env python3
"""
Procura no OpenStreetMap o trecho que falta no Itajaí do Oeste, rio abaixo de Taió.

O PROBLEMA (auditoria dos vínculos, 07/10/2026, docs/VINCULOS-DOS-TRACADOS.md)
No bruto `tracado-rios-osm.json` (base OSM de 01/09/2026), o traçado do Oeste tem uma falha de 2,1 km: a via
1207901002 termina em −27,14508, −49,91523 e a 238628752 só começa em −27,14841, −49,89417. As duas se chamam
"Rio Itajaí do Oeste", e a consulta original pedia o rio PELO NOME. Então o pedaço do meio tem outro nome no
OSM, nenhum nome, outra marcação (só a área da água, sem a linha) ou não está mapeado.

O QUE ESTE SCRIPT FAZ
Pede ao Overpass todo curso d'água (`waterway`) numa caixa em volta da falha, sem filtrar por nome, e encadeia
por CONECTIVIDADE, da ponta de montante até a de jusante, como o `baixar_vao_canhanduba.py`. Também lista as
áreas de água da caixa, para o relatório dizer se o rio ali só existe como área.

Antes de gravar, confere:
  - as duas pontas ainda estão soltas no bruto (senão não há falha a fechar);
  - a cadeia liga uma ponta à outra;
  - o comprimento dela é coerente com um rio entre as duas pontas: entre 1 e `SINUOSIDADE_MAX` vezes a
    distância em linha reta. Um caminho muito mais longo é volta por afluente, não o rio.

O QUE ELE NÃO FAZ
Não desenha reta. Sem cadeia que passe nas conferências, nada é gravado e o mapa continua com a falha: uma reta
de 2,1 km seria geografia inventada num mapa de enchente. Não muda o Monitor nem a cor do rio.

Fonte: © OpenStreetMap contributors, ODbL. Roda onde o Overpass responde: no Actions (`baixar-vao-oeste.yml`).

Uso:
    python3 scripts/baixar_vao_oeste.py                         # procura e confere, não grava
    python3 scripts/baixar_vao_oeste.py --gravar --relatorio rodada.json
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "scripts"))

from baixar_tracado_hercilio import base_osm, buscar_consulta  # noqa: E402
from baixar_vao_canhanduba import encadear, m, pontas  # noqa: E402

BRUTO_TRONCO = RAIZ / "data" / "brutos" / "tracado-rios-osm.json"
SAIDA = RAIZ / "data" / "brutos" / "vao-oeste-osm.json"

NOME_OESTE = "Rio Itajaí do Oeste"

#: As duas pontas da falha, (lon, lat), como estão no bruto de 01/09/2026.
PONTA_MONTANTE = (-49.9152338, -27.1450785)   # fim da via 1207901002
PONTA_JUSANTE = (-49.8941659, -27.1484117)    # começo da via 238628752

#: Folga em volta das pontas, em graus (~1,1 km): o rio faz curva para fora da reta entre elas.
FOLGA_GRAUS = 0.01

#: Uma ponta conta como ligada a outra via quando fica a menos disto de uma ponta dela.
TOCA_M = 30.0

#: Comprimento da cadeia sobre a distância em linha reta. Rio de várzea passa de 1,5; acima de 3, a cadeia está
#: dando volta por afluente.
SINUOSIDADE_MAX = 3.0

CONSULTA = """[out:json][timeout:120];
way["waterway"]({sul},{oeste},{norte},{leste});
out geom;
(
  way["natural"="water"]({sul},{oeste},{norte},{leste});
  relation["natural"="water"]({sul},{oeste},{norte},{leste});
  way["waterway"="riverbank"]({sul},{oeste},{norte},{leste});
);
out tags;
"""


def caixa() -> tuple[float, float, float, float]:
    """(sul, oeste, norte, leste) em volta das duas pontas."""
    lons = (PONTA_MONTANTE[0], PONTA_JUSANTE[0])
    lats = (PONTA_MONTANTE[1], PONTA_JUSANTE[1])
    return (round(min(lats) - FOLGA_GRAUS, 5), round(min(lons) - FOLGA_GRAUS, 5),
            round(max(lats) + FOLGA_GRAUS, 5), round(max(lons) + FOLGA_GRAUS, 5))


def consulta() -> str:
    s, o, n, l = caixa()
    return CONSULTA.format(sul=s, oeste=o, norte=n, leste=l)


def ponta_solta(ponto, vias: list[dict]) -> bool:
    """A ponta encosta em exatamente uma via do Oeste (a dela): ninguém continua dali."""
    tocam = sum(1 for v in vias for p in pontas(v) if m(ponto, p) <= TOCA_M)
    return tocam == 1


def falha_aberta(elementos_do_tronco: list[dict]) -> bool:
    """As duas pontas da falha continuam soltas no bruto do tronco."""
    oeste = [e for e in elementos_do_tronco
             if e.get("type") == "way" and (e.get("tags") or {}).get("name") == NOME_OESTE
             and len(e.get("geometry") or []) >= 2]
    return ponta_solta(PONTA_MONTANTE, oeste) and ponta_solta(PONTA_JUSANTE, oeste)


def emenda_gravada_fecha() -> bool:
    """
    O bruto já gravado (`SAIDA`) liga as duas pontas: a falha está fechada no tronco pela emenda.

    O bruto do tronco continua com a falha (é a cópia do OSM de 01/09/2026); quem a fecha é a emenda, que o
    conversor junta pelo ID. Sem esta conferência, cada push que trazia o script para outro branch consultava o
    Overpass de novo, e a rodada ficava vermelha quando o serviço caía (#522, 08/10/2026).
    """
    if not SAIDA.exists():
        return False
    vias = json.loads(SAIDA.read_text(encoding="utf-8")).get("elements") or []
    return bool(encadear([v for v in vias if v.get("geometry")], PONTA_MONTANTE, [PONTA_JUSANTE]))


def comprimento_m(via: dict) -> float:
    g = via["geometry"]
    return sum(m((a["lon"], a["lat"]), (b["lon"], b["lat"])) for a, b in zip(g, g[1:]))


def conferir_cadeia(cadeia: list[dict]) -> tuple[list[str], dict]:
    """(problemas, medidas). Sem problemas, a cadeia pode ser gravada."""
    reta = m(PONTA_MONTANTE, PONTA_JUSANTE)
    if not cadeia:
        return ["nenhuma cadeia de cursos d'água liga as duas pontas dentro da caixa"], {"reta_m": round(reta)}
    total = sum(comprimento_m(v) for v in cadeia)
    sinuosidade = total / reta
    medidas = {
        "reta_m": round(reta),
        "cadeia_m": round(total),
        "sinuosidade": round(sinuosidade, 2),
        "vias": [{"id": v["id"], "waterway": (v.get("tags") or {}).get("waterway"),
                  "name": (v.get("tags") or {}).get("name"), "pontos": len(v["geometry"]),
                  "comprimento_m": round(comprimento_m(v))} for v in cadeia],
    }
    problemas = []
    if sinuosidade < 1.0:
        problemas.append(f"cadeia de {total:.0f} m é mais curta que a reta de {reta:.0f} m: medida errada")
    if sinuosidade > SINUOSIDADE_MAX:
        problemas.append(f"cadeia de {total:.0f} m é {sinuosidade:.1f} vezes a reta (máximo {SINUOSIDADE_MAX}): "
                         "volta por afluente, não é o rio")
    return problemas, medidas


def resumo_da_caixa(elementos: list[dict]) -> dict:
    """O que veio na caixa, para o relatório: cursos por tipo e nome, e áreas de água."""
    linhas = [e for e in elementos if e.get("type") == "way" and e.get("geometry")]
    areas = [e for e in elementos if not e.get("geometry")]
    nome = lambda e: (e.get("tags") or {}).get("name") or "(sem nome)"  # noqa: E731
    return {
        "cursos": len(linhas),
        "cursos_por_tipo": dict(Counter((e.get("tags") or {}).get("waterway") for e in linhas)),
        "cursos_por_nome": dict(Counter(nome(e) for e in linhas).most_common(15)),
        "areas_de_agua": [{"tipo": e.get("type"), "id": e.get("id"), "name": nome(e),
                           "water": (e.get("tags") or {}).get("water")} for e in areas][:20],
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--gravar", action="store_true", help=f"salva a cadeia em {SAIDA.name}")
    ap.add_argument("--relatorio", type=Path, help="grava o resumo da rodada em JSON (o Actions publica)")
    args = ap.parse_args()

    relatorio: dict = {"caixa": caixa(), "ponta_montante": PONTA_MONTANTE, "ponta_jusante": PONTA_JUSANTE}

    def fim(codigo: int, situacao: str) -> int:
        relatorio["situacao"] = situacao
        print(situacao)
        if args.relatorio:
            args.relatorio.write_text(json.dumps(relatorio, ensure_ascii=False, indent=1), encoding="utf-8")
        return codigo

    tronco = json.loads(BRUTO_TRONCO.read_text(encoding="utf-8")).get("elements") or []
    if not falha_aberta(tronco):
        return fim(0, "a falha já não existe no bruto do tronco: nada a procurar")
    if emenda_gravada_fecha():
        return fim(0, f"a falha já está fechada pela emenda gravada em {SAIDA.relative_to(RAIZ)}: nada a procurar")

    tentativas: list = []
    relatorio["tentativas"] = tentativas
    try:
        resposta, espelho = buscar_consulta(consulta(), registro=tentativas)
    except SystemExit as e:
        # Falha do serviço, não da consulta: o relatório sai do mesmo jeito, com cada tentativa.
        return fim(2, f"Overpass sem resposta útil, nada gravado: {str(e).splitlines()[0]}")
    relatorio["espelho"] = espelho
    relatorio["base_osm"] = base_osm(resposta)
    elementos = resposta.get("elements") or []
    relatorio["caixa_tem"] = resumo_da_caixa(elementos)
    print(json.dumps(relatorio["caixa_tem"], ensure_ascii=False, indent=1))

    cadeia = encadear([e for e in elementos if e.get("geometry")], PONTA_MONTANTE, [PONTA_JUSANTE])
    problemas, medidas = conferir_cadeia(cadeia)
    relatorio["cadeia"] = medidas
    relatorio["problemas"] = problemas
    print(json.dumps(medidas, ensure_ascii=False, indent=1))
    if problemas:
        return fim(1, "NÃO gravado: " + "; ".join(problemas))

    if not args.gravar:
        return fim(0, "cadeia conferida; nada gravado (repita com --gravar)")
    SAIDA.write_text(json.dumps({"osm3s": resposta.get("osm3s"), "elements": cadeia}, ensure_ascii=False),
                     encoding="utf-8")
    return fim(0, f"gravado em {SAIDA.relative_to(RAIZ)}: {len(cadeia)} via(s), {medidas['cadeia_m']} m")


if __name__ == "__main__":
    sys.exit(main())
