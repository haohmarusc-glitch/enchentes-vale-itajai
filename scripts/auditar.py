#!/usr/bin/env python3
"""Audita a série coletada: a coleta está saudável? a defasagem bate com o publicado?

Três perguntas, em ordem de utilidade prática:

1. **A coleta está viva?** Estação que parou de publicar, buraco na série,
   sensor travado repetindo o mesmo valor. Descobrir na cheia que o DC-10 está
   mudo há três dias é tarde demais.
2. **As leituras são plausíveis?** Valor fora de faixa, salto impossível.
3. **A defasagem observada bate com a publicada?** Para cada trecho de
   `transito.json` cujas duas pontas tenham série, mede por correlação cruzada
   qual atraso alinha melhor as duas curvas.

Sobre a pergunta 3, o limite que não dá para contornar: **onda de cheia viaja
mais rápido que água baixa**. Uma defasagem medida em período seco não confirma
nem refuta a faixa da JICA, que vale para cheia. Serve para checar ordem de
grandeza e pegar erro grosseiro — trecho invertido, cidade trocada, faixa dez
vezes maior que a realidade. O relatório diz isso em cada linha, para ninguém
ler o resultado como validação do que não foi validado.

Uso:
    python3 scripts/auditar.py                 # últimos 15 dias
    python3 scripts/auditar.py --dias 30
    python3 scripts/auditar.py --json data/auditoria.json
"""

from __future__ import annotations

import argparse
import gzip
import json
import math
import statistics
import sys
from datetime import datetime, timedelta
from pathlib import Path

from comum import DADOS, le_json

SERIE = DADOS / "tempo-real"

#: Cadência esperada da fonte. A página publica a cada 15-30 min.
CADENCIA_ESPERADA_MIN = 30
#: Vazio acima disto vira alerta de cobertura.
VAZIO_GRAVE_H = 3
#: Mesmo valor por mais que isto sugere sensor travado.
TRAVADO_H = 6
#: Variação mínima da série para a correlação significar alguma coisa.
DESVIO_MINIMO_M = 0.02
#: Passo e alcance da busca de defasagem.
PASSO_MIN = 15
MAX_DEFASAGEM_H = 48
#: Abaixo disto a correlação não sustenta conclusão nenhuma.
CORRELACAO_MINIMA = 0.5
#: Acima disto a defasagem medida é firme o bastante para contradizer o
#: transito.json publicado.
#:
#: Entre os dois valores a medida existe mas não decide. Medido em série
#: sintética com defasagem conhecida de 6 h: com pouco ruído o método devolve
#: 6,00 h com r=0,998; com ruído alto devolve 8,50 h com r=0,593 — erro de duas
#: horas e meia passando pelo limiar de 0,5. Um "fora-da-faixa" dali levaria
#: alguém a mudar tempo de descida publicado, que é o que alimenta a hora de
#: chegada que as pessoas leem.
CORRELACAO_FORTE = 0.9
MIN_PONTOS_SOBREPOSTOS = 48


def arquivos(dias: int) -> list[Path]:
    if not SERIE.exists():
        return []
    return sorted(SERIE.glob("*.ndjson")) + sorted(SERIE.glob("*.ndjson.gz"))


def ler(dias: int) -> dict[str, dict]:
    """Séries por estação, limitadas aos últimos `dias`."""
    corte = datetime.now() - timedelta(days=dias)
    por_estacao: dict[str, dict] = {}
    for arquivo in arquivos(dias):
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
                if quando < corte:
                    continue
                est = d.get("estacao") or "?"
                g = por_estacao.setdefault(
                    est, {"rio": d.get("rio"), "cidade": d.get("cidade"), "pontos": []}
                )
                g["pontos"].append((quando, nivel))
    for g in por_estacao.values():
        g["pontos"] = sorted(set(g["pontos"]))
    return por_estacao


