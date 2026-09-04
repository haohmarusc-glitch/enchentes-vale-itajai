#!/usr/bin/env python3
"""
Mede quanto cada régua oscila com a maré, para decidir por dado quais podem
disparar aviso automático.

O problema que este script resolve: as onze estações de Itajaí têm cota oficial
do Plano de Contingência da COMPDEC, mas nove ficam no estuário, onde o nível
sobe e desce com a maré duas vezes por dia. Em 30/08/2026 a DC-01 marcou
1,24 m às 17:21 — acima da sua cota de atenção, 1,16 — e 0,70 m três horas
depois, sem enchente nenhuma. Um aviso disparado ali tocaria com a maré, e
aviso que toca à toa ensina a pessoa a ignorar o que tocar na noite da cheia.

Por isso `estacoes.json` marca essas nove com `alerta_automatico: false`. A
marca foi posta por julgamento, olhando três leituras. Este script troca o
julgamento por medição, sobre a série que a coleta vem juntando.

O que ele calcula, por estação:

* **amplitude diária** — a diferença entre o maior e o menor nível de cada dia,
  e a mediana dessas diferenças. Régua de estuário tem amplitude grande todo
  dia; régua de rio só tem quando chove.
* **folga até a cota** — quanto falta, do nível típico, até a cota de atenção.
  Quando a amplitude diária é MAIOR que a folga, a régua cruza a cota sozinha.
* **travessias** — quantas vezes o nível cruzou a cota de atenção para cima na
  série inteira, e em quantos dias distintos. Muitas travessias em muitos dias
  sem enchente registrada é a assinatura da maré.

O veredito é uma SUGESTÃO com o número ao lado, não uma decisão automática:
mudar quem dispara aviso é decisão de quem mantém o projeto.

Uso:
    python3 scripts/medir_mare.py
    python3 scripts/medir_mare.py --mes 2026-09
"""

from __future__ import annotations

import argparse
import gzip
import math
import json
import statistics
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path

from comum import (DADOS, classificar_estacao, cota_de_referencia,
                   estacao_por_titulo, estacoes_tempo_real)

SERIE = DADOS / "tempo-real"

#: Abaixo disto a série não diz nada: um dia de dados não separa maré de cheia.
MIN_DIAS = 3


def leituras_da_serie(mes: str | None) -> dict[str, list[tuple[datetime, float]]]:
    padroes = [f"{mes}.ndjson", f"{mes}.ndjson.gz"] if mes else ["*.ndjson", "*.ndjson.gz"]
    arquivos: list[Path] = []
    for padrao in padroes:
        arquivos.extend(sorted(SERIE.glob(padrao)))

    por_estacao: dict[str, list[tuple[datetime, float]]] = defaultdict(list)
    for arquivo in arquivos:
        abrir = gzip.open if arquivo.suffix == ".gz" else open
        with abrir(arquivo, "rt", encoding="utf-8") as f:
            for linha in f:
                linha = linha.strip()
                if not linha:
                    continue
                try:
                    d = json.loads(linha)
                    quando = datetime.fromisoformat(d["medido_em"])
                    nivel = float(d["nivel_m"])
                except (ValueError, KeyError, TypeError):
                    continue
                por_estacao[d.get("estacao", "?")].append((quando, nivel))
    for pontos in por_estacao.values():
        pontos.sort()
    return por_estacao


def travessias(pontos: list[tuple[datetime, float]], cota: float) -> tuple[int, int]:
    """(quantas subidas atravessaram a cota, em quantos dias distintos)."""
    n, dias = 0, set()
    for (_, antes), (quando, agora) in zip(pontos, pontos[1:]):
        if antes < cota <= agora:
            n += 1
            dias.add(quando.date())
    return n, len(dias)


def menor_cota(titulo: str, reguas_na_cidade: int) -> float | None:
    """
    A menor cota que vale para ESTA régua.

    A da própria estação quando cadastrada; senão a da cidade, mas só se a
    cidade tiver uma régua só — mesma regra do resto do projeto. Em Itajaí são
    onze com zeros diferentes, e emprestar a cota da cidade a todas mediria a
    folga contra a régua errada.
    """
    estacao = estacao_por_titulo(titulo) or {}
    proprias = [v for v in (estacao.get("cotas_m") or {}).values()
                if isinstance(v, (int, float))]
    if proprias:
        return min(proprias)
    if reguas_na_cidade > 1:
        return None
    rio, cidade = classificar_estacao(titulo)
    if not rio or not cidade:
        return None
    valor, _ = cota_de_referencia(rio, cidade)
    return valor


