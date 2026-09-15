#!/usr/bin/env python3
"""Mede o tempo de trânsito pela telemetria, sem depender de `hora` em enchentes.json.

O `calibrar_transito.py` mede a diferença entre horários de pico registrados em
`enchentes.json`. Ele está parado desde que nasceu: nenhum registro histórico
tem o campo `hora`, e nem todo boletim publica isso. Este script chega pelo
outro lado — as séries de 10 em 10 minutos que a Defesa Civil de SC já entrega
e que o `consolidar_historico_dcsc.py` deixa em `data/series/dcsc/`. Uma cheia
que passou por Rio do Sul e por Indaial está inteira ali, com carimbo de tempo,
mesmo que ninguém tenha anotado a hora do pico em lugar nenhum.

Os dois scripts coexistem de propósito: um mede o que a fonte oficial declarou,
o outro o que o sensor viu. Quando os dois convergirem num trecho, a faixa vale
muito mais do que qualquer um dos dois sozinho — e quando divergirem, é sinal
de que a régua ou o registro precisam de conferência antes de ir para a tela.

## Os dois métodos, e por que são dois

**Correlação cruzada** da *variação* de nível. Desloca a série de montante hora
a hora e fica com o deslocamento de maior correlação. Usa a variação, e não o
nível bruto, porque cada cidade tem sua régua com zero próprio (CLAUDE.md) e
parte das estações da DCSC reporta cota absoluta em vez de régua — correlacionar
nível bruto compararia coisas diferentes.

**Pareamento de cristas** por proeminência topográfica: a base de cada pico é o
maior dos dois vales que o cercam dentro de `LOOKBACK_H` horas. Medir "subiu X
nas últimas N horas" não serve aqui — uma cheia do Itajaí leva dois ou três
dias para encher, e uma janela curta devolve a inclinação no meio da rampa, não
o tamanho do evento.

A faixa publicada é o p25–p75 dos lags pareados, não o mínimo e o máximo: um
pareamento errado num evento só não deve esticar a faixa que o morador lê.

## Confiança

- `alta`  — ≥ MIN_EVENTOS cristas pareadas E os dois métodos a ≤ 2 h um do outro
- `media` — ≥ 2 cristas pareadas E os dois métodos a ≤ 4 h
- fora disso o trecho não é gravado. Um trânsito inventado é pior que um
  trânsito ausente: é com ele que alguém decide quando sair de casa.

Trecho que passa por barragem operada (Sul, Oeste, Norte) nunca sobe de `media`,
qualquer que seja o número de eventos: o lag medido vale para o regime de
operação que estava valendo na série, não para outro.

Uso:

    python3 scripts/calibrar_transito_telemetria.py            # só relata
    python3 scripts/calibrar_transito_telemetria.py --escrever # grava em transito.json
"""

from __future__ import annotations

import argparse
import csv
import math
from datetime import datetime, timedelta
from pathlib import Path

from cadastro_dcsc import NAO_MEDE_NIVEL, SUSPEITAS, apos_a_quebra, quebra_de
from calibrar_transito import MIN_EVENTOS, pares_para_calibrar
from comum import DADOS, grava_json, le_json

SERIES = DADOS / "series" / "dcsc"

#: As únicas colunas que este script exige do CSV do consolidar_historico_dcsc.py.
#: Ele grava mais (chuva, bateria); ler só estas evita quebrar se o resto mudar.
COLUNAS_MINIMAS = ["medido_em", "rio_nivel"]

