#!/usr/bin/env python3
"""
Onde as duas cabeceiras se juntam e NASCE o Itajaí-Açu, em Rio do Sul.

A topologia canônica já afirmava o FATO ("Taió/Itajaí do Oeste e
Ituporanga/Itajaí do Sul são cabeceiras paralelas que se juntam em Rio do Sul,
onde nasce o Açu" — verificado em OSM/Overpass em 02/09/2026). O que faltava
era a COORDENADA. Ela está no traçado que a Defesa Civil de Rio do Sul publica
pela API Asthon, em data/brutos/rio-do-sul-rios-tracados.geojson.

O QUE ESTE SCRIPT NÃO É
Não é uma medição nossa de "onde os rios passam mais perto". No arquivo da
fonte os três traçados TERMINAM/COMEÇAM no MESMO vértice, ao dígito: a
confluência é declarada pela topologia da fonte, não inferida por nós. É uma
afirmação mais forte que a do achar_confluencias.py (que mede um toque em
metros entre traçados de origens diferentes) — e por isso o guarda aqui é
outro: se o vértice deixar de ser compartilhado, o script RECUSA, em vez de
devolver "o ponto mais próximo", que seria inventar precisão que a fonte não deu.

A CONFERÊNCIA INDEPENDENTE QUE VALE
O sentido de chegada de cada cabeceira é conferível contra a geografia que o
projeto já tinha por outra fonte (OSM): o Itajaí do Sul tem de chegar pelo SUL
(vem de Ituporanga) e o Itajaí do Oeste pelo OESTE (vem de Taió). Duas fontes
independentes concordando é o que transforma "o arquivo diz" em "é verdade".
Se o rumo sair trocado, o script RECUSA: ou o arquivo trocou os nomes, ou a
nossa topologia está errada — e nenhuma das duas se resolve gravando.

COBERTURA — a ressalva que não pode sumir
O traçado cobre só o trecho dentro/perto de Rio do Sul: o "Itajaí do Sul" tem
10,6 km, não é o curso inteiro que vem de Ituporanga. Serve para achar a
confluência (que cai dentro da cobertura); NÃO serve como traçado de mapa. Por
isso o arquivo fica em data/brutos/ e não em data/rios/ — desenhar esse pedaço
como se fosse o rio afirmaria geografia errada na tela.

Uso:
    python3 scripts/achar_confluencia_cabeceiras.py            # relatório
    python3 scripts/achar_confluencia_cabeceiras.py --gravar   # grava em estacoes.json
"""
import argparse
import json
import math
import re
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
TRACADOS = RAIZ / "data" / "brutos" / "rio-do-sul-rios-tracados.geojson"
ESTACOES = RAIZ / "data" / "estacoes.json"

TRONCO = "Rio Itajaí-Açu"
#: cabeceira -> (cidade do projeto, rumo esperado de chegada à confluência)
CABECEIRAS = {
    "Rio Itajaí do Sul": ("ituporanga", "S"),
    "Rio Itajaí do Oeste": ("taio", "O"),
}
#: Vértice compartilhado: a fonte grava o MESMO ponto nos três traçados. A
#: folga existe só para não quebrar por arredondamento de casa decimal — não
#: para acomodar traçados que "quase" se encontram.
LIMITE_VERTICE_M = 1.0

R_TERRA_KM = 6371.0088


def metros(a: tuple[float, float], b: tuple[float, float]) -> float:
    """Distância em metros entre (lon, lat) — haversine."""
    (lon1, lat1), (lon2, lat2) = a, b
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp, dl = p2 - p1, math.radians(lon2 - lon1)
    h = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * R_TERRA_KM * math.asin(math.sqrt(h)) * 1000


def rumo(de: tuple[float, float], para: tuple[float, float]) -> str:
    """
    De que lado `de` está em relação a `para` — N/S/L/O pelo eixo dominante.

    Grosseiro de propósito: a pergunta é "o Sul chega pelo sul?", não o azimute.
    """
    dlon, dlat = de[0] - para[0], de[1] - para[1]
    # Um grau de longitude encurta com o cosseno da latitude; sem isso, perto
    # do paralelo 27 o eixo leste-oeste sairia ~12% maior do que é.
    if abs(dlon * math.cos(math.radians(para[1]))) > abs(dlat):
        return "L" if dlon > 0 else "O"
    return "N" if dlat > 0 else "S"


def carregar() -> dict[str, list[tuple[float, float]]]:
    """Cada rio do arquivo como lista de (lon, lat), na ordem em que a fonte gravou."""
    if not TRACADOS.exists():
        sys.exit(f"ERRO: {TRACADOS.relative_to(RAIZ)} não encontrado.")
    g = json.loads(TRACADOS.read_text(encoding="utf-8"))
    rios: dict[str, list[tuple[float, float]]] = {}
    for f in g.get("features", []):
        geom = f.get("geometry") or {}
        if geom.get("type") != "LineString":
            continue
        nome = (f.get("properties") or {}).get("nome")
        if nome:
            rios[nome] = [(x, y) for x, y, *_ in geom["coordinates"]]
    return rios


