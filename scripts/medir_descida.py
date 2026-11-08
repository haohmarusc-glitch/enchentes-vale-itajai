#!/usr/bin/env python3
"""Mede quanto tempo a cheia leva para DESCER o rio, a partir das séries medidas (07/11/2026).

POR QUE EXISTE. O tempo de descida que o site mostra vem da Tabela 7.5.1 da JICA (2011): hidrogramas
CALCULADOS para cheias de projeto de 5 a 50 anos (`transito.json`, `docs/JICA-2011-VERIFICADO.md`). O
`calibrar_transito_telemetria.py` mede pela rede estadual, mas só onde as DUAS pontas são estações
DCSC — e Blumenau, Gaspar e Itajaí não são. Este script junta as três fontes que o projeto já guarda e
mede cada trecho com cinco métodos independentes, com a incerteza escrita ao lado.

O QUE ELE NÃO FAZ. Nunca grava em `transito.json`: trocar o tempo que o morador lê é decisão do
Jefferson. Não usa o NÍVEL para nada além do horário — cada régua tem seu zero, e aqui só a forma da
onda e o relógio entram na conta. Não prevê o pico: com `--agora`, projeta a janela a partir da cheia
de cima que já passou (ou avisa que ainda não passou).

AS FONTES (todas em hora de Brasília, sem fuso — o contrato do projeto):
  * rede estadual consolidada (`consolidar_historico_dcsc.py` → `<pasta>/DCSC-000NN.csv`, 10 em 10 min);
  * série do coletor (`data/tempo-real/AAAA-MM.ndjson`, cópia no branch `arquivo-series`);
  * a publicação mais recente (`serie-recente.json` do branch `tempo-real`, últimas 48 h).
Cada PONTO diz de qual fonte vem e por quê (ver `PONTOS`). Blumenau: o PADKND (5 min) manda; as lacunas
são preenchidas pelo AlertaBlu deslocado pela diferença mediana entre os dois (~6 cm, sistemática) — o
deslocamento não muda horário, só evita o serrilhado. O repasse antigo "Blumenau", 3 h atrasado
(CLAUDE.md, fuso), fica de fora.

OS MÉTODOS (todos sobre a série regularizada de 10 em 10 min):
  1. `crista`     — meio do platô do pico (a 3 cm do máximo), de cá e de lá;
  2. `meia_subida`— a hora em que a subida passa pela metade da amplitude do evento;
  3. `centroide`  — centro de massa da metade de cima do hidrograma (robusto a pico achatado);
  4. `xcorr`      — correlação cruzada da VARIAÇÃO (não do nível: zeros diferentes), com refino
                    parabólico abaixo dos 10 min;
  5. `dtw`        — Dynamic Time Warping das duas curvas normalizadas (banda de Sakoe–Chiba): alinha a
                    FORMA e devolve a mediana dos deslocamentos na metade de cima da subida e da crista.
A maré sai antes, nas réguas de estuário, por ANÁLISE HARMÔNICA (como o t_tide/UTide): o filtro de Godin
(médias de 24, 24 e 25 h) separa a parte lenta; no resto, mínimos quadrados ajustam dez constituintes (M2,
S2, N2, K2, K1, O1, P1, Q1, M4, MS4), e a maré ajustada sai da série original. A cheia fica com a forma
dela — o Godin sozinho achataria a crista e a empurraria para o lado da descida, que é mais lenta. Só
entram os trechos calmos (fora das cheias) e só as constituintes que a duração separa (critério de Rayleigh).

A FAIXA. Por trecho e método: mediana, p25–p75 dos eventos e um intervalo de confiança de 90 % para a
mediana por bootstrap (reamostra EVENTOS, semente fixa: o resultado é reprodutível). A relação com o
tamanho da cheia sai pela inclinação de Theil–Sen (atraso × amplitude de montante), só com ≥ 5 eventos.

A CONFIANÇA, pela mesma régua do `calibrar_transito_telemetria.py`:
  * `alta`  — ≥ 5 eventos pareados, p25–p75 dos picos em até 3 h e os métodos a ≤ 2 h um do outro;
  * `media` — ≥ 3 eventos, p25–p75 em até 6 h e os métodos a ≤ 4 h;
  * fora disso, `insuficiente`, com o motivo. Um trânsito inventado é pior que um trânsito ausente.

Uso:
    python3 scripts/medir_descida.py --dcsc <pasta dos CSV> --serie <pasta dos ndjson> \\
        [--recente serie-recente.json] [--agora] [--gravar]
"""
from __future__ import annotations

import argparse
import csv
import gzip
import json
import math
import random
import statistics
import sys
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from comum import DADOS, RAIZ, nivel_plausivel  # noqa: E402

PASSO = timedelta(minutes=10)
#: Lacuna maior que isto não é interpolada: vira buraco. 70 min deixa passar o AlertaBlu, que é de hora
#: em hora (com 40 min, Blumenau tinha um buraco a cada hora e só o pico a pico media).
LACUNA_MAX = timedelta(minutes=70)
#: Salto de 10 min acima disto, nos dois lados, é pico de sensor (o consolidador usa a mesma ideia).
SALTO_ISOLADO_M = 1.0
#: 18 h sem cheia separam episódios (regra do extrair_picos.py / eventos_captados.py).
SEPARACAO_EVENTOS = timedelta(hours=18)
#: Janela para trás onde a base do pico é procurada (uma cheia do Itajaí leva 2–3 dias para encher).
LOOKBACK = timedelta(hours=72)
#: Busca da crista de jusante, a partir da crista de montante. O começo negativo é proposital: o baixo
#: vale às vezes cresta ANTES (chuva local), e esconder isso seria escolher a resposta.
JANELA_JUSANTE = (timedelta(hours=-12), timedelta(hours=36))
#: Janela dos métodos de forma (xcorr, dtw) em volta da crista de montante.
JANELA_FORMA = (timedelta(hours=-36), timedelta(hours=24))
LAG_MAX = timedelta(hours=36)
BANDA_DTW = timedelta(hours=36)
PLATO_M = 0.03
#: Queda mínima depois do máximo para dizer que a cheia passou.
QUEDA_MIN_M = 0.10
QUEDA_FRAC = 0.10
BOOTSTRAP_N = 2000
SEMENTE = 20261107

METODOS = ("crista", "meia_subida", "centroide", "xcorr", "dtw")


# --------------------------------------------------------------------------- pontos e trechos

@dataclass(frozen=True)
class Ponto:
    id: str
    nome: str
    #: ("dcsc", "DCSC-00013") ou ("coletor", ["título 1", "título 2", ...]) em ordem de preferência.
    fonte: tuple
    #: Prominência mínima de uma cheia nesta régua, em metros.
    prominencia_m: float = 0.5
    mare: bool = False
    nota: str = ""