#: Passo da grade reamostrada. A DCSC entrega de 10 em 10 min; 1 h basta para
#: trânsito e segura o custo de uma correlação cruzada em série de meses.
PASSO_H = 1
#: Lag máximo testado. Rio do Sul -> Itajaí inteiro cabe folgado aqui.
MAX_LAG_H = 48
#: Subida mínima, em metros, para uma crista contar como evento.
#:
#: 1,0 m, e o número sai das cotas do próprio projeto, não de gosto: é o
#: degrau entre uma faixa e a seguinte nas cidades deste trecho — Indaial vai
#: de atenção 3,00 a alerta 4,00, Rio do Sul de 4,50 a 5,50, Ascurra de 8,50 a
#: 9,76. Uma subida que não move a cidade de faixa não é a cheia que este
#: script quer cronometrar.
#:
#: MEDIDO em 15/09/2026, contra as séries de 2022-2026: a 0,30 m o método
#: achava 156 "cristas" em Indaial em 3,8 anos (41 por ano, uma a cada nove
#: dias, proeminência mediana de 0,45 m) e 294 em Ascurra (86 por ano). Não
#: eram cheias, eram ondulações — e parear ondulação com ondulação é o que
#: produzia lag de 15 a 48 h em um quarto dos pares.
MIN_PROEMINENCIA_M = 1.0
#: Meia-janela do máximo local, em horas.
JANELA_H = 12
#: Até onde procurar os vales que definem a proeminência de uma crista.
LOOKBACK_H = 96
#: Mesmos limites do consolidar_historico_dcsc.py — sentinela e "não é régua".
LIMITE_SENTINELA = -30.0
LIMITE_PLAUSIVEL = 30.0

#: O lag da correlação tem de sobreviver a partir a série ao meio: se as duas
#: metades discordam em mais que isto, o "melhor deslocamento" é artefato da
#: janela, não trânsito. Com 3,5 anos de série, cada metade ainda tem quase
#: dois anos de cheias — é teste honesto, não formalidade.
MAX_DESVIO_ENTRE_METADES_H = 2
#: Fração mínima dos lags pareados que precisa cair perto da mediana.
#: Sem isto, uma distribuição com duas populações (a real e a espúria) passa
#: escondida atrás do p25-p75, que é justamente o que o percentil faz de bom.
MIN_CONCENTRACAO = 0.70
#: Raio, em horas, do "perto da mediana" acima.
RAIO_CONCENTRACAO_H = 3
#: Tolerância entre os dois métodos, como FRAÇÃO do lag — nunca em horas fixas.
#:
#: "≤ 2 h de diferença" é exigente num trecho de 20 h e é tolerância de 200 %
#: num trecho de 1 h. Era por isso que `ascurra -> indaial` passava como alta
#: com a correlação dizendo 2 h e as cristas dizendo 1 h.
TOLERANCIA_ALTA = 0.25
TOLERANCIA_MEDIA = 0.50
#: Piso absoluto da tolerância: abaixo disto a própria grade já não resolve.
TOLERANCIA_MINIMA_H = 1.0
#: Lag abaixo disto não é medível nesta grade e o trecho é recusado.
#:
#: MEDIDO em 15/09/2026. Na grade de 1 h, `ascurra -> indaial` dava r = 0,105
#: em 2 h e parecia bom. Reamostrando no passo NATIVO da DCSC, de 10 min, o
#: mesmo trecho dá r = 0,009 com a curva PLANA (0,008 a 0,009 em toda a
#: vizinhança de ±40 min): não há pico nenhum. A correlação de 1 h era artefato
#: da agregação — a média horária apagava ruído e fabricava sinal.
#: O mesmo teste CONFIRMA `vidal-ramos -> botuvera`: 5,17 h no passo de 10 min
#: contra 5 h no de 1 h, com pico de verdade. Por isso a regra recusa o lag
#: curto em vez de tentar resgatá-lo: nos trechos curtos desta bacia o sinal
#: não está lá para ser recuperado.
MIN_LAG_RESOLVIVEL_H = 2 * PASSO_H

#: Cidades cujo trecho a jusante passa por barragem operada durante a cheia.
COM_BARRAGEM = {"taio", "ituporanga", "ibirama"}


