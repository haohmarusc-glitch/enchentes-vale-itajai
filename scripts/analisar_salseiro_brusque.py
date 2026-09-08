#!/usr/bin/env python3
"""Lê o histórico da estação SALSEIRO baixado do portal da Defesa Civil de Brusque.

ORIGEM (08/09/2026). O Jefferson baixou pelo botão da página
`defesacivil.brusque.sc.gov.br/estacao/ver/31`, em janelas de um ano, dez
arquivos `.xls` que são HTML (uma `<table>` com `data, historico, chuva, cota,
manual`). Verbatim em `data/brutos/brusque-dc-salseiro-31-historico-2018-2026.tar.gz`.
Cobertura: 22/05/2018 → 18/04/2026, leituras de 15 em 15 min, 226.910 carimbos.

⚠️ A ARMADILHA DESTA FONTE: `cota = 0,00` NÃO É RIO SECO, É LEITURA AUSENTE.
Entre 1,20 m e 1,19 m aparecem quatro `0,00` seguidos. Entre 40% e 57% das
linhas de cada arquivo são zero. Um `min()` ingênuo diria que o Mirim seca
toda semana; uma média ingênua daria metade do nível real. Aqui zero vira
`None`, e há teste travando isso.

⚠️ O QUE ESTA ESTAÇÃO É E NÃO É. A SALSEIRO (ANA 83892990) fica a 6,8 km da
sede de Vidal Ramos e a diferença contra a nossa régua foi MEDIDA em 0,70 m
(08/09/2026). Ela NÃO serve como NÍVEL de Vidal Ramos — está em
`codigo_ana_nao_e`. Mas para TEMPO DE TRÂNSITO o que importa é a HORA do
pico, não o metro: como relógio a montante do Mirim ela vale, e é a primeira
fonte do projeto com resolução de minutos. O Jefferson apontou isso, e é o
ponto mais forte da fonte.

Este script NÃO escreve em data/*.json. Ele mede e imprime: cobertura,
buracos, picos com hora, e o pareamento com os picos de Brusque que já têm
`hora` em enchentes.json. Gravar tempo de trânsito continua decisão humana —
e com MIN_EVENTOS = 3 em calibrar_transito.py, um evento não decide nada.

Uso:
    python3 scripts/analisar_salseiro_brusque.py
    python3 scripts/analisar_salseiro_brusque.py --limiar 3.0
"""

from __future__ import annotations

import argparse
import re
import sys
import tarfile
from collections import Counter
from datetime import datetime, timedelta
from pathlib import Path

from comum import DADOS, le_json

BRUTO = DADOS / "brutos" / "brusque-dc-salseiro-31-historico-2018-2026.tar.gz"

#: Uma linha da tabela HTML: data, historico, chuva, cota, manual.
LINHA = re.compile(
    r"<tr><td>(\d\d/\d\d/\d{4} \d\d:\d\d:\d\d)</td>"
    r"<td>([^<]*)</td><td>([^<]*)</td><td>([^<]*)</td><td>([^<]*)</td></tr>"
)

#: Passo nominal da estação. Buraco = sequência de ausentes maior que isto.
PASSO = timedelta(minutes=15)

#: Cota da SALSEIRO em que o portal declara atenção (fonte ANA, lida em
#: 08/09/2026). É a cota DESTA régua — nunca a de Vidal Ramos.
ATENCAO_SALSEIRO_M = 3.0

#: Dois picos da Salseiro separados por menos que isto são o mesmo evento.
SEPARACAO_DE_EVENTOS = timedelta(days=3)

#: Janela em que um pico da Salseiro e um de Brusque contam como a mesma cheia.
JANELA_DE_PAREAMENTO = timedelta(hours=48)


def cota_ou_nada(texto: str) -> float | None:
    """'1,20' -> 1.20; '0,00' -> None. Zero é ausência, não nível."""
    try:
        valor = float(texto.strip().replace(".", "").replace(",", "."))
    except (AttributeError, ValueError):
        return None
    return valor if valor > 0 else None


def linhas_do_html(html: str) -> list[tuple[datetime, float | None]]:
    saida = []
    for data, _historico, _chuva, cota, _manual in LINHA.findall(html):
        saida.append((datetime.strptime(data, "%d/%m/%Y %H:%M:%S"), cota_ou_nada(cota)))
    return saida


def serie_do_tar(caminho: Path = BRUTO) -> list[tuple[datetime, float | None]]:
    """Todos os arquivos do tar, sem duplicata (as janelas anuais se sobrepõem um dia)."""
    por_carimbo: dict[datetime, float | None] = {}
    with tarfile.open(caminho, "r:gz") as tar:
        for membro in tar.getmembers():
            if not membro.isfile():
                continue
            html = tar.extractfile(membro).read().decode("utf-8", "replace")
            for carimbo, cota in linhas_do_html(html):
                # Se dois arquivos discordam no mesmo carimbo, fica o que TEM valor.
                if carimbo not in por_carimbo or por_carimbo[carimbo] is None:
                    por_carimbo[carimbo] = cota
    return sorted(por_carimbo.items())


def buracos(serie, minimo: timedelta = timedelta(days=1)) -> list[tuple[datetime, datetime, int]]:
    """Sequências de leituras ausentes que duram pelo menos `minimo`."""
    saida = []
    inicio, n = None, 0
    for carimbo, cota in serie:
        if cota is None:
            inicio = inicio or carimbo
            n += 1
        else:
            if inicio is not None and n * PASSO >= minimo:
                saida.append((inicio, carimbo, n))
            inicio, n = None, 0
    return sorted(saida, key=lambda b: -b[2])