#: Janela da média móvel que separa o lento do rápido. 13 h porque a maré
#: semidiurna tem período de 12,4 h: a média sobre pouco mais que um ciclo
#: apaga a maré e deixa a recessão da cheia, então o resíduo é o oposto — a
#: maré sem a cheia.
JANELA_DESTENDENCIA_H = 13.0

#: Acima disto, o resíduo desta régua anda junto com o de uma régua de maré
#: conhecida — é maré. O valor separa o que foi medido em 04/09/2026: a DC-11
#: deu +0,92 com a DC-09 e +0,79 com a DC-03 (maré), contra +0,09 com Blumenau
#: e +0,17 com a DC-10 (rio acima).
CORRELACAO_DE_MARE = 0.60


def destendenciar(pontos: list[tuple[datetime, float]],
                  janela_h: float = JANELA_DESTENDENCIA_H) -> list[float]:
    """
    Tira a média móvel: sobra só o que oscila mais rápido que a janela.

    POR QUE ISTO EXISTE (04/09/2026). A amplitude diária NÃO distingue maré de
    cheia — as duas fazem o nível oscilar, e este script chamava as duas de
    "oscila". Numa semana com evento, ele recomendaria TRAVAR régua que estava
    alarmando certo, que é o erro na direção que cala. Foi o que quase
    aconteceu com a DC-11: a janela de 6 dias tinha uma cheia dentro (Blumenau
    caiu 1,15 m, a DC-10 1,00 m, Brusque 0,52 m no mesmo período).

    A recessão de uma cheia é LENTA (dias); a maré é RÁPIDA (12,4 h). Tirando a
    média móvel de 13 h, a recessão sai e a maré fica.
    """
    meia = janela_h * 1800  # metade da janela, em segundos
    saida = []
    for i, (t, v) in enumerate(pontos):
        viz = [w for u, w in pontos if abs((u - t).total_seconds()) <= meia]
        saida.append(v - statistics.fmean(viz) if len(viz) >= 5 else 0.0)
    return saida


#: Período da maré semidiurna lunar (M2). É a componente que domina a maré na
#: costa de SC, e o que se procura no sinal rápido de uma régua de estuário.
PERIODO_M2_H = 12.42

#: Fração da variância rápida que precisa estar NA frequência da maré para a
#: régua ser chamada de estuário. Validado com dado sintético: maré pura dá ~1,0;
#: rio com ruído lento dá abaixo de 0,2.
FRACAO_DE_MARE = 0.45


def fracao_na_frequencia_da_mare(pontos: list[tuple[datetime, float]],
                                 periodo_h: float = PERIODO_M2_H) -> float | None:
    """
    Quanto da oscilação RÁPIDA desta régua está na frequência da maré (0 a 1).

    POR QUE ISTO SUBSTITUIU A CORRELAÇÃO COM OUTRA RÉGUA (04/09/2026)
    ----------------------------------------------------------------
    A primeira versão comparava o resíduo desta régua com o de NOVE réguas de
    estuário e ficava com o MAIOR. Rodado na VPS, isso deu falso positivo em
    cheio:

        Taió       "MARÉ" — correlação +0,69 com DC-04
        Blumenau   "MARÉ" — correlação +0,73 com DC-05

    Taió fica a ~200 km do mar. E o DC-05, usado ali de referência, falhava no
    próprio teste ("não é maré", +0,43) — eu estava usando como padrão uma régua
    que o método reprovava.

    Duas causas, as duas minhas:

    * **comparação múltipla** — pegar o máximo entre nove candidatas infla o
      número sozinho, ainda mais em série curta;
    * **a maré PROPAGA com atraso** rio acima, então correlacionar a atraso zero
      entre réguas a distâncias diferentes mede menos do que existe (a DC-11 dá
      +0,55 com a DC-01, que fica 11 km mais perto do mar) e o "melhor par" acaba
      escolhido por acaso de fase, não por física.

    Este teste não tem referência, então não tem nem uma coisa nem outra: mede a
    energia do resíduo NA frequência da maré, contra a energia total dele. É um
    ajuste de seno e cosseno no período M2 — régua de estuário concentra quase
    tudo ali; rio, quase nada.
    """
    if len(pontos) < 20:
        return None
    residuo = destendenciar(pontos)
    t0 = pontos[0][0]
    horas = [(t - t0).total_seconds() / 3600 for t, _ in pontos]
    # Menos de dois ciclos não distingue período nenhum.
    if horas[-1] < 2 * periodo_h:
        return None

    w = 2 * math.pi / periodo_h
    media = statistics.fmean(residuo)
    y = [v - media for v in residuo]
    n = len(y)
    a = 2 / n * sum(v * math.cos(w * h) for v, h in zip(y, horas))
    b = 2 / n * sum(v * math.sin(w * h) for v, h in zip(y, horas))
    energia_mare = (a * a + b * b) / 2
    energia_total = sum(v * v for v in y) / n
    if energia_total <= 0:
        return None
    return min(1.0, energia_mare / energia_total)