PONTOS: dict[str, Ponto] = {p.id: p for p in (
    Ponto("taio", "Taió (DCSC-00041)", ("dcsc", "DCSC-00041")),
    Ponto("ituporanga", "Ituporanga (DCSC-00039)", ("dcsc", "DCSC-00039"),
          nota="a jusante da Barragem Sul: água amortecida"),
    Ponto("rio-do-sul", "Rio do Sul (DCSC-00013)", ("dcsc", "DCSC-00013"),
          nota="estação estadual: série contínua; a Asthon da Ponte Dom Tito Buss ficou parada de 04 a 07/11"),
    Ponto("ascurra", "Ascurra (DCSC-00003)", ("dcsc", "DCSC-00003")),
    Ponto("blumenau", "Blumenau (PADKND + AlertaBlu)",
          ("coletor", ["Blumenau (PADKND)", "Blumenau (AlertaBlu)"]),
          nota="o repasse antigo 'Blumenau', 3 h atrasado, fica de fora"),
    Ponto("ilhota", "Ilhota (DCSC-00030)", ("dcsc", "DCSC-00030"), prominencia_m=0.3, mare=True,
          nota="estação estadual; zero próprio; a maré chega a Ilhota em ~1 h (docs/ANALISE-CHEGADA-ITAJAI-2026.md)"),
    Ponto("itajai-dc11", "Itajaí DC-11 Volta de Cima",
          ("coletor", ["DC-11 Rio Itajaí-Açú – Santa Regina (Volta de Cima)"]),
          prominencia_m=0.2, mare=True, nota="estuário: maré tirada pelo filtro de Godin"),
    Ponto("itajai-dc02", "Itajaí DC-02 Praça Celso Pereira",
          ("coletor", ["DC-02 Rio Itajaí-Açu - Praça Celso Pereira da Silva"]),
          prominencia_m=0.15, mare=True, nota="estuário: maré tirada pelo filtro de Godin"),
    Ponto("vidal-ramos", "Vidal Ramos (DCSC-00024)", ("dcsc", "DCSC-00024")),
    Ponto("botuvera", "Botuverá (DCSC-00018)", ("dcsc", "DCSC-00018")),
    Ponto("brusque", "Brusque (DCSC-00019)", ("dcsc", "DCSC-00019")),
    Ponto("itajai-dc10", "Itajaí DC-10 Limoeiro",
          ("coletor", ["DC-10 Rio Itajaí-Mirim – Bairro Limoeiro"]),
          nota="acima da maré (CLAUDE.md, DC-10)"),
)}

#: Coluna da Tabela 7.5.1 da JICA, horas depois de Rio do Sul, para 5 / 10 / 25 / 50 anos.
#: Só os pontos que a tabela traz; a diferença entre dois deles vale dentro de uma coluna.
JICA_APOS_RIO_DO_SUL = {
    "taio": (-6, None, None, None), "ituporanga": (1, None, None, None), "rio-do-sul": (0, 0, 0, 0),
    "blumenau": (10, 9, 7, 7), "ilhota": (17, 15, 14, 12), "itajai": (27, 24, 21, 19),
}


def referencia_jica(de: str, para: str) -> tuple[float, float] | None:
    """Faixa da JICA para o trecho, coluna a coluna; None quando a tabela não traz as duas pontas."""
    chave = lambda p: "itajai" if p.startswith("itajai-") and p in ("itajai-dc11", "itajai-dc02") else p  # noqa: E731
    a, b = JICA_APOS_RIO_DO_SUL.get(chave(de)), JICA_APOS_RIO_DO_SUL.get(chave(para))
    if not a or not b:
        return None
    difs = [y - x for x, y in zip(a, b) if x is not None and y is not None]
    return (min(difs), max(difs)) if difs else None


@dataclass(frozen=True)
class Trecho:
    de: str
    para: str
    rio: str


TRECHOS: tuple[Trecho, ...] = (
    Trecho("taio", "rio-do-sul", "itajai-acu"),
    Trecho("ituporanga", "rio-do-sul", "itajai-acu"),
    Trecho("rio-do-sul", "ascurra", "itajai-acu"),
    Trecho("ascurra", "blumenau", "itajai-acu"),
    Trecho("rio-do-sul", "blumenau", "itajai-acu"),
    Trecho("blumenau", "ilhota", "itajai-acu"),
    Trecho("ilhota", "itajai-dc11", "itajai-acu"),
    Trecho("blumenau", "itajai-dc11", "itajai-acu"),
    Trecho("blumenau", "itajai-dc02", "itajai-acu"),
    Trecho("vidal-ramos", "botuvera", "itajai-mirim"),
    Trecho("botuvera", "brusque", "itajai-mirim"),
    Trecho("brusque", "itajai-dc10", "itajai-mirim"),
)


# --------------------------------------------------------------------------- séries

Serie = list[tuple[datetime, float]]


def _quando(texto: str) -> datetime | None:
    try:
        d = datetime.fromisoformat(str(texto).replace("Z", "+00:00"))
    except ValueError:
        return None
    # carimbo com fuso não é o contrato (medido_em é Brasília sem fuso): fica de fora
    return d.replace(microsecond=0) if d.tzinfo is None else None


def ler_dcsc(pasta: Path, codigo: str) -> Serie:
    arquivo = pasta / f"{codigo}.csv"
    if not arquivo.exists():
        return []
    out: Serie = []
    with arquivo.open(encoding="utf-8") as f:
        for linha in csv.DictReader(f):
            q, v = _quando(linha.get("medido_em", "")), linha.get("rio_nivel")
            if q is None or v in (None, ""):
                continue
            try:
                n = float(v)
            except ValueError:
                continue
            if nivel_plausivel(n):
                out.append((q, n))
    return sorted(out)


def ler_coletor(arquivos: list[Path]) -> dict[str, Serie]:
    """Linhas do ndjson do coletor, por TÍTULO da publicação (não por cidade: Itajaí tem onze réguas)."""
    por_titulo: dict[str, dict[datetime, float]] = {}
    for arquivo in arquivos:
        abrir = gzip.open if arquivo.suffix == ".gz" else open
        with abrir(arquivo, "rt", encoding="utf-8") as f:
            for linha in f:
                try:
                    d = json.loads(linha)
                    n = float(d["nivel_m"])
                except (ValueError, KeyError, TypeError):
                    continue
                q = _quando(d.get("medido_em", ""))
                if q is None or not nivel_plausivel(n) or not d.get("estacao"):
                    continue
                por_titulo.setdefault(d["estacao"], {})[q] = n
    return {t: sorted(s.items()) for t, s in por_titulo.items()}


