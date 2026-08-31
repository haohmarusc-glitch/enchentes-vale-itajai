#!/usr/bin/env python3
"""
Importa as 1.615 cotas por rua de Gaspar do KML da Defesa Civil.

De onde vem: o Google My Maps "Cotas de enchente" da Defesa Civil de Gaspar,
pasta `cotas_enchente_gaspar_01042020`. Bruto em
`data/brutos/gaspar-cotas-2020.json`.

POR QUE ESTE ENTRA E O DE BRUSQUE DE 2011 NÃO
---------------------------------------------
Os dois arquivos são My Maps de Defesa Civil, com um campo chamado `cota`, e os
dois vieram com uma conversão que já os gravava como `referencia: "régua"`. Em
Brusque essa afirmação era falsa. Aqui ela foi testada do mesmo jeito, por
`scripts/analisar_kml_gaspar.py`, e passou:

* as **quatro** ruas em comum com o nosso cadastro batem **ao centavo**, e
  sempre no MENOR valor da rua — que é onde a água chega primeiro. Em Brusque
  foram 4 de 13, com nove divergindo de 0,5 a 2,3 m;
* as duas listas que o estudo do CEOPS/FURB publicou — as ruas atingidas
  primeiro e as que entram depois — saem no KML na ordem certa e separadas
  (P por acaso = 0,0014), sem que nada no arquivo diga a que grupo cada rua
  pertence.

`main()` roda essa análise de novo antes de gravar e RECUSA a importação se o
veredito mudar. A prova não fica num documento: fica no caminho da execução.

O QUE ESTA IMPORTAÇÃO SUBSTITUI
-------------------------------
Dezoito registros de Gaspar estão hoje com `cota_m: null` — a fonte anterior
(imprensa, sobre o mesmo estudo) citava a rua sem publicar o número. Agora a
fonte oficial publica. Esses registros são trocados pelos numerados, e não
somados a eles: deixar os dois faria a mesma rua aparecer na tela dizendo
"alaga a partir de 6,46 m" e "cota não publicada" ao mesmo tempo.

Uso:
    python3 scripts/importar_cotas_gaspar.py --seco
    python3 scripts/importar_cotas_gaspar.py
"""

import argparse
import json
import sys
import unicodedata
from datetime import date

from analisar_kml_brusque import cruzar_com_cadastro, e_numero, normalizar
from analisar_kml_gaspar import (carregar_bruto, importavel, minima_por_rua,
                                 numero, separacao_dos_grupos)
from comum import DADOS

CIDADE = "gaspar"
RIO = "itajai-acu"

#: Cota acima disto não é nível de rio nesta bacia. Rio do Sul publica rua
#: alagando a 19,01 m, então o teto tem de caber nisso — mas 30 m, que é onde
#: a pasta de 2011 de Brusque chegava, não.
COTA_MAXIMA_M = 25.0

FONTE = (
    "Defesa Civil de Gaspar — Google My Maps \"Cotas de enchente\", pasta "
    "cotas_enchente_gaspar_01042020. Cotas do estudo do CEOPS/FURB (coord. Ademar "
    "Cordeiro), referenciadas à régua da ANA na empresa Círculo. Escala conferida "
    "contra as cotas já cadastradas: 4 de 4 ruas em comum batem ao centavo. "
    "Bruto em data/brutos/gaspar-cotas-2020.json"
)
DATA_FONTE = "2020-04"


def chave(r: dict) -> tuple:
    """
    Identidade: cidade, rua, ponto e a COTA.

    A cota entra porque a fonte descreve pontos distintos com o mesmo texto —
    há ruas com dezenas de marcadores e `refer_2` repetido. Sem ela, um
    apagaria o outro em silêncio.
    """
    return (r["cidade"], normalizar(r["rua"]), normalizar(r.get("ponto")),
            round(r["cota_m"], 2) if e_numero(r.get("cota_m")) else None)


def como_registro(p: dict) -> dict | None:
    """Um ponto do KML vira um registro de `cotas-ruas.json`, ou nada."""
    cota = numero(p.get("cota_rotulo")) if "cota_rotulo" in p else p.get("cota")
    rua = (p.get("rua") or "").strip()
    if not e_numero(cota) or not rua:
        return None
    if not 0 < cota < COTA_MAXIMA_M:
        return None
    return {
        "cidade": CIDADE,
        "rio": RIO,
        "rua": rua,
        "bairro": (p.get("bairro") or "").strip() or None,
        # `refer_2` é a transversal, o número da casa ou o ponto de referência —
        # é o que distingue um marcador do outro dentro da mesma rua.
        "ponto": (p.get("esquina") or "").strip() or None,
        "cota_m": round(cota, 2),
        "fonte": FONTE,
        "data_fonte": DATA_FONTE,
        "confianca": "alta",
        # A régua de Gaspar é a da ANA na empresa Círculo. O rótulo "régua" tem
        # o mesmo sentido das outras cidades: nível lido na régua da própria
        # cidade, nunca comparável com o de outra.
        "referencia": "régua",
    }


