#!/usr/bin/env python3
"""
Decide se o KML de cotas de Gaspar pode ser importado — e conclui que pode.

O arquivo `data/brutos/gaspar-cotas-2020.json` traz 1.615 pontos do Google My
Maps da Defesa Civil de Gaspar, pasta `cotas_enchente_gaspar_01042020`, cada um
com um campo chamado `cota`. Uma conversão que veio junto com os dados já os
grava com `referencia: "régua"` — a mesma afirmação, palavra por palavra, que a
conversão do KML de Brusque fazia e que se mostrou falsa. Então a afirmação é
testada aqui antes de qualquer importação, com o mesmo instrumento.

O RESULTADO É O OPOSTO DO DE BRUSQUE, e é por isso que este arquivo entra:

1. **As ruas em comum batem todas.** Nosso cadastro tem cinco cotas numéricas de
   Gaspar, do estudo do CEOPS/FURB referenciado à régua da ANA na empresa
   Círculo. Quatro delas estão no KML, e as quatro batem NO CENTAVO — e sempre no
   MENOR valor daquela rua, que é onde a água chega primeiro. Em Brusque foram 4
   de 13, com as outras nove divergindo de 0,5 a 2,3 m; aqui não há divergência
   nenhuma.

2. **A ordem das duas listas publicadas se reproduz.** O estudo, pela imprensa,
   nomeia as ruas atingidas primeiro (a partir de ~6,20 m) e as que entram depois
   (~7,4 m). São dois grupos, 21 ruas, e não há número por rua nessa fonte — só a
   ordem. No KML os dois grupos saem na ordem certa e separados, sem que nada no
   arquivo diga a que grupo cada rua pertence.

3. **Não é a mesma grandeza deslocada.** Se fosse altitude de terreno, ou régua
   com outro zero, os quatro acertos ao centavo não aconteceriam — e se fosse um
   deslocamento constante, ele apareceria nos dois grupos ao mesmo tempo. Não
   aparece.

O QUE NÃO FECHA, e por isso está escrito aqui em vez de escondido: o estudo do
CEOPS, pela imprensa, diz que a 7 m alagam 53 ruas e a 9 m alagam 329. Contando
as ruas do KML pela mínima de cada uma, dá 18 e 158 — cerca de metade. Não é
deslocamento de escala (o limiar que daria 53 ruas seria 7,82 m, e o que daria
329 seria 10,91 m: os dois desvios são diferentes, e um deslocamento constante
seria igual nos dois). As explicações prováveis são de CONTAGEM, não de escala:
a matéria conta ruas da cidade inteira (53 é 3,8% de ~1.390 ruas) e este mapa
tem 408; e o mapa é de 2020, quatro anos depois do estudo. Nenhuma delas muda o
que os itens 1 a 3 mostram, que é a única pergunta que decide a importação: **os
números deste arquivo estão na mesma régua que os nossos.**

Uso:
    python3 scripts/analisar_kml_gaspar.py
"""

import json
import random
import statistics
import sys
from typing import Any

from analisar_kml_brusque import (TOLERANCIA_M, cruzar_com_cadastro, e_numero,
                                  normalizar, probabilidade_por_acaso)
from comum import DADOS

CIDADE = "gaspar"
BRUTO = "brutos/gaspar-cotas-2020.json"

#: As duas listas que o estudo do CEOPS/FURB publicou pela imprensa, sem número
#: por rua — só a ordem entre elas. Estão em `docs/cotas-de-ruas.md`. É a única
#: outra informação independente que existe sobre Gaspar, e serve de teste
#: justamente porque o KML não traz nada que diga a que grupo cada rua pertence.
PRIMEIRAS_RUAS = [
    "Av. Hilberto Gaertner", "Rua Alfazema", "Rua Alício Hugo Hostins",
    "Rua Amor Perfeito", "Rua Costa Rica", "Rua das Palmeiras",
    "Rua Flor de Laranjeira", "Rua Francisco Wessling", "Rua Heinrich Gorisch",
    "Rua Lírio", "Rua Maestro Egon Bohn", "Rua Magnólia", "Rua Maria da Silva",
    "Rua Olga Sabel", "Rua Petúnia", "Rua Rio do Sul", "Rua Sertão Verde",
]
RUAS_SEGUINTES = [
    "Rua Imaruí", "Rua Francisco Laguna", "Rua Augusto Jacinto dos Santos",
    "Rua José Eberhardt", "Rua Frei Canisio",
]


def carregar_bruto(caminho=None) -> list[dict[str, Any]]:
    """Os pontos do KML, já com a cota como número no campo `cota`."""
    caminho = caminho or (DADOS / BRUTO)
    with open(caminho, encoding="utf-8") as arquivo:
        brutos = json.load(arquivo)["pontos"]
    pontos = []
    for p in brutos:
        copia = dict(p)
        copia["cota"] = numero(p.get("cota_rotulo"))
        pontos.append(copia)
    return pontos


def numero(texto: Any) -> float | None:
    """`8,25` e `8.25` viram 8.25. O que não é número vira None."""
    if texto is None:
        return None
    try:
        return float(str(texto).strip().replace(",", "."))
    except ValueError:
        return None


def minima_por_rua(pontos: list[dict[str, Any]]) -> dict[str, float]:
    """
    A menor cota de cada rua — o nível em que a água chega àquela rua.

    É esta a grandeza comparável com o que temos: nosso cadastro guarda, por
    rua, o ponto em que ela COMEÇA a alagar.
    """
    minimas: dict[str, float] = {}
    for p in pontos:
        rua = normalizar(p.get("rua"))
        if rua and e_numero(p.get("cota")):
            minimas[rua] = min(minimas.get(rua, float("inf")), p["cota"])
    return minimas