# --------------------------------------------------------------------------- #
# Leitura das séries
# --------------------------------------------------------------------------- #
def ler_serie(codigo: str, origem: Path = SERIES) -> list[tuple[datetime, float]]:
    """Série (carimbo, nível) de uma estação, já sem sentinela nem leitura implausível.

    `medido_em` vem sem fuso e é horário de Brasília (CLAUDE.md). Fica como está:
    trânsito é diferença entre dois carimbos da mesma fonte, e converter aqui só
    criaria mais uma chance de errar o fuso.
    """
    caminho = origem / f"{codigo}.csv"
    if not caminho.exists():
        return []
    fora: list[tuple[datetime, float]] = []
    with caminho.open(encoding="utf-8") as f:
        for linha in csv.DictReader(f):
            bruto = (linha.get("rio_nivel") or "").strip()
            if not bruto:
                continue
            try:
                valor = float(bruto)
                quando = datetime.fromisoformat(linha["medido_em"][:19])
            except (ValueError, KeyError):
                continue
            if valor <= LIMITE_SENTINELA or abs(valor) > LIMITE_PLAUSIVEL:
                continue
            if apos_a_quebra(codigo, quando):
                # Defesa em profundidade: o consolidador já esvazia o nível depois da quebra ao
                # gravar o CSV, mas um CSV gerado ANTES de 15/09/2026 ainda traz a grandeza nova
                # misturada. Correlacionar régua com altitude produz um lag com aparência de
                # medida — e este script grava `transito.json`, que vai para a tela.
                continue
            fora.append((quando, valor))
    fora.sort(key=lambda t: t[0])
    return fora


def grade(serie: list[tuple[datetime, float]], passo_h: int = PASSO_H
          ) -> tuple[list[datetime], list[float | None]]:
    """Reamostra para uma grade regular. Buraco fica como None — nunca interpolado
    por cima de mais de `passo_h`*3, para não inventar rampa onde faltou leitura."""
    if not serie:
        return [], []
    passo = timedelta(hours=passo_h)
    inicio = serie[0][0].replace(minute=0, second=0, microsecond=0)
    fim = serie[-1][0]
    baldes: dict[datetime, list[float]] = {}
    for quando, valor in serie:
        k = inicio + passo * int((quando - inicio) / passo)
        baldes.setdefault(k, []).append(valor)

    carimbos: list[datetime] = []
    valores: list[float | None] = []
    atual = inicio
    while atual <= fim:
        v = baldes.get(atual)
        carimbos.append(atual)
        valores.append(sum(v) / len(v) if v else None)
        atual += passo

    # preenche buracos de até 3 passos
    for i, v in enumerate(valores):
        if v is not None:
            continue
        esq = next((j for j in range(i - 1, max(-1, i - 4), -1) if valores[j] is not None), None)
        dir_ = next((j for j in range(i + 1, min(len(valores), i + 4)) if valores[j] is not None), None)
        if esq is not None and dir_ is not None:
            peso = (i - esq) / (dir_ - esq)
            valores[i] = valores[esq] + peso * (valores[dir_] - valores[esq])
    return carimbos, valores


# --------------------------------------------------------------------------- #
# Método 1 — correlação cruzada da variação
# --------------------------------------------------------------------------- #
def _correlacao(x: list[float], y: list[float]) -> float | None:
    n = len(x)
    if n < 48:
        return None
    mx, my = sum(x) / n, sum(y) / n
    sxy = sum((a - mx) * (b - my) for a, b in zip(x, y))
    sxx = sum((a - mx) ** 2 for a in x)
    syy = sum((b - my) ** 2 for b in y)
    if sxx <= 0 or syy <= 0:
        return None
    return sxy / math.sqrt(sxx * syy)


