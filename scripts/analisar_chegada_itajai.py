#!/usr/bin/env python3
"""Cruza Blumenau, as réguas de Itajaí, a maré e a chuva local na série guardada pelo coletor.

Uso:
    python3 scripts/analisar_chegada_itajai.py <pasta com os .ndjson de data/tempo-real>

Somente leitura: imprime um relatório e não escreve em data/. Os números são
DESCRITIVOS de 2026 (ago–out). Não calibram a faixa de chegada, que só muda com
cinco eventos conferidos e decisão do Jefferson (ver calibrar_chegada_itajai.py).
Método e resultado em docs/ANALISE-CHEGADA-ITAJAI-2026.md.

Três passos:
 1. a maré de cada régua: o componente rápido da régua (régua menos a média
    móvel de 25 h) é regredido no componente rápido da maré astronômica da tábua
    da Marinha, testando atrasos de 0 a 5 h. Cada régua sai com o seu atraso e o
    seu fator: "1 m de maré na tábua = X m nesta régua";
 2. a régua "sem maré": a régua menos fator × maré (com o atraso dela);
 3. os eventos de Blumenau e a crista "sem maré" em Itajaí em cada um, contada a
    partir do meio do platô de Blumenau.

Fuso: `medido_em` sem fuso é horário de Brasília (CLAUDE.md). A publicação
"Blumenau" lida na página da Defesa Civil de Itajaí carimbava 3 h ATRASADA
(saiu do ar em 19/09/2026); aqui ela só é usada onde falta o AlertaBlu, e
corrigida.
"""
from __future__ import annotations

import argparse
import json
import math
import statistics
import sys
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path

from comum import DADOS

ATRASOS_H = range(0, 6)
JANELA_MEDIA_H = 25  # um dia de maré (dois ciclos de 12,4 h): a média móvel tira a maré e deixa o rio
PROEMINENCIA_M = 1.0  # quanto Blumenau precisa subir para contar como evento
QUEDA_M = 0.10  # o pico só passou depois de descer isto, como no site
PLATO_M = 0.05  # o mesmo critério de web/src/logica/picoBlumenau.ts
ATRASO_PORTAL_BLUMENAU = timedelta(hours=3)
ILHOTA = "DCSC-00030"

Serie = list[float | None]


def hora(t: datetime) -> datetime:
    return t.replace(minute=0, second=0, microsecond=0)


def horas(inicio: datetime, fim: datetime) -> list[datetime]:
    out, t = [], hora(inicio)
    while t <= fim:
        out.append(t)
        t += timedelta(hours=1)
    return out


def curva_mare(extremos: list[tuple[datetime, float]]):
    """Altura da maré astronômica a qualquer hora, por cosseno entre preamar e baixa-mar."""
    ext = sorted(extremos)

    def altura(t: datetime) -> float | None:
        for (a, ha), (b, hb) in zip(ext, ext[1:]):
            if a <= t <= b:
                f = (t - a).total_seconds() / (b - a).total_seconds()
                return ha + (hb - ha) * (1 - math.cos(math.pi * f)) / 2
        return None

    return altura


def media_movel(x: Serie, n: int, cobertura: float = 0.75) -> Serie:
    h = n // 2
    out: Serie = []
    for i in range(len(x)):
        w = [v for v in x[max(0, i - h): i + h + 1] if v is not None]
        out.append(sum(w) / len(w) if len(w) >= cobertura * n else None)
    return out


def atrasar(x: Serie, lag: int) -> Serie:
    return ([None] * lag + x[: len(x) - lag]) if lag else list(x)


def ajuste_mare(regua: Serie, mare: Serie) -> dict | None:
    """O atraso e o fator da maré nesta régua, pela correlação dos componentes rápidos."""
    rapido_r = [None if a is None or b is None else a - b for a, b in zip(regua, media_movel(regua, JANELA_MEDIA_H))]
    rapido_m = [None if a is None or b is None else a - b for a, b in zip(mare, media_movel(mare, JANELA_MEDIA_H))]
    melhor = None
    for lag in ATRASOS_H:
        m = atrasar(rapido_m, lag)
        pares = [(a, b) for a, b in zip(rapido_r, m) if a is not None and b is not None]
        if len(pares) < 200:
            continue
        xs, ys = [b for _, b in pares], [a for a, _ in pares]
        if statistics.pstdev(xs) == 0 or statistics.pstdev(ys) == 0:
            continue
        r = statistics.correlation(xs, ys)
        fator = sum(x * y for x, y in zip(xs, ys)) / sum(x * x for x in xs)
        if melhor is None or r > melhor["r"]:
            melhor = {"r": r, "atraso_h": lag, "fator": fator, "horas": len(pares)}
    return melhor


