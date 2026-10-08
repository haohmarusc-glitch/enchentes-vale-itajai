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
import pathlib
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

#: Bruto da Defesa Civil de RIO DO SUL (API Asthon), com dez cursos em GeoJSON.
#:
#: Existe porque o Itajaí do SUL — a cabeceira que se junta a Taió em Rio do Sul
#: — NÃO ESTAVA NO MAPA, achado em 05/09/2026. A causa tem duas camadas, e as
#: duas são a mesma omissão: a consulta original do Overpass não pediu o Sul (o
#: `tracado-rios-osm.json` tem 50 ways do Oeste e ZERO do Sul), e o `RIOS` aqui
#: só listava Oeste e Açu. Resultado na tela: Ituporanga e a Barragem Sul
#: flutuando a 28 e 31 km de qualquer linha, e a linha que passa perto delas
#: sendo o OESTE — o mapa sugerindo Taió -> Ituporanga -> Rio do Sul EM SÉRIE,
#: que é a fila que este projeto desmontou nos dados.
#:
#: ⚠️ COBERTURA MUNICIPAL, e por isso PARCIAL: são 10,5 km perto de Rio do Sul,
#: e a ponta de montante ainda fica a 21,4 km de Ituporanga. Desenha a
#: CONFLUÊNCIA (duas cabeceiras chegando, que é o que a tela precisa afirmar) e
#: não desenha o trecho de Ituporanga até lá. Completar pelo Overpass:
#:     way["waterway"]["name"~"Itajaí do Sul",i](-27.60,-49.75,-27.15,-49.45);
#: Ver docs/TRACADO-ITAJAI-DO-SUL.md.
BRUTO_RIO_DO_SUL = RAIZ / "data/brutos/rio-do-sul-rios-tracados.geojson"

#: Bruto do RIO HERCÍLIO (Itajaí do Norte), o rio de Ibirama. Baixado por
#: `baixar_tracado_hercilio.py`, que só grava depois de conferir que o traçado
#: chega ao Açu e passa pelo pino de Ibirama. Opcional, como os ribeirões.
BRUTO_HERCILIO = RAIZ / "data/brutos/tracado-hercilio-osm.json"
#: Brutos do BENEDITO (Timbó), do ITAJAÍ DO SUL (Ituporanga) e do TROMBUDO (Trombudo Central), baixados por
#: `baixar_tracados_afluentes.py` (pedido do Jefferson, 06/10/2026), que só grava o rio que chega a um rio
#: desenhado e passa pela régua da cidade. Opcionais: sem o arquivo, o rio fica de fora. O Itajaí do Sul do
#: OSM, quando existe, SUBSTITUI o da Asthon (10,5 km perto de Rio do Sul).
BRUTOS_AFLUENTES = {
    "benedito": RAIZ / "data/brutos/tracado-benedito-osm.json",
    "itajai-do-sul": RAIZ / "data/brutos/tracado-itajai-do-sul-osm.json",
    "trombudo": RAIZ / "data/brutos/tracado-trombudo-osm.json",
    "rio-dos-cedros": RAIZ / "data/brutos/tracado-rio-dos-cedros-osm.json",
    "guabiruba": RAIZ / "data/brutos/tracado-guabiruba-osm.json",
    # O afluente que o Açu recebe em Ilhota (`baixar_tracado_luiz_alves.py`): só para achar a confluência.
    "luiz-alves": RAIZ / "data/brutos/tracado-luiz-alves-osm.json",
}
#: Brutos dos cursos d'água COM NOME que passam por um município
#: (`baixar_rios_municipio.py`, `data/brutos/rios-<municipio>-osm.json`). Cada
#: nome vira um arquivo próprio — como o Rio Conceição, nenhum se funde a outro.
#: Os nomes que o tronco ou um afluente já desenham são pulados. Pedido do
#: Jefferson (05/10/2026): os rios que passam por Ibirama no Monitor.
BRUTOS_MUNICIPIOS = sorted((RAIZ / "data/brutos").glob("rios-*-osm.json"))
SAIDA = RAIZ / "data/rios"

ATRIBUICAO = "© OpenStreetMap contributors, ODbL (openstreetmap.org/copyright)"

