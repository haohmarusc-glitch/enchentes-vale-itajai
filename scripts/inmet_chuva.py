#!/usr/bin/env python3
"""
Chuva horária do INMET nas quatro estações da bacia: leitura, acumulados e conferência.

O QUE É A FONTE
---------------
Em 22/09/2026, no mesmo dia em que a LAI C8 foi respondida
(`docs/LAI-INMET-2026-09-22.md`), o Jefferson baixou do portal do INMET
(portal.inmet.gov.br/dadoshistoricos) a precipitação horária das quatro estações
automáticas que o INMET conta na bacia — A817 Indaial, A861 Rio do Campo,
A863 Ituporanga, A868 Itajaí — de 2006 a 08/2026, e entregou três arquivos:

* `data/brutos/inmet-chuva-horaria-2006-2026.csv.gz` — `codigo,ts_utc,prec_mm,suspeito`.
  Uma linha por estação e hora, carimbo em UTC. `prec_mm` vazio = sem dado.
  `suspeito` é marcação do Jefferson (o INMET não publica flag: dado suspeito
  é isolado antes de sair, e falha vem como 9999, Null ou branco).
* `data/brutos/inmet-chuva-diaria-2006-2026.csv` — `codigo,data_local,prec_mm,horas_validas`.
  Dia local = UTC−3 fixo. `prec_mm` é 0.0 mesmo quando `horas_validas` é 0:
  quem lê olha as horas, não o zero.
* `data/brutos/inmet-chuva-eventos-atlas-2026-09-22.json` — acumulados
  (24 h, 72 h, 7 d, 30 d, máximo horário em 7 d) por evento do Atlas de
  Desastres (chave rio-ano-mês), ancorados na data com mais registros do mês.

Este script NÃO baixa nada: os domínios do INMET não respondem deste ambiente e
a API exige Acordo de Cooperação Técnica. Ele lê o que está em `data/brutos/`
e serve para (1) reproduzir os acumulados do JSON a partir da horária, (2)
reproduzir a diária, (3) calcular um acumulado qualquer para uma janela que
termina numa hora local.

CONVENÇÕES QUE O CÓDIGO ASSUME (e que os testes travam)
-------------------------------------------------------
* Hora local = UTC − 3 h, FIXO. Santa Catarina teve horário de verão até 2019;
  os arquivos e o JSON ignoram isso, e este script também, para reproduzi-los.
  Nos meses de out–fev anteriores a 2019, "00h local" está 1 h deslocado.
* O carimbo `ts_utc` é a hora a que a leitura pertence; a diária do Jefferson
  se reproduz somando as horas cujo `ts_utc − 3 h` cai no dia.
* Acumulado ignora horas sem dado e devolve a COBERTURA (fração de horas com
  dado). Cobertura zero → acumulado None, como no JSON. Cobertura < 1
  subestima; quem cita um acumulado cita a cobertura junto.
* `suspeito`: a coluna marca, na horária, as horas que a diária e o JSON
  descartam — TODAS são zeros, e são exatamente os zeros que fazem parte de
  uma sequência de zeros que se estende por ≥ 20 dias (horas sem dado no meio
  não quebram a sequência): o retrato de pluviômetro entupido ou parado, que o
  INMET publica como 0,0. `ler_horaria` honra a marca por padrão
  (`honrar_suspeito=True`) e é assim que reproduz os outros dois arquivos;
  `zeros_travados()` recalcula a marca a partir dos valores, e o teste exige
  que as duas coincidam.
* Chuva é contexto. Nunca cota, nunca aviso. Nada daqui escreve em
  `enchentes.json`, `estacoes.json` ou `transito.json`.
"""
from __future__ import annotations

import argparse
import csv
import gzip
import json
import sys
from collections import defaultdict
from datetime import date, datetime, timedelta
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
BRUTOS = RAIZ / "data" / "brutos"
HORARIA = BRUTOS / "inmet-chuva-horaria-2006-2026.csv.gz"
DIARIA = BRUTOS / "inmet-chuva-diaria-2006-2026.csv"
EVENTOS = BRUTOS / "inmet-chuva-eventos-atlas-2026-09-22.json"

FUSO = timedelta(hours=-3)  # Brasília, sem horário de verão — ver docstring
SEM_DADO = {"", "null", "none", "nan", "9999", "-9999", "9999.0", "-9999.0"}
JANELAS_H = {"24h": 24, "72h": 72, "7d": 168, "30d": 720}