def lag_por_correlacao(montante: list[float | None], jusante: list[float | None],
                       max_lag_h: int = MAX_LAG_H) -> tuple[int, float] | None:
    """Deslocamento, em horas, de maior correlação entre as VARIAÇÕES das duas séries."""
    def variacao(v: list[float | None]) -> list[float | None]:
        fora: list[float | None] = [None]
        for anterior, atual in zip(v, v[1:]):
            fora.append(None if anterior is None or atual is None else atual - anterior)
        return fora

    dm, dj = variacao(montante), variacao(jusante)
    melhor: tuple[int, float] | None = None
    for lag in range(0, max_lag_h + 1, PASSO_H):
        passos = lag // PASSO_H
        pares = [(a, b) for a, b in zip(dm, dj[passos:]) if a is not None and b is not None]
        if len(pares) < 48:
            continue
        r = _correlacao([p[0] for p in pares], [p[1] for p in pares])
        if r is not None and (melhor is None or r > melhor[1]):
            melhor = (lag, r)
    return melhor


# --------------------------------------------------------------------------- #
# Método 2 — pareamento de cristas por proeminência
# --------------------------------------------------------------------------- #
def cristas(carimbos: list[datetime], valores: list[float | None],
            min_proeminencia: float = MIN_PROEMINENCIA_M,
            janela_h: int = JANELA_H, lookback_h: int = LOOKBACK_H
            ) -> list[tuple[datetime, float, float]]:
    """(carimbo, nível, proeminência) de cada cheia da série."""
    janela, lookback = janela_h // PASSO_H, lookback_h // PASSO_H
    n = len(valores)
    candidatas: list[tuple[datetime, float, float]] = []
    for i in range(janela, n - janela):
        v = valores[i]
        if v is None:
            continue
        vizinhos = [x for x in valores[i - janela: i + janela + 1] if x is not None]
        if not vizinhos or v < max(vizinhos):
            continue
        esq = [x for x in valores[max(0, i - lookback): i + 1] if x is not None]
        dir_ = [x for x in valores[i: min(n, i + lookback + 1)] if x is not None]
        if not esq or not dir_:
            continue
        prom = v - max(min(esq), min(dir_))
        if prom >= min_proeminencia:
            candidatas.append((carimbos[i], v, prom))

    # cristas coladas: fica a mais proeminente
    candidatas.sort(key=lambda t: -t[2])
    escolhidas: list[tuple[datetime, float, float]] = []
    for c in candidatas:
        if any(abs((c[0] - e[0]).total_seconds()) < janela_h * 3600 for e in escolhidas):
            continue
        escolhidas.append(c)
    return sorted(escolhidas, key=lambda t: t[0])


def parear_cristas(cm: list[tuple[datetime, float, float]],
                   cj: list[tuple[datetime, float, float]],
                   max_lag_h: int = MAX_LAG_H) -> list[float]:
    """Horas entre cada crista de montante e a de jusante que lhe corresponde.

    Como no `calibrar_transito.py`: mais de uma candidata plausível é ambíguo, e
    medir o errado é pior que não medir — só que aqui "plausível" é a crista de
    jusante com proeminência comparável (≥ 40 % da de montante), porque um
    chuvisco local a jusante não é a mesma cheia.
    """
    horas: list[float] = []
    for tm, _, pm in cm:
        candidatas = [
            (tj - tm).total_seconds() / 3600
            for tj, _, pj in cj
            if 0 < (tj - tm).total_seconds() / 3600 <= max_lag_h and pj >= 0.4 * pm
        ]
        if len(candidatas) == 1:
            horas.append(candidatas[0])
    return horas


def lag_estavel(montante: list[float | None], jusante: list[float | None]
                ) -> tuple[bool, int | None, int | None]:
    """O lag da correlação sobrevive a partir a série ao meio?

    A curva r(lag) destas séries tem pico de verdade — a mediana de r sobre
    todos os lags fica em 0,000 e o pico se destaca —, mas o pico é BAIXO
    (r entre 0,05 e 0,25 nos trechos reais) porque correlacionar 3,5 anos
    inteiros dilui a cheia no meio de milhares de horas em que o rio não faz
    nada. Um piso em r, então, ou reprova tudo ou não filtra nada.

    O que separa sinal de artefato aqui não é a altura do pico e sim a
    ESTABILIDADE do argmax: se o deslocamento de maior correlação é trânsito,
    as duas metades da série encontram o mesmo; se é acidente da janela, elas
    discordam. Medido em 15/09/2026: rio-do-sul -> indaial dá 4 h numa metade
    e 8 h na outra, enquanto ituporanga -> rio-do-sul dá 6 h nas duas.
    """
    meio = len(montante) // 2
    a = lag_por_correlacao(montante[:meio], jusante[:meio])
    b = lag_por_correlacao(montante[meio:], jusante[meio:])
    if a is None or b is None:
        return False, a[0] if a else None, b[0] if b else None
    return abs(a[0] - b[0]) <= MAX_DESVIO_ENTRE_METADES_H, a[0], b[0]