def sem_mare(regua: Serie, mare: Serie, ajuste: dict) -> Serie:
    validos = [v for v in mare if v is not None]
    media = sum(validos) / len(validos)
    m = atrasar(mare, ajuste["atraso_h"])
    bruto = [None if a is None or b is None else a - ajuste["fator"] * (b - media) for a, b in zip(regua, m)]
    return media_movel(bruto, 5, cobertura=0.6)


def eventos(blu: Serie, eixo: list[datetime]) -> list[int]:
    """Índices dos picos de Blumenau: máximo em ±24 h, subida de pelo menos 1 m nas 48 h
    antes e descida de pelo menos 10 cm nas 24 h depois (um patamar não é pico)."""
    picos = []
    for i, v in enumerate(blu):
        if v is None:
            continue
        viz = [x for x in blu[max(0, i - 24): i + 25] if x is not None]
        antes = [x for x in blu[max(0, i - 48): i] if x is not None]
        depois = [x for x in blu[i + 1: i + 25] if x is not None]
        if (v >= max(viz) and antes and v - min(antes) >= PROEMINENCIA_M
                and depois and v - min(depois) >= QUEDA_M):
            if not picos or i - picos[-1] > 24:
                picos.append(i)
    return picos


def plato(blu: Serie, i: int) -> tuple[int, int]:
    teto = blu[i] - PLATO_M
    a = i
    while a > 0 and blu[a - 1] is not None and blu[a - 1] >= teto:
        a -= 1
    b = i
    while b < len(blu) - 1 and blu[b + 1] is not None and blu[b + 1] >= teto:
        b += 1
    return a, b


LACUNA_H = 2  # horas seguidas sem leitura bruta que deixam a crista indeterminada


def crista(serie: Serie, ini: int, fim: int, bruta: Serie | None = None) -> tuple[int, bool, bool] | None:
    """O máximo na janela: (índice, caiu na ponta final, há lacuna na janela).

    Com `bruta`, a crista só pode cair numa hora que TEM leitura bruta — a média
    móvel preenche buracos, e um máximo inventado dentro de um buraco não é
    crista (12/09/2026, DC-11: o "máximo das 07h" era uma hora sem leitura). E
    uma lacuna de `LACUNA_H` horas ou mais em qualquer ponto da janela deixa o
    horário indeterminado: a crista de verdade pode ter caído dentro dela.
    """
    janela = [(v, k) for k, v in enumerate(serie[ini: fim + 1])
              if v is not None and (bruta is None or bruta[ini + k] is not None)]
    if len(janela) < 0.75 * (fim - ini + 1):
        return None  # janela com buraco demais: o máximo dela pode não ser a crista
    _, k = max(janela)
    lacuna = False
    if bruta is not None:
        seguidas = 0
        for v in bruta[ini: fim + 1]:
            seguidas = seguidas + 1 if v is None else 0
            lacuna = lacuna or seguidas >= LACUNA_H
    return ini + k, k == fim - ini, lacuna


def ler(pasta: Path):
    niveis: dict[str, dict[datetime, list[float]]] = defaultdict(lambda: defaultdict(list))
    chuva: dict[datetime, list[float]] = defaultdict(list)
    for arq in sorted(pasta.glob("*.ndjson")):
        with arq.open(encoding="utf-8") as f:
            linhas = list(f)
        for linha in linhas:
            try:
                d = json.loads(linha)
                t = datetime.fromisoformat(d["medido_em"][:19])
            except (ValueError, KeyError, TypeError):
                continue
            if arq.name.startswith("chuva-"):
                h1 = (d.get("mm") or {}).get("h1")
                if d.get("cidade") == "itajai" and h1 is not None:
                    chuva[hora(t)].append(h1)
            elif arq.name.startswith("nivel-sc-"):
                if d.get("codigo") == ILHOTA and d.get("nivel_bruto_m") is not None:
                    niveis["ilhota"][hora(t)].append(d["nivel_bruto_m"])
            elif d.get("nivel_m") is not None:
                if d.get("estacao") == "Blumenau (AlertaBlu)":
                    niveis["blumenau"][hora(t)].append(d["nivel_m"])
                elif d.get("estacao") == "Blumenau":
                    niveis["blumenau-portal"][hora(t + ATRASO_PORTAL_BLUMENAU)].append(d["nivel_m"])
                elif d.get("cidade") == "itajai":
                    niveis[d["estacao"][:5]][hora(t)].append(d["nivel_m"])
    return niveis, chuva


def serie(dados: dict[datetime, list[float]], eixo: list[datetime]) -> Serie:
    return [statistics.median(dados[h]) if dados.get(h) else None for h in eixo]