def picos(serie, limiar: float = ATENCAO_SALSEIRO_M * 0.8) -> list[tuple[datetime, float, int]]:
    """Maior leitura de cada evento acima de `limiar`, com quantas leituras o evento teve."""
    eventos, atual = [], []
    for carimbo, cota in serie:
        if cota is not None and cota >= limiar:
            if atual and carimbo - atual[-1][0] > SEPARACAO_DE_EVENTOS:
                eventos.append(atual)
                atual = []
            atual.append((carimbo, cota))
    if atual:
        eventos.append(atual)
    return [(*max(ev, key=lambda x: x[1]), len(ev)) for ev in eventos]


def picos_de_brusque_com_hora(eventos: list[dict]) -> list[tuple[datetime, float]]:
    saida = []
    for e in eventos:
        if e.get("cidade") == "brusque" and e.get("hora") and len(str(e.get("data", ""))) == 10:
            saida.append((datetime.fromisoformat(f"{e['data']}T{e['hora']}"), float(e["pico_m"])))
    return sorted(saida)


def parear(serie, brusque: list[tuple[datetime, float]]):
    """Para cada pico de Brusque com hora, o pico da Salseiro na janela anterior.

    Devolve dicionários; `recusa` explica quando não dá para medir. A
    cobertura da janela vai junto porque um pico da Salseiro dentro de um
    buraco de 64% de ausência é PISO, não pico.
    """
    saida = []
    for quando, pico_m in brusque:
        janela = [(t, c) for t, c in serie if quando - JANELA_DE_PAREAMENTO <= t <= quando]
        validas = [(t, c) for t, c in janela if c is not None]
        item = {"brusque_em": quando, "brusque_m": pico_m,
                "leituras": len(janela), "ausentes": len(janela) - len(validas)}
        if not janela:
            item["recusa"] = "a Salseiro não tem leitura nenhuma nessa janela"
        elif not validas:
            item["recusa"] = "a Salseiro só tem leituras ausentes (0,00) nessa janela"
        else:
            t, c = max(validas, key=lambda x: x[1])
            item.update(salseiro_em=t, salseiro_m=c,
                        horas=round((quando - t).total_seconds() / 3600, 2))
        saida.append(item)
    return saida


def relatorio(serie, brusque, limiar: float) -> None:
    validas = [c for _, c in serie if c is not None]
    print(f"série: {len(serie)} carimbos, {serie[0][0]:%d/%m/%Y %H:%M} → {serie[-1][0]:%d/%m/%Y %H:%M}")
    print(f"   com valor: {len(validas)} ({100 * len(validas) / len(serie):.0f}%)  "
          f"ausentes (0,00): {len(serie) - len(validas)}  "
          f"máx {max(validas):.2f} m  mín {min(validas):.2f} m")
    passos = Counter(b[0] - a[0] for a, b in zip(serie, serie[1:]))
    print("   passos mais comuns:", ", ".join(f"{int(p.total_seconds() // 60)} min ×{n}"
                                             for p, n in passos.most_common(3)))

    print(f"\nburacos de pelo menos 1 dia: {len(buracos(serie))}")
    for inicio, fim, n in buracos(serie)[:5]:
        print(f"   {inicio:%d/%m/%Y %H:%M} → {fim:%d/%m/%Y %H:%M}  ({n * 15 / 60 / 24:.1f} dias)")

    print(f"\npicos ≥ {limiar:.2f} m na SALSEIRO (atenção da própria régua: {ATENCAO_SALSEIRO_M:.2f} m):")
    for quando, cota, n in picos(serie, limiar):
        marca = " ← acima da atenção da Salseiro" if cota >= ATENCAO_SALSEIRO_M else ""
        print(f"   {quando:%d/%m/%Y %H:%M}  {cota:.2f} m  ({n} leituras no evento){marca}")

    print("\npareamento com os picos de Brusque que têm `hora` em enchentes.json:")
    if not brusque:
        print("   (nenhum registro de Brusque tem hora)")
    for p in parear(serie, brusque):
        cab = f"   Brusque {p['brusque_m']:.2f} m em {p['brusque_em']:%d/%m/%Y %H:%M}"
        if "recusa" in p:
            print(f"{cab}: SEM PAR — {p['recusa']}")
            continue
        aus = f"{100 * p['ausentes'] / p['leituras']:.0f}% da janela ausente"
        print(f"{cab}  ←  Salseiro {p['salseiro_m']:.2f} m em {p['salseiro_em']:%d/%m/%Y %H:%M}"
              f"  =  {p['horas']:.2f} h   ({aus})")
    print("\n⚠️ um evento não é tempo de trânsito: calibrar_transito.py exige "
          "3, e a Salseiro é relógio, não régua de Vidal Ramos.")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--bruto", type=Path, default=BRUTO)
    ap.add_argument("--limiar", type=float, default=ATENCAO_SALSEIRO_M * 0.8,
                    help="cota mínima para listar um pico (padrão 80%% da atenção)")
    args = ap.parse_args()
    if not args.bruto.exists():
        print(f"ERRO: {args.bruto} não existe", file=sys.stderr)
        return 1
    serie = serie_do_tar(args.bruto)
    brusque = picos_de_brusque_com_hora(le_json("enchentes.json")["eventos"])
    relatorio(serie, brusque, args.limiar)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