def correlacao(a: list[float], b: list[float]) -> float | None:
    """Pearson entre duas listas do mesmo tamanho, ou None se não der."""
    par = [(x, y) for x, y in zip(a, b) if x is not None and y is not None]
    if len(par) < 20:
        return None
    xs = [p[0] for p in par]
    ys = [p[1] for p in par]
    mx, my = statistics.fmean(xs), statistics.fmean(ys)
    den = (sum((x - mx) ** 2 for x in xs) * sum((y - my) ** 2 for y in ys)) ** 0.5
    return None if den == 0 else sum((x - mx) * (y - my) for x, y in par) / den


def amostrar(pontos: list[tuple[datetime, float]],
             grade: list[datetime]) -> list[float | None]:
    """Interpola a série nos instantes da grade, para duas réguas se compararem."""
    saida: list[float | None] = []
    for t in grade:
        ant = nxt = None
        for u, v in pontos:
            if u <= t:
                ant = (u, v)
            else:
                nxt = (u, v)
                break
        if ant is None or nxt is None:
            saida.append(None)
            continue
        h = (nxt[0] - ant[0]).total_seconds()
        saida.append(ant[1] if h <= 0 else
                     ant[1] + ((t - ant[0]).total_seconds() / h) * (nxt[1] - ant[1]))
    return saida


def duracao_das_travessias(pontos: list[tuple[datetime, float]],
                           cota: float) -> list[float]:
    """
    Quanto tempo (horas) a régua fica ACIMA da cota, em cada travessia.

    É o número que separa maré de cheia sem depender de outra régua: a maré
    cruza e volta em horas; a cheia cruza e FICA. E é o que calibra uma regra
    de persistência — "só avisar depois de N horas acima" —, que sem esta
    medição seria chute.
    """
    duracoes = []
    inicio = None
    for t, v in pontos:
        if v >= cota and inicio is None:
            inicio = t
        elif v < cota and inicio is not None:
            duracoes.append((t - inicio).total_seconds() / 3600)
            inicio = None
    if inicio is not None:  # ainda acima quando a série termina
        duracoes.append((pontos[-1][0] - inicio).total_seconds() / 3600)
    return duracoes


def medir(titulo: str, pontos: list[tuple[datetime, float]],
          reguas_na_cidade: int = 1) -> dict | None:
    if len(pontos) < 4:
        return None
    por_dia: dict[object, list[float]] = defaultdict(list)
    for quando, nivel in pontos:
        por_dia[quando.date()].append(nivel)
    amplitudes = [max(v) - min(v) for v in por_dia.values() if len(v) >= 4]
    if not amplitudes:
        return None

    estacao = estacao_por_titulo(titulo) or {}
    cota = menor_cota(titulo, reguas_na_cidade)
    niveis = [n for _, n in pontos]
    tipico = statistics.median(niveis)

    amplitude = statistics.median(amplitudes)
    folga = None if cota is None else round(cota - tipico, 2)
    cruzou, dias_cruzou = travessias(pontos, cota) if cota is not None else (0, 0)

    duracoes = duracao_das_travessias(pontos, cota) if cota is not None else []
    fracao = fracao_na_frequencia_da_mare(pontos)
    return {
        "estacao": titulo,
        "codigo": estacao.get("codigo"),
        # Quanto da oscilação rápida está NA frequência da maré (0 a 1). É o
        # teste principal: não usa referência, então não sofre de comparação
        # múltipla nem do atraso com que a maré sobe o rio.
        "mare_fracao": None if fracao is None else round(fracao, 2),
        # Quanto tempo a régua fica acima da cota em cada travessia. Maré cruza
        # e volta em horas; cheia cruza e fica. Sem outra régua para comparar,
        # é o melhor separador que existe — e é o que calibraria uma regra de
        # persistência.
        "horas_acima_mediana": (round(statistics.median(duracoes), 1)
                                if duracoes else None),
        "horas_acima_maxima": round(max(duracoes), 1) if duracoes else None,
        "leituras": len(pontos),
        "dias": len(por_dia),
        "nivel_tipico_m": round(tipico, 2),
        "amplitude_diaria_mediana_m": round(amplitude, 2),
        "menor_cota_m": cota,
        "folga_ate_a_cota_m": folga,
        "travessias": cruzou,
        "dias_com_travessia": dias_cruzou,
        "alerta_automatico_hoje": estacao.get("alerta_automatico", True),
    }


