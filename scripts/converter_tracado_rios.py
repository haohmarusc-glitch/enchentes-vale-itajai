#!/usr/bin/env python3
"""
Converte o traçado dos rios (bruto do OpenStreetMap, via Overpass) em GeoJSON
para o mapa geográfico do site.

ENTRADA  data/brutos/tracado-rios-osm.json — resposta `out geom;` do Overpass,
         com os ways de `waterway=river` nomeados. Baixado na VPS (o egress do
         ambiente de dev não alcança o Overpass); a query está no próprio bruto
         pela procedência, e o comando fica em docs/.
SAÍDA    data/rios/itajai-acu.geojson e itajai-mirim.geojson — um MultiLineString
         por rio, em [lon, lat] (ordem GeoJSON), com atribuição ODbL.

POR QUE JUNTAR OESTE COM AÇU
----------------------------
No OSM, a calha principal do Açu troca de nome na confluência de Rio do Sul: a
montante dela chama-se "Rio Itajaí do Oeste" (a vinda de Taió). Para a linha do
mapa cobrir o diagrama inteiro (Taió → foz), o Açu do site é os dois juntos. O
Itajaí do Sul (de Ituporanga) é a OUTRA cabeceira e fica de fora por enquanto:
o diagrama do Açu segue o eixo Taió → Rio do Sul.

Uso:
    python3 scripts/converter_tracado_rios.py
"""

import json
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
BRUTO = RAIZ / "data/brutos/tracado-rios-osm.json"

#: Bruto OPCIONAL e SEPARADO, com os cursos menores de Itajaí.
#:
#: Separado de propósito: o `tracado-rios-osm.json` já produz um tronco
#: conferido (as sete réguas que caem nele estão a menos de 0,2 km), e
#: rebaixá-lo para acrescentar ribeirão arriscaria mexer no que já está certo
#: por causa do que ainda falta. Este arquivo só ALIMENTA os afluentes
#: opcionais; some sem quebrar nada.
#:
#: A consulta do Overpass está em `docs/tracado-ribeiroes.md`.
BRUTO_RIBEIROES = RAIZ / "data/brutos/tracado-ribeiroes-osm.json"

#: Bruto do VÃO do Canhanduba — o trecho final até o Mirim.
#:
#: Existe porque a busca por NOME não o alcançava: medido em 04/09/2026, o
#: traçado do Canhanduba morria a 578 m do Mirim, e o pedaço que falta chama-se
#: **Rio Conceição** no OSM. `baixar_vao_canhanduba.py` o achou por
#: CONECTIVIDADE (650 m de canal para 578 m em linha reta — sinuosidade 1,12,
#: normal em várzea; se a cadeia estivesse vagando, seria muito mais longa).
#:
#: Entra como rio PRÓPRIO, não fundido ao Canhanduba: o OSM lhe dá outro nome, e
#: juntar os dois faria o arquivo afirmar que 650 m de Rio Conceição são
#: Canhanduba. Desenhados lado a lado eles se tocam, a água chega ao Mirim na
#: tela, e nenhum dos dois diz ser o outro.
BRUTO_VAO_CANHANDUBA = RAIZ / "data/brutos/vao-canhanduba-osm.json"
SAIDA = RAIZ / "data/rios"

ATRIBUICAO = "© OpenStreetMap contributors, ODbL (openstreetmap.org/copyright)"

#: Tronco do site e os nomes de way do OSM que o compõem — match EXATO, e
#: OBRIGATÓRIO (aborta se faltar: um rio pela metade enganaria o mapa).
RIOS = {
    "itajai-acu": ["Rio Itajaí do Oeste", "Rio Itajaí-Açu"],
    "itajai-mirim": ["Rio Itajaí-Mirim"],
}

#: Afluentes do tronco — necessários para scripts/achar_confluencias.py achar
#: onde Benedito e Luís Alves entram. OPCIONAIS: o bruto só os tem se a query do
#: Overpass os incluir (ver docs/fontes-tempo-real.md). Match por SUBSTRING em
#: minúsculas, tolerante à grafia do OSM (Luiz/Luís, acento). Se não achar nada,
#: pula com aviso — nunca emite um afluente vazio nem aborta o tronco.
RIOS_AFLUENTES = {
    "benedito": ["rio benedito"],
    "luiz-alves": ["rio luiz alves", "rio luís alves"],
    "hercilio": ["rio hercílio", "rio hercilio"],
    # Os cursos de ITAJAÍ que carregam régua e não estavam no mapa. Medido em
    # 04/09/2026 (scripts/conferir_reguas_no_tracado.py): sem eles, DC-07 fica a
    # 2,25 km, DC-09 a 0,87 km e DC-08 a 4,41 km do traçado mais próximo — os
    # pinos flutuavam fora de qualquer rio. São `waterway=stream`/`canal` no
    # OSM, e a consulta original só pediu `waterway=river`: por isso faltavam.
    "ribeirao-murta": ["ribeirão da murta", "ribeirao da murta"],
    "ribeirao-canhanduba": [
        "ribeirão da canhanduba", "ribeirao da canhanduba",
        "rio canhanduba", "rio do meio",
    ],
    # O canal retificado do Mirim, onde fica a DC-03 (SEMASA), hoje a 2,32 km do
    # traçado. Fica em id próprio, e não fundido ao Mirim, porque é obra: o
    # curso antigo continua existindo ao lado (DC-05 e DC-06 estão nele), e
    # juntar os dois numa linha só apagaria essa distinção — que o cadastro faz
    # questão de manter no título de cada régua.
    "mirim-canal-retificado": ["canal retificado", "canal do itajaí-mirim"],
    # O trecho que liga o Canhanduba ao Mirim. Ver BRUTO_VAO_CANHANDUBA.
    "rio-conceicao": ["rio conceição", "rio conceicao"],
}