# As quatro estações que o INMET conta na bacia (LAI C8, resposta de 22/09/2026).
ESTACOES = {
    "A817": {"nome": "Indaial", "lat": -26.9136, "lon": -49.2681, "alt_m": 72.2,
             "inicio": "2006-07-02", "situacao_2026_09": "Pane"},
    "A861": {"nome": "Rio do Campo", "lat": -26.9375, "lon": -50.1456, "alt_m": 591.7,
             "inicio": "2008-03-10", "situacao_2026_09": "Operante"},
    "A863": {"nome": "Ituporanga", "lat": -27.4183, "lon": -49.6469, "alt_m": 479.8,
             "inicio": "2008-03-04", "situacao_2026_09": "Operante"},
    "A868": {"nome": "Itajaí", "lat": -26.9508, "lon": -48.7619, "alt_m": 9.8,
             "inicio": "2010-06-24", "situacao_2026_09": "Operante"},
}

Serie = dict[datetime, float | None]


def numero(texto: str | None) -> float | None:
    """Converte a célula do INMET; 9999/Null/branco viram None, nunca 9 999 mm."""
    if texto is None:
        return None
    t = texto.strip().replace(",", ".")
    if t.lower() in SEM_DADO:
        return None
    valor = float(t)
    if valor < 0:
        raise ValueError(f"chuva negativa: {texto!r}")
    return valor


def _abre(caminho: Path):
    if str(caminho).endswith(".gz"):
        return gzip.open(caminho, "rt", encoding="utf-8", newline="")
    return open(caminho, encoding="utf-8", newline="")


def ler_horaria(caminho: Path = HORARIA, honrar_suspeito: bool = True) -> dict[str, Serie]:
    """`{codigo: {ts_utc: mm | None}}`. Carimbo `AAAA-MM-DDTHH:MMZ`.

    Com `honrar_suspeito`, hora marcada `suspeito != 0` vira None (ver docstring
    do módulo). Sem, a horária vem como o INMET a publicou.
    """
    series: dict[str, Serie] = defaultdict(dict)
    with _abre(caminho) as f:
        for linha in csv.DictReader(f):
            ts = datetime.strptime(linha["ts_utc"], "%Y-%m-%dT%H:%MZ")
            valor = numero(linha["prec_mm"])
            if honrar_suspeito and linha.get("suspeito", "0").strip() not in ("", "0"):
                valor = None
            series[linha["codigo"]][ts] = valor
    return dict(series)


def ler_suspeitos(caminho: Path = HORARIA) -> dict[str, set[datetime]]:
    """As horas marcadas `suspeito != 0`, por estação."""
    marcas: dict[str, set[datetime]] = defaultdict(set)
    with _abre(caminho) as f:
        for linha in csv.DictReader(f):
            if linha.get("suspeito", "0").strip() not in ("", "0"):
                marcas[linha["codigo"]].add(datetime.strptime(linha["ts_utc"], "%Y-%m-%dT%H:%MZ"))
    return dict(marcas)


def zeros_travados(serie: Serie, dias: int = 20) -> set[datetime]:
    """Horas com 0,0 numa sequência de zeros que se estende por ≥ `dias` (primeiro ao último zero).

    Um valor > 0 encerra a sequência; hora sem dado (None ou ausente) não
    encerra. É a regra que reproduz a coluna `suspeito` do bruto.
    """
    minimo = timedelta(days=dias) - timedelta(hours=1)
    marcadas: set[datetime] = set()
    corrida: list[datetime] = []

    def fecha():
        if corrida and corrida[-1] - corrida[0] >= minimo:
            marcadas.update(corrida)
        corrida.clear()

    for ts in sorted(serie):
        v = serie[ts]
        if v is None:
            continue
        if v == 0.0:
            corrida.append(ts)
        else:
            fecha()
    fecha()
    return marcadas


def acumulado(serie: Serie, fim_local: datetime, horas: int) -> tuple[float | None, float]:
    """Soma das `horas` que terminam em `fim_local` (exclusivo), e a cobertura.

    `fim_local` é hora de Brasília sem fuso; a janela é [fim − horas, fim).
    Horas ausentes da série contam como sem dado. Cobertura 0 → (None, 0.0).
    """
    fim_utc = fim_local - FUSO
    inicio_utc = fim_utc - timedelta(hours=horas)
    soma = 0.0
    validas = 0
    t = inicio_utc
    while t < fim_utc:
        v = serie.get(t)
        if v is not None:
            soma += v
            validas += 1
        t += timedelta(hours=1)
    if validas == 0:
        return None, 0.0
    return round(soma, 1), round(validas / horas, 2)


def diaria(serie: Serie) -> dict[date, tuple[float, int]]:
    """`{dia_local: (mm, horas_validas)}` com o dia em UTC−3 fixo, como a diária do Jefferson."""
    dias: dict[date, list] = defaultdict(lambda: [0.0, 0])
    for ts, v in serie.items():
        d = (ts + FUSO).date()
        if v is not None:
            dias[d][0] += v
            dias[d][1] += 1
        else:
            dias[d]  # noqa: B018 — garante o dia mesmo sem hora válida
    return {d: (round(mm, 1), n) for d, (mm, n) in sorted(dias.items())}


