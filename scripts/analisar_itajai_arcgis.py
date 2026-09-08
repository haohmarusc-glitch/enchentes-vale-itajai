#!/usr/bin/env python3
"""
Diz o que fazer com as três camadas do ArcGIS de Itajaí — e o que não fazer.

`scripts/baixar_itajai_arcgis.py` trouxe as camadas que dois documentos
prometiam. Este script responde as três perguntas que sobraram, porque nenhuma
delas se responde olhando o nome do arquivo.

1. **Trocar as manchas que já temos pelas do ArcGIS?** Um documento afirmou que
   as do ArcGIS são "mais ricas". São — de atributo derivado, não de geometria:
   mesma contagem de feições em todas as dez camadas, mesmo `situa`, e por cima
   `Shape__Area` e `Shape__Length`, que se calculam da própria geometria. O que
   se perderia na troca é concreto: as nossas vêm do GitHub da GeoItajaí com
   **licença MIT declarada**, e o serviço do ArcGIS não declara licença nenhuma
   (é o item 2 do ofício C2). Trocar piora a procedência para ganhar número
   derivável. **Não trocar.**

2. **A área atingida em cada evento.** Essa sim é informação nova e oficial, e
   três camadas a publicam: 1983 = 7.086 ha, 1984 = 7.015 ha, 2001 = 3.425 ha.
   Confere com a área calculada da geometria dentro de 0,4%. A de 2011 **não**
   entra: somar o campo `areas` dos 32 polígonos dá 6.995 ha contra 7.634 ha
   calculados, porque eles se sobrepõem — soma de polígono sobreposto não é área.

3. **Colocar o "terreno sujeito a inundação" na tela?** **Não**, e é o achado que
   mais importa aqui. A camada tem 110 polígonos somando **38,7 hectares**, com
   mediana de 1.786 m² e o menor deles com 4 m². A mancha de 1983 sozinha cobre
   7.086 ha — **183 vezes mais**. Três quartos dos polígonos caem dentro das
   manchas históricas e um quarto cai fora, espalhados por 19 km de município.

   Sejam o que forem — pontos de alagamento localizado, lotes levantados,
   estruturas de drenagem —, **não são "a área inundável de Itajaí"**. Publicar
   isso com esse rótulo diria a quem mora fora dos polígonos que sua rua não
   alaga, quando a mancha de 1983 diz o contrário para uma área 183 vezes maior.
   É o erro que faz alguém dormir tranquilo na noite errada.

   O que falta para usar: o dicionário de dados da Prefeitura, dizendo o que a
   camada representa e em que escala. Virou pergunta no ofício C2.

Uso:
    python3 scripts/analisar_itajai_arcgis.py
"""

import json
import math
import statistics
import sys

from comum import DADOS

INUNDACOES = "brutos/itajai-arcgis-inundacoes.geojson.json"
TERRENO = "brutos/itajai-terreno-sujeito-inundacao.geojson.json"
PONTOS = "brutos/itajai-pontos-cotados-altimetricos.geojson.json"

#: Área que as camadas do próprio ArcGIS publicam, por evento. Só as três que
#: trazem um total; 2011 tem área por polígono e eles se sobrepõem.
AREA_OFICIAL_HA = {0: ("1983", 7085.69), 1: ("1984", 7015.30), 2: ("2001", 3424.89)}

#: Quanto a área calculada pode divergir da publicada e ainda confirmar. A conta
#: local achata a curvatura da Terra, então alguns décimos por cento é o esperado.
TOLERANCIA_AREA = 0.03

#: Abaixo desta fração da mancha de 1983, uma camada não descreve "a área
#: inundável da cidade" — descreve outra coisa, com nome parecido.
FRACAO_MINIMA_DA_MANCHA = 0.25

#: As cinco camadas que trazem lâmina d'água por polígono, no campo `situa`.
CAMADAS_DE_LAMINA = {5: "2011-09", 6: "2013-07", 7: "2013-09",
                     8: "2014-06", 9: "2015-10"}


def carregar(nome: str) -> dict:
    return json.loads((DADOS / nome).read_text(encoding="utf-8"))


