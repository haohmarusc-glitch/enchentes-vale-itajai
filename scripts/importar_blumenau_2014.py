#!/usr/bin/env python3
"""
Aplica o PDF oficial de 2014 de Blumenau ao cadastro de cotas por rua.

O que este script faz, e só depois de `conferir_blumenau_2014.py` dizer que a
conferência fechou:

1. **Sobe a confiança de `media` para `alta`** nos registros que o documento
   oficial confirma. Eles estavam em `media` porque tinham vindo por imprensa;
   agora existe a fonte direta, e ela bate ao centavo em 1.891 pontos, com zero
   divergências e deslocamento zero.
2. **Acrescenta o ABRIGO de cada rua**, com o código. É o que a relação da
   imprensa não trazia e é a informação que muda o que a pessoa faz: a cota diz
   que é hora de sair, o abrigo diz para onde.
3. **Importa os pontos que só o PDF tem** — ruas e trechos que a relação de
   2023 não lista.

O que NÃO faz: mexer em cota. Nenhum número de rua muda aqui — os que existiam
foram confirmados, não corrigidos, e é por isso que a operação é segura.

`main()` refaz a conferência antes de gravar e RECUSA se ela deixar de fechar.

Uso:
    python3 scripts/importar_blumenau_2014.py --seco
    python3 scripts/importar_blumenau_2014.py
"""

import argparse
import json
import re
import sys
from datetime import date

from conferir_blumenau_2014 import (BRUTO, CIDADE, DATA_FONTE, carregar_pdf,
                                    confirmado, indexar, normalizar_ponto,
                                    normalizar_rua, numero, parear,
                                    sem_par_no_cadastro)
from comum import DADOS

RIO = "itajai-acu"
COTA_MAXIMA_M = 25.0

#: O PDF abrevia o logradouro ("R", "AL") e o resto do cadastro escreve por
#: extenso. Expandir é trocar a abreviação pela palavra que ela abrevia, não
#: mexer no nome: sem isso, "R 1º de Janeiro" apareceria na busca ao lado de
#: "Rua São Rafael" como se fossem coisas de tipos diferentes.
LOGRADOURO = {"r": "Rua", "av": "Avenida", "al": "Alameda", "tr": "Travessa",
              "rod": "Rodovia", "estr": "Estrada"}

#: A própria fonte usa este texto quando não conseguiu identificar a rua. Não é
#: nome de rua: é a ausência de um. Entra como registro, viraria uma "Rua Não
#: Localizado" que ninguém procura e que ninguém acha.
RE_NAO_IDENTIFICADA = re.compile(r"n[ãa]o\s+localizado", re.IGNORECASE)

FONTE = ("Defesa Civil de Blumenau — \"Cotas das ruas de Blumenau\", PDF da Secretaria "
         "Municipal de Defesa Civil (111 páginas, 2.034 pontos). Bruto em "
         "data/brutos/blumenau-cotas-2014.pdf")

#: Frase acrescentada à fonte dos registros que o PDF confirma. Serve também de
#: marca de idempotência: quem já a tem não recebe de novo.
CONFIRMACAO = (" Valor conferido contra o PDF oficial da Defesa Civil de Blumenau "
               "(data/brutos/blumenau-cotas-2014.pdf): bate ao centavo.")


def abrigo_de(por_ponto: dict, por_cota: dict, registro: dict) -> tuple[str | None, str | None]:
    """O abrigo que o PDF dá àquele ponto — pelo ponto, ou pela cota."""
    achado = por_ponto.get((normalizar_rua(registro.get("rua")),
                            normalizar_ponto(registro.get("ponto"))))
    if achado is None and registro.get("cota_m") is not None:
        achado = por_cota.get((normalizar_rua(registro.get("rua")),
                               round(registro["cota_m"], 2)))
    if not achado:
        return None, None
    return achado.get("abrigo"), achado.get("abrigo_codigo")


