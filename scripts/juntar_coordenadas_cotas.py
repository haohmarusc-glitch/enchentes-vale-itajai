#!/usr/bin/env python3
"""
Leva a COORDENADA dos brutos para o `cotas-ruas.json`, só onde o par é certo.

POR QUE ESTE SCRIPT EXISTE (04/09/2026)
---------------------------------------
Um documento de viabilidade afirmava "Brusque e Gaspar 100% georreferenciadas"
e recomendava colorir as ruas no mapa a partir disso. Conferido: o
`cotas-ruas.json` consolidado **não tem campo de coordenada nenhum**. As
coordenadas existem, mas só nos brutos, e ninguém as tinha trazido. Era
pré-requisito silencioso de "colorir as ruas" — e um mapa construído sobre o
pressuposto errado teria pintado a rua errada.

O QUE ESTE SCRIPT NÃO FAZ
-------------------------
Não inventa coordenada, não move cota, não cria linha. Só acrescenta `lat`/`lon`
a linhas que já existem, e **só quando sabe qual ponto do bruto é qual linha**.
Onde não sabe, deixa sem coordenada — a linha continua aparecendo na tela com o
número, apenas sem posição no mapa. Uma rua no lugar errado é pior que uma rua
sem lugar.

DUAS CIDADES, DOIS MÉTODOS — E O MOTIVO DE CADA UM
--------------------------------------------------
Medido antes de escolher, não depois:

* **Gaspar** — a ORDEM do bruto foi preservada na consolidação. As duas
  sequências de `(rua, cota)` alinham em três blocos contíguos, com 1.613 de
  1.613 linhas casadas e apenas 2 pontos do bruto que a consolidação descartou.
  Por isso o pareamento é por **alinhamento de sequência** (`difflib`), que
  resolve até as ruas repetidas: duas linhas com a mesma `(rua, cota)` ficam na
  mesma ordem dos dois lados.

* **Brusque** — a ordem NÃO foi preservada (o alinhamento casa 1 de 350). Sobra
  o pareamento por **chave `(rua, cota)`**, que casa 349 de 350. A chave que
  aparece duas vezes no bruto fica **de fora**: "General Osório, cota 7,87" são
  dois pontos reais a ~330 m um do outro, e há uma linha só no consolidado —
  não há como saber qual. Escolher um seria pintar 330 m de rua errada.

O BRUTO QUE NÃO PODE SER USADO
------------------------------
`brusque-mymaps-cotas.json` (3.688 pontos) tem coordenada e **está proibido**.
O `_meta` dele diz por quê, e é a razão certa: *"NÃO IMPORTADO. O campo `cota`
deste arquivo não pôde ser identificado como nível de régua."* É a mesma
armadilha da camada de 2011 — um campo chamado "cota" não prova ser nível de
régua. Coordenada boa não redime cota não verificada. O script recusa por nome,
com o motivo à vista, para ninguém o adicionar por parecer o arquivo maior.

A GUARDA CONTRA TROCA DE LINHA
------------------------------
O erro que mais importa não é coordenada fora do mundo — é coordenada certa na
LINHA errada. As duas nuvens de pontos são disjuntas por ~10 km (Gaspar em
-26,95..-26,89; Brusque em -27,15..-27,04), então uma linha de Gaspar que caia
dentro da nuvem de Brusque, ou o contrário, é troca de linha. O limite não é
inventado: sai da extensão dos próprios brutos, medida a cada execução.

IDEMPOTENTE. Rodar duas vezes dá o mesmo arquivo.

Uso:
    python3 scripts/juntar_coordenadas_cotas.py            # relatório, não grava
    python3 scripts/juntar_coordenadas_cotas.py --gravar
"""

from __future__ import annotations

import argparse
import difflib
import json
import sys
import unicodedata
from collections import Counter, defaultdict

from comum import DADOS, grava_json

COTAS = DADOS / "cotas-ruas.json"
BRUTOS = DADOS / "brutos"