def separacao_dos_grupos(minimas: dict[str, float]) -> dict[str, Any]:
    """
    O teste da ordem: as ruas que a fonte diz alagarem primeiro têm mesmo cota
    menor no KML do que as que entram depois?

    Nada no arquivo diz a que grupo cada rua pertence — a divisão vem de fora,
    da matéria sobre o estudo. Se o campo `cota` fosse outra grandeza, não teria
    por que respeitar essa ordem.
    """
    def cotas(nomes):
        return sorted(minimas[k] for k in (normalizar(n) for n in nomes) if k in minimas)

    a, b = cotas(PRIMEIRAS_RUAS), cotas(RUAS_SEGUINTES)
    return {
        "primeiras": a,
        "seguintes": b,
        "mediana_primeiras": statistics.median(a) if a else None,
        "mediana_seguintes": statistics.median(b) if b else None,
        "na_ordem": bool(a and b and statistics.median(a) < statistics.median(b)),
        "p": p_da_ordem(a, b),
    }


def p_da_ordem(a: list[float], b: list[float], rodadas: int = 20000,
               semente: int = 7) -> float:
    """
    P(a diferença entre as medianas sair tão grande por acaso), embaralhando
    quais ruas caem em que grupo. Sem isto, "o grupo A ficou abaixo do B" seria
    só uma impressão com 21 números.
    """
    if not a or not b:
        return float("nan")
    observado = statistics.median(b) - statistics.median(a)
    juntos = a + b
    sorteio = random.Random(semente)
    tao_bons = 0
    for _ in range(rodadas):
        sorteio.shuffle(juntos)
        if statistics.median(juntos[len(a):]) - statistics.median(juntos[:len(a)]) >= observado:
            tao_bons += 1
    return tao_bons / rodadas


def importavel(acertos: int, total_comum: int, na_ordem: bool, p_ordem: float) -> bool:
    """
    O arquivo só é importável se as duas coisas forem verdade ao mesmo tempo:
    TODAS as ruas em comum baterem ao centavo com o cadastro, e a ordem das duas
    listas publicadas se reproduzir com folga estatística.

    Uma divergência que seja já reabre a pergunta de Brusque — lá parte do
    arquivo era régua e parte não, e não havia campo que dissesse qual era qual.
    Meia prova, aqui, é o mesmo que nenhuma.
    """
    if total_comum < 3:
        return False
    if acertos != total_comum:
        return False
    return na_ordem and p_ordem < 0.05


def main() -> int:
    pontos = carregar_bruto()
    cadastro = [c for c in json.loads(
        (DADOS / "cotas-ruas.json").read_text(encoding="utf-8"))["cotas"]
        if c.get("cidade") == CIDADE]
    minimas = minima_por_rua(pontos)
    valores = [p["cota"] for p in pontos if e_numero(p.get("cota"))]

    print(f"{len(pontos)} pontos, {len(minimas)} ruas distintas")
    print(f"cota de {min(valores):.2f} m a {max(valores):.2f} m, "
          f"mediana {statistics.median(valores):.2f} m")

    print("\n1. As ruas em comum com o nosso cadastro")
    comuns = cruzar_com_cadastro(pontos, cadastro)
    for c in comuns:
        marca = "bate" if c["bate"] else "NÃO BATE"
        onde = " (no menor da rua)" if c["bate_no_menor"] else ""
        print(f"   {c['rua'][:34]:36} nosso {c['nosso_m']:5.2f}  "
              f"KML {c['kml_m'][0]:5.2f}–{c['kml_m'][-1]:5.2f}  {marca}{onde}")
    acertos = sum(1 for c in comuns if c["bate"])
    nossas = [c["cota_m"] for c in cadastro if e_numero(c.get("cota_m"))]
    p_acaso = probabilidade_por_acaso(comuns, nossas)
    print(f"   {acertos} de {len(comuns)} batem ao centavo"
          + (f" · P por acaso = {p_acaso:.4f}" if p_acaso == p_acaso else ""))

    print("\n2. A ordem das duas listas publicadas")
    grupos = separacao_dos_grupos(minimas)
    print(f"   primeiras ruas (~6,20 m na fonte): mediana {grupos['mediana_primeiras']:.2f} m "
          f"({len(grupos['primeiras'])} ruas)")
    print(f"   ruas seguintes (~7,4 m na fonte):  mediana {grupos['mediana_seguintes']:.2f} m "
          f"({len(grupos['seguintes'])} ruas)")
    print(f"   na ordem certa: {'sim' if grupos['na_ordem'] else 'NÃO'} · "
          f"P por acaso = {grupos['p']:.4f}")

    print("\n3. O que não fecha, e por que não decide")
    for nivel, dito in ((7.0, 53), (9.0, 329)):
        quantas = sum(1 for v in minimas.values() if v <= nivel)
        ordenadas = sorted(minimas.values())
        limiar = ordenadas[dito - 1] if dito <= len(ordenadas) else None
        print(f"   a {nivel:.0f} m o estudo diz {dito} ruas; aqui dão {quantas}"
              + (f" (seriam {dito} a {limiar:.2f} m)" if limiar else ""))
    print("   os dois desvios são diferentes, então não é deslocamento de escala;")
    print("   a matéria conta ruas da cidade inteira e este mapa tem "
          f"{len(minimas)}.")

    veredito = importavel(acertos, len(comuns), grupos["na_ordem"], grupos["p"])
    print("\nVEREDITO: " + ("IMPORTAR — mesma régua do nosso cadastro."
                            if veredito else
                            "NÃO IMPORTAR — a prova de que é a mesma régua não fecha."))
    return 0 if veredito else 2


if __name__ == "__main__":
    raise SystemExit(main())
