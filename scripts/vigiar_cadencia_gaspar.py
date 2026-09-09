#!/usr/bin/env python3
"""
Mede a cadência real da estação 21 de Gaspar (Rio Itajaí-Açu) pelo campo
"Última Medição" — e não pela frequência com que este script roda.

POR QUE EXISTE (09/09/2026). A página `/estacao/ver/21` está viva sob o site
novo da Defesa Civil de Gaspar, mas às 21h a leitura era das 08:03 — treze
horas de idade. Se a estação publica uma leitura por turno, Gaspar ganha número
e continua cinza quase o dia inteiro (MIN_VELHA = 180 min), o que é diferente
de "voltou a funcionar". Só a cadência decide se vale reapontar o coletor.

REGRA METODOLÓGICA: a cadência é o intervalo entre MUDANÇAS de "Última
Medição". Rodar de hora em hora não faz a estação ser horária.

ONDE RODAR: de um IP no Brasil. O host não responde à VPS na Finlândia
(timeout medido em 07/09/2026), então o cron tem de ficar num computador ou
celular (Termux) em casa. Uma linha no crontab:

    0 * * * * cd /caminho/do/repo && python3 scripts/vigiar_cadencia_gaspar.py >> gaspar-cadencia.log 2>&1

O QUE GRAVA: uma linha por consulta em `data/tempo-real/gaspar-cadencia.csv`
(consultado_em, ultima_medicao, nivel_m, mudou). Se a página mudar de formato e
o parser não achar os campos, o HTML é salvo ao lado para conferência e a
linha registra o erro — silêncio nunca.

Uso:
    python3 scripts/vigiar_cadencia_gaspar.py                    # consulta e grava
    python3 scripts/vigiar_cadencia_gaspar.py --arquivo pagina.html   # testa o parser sem rede
    python3 scripts/vigiar_cadencia_gaspar.py --resumo           # intervalos entre mudanças
"""

from __future__ import annotations

import argparse
import csv
import re
import sys
import unicodedata
from datetime import datetime
from pathlib import Path

from comum import DADOS, USER_AGENT

URL = "https://defesacivil.gaspar.sc.gov.br/estacao/ver/21"
SAIDA = DADOS / "tempo-real" / "gaspar-cadencia.csv"
CAMPOS = ["consultado_em", "ultima_medicao", "nivel_m", "mudou", "erro"]


def sem_acento(texto: str) -> str:
    return unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode().lower()


def texto_da_pagina(html: str) -> str:
    """HTML → texto corrido, para os regex não dependerem das tags."""
    sem_script = re.sub(r"<(script|style)\b.*?</\1>", " ", html, flags=re.S | re.I)
    texto = re.sub(r"<[^>]+>", " ", sem_script)
    texto = texto.replace("&nbsp;", " ")
    return re.sub(r"\s+", " ", texto)


def extrair(html: str) -> dict:
    """{'ultima_medicao': 'dd/mm/aaaa hh:mm', 'nivel_m': float} — ou o que der, com erro."""
    t = texto_da_pagina(html)
    plano = sem_acento(t)
    saida: dict = {"ultima_medicao": None, "nivel_m": None, "erro": None}

    m = re.search(r"ultima medicao\D{0,40}(\d{2}/\d{2}/\d{4})\D{0,5}(\d{2}:\d{2})", plano)
    if m:
        saida["ultima_medicao"] = f"{m.group(1)} {m.group(2)}"

    # "NÍVEL DO RIO 1,12 m" — o número que segue o rótulo, com vírgula ou ponto.
    n = re.search(r"nivel do rio\D{0,40}?(\d{1,2}[.,]\d{1,2})\s*m\b", plano)
    if n:
        saida["nivel_m"] = float(n.group(1).replace(",", "."))

    faltam = [k for k in ("ultima_medicao", "nivel_m") if saida[k] is None]
    if faltam:
        saida["erro"] = "parser não achou: " + ", ".join(faltam)
    return saida


def ultima_linha(caminho: Path = SAIDA) -> dict | None:
    if not caminho.exists():
        return None
    with caminho.open(encoding="utf-8") as f:
        linhas = list(csv.DictReader(f))
    return linhas[-1] if linhas else None


def registrar(dados: dict, agora: datetime, caminho: Path = SAIDA) -> dict:
    anterior = ultima_linha(caminho)
    mudou = ""
    if dados.get("ultima_medicao"):
        mudou = "sim" if (anterior is None or anterior.get("ultima_medicao") != dados["ultima_medicao"]) else "nao"
    linha = {
        "consultado_em": agora.strftime("%Y-%m-%dT%H:%M:%S"),
        "ultima_medicao": dados.get("ultima_medicao") or "",
        "nivel_m": "" if dados.get("nivel_m") is None else f"{dados['nivel_m']:.2f}",
        "mudou": mudou,
        "erro": dados.get("erro") or "",
    }
    caminho.parent.mkdir(parents=True, exist_ok=True)
    novo = not caminho.exists()
    with caminho.open("a", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=CAMPOS)
        if novo:
            w.writeheader()
        w.writerow(linha)
    return linha


def intervalos_entre_mudancas(linhas: list[dict]) -> list[float]:
    """Horas entre leituras efetivamente novas — a cadência de verdade."""
    marcas = []
    for l in linhas:
        if l.get("mudou") == "sim" and l.get("ultima_medicao"):
            try:
                marcas.append(datetime.strptime(l["ultima_medicao"], "%d/%m/%Y %H:%M"))
            except ValueError:
                continue
    return [round((b - a).total_seconds() / 3600, 2) for a, b in zip(marcas, marcas[1:])]


def baixar() -> str:
    import urllib.request

    req = urllib.request.Request(URL, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode("utf-8", errors="replace")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--arquivo", metavar="HTML", help="testa o parser num HTML salvo, sem rede e sem gravar")
    ap.add_argument("--resumo", action="store_true", help="imprime os intervalos entre mudanças e sai")
    args = ap.parse_args()

    if args.resumo:
        linhas = []
        if SAIDA.exists():
            with SAIDA.open(encoding="utf-8") as f:
                linhas = list(csv.DictReader(f))
        horas = intervalos_entre_mudancas(linhas)
        print(f"{len(linhas)} consulta(s); {sum(1 for l in linhas if l.get('mudou') == 'sim')} leitura(s) nova(s).")
        print("intervalos entre leituras novas (h):", horas or "ainda não há duas")
        return 0

    if args.arquivo:
        dados = extrair(Path(args.arquivo).read_text(encoding="utf-8", errors="replace"))
        print(dados)
        return 0 if not dados["erro"] else 1

    agora = datetime.now()
    try:
        html = baixar()
    except Exception as erro:  # rede, timeout, HTTP
        linha = registrar({"erro": f"rede: {erro}"}, agora)
        print(linha, file=sys.stderr)
        return 1
    dados = extrair(html)
    if dados["erro"]:
        guardado = SAIDA.parent / f"gaspar-21-{agora.strftime('%Y%m%dT%H%M')}.html"
        guardado.write_text(html, encoding="utf-8")
        dados["erro"] += f" (HTML salvo em {guardado.name})"
    linha = registrar(dados, agora)
    print(linha)
    return 0 if not dados["erro"] else 1


if __name__ == "__main__":
    sys.exit(main())