def analisar() -> dict:
    """
    O vértice que os três compartilham, e o rumo de chegada de cada cabeceira.

    Devolve `status`: "ok", "sem_tracado" (falta rio no arquivo), "nao_compartilham"
    (a fonte deixou de snapar os traçados) ou "rumo_inesperado" (o arquivo e a
    nossa topologia discordam de que lado vem cada cabeceira).
    """
    rios = carregar()
    faltam = [n for n in [TRONCO, *CABECEIRAS] if n not in rios]
    if faltam:
        return {"status": "sem_tracado", "texto": f"faltam no arquivo: {', '.join(faltam)}"}

    # O Açu NASCE na confluência: seu primeiro vértice é o candidato.
    nascente = rios[TRONCO][0]

    pontas, rumos = {}, {}
    for nome, (cidade, esperado) in CABECEIRAS.items():
        linha = rios[nome]
        # A cabeceira DESAGUA na confluência, então é a ponta final dela que
        # tem de coincidir. Conferir as duas pontas e pegar a mais perto
        # aceitaria um traçado gravado ao contrário sem avisar.
        d = metros(linha[-1], nascente)
        if d > LIMITE_VERTICE_M:
            return {
                "status": "nao_compartilham",
                "texto": f"{nome} termina a {d:.1f} m da nascente do Açu "
                         f"(limite {LIMITE_VERTICE_M:.0f} m): a fonte não declara mais a junção",
            }
        pontas[nome] = linha[-1]
        # Rumo de chegada: de onde a cabeceira VEM, ou seja, o começo dela.
        rumos[nome] = (rumo(linha[0], nascente), esperado, cidade)

    trocados = [n for n, (obtido, esperado, _) in rumos.items() if obtido != esperado]
    if trocados:
        detalhe = "; ".join(
            f"{n} chega de {rumos[n][0]}, esperado {rumos[n][1]}" for n in trocados
        )
        return {"status": "rumo_inesperado", "texto": detalhe}

    return {
        "status": "ok",
        "lat": nascente[1],
        "lon": nascente[0],
        "rumos": {n: v[0] for n, v in rumos.items()},
        "texto": (
            f"{nascente[1]:.7f}, {nascente[0]:.7f} — vértice que o Rio Itajaí do Sul "
            f"(chega de {rumos['Rio Itajaí do Sul'][0]}, vem de Ituporanga), o Rio Itajaí do Oeste "
            f"(chega de {rumos['Rio Itajaí do Oeste'][0]}, vem de Taió) e o Rio Itajaí-Açu "
            "COMPARTILHAM no traçado da Defesa Civil de Rio do Sul (API Asthon, 04/09/2026): a "
            "junção é declarada pela fonte, não medida por nós. O rumo de chegada de cada cabeceira "
            "confere com a topologia levantada em OSM/Overpass — duas fontes independentes. "
            "A cobertura do arquivo é só o trecho perto de Rio do Sul, então ele serve para o "
            "ponto, NÃO como traçado de mapa (fica em data/brutos/, não em data/rios/)."
        ),
    }


def gravar(r: dict) -> bool:
    """
    Escreve `confluencia_cabeceiras` em _topologia, preservando o formato do arquivo.

    Edita o texto, não o dicionário: reserializar o JSON inteiro reformataria
    um arquivo de milhares de linhas e enterraria a mudança real no diff.
    """
    raw = ESTACOES.read_text(encoding="utf-8")
    # A indentação vem do ARQUIVO, não de um palpite: `_topologia` é um bloco
    # aninhado, e um recuo chutado sairia desalinhado do vizinho — ruído no
    # diff exatamente onde a mudança precisa ser fácil de conferir.
    ancora = re.search(r'^([ \t]*)"cabeceiras_paralelas":', raw, re.M)
    if not ancora:
        print("aviso: não achei 'cabeceiras_paralelas' em _topologia — nada gravado",
              file=sys.stderr)
        return False
    ind = ancora.group(1)
    dentro = ind + "  "
    bloco = (
        f'{ind}"confluencia_cabeceiras": {{\n'
        f'{dentro}"lat": {r["lat"]},\n'
        f'{dentro}"lon": {r["lon"]},\n'
        f'{dentro}"cabeceiras": ["taio", "ituporanga"],\n'
        f'{dentro}"nasce": "rio-do-sul",\n'
        f'{dentro}"nota": {json.dumps(r["texto"], ensure_ascii=False)},\n'
        f'{dentro}"fonte": "Defesa Civil de Rio do Sul / API Asthon, '
        'data/brutos/rio-do-sul-rios-tracados.geojson (04/09/2026)"\n'
        f'{ind}}},\n'
    )
    if '"confluencia_cabeceiras"' in raw:
        # Já existe: troca o bloco inteiro, para o script ser idempotente.
        padrao = re.compile(
            r'^[ \t]*"confluencia_cabeceiras": \{.*?^[ \t]*\},\n', re.S | re.M)
        novo, n = padrao.subn(lambda _: bloco, raw, count=1)
    else:
        # Entra logo antes de "cabeceiras_paralelas", que é o campo que ele detalha.
        novo, n = re.subn(r'^([ \t]*"cabeceiras_paralelas":)',
                          lambda m: bloco + m.group(1), raw, count=1, flags=re.M)
    if not n:
        print("aviso: não achei onde inserir em _topologia — nada gravado", file=sys.stderr)
        return False
    json.loads(novo)  # trava: nunca grava JSON inválido
    ESTACOES.write_text(novo, encoding="utf-8")
    return True


def main() -> int:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument("--gravar", action="store_true",
                    help="grava confluencia_cabeceiras em estacoes.json")
    args = ap.parse_args()

    r = analisar()
    print(f"[{r['status']}] {r['texto']}")
    if r["status"] != "ok":
        print("\nNada gravado — melhor sem resposta que com resposta errada.")
        return 1
    if args.gravar:
        print("\ngravado em _topologia (formato preservado)." if gravar(r)
              else "\nnada gravado.")
    else:
        print("\n(relatório; use --gravar para escrever em estacoes.json)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