def cobertura(
    pontos: list[tuple[datetime, float]], dias: int, agora: datetime | None = None
) -> dict:
    """
    Saúde da série de uma estação.

    `agora` entra por parâmetro para que todas as estações do relatório sejam
    julgadas contra o MESMO instante — e para que o teste possa fixá-lo. Função
    que lê o relógio por dentro produz relatório em que cada linha mede o tempo
    de um jeito.
    """
    agora = agora or datetime.now()
    if len(pontos) < 2:
        return {"leituras": len(pontos), "veredito": "sem-serie"}

    inicio, fim = pontos[0][0], pontos[-1][0]
    intervalos = [
        (b[0] - a[0]).total_seconds() / 60 for a, b in zip(pontos, pontos[1:])
    ]
    maior_vazio_h = max(intervalos) / 60
    esperado = (dias * 24 * 60) / CADENCIA_ESPERADA_MIN

    # Sensor travado: mesmo valor por horas seguidas.
    travado_h = 0.0
    ini = 0
    for i in range(1, len(pontos) + 1):
        if i == len(pontos) or pontos[i][1] != pontos[ini][1]:
            travado_h = max(travado_h, (pontos[i - 1][0] - pontos[ini][0]).total_seconds() / 3600)
            ini = i

    fora_de_faixa = [p for p in pontos if not 0 < p[1] < 25]
    desvio = statistics.pstdev([p[1] for p in pontos]) if len(pontos) > 1 else 0.0

    problemas = []
    if maior_vazio_h > VAZIO_GRAVE_H:
        problemas.append(f"vazio de {maior_vazio_h:.1f} h na série")
    if travado_h > TRAVADO_H:
        problemas.append(f"mesmo valor por {travado_h:.1f} h — possível sensor travado")
    if fora_de_faixa:
        problemas.append(f"{len(fora_de_faixa)} leitura(s) fora de faixa plausível")
    desatualizada_h = (agora - fim).total_seconds() / 3600
    if desatualizada_h > VAZIO_GRAVE_H:
        problemas.append(f"sem leitura nova há {desatualizada_h:.1f} h")

    return {
        "leituras": len(pontos),
        "de": inicio.isoformat(timespec="minutes"),
        "ate": fim.isoformat(timespec="minutes"),
        "cobertura_pct": round(100 * len(pontos) / esperado, 1) if esperado else None,
        "maior_vazio_h": round(maior_vazio_h, 1),
        "cadencia_mediana_min": round(statistics.median(intervalos), 1),
        "variacao_m": round(desvio, 3),
        "problemas": problemas,
        "veredito": "ok" if not problemas else "atencao",
    }


