#!/usr/bin/env python3
"""Calcula quanto tempo a cheia leva de verdade para descer entre duas cidades.

Como funciona: para cada par de cidades vizinhas no mesmo rio, procura eventos
em que AS DUAS tenham data **e hora** de pico registradas em `enchentes.json`,
e mede a diferença. A faixa publicada em `transito.json` passa a ser o mínimo e
o máximo observados, com confiança `alta` — deixando de ser estimativa de
literatura.

Hoje nenhum registro tem o campo `hora`, então o script não altera nada e
apenas relata o que falta. Isso é proposital: a única coisa pior que não ter
tempo de trânsito é ter um número inventado, porque é com ele que alguém
decide quando sair de casa.

Uso:

    python3 scripts/calibrar_transito.py            # só relata
    python3 scripts/calibrar_transito.py --escrever # grava em transito.json
"""

from __future__ import annotations

import argparse
from collections import defaultdict
from datetime import datetime, timedelta

from comum import grava_json, le_json

#: Mínimo de eventos medidos para substituir a estimativa de literatura.
MIN_EVENTOS = 3
#: Diferença máxima entre picos de cidades vizinhas ainda tratada como o mesmo evento.
MAX_HORAS = 120


def instante(ev: dict) -> datetime | None:
    """Data + hora do pico, ou None quando o registro não tem hora."""
    if len(ev.get("data", "")) != 10 or not ev.get("hora"):
        return None
    try:
        return datetime.fromisoformat(f"{ev['data']}T{ev['hora']}")
    except ValueError:
        return None


def pares_vizinhos() -> list[tuple[str, str, str]]:
    """(rio, cidade de montante, cidade de jusante) para cada par consecutivo."""
    estacoes = le_json("estacoes.json")
    saida = []
    for rio_id, rio in estacoes["rios"].items():
        ordenadas = sorted(rio["cidades"], key=lambda c: c["ordem"])
        for a, b in zip(ordenadas, ordenadas[1:]):
            saida.append((rio_id, a["id"], b["id"]))
    return saida


def medicoes(eventos: list[dict], rio: str, de: str, para: str) -> list[float]:
    """Horas entre o pico de montante e o de jusante, por evento."""
    por_cidade: dict[str, list[dict]] = defaultdict(list)
    for ev in eventos:
        if ev["rio"] == rio:
            por_cidade[ev["cidade"]].append(ev)

    horas: list[float] = []
    for ev_montante in por_cidade.get(de, []):
        t0 = instante(ev_montante)
        if t0 is None:
            continue
        candidatos = []
        for ev_jusante in por_cidade.get(para, []):
            t1 = instante(ev_jusante)
            if t1 is None:
                continue
            delta = (t1 - t0) / timedelta(hours=1)
            # A água desce: o pico a jusante vem depois do de montante.
            if 0 < delta <= MAX_HORAS:
                candidatos.append(delta)
        # Mais de um candidato = ambíguo; medir o errado é pior que não medir.
        if len(candidatos) == 1:
            horas.append(candidatos[0])
    return horas


def main() -> int:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument(
        "--escrever", action="store_true", help="grava os trechos calibrados em transito.json"
    )
    args = ap.parse_args()

    eventos = le_json("enchentes.json")["eventos"]
    transito = le_json("transito.json")
    por_chave = {(t["rio"], t["de"], t["para"]): t for t in transito["trechos"]}

    com_hora = sum(1 for ev in eventos if instante(ev) is not None)
    print(f"{com_hora} de {len(eventos)} registros têm data e hora de pico.\n")

    calibrados = 0
    for rio, de, para in pares_vizinhos():
        horas = medicoes(eventos, rio, de, para)
        atual = por_chave.get((rio, de, para))
        rotulo = f"{rio}: {de} -> {para}"

        if len(horas) < MIN_EVENTOS:
            faltam = MIN_EVENTOS - len(horas)
            estado = (
                f"estimativa atual {atual['horas_min']}–{atual['horas_max']} h "
                f"(confiança {atual['confianca']})"
                if atual
                else "sem trecho cadastrado"
            )
            print(f"{rotulo}: {len(horas)} medição(ões), faltam {faltam} — {estado}")
            continue

        novo = {
            "rio": rio,
            "de": de,
            "para": para,
            "horas_min": round(min(horas), 1),
            "horas_max": round(max(horas), 1),
            "confianca": "alta",
            "fonte": (
                f"Calibrado com {len(horas)} eventos de enchentes.json "
                "(horários de pico registrados)"
            ),
        }
        print(
            f"{rotulo}: {novo['horas_min']}–{novo['horas_max']} h "
            f"a partir de {len(horas)} eventos"
        )
        por_chave[(rio, de, para)] = novo
        calibrados += 1

    if not calibrados:
        print(
            "\nNada a calibrar. Para destravar isto, registre o horário do pico "
            "(campo 'hora', formato HH:MM) nos eventos de enchentes.json — os boletins "
            "das Defesas Civis de Brusque e de Blumenau trazem esse dado."
        )
        return 0

    if not args.escrever:
        print(f"\n{calibrados} trecho(s) calibrável(is). Rode com --escrever para gravar.")
        return 0

    transito["trechos"] = sorted(
        por_chave.values(), key=lambda t: (t["rio"], t["de"], t["para"])
    )
    grava_json("transito.json", transito)
    print(f"\ntransito.json atualizado com {calibrados} trecho(s) calibrado(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