def concentracao(lags: list[float], raio_h: int = RAIO_CONCENTRACAO_H) -> float:
    """Fração dos lags a menos de `raio_h` da mediana.

    O p25-p75 protege a faixa publicada de um pareamento errado, mas ESCONDE
    que houve muitos: em ascurra -> indaial, 23 % dos 107 pares tinham lag de
    15 a 48 h — outra população — e mesmo assim a faixa saía 2,0-4,0 h, limpa.
    Esta conta é o que não deixa isso passar calado.
    """
    if not lags:
        return 0.0
    mediana = percentil(lags, 0.5)
    perto = sum(1 for x in lags if abs(x - mediana) <= raio_h)
    return perto / len(lags)


def percentil(valores: list[float], p: float) -> float:
    ordenados = sorted(valores)
    if len(ordenados) == 1:
        return ordenados[0]
    pos = (len(ordenados) - 1) * p
    baixo, alto = math.floor(pos), math.ceil(pos)
    if baixo == alto:
        return ordenados[baixo]
    return ordenados[baixo] + (ordenados[alto] - ordenados[baixo]) * (pos - baixo)


# --------------------------------------------------------------------------- #
# Um trecho
# --------------------------------------------------------------------------- #
def medir_trecho(codigo_montante: str, codigo_jusante: str, origem: Path = SERIES) -> dict | None:
    """Tudo que se sabe sobre um trecho a partir das duas séries, ou None sem dados."""
    sm, sj = ler_serie(codigo_montante, origem), ler_serie(codigo_jusante, origem)
    if not sm or not sj:
        return None
    tm, vm = grade(sm)
    tj, vj = grade(sj)
    if not tm or not tj:
        return None

    # alinha as duas grades pelo trecho em comum
    inicio, fim = max(tm[0], tj[0]), min(tm[-1], tj[-1])
    if fim <= inicio:
        return None
    corta = lambda t, v: zip(*[(a, b) for a, b in zip(t, v) if inicio <= a <= fim])  # noqa: E731
    tm, vm = [list(x) for x in corta(tm, vm)]
    tj, vj = [list(x) for x in corta(tj, vj)]

    corr = lag_por_correlacao(vm, vj)
    estavel, lag_a, lag_b = lag_estavel(vm, vj)
    lags = parear_cristas(cristas(tm, vm), cristas(tj, vj))
    return {
        "lag_correlacao_h": corr[0] if corr else None,
        "r": round(corr[1], 3) if corr else None,
        "lag_estavel": estavel,
        "lag_metades_h": [lag_a, lag_b],
        "lags_cristas_h": [round(h, 1) for h in lags],
        "concentracao": round(concentracao([round(h, 1) for h in lags]), 2),
        "horas_comuns": len(tm),
    }


