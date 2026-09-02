#!/usr/bin/env python3
"""
Ordena as réguas DC de Itajaí pela descida do rio (montante → mar), por curso.

CONTEXTO — por que NÃO é "projeção no traçado" (o T2 original supunha isso):
o traçado dos rios (`data/rios/*.geojson`) é um **MultiLineString de segmentos
soltos do OpenStreetMap** (57 no Mirim, 122 no Açu), sem ordem nem conectividade
— não é uma linha única da nascente à foz. Montar "distância ao longo do curso"
exigiria assemblar a rede em grafo, e o Mirim ainda tem DOIS braços (canal
retificado + curso antigo). Pior: o **canal retificado e os ribeirões não estão
no traçado** (o OSM tem o curso antigo). Medido em 02/09: DC-03/SEMASA cai a
2,3 km do traçado, os ribeirões a 0,9–4,4 km.

Por isso a ordem é pela **distância à foz** (reta), que é robusta e verificável
— DC-01/CEPSUL é a mais perto do mar, DC-10/Limoeiro a mais longe. A projeção no
traçado entra só como **checagem de qualidade** (afastamento): régua longe do
traçado é sinal de que está num braço/ribeirão fora do desenho, não de erro.

EMPATE (o T3): DC-04 (Vitalmar) e DC-06 (Itamirim) ficam à MESMA distância da foz
(~4,8 km) e projetam no MESMO ponto do traçado. Não dá para dizer qual vem antes
— e o projeto não inventa. Elas saem com a MESMA `ordem_descida` e uma nota de
"co-locadas / braços paralelos". Nunca forçar sequência entre elas.

A ordem é POR CURSO (`rio`): dentro do Itajaí-Mirim, dentro do Açu, dentro de
cada ribeirão — não se mistura curso, porque cada um é um caminho ao mar.

Uso:
    python3 scripts/ordenar_estacoes_itajai.py           # relatório
    python3 scripts/ordenar_estacoes_itajai.py --gravar  # grava ordem_descida
"""

import argparse
import json
import math
import sys

from comum import DADOS

ESTACOES = DADOS / "estacoes.json"

#: Barra do rio Itajaí (foz no mar), aproximada. Só o SENTIDO importa para a
#: ordem — a foz exata não muda o ranking.
FOZ = (-26.906, -48.642)

#: Régua a mais que isto do traçado do seu rio está num braço/ribeirão fora do
#: desenho do OSM: a projeção não vale como conferência de posição para ela.
OFFSET_ALERTA_M = 500.0

#: Diferença de distância à foz abaixo disto = empate: réguas co-locadas, sem
#: ordem definível (DC-04 × DC-06). Não se força sequência.
EMPATE_KM = 0.25

#: Ribeirão → rio-mãe, só para escolher o traçado da conferência de afastamento.
RIO_MAE = {"ribeirao-murta": "itajai-acu", "ribeirao-canhanduba": "itajai-mirim"}


def _dist_km(a: tuple[float, float], b: tuple[float, float]) -> float:
    return math.hypot((a[0] - b[0]) * 111.32,
                      (a[1] - b[1]) * 111.32 * math.cos(math.radians(a[0])))


def _tracado(rio: str) -> list[list[list[float]]]:
    g = json.loads((DADOS / "rios" / f"{rio}.geojson").read_text(encoding="utf-8"))
    return g["geometry"]["coordinates"]


def _afastamento_m(lat: float, lon: float, rio: str) -> float | None:
    rio_check = RIO_MAE.get(rio, rio)
    if rio_check not in ("itajai-acu", "itajai-mirim"):
        return None
    melhor = math.inf
    for linha in _tracado(rio_check):
        for lon2, lat2 in linha:  # geojson é [lon, lat]
            melhor = min(melhor, _dist_km((lat, lon), (lat2, lon2)))
    return melhor * 1000


def reguas_dc(dados: dict) -> list[dict]:
    """As réguas DC com coordenada, com km da foz e afastamento calculados."""
    saida = []
    for e in dados.get("estacoes_tempo_real", []):
        cod = str(e.get("codigo", ""))
        if not cod.startswith("DC-") or cod == "DC-00" or e.get("lat") is None:
            continue
        lat, lon = e["lat"], e["lon"]
        saida.append({
            "codigo": cod,
            "rio": e.get("rio"),
            "titulo": e.get("titulo", cod),
            "km_da_foz": round(_dist_km((lat, lon), FOZ), 2),
            "afastamento_m": _afastamento_m(lat, lon, e.get("rio")),
        })
    return saida