def por_camada(dados: dict) -> dict[int, list[dict]]:
    return {c["camada"]: c["feicoes"] for c in dados["camadas"]}


def area_ha(feicoes: list[dict]) -> float:
    """
    Área das feições, em hectares, direto de lon/lat.

    Projeção local achatada: serve para conferir ordem de grandeza e comparar
    camadas entre si, que é para o que ela é usada aqui. Não é medição
    cartográfica, e nenhum número dela vai para a tela.
    """
    total = 0.0
    for f in feicoes:
        g = f.get("geometry") or {}
        if g.get("type") not in ("Polygon", "MultiPolygon"):
            continue
        pols = g["coordinates"] if g["type"] == "MultiPolygon" else [g["coordinates"]]
        for pol in pols:
            if not pol or not pol[0]:
                continue
            lat0 = pol[0][0][1]
            kx = 111320 * math.cos(math.radians(lat0))
            ky = 110540

            def sapato(anel):
                soma = 0.0
                for i in range(len(anel)):
                    x1, y1 = anel[i]
                    x2, y2 = anel[i - 1]
                    soma += (x1 * kx) * (y2 * ky) - (x2 * kx) * (y1 * ky)
                return abs(soma) / 2

            total += sapato(pol[0]) - sum(sapato(b) for b in pol[1:])
    return total / 10000


def mesma_geometria(arcgis: dict[int, list[dict]], nosso_indice: list[dict]) -> list[str]:
    """
    As camadas do ArcGIS e as nossas descrevem as mesmas feições? Devolve as
    diferenças; lista vazia quer dizer que a troca não traria geometria nova.
    """
    contagens = [len(arcgis[c]) for c in sorted(arcgis)]
    nossas = [m["feicoes"] for m in nosso_indice]
    if contagens != nossas:
        return [f"contagem difere: ArcGIS {contagens} · nosso {nossas}"]
    return []


def terreno_descreve_a_cidade(area_terreno: float, area_1983: float) -> bool:
    """
    A camada de terreno inundável cobre área comparável à de uma cheia grande?

    Se não cobre, o rótulo dela promete mais do que ela entrega, e mostrá-la
    como "área inundável" faz quem está fora dos polígonos se sentir seguro.
    """
    if area_1983 <= 0:
        return False
    return area_terreno / area_1983 >= FRACAO_MINIMA_DA_MANCHA


def limites_da_faixa(rotulo: str) -> tuple[float, float] | None:
    """
    Os dois extremos de um rótulo de lâmina, em metros — ou None.

    `"0,41 a 0,60"` vira `(0.41, 0.60)`. Mas `"0,20"` sozinho devolve **None**,
    de propósito: o serviço não diz se é "até 0,20" ou "exatamente 0,20", e
    inventar o limite de baixo é inventar área.
    """
    partes = rotulo.split(" a ")
    if len(partes) != 2:
        return None
    try:
        a, b = (float(x.strip().replace(",", ".")) for x in partes)
    except ValueError:
        return None
    return (a, b) if a <= b else (b, a)


def faixas_que_se_sobrepoem(rotulos) -> list[tuple[str, str]]:
    """
    Pares de faixas que cobrem a mesma lâmina — logo, não são classes disjuntas.

    POR QUE EXISTE (08/09/2026). A camada de out/2015 publica ao mesmo tempo
    `"0,41 a 0,60"` e `"0,51 a 1"`: entre 0,51 e 0,60 as duas valem. Somar
    hectares por faixa como se fossem categorias exclusivas — que é o que um
    gráfico de barras faz sem perguntar — conta a mesma área duas vezes e
    apresenta o resultado como repartição de um todo.
    """
    com_limite = [(r, lim) for r in rotulos if (lim := limites_da_faixa(r))]
    pares = []
    for i, (r1, (a1, b1)) in enumerate(com_limite):
        for r2, (a2, b2) in com_limite[i + 1:]:
            if a1 <= b2 and a2 <= b1:
                pares.append((r1, r2))
    return pares


def ha_por_faixa(feicoes: list[dict]) -> dict[str, float]:
    """Hectares por rótulo de lâmina, de `Shape__Area` (m²) do próprio serviço."""
    fora = {}
    for f in feicoes:
        prop = f.get("properties") or {}
        rotulo = prop.get("situa")
        if rotulo is None:
            continue
        fora[rotulo] = fora.get(rotulo, 0.0) + (prop.get("Shape__Area") or 0) / 10000
    return fora