#: Bruto com coordenada que NÃO pode ser usado, e o motivo (do `_meta` dele).
PROIBIDOS = {
    "brusque-mymaps-cotas.json":
        "o `_meta` do próprio arquivo diz NÃO IMPORTADO: o campo `cota` não pôde "
        "ser identificado como nível de régua. Coordenada boa não redime cota "
        "não verificada.",
}

#: Margem sobre a extensão medida do bruto, em graus (~1,1 km), para a guarda de
#: troca de linha. Só precisa ser MENOR que o vão entre as duas nuvens (~0,09°).
MARGEM_GRAUS = 0.01


def norma(s) -> str:
    """Compara nome de rua sem depender de acento, caixa ou espaço duplicado."""
    if not s:
        return ""
    s = unicodedata.normalize("NFKD", str(s)).encode("ascii", "ignore").decode()
    return " ".join(s.lower().split())


def duas_casas(v) -> float | None:
    """'8,25' e 8.25 são a mesma cota; a fonte usa vírgula, o JSON usa ponto."""
    try:
        return round(float(str(v).replace(",", ".")), 2)
    except (TypeError, ValueError):
        return None


def chave(rua, cota) -> tuple[str, float | None]:
    return (norma(rua), duas_casas(cota))


def carregar_bruto(nome: str, campo_cota: str) -> list[dict]:
    if nome in PROIBIDOS:
        raise ValueError(f"{nome} é bruto proibido: {PROIBIDOS[nome]}")
    pontos = json.loads((BRUTOS / nome).read_text(encoding="utf-8"))["pontos"]
    return [p for p in pontos
            if p.get("lat") is not None and p.get("lon") is not None
            and duas_casas(p.get(campo_cota)) is not None]


def parear_por_ordem(linhas: list[dict], pontos: list[dict], campo_cota: str) -> dict[int, dict]:
    """
    Gaspar: a ordem foi preservada, então o alinhamento resolve até as repetidas.

    Devolve {índice na lista de linhas: ponto do bruto}. Só os blocos que o
    `difflib` dá como iguais entram — trecho que ele marca como inserção ou
    substituição fica sem coordenada.
    """
    a = [chave(x.get("rua"), x.get("cota_m")) for x in linhas]
    b = [chave(p.get("rua"), p.get(campo_cota)) for p in pontos]
    pares: dict[int, dict] = {}
    for i, j, n in difflib.SequenceMatcher(a=a, b=b, autojunk=False).get_matching_blocks():
        for k in range(n):
            pares[i + k] = pontos[j + k]
    return pares


def parear_por_chave(linhas: list[dict], pontos: list[dict], campo_cota: str) -> dict[int, dict]:
    """
    Brusque: a ordem se perdeu, sobra a chave — e chave repetida no bruto fica
    de fora, porque duas posições diferentes para uma linha só é "não sei".
    """
    por_chave: dict[tuple, list[dict]] = defaultdict(list)
    for p in pontos:
        por_chave[chave(p.get("rua"), p.get(campo_cota))].append(p)
    pares: dict[int, dict] = {}
    for i, x in enumerate(linhas):
        achados = por_chave.get(chave(x.get("rua"), x.get("cota_m")), [])
        if len(achados) == 1:
            pares[i] = achados[0]
    return pares


#: (cidade, prefixo da fonte no consolidado, bruto, campo da cota no bruto, método)
JUNCOES = (
    ("gaspar", "Defesa Civil de Gaspar", "gaspar-cotas-2020.json", "cota_rotulo", parear_por_ordem),
    ("brusque", "Defesa Civil de Brusque", "brusque-cotas-2023.json", "cota_rotulo", parear_por_chave),
)


def extensao(pontos: list[dict]) -> tuple[float, float, float, float]:
    lats = [p["lat"] for p in pontos]
    lons = [p["lon"] for p in pontos]
    return (min(lats) - MARGEM_GRAUS, max(lats) + MARGEM_GRAUS,
            min(lons) - MARGEM_GRAUS, max(lons) + MARGEM_GRAUS)


def dentro(p: dict, ext: tuple[float, float, float, float]) -> bool:
    return ext[0] <= p["lat"] <= ext[1] and ext[2] <= p["lon"] <= ext[3]


