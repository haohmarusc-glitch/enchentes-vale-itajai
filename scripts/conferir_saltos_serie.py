#!/usr/bin/env python3
"""
Confere se a série publicada tem salto grande demais para ser rio — o sinal de
que réguas de zeros diferentes voltaram a ser misturadas.

POR QUE EXISTE (04/09/2026)
---------------------------
`serie-recente.json` agrupava por (rio, cidade) e jogava fora a estação. Itajaí
tem onze réguas com zeros diferentes, e todas caíam no mesmo vetor. Medido no
arquivo em produção:

    Itajaí no Açu     3,00 -> 0,78 m em 1 min   = 13.320 cm/h
    Itajaí no Mirim   4,15 -> 0,13 m em 10 min  =  2.412 cm/h
    Blumenau          4,60 -> 4,35 m em 5 min   =    300 cm/h

O dado permitia afirmar que o rio desceu 133 metros por hora. Depois de separar
por régua, a MAIOR taxa de toda a bacia caiu para 96 cm/h (DC-01, maré) — as
outras dezesseis ficam abaixo de 85.

DE ONDE VEM O LIMITE
--------------------
Não é chute. Sobre as 48 h publicadas em 04/09, já separadas por régua:

    maior taxa REAL medida         96 cm/h   (DC-01 CEPSUL, estuário)
    menor artefato de MISTURA     300 cm/h   (Blumenau, duas publicações)

`LIMITE_CM_H` fica em 150: acima de tudo que o rio faz de verdade e abaixo de
tudo que a mistura produziu. Aviso que dispara numa cheia de verdade ensina a
ignorar o aviso — o mesmo motivo pelo qual nove réguas de Itajaí não disparam
alarme sozinhas.

POR QUE ISTO NÃO ABORTA A PUBLICAÇÃO
------------------------------------
A proposta original era `raise` antes de publicar. Recusada de propósito: um
salto numa régua derrubaria o arquivo de TODAS as cidades, e o pior momento
para o site ficar sem série é justamente a cheia em que o dado fica estranho.
Isto aqui RELATA — sai não-zero para o vigia e a CI verem —, e quem apaga o
número errado da tela é a guarda do site (`tendencia` devolve null quando a
série mistura réguas).

Uso:
    python3 scripts/conferir_saltos_serie.py
    python3 scripts/conferir_saltos_serie.py --arquivo caminho/serie-recente.json
    python3 scripts/conferir_saltos_serie.py --json
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

from comum import DADOS, estacao_por_titulo

SERIE_RECENTE = DADOS / "tempo-real" / "serie-recente.json"

#: Acima disto não é rio — ver "DE ONDE VEM O LIMITE" no topo.
LIMITE_CM_H = 150.0

#: As réguas de estuário oscilam com a maré por natureza, e a maré é rápida:
#: a DC-01 chega a 96 cm/h sem enchente nenhuma. Elas ganham folga — mas
#: EXPLÍCITA, marcada no cadastro por `alerta_automatico: false`, nunca por
#: omissão. Pular a conferência calado seria não conferir.
LIMITE_ESTUARIO_CM_H = 400.0


def eh_estuario(titulo: str) -> bool:
    """A régua está travada por maré no cadastro?"""
    return (estacao_por_titulo(titulo) or {}).get("alerta_automatico") is False


def por_regua(doc: dict, rio: str, cidade: str) -> dict[str, list[dict]]:
    """
    Os pontos daquela cidade, separados por régua.

    Ponto sem `r`, ou com `r` fora da legenda, cai em `""` — "régua
    desconhecida". Não vai para a primeira da legenda: isso afirmaria um zero de
    medição que o arquivo não disse.
    """
    legenda = (doc.get("reguas") or {}).get(rio, {}).get(cidade, [])
    saida: dict[str, list[dict]] = {}
    for ponto in doc["series"][rio][cidade]:
        indice = ponto.get("r")
        titulo = legenda[indice] if isinstance(indice, int) and 0 <= indice < len(legenda) else ""
        saida.setdefault(titulo, []).append(ponto)
    for pontos in saida.values():
        pontos.sort(key=lambda p: p["medido_em"])
    return saida


def saltos(pontos: list[dict], limite: float) -> list[dict]:
    """Os pares vizinhos cuja variação implica taxa acima do limite."""
    achados = []
    for a, b in zip(pontos, pontos[1:]):
        try:
            ta = datetime.fromisoformat(a["medido_em"])
            tb = datetime.fromisoformat(b["medido_em"])
        except (ValueError, KeyError):
            continue
        horas = (tb - ta).total_seconds() / 3600
        if horas <= 0:
            continue
        taxa = abs(b["nivel_m"] - a["nivel_m"]) / horas * 100
        if taxa > limite:
            achados.append({
                "cm_h": round(taxa),
                "de": a["medido_em"], "nivel_de": a["nivel_m"],
                "para": b["medido_em"], "nivel_para": b["nivel_m"],
            })
    return achados


def conferir(doc: dict) -> list[dict]:
    """Uma linha por (rio, cidade, régua) com problema."""
    problemas = []
    for rio, cidades in (doc.get("series") or {}).items():
        for cidade in cidades:
            grupos = por_regua(doc, rio, cidade)
            anonimos = grupos.get("", [])

            # SÉRIE SEM RÉGUA NENHUMA. É o defeito original — não dá para
            # separar, logo não dá para conferir régua por régua. Pular seria
            # ficar cego justamente no caso que este script existe para pegar:
            # a primeira versão daqui fazia isso, e passou verde no arquivo de
            # 04/09 15:16 que tinha um salto de 13.320 cm/h. A falsificação
            # flagrou. Então o vetor MISTURADO é conferido inteiro, contra o
            # limite de rio — que é o certo, porque se a série fosse mesmo de
            # uma régua só ela obedeceria a ele.
            if len(grupos) == 1 and anonimos:
                achados = saltos(anonimos, LIMITE_CM_H)
                if achados:
                    problemas.append({
                        "rio": rio, "cidade": cidade, "regua": None,
                        "motivo": (f"série SEM RÉGUA e com salto acima de "
                                   f"{LIMITE_CM_H:.0f} cm/h — provavelmente várias "
                                   f"réguas no mesmo vetor"),
                        "pontos": len(anonimos),
                        "saltos": sorted(achados, key=lambda s: -s["cm_h"])[:5],
                    })
                continue

            # Mistura parcial: umas com régua, outras sem.
            if len(anonimos) > 1 and len(grupos) > 1:
                problemas.append({
                    "rio": rio, "cidade": cidade, "regua": None,
                    "motivo": "pontos sem régua no meio de uma série que tem réguas",
                    "pontos": len(anonimos), "saltos": [],
                })
            for titulo, pontos in grupos.items():
                if not titulo:
                    continue
                limite = LIMITE_ESTUARIO_CM_H if eh_estuario(titulo) else LIMITE_CM_H
                achados = saltos(pontos, limite)
                if achados:
                    problemas.append({
                        "rio": rio, "cidade": cidade, "regua": titulo,
                        "motivo": f"salto acima de {limite:.0f} cm/h",
                        "estuario": eh_estuario(titulo),
                        "pontos": len(pontos),
                        "saltos": sorted(achados, key=lambda s: -s["cm_h"])[:5],
                    })
    return problemas


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--arquivo", type=Path, default=SERIE_RECENTE)
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    if not args.arquivo.exists():
        print(f"{args.arquivo} não existe — rode a coleta antes.", file=sys.stderr)
        return 1
    doc = json.loads(args.arquivo.read_text(encoding="utf-8"))

    problemas = conferir(doc)
    if args.json:
        print(json.dumps(problemas, ensure_ascii=False, indent=2))
        return 1 if problemas else 0

    total = sum(len(c) for c in (doc.get("series") or {}).values())
    if not problemas:
        print(f"{total} cidade(s) na série; nenhum salto acima do limite "
              f"({LIMITE_CM_H:.0f} cm/h, {LIMITE_ESTUARIO_CM_H:.0f} nas de estuário).")
        return 0

    print(f"{len(problemas)} problema(s):\n")
    for p in problemas:
        alvo = f"{p['rio']}/{p['cidade']}" + (f"/{p['regua']}" if p["regua"] else "")
        print(f"{alvo}\n       {p['motivo']}")
        for s in p["saltos"]:
            print(f"       {s['cm_h']:6d} cm/h  {s['de'][11:16]} {s['nivel_de']:.2f} m"
                  f"  ->  {s['para'][11:16]} {s['nivel_para']:.2f} m")
        print()
    print("Salto assim quase sempre é RÉGUA MISTURADA, não rio. Confira se cada\n"
          "ponto leva o `r` da régua dele — ver escrever_serie_recente().")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