def indexar_abrigos(pdf: list[dict]) -> dict[tuple, dict]:
    """(rua, ponto) -> o registro do PDF, para pegar abrigo e código."""
    return {(normalizar_rua(r.get("rua")), normalizar_ponto(r.get("observacao"))): r
            for r in pdf}


def indexar_abrigos_por_cota(pdf: list[dict]) -> dict[tuple, dict]:
    """
    (rua, cota) -> o registro do PDF. É a segunda tentativa para achar o abrigo.

    As duas fontes descrevem o mesmo lugar com palavras diferentes — "final da
    rua" e "Final da rua (pega só uma casa)" —, e por isso 47 registros ficariam
    sem abrigo enquanto os vizinhos deles teriam. A cota é o que identifica o
    ponto: casar só por nome de rua seria grosso demais, porque uma rua comprida
    tem abrigos diferentes em pontos diferentes (a Marechal Deodoro tem dois).
    """
    indice: dict[tuple, dict] = {}
    for r in pdf:
        cota = numero(r.get("cota_rotulo"))
        if cota is not None:
            indice.setdefault((normalizar_rua(r.get("rua")), round(cota, 2)), r)
    return indice


def enriquecer(cadastro: list[dict], pdf: list[dict]) -> tuple[int, int]:
    """
    Sobe a confiança e escreve o abrigo nos registros que o PDF confirma.
    Muda a lista no lugar. Devolve (confirmados, com abrigo novo).
    """
    por_ponto = indexar_abrigos(pdf)
    por_cota = indexar_abrigos_por_cota(pdf)
    confirmados = com_abrigo = 0
    pares = {(normalizar_rua(p["rua"]), normalizar_ponto(p["ponto"]))
             for p in parear(pdf, cadastro) if p["bate"]}

    for registro in cadastro:
        # O abrigo vai para todo registro que o PDF descreve, mesmo os que a
        # conferência não pareou por diferença de redação do ponto.
        abrigo, codigo = abrigo_de(por_ponto, por_cota, registro)
        if abrigo and not registro.get("abrigo"):
            registro["abrigo"] = abrigo
            registro["abrigo_codigo"] = codigo
            com_abrigo += 1

        # A confiança, não. Ela só sobe onde a conferência de fato comparou os
        # dois números e eles bateram — casar pela cota provaria só que a cota é
        # igual à cota, que é circular.
        if (normalizar_rua(registro.get("rua")),
                normalizar_ponto(registro.get("ponto"))) not in pares:
            continue
        if CONFIRMACAO not in (registro.get("fonte") or ""):
            registro["fonte"] = (registro.get("fonte") or "") + CONFIRMACAO
            confirmados += 1
        # A definição está no _meta de cotas-ruas.json: alta = tabela oficial direta.
        registro["confianca"] = "alta"
    return confirmados, com_abrigo


def nome_da_rua(bruto: str) -> str:
    """"R 1º de Janeiro" vira "Rua 1º de Janeiro"; o resto do nome não muda."""
    partes = (bruto or "").strip().split()
    if not partes:
        return ""
    inteiro = LOGRADOURO.get(partes[0].rstrip(".").lower())
    return " ".join([inteiro] + partes[1:]) if inteiro else " ".join(partes)