def conferir_diaria(series: dict[str, Serie], caminho: Path = DIARIA) -> dict:
    """Reproduz a diária a partir da horária. Devolve contagens e as diferenças."""
    calc = {cod: diaria(s) for cod, s in series.items()}
    iguais = 0
    diferentes: list[tuple] = []
    with open(caminho, encoding="utf-8", newline="") as f:
        for linha in csv.DictReader(f):
            cod = linha["codigo"]
            d = date.fromisoformat(linha["data_local"])
            mm, n = calc.get(cod, {}).get(d, (0.0, 0))
            if abs(mm - float(linha["prec_mm"])) < 0.05 and n == int(linha["horas_validas"]):
                iguais += 1
            else:
                diferentes.append((cod, linha["data_local"], linha["prec_mm"], linha["horas_validas"], mm, n))
    return {"iguais": iguais, "diferentes": len(diferentes), "exemplos": diferentes[:10]}


def conferir_eventos(series: dict[str, Serie], caminho: Path = EVENTOS) -> dict:
    """Reproduz `estacoes[cod][janela].mm` de cada evento do JSON a partir da horária."""
    dados = json.loads(Path(caminho).read_text(encoding="utf-8"))
    iguais = nulos = 0
    diferentes: list[tuple] = []
    for chave, evento in dados["eventos"].items():
        if not evento["estacoes"]:
            continue
        fim = datetime.fromisoformat(evento["janela_termina"]).replace(tzinfo=None)
        for cod, janelas in evento["estacoes"].items():
            for nome, horas in JANELAS_H.items():
                esperado = janelas[nome]["mm"]
                cob_esperada = janelas[nome].get("cobertura")
                mm, cob = acumulado(series.get(cod, {}), fim, horas)
                cob_bate = cob_esperada is None or abs(cob - cob_esperada) < 0.011
                if esperado is None:
                    nulos += 1
                    if mm is not None:
                        diferentes.append((chave, cod, nome, esperado, mm, cob_esperada, cob))
                elif mm is not None and abs(mm - esperado) < 0.15 and cob_bate:
                    iguais += 1
                else:
                    diferentes.append((chave, cod, nome, esperado, mm, cob_esperada, cob))
    return {"iguais": iguais, "nulos": nulos, "diferentes": len(diferentes), "exemplos": diferentes[:10]}


def ultimo_valido(serie: Serie) -> datetime | None:
    validos = [t for t, v in serie.items() if v is not None]
    return max(validos) if validos else None


def cobertura_por_ano(serie: Serie) -> dict[int, float]:
    tot: dict[int, list] = defaultdict(lambda: [0, 0])
    for t, v in serie.items():
        tot[t.year][1] += 1
        if v is not None:
            tot[t.year][0] += 1
    return {ano: round(n / total, 2) for ano, (n, total) in sorted(tot.items())}


def _cli(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    p.add_argument("--conferir", action="store_true", help="reproduz a diária e o JSON de eventos")
    p.add_argument("--estado", action="store_true", help="último dado válido e cobertura por ano")
    p.add_argument("--acumulado", nargs=2, metavar=("CODIGO", "FIM_LOCAL"),
                   help="ex.: A817 2008-11-25T00:00 — janela termina nessa hora de Brasília")
    p.add_argument("--horas", type=int, nargs="+", default=[24, 72, 96, 168, 720])
    a = p.parse_args(argv)
    if not (a.conferir or a.estado or a.acumulado):
        p.print_help()
        return 2
    series = ler_horaria()
    if a.conferir:
        r = conferir_diaria(series)
        print(f"diária: {r['iguais']} iguais, {r['diferentes']} diferentes")
        for ex in r["exemplos"]:
            print("   ", ex)
        r = conferir_eventos(series)
        print(f"eventos: {r['iguais']} iguais, {r['nulos']} nulos no JSON, {r['diferentes']} diferentes")
        for ex in r["exemplos"]:
            print("   ", ex)
    if a.estado:
        for cod, s in sorted(series.items()):
            print(f"{cod} {ESTACOES.get(cod, {}).get('nome', '?')}: último válido {ultimo_valido(s)}Z")
            print("    cobertura/ano:", cobertura_por_ano(s))
    if a.acumulado:
        cod, fim = a.acumulado
        s = series.get(cod)
        if s is None:
            print(f"estação {cod} não está na horária", file=sys.stderr)
            return 1
        fim_local = datetime.fromisoformat(fim)
        for h in a.horas:
            mm, cob = acumulado(s, fim_local, h)
            print(f"{cod} {h:>4} h até {fim_local:%Y-%m-%d %H:%M} local: "
                  f"{'—' if mm is None else f'{mm:.1f} mm'} (cobertura {cob:.2f})")
    return 0


if __name__ == "__main__":
    sys.exit(_cli())
