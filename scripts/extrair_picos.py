#!/usr/bin/env python3
"""Encontra os picos de cheia na série coletada e PROPÕE registros para enchentes.json.

Por que existe: dos 116 registros de `enchentes.json`, só 2 têm o horário do
pico. Sem horário não dá para medir quanto tempo a cheia leva de uma cidade
até a outra, e os tempos de descida continuam vindo do hidrograma de projeto da
JICA — um evento sintético — em vez de cheias que aconteceram. Este script lê a
série que o coletor foi juntando e destila dela o que fica para sempre: o pico
de cada cidade em cada evento, com data e hora.

O que ele NÃO faz: gravar sozinho. O padrão é imprimir a proposta para alguém
conferir contra o boletim da Defesa Civil. Dado de enchente não entra no
arquivo sem uma pessoa olhar. `--escrever` existe para depois da conferência,
e recusa duplicar registro que já esteja lá.

Uso:
    python3 scripts/extrair_picos.py                      # propõe, não grava
    python3 scripts/extrair_picos.py --mes 2026-08        # só um mês
    python3 scripts/extrair_picos.py --cidade blumenau
    python3 scripts/extrair_picos.py --escrever           # grava o que propôs
"""

from __future__ import annotations

import argparse
import gzip
import json
import sys
from datetime import datetime, timedelta
from pathlib import Path

from comum import DADOS, cota_de_referencia, grava_json, le_json

SERIE = DADOS / "tempo-real"

#: Intervalo sem leitura acima da cota que separa duas cheias. Uma cheia do
#: Itajaí-Açu leva mais de um dia para passar; 18 h de rio abaixo da cota
#: separa episódios sem partir um só em pedaços.
INTERVALO_ENTRE_EVENTOS_H = 18

#: Mínimo de leituras acima da cota para chamar de evento. Uma leitura isolada
#: acima do limiar é mais provavelmente falha de sensor que cheia.
MIN_LEITURAS = 2

#: Variação entre leituras vizinhas acima da qual o valor é marcado como
#: suspeito. NÃO é descartado: em 2026 Blumenau subiu mais de 4 m em menos de
#: 24 h, e jogar fora o extremo é justamente perder o que importa.
SALTO_SUSPEITO_M_POR_H = 1.5


class Leitura:
    __slots__ = ("quando", "nivel_m", "estacao")

    def __init__(self, quando: datetime, nivel_m: float, estacao: str):
        self.quando = quando
        self.nivel_m = nivel_m
        self.estacao = estacao


class Evento:
    def __init__(self, leituras: list[Leitura]):
        self.leituras = leituras
        pico = max(leituras, key=lambda l: l.nivel_m)
        self.pico_m = pico.nivel_m
        self.quando = pico.quando
        self.inicio = leituras[0].quando
        self.fim = leituras[-1].quando
        self.estacoes = sorted({l.estacao for l in leituras})

    @property
    def suspeitos(self) -> list[Leitura]:
        """Leituras com salto grande demais em relação à anterior."""
        fora = []
        for anterior, atual in zip(self.leituras, self.leituras[1:]):
            horas = (atual.quando - anterior.quando).total_seconds() / 3600
            if horas <= 0:
                continue
            if abs(atual.nivel_m - anterior.nivel_m) / horas > SALTO_SUSPEITO_M_POR_H:
                fora.append(atual)
        return fora


def arquivos_da_serie(mes: str | None) -> list[Path]:
    if not SERIE.exists():
        return []
    padroes = [f"{mes}.ndjson", f"{mes}.ndjson.gz"] if mes else ["*.ndjson", "*.ndjson.gz"]
    achados: list[Path] = []
    for padrao in padroes:
        achados.extend(sorted(SERIE.glob(padrao)))
    return achados


def ler_serie(mes: str | None) -> dict[tuple[str, str], list[Leitura]]:
    """Leituras agrupadas por (rio, cidade)."""
    por_cidade: dict[tuple[str, str], list[Leitura]] = {}
    for arquivo in arquivos_da_serie(mes):
        abrir = gzip.open if arquivo.suffix == ".gz" else open
        with abrir(arquivo, "rt", encoding="utf-8") as f:
            for numero, linha in enumerate(f, start=1):
                linha = linha.strip()
                if not linha:
                    continue
                try:
                    d = json.loads(linha)
                    quando = datetime.fromisoformat(d["medido_em"])
                    nivel = float(d["nivel_m"])
                except (ValueError, KeyError, TypeError) as e:
                    print(f"aviso: {arquivo.name}:{numero} ignorada ({e})", file=sys.stderr)
                    continue
                if not d.get("rio") or not d.get("cidade"):
                    continue  # estação não mapeada para uma cidade do projeto
                chave = (d["rio"], d["cidade"])
                por_cidade.setdefault(chave, []).append(
                    Leitura(quando, nivel, d.get("estacao", "?"))
                )
    for leituras in por_cidade.values():
        leituras.sort(key=lambda l: l.quando)
    return por_cidade


