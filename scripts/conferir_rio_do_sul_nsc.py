#!/usr/bin/env python3
"""
Confere as 554 cotas de Rio do Sul contra uma transcrição independente da mesma tabela.

Temos duas leituras da "Cota de Cheias por Rua" da Defesa Civil de Rio do Sul:

* a nossa, com 554 ruas, raspada do próprio portal
  (`importar_cotas_rio_do_sul.py`, `confianca: alta`, com mínima E máxima);
* a da NSC Total de 14/08/2026, com 545 ruas, em
  `data/brutos/rio-do-sul-nsc-2026-08-14.json` (`confianca: media`, só a mínima).

Duas fontes independentes da mesma tabela é a oportunidade de conferência mais
barata que este projeto tem, e o resultado é bom: das 544 ruas que as duas
publicam, **544 trazem a mesma cota mínima, ao centavo**. Nenhuma divergência.

Também mostra o que só uma das duas tem:

* seis nomes que parecem "só da NSC" são a mesma rua com outra grafia
  (Amábile/Amabilio Testoni, Menegetti/Meneghetti, Guaiâniazes/Guaianazes,
  Gutenberg/Gutemberg, Frankenberger/Frankemberger, Jurací/Juracy Dalfovo) e
  trazem cota idêntica;
* **uma rua a NSC tem e nós não: Visconde de Cairu, 19,01 m.** Não é grafia de
  nenhuma outra — a nossa lista tem "Visconde de Mauá", que é outra rua a
  10,89 m, e tem "Hilberto Bruch" a 19,01 m, que a NSC também publica
  separadamente. O portal declara 555 itens e nós tínhamos 554: é esta.
  Entrou no cadastro com a fonte da NSC e `confianca: media`, não `alta`, porque
  não veio do portal;
* dez ruas que só nós temos, porque a transcrição do jornal saiu com 545 de 555.

Uso:
    python3 scripts/conferir_rio_do_sul_nsc.py
"""

import json
import sys
import unicodedata
from typing import Any

from comum import DADOS

CIDADE = "rio-do-sul"
BRUTO = "brutos/rio-do-sul-nsc-2026-08-14.json"
TOLERANCIA_M = 0.005

PREFIXOS = ("RUA ", "AV. ", "AV ", "AVENIDA ", "R. ", "TRAVESSA ", "SERVIDAO ",
            "ESTRADA GERAL ", "ESTRADA ")


def normalizar(texto: Any) -> str:
    sem_acento = unicodedata.normalize("NFD", str(texto or ""))
    sem_acento = sem_acento.encode("ascii", "ignore").decode().upper()
    for prefixo in PREFIXOS:
        if sem_acento.startswith(prefixo):
            sem_acento = sem_acento[len(prefixo):]
            break
    return " ".join(sem_acento.replace(".", " ").replace("-", " ").split())


def e_numero(valor: Any) -> bool:
    return isinstance(valor, (int, float)) and not isinstance(valor, bool)


def por_rua(registros: list[dict[str, Any]], campo: str) -> dict[str, float]:
    """Menor cota publicada para cada rua, pela chave normalizada."""
    saida: dict[str, float] = {}
    for registro in registros:
        if not e_numero(registro.get(campo)):
            continue
        chave = normalizar(registro.get("rua"))
        valor = registro[campo]
        if chave not in saida or valor < saida[chave]:
            saida[chave] = valor
    return saida


def comparar(nossos: dict[str, float], deles: dict[str, float]) -> dict[str, Any]:
    comuns = sorted(set(nossos) & set(deles))
    divergentes = [
        {"rua": k, "nosso_m": nossos[k], "deles_m": deles[k]}
        for k in comuns
        if abs(nossos[k] - deles[k]) >= TOLERANCIA_M
    ]
    return {
        "comuns": len(comuns),
        "iguais": len(comuns) - len(divergentes),
        "divergentes": divergentes,
        "so_nosso": sorted(set(nossos) - set(deles)),
        "so_deles": sorted(set(deles) - set(nossos)),
    }


def main() -> int:
    try:
        brutos = json.loads((DADOS / BRUTO).read_text(encoding="utf-8"))["cotas"]
    except (OSError, ValueError, KeyError) as erro:
        print(f"não deu para ler {BRUTO}: {erro}", file=sys.stderr)
        return 1

    nossos_reg = [
        r
        for r in json.loads((DADOS / "cotas-ruas.json").read_text(encoding="utf-8"))["cotas"]
        if r.get("cidade") == CIDADE
    ]
    nossos = por_rua(nossos_reg, "cota_m")
    deles = por_rua(brutos, "cota_minima_m")
    resultado = comparar(nossos, deles)

    print(f"nosso cadastro: {len(nossos_reg)} registros, {len(nossos)} ruas")
    print(f"transcrição NSC: {len(brutos)} registros, {len(deles)} ruas\n")
    print(f"ruas em comum: {resultado['comuns']}")
    print(f"  com a mesma cota mínima ao centavo: {resultado['iguais']}")
    print(f"  divergentes: {len(resultado['divergentes'])}")
    for caso in resultado["divergentes"]:
        print(f"    {caso['rua'][:40]:42} nosso={caso['nosso_m']:6.2f}  NSC={caso['deles_m']:6.2f}")

    print(f"\nsó na NSC: {len(resultado['so_deles'])}")
    for rua in resultado["so_deles"]:
        print(f"    {rua[:40]:42} {deles[rua]:6.2f}")
    print(f"\nsó no nosso: {len(resultado['so_nosso'])}")

    if resultado["divergentes"]:
        print("\nATENÇÃO: as duas fontes discordam de valor. Conferir antes de publicar.")
        return 2
    print("\nNenhuma divergência de valor entre as duas fontes.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
