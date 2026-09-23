#!/usr/bin/env python3
"""
Velocidade de subida de uma cheia, em cm/h, a partir de uma série extraída da coleta.

ENTRADA: um `.ndjson` como `data/brutos/cheia-2026-09-11-12.ndjson` — uma leitura por
linha, com `estacao`, `rio`, `cidade`, `medido_em` (horário de Brasília, sem fuso,
como toda leitura do projeto) e `nivel_m`. A série de resgate (`resgate_de`) é
tratada como estação própria, porque tem carimbo e cadência próprios.

O QUE CALCULA, por estação
- base: a menor leitura antes do meio-dia do primeiro dia da janela (o rio antes
  da chuva);
- crista: a maior leitura e o horário dela;
- subida total: crista − base, em cm;
- maior subida em 1 h e em 3 h: para cada leitura, o nível exatamente N horas
  depois é obtido por INTERPOLAÇÃO LINEAR entre as duas leituras vizinhas; sem
  interpolar por cima de buracos maiores que `BURACO_MAX` (3 h). É a taxa que
  alguém lendo a régua de hora em hora teria visto;
- saltos suspeitos: uma leitura que muda ≥ 60 cm em ≤ 20 min. Rio não faz isso;
  régua com ruído, sim. Ficam listados, não apagados.

O QUE NÃO FAZ
- Não distingue cheia de maré. Nas réguas de estuário de Itajaí (DC-01 a DC-09) a
  subida mistura as duas coisas, e o número sai com essa etiqueta na documentação —
  nunca como velocidade de cheia.
- Não compara estações em metros: cada uma tem a própria régua. Compara em cm/h,
  que é diferença na mesma régua, e mesmo assim só como descrição do evento.
- Não escreve em `enchentes.json` nem em `transito.json`.

Uso: python3 scripts/subida_cheia.py [caminho.ndjson] [--json]
"""
from __future__ import annotations

import argparse
import bisect
import json
import sys
from collections import defaultdict
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
PADRAO = RAIZ / "data" / "brutos" / "cheia-2026-09-11-12.ndjson"
BURACO_MAX = timedelta(hours=3)
SALTO_CM = 60.0
SALTO_MIN = 20

Ponto = tuple[datetime, float]


@dataclass
class Subida:
    estacao: str
    rio: str
    cidade: str
    leituras: int
    base_m: float
    crista_m: float
    crista_em: str
    subida_cm: float
    max_1h_cm_h: float | None
    max_1h_em: str | None
    max_3h_cm_h: float | None
    max_3h_em: str | None
    saltos: list[tuple[str, float, float]]


def ler_ndjson(caminho: Path) -> dict[tuple[str, str, str], list[Ponto]]:
    """`{(estacao, rio, cidade): [(quando, nivel_m), …]}`, ordenado e sem duplicatas."""
    series: dict[tuple[str, str, str], set[Ponto]] = defaultdict(set)
    with open(caminho, encoding="utf-8") as f:
        for linha in f:
            linha = linha.strip()
            if not linha:
                continue
            r = json.loads(linha)
            v = r.get("nivel_m")
            if v is None:
                continue
            chave = (r["estacao"], r.get("rio", ""), r.get("cidade", ""))
            series[chave].add((datetime.fromisoformat(r["medido_em"]), float(v)))
    return {k: sorted(v) for k, v in series.items()}


def interpolar(serie: list[Ponto], quando: datetime) -> float | None:
    """Nível em `quando`, entre as duas leituras vizinhas. None fora da série ou sobre buraco > BURACO_MAX."""
    tempos = [p[0] for p in serie]
    i = bisect.bisect_left(tempos, quando)
    if i < len(serie) and serie[i][0] == quando:
        return serie[i][1]
    if i == 0 or i >= len(serie):
        return None
    (t0, v0), (t1, v1) = serie[i - 1], serie[i]
    if t1 - t0 > BURACO_MAX:
        return None
    f = (quando - t0).total_seconds() / (t1 - t0).total_seconds()
    return v0 + f * (v1 - v0)


def maior_subida(serie: list[Ponto], horas: float) -> tuple[float, datetime] | None:
    """Maior (nível em t+horas − nível em t) / horas, em cm/h, e o t em que começa."""
    melhor: tuple[float, datetime] | None = None
    for t0, v0 in serie:
        v1 = interpolar(serie, t0 + timedelta(hours=horas))
        if v1 is None:
            continue
        taxa = (v1 - v0) * 100 / horas
        if melhor is None or taxa > melhor[0]:
            melhor = (round(taxa, 1), t0)
    return melhor


def saltos_suspeitos(serie: list[Ponto], limite_cm: float = SALTO_CM, ate_min: int = SALTO_MIN) -> list[tuple[str, float, float]]:
    out = []
    for (t0, v0), (t1, v1) in zip(serie, serie[1:]):
        minutos = (t1 - t0).total_seconds() / 60
        if 0 < minutos <= ate_min and abs(v1 - v0) * 100 >= limite_cm:
            out.append((t0.strftime("%d/%m %H:%M"), v0, v1))
    return out


def analisar(chave: tuple[str, str, str], serie: list[Ponto]) -> Subida | None:
    if len(serie) < 3:
        return None
    primeiro_dia = serie[0][0].replace(hour=12, minute=0, second=0, microsecond=0)
    antes = [v for t, v in serie if t < primeiro_dia] or [serie[0][1]]
    base = min(antes)
    crista_em, crista = max(serie, key=lambda p: p[1])
    m1 = maior_subida(serie, 1)
    m3 = maior_subida(serie, 3)
    return Subida(
        estacao=chave[0], rio=chave[1], cidade=chave[2], leituras=len(serie),
        base_m=base, crista_m=crista, crista_em=crista_em.strftime("%d/%m %H:%M"),
        subida_cm=round((crista - base) * 100),
        max_1h_cm_h=m1[0] if m1 else None, max_1h_em=m1[1].strftime("%d/%m %H:%M") if m1 else None,
        max_3h_cm_h=m3[0] if m3 else None, max_3h_em=m3[1].strftime("%d/%m %H:%M") if m3 else None,
        saltos=saltos_suspeitos(serie),
    )


def relatorio(caminho: Path = PADRAO) -> list[Subida]:
    series = ler_ndjson(caminho)
    saida = [s for chave in sorted(series) if (s := analisar(chave, series[chave])) is not None]
    return sorted(saida, key=lambda s: (s.rio, s.cidade, s.estacao))


def _cli(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    p.add_argument("caminho", nargs="?", type=Path, default=PADRAO)
    p.add_argument("--json", action="store_true")
    a = p.parse_args(argv)
    res = relatorio(a.caminho)
    if a.json:
        print(json.dumps([asdict(s) for s in res], ensure_ascii=False, indent=1))
        return 0
    print(f"{'estação':<56} {'n':>4} {'base':>6} {'crista':>7} {'quando':<12} {'subida':>7} {'1 h':>6} {'às':<12} {'3 h':>6}  saltos")
    for s in res:
        print(f"{s.estacao[:56]:<56} {s.leituras:>4} {s.base_m:>6.2f} {s.crista_m:>7.2f} {s.crista_em:<12} "
              f"{s.subida_cm:>5.0f}cm {s.max_1h_cm_h if s.max_1h_cm_h is not None else float('nan'):>6.1f} "
              f"{s.max_1h_em or '—':<12} {s.max_3h_cm_h if s.max_3h_cm_h is not None else float('nan'):>6.1f}  {s.saltos or ''}")
    return 0


if __name__ == "__main__":
    sys.exit(_cli())