def como_registro(bruto: dict) -> dict | None:
    """Um registro do PDF vira um registro de `cotas-ruas.json`, ou nada."""
    cota = numero(bruto.get("cota_rotulo"))
    rua = nome_da_rua(bruto.get("rua") or "")
    if cota is None or not rua or not 0 < cota < COTA_MAXIMA_M:
        return None
    if RE_NAO_IDENTIFICADA.search(rua):
        return None
    bairro = (bruto.get("bairro") or "").strip() or None
    return {
        "cidade": CIDADE,
        "rio": RIO,
        "rua": rua,
        # O PDF escreve o bairro em caixa alta; na tela isso vira grito.
        "bairro": bairro.title() if bairro else None,
        "ponto": (bruto.get("observacao") or "").strip() or None,
        "cota_m": round(cota, 2),
        "fonte": FONTE,
        "data_fonte": DATA_FONTE,
        "confianca": "alta",
        # O PDF não declara a referência. O rótulo vem da conferência, não de
        # suposição: 1.891 pontos deste mesmo documento batem ao centavo com
        # registros já rotulados "régua", com deslocamento mediano zero. Se
        # fosse outra referência, apareceria ali como diferença constante.
        "referencia": "régua",
        "abrigo": bruto.get("abrigo"),
        "abrigo_codigo": bruto.get("abrigo_codigo"),
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--seco", action="store_true", help="mostra o que faria, sem gravar")
    args = ap.parse_args()

    try:
        pdf = carregar_pdf()
    except (OSError, ValueError, KeyError) as erro:
        print(f"não deu para ler {BRUTO}: {erro}", file=sys.stderr)
        print("rode antes: python3 scripts/extrair_blumenau_2014.py", file=sys.stderr)
        return 1

    arquivo = DADOS / "cotas-ruas.json"
    dados = json.loads(arquivo.read_text(encoding="utf-8"))
    cadastro = [c for c in dados["cotas"]
                if c.get("cidade") == CIDADE and c.get("data_fonte") != DATA_FONTE]

    pares = parear(pdf, cadastro)
    divergem = [p for p in pares if not p["bate"]]
    print(f"conferência: {len(pares) - len(divergem)} de {len(pares)} pontos batem ao centavo")
    for p in divergem[:5]:
        print(f"  DIVERGE — {p['rua']} ({p['ponto']}): nosso {p['nosso_m']:.2f}, "
              f"PDF {p['pdf_m']:.2f}")
    if not confirmado(pares):
        print(
            "\nRECUSADO: o documento oficial não confirma a relação que está no\n"
            "cadastro. Subir a confiança dessas cotas agora seria carimbar de\n"
            "'oficial direto' um número que as duas fontes discordam. Investigar\n"
            "as divergências antes.",
            file=sys.stderr,
        )
        return 2

    confirmados, com_abrigo = enriquecer(cadastro, pdf)
    print(f"{confirmados} registros passam a citar o PDF e sobem para confiança alta")
    print(f"{com_abrigo} ganham o abrigo, que a relação da imprensa não trazia")

    # Contra TODOS os registros de Blumenau, inclusive os que esta importação já
    # gravou antes. `cadastro` exclui os de 2014-06 de propósito, para a
    # conferência não comparar o PDF com ele mesmo — mas usar essa lista aqui
    # faria a segunda execução não enxergar o que a primeira gravou e reimportar
    # os 104 pontos a cada rodada.
    de_blumenau = [c for c in dados["cotas"] if c.get("cidade") == CIDADE]
    candidatos = sem_par_no_cadastro(pdf, de_blumenau)
    novos = [r for r in (como_registro(b) for b in candidatos) if r]
    print(f"{len(novos)} pontos novos entram (ruas e trechos que só o PDF tem)")
    recusados = len(candidatos) - len(novos)
    if recusados:
        print(f"{recusados} ficam de fora: a própria fonte não identificou a rua")

    if args.seco:
        for r in novos[:5]:
            print(f"  {r['cota_m']:5.2f} m  {r['rua'][:30]:32} {r['bairro'] or '':16} "
                  f"{(r['abrigo'] or '')[:30]}")
        return 0

    dados["cotas"] = dados["cotas"] + novos
    campos = dados.setdefault("_meta", {}).setdefault("campos", {})
    campos.setdefault("abrigo", "abrigo indicado pela Defesa Civil para aquela rua, "
                                "quando a fonte informa")
    campos.setdefault("abrigo_codigo", "o código do abrigo na fonte (ex.: E9)")
    arquivo.write_text(json.dumps(dados, ensure_ascii=False, indent=2) + "\n",
                       encoding="utf-8")
    print(f"\ngravado em {arquivo} ({date.today().isoformat()})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