def veredito(m: dict) -> tuple[str, str]:
    """
    (sugestão, porquê). Sugestão, não decisão.

    A ORDEM DAS REGRAS IMPORTA, e mudou em 04/09/2026. Antes, a primeira coisa
    que decidia era a amplitude — e amplitude não distingue maré de cheia.
    Agora a ASSINATURA DE MARÉ vem primeiro quando existe: se a oscilação rápida
    desta régua está concentrada no período de 12,4 h, é maré, e aí a amplitude
    quer dizer o que o script sempre supôs. Quando a assinatura diz
    que NÃO é maré, a amplitude grande passa a ser evidência de CHEIA — e
    recomendar trava nesse caso calaria um aviso verdadeiro.
    """
    if m.get("mare_fracao") is not None and m["mare_fracao"] < FRACAO_DE_MARE:
        if m.get("menor_cota_m") is not None and m["travessias"]:
            return ("pode disparar",
                    f"só {m['mare_fracao']:.0%} da oscilação rápida está na frequência "
                    f"da maré (12,4 h), abaixo de {FRACAO_DE_MARE:.0%} — a oscilação "
                    f"parece ser o RIO")
    if m["dias"] < MIN_DIAS:
        return "sem opinião", f"só {m['dias']} dia(s) de série; um dia não separa maré de cheia"
    if m["menor_cota_m"] is None:
        return "sem opinião", "estação sem cota cadastrada"
    if m["folga_ate_a_cota_m"] is not None and m["amplitude_diaria_mediana_m"] > m["folga_ate_a_cota_m"]:
        selo = ""
        if m.get("mare_fracao") is not None and m["mare_fracao"] >= FRACAO_DE_MARE:
            selo = (f"; e a oscilação É de maré ({m['mare_fracao']:.0%} dela está no "
                    f"período de 12,4 h)")
        if m.get("horas_acima_mediana") is not None:
            selo += (f"; fica acima da cota {m['horas_acima_mediana']:.1f} h por travessia "
                     f"(máx {m['horas_acima_maxima']:.1f} h)")
        return ("NÃO disparar sozinha",
                f"oscila {m['amplitude_diaria_mediana_m']:.2f} m por dia contra "
                f"{m['folga_ate_a_cota_m']:.2f} m de folga até a cota — cruza sozinha{selo}")
    if m["dias_com_travessia"] >= max(2, m["dias"] // 3):
        return ("NÃO disparar sozinha",
                f"cruzou a cota em {m['dias_com_travessia']} de {m['dias']} dias")
    return ("pode disparar",
            f"oscila {m['amplitude_diaria_mediana_m']:.2f} m por dia com "
            f"{m['folga_ate_a_cota_m']:.2f} m de folga; "
            f"{m['travessias']} travessia(s) em {m['dias']} dias")


def reguas_de_mare_conhecidas() -> list[str]:
    """
    As réguas que o CADASTRO já declara de estuário (`alerta_automatico: false`).

    São a referência contra a qual se testa uma régua em dúvida. Usar o cadastro
    e não uma lista aqui dentro é de propósito: quem destravar uma delas tira a
    referência junto, e é bom que as duas coisas andem juntas.
    """
    return [e.get("titulo", "") for e in (estacoes_tempo_real() or [])
            if e.get("alerta_automatico") is False and e.get("titulo")]


def marcar_assinatura_de_mare(medidas: list[dict],
                              serie: dict[str, list[tuple[datetime, float]]]) -> None:
    """
    Anota, em cada medida, se a oscilação RÁPIDA dela anda junto com a de uma
    régua de maré conhecida — o teste que separa maré de cheia.

    Sem isto, a amplitude sozinha confunde as duas: numa semana com evento, a
    recessão da cheia faz toda régua "oscilar", e o script recomendaria travar
    quem estava alarmando certo.
    """
    referencias = [t for t in reguas_de_mare_conhecidas() if t in serie]
    for m in medidas:
        pontos = serie.get(m["estacao"]) or []
        outras = [t for t in referencias if t != m["estacao"]]
        if len(pontos) < 20 or not outras:
            m["mare_correlacao"] = None
            m["mare_referencia"] = None
            continue
        grade = [t for t, _ in pontos]
        meu = destendenciar(pontos)
        melhor = (None, None)
        for titulo in outras:
            amostra = amostrar(serie[titulo], grade)
            # Só compara onde as duas têm valor; o resto vira None e sai fora.
            pares = [(a, b) for a, b in zip(meu, amostra) if b is not None]
            if len(pares) < 20:
                continue
            # Destendencia a referência JÁ AMOSTRADA, na mesma grade.
            ref_pontos = [(t, b) for (t, _), b in zip(pontos, amostra) if b is not None]
            outro = destendenciar(ref_pontos)
            r = correlacao([a for a, _ in pares], outro)
            if r is not None and (melhor[0] is None or r > melhor[0]):
                melhor = (r, titulo)
        m["mare_correlacao"] = None if melhor[0] is None else round(melhor[0], 2)
        m["mare_referencia"] = melhor[1]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--mes", help="AAAA-MM; sem isso, a série inteira")
    ap.add_argument("--json", action="store_true", help="despeja as medidas em JSON")
    args = ap.parse_args()

    serie = leituras_da_serie(args.mes)
    if not serie:
        print("Nenhuma série em data/tempo-real/. Rode a coleta por alguns dias antes.",
              file=sys.stderr)
        return 1

    # Quantas réguas cada cidade tem NA SÉRIE: é o que decide se a cota da
    # cidade pode ser emprestada à estação.
    reguas: dict[tuple, int] = {}
    for titulo in serie:
        reguas[classificar_estacao(titulo)] = reguas.get(classificar_estacao(titulo), 0) + 1
    medidas = [
        m for m in (medir(t, p, reguas.get(classificar_estacao(t), 1))
                    for t, p in sorted(serie.items()))
        if m
    ]
    marcar_assinatura_de_mare(medidas, serie)
    if args.json:
        print(json.dumps(medidas, ensure_ascii=False, indent=2))
        return 0

    print(f"{len(medidas)} estação(ões) na série.\n")
    divergem = []
    for m in medidas:
        sugestao, porque = veredito(m)
        hoje = "dispara" if m["alerta_automatico_hoje"] else "não dispara"
        marca = ""
        if sugestao == "pode disparar" and not m["alerta_automatico_hoje"]:
            marca = "   <<< hoje está travada; a medição não confirma a trava"
            divergem.append(m)
        if sugestao == "NÃO disparar sozinha" and m["alerta_automatico_hoje"]:
            marca = "   <<< hoje dispara; a medição diz que não devia"
            divergem.append(m)
        print(f"{m['codigo'] or '—':6} {m['estacao'][:44]:44}")
        print(f"       {m['leituras']:5d} leituras em {m['dias']} dia(s) · "
              f"típico {m['nivel_tipico_m']:.2f} m · oscila {m['amplitude_diaria_mediana_m']:.2f} m/dia")
        print(f"       cota {m['menor_cota_m']} · folga {m['folga_ate_a_cota_m']} · "
              f"{m['travessias']} travessia(s) em {m['dias_com_travessia']} dia(s)")
        if m.get("horas_acima_mediana") is not None:
            print(f"       fica acima da cota {m['horas_acima_mediana']:.1f} h por travessia "
                  f"(máx {m['horas_acima_maxima']:.1f} h)")
        if m.get("mare_fracao") is not None:
            eh = "MARÉ" if m["mare_fracao"] >= FRACAO_DE_MARE else "não é maré"
            extra = ""
            if m.get("mare_correlacao") is not None:
                # Secundária: informativa quando a referência é de fato de
                # estuário, mas NÃO decide — ver `fracao_na_frequencia_da_mare`.
                extra = (f" · anda com {m['mare_referencia'][:24]} "
                         f"({m['mare_correlacao']:+.2f})")
            print(f"       assinatura: {eh} — {m['mare_fracao']:.0%} da oscilação "
                  f"rápida no período de 12,4 h{extra}")
        print(f"       hoje: {hoje} · medição sugere: {sugestao} — {porque}{marca}\n")

    if divergem:
        print(f"{len(divergem)} estação(ões) em que a medição discorda do cadastro. "
              "Mudar quem dispara aviso é decisão de quem mantém o projeto, não deste script.")
    else:
        print("A medição concorda com o cadastro em todas as estações.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
