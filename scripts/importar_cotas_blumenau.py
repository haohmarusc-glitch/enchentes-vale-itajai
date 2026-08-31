#!/usr/bin/env python3
"""
Importa as 1.938 cotas por rua de Blumenau.

De onde vem: a relação da Defesa Civil de Blumenau (2023), publicada pela NSC
Total num gráfico Flourish. O arquivo bruto está em
`data/brutos/blumenau-cotas-ruas-2023.json` para a importação ser conferível e
repetível — sem ele, o resultado seria um número de onde ninguém sabe.

Por que não veio do AlertaBlu: o `robots.txt` de lá proíbe acesso automatizado,
e essa recusa está registrada em `docs/cotas-de-ruas.md`. Esta tabela é a mesma
relação reproduzida por um veículo de imprensa — por isso `confianca: media`,
como já eram os sete registros que tínhamos.

**Verificação da referência, feita antes de importar:** os sete registros que já
estavam no arquivo — vindos da mesma relação, por outro caminho — aparecem nesta
tabela com o MESMO valor, do 7,40 m da São Rafael ao 7,95 m da Max Aldemann. É
a régua da Ponte Adolfo Konder, que é a referência que as cotas de rua exigem
(REGRA BLOQUEANTE do CLAUDE.md, item 4).

Duas decisões que o dado impôs:

* **A identidade inclui a cota.** Vinte e dois pares (rua, ponto) se repetem
  com cotas DIFERENTES — são pontos distintos que a fonte descreve igual
  ("sem número", "defronte ao autoshopping"). Uma chave sem a cota juntaria os
  dois e perderia 22 registros calados.
* **Os sete que já estão ficam.** Eles são os mesmos pontos, e têm os acentos
  que esta tabela perdeu ("Rua Sao Rafael"). O importador pula os equivalentes
  em vez de sobrescrever o texto melhor pelo pior.

Uso:
    python3 scripts/importar_cotas_blumenau.py --seco
    python3 scripts/importar_cotas_blumenau.py
"""

import argparse
import json
import re
import sys
import unicodedata
from datetime import date

from comum import DADOS

CIDADE = "blumenau"
RIO = "itajai-acu"
BRUTO = DADOS / "brutos" / "blumenau-cotas-ruas-2023.json"
ARQUIVO = DADOS / "cotas-ruas.json"

#: Nenhuma régua desta bacia chega perto disso.
COTA_MAXIMA_M = 25.0

FONTE = ("Defesa Civil de Blumenau — relação de cotas por rua (2023), reproduzida pela NSC "
         "Total (visualização Flourish 3801020). Bruto em "
         "data/brutos/blumenau-cotas-ruas-2023.json")


def normalizar(texto: str) -> str:
    """Sem acento, sem maiúscula, sem espaço dobrado — só para COMPARAR."""
    s = "".join(
        c for c in unicodedata.normalize("NFD", (texto or "").lower())
        if unicodedata.category(c) != "Mn"
    )
    return re.sub(r"\s+", " ", s.replace(".", "").strip())


def chave(registro: dict) -> tuple:
    """
    Identidade de um ponto: cidade, rua, ponto E cota.

    A cota entra porque a fonte descreve pontos diferentes com o mesmo texto.
    Sem ela, "Rua Franz Volles / sem número" a 11,10, 14,05 e 16,95 m viraria
    um registro só.
    """
    return (
        registro.get("cidade"),
        normalizar(registro.get("rua", "")),
        normalizar(registro.get("ponto") or ""),
        registro.get("cota_m"),
    )


def como_registro(bruto: dict, quando: str) -> dict:
    return {
        "cidade": CIDADE,
        "rio": RIO,
        "rua": bruto["rua"],
        "bairro": bruto.get("bairro") or None,
        "ponto": bruto.get("ponto") or None,
        "cota_m": bruto["cota_m"],
        "fonte": FONTE,
        "data_fonte": "2023",
        "confianca": "media",
        "referencia": "régua",
    }


def ler_bruto() -> tuple[list[dict], dict]:
    dados = json.loads(BRUTO.read_text(encoding="utf-8"))
    return dados.get("cotas", []), dados.get("_meta", {})


def separar(brutos: list[dict]) -> tuple[list[dict], list[str]]:
    """Os que entram e os que foram recusados, com o motivo de cada recusa."""
    bons, recusas = [], []
    for b in brutos:
        cota = b.get("cota_m")
        if not isinstance(cota, (int, float)) or isinstance(cota, bool):
            recusas.append(f"{b.get('rua', '?')}: cota {cota!r} não é número")
            continue
        if not 0 < float(cota) < COTA_MAXIMA_M:
            recusas.append(f"{b.get('rua', '?')}: cota {cota} fora da faixa de nível de rio")
            continue
        if not (b.get("rua") or "").strip():
            recusas.append(f"registro sem nome de rua (cota {cota})")
            continue
        bons.append(b)
    return bons, recusas


def mesclar(existentes: list[dict], novos: list[dict]) -> tuple[list[dict], int, int]:
    """
    União pela identidade. Cidade nenhuma perde registro, e um ponto que já
    está com o nome mais bem escrito não é sobrescrito pelo pior.
    """
    indice = {chave(r): i for i, r in enumerate(existentes)}
    # Também por (rua, cota): é assim que os sete antigos, com acento e com
    # outro texto de ponto, casam com os mesmos pontos desta tabela.
    por_rua_cota = {(normalizar(r.get("rua", "")), r.get("cota_m"))
                    for r in existentes if r.get("cidade") == CIDADE}

    saida = list(existentes)
    novos_n = pulados = 0
    for r in novos:
        k = chave(r)
        if k in indice:
            saida[indice[k]] = r
            pulados += 1
            continue
        if (normalizar(r["rua"]), r["cota_m"]) in por_rua_cota:
            pulados += 1  # já está, com texto melhor
            continue
        saida.append(r)
        novos_n += 1
    return saida, novos_n, pulados


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--seco", action="store_true", help="mostra o que faria, sem gravar")
    args = ap.parse_args()

    brutos, meta = ler_bruto()
    print(f"bruto: {len(brutos)} registro(s) — {meta.get('origem', 'sem origem declarada')}")
    bons, recusas = separar(brutos)
    print(f"aceitos: {len(bons)} · recusados: {len(recusas)}")
    for m in recusas[:20]:
        print(f"  {m}")

    if not bons:
        print("nada a importar.")
        return 1

    valores = [float(b["cota_m"]) for b in bons]
    print(f"faixa: {min(valores):.2f} m a {max(valores):.2f} m")
    print(f"ruas distintas: {len({normalizar(b['rua']) for b in bons})}")

    quando = date.today().isoformat()
    registros = [como_registro(b, quando) for b in bons]

    base = json.loads(ARQUIVO.read_text(encoding="utf-8"))
    antes = len(base.get("cotas", []))
    mesclados, novos, pulados = mesclar(base.get("cotas", []), registros)
    print(f"\ncotas-ruas.json: {antes} → {len(mesclados)} "
          f"({novos} novo(s), {pulados} já presente(s))")

    if args.seco:
        print("\n--seco: nada gravado.")
        return 0

    base["cotas"] = mesclados
    ARQUIVO.write_text(json.dumps(base, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"gravado em {ARQUIVO}")
    print("Agora rode: python3 scripts/validar_dados.py")
    return 0


if __name__ == "__main__":
    sys.exit(main())
