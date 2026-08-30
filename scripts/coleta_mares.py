#!/usr/bin/env python3
"""Coleta a tábua de maré publicada pela Defesa Civil de Itajaí.

Por que a maré importa: em Itajaí a preamar TRAVA o escoamento do rio. Uma
cheia que chega na maré alta é pior que a mesma cheia chegando na vazante — e o
Itajaí-Mirim, que deságua no Açu dentro da cidade, deixa de entregar água
quando os dois leitos estão cheios. O site cruza a janela de chegada da cheia
com as preamares deste arquivo.

ATENÇÃO — a estrutura da página NÃO foi conferida contra o site no ar (o
ambiente onde este script foi escrito não tem acesso ao domínio). Por isso o
analisador não depende de seletores de HTML: ele varre o TEXTO da página atrás
de pares "HH:MM" + altura em metros, e classifica preamar/baixa-mar pelas
palavras ao redor. Rode `--verificar` uma vez e confira as linhas na tela antes
de confiar no arquivo gerado.

Uso:
    python3 scripts/coleta_mares.py --verificar   # mostra o que achou, não grava
    python3 scripts/coleta_mares.py               # grava data/mare-itajai.json

Idempotente: reescrever o arquivo com a mesma tábua não muda nada além do
carimbo de coleta.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import date, datetime, timezone
from pathlib import Path

try:
    import requests
except ImportError:  # pragma: no cover
    sys.exit("Instale as dependências: pip install -r scripts/requirements.txt")

try:
    from bs4 import BeautifulSoup
except ImportError:  # pragma: no cover
    sys.exit("Instale as dependências: pip install -r scripts/requirements.txt")

URL = "https://defesacivil.itajai.sc.gov.br/monitoramento/mares"
UA = "enchentes-vale-itajai/0.1 (+https://github.com/haohmarusc-glitch/enchentes-vale-itajai)"
RAIZ = Path(__file__).resolve().parent.parent
DESTINO = RAIZ / "data" / "mare-itajai.json"

#: Altura plausível de maré no porto de Itajaí. Fora disso, o número lido não é maré.
ALTURA_MIN_M = 0.0
ALTURA_MAX_M = 3.0

RE_DATA = re.compile(r"\b(\d{2})/(\d{2})/(\d{4})\b")
# "03:12  1,2 m" ou "03:12 - 1.2m" ou "PREAMAR 03:12 1,2"
RE_ENTRADA = re.compile(
    r"(?P<hora>\b[0-2]?\d:[0-5]\d\b)\D{0,20}?(?P<altura>\d{1,2}[.,]\d{1,2})\s*m?\b",
    re.I,
)
# Rótulos explícitos. Sem "alta"/"baixa" soltos: casariam com qualquer palavra da página.
RE_PREAMAR = re.compile(r"pre[aá]?[- ]?mar|mar[ée]\s+alta", re.I)
RE_BAIXAMAR = re.compile(r"baixa[- ]?mar|mar[ée]\s+baixa", re.I)


def texto_da_pagina(html: str) -> list[str]:
    """
    Linhas de texto da página, em ordem de leitura.

    Cada linha de tabela vira UMA linha, com as células juntas: numa tabela o
    horário e a altura ficam em `<td>` separados, e separá-los faria o par
    "03:12 / 1,20 m" deixar de ser reconhecido.
    """
    sopa = BeautifulSoup(html, "html.parser")
    for tag in sopa(["script", "style"]):
        tag.decompose()

    linhas: list[str] = []
    for elemento in sopa.find_all(["h1", "h2", "h3", "h4", "caption", "tr", "li", "p", "div"]):
        # Só o nível mais interno interessa: um <div> que contém tabela repetiria tudo.
        if elemento.find(["tr", "li", "p", "div", "table"]):
            continue
        texto = elemento.get_text(" ", strip=True)
        if texto:
            linhas.append(re.sub(r"\s+", " ", texto))

    if not linhas:  # página sem nenhuma dessas tags: cai no texto corrido
        linhas = [l.strip() for l in sopa.get_text("\n", strip=True).split("\n") if l.strip()]
    return linhas


def analisar(linhas: list[str]) -> tuple[list[dict], list[dict], str | None]:
    """Devolve (preamares, baixamares, data_encontrada)."""
    dia: str | None = None
    #: Rótulo da seção corrente — um cabeçalho "Preamar" vale para as linhas seguintes.
    rotulo_secao: str | None = None
    rotuladas: list[tuple[str, dict]] = []
    sem_rotulo: list[dict] = []

    for linha in linhas:
        m_data = RE_DATA.search(linha)
        if m_data:
            d, mes, ano = m_data.groups()
            try:
                dia = date(int(ano), int(mes), int(d)).isoformat()
            except ValueError:
                pass

        na_linha: str | None = None
        tem_pre = bool(RE_PREAMAR.search(linha))
        tem_baixa = bool(RE_BAIXAMAR.search(linha))
        if tem_pre and not tem_baixa:
            na_linha = "preamar"
        elif tem_baixa and not tem_pre:
            na_linha = "baixamar"

        entradas = list(RE_ENTRADA.finditer(linha))
        if na_linha and not entradas:
            rotulo_secao = na_linha  # cabeçalho de seção
            continue

        for m in entradas:
            altura = float(m.group("altura").replace(",", "."))
            if not ALTURA_MIN_M <= altura <= ALTURA_MAX_M:
                continue  # não é altura de maré (nível de rio, por exemplo)
            if dia is None:
                continue  # sem data não dá para montar o horário; descartar é o certo
            hora = m.group("hora")
            if len(hora) == 4:
                hora = "0" + hora
            entrada = {"quando": f"{dia}T{hora}", "altura_m": altura}

            rotulo = na_linha or rotulo_secao
            if rotulo:
                rotuladas.append((rotulo, entrada))
            else:
                sem_rotulo.append(entrada)

    preamares = [e for r, e in rotuladas if r == "preamar"]
    baixamares = [e for r, e in rotuladas if r == "baixamar"]

    # Nada rotulado na página inteira: separa pela altura — as maiores do dia
    # são as preamares. Só vale quando não há NENHUM rótulo, para não misturar
    # critérios diferentes no mesmo arquivo.
    if not rotuladas and sem_rotulo:
        alturas = sorted(e["altura_m"] for e in sem_rotulo)
        corte = alturas[len(alturas) // 2]
        preamares = [e for e in sem_rotulo if e["altura_m"] >= corte]
        baixamares = [e for e in sem_rotulo if e["altura_m"] < corte]

    def ordenar(xs: list[dict]) -> list[dict]:
        unicas = sorted({(e["quando"], e["altura_m"]) for e in xs})
        return [{"quando": q, "altura_m": a} for q, a in unicas]

    return ordenar(preamares), ordenar(baixamares), dia


def montar(preamares: list[dict], baixamares: list[dict]) -> dict:
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
            "aviso": (
                "Gerado por scripts/coleta_mares.py. A leitura da página não foi conferida "
                "contra o site no ar; rode com --verificar e confira antes de confiar."
            ),
        },
        "porto": "Itajaí",
        "coletado_em": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "preamares": preamares,
        "baixamares": baixamares,
    }


def main() -> int:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument("--verificar", action="store_true", help="mostra o que achou e não grava")
    ap.add_argument("--arquivo", help="analisa um HTML salvo em vez de baixar")
    args = ap.parse_args()

    if args.arquivo:
        html = Path(args.arquivo).read_text(encoding="utf-8", errors="replace")
    else:
        try:
            r = requests.get(URL, headers={"User-Agent": UA}, timeout=30)
            r.raise_for_status()
        except requests.RequestException as e:
            print(f"ERRO ao baixar {URL}: {e}", file=sys.stderr)
            return 1
        html = r.text

    preamares, baixamares, dia = analisar(texto_da_pagina(html))

    print(f"data encontrada na página: {dia or '(nenhuma)'}")
    print(f"preamares: {len(preamares)}")
    for e in preamares:
        print(f"   ALTA  {e['quando']}  {e['altura_m']:.2f} m")
    print(f"baixa-mares: {len(baixamares)}")
    for e in baixamares:
        print(f"   BAIXA {e['quando']}  {e['altura_m']:.2f} m")

    if not preamares:
        print(
            "\nAVISO: nenhuma preamar reconhecida. A estrutura da página provavelmente mudou "
            "— o arquivo NÃO foi alterado, para não apagar uma tábua boa por uma leitura ruim.",
            file=sys.stderr,
        )
        return 1

    if args.verificar:
        print("\n--verificar: nada foi gravado.")
        return 0

    temporario = DESTINO.with_suffix(".json.tmp")
    temporario.write_text(
        json.dumps(montar(preamares, baixamares), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    temporario.replace(DESTINO)
    print(f"\ngravado em {DESTINO.relative_to(RAIZ)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