#: O bruto de Rio do Sul não é OSM: é da Defesa Civil do município, pela API
#: Asthon. Fonte diferente, crédito diferente — não herda a atribuição do OSM.
ATRIBUICAO_ASTHON = "Defesa Civil de Rio do Sul (API Asthon), captura de 04/09/2026"

#: Cursos que saem do bruto de Rio do Sul, por nome EXATO do campo `nome`.
#: Só o Sul: o Oeste e o Açu já vêm do OSM, com cobertura muito maior (o Oeste
#: do OSM alcança Taió; o da Asthon morre a 30 km dela).
RIOS_DE_RIO_DO_SUL = {"itajai-do-sul": "Rio Itajaí do Sul"}

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
    # O mesmo rio com DOIS nomes no OSM: "Rio Itajaí do Norte" a montante
    # (José Boiteux) e "Rio Hercílio" a jusante (Ibirama até o Açu). A ANA o
    # cadastra como um só, "Rio Itajaí do Norte ou Hercílio" — por isso os dois
    # cabem no mesmo arquivo, ao contrário do Rio Conceição. Pedir só Hercílio
    # deixava o rio sem montante (05/10/2026).
    "hercilio": ["rio hercílio", "rio hercilio", "rio itajaí do norte", "rio itajai do norte"],
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
    # A cabeceira do Sul inteira, do OSM (BRUTOS_AFLUENTES). Sem o bruto, fica a da Asthon.
    "itajai-do-sul": ["rio itajaí do sul", "rio itajai do sul"],
    # O rio de Trombudo Central (BRUTOS_AFLUENTES). Desenhá-lo NÃO dá posição na árvore à cidade: a
    # confluência é geometria do OSM, e a árvore só muda com fonte (docs/TOPOLOGIA-CANONICA.md).
    "trombudo": ["rio trombudo"],
    # O rio da cidade de Rio dos Cedros, que chega ao Benedito em Timbó (BRUTOS_AFLUENTES).
    "rio-dos-cedros": ["rio dos cedros"],
    # O curso que a DCSC-00029 mede em Guabiruba, até o Mirim em Brusque (BRUTOS_AFLUENTES): o "Rio Guabiruba
    # Norte", onde fica a estação, e o "Rio Guabiruba", que nasce do encontro dele com o Sul. NOME EXATO
    # (NOMES_EXATOS): por substring, "rio guabiruba" pegaria também o Sul, que não é o curso da estação.
    "guabiruba": ["rio guabiruba norte", "rio guabiruba"],
}

#: Afluentes casados pelo nome EXATO (minúsculo), não por substring.
NOMES_EXATOS = {"guabiruba"}

#: Afluentes desenhados só no trecho LIGADO à régua da cidade (vértice comum). No Rio Guabiruba Norte, o OSM
#: tem uma lacuna de ~1,8 km rio acima da estação: a cabeceira vem solta. Ligar a lacuna seria reta inventada;
#: desenhar o pedaço solto seria um salto no mapa. Fica o curso da estação até o Mirim.
SO_O_LIGADO_A_REGUA = {"guabiruba": "guabiruba"}

#: Afluentes desenhados só no trecho LIGADO ao tronco (vértice comum, a partir da ponta mais perto do Açu). No Rio
#: Luís Alves, o OSM tem uma lacuna de ~7,8 km em linha reta entre o alto curso (cidade de Luiz Alves, vias
#: 24582788 e 741111134) e o baixo (136185376 em diante). Pela mesma regra do Guabiruba, o pedaço solto fica de
#: fora; o que fica chega ao Açu no nó 3981099664, que é onde a confluência é medida (08/10/2026).
SO_O_LIGADO_AO_TRONCO = {"luiz-alves"}

#: Os rios recortados na CAIXA do mapa (a extensão do tronco e das réguas do cadastro). O Benedito nasce ao
#: norte de Doutor Pedrinho e o Itajaí do Sul em Alfredo Wagner, fora do quadro de hoje; inteiros, eles
#: afastariam o mapa inteiro. O recorte guarda o trecho das cidades e a chegada ao rio de baixo.
RECORTE_NA_CAIXA = ("benedito", "itajai-do-sul", "trombudo", "rio-dos-cedros", "guabiruba", "luiz-alves")
#: Folga do recorte, em graus (~1,5 km). Sem ela, a régua que define a borda do quadro (Rio dos Cedros, a mais
#: ao norte) ficava NA PONTA do rio recortado, a 137 m do fim da linha — o rio parecia nascer na cidade. Com a
#: folga, a linha passa pela régua e segue um pouco além. O quadro do Monitor cresce no máximo isso.
FOLGA_DA_CAIXA_GRAUS = 0.015