def main() -> int:
    try:
        inundacoes = por_camada(carregar(INUNDACOES))
        terreno = por_camada(carregar(TERRENO))[0]
    except (OSError, ValueError, KeyError) as erro:
        print(f"faltam os brutos do ArcGIS: {erro}\n"
              "rode antes: python3 scripts/baixar_itajai_arcgis.py", file=sys.stderr)
        return 1

    indice = json.loads((DADOS / "manchas" / "index.json").read_text(encoding="utf-8"))["manchas"]

    print("1. Trocar as manchas pelas do ArcGIS?")
    diferencas = mesma_geometria(inundacoes, indice)
    for d in diferencas:
        print(f"   {d}")
    if not diferencas:
        print("   mesma contagem de feições nas dez camadas — a troca não traz geometria nova.")
        print("   NÃO TROCAR: as nossas têm licença MIT declarada; o ArcGIS não declara.")

    print("\n2. Área atingida, do próprio ArcGIS")
    for camada, (evento, publicada) in sorted(AREA_OFICIAL_HA.items()):
        calculada = area_ha(inundacoes[camada])
        bate = abs(calculada - publicada) / publicada <= TOLERANCIA_AREA
        print(f"   {evento}: {publicada:>8.0f} ha publicados · {calculada:>8.0f} calculados"
              f"  {'confere' if bate else 'NÃO CONFERE'}")
    soma_2011 = sum(f["properties"].get("areas", 0) for f in inundacoes[4]) / 10000
    print(f"   2011: {soma_2011:>8.0f} ha somando os 32 polígonos · "
          f"{area_ha(inundacoes[4]):>8.0f} calculados — eles se sobrepõem, não somar")

    print("\n3. Colocar o terreno sujeito a inundação na tela?")
    a_terreno = area_ha(terreno)
    a_1983 = area_ha(inundacoes[0])
    areas = sorted(f["properties"].get("st_area(shape)", 0) for f in terreno)
    print(f"   {len(terreno)} polígonos · {a_terreno:.1f} ha no total · "
          f"mediana {statistics.median(areas):.0f} m² · menor {areas[0]:.0f} m²")
    print(f"   a mancha de 1983 cobre {a_1983:.0f} ha — {a_1983 / a_terreno:.0f} vezes mais")
    pode_terreno = terreno_descreve_a_cidade(a_terreno, a_1983)
    if pode_terreno:
        print("   pode entrar na tela como área inundável.")
    else:
        print("   NÃO MOSTRAR como \"área inundável\": quem mora fora dos polígonos leria")
        print("   que sua rua não alaga, e a mancha de 1983 diz o contrário para uma área")
        print("   muito maior. Falta o dicionário de dados da Prefeitura (ofício C2).")

    print("\n4. Lâmina d'água por faixa — LÂMINA, não cota de régua")
    print("   quanto a água subiu NAQUELE ponto; não é o nível em que a rua alaga.")
    houve_sobreposicao = False
    for camada, evento in sorted(CAMADAS_DE_LAMINA.items()):
        faixas = ha_por_faixa(inundacoes[camada])
        total = sum(faixas.values())
        print(f"   {evento}: {len(inundacoes[camada]):>3} polígonos · {total:>8.1f} ha")
        for rotulo in sorted(faixas, key=lambda r: limites_da_faixa(r) or (-1.0, -1.0)):
            print(f"        {rotulo:>12} m : {faixas[rotulo]:>8.1f} ha")
        for r1, r2 in faixas_que_se_sobrepoem(faixas):
            houve_sobreposicao = True
            print(f"        ⚠️  \"{r1}\" e \"{r2}\" se sobrepõem — NÃO somar como classes")
    if houve_sobreposicao:
        print("   Faixas sobrepostas contam a mesma área duas vezes. Um gráfico de")
        print("   barras aqui apresentaria isso como repartição de um todo.")

    return 0 if pode_terreno else 2


if __name__ == "__main__":
    raise SystemExit(main())
