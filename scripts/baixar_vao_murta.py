#!/usr/bin/env python3
"""
Procura no OpenStreetMap os dois trechos que faltam no Ribeirão da Murta (Itajaí), entre a DC-07 e a foz.

O PROBLEMA (auditoria dos vínculos, 07–08/10/2026, docs/VINCULOS-DOS-TRACADOS.md)
No bruto `tracado-ribeiroes-osm.json` (consulta por NOME, 04/09/2026), o traçado da Murta tem cinco vias, todas
"Ribeirão da Murta", em TRÊS pedaços que não se tocam: a via 138922683 (onde fica a DC-07) termina a 78 m do
começo da 390147234, e essa termina a 38 m do começo da 556881889 — que segue, já ligada às outras duas, até a
foz no Itajaí-Açu, passando pela DC-09. Entre a DC-07 e a foz, só 68 dos 195 vértices eram alcançáveis. Jefferson
(08/10/2026): "destravar a DC-07 exige também conferir a continuidade do traçado e delimitar o trecho do novo
vínculo" — e vínculo de régua só pinta caminho CONTÍNUO em arestas do traçado (`arestasDoAlcance`).

Como as duas falhas têm o tamanho de uma travessia de rua, o provável é que o pedaço do meio seja um bueiro
(`tunnel=culvert`) sem nome, ou com outro nome: a consulta por nome não o trazia.

O QUE ESTE SCRIPT FAZ
Pede ao Overpass todo curso d'água (`waterway`) numa caixa em volta das quatro pontas, sem filtrar por nome, e
encadeia por CONECTIVIDADE cada vão, da ponta de montante à de jusante, como o `baixar_vao_oeste.py`. Aqui o
encadeamento é mais rigoroso que o do Canhanduba: a cadeia só CHEGA quando termina a menos de `TOCA_M` da ponta
de jusante (lá bastavam 100 m, mais que os dois vãos inteiros), e as vias já presentes no bruto dos ribeirões
não servem de emenda (a emenda é o que falta, não o que já está).

Antes de gravar, confere:
  - os dois vãos continuam abertos no bruto dos ribeirões (senão não há o que fechar);
  - as vias da Murta que o Overpass devolve hoje NÃO fecham o vão sozinhas — se fecharem, o OSM foi corrigido e o
    certo é rebaixar o bruto dos ribeirões (docs/tracado-ribeiroes.md), não emendar;
  - a cadeia liga uma ponta à outra;
  - o comprimento dela é coerente com o vão: entre 1 e `SINUOSIDADE_MAX` vezes a reta.

O QUE ELE NÃO FAZ
Não desenha reta: 78 m e 38 m seriam fáceis de "completar", e seriam geografia inventada num mapa de enchente.
Não cria vínculo, não destrava a DC-07 (`alerta_automatico: false`, decisão do Jefferson) e não muda o Monitor.

Fonte: © OpenStreetMap contributors, ODbL. Roda onde o Overpass responde: no Actions (`baixar-vao-murta.yml`).

Uso:
    python3 scripts/baixar_vao_murta.py                         # procura e confere, não grava
    python3 scripts/baixar_vao_murta.py --gravar --relatorio rodada.json
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "scripts"))

from baixar_tracado_hercilio import base_osm, buscar_consulta  # noqa: E402
from baixar_vao_canhanduba import m, pontas  # noqa: E402

BRUTO_RIBEIROES = RAIZ / "data" / "brutos" / "tracado-ribeiroes-osm.json"
SAIDA = RAIZ / "data" / "brutos" / "vao-murta-osm.json"

NOME_MURTA = "Ribeirão da Murta"


@dataclass(frozen=True)
class Vao:
    """Uma falha do traçado: a via que termina antes dela e a que começa depois, com as duas pontas (lon, lat)."""

    nome: str
    via_montante: int
    via_jusante: int
    montante: tuple[float, float]
    jusante: tuple[float, float]


#: Os dois vãos, como estão no bruto dos ribeirões de 04/09/2026 (medidos em 08/10/2026).
VAOS = (
    Vao("vao-1", 138922683, 390147234, (-48.720949, -26.89213), (-48.720167, -26.892064)),   # 78 m
    Vao("vao-2", 390147234, 556881889, (-48.716999, -26.891344), (-48.71671, -26.891114)),   # 38 m
)

#: Folga em volta das pontas, em graus (~550 m): os vãos têm dezenas de metros, a caixa não precisa de mais.
FOLGA_GRAUS = 0.005

#: Uma ponta conta como ligada a outra via quando fica a menos disto de uma ponta dela — e a cadeia só CHEGA quando
#: a última via termina a menos disto da ponta de jusante. Os vãos têm 78 e 38 m: um alvo de 100 m aceitaria uma via
#: que parasse no meio.
TOCA_M = 30.0

#: Comprimento da cadeia sobre a reta. Travessia de rua é quase reta; acima de 3, a cadeia está dando volta.
SINUOSIDADE_MAX = 3.0

#: Quanto a cadeia pode ficar aquém da reta por arredondamento das pontas (1ª rodada, 08/10/2026: o bueiro de 38 m
#: saiu 38,45 m contra uma reta de 38,45 m e foi recusado por 0,3 mm).
TOLERANCIA_M = 1.0

CONSULTA = """[out:json][timeout:120];
way["waterway"]({sul},{oeste},{norte},{leste});
out geom;
(
  way["natural"="water"]({sul},{oeste},{norte},{leste});
  relation["natural"="water"]({sul},{oeste},{norte},{leste});
);
out tags;
"""


def caixa() -> tuple[float, float, float, float]:
    """(sul, oeste, norte, leste) em volta das quatro pontas."""
    pts = [p for v in VAOS for p in (v.montante, v.jusante)]
    lons = [p[0] for p in pts]
    lats = [p[1] for p in pts]
    return (round(min(lats) - FOLGA_GRAUS, 5), round(min(lons) - FOLGA_GRAUS, 5),
            round(max(lats) + FOLGA_GRAUS, 5), round(max(lons) + FOLGA_GRAUS, 5))


def consulta() -> str:
    s, o, n, l = caixa()
    return CONSULTA.format(sul=s, oeste=o, norte=n, leste=l)


def vias_da_murta(elementos: list[dict]) -> list[dict]:
    return [e for e in elementos
            if e.get("type") == "way" and (e.get("tags") or {}).get("name") == NOME_MURTA
            and len(e.get("geometry") or []) >= 2]


def ponta_solta(ponto, vias: list[dict]) -> bool:
    """A ponta encosta em exatamente uma via da Murta (a dela): ninguém continua dali."""
    tocam = sum(1 for v in vias for p in pontas(v) if m(ponto, p) <= TOCA_M)
    return tocam == 1


def vao_aberto(vao: Vao, vias_murta: list[dict]) -> bool:
    """As duas pontas do vão continuam soltas entre as vias da Murta dadas."""
    return ponta_solta(vao.montante, vias_murta) and ponta_solta(vao.jusante, vias_murta)


def vaos_abertos(elementos: list[dict]) -> list[Vao]:
    vias = vias_da_murta(elementos)
    return [v for v in VAOS if vao_aberto(v, vias)]


def fechado_pela_murta(vao: Vao, elementos: list[dict]) -> bool:
    """
    As vias chamadas "Ribeirão da Murta" nestes elementos (o OSM de hoje) já ligam as duas pontas do vão.

    Aí não há emenda a gravar: o ribeirão foi corrigido no OSM e o certo é rebaixar o bruto dos ribeirões. Uma via
    de outro nome (ou sem nome) ligando as pontas não conta aqui — essa é a emenda.
    """
    return bool(encadear(vias_da_murta(elementos), vao.montante, vao.jusante))


def ids_do_bruto(elementos: list[dict]) -> set[int]:
    return {e["id"] for e in elementos if e.get("type") == "way" and "id" in e}


def encadear(elementos: list[dict], origem, alvo, *, excluir: set[int] = frozenset()) -> list[dict]:
    """
    Caminho por CONECTIVIDADE da ponta de montante à de jusante, em vias que NÃO estão em `excluir`.

    Busca em largura: duas vias se ligam quando uma extremidade de uma está a menos de `TOCA_M` de uma extremidade
    da outra, e a cadeia chega quando a extremidade livre da última via está a menos de `TOCA_M` do alvo. Devolve
    a menor cadeia que chega — ou lista vazia, e aí NÃO se inventa o vão.
    """
    vias = [e for e in elementos
            if e.get("type") == "way" and len(e.get("geometry") or []) >= 2 and e.get("id") not in excluir]
    fila: list[tuple[tuple[float, float], list[dict]]] = [(origem, [])]
    vistas: set[int] = set()
    while fila:
        ponto, rota = fila.pop(0)
        for v in vias:
            if v["id"] in vistas:
                continue
            a, b = pontas(v)
            if m(ponto, a) <= TOCA_M:
                prox = b
            elif m(ponto, b) <= TOCA_M:
                prox = a
            else:
                continue
            vistas.add(v["id"])
            nova = rota + [v]
            if m(prox, alvo) <= TOCA_M:
                return nova
            fila.append((prox, nova))
    return []


def emenda_gravada_fecha(vao: Vao) -> bool:
    """
    O bruto já gravado (`SAIDA`) liga as duas pontas deste vão: a falha está fechada pela emenda.

    O bruto dos ribeirões continua com os vãos (é a cópia do OSM de 04/09/2026); quem os fecha é a emenda, que o
    conversor junta pelo ID. Sem esta conferência, cada push que trouxesse o script consultaria o Overpass de novo.
    """
    if not SAIDA.exists():
        return False
    vias = json.loads(SAIDA.read_text(encoding="utf-8")).get("elements") or []
    return bool(encadear([v for v in vias if v.get("geometry")], vao.montante, vao.jusante))


def nome_da_saida() -> str:
    """O caminho da emenda para as mensagens, relativo ao repositório quando está nele."""
    try:
        return str(SAIDA.relative_to(RAIZ))
    except ValueError:
        return str(SAIDA)


def comprimento_m(via: dict) -> float:
    g = via["geometry"]
    return sum(m((a["lon"], a["lat"]), (b["lon"], b["lat"])) for a, b in zip(g, g[1:]))


def conferir_cadeia(vao: Vao, cadeia: list[dict]) -> tuple[list[str], dict]:
    """(problemas, medidas). Sem problemas, a cadeia pode ser gravada."""
    reta = m(vao.montante, vao.jusante)
    if not cadeia:
        return [f"{vao.nome}: nenhuma cadeia de cursos d'água liga as duas pontas dentro da caixa"], {"reta_m": round(reta)}
    total = sum(comprimento_m(v) for v in cadeia)
    sinuosidade = total / reta
    medidas = {
        "reta_m": round(reta),
        "cadeia_m": round(total),
        "sinuosidade": round(sinuosidade, 2),
        "vias": [{"id": v["id"], "waterway": (v.get("tags") or {}).get("waterway"),
                  "name": (v.get("tags") or {}).get("name"), "tunnel": (v.get("tags") or {}).get("tunnel"),
                  "pontos": len(v["geometry"]), "comprimento_m": round(comprimento_m(v))} for v in cadeia],
    }
    problemas = []
    # As pontas de `VAOS` estão arredondadas à sexta casa (~0,1 m): uma via reta entre os mesmos nós sai alguns
    # centímetros "mais curta" que a reta. Só é medida errada quando falta mais que `TOLERANCIA_M`.
    if total < reta - TOLERANCIA_M:
        problemas.append(f"{vao.nome}: cadeia de {total:.1f} m é mais curta que a reta de {reta:.1f} m: medida errada")
    if sinuosidade > SINUOSIDADE_MAX:
        problemas.append(f"{vao.nome}: cadeia de {total:.0f} m é {sinuosidade:.1f} vezes a reta "
                         f"(máximo {SINUOSIDADE_MAX}): volta por outro curso, não é o ribeirão")
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
        "tuneis": sum(1 for e in linhas if (e.get("tags") or {}).get("tunnel")),
        "areas_de_agua": [{"tipo": e.get("type"), "id": e.get("id"), "name": nome(e),
                           "water": (e.get("tags") or {}).get("water")} for e in areas][:20],
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--gravar", action="store_true", help=f"salva as cadeias conferidas em {SAIDA.name}")
    ap.add_argument("--relatorio", type=Path, help="grava o resumo da rodada em JSON (o Actions publica)")
    args = ap.parse_args()

    relatorio: dict = {"caixa": caixa(),
                       "vaos": [{"nome": v.nome, "via_montante": v.via_montante, "via_jusante": v.via_jusante,
                                 "montante": v.montante, "jusante": v.jusante} for v in VAOS]}

    def fim(codigo: int, situacao: str) -> int:
        relatorio["situacao"] = situacao
        print(situacao)
        if args.relatorio:
            args.relatorio.write_text(json.dumps(relatorio, ensure_ascii=False, indent=1), encoding="utf-8")
        return codigo

    ribeiroes = json.loads(BRUTO_RIBEIROES.read_text(encoding="utf-8")).get("elements") or []
    abertos = [v for v in vaos_abertos(ribeiroes) if not emenda_gravada_fecha(v)]
    relatorio["vaos_abertos"] = [v.nome for v in abertos]
    if not abertos:
        return fim(0, "nenhum vão aberto: o bruto dos ribeirões ou a emenda gravada em "
                      f"{nome_da_saida()} já ligam as pontas; nada a procurar")

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

    # O OSM de hoje pode já ter corrigido o ribeirão: aí a resposta é rebaixar o bruto dos ribeirões, não emendar.
    corrigidos = [v.nome for v in abertos if fechado_pela_murta(v, elementos)]
    relatorio["fechados_no_osm_de_hoje"] = corrigidos
    if corrigidos:
        return fim(1, f"NÃO gravado: as vias da Murta no OSM de hoje já fecham {', '.join(corrigidos)}; "
                      "rebaixe data/brutos/tracado-ribeiroes-osm.json (docs/tracado-ribeiroes.md) em vez de emendar")

    ja_no_bruto = ids_do_bruto(ribeiroes)
    cadeias: dict[str, list[dict]] = {}
    problemas: list[str] = []
    relatorio["cadeias"] = {}
    for vao in abertos:
        cadeia = encadear([e for e in elementos if e.get("geometry")], vao.montante, vao.jusante, excluir=ja_no_bruto)
        probs, medidas = conferir_cadeia(vao, cadeia)
        relatorio["cadeias"][vao.nome] = medidas
        print(vao.nome, json.dumps(medidas, ensure_ascii=False, indent=1))
        if probs:
            problemas.extend(probs)
        else:
            cadeias[vao.nome] = cadeia
    relatorio["problemas"] = problemas

    if not args.gravar:
        return fim(1 if problemas else 0,
                   ("cadeias conferidas; nada gravado (repita com --gravar)" if not problemas
                    else "NÃO gravado: " + "; ".join(problemas)))
    if not cadeias:
        return fim(1, "NÃO gravado: " + "; ".join(problemas))

    # Grava o que fechou — a emenda de um vão vale mesmo que o outro siga aberto —, e a rodada fica vermelha se
    # algum vão ficou aberto, para ninguém ler "verde" como "contínuo".
    vias_gravadas: dict[int, dict] = {}
    if SAIDA.exists():
        for v in json.loads(SAIDA.read_text(encoding="utf-8")).get("elements") or []:
            vias_gravadas[v["id"]] = v
    for cadeia in cadeias.values():
        for v in cadeia:
            vias_gravadas[v["id"]] = v
    SAIDA.write_text(json.dumps({"osm3s": resposta.get("osm3s"), "elements": list(vias_gravadas.values())},
                                ensure_ascii=False), encoding="utf-8")
    gravado = f"gravado em {nome_da_saida()}: {', '.join(cadeias)} ({len(vias_gravadas)} via(s))"
    if problemas:
        return fim(1, gravado + "; ainda aberto: " + "; ".join(problemas))
    return fim(0, gravado)


if __name__ == "__main__":
    sys.exit(main())