#: Recorte do Hercílio ao NORTE desta latitude. O Itajaí do Norte nasce em
#: Itaiópolis, ~55 km acima da borda norte do traçado de hoje (-26,838, o Açu em
#: Blumenau). O Monitor enquadra a bacia pela extensão de TODOS os rios, então o
#: rio inteiro afastaria o mapa inteiro — e a regra é que o Monitor não muda. O
#: recorte guarda o que serve à tela: José Boiteux (barragem Norte), Ibirama e a
#: chegada ao Açu. Teste: `teste_converter_tracado_rios.TesteHercilio`.
CORTE_NORTE = {"hercilio": -26.84}


def recortar_na_caixa(linhas: list[list[list[float]]], caixa: tuple[float, float, float, float]) -> list[list[list[float]]]:
    """Os trechos de cada linha dentro da caixa (oeste, sul, leste, norte); a linha que sai e volta vira duas."""
    oeste, sul, leste, norte = caixa
    out: list[list[list[float]]] = []
    for linha in linhas:
        atual: list[list[float]] = []
        for p in linha:
            if oeste <= p[0] <= leste and sul <= p[1] <= norte:
                atual.append(p)
            else:
                if len(atual) >= 2:
                    out.append(atual)
                atual = []
        if len(atual) >= 2:
            out.append(atual)
    return out


def caixa_do_mapa(tronco: list[list[list[float]]]) -> tuple[float, float, float, float]:
    """(oeste, sul, leste, norte) do tronco desenhado e das coordenadas do cadastro — o quadro do Monitor."""
    pts = [p for l in tronco for p in l]
    estacoes = json.loads((RAIZ / "data/estacoes.json").read_text(encoding="utf-8"))
    for rio in estacoes["rios"].values():
        for c in rio["cidades"]:
            if c.get("coordenadas"):
                pts.append([c["coordenadas"][1], c["coordenadas"][0]])
    return (min(p[0] for p in pts), min(p[1] for p in pts), max(p[0] for p in pts), max(p[1] for p in pts))


def coordenada_da_cidade(cidade_id: str) -> tuple[float, float]:
    """(lon, lat) da cidade no cadastro."""
    estacoes = json.loads((RAIZ / "data/estacoes.json").read_text(encoding="utf-8"))
    c = next(c for r in estacoes["rios"].values() for c in r["cidades"] if c["id"] == cidade_id)
    return (c["coordenadas"][1], c["coordenadas"][0])


def ligadas_ao_ponto(linhas: list[list[list[float]]], ponto: tuple[float, float]) -> list[list[list[float]]]:
    """As linhas ligadas, por vértice comum, à linha com o vértice mais perto do ponto (lon, lat)."""
    chaves = [{(round(p[0], 7), round(p[1], 7)) for p in l} for l in linhas]
    def d2(l: list[list[float]]) -> float:
        return min((p[0] - ponto[0]) ** 2 + (p[1] - ponto[1]) ** 2 for p in l)
    inicio = min(range(len(linhas)), key=lambda i: d2(linhas[i]))
    vistos, fila = {inicio}, [inicio]
    while fila:
        i = fila.pop()
        for j in range(len(linhas)):
            if j not in vistos and chaves[i] & chaves[j]:
                vistos.add(j)
                fila.append(j)
    return [linhas[i] for i in sorted(vistos)]


def ponta_mais_perto(linhas: list[list[list[float]]], alvo: list[list[list[float]]]) -> tuple[float, float]:
    """A ponta (lon, lat) das `linhas` mais perto de algum vértice do `alvo` — a chegada do afluente."""
    pontos = [p for l in alvo for p in l]
    def d2(p: list[float]) -> float:
        return min((p[0] - q[0]) ** 2 + (p[1] - q[1]) ** 2 for q in pontos)
    ponta = min((p for l in linhas for p in (l[0], l[-1])), key=d2)
    return (ponta[0], ponta[1])