def classificar(m: dict, com_barragem: bool) -> tuple[str | None, str]:
    """Confiança do trecho e o porquê, em uma linha legível."""
    lags, corr = m["lags_cristas_h"], m["lag_correlacao_h"]
    if not lags or corr is None:
        return None, f"{len(lags)} crista(s) pareada(s), correlação {corr}"

    # Os dois métodos só valem como confirmação um do outro se cada um tiver
    # passado no seu próprio teste antes. Sem isto, um lag de correlação que é
    # artefato da janela "concorda" com a mediana das cristas por acaso e o
    # trecho sobe para alta — foi o que acontecia até 15/09/2026.
    if not m.get("lag_estavel", True):
        a, b = m.get("lag_metades_h", [None, None])
        return None, (f"lag da correlação instável: {a} h numa metade da série "
                      f"e {b} h na outra")
    conc = m.get("concentracao", 1.0)
    if conc < MIN_CONCENTRACAO:
        return None, (f"{len(lags)} crista(s), mas só {conc:.0%} dos pares caem a "
                      f"±{RAIO_CONCENTRACAO_H} h da mediana — mais de uma população")

    mediana = percentil(lags, 0.5)
    if mediana < MIN_LAG_RESOLVIVEL_H:
        return None, (f"lag de {mediana:.1f} h encosta no passo da grade "
                      f"({PASSO_H} h) — quantização, não medição")

    diferenca = abs(mediana - corr)
    tol_alta = max(TOLERANCIA_MINIMA_H, TOLERANCIA_ALTA * mediana)
    tol_media = max(TOLERANCIA_MINIMA_H, TOLERANCIA_MEDIA * mediana)
    if len(lags) >= MIN_EVENTOS and diferenca <= tol_alta:
        conf = "alta"
    elif len(lags) >= 2 and diferenca <= tol_media:
        conf = "media"
    else:
        return None, (f"{len(lags)} crista(s), métodos a {diferenca:.1f} h "
                      f"um do outro — mais que os {tol_media:.1f} h que um lag "
                      f"de {mediana:.1f} h admite")
    if com_barragem and conf == "alta":
        conf = "media"
    return conf, (f"{len(lags)} crista(s), correlação em {corr} h "
                  f"(r={m['r']}, estável nas duas metades), "
                  f"{m.get('concentracao', 1.0):.0%} dos pares a ±{RAIO_CONCENTRACAO_H} h "
                  f"da mediana de {percentil(lags, 0.5):.1f} h")


def recusa_do_cadastro(cod_montante: str, cod_jusante: str) -> str | None:
    """Motivo pelo qual este par NÃO pode ser medido, pelo cadastro da rede — ou None.

    Vem antes de qualquer conta, e recusa UMA coisa só: estação que não mede nível de rio nesta
    rede. Gaspar (DCSC-00005) e Blumenau (DCSC-00026) estão em `estacoes.json` com `codigo_dcsc`
    e nenhuma das duas mede — Blumenau é `type=Meteo`. Sem esta checagem o script tentaria
    cronometrar `blumenau -> gaspar`; os guardas estatísticos até recusariam, mas pela razão
    errada ("sem crista pareada"), que é a razão que faz alguém tentar de novo amanhã com mais
    série. Não é falta de série: não há rio medido ali.

    O QUE NÃO SE RECUSA AQUI, e por quê:
      * **datum/escala não calibrada** (`SUSPEITAS`) — trânsito é diferença entre dois HORÁRIOS,
        e este script correlaciona a VARIAÇÃO justamente para o zero de cada régua não entrar na
        conta. Recusar por datum seria recusar por um motivo que não se aplica à medida. Sai
        como aviso, em `aviso_do_cadastro`.
      * **quebra de série** — essa sim mistura duas grandezas DENTRO da mesma série, mas o corte
        já é feito leitura a leitura em `ler_serie`, e o que sobra antes da quebra é régua de
        verdade, medível.
    """
    for papel, cod in (("montante", cod_montante), ("jusante", cod_jusante)):
        if cod in NAO_MEDE_NIVEL:
            return f"{cod} ({papel}) não mede nível de rio nesta rede — {NAO_MEDE_NIVEL[cod]}"
    return None


def aviso_do_cadastro(cod_montante: str, cod_jusante: str) -> str | None:
    """O que o leitor precisa saber sobre este par, sem que isso impeça a medida."""
    recados = []
    for papel, cod in (("montante", cod_montante), ("jusante", cod_jusante)):
        if cod in SUSPEITAS:
            recados.append(f"{cod} ({papel}) tem datum/escala não calibrada (cadastro_dcsc.SUSPEITAS) "
                           "— não atrapalha o lag, mas o NÍVEL desta estação não é publicável")
        q = quebra_de(cod)
        if q:
            recados.append(f"{cod} ({papel}) tem quebra de série em {q['desde']}: só a parte "
                           "anterior entra na conta")
    return "; ".join(recados) or None