def juntar(cotas: list[dict]) -> tuple[list[dict], list[dict]]:
    """
    Devolve (cotas com lat/lon onde soube, relatório por junção).

    Não altera a lista recebida: devolve linhas novas, para o chamador decidir
    se grava. O relatório é a prestação de contas — quantas casaram, quantas
    ficaram sem, e por quê.
    """
    saida = [dict(x) for x in cotas]
    relatos = []
    extensoes = {}

    for cidade, prefixo, bruto, campo, metodo in JUNCOES:
        pontos = carregar_bruto(bruto, campo)
        extensoes[cidade] = extensao(pontos)
        idx = [i for i, x in enumerate(saida)
               if x.get("cidade") == cidade and str(x.get("fonte", "")).startswith(prefixo)]
        linhas = [saida[i] for i in idx]
        pares = metodo(linhas, pontos, campo)

        for pos, ponto in pares.items():
            linha = saida[idx[pos]]
            linha["lat"] = round(float(ponto["lat"]), 6)
            linha["lon"] = round(float(ponto["lon"]), 6)

        relatos.append({
            "cidade": cidade, "bruto": bruto, "metodo": metodo.__name__,
            "linhas": len(linhas), "pontos_no_bruto": len(pontos),
            "com_coordenada": len(pares), "sem_coordenada": len(linhas) - len(pares),
        })

    # Guarda de troca de linha: nenhuma coordenada pode cair na nuvem da outra.
    for cidade, ext in extensoes.items():
        for outra, ext_outra in extensoes.items():
            if outra == cidade:
                continue
            invasoras = [x for x in saida
                         if x.get("cidade") == cidade and x.get("lat") is not None
                         and dentro(x, ext_outra)]
            if invasoras:
                raise ValueError(
                    f"{len(invasoras)} linha(s) de {cidade} caíram dentro da nuvem de "
                    f"{outra} — isso é troca de linha, não coordenada ruim. "
                    f"Exemplo: {invasoras[0].get('rua')}")

    return saida, relatos


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Leva a coordenada dos brutos para o cotas-ruas.json.")
    p.add_argument("--gravar", action="store_true", help="grava; sem isto, só relata")
    a = p.parse_args(argv)

    doc = json.loads(COTAS.read_text(encoding="utf-8"))
    novas, relatos = juntar(doc["cotas"])

    for r in relatos:
        print(f"\n{r['cidade']} — {r['bruto']} ({r['metodo']})")
        print(f"  linhas no consolidado com essa fonte: {r['linhas']}")
        print(f"  pontos com coordenada no bruto:       {r['pontos_no_bruto']}")
        print(f"  ganharam coordenada:                  {r['com_coordenada']}")
        print(f"  ficaram sem (par incerto):            {r['sem_coordenada']}")

    antes = sum(1 for x in doc["cotas"] if x.get("lat") is not None)
    depois = sum(1 for x in novas if x.get("lat") is not None)
    por_cidade = Counter(x["cidade"] for x in novas if x.get("lat") is not None)
    print(f"\ntotal com coordenada: {antes} → {depois}  ({dict(por_cidade)})")
    print(f"sem coordenada: {len(novas) - depois} de {len(novas)} "
          "— Blumenau e Rio do Sul não têm nos brutos; precisam de geocodificação revisada")

    if not a.gravar:
        print("\n(nada gravado — use --gravar)")
        return 0

    doc["cotas"] = novas
    doc["_meta"].setdefault("campos", {})
    doc["_meta"]["campos"]["lat"] = (
        "latitude do ponto, quando o bruto da cidade a traz e o par com esta linha é "
        "certo; ausente quando não é. Ver scripts/juntar_coordenadas_cotas.py")
    doc["_meta"]["campos"]["lon"] = "longitude, nas mesmas condições de `lat`"
    # `grava_json` é a convenção do projeto: indent=2, acento preservado e
    # escrita atômica (temporário + replace). Serializar aqui à mão reformataria
    # as 4.593 linhas e esconderia a mudança real dentro de um diff do arquivo
    # inteiro — além de arriscar deixar meia fonte de verdade em disco.
    grava_json(COTAS.name, doc)
    print(f"\ngravado em {COTAS}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