def ordenar(reguas: list[dict]) -> dict[str, list[dict]]:
    """
    Por curso, ordena da foz para a montante e atribui `ordem_descida` (1 = mais
    a montante, desce até a foz). Réguas empatadas na distância à foz recebem a
    MESMA ordem e ganham `ordem_nota`.
    """
    por_rio: dict[str, list[dict]] = {}
    for r in reguas:
        por_rio.setdefault(r["rio"], []).append(r)

    for rio, lista in por_rio.items():
        # montante (mais longe da foz) primeiro
        lista.sort(key=lambda r: -r["km_da_foz"])
        ordem = 0
        anterior_km = None
        for r in lista:
            if anterior_km is None or abs(r["km_da_foz"] - anterior_km) >= EMPATE_KM:
                ordem += 1
                anterior_km = r["km_da_foz"]
            r["ordem_descida"] = ordem
        # marca os empates (mesma ordem em mais de uma régua)
        from collections import Counter
        conta = Counter(r["ordem_descida"] for r in lista)
        for r in lista:
            if conta[r["ordem_descida"]] > 1:
                r["ordem_nota"] = ("co-locada com outra régua na mesma distância da foz — "
                                   "ordem entre elas indefinível (braços paralelos)")
    return por_rio


def _grava(dados: dict, por_rio: dict[str, list[dict]]) -> None:
    """Escreve ordem_descida (e nota) preservando o formato, por inserção após o codigo."""
    por_codigo = {r["codigo"]: r for lista in por_rio.values() for r in lista}
    raw = ESTACOES.read_text(encoding="utf-8")
    import re
    for cod in sorted(por_codigo, reverse=True):
        r = por_codigo[cod]
        m = re.search(r'("codigo":\s*"' + re.escape(cod) + r'",\n)([ \t]*)', raw)
        recuo = m.group(2)
        # remove ordem_* antigos deste bloco, se houver (idempotente)
        prox = re.search(r'"codigo":\s*"', raw[m.end():])
        fim = m.end() + prox.start() if prox else len(raw)
        bloco = raw[m.end(1):fim]
        bloco = re.sub(r'[ \t]*"ordem_descida":.*\n(?:[ \t]*"ordem_nota":.*\n)?'
                       r'(?:[ \t]*"ordem_confirmada_por":.*\n)?', '', bloco)
        raw = raw[:m.end(1)] + bloco + raw[fim:]
        linhas = [f'{recuo}"ordem_descida": {r["ordem_descida"]},']
        if "ordem_nota" in r:
            linhas.append(f'{recuo}"ordem_nota": {json.dumps(r["ordem_nota"], ensure_ascii=False)},')
        linhas.append(f'{recuo}"ordem_confirmada_por": '
                      f'{json.dumps("distância à foz (traçado OSM não ordena); ver docs/coordenadas-dc-itajai.md", ensure_ascii=False)},')
        raw = raw[:m.end(1)] + "\n".join(linhas) + "\n" + raw[m.end(1):]
    json.loads(raw)
    ESTACOES.write_text(raw, encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--gravar", action="store_true", help="grava ordem_descida no estacoes.json")
    args = ap.parse_args()

    dados = json.loads(ESTACOES.read_text(encoding="utf-8"))
    reguas = reguas_dc(dados)
    if not reguas:
        print("ERRO: nenhuma régua DC com coordenada — rode preencher_coordenadas_dc.py antes.",
              file=sys.stderr)
        return 1

    por_rio = ordenar(reguas)
    NOME = {"itajai-acu": "Itajaí-Açu", "itajai-mirim": "Itajaí-Mirim",
            "ribeirao-murta": "Ribeirão da Murta", "ribeirao-canhanduba": "Ribeirão Canhanduba"}
    for rio in sorted(por_rio):
        print(f"\n{NOME.get(rio, rio)} (montante → foz):")
        for r in sorted(por_rio[rio], key=lambda x: x["ordem_descida"]):
            off = r["afastamento_m"]
            marca = ""
            if off is not None and off > OFFSET_ALERTA_M:
                marca = f"  ⚠ {off:.0f} m fora do traçado (braço/ribeirão não desenhado)"
            elif "ordem_nota" in r:
                marca = "  ⚠ empate (co-locada)"
            local = r["titulo"].split(" - ")[-1].split(" – ")[-1][:26]
            print(f"  {r['ordem_descida']}. {r['codigo']:6} {r['km_da_foz']:5.1f} km  {local}{marca}")

    if args.gravar:
        _grava(dados, por_rio)
        print(f"\ngravado ordem_descida em {ESTACOES}")
    else:
        print("\n(relatório; use --gravar para escrever ordem_descida)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