def ler_recente(arquivo: Path) -> dict[str, Serie]:
    """`serie-recente.json`: o `r` de cada ponto aponta o título em `reguas[rio][cidade]`."""
    d = json.loads(arquivo.read_text(encoding="utf-8"))
    out: dict[str, dict[datetime, float]] = {}
    for rio, cidades in d.get("series", {}).items():
        for cidade, pontos in cidades.items():
            titulos = d.get("reguas", {}).get(rio, {}).get(cidade, [])
            for p in pontos:
                r = p.get("r")
                if not isinstance(r, int) or not 0 <= r < len(titulos):
                    continue  # sem `r` não se sabe a régua: não comparável (contrato do arquivo)
                q = _quando(p.get("medido_em", ""))
                n = p.get("nivel_m")
                if q is None or not isinstance(n, (int, float)) or not nivel_plausivel(n):
                    continue
                out.setdefault(titulos[r], {})[q] = float(n)
    return {t: sorted(s.items()) for t, s in out.items()}


def juntar_fontes(series: list[Serie]) -> Serie:
    """A primeira manda; as outras preenchem lacunas, deslocadas pela diferença mediana na sobreposição."""
    if not series:
        return []
    base = dict(series[0])
    for outra in series[1:]:
        if not outra:
            continue
        horas_base = {_hora(q): v for q, v in base.items() if q.minute == 0}
        difs = [horas_base[_hora(q)] - v for q, v in outra if q.minute == 0 and _hora(q) in horas_base]
        deslocamento = statistics.median(difs) if len(difs) >= 6 else 0.0
        ocupados = sorted(base)
        for q, v in outra:
            if not _perto(ocupados, q, LACUNA_MAX / 2):
                base[q] = v + deslocamento
    return sorted(base.items())


def _hora(q: datetime) -> datetime:
    return q.replace(minute=0, second=0, microsecond=0)


def _perto(ordenados: list[datetime], q: datetime, tolerancia: timedelta) -> bool:
    import bisect
    i = bisect.bisect_left(ordenados, q)
    for j in (i - 1, i):
        if 0 <= j < len(ordenados) and abs(ordenados[j] - q) <= tolerancia:
            return True
    return False


def tirar_picos_isolados(s: Serie) -> Serie:
    """Leitura que salta mais de SALTO_ISOLADO_M dos DOIS vizinhos em 10–20 min é sensor, não rio."""
    fora = set()
    for i in range(1, len(s) - 1):
        (q0, a), (_, b), (q2, c) = s[i - 1], s[i], s[i + 1]
        if (q2 - q0) <= timedelta(minutes=40) and abs(b - a) > SALTO_ISOLADO_M and abs(b - c) > SALTO_ISOLADO_M:
            fora.add(i)
    return [p for i, p in enumerate(s) if i not in fora]


@dataclass
class Grade:
    """Série regularizada: `inicio` + i × PASSO; `None` onde há buraco."""
    inicio: datetime
    v: list[float | None]

    def t(self, i: int) -> datetime:
        return self.inicio + i * PASSO

    def i(self, q: datetime) -> int:
        return round((q - self.inicio) / PASSO)

    def em(self, q: datetime) -> float | None:
        i = self.i(q)
        return self.v[i] if 0 <= i < len(self.v) else None


def regularizar(s: Serie) -> Grade | None:
    """Interpolação linear numa grade de 10 min; lacuna > LACUNA_MAX vira buraco."""
    if len(s) < 2:
        return None
    ini = s[0][0].replace(second=0, microsecond=0)
    ini -= timedelta(minutes=ini.minute % 10)
    n = int((s[-1][0] - ini) / PASSO) + 1
    v: list[float | None] = [None] * n
    j = 0
    for i in range(n):
        q = ini + i * PASSO
        while j + 1 < len(s) and s[j + 1][0] <= q:
            j += 1
        (qa, a) = s[j]
        if qa == q:
            v[i] = a
            continue
        if j + 1 >= len(s) or qa > q:
            continue
        (qb, b) = s[j + 1]
        if qb - qa > LACUNA_MAX:
            continue
        v[i] = a + (b - a) * ((q - qa) / (qb - qa))
    return Grade(ini, v)


