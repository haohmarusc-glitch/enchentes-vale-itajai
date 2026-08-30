#!/usr/bin/env python3
"""Coleta a maré de Itajaí do endpoint JSON da Defesa Civil.

Por que a maré importa: em Itajaí a preamar TRAVA o escoamento do rio. Uma
cheia que chega na maré alta é pior que a mesma cheia chegando na vazante — e o
Itajaí-Mirim, que deságua no Açu dentro da cidade, deixa de entregar água
quando os dois leitos estão cheios. O site cruza a janela de chegada da cheia
com as preamares deste arquivo.

FONTE: `ajax/mares.php`, o mesmo endpoint que o gráfico do site consome. Ele
não aceita parâmetro nenhum — devolve a série inteira que a Defesa Civil tem
publicada no momento. Formato, lido do próprio `mares.js` do site:

    {"tides":              [{"datetime", "date_formated", "tidelevel"}],
     "astronimical_tides": [{"datetime", "date_formated", "level"}]}

* `tides` é a maré OBSERVADA pelo marégrafo, com `tidelevel` em centímetros
  (o site divide por 100 para plotar em metros).
* `astronimical_tides` é a maré ASTRONÔMICA prevista, com `level` já em metros.
  É a tábua propriamente dita, e é dela que saem as preamares.
* A chave `astronimical_tides` está escrita assim na API, com o erro de
  digitação. Não é engano deste script.

As preamares são os máximos locais da curva astronômica. A fonte publica uma
série contínua, não uma tabela de quatro linhas por dia, então o horário da
maré alta é calculado — e calculado a partir do dado oficial, não estimado.

Uso:
    python3 scripts/coleta_mares.py --verificar   # mostra o que veio, não grava
    python3 scripts/coleta_mares.py               # grava data/mare-itajai.json
    python3 scripts/coleta_mares.py --arquivo r.json --verificar   # de um arquivo
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
DESTINO = RAIZ / "data" / "mare-itajai.json"

URL = "https://defesacivil.itajai.sc.gov.br/monitoramento/ajax/mares.php"
UA = "enchentes-vale-itajai/0.1 (+https://github.com/haohmarusc-glitch/enchentes-vale-itajai)"

#: Altura plausível de maré no porto de Itajaí. Fora disso, o número não é maré.
ALTURA_MIN_M = -1.0
ALTURA_MAX_M = 3.0

#: Janela para considerar um ponto máximo local. A maré semidiurna tem preamares
#: a cada ~12 h 25 min; 2 h para cada lado isola um pico sem juntar dois.
JANELA_PICO_H = 2

FORMATOS = (
    "%Y-%m-%dT%H:%M:%S",
    "%Y-%m-%d %H:%M:%S",
    "%Y-%m-%dT%H:%M",
    "%Y-%m-%d %H:%M",
    "%d/%m/%Y %H:%M:%S",
    "%d/%m/%Y %H:%M",
)


def instante(texto: str) -> datetime | None:
    """Converte o `datetime` da API. Devolve None em vez de adivinhar."""
    texto = (texto or "").strip().replace("Z", "")
    if not texto:
        return None
    try:
        return datetime.fromisoformat(texto)
    except ValueError:
        pass
    for f in FORMATOS:
        try:
            return datetime.strptime(texto, f)
        except ValueError:
            continue
    return None


def serie_astronomica(resposta: dict) -> list[dict]:
    """(instante, altura em metros) da maré astronômica, em ordem cronológica."""
    saida = []
    for item in resposta.get("astronimical_tides") or []:
        quando = instante(item.get("datetime", ""))
        if quando is None:
            continue
        try:
            altura = float(item["level"])
        except (KeyError, TypeError, ValueError):
            continue
        if not ALTURA_MIN_M <= altura <= ALTURA_MAX_M:
            continue
        saida.append({"quando": quando, "altura_m": round(altura, 2)})
    saida.sort(key=lambda p: p["quando"])
    return saida


def serie_observada(resposta: dict) -> list[dict]:
    """A maré medida pelo marégrafo. `tidelevel` vem em CENTÍMETROS."""
    saida = []
    for item in resposta.get("tides") or []:
        quando = instante(item.get("datetime", ""))
        if quando is None:
            continue
        try:
            altura = float(item["tidelevel"]) / 100.0
        except (KeyError, TypeError, ValueError):
            continue
        if not ALTURA_MIN_M <= altura <= ALTURA_MAX_M:
            continue
        saida.append({"quando": quando, "altura_m": round(altura, 2)})
    saida.sort(key=lambda p: p["quando"])
    return saida


def extremos(serie: list[dict], maximos: bool = True) -> list[dict]:
    """
    Preamares (máximos) ou baixa-mares (mínimos) da curva.

    Um ponto é extremo quando é o maior (ou menor) da janela de
    `JANELA_PICO_H` horas em volta dele. Pontos empatados dentro da mesma
    janela viram um só: é a mesma maré, lida duas vezes.

    As pontas da série nunca contam. O primeiro ponto é o menor de tudo que
    veio depois dele, mas isso diz onde os dados começam, não onde a maré
    virou — e publicar isso como baixa-mar seria inventar uma maré que a fonte
    não afirma.
    """
    if len(serie) < 3:
        return []

    janela = timedelta(hours=JANELA_PICO_H)
    achados: list[dict] = []

    for ponto in serie:
        antes = [p for p in serie
                 if timedelta(0) < ponto["quando"] - p["quando"] <= janela]
        depois = [p for p in serie
                  if timedelta(0) < p["quando"] - ponto["quando"] <= janela]
        if not antes or not depois:
            continue  # ponta da série: não dá para saber se a maré virou aqui
        vizinhos = antes + depois
        alturas = [p["altura_m"] for p in vizinhos]
        eh_extremo = (
            ponto["altura_m"] >= max(alturas) if maximos else ponto["altura_m"] <= min(alturas)
        )
        if not eh_extremo:
            continue
        # Sem vizinho estritamente diferente, é trecho plano — não é maré alta.
        if all(abs(a - ponto["altura_m"]) < 1e-9 for a in alturas):
            continue
        # Já registrou um extremo desta mesma maré?
        if achados and ponto["quando"] - achados[-1]["quando"] <= janela:
            melhor = (
                ponto["altura_m"] > achados[-1]["altura_m"] if maximos
                else ponto["altura_m"] < achados[-1]["altura_m"]
            )
            if melhor:
                achados[-1] = ponto
            continue
        achados.append(ponto)

    return achados


def formatar(pontos: list[dict]) -> list[dict]:
    return [
        {"quando": p["quando"].strftime("%Y-%m-%dT%H:%M"), "altura_m": p["altura_m"]}
        for p in pontos
    ]


def montar(astronomica: list[dict], observada: list[dict]) -> dict:
    preamares = extremos(astronomica, maximos=True)
    baixamares = extremos(astronomica, maximos=False)
    return {
        "_meta": {
            "descricao": (
                "Tábua de maré do porto de Itajaí. O site cruza estas preamares com a janela "
                "de chegada da cheia: maré alta trava o escoamento do rio."
            ),
            "fuso": "Horário local (America/Sao_Paulo), sem indicação de fuso — igual ao "
                    "que a fonte publica e ao que o site espera.",
            "fonte": URL,
            "fonte_oficial": "Tábuas de maré da Marinha do Brasil (DHN) — porto de Itajaí",
            "metodo": (
                "Preamares e baixa-mares são os máximos e mínimos locais da curva de maré "
                "astronômica que a Defesa Civil publica. A fonte não traz a tábua em forma de "
                "tabela; os horários são calculados a partir dela, não estimados."
            ),
            "aviso": "Gerado por scripts/coleta_mares.py.",
        },
        "porto": "Itajaí",
        "coletado_em": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "pontos_astronomicos": len(astronomica),
        "pontos_observados": len(observada),
        "preamares": formatar(preamares),
        "baixamares": formatar(baixamares),
    }


def main() -> int:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument("--verificar", action="store_true", help="mostra o que veio e não grava")
    ap.add_argument("--arquivo", help="analisa uma resposta JSON salva em vez de baixar")
    args = ap.parse_args()

    if args.arquivo:
        try:
            resposta = json.loads(Path(args.arquivo).read_text(encoding="utf-8"))
        except (OSError, ValueError) as e:
            print(f"ERRO ao ler {args.arquivo}: {e}", file=sys.stderr)
            return 1
    else:
        try:
            import requests
        except ImportError:  # pragma: no cover
            print(
                "Para baixar é preciso o requests: pip install -r scripts/requirements.txt",
                file=sys.stderr,
            )
            return 2
        try:
            from comum import baixar

            resposta = json.loads(baixar(URL))
        except Exception as e:
            print(f"ERRO ao baixar {URL}: {e}", file=sys.stderr)
            return 1

    astronomica = serie_astronomica(resposta)
    observada = serie_observada(resposta)
    dados = montar(astronomica, observada)

    print(f"maré astronômica: {len(astronomica)} ponto(s)")
    print(f"maré observada:   {len(observada)} ponto(s)")
    print(f"preamares:   {len(dados['preamares'])}")
    for e in dados["preamares"]:
        print(f"   ALTA  {e['quando']}  {e['altura_m']:.2f} m")
    print(f"baixa-mares: {len(dados['baixamares'])}")
    for e in dados["baixamares"]:
        print(f"   BAIXA {e['quando']}  {e['altura_m']:.2f} m")

    if not astronomica:
        print(
            "\nA fonte não publicou maré astronômica agora — as listas vieram vazias.\n"
            "Isso não é falha deste script: o gráfico de maré do próprio site também fica em\n"
            "branco nesse estado. Enquanto durar, a tela da foz pede a tábua a quem estiver\n"
            "usando, em vez de estimar horário de preamar. O arquivo NÃO foi alterado.",
            file=sys.stderr,
        )
        return 1

    if args.verificar:
        print("\n--verificar: nada foi gravado.")
        return 0

    temporario = DESTINO.with_suffix(".json.tmp")
    temporario.write_text(json.dumps(dados, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporario.replace(DESTINO)
    print(f"\ngravado em {DESTINO.relative_to(RAIZ)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