# --------------------------------------------------------------------------- #
def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0],
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--escrever", action="store_true",
                    help="grava os trechos medidos em transito.json")
    ap.add_argument("--series", type=Path, default=SERIES,
                    help="pasta das séries da DCSC (padrão: data/series/dcsc)")
    args = ap.parse_args()

    if not args.series.exists():
        print(f"{args.series} não existe. Rode antes o consolidar_historico_dcsc.py "
              "(ou o baixar_historico_dcsc.py, se ainda não há zips).")
        return 1

    estacoes = le_json("estacoes.json")
    dcsc: dict[str, str] = {}
    for rio in estacoes["rios"].values():
        for c in rio["cidades"]:
            if c.get("codigo_dcsc"):
                dcsc[c["id"]] = c["codigo_dcsc"]

    transito = le_json("transito.json")
    por_chave = {(t["rio"], t["de"], t["para"]): t for t in transito["trechos"]}
    medidos = 0

    for rio, de, para in pares_para_calibrar():
        rotulo = f"{rio}: {de} -> {para}"
        if de not in dcsc or para not in dcsc:
            falta = ", ".join(c for c in (de, para) if c not in dcsc)
            print(f"{rotulo}: sem codigo_dcsc em {falta}")
            continue

        impedimento = recusa_do_cadastro(dcsc[de], dcsc[para])
        if impedimento:
            print(f"{rotulo}: não medível — {impedimento}")
            continue
        aviso = aviso_do_cadastro(dcsc[de], dcsc[para])
        if aviso:
            print(f"{rotulo}: atenção — {aviso}")

        m = medir_trecho(dcsc[de], dcsc[para], args.series)
        if m is None:
            print(f"{rotulo}: sem série em data/series/dcsc")
            continue

        conf, porque = classificar(m, de in COM_BARRAGEM)
        if conf is None:
            print(f"{rotulo}: não publicável — {porque}")
            continue

        lags = m["lags_cristas_h"]
        novo = {
            "rio": rio,
            "de": de,
            "para": para,
            "horas_min": round(percentil(lags, 0.25), 1),
            "horas_max": round(percentil(lags, 0.75), 1),
            "confianca": conf,
            "fonte": (
                "Medido na telemetria da Defesa Civil de SC "
                f"({dcsc[de]} -> {dcsc[para]}, {m['horas_comuns']} h de série em comum): "
                f"{porque}. Faixa = p25-p75 das cristas pareadas."
                + (" Trecho com barragem operada: a confiança não passa de média."
                   if de in COM_BARRAGEM else "")
            ),
        }
        anterior = por_chave.get((rio, de, para))
        if anterior:
            print(f"{rotulo}: {novo['horas_min']}–{novo['horas_max']} h ({conf}) "
                  f"— hoje {anterior['horas_min']}–{anterior['horas_max']} h "
                  f"({anterior['confianca']}, literatura)")
        else:
            print(f"{rotulo}: {novo['horas_min']}–{novo['horas_max']} h ({conf}) — trecho novo")
        por_chave[(rio, de, para)] = novo
        medidos += 1

    if not medidos:
        print("\nNenhum trecho medível. Faltam séries em data/series/dcsc "
              "ou cristas em comum entre as estações do par.")
        return 0
    if not args.escrever:
        print(f"\n{medidos} trecho(s) medido(s). Rode com --escrever para gravar.")
        return 0

    transito["trechos"] = sorted(por_chave.values(), key=lambda t: (t["rio"], t["de"], t["para"]))
    grava_json("transito.json", transito)
    print(f"\ntransito.json atualizado com {medidos} trecho(s) medido(s) na telemetria.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
