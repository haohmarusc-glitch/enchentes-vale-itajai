#!/usr/bin/env python3
"""Lê o inventário da API da ANA e responde três perguntas sobre a nossa bacia.

POR QUE EXISTE (08/09/2026)
A rota `HidroInventarioEstacoes` devolveu 1.808 estações de SC, com 69 campos
cada. A primeira análise foi um heredoc colado no terminal e ele QUEBROU no meio
da lista, num `i.get(chave, "")[:7]`: quando a chave EXISTE com valor `None`, o
`.get` devolve `None` e o default nunca entra. A saída ficou truncada e parecia
dizer que a bacia do Itajaí não tem estação de nível — quando o que houve foi um
crash antes de chegar nelas. Análise que morre no meio mente por omissão.

Por isso isto é um script com teste, e não um bloco para colar.

TRÊS PERGUNTAS:

1. As estações que o projeto já nomeia estão no inventário, e o que ele diz
   delas? Em especial `Tipo_Estacao_Telemetrica` — é o campo que explica por que
   a série telemétrica devolveu zero para as cinco candidatas.
2. Que estações de NÍVEL existem nos rios da bacia? Filtro por COORDENADA e por
   NOME DO RIO: a caixa de coordenadas sozinha trouxe Tijucas, Itapocu e
   Cubatão, que são outras bacias.
3. Quantos registros têm o campo `UF_Estacao` incoerente com a coordenada? (Na
   leitura de 08/09/2026: 1 em 1.808 — um caso isolado, não um defeito
   sistêmico. Fica medido para não virar lenda em nenhuma das duas direções.)

Uso:
    python3 scripts/analisar_inventario_ana.py data/brutos/ana-inventario-api-2026-09-08.json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

#: Caixa folgada de Santa Catarina, para achar UF incoerente com coordenada.
CAIXA_SC = (-29.5, -25.8, -54.0, -48.2)

#: Caixa da bacia do Itajaí. Sozinha ela NÃO basta — vizinhas caem dentro.
CAIXA_ITAJAI = (-27.80, -26.30, -50.40, -48.40)

#: Nomes de rio que são a bacia. O `Rio_Nome` da ANA é o segundo filtro, e é
#: ele que separa o Itajaí do Tijucas e do Itapocu dentro da mesma caixa.
RIOS_DA_BACIA = ("ITAJA", "HERCILIO", "HERCÍLIO", "BENEDITO", "LUIZ ALVES", "TROMBUDO")

#: Estações que o projeto já nomeia, com o papel de cada uma. Recusa também é
#: papel: quatro destas estão em `codigo_ana_nao_e` e o rótulo diz isso, para a
#: saída nunca sugerir que sondar equivale a vincular.
NOSSAS = {
    "83050000": "Taió (vinculada)",
    "83145140": "Ituporanga (vinculada)",
    "83300200": "Rio do Sul (vinculada)",
    "83800002": "Blumenau (vinculada)",
    "83840000": "Gaspar (vinculada)",
    "83900000": "Brusque (vinculada)",
    "83440000": "Ibirama (CANDIDATA, decisão aberta)",
    "83250000": "ITUPORANGA-ANA (RECUSADA)",
    "83520000": "WARNOW (RECUSADA)",
    "83870001": "ILHOTA-JUSANTE (RECUSADA)",
    "83892990": "SALSEIRO (RECUSADA)",
    "83892998": "BOTUVERA-MONTANTE (RECUSADA)",
}


def texto(valor, corte: int | None = None) -> str:
    """Nunca fatia `None`.

    Foi exatamente isto que derrubou a análise de 08/09/2026: `.get(k, "")`
    devolve `None` quando a chave existe com valor nulo, e `None[:7]` explode.
    """
    saida = "—" if valor in (None, "") else str(valor)
    return saida[:corte] if corte else saida


def numero(valor) -> float | None:
    try:
        return float(valor)
    except (TypeError, ValueError):
        return None


def dentro(item: dict, caixa: tuple[float, float, float, float]) -> bool:
    lat, lon = numero(item.get("Latitude")), numero(item.get("Longitude"))
    if lat is None or lon is None:
        return False
    sul, norte, oeste, leste = caixa
    return sul <= lat <= norte and oeste <= lon <= leste


def mede_nivel(item: dict) -> bool:
    return item.get("Tipo_Estacao_Escala") == "1" or \
        item.get("Tipo_Estacao_Registrador_Nivel") == "1"


def e_da_bacia(item: dict) -> bool:
    """Coordenada E nome do rio. Uma só das duas erra, e de jeitos diferentes."""
    if not dentro(item, CAIXA_ITAJAI):
        return False
    rio = texto(item.get("Rio_Nome")).upper()
    return any(n in rio for n in RIOS_DA_BACIA)


def uf_incoerente(itens: list[dict]) -> list[dict]:
    return [i for i in itens if not dentro(i, CAIXA_SC) and numero(i.get("Latitude")) is not None]


def _linha(item: dict) -> str:
    return (f"{texto(item.get('codigoestacao')):>9} "
            f"{texto(item.get('Estacao_Nome'), 30):<30} "
            f"rio={texto(item.get('Rio_Nome'), 24):<24} "
            f"mun={texto(item.get('Municipio_Nome'), 16):<16} "
            f"tele={texto(item.get('Tipo_Estacao_Telemetrica'))} "
            f"oper={texto(item.get('Operando'))} "
            f"escala={texto(item.get('Data_Periodo_Escala_Inicio'), 7)}"
            f"→{texto(item.get('Data_Periodo_Escala_Fim'), 7)} "
            f"telem={texto(item.get('Data_Periodo_Telemetrica_Inicio'), 7)}"
            f"→{texto(item.get('Data_Periodo_Telemetrica_Fim'), 7)}")


def relatorio(itens: list[dict]) -> None:
    print(f"inventário: {len(itens)} estações\n")

    print("=== 1. AS ESTAÇÕES QUE O PROJETO JÁ NOMEIA ===")
    por_codigo = {texto(i.get("codigoestacao")): i for i in itens}
    for codigo, papel in NOSSAS.items():
        item = por_codigo.get(codigo)
        if item is None:
            print(f"{codigo} {papel:<36} ⚠️ NÃO ESTÁ no inventário de SC")
            continue
        print(f"{codigo} {papel:<36} {_linha(item)}")

    print("\n=== 2. RIOS DA BACIA, ESTAÇÕES QUE MEDEM NÍVEL ===")
    bacia = [i for i in itens if e_da_bacia(i) and mede_nivel(i)]
    for item in sorted(bacia, key=lambda i: texto(i.get("Rio_Nome"))):
        print(_linha(item))
    vivas = [i for i in bacia if i.get("Tipo_Estacao_Telemetrica") == "1"
             and i.get("Operando") == "1"]
    print(f"\ntotal nos rios da bacia: {len(bacia)}  |  telemétricas E operando: {len(vivas)}")
    if vivas:
        print("Candidatas a NÍVEL AO VIVO (⚠️ sondar não é vincular — a conferência "
              "de régua contra o pino da cidade é outra etapa):")
        for item in vivas:
            print(f"   {texto(item.get('codigoestacao'))} {texto(item.get('Estacao_Nome'))}")

    print("\n=== 3. UF_Estacao INCOERENTE COM A COORDENADA ===")
    fora = uf_incoerente(itens)
    print(f"{len(fora)} de {len(itens)} registros dizem SC e caem fora da caixa do estado.")
    for item in fora[:10]:
        print(f"   {texto(item.get('codigoestacao'))} {texto(item.get('Estacao_Nome'), 28):<28} "
              f"{texto(item.get('Municipio_Nome'))} "
              f"({texto(item.get('Latitude'))}, {texto(item.get('Longitude'))}) "
              f"bacia={texto(item.get('Bacia_Nome'))}")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("arquivo", type=Path, help="bruto salvo por scripts/sonda_ana_api.py")
    args = ap.parse_args()

    if not args.arquivo.exists():
        print(f"ERRO: {args.arquivo} não existe. Rode antes: "
              "python3 scripts/sonda_ana_api.py", file=sys.stderr)
        return 1

    corpo = json.loads(args.arquivo.read_text(encoding="utf-8"))
    itens = corpo.get("items") if isinstance(corpo, dict) else corpo
    if not isinstance(itens, list):
        print(f"ERRO: {args.arquivo} não tem lista 'items' "
              f"(chaves: {list(corpo)[:8]})", file=sys.stderr)
        return 1

    relatorio(itens)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