def separar_eventos(leituras: list[Leitura], limiar: float) -> list[Evento]:
    """Períodos acima da cota, separados por INTERVALO_ENTRE_EVENTOS_H sem cheia."""
    acima = [l for l in leituras if l.nivel_m >= limiar]
    if not acima:
        return []

    grupos: list[list[Leitura]] = [[acima[0]]]
    for anterior, atual in zip(acima, acima[1:]):
        if atual.quando - anterior.quando > timedelta(hours=INTERVALO_ENTRE_EVENTOS_H):
            grupos.append([atual])
        else:
            grupos[-1].append(atual)

    return [Evento(g) for g in grupos if len(g) >= MIN_LEITURAS]


def ja_registrado(eventos_json: list[dict], rio: str, cidade: str, data: str) -> bool:
    return any(e["rio"] == rio and e["cidade"] == cidade and e["data"] == data for e in eventos_json)


def main() -> int:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument("--mes", help="analisa só um mês (AAAA-MM)")
    ap.add_argument("--cidade", help="analisa só uma cidade (id de estacoes.json)")
    ap.add_argument("--limiar", type=float, help="cota mínima, para cidades sem cota cadastrada")
    ap.add_argument("--escrever", action="store_true", help="grava as propostas em enchentes.json")
    args = ap.parse_args()

    por_cidade = ler_serie(args.mes)
    if not por_cidade:
        print(
            f"Nenhuma leitura em {SERIE.relative_to(DADOS.parent)}. "
            "Rode scripts/coleta_niveis.py primeiro — a série é construída ao longo do tempo, "
            "e só cobre cheias que aconteceram depois de a coleta começar.",
        )
        return 0

    enchentes = le_json("enchentes.json")
    propostas: list[dict] = []

    for (rio, cidade), leituras in sorted(por_cidade.items()):
        if args.cidade and cidade != args.cidade:
            continue

        limiar, nome_cota = (args.limiar, "informada na linha de comando") if args.limiar else \
            cota_de_referencia(rio, cidade)
        if limiar is None:
            print(
                f"{cidade} ({rio}): sem cota de referência em estacoes.json. "
                f"{len(leituras)} leituras guardadas; use --limiar para analisar mesmo assim."
            )
            continue

        eventos = separar_eventos(leituras, limiar)
        print(
            f"\n{cidade} ({rio}): {len(leituras)} leituras, "
            f"cota de {nome_cota} = {limiar:.2f} m -> {len(eventos)} evento(s)"
        )

        for ev in eventos:
            data = ev.quando.date().isoformat()
            hora = ev.quando.strftime("%H:%M")
            marca = " [JÁ REGISTRADO]" if ja_registrado(enchentes["eventos"], rio, cidade, data) else ""
            print(
                f"  pico {ev.pico_m:.2f} m em {data} {hora}"
                f" | acima da cota de {ev.inicio:%d/%m %H:%M} a {ev.fim:%d/%m %H:%M}"
                f" | {len(ev.leituras)} leituras{marca}"
            )
            for s in ev.suspeitos:
                print(
                    f"     ATENÇÃO: salto grande até {s.nivel_m:.2f} m em {s.quando:%d/%m %H:%M}"
                    " — pode ser subida rápida real ou falha de sensor. Confira antes de aceitar."
                )
            if marca:
                continue
            propostas.append({
                "rio": rio,
                "cidade": cidade,
                "data": data,
                "hora": hora,
                "pico_m": round(ev.pico_m, 2),
                "confianca": "alta",
                "fonte": f"Defesa Civil de Itajaí, leitura automática ({', '.join(ev.estacoes)})",
            })

    if not propostas:
        print("\nNenhuma proposta nova.")
        return 0

    print(f"\n{len(propostas)} registro(s) propostos:")
    for p in propostas:
        print("  " + json.dumps(p, ensure_ascii=False))

    if not args.escrever:
        print(
            "\nNada foi gravado. Confira cada pico contra o boletim da Defesa Civil "
            "e rode de novo com --escrever para incluí-los em enchentes.json."
        )
        return 0

    enchentes["eventos"].extend(propostas)
    enchentes["eventos"].sort(key=lambda e: (e["rio"], e["cidade"], e["data"].ljust(10, "0")))
    grava_json("enchentes.json", enchentes)
    print(f"\nenchentes.json atualizado com {len(propostas)} registro(s).")
    print("Rode scripts/validar_dados.py antes de commitar.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