def recortar_ao_sul(linhas: list[list[list[float]]], lat_max: float) -> list[list[list[float]]]:
    """Os trechos de cada linha com lat <= lat_max; uma linha que sai e volta vira duas."""
    out: list[list[list[float]]] = []
    for linha in linhas:
        atual: list[list[float]] = []
        for p in linha:
            if p[1] <= lat_max:
                atual.append(p)
            else:
                if len(atual) >= 2:
                    out.append(atual)
                atual = []
        if len(atual) >= 2:
            out.append(atual)
    return out


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


def ways_por_substring(elementos: list[dict], chaves: list[str]) -> list[dict]:
    """Ways (com geometria de 2+ pontos) cujo `name` (minúsculo) contém alguma das chaves — para afluentes."""
    return [e for e in elementos
            if e.get("type") == "way" and "geometry" in e
            and any(c in ((e.get("tags") or {}).get("name") or "").lower() for c in chaves)
            and len(linha_do_way(e)) >= 2]


def ways_por_nome_exato(elementos: list[dict], nomes: list[str]) -> list[dict]:
    """Ways (com geometria de 2+ pontos) cujo `name` (minúsculo) é exatamente um dos nomes."""
    return [e for e in elementos
            if e.get("type") == "way" and "geometry" in e
            and ((e.get("tags") or {}).get("name") or "").lower() in nomes
            and len(linha_do_way(e)) >= 2]


def linhas_por_substring(elementos: list[dict], chaves: list[str]) -> list[list[list[float]]]:
    """Ways cujo `name` (minúsculo) contém alguma das chaves — para afluentes."""
    return [linha_do_way(e) for e in ways_por_substring(elementos, chaves)]


def linhas_por_nome_exato(elementos: list[dict], nomes: list[str]) -> list[list[list[float]]]:
    """Ways cujo `name` (minúsculo) é exatamente um dos nomes."""
    return [linha_do_way(e) for e in ways_por_nome_exato(elementos, nomes)]


def marcar_origem(dados: dict, bruto: pathlib.Path) -> list[dict]:
    """
    Os elementos do bruto, cada um marcado com o arquivo e a data da base do OSM de onde veio.

    A data da base (`osm3s.timestamp_osm_base`) é a da cópia do OpenStreetMap que o espelho respondeu, não a
    do download (docs/TRACADOS-AFLUENTES-2026-10-06.md). Ela morava só no bruto; com isto ela vai para o
    arquivo de `data/rios/`, e o chat responde "de onde vem esse traçado?" com a data (docs/CHAT-GLOBAL-COMANDOS.md).
    """
    base = (dados.get("osm3s") or {}).get("timestamp_osm_base")
    elementos = dados.get("elements") or []
    for e in elementos:
        e["_origem"] = (bruto.name, base if isinstance(base, str) else None)
    return elementos


def origem_das_ways(ways: list[dict]) -> list[dict]:
    """Os brutos de onde vieram as ways do arquivo, sem repetição: [{"bruto": ..., "base_osm": ...}]."""
    vistos = sorted({w["_origem"] for w in ways if "_origem" in w}, key=lambda o: (o[0], o[1] or ""))
    return [{"bruto": b, "base_osm": base} for b, base in vistos]


def feature_do_rio(rio_id: str, linhas: list[list[list[float]]]) -> dict:
    return {
        "type": "Feature",
        "properties": {"rio": rio_id, "fonte": ATRIBUICAO, "trechos": len(linhas)},
        "geometry": {"type": "MultiLineString", "coordinates": linhas},
    }


def geojson_do_rio(rio_id: str, nomes: list[str], por_nome: dict[str, list[dict]]) -> dict:
    linhas = []
    faltando = []
    usadas = []
    for nome in nomes:
        ways = por_nome.get(nome) or []
        if not ways:
            faltando.append(nome)
        for w in ways:
            linha = linha_do_way(w)
            if len(linha) >= 2:
                linhas.append(linha)
                usadas.append(w)
    if faltando:
        # Nome esperado que não veio: o bruto mudou ou a query pegou coisa
        # diferente. Grita, não emite um rio pela metade em silêncio.
        raise SystemExit(f"{rio_id}: nomes ausentes no bruto: {faltando}")
    feat = {
        "type": "Feature",
        "properties": {
            "rio": rio_id,
            "fonte": ATRIBUICAO,
            "trechos": len(linhas),
        },
        "geometry": {"type": "MultiLineString", "coordinates": linhas},
    }
    if origem := origem_das_ways(usadas):
        feat["properties"]["origem"] = origem
    return feat