def superados(atuais: list[dict], novos: list[dict]) -> list[int]:
    """
    Índices dos registros de Gaspar que a fonte oficial supera. Dois casos:

    Sai o registro **sem número** cuja rua a importação agora numera. A fonte
    anterior (imprensa, sobre este mesmo estudo) citava a rua sem publicar a
    cota; agora a cota existe, e deixar os dois faria a mesma rua aparecer na
    busca dizendo "alaga a partir de 6,46 m" e "cota não publicada" ao mesmo
    tempo.

    O que NÃO sai, e é importante que não saia:

    * **os cinco registros COM número.** Eles são a prova de escala desta
      importação inteira: é contra eles que as ruas em comum batem ao centavo.
      Apagá-los porque a fonte oficial repete o mesmo valor deixaria a
      conferência sem contra o que rodar — a evidência sumiria junto com o
      registro que a sustenta. Aparecem duas vezes na busca, com o mesmo
      número e fontes diferentes, e isso é barato perto de perder a prova.
    * **rua que a importação não cobre.** "Rua Lino", 6,57 m, continua no
      cadastro mesmo com o KML trazendo "Rua Lírio" a 6,57 m. Os dois nomes
      podem ser a mesma rua com um erro de transcrição em algum ponto da
      cadeia, mas "podem ser" não apaga registro — é pergunta para a Defesa
      Civil.
    """
    por_rua: dict[str, list[float]] = {}
    for r in novos:
        por_rua.setdefault(normalizar(r["rua"]), []).append(r["cota_m"])

    fora = []
    for i, r in enumerate(atuais):
        if r.get("cidade") != CIDADE:
            continue
        # Registro desta mesma importação não supera a si mesmo. Sem esta
        # linha, rodar duas vezes apagaria os 1.613 e os regravaria — e, se a
        # fonte tivesse encolhido no meio, apagaria sem regravar.
        if r.get("data_fonte") == DATA_FONTE:
            continue
        if e_numero(r.get("cota_m")):
            continue
        if por_rua.get(normalizar(r.get("rua"))):
            fora.append(i)
    return fora


def mesclar(atuais: list[dict], novos: list[dict]) -> tuple[list[dict], int, int, list[str]]:
    """
    União pela identidade, mais a troca dos registros sem número que a
    importação superou. Devolve (lista, acrescentados, repetidos, substituídos).
    """
    fora = set(superados(atuais, novos))
    trocados = [atuais[i].get("rua") for i in sorted(fora)]
    saida = [r for i, r in enumerate(atuais) if i not in fora]

    vistos = {chave(r) for r in saida if e_numero(r.get("cota_m"))}
    novos_n = repetidos = 0
    for r in novos:
        if chave(r) in vistos:
            repetidos += 1
            continue
        vistos.add(chave(r))
        saida.append(r)
        novos_n += 1
    return saida, novos_n, repetidos, trocados


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--seco", action="store_true", help="mostra o que faria, sem gravar")
    args = ap.parse_args()

    try:
        pontos = carregar_bruto()
    except (OSError, ValueError, KeyError) as erro:
        print(f"não deu para ler o bruto de Gaspar: {erro}", file=sys.stderr)
        return 1

    arquivo = DADOS / "cotas-ruas.json"
    dados = json.loads(arquivo.read_text(encoding="utf-8"))
    cadastro = [c for c in dados["cotas"] if c.get("cidade") == CIDADE]

    # O portão: a mesma análise que autorizou a importação, refeita agora.
    comuns = cruzar_com_cadastro(pontos, cadastro)
    acertos = sum(1 for c in comuns if c["bate"])
    grupos = separacao_dos_grupos(minima_por_rua(pontos))
    print(f"{len(pontos)} pontos no KML")
    print(f"conferência: {acertos} de {len(comuns)} ruas em comum batem ao centavo; "
          f"as duas listas publicadas saem {'na ordem' if grupos['na_ordem'] else 'FORA DE ORDEM'} "
          f"(P = {grupos['p']:.4f})")
    if not importavel(acertos, len(comuns), grupos["na_ordem"], grupos["p"]):
        print(
            "\nRECUSADO: a prova de que estes números estão na régua de Gaspar não fecha.\n"
            "Sem ela, seriam 1.615 cotas de rua publicadas sem se saber o que medem —\n"
            "que foi exatamente o caso da camada de 2011 de Brusque. Rodar\n"
            "scripts/analisar_kml_gaspar.py e conferir a fonte antes de importar.",
            file=sys.stderr,
        )
        return 2

    registros = [r for r in (como_registro(p) for p in pontos) if r]
    print(f"{len(registros)} viram registro "
          f"({len(pontos) - len(registros)} ficam de fora: sem rua ou fora de faixa)")

    lista, novos, repetidos, trocados = mesclar(dados["cotas"], registros)
    if trocados:
        print(f"{len(trocados)} registros anteriores são substituídos pela cota oficial: "
              + ", ".join(sorted(trocados)[:6])
              + (" …" if len(trocados) > 6 else ""))
    print(f"acrescenta {novos}, já existiam {repetidos}; "
          f"total de {len(dados['cotas'])} para {len(lista)}")

    if args.seco:
        for r in registros[:5]:
            print(f"  {r['cota_m']:5.2f} m  {r['rua'][:34]:36} {r.get('ponto') or ''}")
        return 0

    dados["cotas"] = lista
    arquivo.write_text(json.dumps(dados, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"\ngravado em {arquivo} ({date.today().isoformat()})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