def reamostrar(pontos: list[tuple[datetime, float]], passo_min: int) -> dict[int, float]:
    """Série numa grade regular, por interpolação linear entre leituras vizinhas."""
    if len(pontos) < 2:
        return {}
    base = pontos[0][0]
    fim = pontos[-1][0]
    grade: dict[int, float] = {}
    i = 0
    passo = timedelta(minutes=passo_min)
    t = base
    while t <= fim:
        while i + 1 < len(pontos) and pontos[i + 1][0] < t:
            i += 1
        a, b = pontos[i], pontos[min(i + 1, len(pontos) - 1)]
        if b[0] == a[0]:
            valor = a[1]
        else:
            fracao = (t - a[0]).total_seconds() / (b[0] - a[0]).total_seconds()
            fracao = min(max(fracao, 0.0), 1.0)
            valor = a[1] + fracao * (b[1] - a[1])
        grade[int((t - base).total_seconds() // 60)] = valor
        t += passo
    return grade


def correlacao(xs: list[float], ys: list[float]) -> float:
    n = len(xs)
    if n < 3:
        return 0.0
    mx, my = sum(xs) / n, sum(ys) / n
    sxy = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    sxx = sum((x - mx) ** 2 for x in xs)
    syy = sum((y - my) ** 2 for y in ys)
    if sxx <= 0 or syy <= 0:
        return 0.0
    return sxy / math.sqrt(sxx * syy)


def defasagem(
    montante: list[tuple[datetime, float]],
    jusante: list[tuple[datetime, float]],
) -> dict | None:
    """
    Atraso, em horas, que melhor alinha a série de jusante com a de montante.

    Só devolve resultado quando as duas séries variam de verdade: com o rio
    parado, qualquer defasagem "alinha" igualmente bem e o número não
    significaria nada.
    """
    if len(montante) < 3 or len(jusante) < 3:
        return None
    if (statistics.pstdev([p[1] for p in montante]) < DESVIO_MINIMO_M
            or statistics.pstdev([p[1] for p in jusante]) < DESVIO_MINIMO_M):
        return None

    base = min(montante[0][0], jusante[0][0])
    desloca_m = int((montante[0][0] - base).total_seconds() // 60)
    desloca_j = int((jusante[0][0] - base).total_seconds() // 60)
    gm = {k + desloca_m: v for k, v in reamostrar(montante, PASSO_MIN).items()}
    gj = {k + desloca_j: v for k, v in reamostrar(jusante, PASSO_MIN).items()}
    if not gm or not gj:
        return None

    melhor = None
    for passos in range(0, int(MAX_DEFASAGEM_H * 60 / PASSO_MIN) + 1):
        atraso = passos * PASSO_MIN
        comuns = [t for t in gm if (t + atraso) in gj]
        if len(comuns) < MIN_PONTOS_SOBREPOSTOS:
            continue
        r = correlacao([gm[t] for t in comuns], [gj[t + atraso] for t in comuns])
        if melhor is None or r > melhor["correlacao"]:
            melhor = {"horas": atraso / 60, "correlacao": r, "pontos": len(comuns)}
    return melhor


def veredito_do_trecho(horas: float, correlacao: float,
                       horas_min: float, horas_max: float) -> str:
    """
    O que a defasagem medida diz sobre a faixa publicada em transito.json.

    Duas coisas separam este veredito de um simples "está dentro ou fora":

    * **A faixa ganha a tolerância de um passo de reamostragem.** A medida tem
      resolução de PASSO_MIN, então 5,75 h contra "6-8 h" é diferença do método,
      não do rio.
    * **Fora da faixa com correlação fraca não contradiz o publicado.** Em série
      sintética com defasagem CONHECIDA de 6 h, o método devolve 6,00 h com
      r=0,998 quando há pouco ruído, e 8,50 h com r=0,593 quando há muito — erro
      de duas horas e meia passando pelo limiar de 0,5. Chamar isso de
      "fora-da-faixa" levaria alguém a mudar tempo de descida publicado, que é o
      que alimenta a hora de chegada que as pessoas leem.
    """
    passo_h = PASSO_MIN / 60
    if (horas_min - passo_h) <= horas <= (horas_max + passo_h):
        return "dentro-da-faixa"
    if correlacao >= CORRELACAO_FORTE:
        return "fora-da-faixa"
    return "fora-da-faixa-sem-firmeza"


def auditar_trechos(por_estacao: dict[str, dict]) -> list[dict]:
    """Compara a defasagem observada com a faixa publicada em transito.json."""
    # Uma régua por cidade: com várias, não dá para saber qual representa a cidade.
    serie_da_cidade: dict[tuple[str, str], tuple[str, list]] = {}
    contagem: dict[tuple[str, str], int] = {}
    for est, g in por_estacao.items():
        chave = (g["rio"], g["cidade"])
        contagem[chave] = contagem.get(chave, 0) + 1
        serie_da_cidade[chave] = (est, g["pontos"])

    saida = []
    for t in le_json("transito.json")["trechos"]:
        chave_m = (t["rio"], t["de"])
        chave_j = (t["rio"], t["para"])
        rotulo = f"{t['de']} -> {t['para']}"
        faixa = f"{t['horas_min']}-{t['horas_max']} h"

        if chave_m not in serie_da_cidade or chave_j not in serie_da_cidade:
            saida.append({"trecho": rotulo, "faixa_publicada": faixa,
                          "veredito": "sem-serie", "detalhe": "uma das pontas não é coletada"})
            continue
        if contagem[chave_m] > 1 or contagem[chave_j] > 1:
            saida.append({"trecho": rotulo, "faixa_publicada": faixa, "veredito": "varias-reguas",
                          "detalhe": "cidade com mais de uma régua; não dá para escolher uma"})
            continue

        est_m, serie_m = serie_da_cidade[chave_m]
        est_j, serie_j = serie_da_cidade[chave_j]
        medida = defasagem(serie_m, serie_j)
        if medida is None:
            saida.append({"trecho": rotulo, "faixa_publicada": faixa, "veredito": "rio-parado",
                          "detalhe": "as séries mal variaram; qualquer defasagem alinharia igual"})
            continue
        if medida["correlacao"] < CORRELACAO_MINIMA:
            saida.append({
                "trecho": rotulo, "faixa_publicada": faixa, "veredito": "correlacao-fraca",
                "horas_observadas": medida["horas"], "correlacao": round(medida["correlacao"], 3),
                "detalhe": "as curvas não se parecem o bastante para medir atraso",
            })
            continue

        veredito = veredito_do_trecho(
            medida["horas"], medida["correlacao"], t["horas_min"], t["horas_max"]
        )
        saida.append({
            "trecho": rotulo,
            "estacoes": [est_m, est_j],
            "faixa_publicada": faixa,
            "horas_observadas": medida["horas"],
            "correlacao": round(medida["correlacao"], 3),
            "pontos": medida["pontos"],
            "veredito": veredito,
        })
    return saida


def main() -> int:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument("--dias", type=int, default=15, help="janela a auditar (padrão: 15)")
    ap.add_argument("--json", help="grava o relatório também em JSON")
    args = ap.parse_args()

    agora = datetime.now()
    por_estacao = ler(args.dias)
    if not por_estacao:
        print(
            f"Nenhuma leitura nos últimos {args.dias} dias em "
            f"{SERIE.relative_to(DADOS.parent)}.\n"
            "A série é construída pelo cron: rode scripts/coleta_niveis.py de tempos em tempos."
        )
        return 0

    print(f"=== COBERTURA — últimos {args.dias} dias ===\n")
    cob = {}
    for est, g in sorted(por_estacao.items()):
        c = cobertura(g["pontos"], args.dias, agora)
        cob[est] = c
        marca = "ok " if c["veredito"] == "ok" else "!! "
        if c["veredito"] == "sem-serie":
            print(f"{marca}{est}: menos de 2 leituras")
            continue
        print(
            f"{marca}{est}\n"
            f"     {c['leituras']} leituras ({c['cobertura_pct']}% do esperado), "
            f"cadência mediana {c['cadencia_mediana_min']} min, "
            f"variação {c['variacao_m']:.3f} m"
        )
        for p in c["problemas"]:
            print(f"     ATENÇÃO: {p}")

    print(f"\n=== DEFASAGEM OBSERVADA vs PUBLICADA ===\n")
    print(
        "Onda de cheia viaja mais rápido que água baixa. Em período seco isto NÃO\n"
        "confirma nem refuta a faixa publicada, que vale para cheia — serve para pegar\n"
        "erro grosseiro: trecho invertido, cidade trocada, faixa fora de ordem de grandeza.\n"
    )
    trechos = auditar_trechos(por_estacao)
    for t in trechos:
        if "horas_observadas" in t:
            print(
                f"{t['trecho']}: publicado {t['faixa_publicada']}, "
                f"observado {t['horas_observadas']:.2f} h "
                f"(r={t['correlacao']}, {t.get('pontos', 0)} pontos) -> {t['veredito']}"
            )
        else:
            print(f"{t['trecho']}: publicado {t['faixa_publicada']} -> {t['veredito']} ({t['detalhe']})")

    problemas = sum(1 for c in cob.values() if c["veredito"] != "ok")
    fora = sum(1 for t in trechos if t["veredito"] == "fora-da-faixa")
    sem_firmeza = sum(1 for t in trechos if t["veredito"] == "fora-da-faixa-sem-firmeza")
    print(f"\n=== RESUMO ===")
    print(f"{len(cob)} estações, {problemas} com problema de coleta.")
    print(f"{len(trechos)} trechos publicados, {fora} com defasagem fora da faixa.")
    if sem_firmeza:
        # Contado à parte de propósito: somado ao de cima, viraria argumento
        # para mexer no transito.json com medida que não decide.
        print(f"{sem_firmeza} ficaram fora da faixa com correlação fraca demais para "
              f"contradizer o publicado (r < {CORRELACAO_FORTE}).")

    if args.json:
        Path(args.json).write_text(
            json.dumps(
                {
                    "gerado_em": agora.astimezone().isoformat(timespec="seconds"),
                    "janela_dias": args.dias,
                    "cobertura": cob,
                    "trechos": trechos,
                },
                ensure_ascii=False,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        print(f"relatório em {args.json}")

    # Problema de coleta é operacional e precisa acordar alguém; defasagem fora
    # da faixa em água baixa é observação, não erro.
    return 1 if problemas else 0


if __name__ == "__main__":
    raise SystemExit(main())