def linhas_do_geojson_asthon(caminho: pathlib.Path, nome: str) -> list[list[list[float]]]:
    """
    O curso `nome` do FeatureCollection da Asthon, como lista de linhas.

    Formato diferente do Overpass (Feature/geometry, não element/geometry), por
    isso não passa pelo `ways_por_nome`. Nome ausente devolve vazio: o traçado é
    OPCIONAL, e um arquivo que mudou não pode derrubar o tronco.
    """
    dados = json.loads(caminho.read_text(encoding="utf-8"))
    linhas: list[list[list[float]]] = []
    for f in dados.get("features") or []:
        props = f.get("properties") or {}
        if (props.get("nome") or props.get("name")) != nome:
            continue
        g = f.get("geometry") or {}
        if g.get("type") == "LineString" and len(g.get("coordinates") or []) >= 2:
            linhas.append(g["coordinates"])
        elif g.get("type") == "MultiLineString":
            linhas.extend(l for l in g.get("coordinates") or [] if len(l) >= 2)
    return linhas


def main() -> int:
    if not BRUTO.exists():
        raise SystemExit(f"falta o bruto {BRUTO} — baixe na VPS (ver docs)")
    dados = json.loads(BRUTO.read_text(encoding="utf-8"))
    elementos = marcar_origem(dados, BRUTO)
    por_nome = ways_por_nome(elementos)

    # O bruto dos ribeirões entra SÓ na busca por substring (afluentes
    # opcionais). O tronco continua saindo do bruto conferido, intocado.
    for extra_caminho, oque in ((BRUTO_RIBEIROES, "ribeirões de Itajaí"),
                                (BRUTO_VAO_CANHANDUBA, "vão do Canhanduba"),
                                (BRUTO_HERCILIO, "Rio Hercílio / Itajaí do Norte"),
                                *((c, f"afluente {r}") for r, c in BRUTOS_AFLUENTES.items())):
        if extra_caminho.exists():
            extra = json.loads(extra_caminho.read_text(encoding="utf-8"))
            n = len(extra.get("elements") or [])
            elementos = elementos + marcar_origem(extra, extra_caminho)
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

    # Cabeceira do SUL, do bruto da Defesa Civil de Rio do Sul. Opcional e
    # parcial — ver BRUTO_RIO_DO_SUL.
    for rio_id, nome in RIOS_DE_RIO_DO_SUL.items():
        if not BRUTO_RIO_DO_SUL.exists():
            print(f"{rio_id}: sem {BRUTO_RIO_DO_SUL.name} — pulado.")
            continue
        linhas = linhas_do_geojson_asthon(BRUTO_RIO_DO_SUL, nome)
        if not linhas:
            print(f"{rio_id}: '{nome}' não está em {BRUTO_RIO_DO_SUL.name} — pulado.")
            continue
        feat = feature_do_rio(rio_id, linhas)
        feat["properties"]["fonte"] = ATRIBUICAO_ASTHON
        feat["properties"]["cobertura"] = (
            "PARCIAL: cobertura municipal de Rio do Sul. Desenha a chegada da cabeceira à "
            "confluência; NÃO alcança Ituporanga, 21 km a montante. Completar pelo Overpass "
            "(docs/TRACADO-ITAJAI-DO-SUL.md)."
        )
        grava(feat, rio_id)

    tronco = [l for r, nomes in RIOS.items() for l in geojson_do_rio(r, nomes, por_nome)["geometry"]["coordinates"]]
    oeste, sul, leste, norte = caixa_do_mapa(tronco)
    f = FOLGA_DA_CAIXA_GRAUS
    caixa = (oeste - f, sul - f, leste + f, norte + f)
    for rio_id, chaves in RIOS_AFLUENTES.items():   # afluentes: opcional
        ways = (ways_por_nome_exato(elementos, chaves) if rio_id in NOMES_EXATOS
                else ways_por_substring(elementos, chaves))
        linhas = [linha_do_way(w) for w in ways]
        if rio_id in CORTE_NORTE:
            linhas = recortar_ao_sul(linhas, CORTE_NORTE[rio_id])
        if rio_id in RECORTE_NA_CAIXA:
            linhas = recortar_na_caixa(linhas, caixa)
        if rio_id in SO_O_LIGADO_A_REGUA and linhas:
            linhas = ligadas_ao_ponto(linhas, coordenada_da_cidade(SO_O_LIGADO_A_REGUA[rio_id]))
        if rio_id in SO_O_LIGADO_AO_TRONCO and linhas:
            linhas = ligadas_ao_ponto(linhas, ponta_mais_perto(linhas, tronco))
        if not linhas:
            print(f"{rio_id}: nenhum way com {chaves} no bruto — pulado. Inclua o rio na "
                  "query do Overpass (docs/fontes-tempo-real.md) e rebaixe o bruto.")
            continue
        feat = feature_do_rio(rio_id, linhas)
        if origem := origem_das_ways(ways):
            feat["properties"]["origem"] = origem
        if rio_id in RECORTE_NA_CAIXA:
            feat["properties"]["cobertura"] = (
                "RECORTADO na caixa do mapa (extensão do tronco e das réguas do cadastro), para não mudar o "
                "enquadramento do Monitor. Baixado por scripts/"
                + ("baixar_tracado_luiz_alves.py." if rio_id == "luiz-alves" else "baixar_tracados_afluentes.py.")
            )
        if rio_id in SO_O_LIGADO_A_REGUA:
            feat["properties"]["cobertura"] += (
                " Só o trecho ligado à régua de Guabiruba (DCSC-00029): o Rio Guabiruba Norte a partir de ~2 km acima da"
                " estação e o Rio Guabiruba até o Itajaí-Mirim. A cabeceira do Norte, solta no OSM por uma lacuna de ~1,8 km, fica"
                " de fora; o Rio Guabiruba Sul não é o curso da estação."
            )
        if rio_id in SO_O_LIGADO_AO_TRONCO:
            feat["properties"]["cobertura"] += (
                " Só o trecho ligado ao Itajaí-Açu: o alto curso, solto no OSM por uma lacuna de ~7,8 km, fica de fora."
                " Serve para medir a confluência (achar_confluencias.py); o rio não tem régua no cadastro e fica cinza."
            )
        if rio_id in CORTE_NORTE:
            feat["properties"]["cobertura"] = (
                f"RECORTADO ao sul da latitude {CORTE_NORTE[rio_id]}: de José Boiteux (barragem Norte) até o Açu, "
                "passando por Ibirama. As nascentes, em Itaiópolis, ficam fora para não mudar o enquadramento do Monitor."
            )
        grava(feat, rio_id)

    # Rios de município. Recortados na borda norte do Açu, como o Hercílio, para
    # não mudar o enquadramento do Monitor.
    lat_max = max(p[1] for l in geojson_do_rio("itajai-acu", RIOS["itajai-acu"], por_nome)["geometry"]["coordinates"] for p in l)
    for bruto in BRUTOS_MUNICIPIOS:
        municipio = bruto.name[len("rios-"):-len("-osm.json")]
        dados_m = json.loads(bruto.read_text(encoding="utf-8"))
        for nome, ways in sorted(ways_por_nome(marcar_origem(dados_m, bruto)).items()):
            if ja_desenhado(nome):
                continue
            linhas = recortar_ao_sul([linha_do_way(w) for w in ways if len(linha_do_way(w)) >= 2], lat_max)
            if not linhas:
                continue
            rio_id = slug(nome)
            feat = feature_do_rio(rio_id, linhas)
            if origem := origem_das_ways(ways):
                feat["properties"]["origem"] = origem
            feat["properties"]["nome"] = nome
            feat["properties"]["municipio"] = municipio
            grava(feat, rio_id)
    return 0


def slug(texto: str) -> str:
    import unicodedata
    t = "".join(c for c in unicodedata.normalize("NFD", texto) if unicodedata.category(c) != "Mn").lower()
    return "-".join("".join(c if c.isalnum() else " " for c in t).split())


def ja_desenhado(nome: str) -> bool:
    """O nome já sai pelo tronco (match exato) ou por um afluente (substring)?"""
    if any(nome in nomes for nomes in RIOS.values()):
        return True
    n = nome.lower()
    return any(c in n for chaves in RIOS_AFLUENTES.values() for c in chaves)


if __name__ == "__main__":
    sys.exit(main())