def analisar(pasta: Path, mare_json: Path) -> dict:
    niveis, chuva = ler(pasta)
    todos = [t for d in niveis.values() for t in d]
    eixo = horas(min(todos), max(todos))
    m = json.loads(mare_json.read_text(encoding="utf-8"))
    ext = [(datetime.fromisoformat(e["quando"][:19]), e["altura_m"])
           for e in m["preamares"] + m["baixamares"] if e.get("altura_m") is not None]
    altura = curva_mare(ext)
    mare = [altura(h) for h in eixo]

    reguas = {}
    for nome in sorted(k for k in niveis if k.startswith("DC-") or k == "ilhota"):
        s = serie(niveis[nome], eixo)
        aj = ajuste_mare(s, mare)
        if aj:
            reguas[nome] = {**aj, "serie": s}

    blu = [a if a is not None else b for a, b in
           zip(serie(niveis["blumenau"], eixo), serie(niveis["blumenau-portal"], eixo))]
    chuva_h = [statistics.mean(chuva[h]) if chuva.get(h) else None for h in eixo]
    picos = eventos(blu, eixo)
    lista = []
    for n, i in enumerate(picos):
        a, b = plato(blu, i)
        meio = eixo[a] + (eixo[b] - eixo[a]) / 2
        # Até 36 h depois do pico, e nunca dentro da subida do evento seguinte.
        fim = min(len(eixo) - 1, i + 36, (picos[n + 1] - 6) if n + 1 < len(picos) else i + 36)
        ev = {"pico": eixo[i], "nivel_m": blu[i], "plato": (eixo[a], eixo[b]), "cristas": {}}
        antes = [v for v in chuva_h[max(0, i - 24): i + 1] if v is not None]
        ev["chuva_itajai_24h_mm"] = round(sum(antes), 1) if antes else None
        for nome in ("DC-11", "ilhota"):
            if nome not in reguas:
                continue
            serie_bruta = reguas[nome]["serie"]
            c = crista(sem_mare(serie_bruta, mare, reguas[nome]), max(0, a - 3), fim, serie_bruta)
            if c:
                k, borda, lacuna = c
                ev["cristas"][nome] = {"quando": eixo[k], "horas": (eixo[k] - meio).total_seconds() / 3600,
                                       "borda": borda, "lacuna": lacuna}
        lista.append(ev)
    return {"inicio": eixo[0], "fim": eixo[-1], "reguas": reguas, "eventos": lista}


def relatorio(r: dict) -> str:
    out = [f"Série de {r['inicio']:%d/%m %Hh} a {r['fim']:%d/%m/%Y %Hh} (horário de Brasília)", "",
           "Maré em cada régua (1 m na tábua = fator × 1 m na régua)",
           "| régua | correlação | atraso | fator | horas |", "|---|---|---|---|---|"]
    for nome, a in r["reguas"].items():
        out.append(f"| {nome} | {a['r']:.2f} | {a['atraso_h']} h | {a['fator']:.2f} | {a['horas']} |")
    out += ["", "Crista local sem maré astronômica, em horas depois do meio do platô de Blumenau",
            "(NÃO é o tempo de chegada da água de Blumenau: ver docs/ANALISE-CHEGADA-ITAJAI-2026.md)",
            "| pico Blumenau | nível | platô | chuva Itajaí 24 h | DC-11 | Ilhota |", "|---|---|---|---|---|---|"]
    for e in r["eventos"]:
        def c(n):
            x = e["cristas"].get(n)
            if not x:
                return "sem série"
            if x["borda"]:
                return "não achada (sobe até o fim)"
            if x["lacuna"]:
                return f"primeira crista detectada em {x['horas']:+.1f} h; horário indeterminado (lacuna)"
            return f"{x['horas']:+.1f} h"
        chuva = "—" if e["chuva_itajai_24h_mm"] is None else f"{e['chuva_itajai_24h_mm']:.0f} mm"
        out.append(f"| {e['pico']:%d/%m %Hh} | {e['nivel_m']:.2f} m | {e['plato'][0]:%Hh}–{e['plato'][1]:%Hh} "
                   f"| {chuva} | {c('DC-11')} | {c('ilhota')} |")
    return "\n".join(out)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("pasta", type=Path, help="pasta com os .ndjson de data/tempo-real")
    p.add_argument("--mare", type=Path, default=DADOS / "mare-itajai.json")
    a = p.parse_args(argv)
    if not a.pasta.is_dir():
        print(f"pasta não encontrada: {a.pasta}", file=sys.stderr)
        return 2
    print(relatorio(analisar(a.pasta, a.mare)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