def ways_por_nome(elementos: list[dict]) -> dict[str, list[dict]]:
    por_nome: dict[str, list[dict]] = {}
    for e in elementos:
        if e.get("type") != "way" or "geometry" not in e:
            continue
        nome = (e.get("tags") or {}).get("name")
        if nome:
            por_nome.setdefault(nome, []).append(e)
    return por_nome


def linha_do_way(way: dict) -> list[list[float]]:
    """Geometria de um way em [lon, lat] (GeoJSON), como o OSM devolve em lat/lon."""
    return [[p["lon"], p["lat"]] for p in way["geometry"]
            if isinstance(p.get("lon"), (int, float)) and isinstance(p.get("lat"), (int, float))]


def linhas_por_substring(elementos: list[dict], chaves: list[str]) -> list[list[list[float]]]:
    """Ways cujo `name` (minúsculo) contém alguma das chaves — para afluentes."""
    linhas = []
    for e in elementos:
        if e.get("type") != "way" or "geometry" not in e:
            continue
        nome = ((e.get("tags") or {}).get("name") or "").lower()
        if any(c in nome for c in chaves):
            linha = linha_do_way(e)
            if len(linha) >= 2:
                linhas.append(linha)
    return linhas


def feature_do_rio(rio_id: str, linhas: list[list[list[float]]]) -> dict:
    return {
        "type": "Feature",
        "properties": {"rio": rio_id, "fonte": ATRIBUICAO, "trechos": len(linhas)},
        "geometry": {"type": "MultiLineString", "coordinates": linhas},
    }


def geojson_do_rio(rio_id: str, nomes: list[str], por_nome: dict[str, list[dict]]) -> dict:
    linhas = []
    faltando = []
    for nome in nomes:
        ways = por_nome.get(nome) or []
        if not ways:
            faltando.append(nome)
        for w in ways:
            linha = linha_do_way(w)
            if len(linha) >= 2:
                linhas.append(linha)
    if faltando:
        # Nome esperado que não veio: o bruto mudou ou a query pegou coisa
        # diferente. Grita, não emite um rio pela metade em silêncio.
        raise SystemExit(f"{rio_id}: nomes ausentes no bruto: {faltando}")
    return {
        "type": "Feature",
        "properties": {
            "rio": rio_id,
            "fonte": ATRIBUICAO,
            "trechos": len(linhas),
        },
        "geometry": {"type": "MultiLineString", "coordinates": linhas},
    }


def main() -> int:
    if not BRUTO.exists():
        raise SystemExit(f"falta o bruto {BRUTO} — baixe na VPS (ver docs)")
    dados = json.loads(BRUTO.read_text(encoding="utf-8"))
    por_nome = ways_por_nome(dados.get("elements") or [])
    elementos = dados.get("elements") or []

    # O bruto dos ribeirões entra SÓ na busca por substring (afluentes
    # opcionais). O tronco continua saindo do bruto conferido, intocado.
    for extra_caminho, oque in ((BRUTO_RIBEIROES, "ribeirões de Itajaí"),
                                (BRUTO_VAO_CANHANDUBA, "vão do Canhanduba")):
        if extra_caminho.exists():
            extra = json.loads(extra_caminho.read_text(encoding="utf-8"))
            n = len(extra.get("elements") or [])
            elementos = elementos + (extra.get("elements") or [])
            print(f"bruto ({oque}): +{n} elemento(s) de {extra_caminho.name}")
        else:
            print(f"sem {extra_caminho.name} — {oque} fica de fora "
                  "(ver docs/tracado-ribeiroes.md para baixar na VPS)")

    SAIDA.mkdir(parents=True, exist_ok=True)

    def grava(feat: dict, rio_id: str) -> None:
        destino = SAIDA / f"{rio_id}.geojson"
        destino.write_text(json.dumps(feat, ensure_ascii=False) + "\n", encoding="utf-8")
        pts = sum(len(l) for l in feat["geometry"]["coordinates"])
        print(f"{rio_id}: {feat['properties']['trechos']} trechos, {pts} pontos -> {destino.name}")

    for rio_id, nomes in RIOS.items():   # tronco: obrigatório
        grava(geojson_do_rio(rio_id, nomes, por_nome), rio_id)

    for rio_id, chaves in RIOS_AFLUENTES.items():   # afluentes: opcional
        linhas = linhas_por_substring(elementos, chaves)
        if not linhas:
            print(f"{rio_id}: nenhum way com {chaves} no bruto — pulado. Inclua o rio na "
                  "query do Overpass (docs/fontes-tempo-real.md) e rebaixe o bruto.")
            continue
        grava(feature_do_rio(rio_id, linhas), rio_id)
    return 0


if __name__ == "__main__":
    sys.exit(main())