def godin(g: Grade) -> Grade:
    """Filtro de Godin (A24·A24·A25 sobre médias horárias): tira maré diurna e semidiurna.

    Simétrico — não desloca o horário. Hora com buraco contamina as médias que a contêm: a saída fica
    vazia ali, em vez de inventar maré.
    """
    passos_hora = int(timedelta(hours=1) / PASSO)
    horas: list[float | None] = []
    for k in range(0, len(g.v) - passos_hora + 1, passos_hora):
        bloco = g.v[k:k + passos_hora]
        horas.append(None if any(x is None for x in bloco) else sum(bloco) / len(bloco))
    for janela in (24, 24, 25):
        nova: list[float | None] = [None] * len(horas)
        for c in range(len(horas)):
            a = c - janela // 2
            b = a + janela
            if a < 0 or b > len(horas):
                continue
            bloco = horas[a:b]
            if any(x is None for x in bloco):
                continue
            nova[c] = sum(bloco) / janela
        horas = nova
    # de volta à grade de 10 min, centrando cada hora no meio dela
    v: list[float | None] = [None] * len(g.v)
    for i in range(len(v)):
        h = (i - passos_hora // 2) / passos_hora
        a, b = math.floor(h), math.floor(h) + 1
        if 0 <= a and b < len(horas) and horas[a] is not None and horas[b] is not None:
            v[i] = horas[a] + (horas[b] - horas[a]) * (h - a)
    return Grade(g.inicio, v)


#: Constituintes de maré (período em horas) — as principais da costa de SC, como no t_tide/UTide.
#: Variação máxima da parte lenta para o ponto entrar no ajuste da maré (fora das cheias).
MARE_CALMA_M_POR_H = 0.02
#: Dias de calmaria necessários para ajustar dez constituintes com folga.
MARE_MIN_DIAS = 4
#: Na ordem de importância: o critério de Rayleigh decide quais entram, de cima para baixo.
CONSTITUINTES_H = {
    "M2": 12.4206012, "K1": 23.93446966, "S2": 12.0, "O1": 25.81934166, "N2": 12.65834751,
    "M4": 6.210300601, "P1": 24.06589016, "K2": 11.96723606, "Q1": 26.86835667, "MS4": 6.103339275,
}


def constituintes_por_rayleigh(duracao_h: float) -> list[float]:
    """Períodos que a série resolve (critério de Rayleigh, como o t_tide/UTide).

    Na ordem de importância (`CONSTITUINTES_H`), uma constituinte só entra se a frequência dela se afasta
    de todas as já escolhidas em pelo menos 1/duração. Com 16 dias, K1 e P1 (182 dias para separar) ou M2
    e S2 (15 dias) não se distinguem: ajustar as duas daria coeficientes enormes e opostos, e a "maré"
    inventada apareceria justamente nos trechos sem dado.
    """
    escolhidas: list[float] = []
    for periodo in CONSTITUINTES_H.values():
        f = 1 / periodo
        if all(abs(f - 1 / p) * duracao_h >= 1 for p in escolhidas):
            escolhidas.append(periodo)
    return escolhidas


def _resolver(a: list[list[float]], b: list[float]) -> list[float] | None:
    """Eliminação de Gauss com pivô parcial (sistema pequeno: 2 × constituintes)."""
    n = len(b)
    m = [linha[:] + [b[i]] for i, linha in enumerate(a)]
    for c in range(n):
        piv = max(range(c, n), key=lambda r: abs(m[r][c]))
        if abs(m[piv][c]) < 1e-12:
            return None
        m[c], m[piv] = m[piv], m[c]
        for r in range(c + 1, n):
            f = m[r][c] / m[c][c]
            for k in range(c, n + 1):
                m[r][k] -= f * m[c][k]
    x = [0.0] * n
    for r in range(n - 1, -1, -1):
        x[r] = (m[r][n] - sum(m[r][k] * x[k] for k in range(r + 1, n))) / m[r][r]
    return x


def tirar_mare(g: Grade) -> Grade:
    """Maré por ANÁLISE HARMÔNICA (mínimos quadrados, `CONSTITUINTES_H`), tirada da série inteira.

    1. o filtro de Godin separa a parte lenta (rio, maré meteorológica);
    2. no resíduo (série − parte lenta), ajusta seno e cosseno de cada constituinte;
    3. a maré ajustada sai da série ORIGINAL — a cheia fica com a forma dela, sem alisamento.
    Godin sozinho tiraria a maré, mas achataria a crista e a deslocaria para o lado da descida, que é mais
    lenta. Sem 4 dias de resíduo, devolve a série sem mexer (melhor que maré inventada).
    """
    lento = godin(g)
    meia_h = int(timedelta(minutes=30) / PASSO)

    def calmo(i: int) -> bool:
        # Só onde a parte lenta quase não se mexe: numa cheia, o resto do Godin carrega a própria cheia e o
        # ajuste a confundiria com maré diurna. Numa série de meses sobra calmaria de sobra.
        a_, b_ = i - meia_h * 2, i + meia_h * 2
        if a_ < 0 or b_ >= len(lento.v) or lento.v[a_] is None or lento.v[b_] is None:
            return False
        return abs(lento.v[b_] - lento.v[a_]) <= MARE_CALMA_M_POR_H * _horas((b_ - a_) * PASSO)

    pontos = [(i, g.v[i] - lento.v[i]) for i in range(len(g.v))
              if g.v[i] is not None and lento.v[i] is not None and calmo(i)]
    if len(pontos) < MARE_MIN_DIAS * 24 * 6:
        return g
    omegas = [2 * math.pi / p for p in constituintes_por_rayleigh(_horas((pontos[-1][0] - pontos[0][0]) * PASSO))]
    k = 2 * len(omegas)
    ata = [[0.0] * k for _ in range(k)]
    atb = [0.0] * k
    passo_h = _horas(PASSO)
    for i, r in pontos:
        h = i * passo_h
        linha = []
        for w in omegas:
            linha += [math.cos(w * h), math.sin(w * h)]
        for a in range(k):
            la = linha[a]
            atb[a] += la * r
            for b in range(a, k):
                ata[a][b] += la * linha[b]
    for a in range(k):
        for b in range(a):
            ata[a][b] = ata[b][a]
    coef = _resolver(ata, atb)
    if coef is None:
        return g
    v: list[float | None] = []
    for i, x in enumerate(g.v):
        if x is None:
            v.append(None)
            continue
        h = i * passo_h
        mare = sum(coef[2 * j] * math.cos(w * h) + coef[2 * j + 1] * math.sin(w * h) for j, w in enumerate(omegas))
        v.append(x - mare)
    return Grade(g.inicio, v)


# --------------------------------------------------------------------------- eventos

@dataclass
class Evento:
    crista: datetime          # meio do platô
    maximo: datetime          # hora do máximo
    pico: float
    base: float
    inicio: datetime          # vale antes da subida
    prominencia: float
    aberto: bool = False      # o máximo está na ponta da série: a cheia pode não ter passado

    @property
    def amplitude(self) -> float:
        return self.pico - self.base


def _suavizar(v: list[float | None], meia: int = 1) -> list[float | None]:
    """Mediana móvel de 3 pontos (30 min): tira o serrilhado de 1 cm sem deslocar o pico."""
    out: list[float | None] = []
    for i in range(len(v)):
        bloco = [x for x in v[max(0, i - meia):i + meia + 1] if x is not None]
        out.append(statistics.median(bloco) if v[i] is not None and bloco else None)
    return out


def achar_eventos(g: Grade, prominencia_min: float) -> list[Evento]:
    """Picos por proeminência topográfica, separados por SEPARACAO_EVENTOS (fica o mais proeminente)."""
    v = _suavizar(g.v)
    n = len(v)
    lb = int(LOOKBACK / PASSO)
    candidatos: list[Evento] = []
    for i in range(1, n):
        x = v[i]
        if x is None:
            continue
        esq = next((v[j] for j in range(i - 1, -1, -1) if v[j] is not None), None)
        dir_ = next((v[j] for j in range(i + 1, n) if v[j] is not None), None)
        if esq is None or esq > x or (dir_ is not None and dir_ > x):
            continue
        # proeminência: a base é o MAIOR dos dois vales até um ponto mais alto (ou até LOOKBACK)
        vales = []
        idx_vale_esq = i
        for passo, limite in ((-1, max(-1, i - lb)), (1, min(n, i + lb))):
            menor, j, idx, viu = x, i + passo, i, False
            while j != limite:
                y = v[j]
                if y is not None:
                    viu = True
                    if y > x:
                        break
                    if y < menor:
                        menor, idx = y, j
                j += passo
            # A série ACABOU daquele lado sem aparecer ponto mais alto nem descida que feche o evento (a cheia
            # em curso, à direita): o vale de lá é desconhecido e não conta — senão o "vale" seria a última
            # leitura, colada no pico, e a proeminência, zero. Chegar ao LOOKBACK conta normalmente.
            acabou = j in (-1, n) and (passo == 1 or limite == -1)
            fechou = viu and (x - menor) >= max(QUEDA_MIN_M, QUEDA_FRAC * prominencia_min)
            if viu and not (acabou and not fechou):
                vales.append(menor)
            if passo == -1:
                idx_vale_esq = idx
        if not vales:
            continue
        base = max(vales)
        prom = x - base
        if prom < prominencia_min:
            continue
        # platô a PLATO_M do máximo, contíguo ao máximo
        a = i
        while a - 1 >= 0 and v[a - 1] is not None and v[a - 1] >= x - PLATO_M:
            a -= 1
        b = i
        while b + 1 < n and v[b + 1] is not None and v[b + 1] >= x - PLATO_M:
            b += 1
        meio = g.t(a) + (g.t(b) - g.t(a)) / 2
        # Só PASSOU quando o nível caiu de verdade depois do máximo; senão a cheia pode estar no topo agora.
        queda = max(QUEDA_MIN_M, QUEDA_FRAC * prom)
        aberto = not any(y is not None and y <= x - queda for y in v[b + 1:])
        candidatos.append(Evento(meio, g.t(i), x, x - prom, g.t(idx_vale_esq), prom, aberto))
    # um por janela de SEPARACAO_EVENTOS: o mais proeminente
    candidatos.sort(key=lambda e: -e.prominencia)
    escolhidos: list[Evento] = []
    for e in candidatos:
        if all(abs(e.crista - o.crista) >= SEPARACAO_EVENTOS for o in escolhidos):
            escolhidos.append(e)
    return sorted(escolhidos, key=lambda e: e.crista)


def _evento_na_janela(eventos: list[Evento], centro: datetime, janela: tuple[timedelta, timedelta]) -> Evento | None:
    dentro = [e for e in eventos if centro + janela[0] <= e.crista <= centro + janela[1]]
    return max(dentro, key=lambda e: e.prominencia) if dentro else None


# --------------------------------------------------------------------------- métodos

def _horas(d: timedelta) -> float:
    return d.total_seconds() / 3600


def _meia_subida(g: Grade, e: Evento) -> datetime | None:
    alvo = e.base + 0.5 * e.amplitude
    i0, i1 = g.i(e.inicio), g.i(e.maximo)
    anterior = None
    for i in range(max(0, i0), min(len(g.v), i1 + 1)):
        y = g.v[i]
        if y is None:
            anterior = None
            continue
        if anterior is not None and anterior[1] < alvo <= y:
            frac = (alvo - anterior[1]) / (y - anterior[1])
            return g.t(anterior[0]) + frac * PASSO
        anterior = (i, y)
    return None


def _centroide(g: Grade, e: Evento) -> datetime | None:
    """Centro de massa da parte do hidrograma acima de base + metade da amplitude, em volta da crista."""
    corte = e.base + 0.5 * e.amplitude
    i = g.i(e.maximo)
    a = i
    while a - 1 >= 0 and g.v[a - 1] is not None and g.v[a - 1] >= corte:
        a -= 1
    b = i
    while b + 1 < len(g.v) and g.v[b + 1] is not None and g.v[b + 1] >= corte:
        b += 1
    if b + 1 >= len(g.v) or g.v[b + 1] is None:
        return None  # a descida não está na série: o centro de massa sairia puxado para a esquerda
    massa = sum(g.v[k] - corte for k in range(a, b + 1))
    if massa <= 0:
        return None
    k_medio = sum(k * (g.v[k] - corte) for k in range(a, b + 1)) / massa
    return g.inicio + k_medio * PASSO


def _janela(g: Grade, ini: datetime, fim: datetime) -> list[float | None]:
    return [g.em(ini + k * PASSO) for k in range(int((fim - ini) / PASSO) + 1)]


def _xcorr(up: Grade, dn: Grade, centro: datetime) -> float | None:
    """Atraso (h) de maior correlação de Pearson entre as VARIAÇÕES, com refino parabólico."""
    ini, fim = centro + JANELA_FORMA[0], centro + JANELA_FORMA[1]
    a = _janela(up, ini, fim)
    da = [(y - x) if x is not None and y is not None else None for x, y in zip(a, a[1:])]
    melhor: list[tuple[int, float]] = []
    passos = int(LAG_MAX / PASSO)
    for k in range(-int(timedelta(hours=12) / PASSO), passos + 1):
        b = _janela(dn, ini + k * PASSO, fim + k * PASSO)
        db = [(y - x) if x is not None and y is not None else None for x, y in zip(b, b[1:])]
        pares = [(x, y) for x, y in zip(da, db) if x is not None and y is not None]
        if len(pares) < 0.6 * len(da):
            melhor.append((k, float("nan")))
            continue
        r = _pearson(pares)
        melhor.append((k, r))
    validos = [(k, r) for k, r in melhor if not math.isnan(r)]
    if not validos:
        return None
    k, r = max(validos, key=lambda x: x[1])
    if r < 0.3:
        return None
    # refino parabólico com os vizinhos
    vizinhos = dict(validos)
    if k - 1 in vizinhos and k + 1 in vizinhos:
        y0, y1, y2 = vizinhos[k - 1], r, vizinhos[k + 1]
        den = y0 - 2 * y1 + y2
        if den < 0:
            k = k + 0.5 * (y0 - y2) / den
    return k * _horas(PASSO)


def _pearson(pares: list[tuple[float, float]]) -> float:
    n = len(pares)
    mx = sum(x for x, _ in pares) / n
    my = sum(y for _, y in pares) / n
    sxy = sum((x - mx) * (y - my) for x, y in pares)
    sxx = sum((x - mx) ** 2 for x, _ in pares)
    syy = sum((y - my) ** 2 for _, y in pares)
    return sxy / math.sqrt(sxx * syy) if sxx > 0 and syy > 0 else float("nan")


def _dtw(up: Grade, dn: Grade, centro: datetime, e_up: Evento, e_dn: Evento) -> float | None:
    """DTW com banda de Sakoe–Chiba; atraso = mediana dos deslocamentos na metade de cima do evento.

    Cada curva é normalizada pela base e pela amplitude da PRÓPRIA cheia (0 = base, 1 = pico): zeros e
    tamanhos diferentes não entram, só a forma. A normalização z sobre a janela inteira não serve aqui —
    a janela de baixo é mais longa (cobre o atraso) e o rabo dela mudava a escala.
    """
    ini_a, fim_a = centro + JANELA_FORMA[0], centro + JANELA_FORMA[1]
    ini_b, fim_b = ini_a, fim_a + LAG_MAX
    a_raw = _janela(up, ini_a, fim_a)
    b_raw = _janela(dn, ini_b, fim_b)
    if sum(x is None for x in a_raw) > 0.2 * len(a_raw) or sum(x is None for x in b_raw) > 0.2 * len(b_raw):
        return None
    a = [(x - e_up.base) / e_up.amplitude for x in _preencher(a_raw)]
    b = [(x - e_dn.base) / e_dn.amplitude for x in _preencher(b_raw)]
    n, m = len(a), len(b)
    banda = int(BANDA_DTW / PASSO)
    inf = float("inf")
    custo = [[inf] * (m + 1) for _ in range(n + 1)]
    custo[0][0] = 0.0
    for i in range(1, n + 1):
        j0, j1 = max(1, i - int(timedelta(hours=12) / PASSO)), min(m, i + banda)
        ci, cp = custo[i], custo[i - 1]
        ai = a[i - 1]
        for j in range(j0, j1 + 1):
            d = (ai - b[j - 1]) ** 2
            ci[j] = d + min(cp[j], ci[j - 1], cp[j - 1])
    if custo[n][m] == inf:
        # o fim da janela de baixo não precisa casar: termina no melhor j alcançável
        pass
    j_fim = min(range(1, m + 1), key=lambda j: custo[n][j])
    if custo[n][j_fim] == inf:
        return None
    # caminho de volta
    caminho = []
    i, j = n, j_fim
    while i > 0 and j > 0:
        caminho.append((i - 1, j - 1))
        opcoes = ((custo[i - 1][j - 1], i - 1, j - 1), (custo[i - 1][j], i - 1, j), (custo[i][j - 1], i, j - 1))
        _, i, j = min(opcoes)
    corte = e_up.base + 0.5 * e_up.amplitude
    desloc = [(ini_b + jj * PASSO) - (ini_a + ii * PASSO) for ii, jj in caminho
              if a_raw[ii] is not None and a_raw[ii] >= corte]
    if not desloc:
        return None
    return statistics.median(_horas(d) for d in desloc)


def _preencher(v: list[float | None]) -> list[float]:
    """Buraco curto vira o último valor conhecido (só para o DTW, que não aceita vazio)."""
    out, ultimo = [], next((x for x in v if x is not None), 0.0)
    for x in v:
        ultimo = x if x is not None else ultimo
        out.append(ultimo)
    return out


# --------------------------------------------------------------------------- medida do trecho

@dataclass
class Par:
    crista_montante: datetime
    pico_montante: float
    amplitude_montante: float
    crista_jusante: datetime | None
    lags: dict[str, float | None] = field(default_factory=dict)
    obs: str = ""


def medir_par(up: Grade, dn: Grade, e_up: Evento, eventos_dn: list[Evento]) -> Par:
    par = Par(e_up.crista, e_up.pico, e_up.amplitude, None)
    e_dn = _evento_na_janela(eventos_dn, e_up.crista, JANELA_JUSANTE)
    if e_dn is None:
        par.obs = "sem cheia correspondente lá embaixo na janela de −12 a +36 h"
        par.lags = {m: None for m in METODOS}
        return par
    if e_dn.aberto:
        par.obs = "a crista de baixo está na ponta da série (pode não ter passado)"
    par.crista_jusante = e_dn.crista
    ms_up, ms_dn = _meia_subida(up, e_up), _meia_subida(dn, e_dn)
    ce_up, ce_dn = _centroide(up, e_up), _centroide(dn, e_dn)
    par.lags = {
        "crista": _horas(e_dn.crista - e_up.crista),
        "meia_subida": _horas(ms_dn - ms_up) if ms_up and ms_dn else None,
        "centroide": _horas(ce_dn - ce_up) if ce_up and ce_dn else None,
        "xcorr": _xcorr(up, dn, e_up.crista),
        "dtw": _dtw(up, dn, e_up.crista, e_up, e_dn),
    }
    return par


def percentil(xs: list[float], p: float) -> float:
    s = sorted(xs)
    if len(s) == 1:
        return s[0]
    k = (len(s) - 1) * p
    a = math.floor(k)
    b = min(a + 1, len(s) - 1)
    return s[a] + (s[b] - s[a]) * (k - a)


def bootstrap_mediana(xs: list[float], n: int = BOOTSTRAP_N, semente: int = SEMENTE) -> tuple[float, float]:
    rng = random.Random(semente)
    meds = sorted(statistics.median(rng.choices(xs, k=len(xs))) for _ in range(n))
    return percentil(meds, 0.05), percentil(meds, 0.95)


def theil_sen(xs: list[float], ys: list[float]) -> float | None:
    inclin = [(ys[j] - ys[i]) / (xs[j] - xs[i]) for i in range(len(xs)) for j in range(i + 1, len(xs))
              if xs[j] != xs[i]]
    return statistics.median(inclin) if inclin else None


def resumir(pares: list[Par]) -> dict:
    fechados = [p for p in pares if p.crista_jusante is not None and "ponta da série" not in p.obs]
    por_metodo = {}
    for m in METODOS:
        xs = [p.lags[m] for p in fechados if p.lags.get(m) is not None]
        if not xs:
            por_metodo[m] = {"n": 0}
            continue
        ic = bootstrap_mediana(xs) if len(xs) >= 3 else None
        por_metodo[m] = {
            "n": len(xs), "mediana_h": round(statistics.median(xs), 1),
            "p25_h": round(percentil(xs, 0.25), 1), "p75_h": round(percentil(xs, 0.75), 1),
            "ic90_mediana_h": [round(ic[0], 1), round(ic[1], 1)] if ic else None,
        }
    cristas = [p.lags["crista"] for p in fechados if p.lags.get("crista") is not None]
    # Um método só entra na comparação quando mediu a maior parte das cheias: com 1 ou 2 eventos, a mediana
    # dele é um evento solto, e "concordar" com ele não confere nada.
    minimo = max(3, math.ceil(0.5 * len(cristas)))
    medianas = [v["mediana_h"] for v in por_metodo.values() if v.get("n", 0) >= minimo]
    espalhamento = (max(medianas) - min(medianas)) if len(medianas) >= 2 else None
    n = len(cristas)
    iqr = (percentil(cristas, 0.75) - percentil(cristas, 0.25)) if cristas else None
    if n >= 5 and iqr is not None and iqr <= 3 and espalhamento is not None and espalhamento <= 2:
        conf, porque = "alta", None
    elif n >= 3 and iqr is not None and iqr <= 6 and espalhamento is not None and espalhamento <= 4:
        conf, porque = "media", None
    else:
        conf = "insuficiente"
        motivos = []
        if n < 3:
            motivos.append(f"só {n} evento(s) pareado(s)")
        if iqr is not None and iqr > 6:
            motivos.append(f"os eventos discordam: p25–p75 de {iqr:.1f} h")
        if espalhamento is not None and espalhamento > 4:
            motivos.append(f"os métodos discordam em {espalhamento:.1f} h")
        if espalhamento is None and n >= 3:
            motivos.append("só um método achou forma comparável nas duas réguas; sem segundo método, não há "
                           "como conferir")
        porque = "; ".join(motivos) or "métodos sem dado suficiente"
    tendencia = None
    amp = [p.amplitude_montante for p in fechados if p.lags.get("crista") is not None]
    if n >= 5:
        tendencia = theil_sen(amp, cristas)
    simultaneos = sum(1 for x in cristas if abs(x) <= 1.0)
    return {
        "eventos_pareados": n,
        "metodos": por_metodo,
        "espalhamento_entre_metodos_h": round(espalhamento, 1) if espalhamento is not None else None,
        "confianca": conf,
        "por_que_nao": porque,
        "theil_sen_h_por_m": round(tendencia, 2) if tendencia is not None else None,
        "cristas_simultaneas": simultaneos,
    }


# --------------------------------------------------------------------------- montagem

def montar_grades(dcsc: Path | None, coletor: dict[str, Serie]) -> tuple[dict[str, Grade], dict[str, str]]:
    grades: dict[str, Grade] = {}
    faltas: dict[str, str] = {}
    for p in PONTOS.values():
        tipo, chave = p.fonte
        if tipo == "dcsc":
            serie = ler_dcsc(dcsc, chave) if dcsc else []
            # a série do coletor da mesma estação completa a ponta mais nova (o consolidado pode ser de ontem)
            extra = [s for t, s in coletor.items() if chave in t]
            serie = juntar_fontes([serie] + extra)
        else:
            serie = juntar_fontes([coletor.get(t, []) for t in chave])
        serie = tirar_picos_isolados(serie)
        g = regularizar(serie)
        if g is None:
            faltas[p.id] = "sem série"
            continue
        grades[p.id] = tirar_mare(g) if p.mare else g
    return grades, faltas


def medir(grades: dict[str, Grade], faltas: dict[str, str]) -> dict:
    trechos = []
    for t in TRECHOS:
        up, dn = PONTOS[t.de], PONTOS[t.para]
        item = {"rio": t.rio, "de": t.de, "para": t.para, "de_nome": up.nome, "para_nome": dn.nome,
                "jica_h": referencia_jica(t.de, t.para)}
        if t.de not in grades or t.para not in grades:
            item["sem_medida"] = "; ".join(f"{x}: {faltas.get(x, 'sem série')}" for x in (t.de, t.para)
                                           if x not in grades)
            trechos.append(item)
            continue
        g_up, g_dn = grades[t.de], grades[t.para]
        ev_up = [e for e in achar_eventos(g_up, up.prominencia_m) if not e.aberto]
        ev_dn = achar_eventos(g_dn, dn.prominencia_m)
        pares = [medir_par(g_up, g_dn, e, ev_dn) for e in ev_up]
        item["eventos"] = [{
            "crista_montante": p.crista_montante.isoformat(timespec="minutes"),
            "pico_montante_m": round(p.pico_montante, 2),
            "amplitude_montante_m": round(p.amplitude_montante, 2),
            "crista_jusante": p.crista_jusante.isoformat(timespec="minutes") if p.crista_jusante else None,
            "lags_h": {m: (round(v, 1) if v is not None else None) for m, v in p.lags.items()},
            **({"obs": p.obs} if p.obs else {}),
        } for p in pares]
        item["resumo"] = resumir(pares)
        trechos.append(item)
    return {"trechos": trechos}


def agora(grades: dict[str, Grade], resultado: dict) -> list[str]:
    """Para cada trecho: a última cheia de cima, se já passou, e a janela projetada lá embaixo."""
    linhas = []
    for t in resultado["trechos"]:
        g = grades.get(t["de"])
        if g is None:
            continue
        evs = achar_eventos(g, PONTOS[t["de"]].prominencia_m)
        if not evs:
            continue
        e = evs[-1]
        if g.t(len(g.v) - 1) - e.crista > timedelta(hours=48):
            continue  # nenhuma cheia recente em cima
        titulo = f"{t['de_nome']} → {t['para_nome']}"
        if e.aberto:
            linhas.append(f"{titulo}: a cheia de cima ainda não passou (máximo até agora {e.pico:.2f} m às "
                          f"{e.maximo:%d/%m %H:%M}); sem janela.")
            continue
        r = t.get("resumo") or {}
        cr = (r.get("metodos") or {}).get("crista") or {}
        partes = [f"{titulo}: crista em cima {e.crista:%d/%m %H:%M}"]
        if r.get("confianca") in ("alta", "media") and cr.get("n"):
            a, b = e.crista + timedelta(hours=cr["p25_h"]), e.crista + timedelta(hours=cr["p75_h"])
            partes.append(f"medido ({r['confianca']}, {cr['n']} cheias): {a:%d/%m %H:%M}–{b:%d/%m %H:%M}")
        else:
            partes.append(f"medido: {r.get('por_que_nao') or 'sem medida'}")
        if t.get("jica_h"):
            a, b = (e.crista + timedelta(hours=h) for h in t["jica_h"])
            partes.append(f"JICA: {a:%d/%m %H:%M}–{b:%d/%m %H:%M}")
        linhas.append(" · ".join(partes))
    return linhas


# --------------------------------------------------------------------------- relatório

NOMES_METODO = {"crista": "pico a pico", "meia_subida": "meia-subida", "centroide": "centro de massa",
                "xcorr": "correlação", "dtw": "DTW"}


def _faixa_h(f) -> str:
    return f"{f[0]:g} h" if f[0] == f[1] else f"{f[0]:g}–{f[1]:g} h"


def relatorio_md(resultado: dict) -> str:
    m = resultado["_meta"]
    out = [
        "# Descida medida — quanto tempo a cheia leva de uma régua à outra",
        "",
        f"Gerado por `scripts/medir_descida.py` em {m['gerado_em']}. Séries de {m['cobertura']['de']} a "
        f"{m['cobertura']['ate']} (hora de Brasília). **Não é o tempo que o site mostra** (`transito.json`, "
        "Tabela 7.5.1 da JICA): é o que as réguas viram nas cheias de 2026. Trocar o do site é decisão do Jefferson.",
        "",
        "Atraso em horas a partir da crista de cima; negativo = lá embaixo cresta ANTES (chuva local, maré, "
        "afluente). Faixa = p25–p75 dos eventos; IC90 = intervalo de confiança de 90 % da mediana (bootstrap).",
        "",
        "| Trecho | Eventos | Pico a pico | Meia-subida | Centro de massa | Correlação | DTW | JICA | Confiança |",
        "|---|---|---|---|---|---|---|---|---|",
    ]

    def cel(r: dict, k: str) -> str:
        x = (r.get("metodos") or {}).get(k) or {}
        if not x.get("n"):
            return "—"
        return f"{x['mediana_h']:+.1f} ({x['p25_h']:+.1f} a {x['p75_h']:+.1f})"

    for t in resultado["trechos"]:
        nome = f"{t['de_nome']} → {t['para_nome']}"
        jica = _faixa_h(t["jica_h"]) if t.get("jica_h") else "—"
        if "resumo" not in t:
            out.append(f"| {nome} | — | {t.get('sem_medida', '')} | | | | | {jica} | — |")
            continue
        r = t["resumo"]
        conf = r["confianca"] + (f": {r['por_que_nao']}" if r.get("por_que_nao") else "")
        out.append(f"| {nome} | {r['eventos_pareados']} | " + " | ".join(cel(r, k) for k in METODOS)
                   + f" | {jica} | {conf} |")
    out += ["", "## Evento a evento", ""]
    for t in resultado["trechos"]:
        if not t.get("eventos"):
            continue
        out.append(f"### {t['de_nome']} → {t['para_nome']}")
        out.append("")
        out.append("| Crista em cima | Pico (zero da régua) | Crista embaixo | " +
                   " | ".join(NOMES_METODO[k] for k in METODOS) + " | Obs. |")
        out.append("|---|---|---|" + "---|" * len(METODOS) + "---|")
        for e in t["eventos"]:
            lags = " | ".join("—" if e["lags_h"][k] is None else f"{e['lags_h'][k]:+.1f}" for k in METODOS)
            out.append(f"| {e['crista_montante'].replace('T', ' ')} | {e['pico_montante_m']:.2f} m | "
                       f"{(e['crista_jusante'] or '—').replace('T', ' ')} | {lags} | {e.get('obs', '')} |")
        r = t.get("resumo") or {}
        if r.get("theil_sen_h_por_m") is not None:
            out.append("")
            out.append(f"Theil–Sen: {r['theil_sen_h_por_m']:+.2f} h por metro de amplitude em cima "
                       "(negativo = cheia maior desce mais rápido, como a JICA prevê).")
        out.append("")
    out += ["## Como ler", "",
            "- Cada régua tem o seu zero; só o HORÁRIO entra na conta, nunca o metro.",
            "- Nas réguas de Itajaí a maré sai pelo filtro de Godin (24-24-25 h); ele não desloca o horário, "
            "mas achata a crista.",
            "- Cristas quase simultâneas (|atraso| ≤ 1 h) dizem que o baixo vale subiu com a mesma chuva, não "
            "que a água chegou em uma hora.",
            "- **Blumenau → Ilhota e → Itajaí:** a crista lá embaixo vem cedo (1 a 4 h) porque o baixo vale "
            "cresta com a chuva local, o Luiz Alves e o represamento da maré (`docs/ANALISE-CHEGADA-ITAJAI-2026.md`). "
            "Esse número é a hora da crista local, **não** a chegada da água de Blumenau; a JICA (12–17 h até "
            "Itajaí) continua sendo a referência para a onda que desce. Nenhuma das cheias de 2026 foi grande.",
            "- Confiança `alta`: ≥ 5 cheias, p25–p75 ≤ 3 h e métodos a ≤ 2 h; `media`: ≥ 3, ≤ 6 h e ≤ 4 h.",
            ""]
    return "\n".join(out)


def cobertura(grades: dict[str, Grade]) -> dict:
    ini = min((g.inicio for g in grades.values()), default=None)
    fim = max((g.t(len(g.v) - 1) for g in grades.values()), default=None)
    return {"de": ini.isoformat(timespec="minutes") if ini else None,
            "ate": fim.isoformat(timespec="minutes") if fim else None}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    ap.add_argument("--dcsc", type=Path, help="pasta com os DCSC-000NN.csv do consolidar_historico_dcsc.py")
    ap.add_argument("--serie", type=Path, help="pasta com os AAAA-MM.ndjson do coletor (arquivo-series/tempo-real)")
    ap.add_argument("--recente", type=Path, help="serie-recente.json do branch tempo-real (últimas 48 h)")
    ap.add_argument("--agora", action="store_true", help="projeta a janela da cheia em curso")
    ap.add_argument("--gravar", action="store_true",
                    help="grava data/descida-medida.json e docs/DESCIDA-MEDIDA.md (nunca transito.json)")
    a = ap.parse_args(argv)

    arquivos = sorted(a.serie.glob("[0-9][0-9][0-9][0-9]-[0-9][0-9].ndjson*")) if a.serie else []
    coletor = ler_coletor(arquivos)
    if a.recente and a.recente.exists():
        for titulo, s in ler_recente(a.recente).items():
            coletor[titulo] = sorted({**dict(coletor.get(titulo, [])), **dict(s)}.items())
    grades, faltas = montar_grades(a.dcsc, coletor)
    if not grades:
        print("Nenhuma série. Passe --dcsc e/ou --serie.", file=sys.stderr)
        return 1
    resultado = medir(grades, faltas)
    resultado = {"_meta": {
        "o_que_e": ("Tempo de descida MEDIDO nas séries de 2026, por trecho e por método. Derivado; o site e o "
                    "bot não leem. Nunca entra em transito.json por aqui (decisão do Jefferson)."),
        "gerado_em": datetime.now().astimezone().isoformat(timespec="seconds"),
        "fuso": "horário de Brasília, sem fuso (como as séries)",
        "cobertura": cobertura(grades),
        "fontes": {"dcsc": str(a.dcsc) if a.dcsc else None, "coletor": [f.name for f in arquivos],
                   "recente": bool(a.recente)},
        "metodos": {k: NOMES_METODO[k] for k in METODOS},
        "regra_de_confianca": "alta: ≥5 cheias, p25–p75 ≤3 h, métodos a ≤2 h; media: ≥3, ≤6 h, ≤4 h",
    }, **resultado}

    for t in resultado["trechos"]:
        r = t.get("resumo")
        nome = f"{t['de_nome']} → {t['para_nome']}"
        if not r:
            print(f"{nome}: {t.get('sem_medida')}")
            continue
        cr = r["metodos"]["crista"]
        faixa = f"{cr['mediana_h']:+.1f} h ({cr['p25_h']:+.1f} a {cr['p75_h']:+.1f})" if cr.get("n") else "—"
        jica = f" · JICA {_faixa_h(t['jica_h'])}" if t.get("jica_h") else ""
        print(f"{nome}: {r['eventos_pareados']} cheia(s), pico a pico {faixa}{jica} · {r['confianca']}"
              + (f" ({r['por_que_nao']})" if r.get("por_que_nao") else ""))
    if a.agora:
        print("\nAGORA:")
        for linha in agora(grades, resultado) or ["nenhuma cheia nas últimas 48 h"]:
            print("  " + linha)
    if a.gravar:
        (DADOS / "descida-medida.json").write_text(json.dumps(resultado, ensure_ascii=False, indent=1) + "\n",
                                                   encoding="utf-8")
        (RAIZ / "docs" / "DESCIDA-MEDIDA.md").write_text(relatorio_md(resultado), encoding="utf-8")
        print("\ngravado: data/descida-medida.json, docs/DESCIDA-MEDIDA.md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
