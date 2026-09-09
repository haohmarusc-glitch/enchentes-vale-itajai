#!/usr/bin/env python3
"""
Imprime as faixas de condição que a Defesa Civil de Blumenau publica no JSON oficial.

POR QUE EXISTE (09/09/2026). O cadastro pinta Blumenau com 6,00 / 6,50 / 7,40 m,
rotulados "AlertaBlu" desde 30/08/2026, sem bruto no repositório e com três nomes
(atenção/alerta/inundação) que não são os cinco do AlertaBlu. Um levantamento
externo relatou, da página "Nível do Rio" da própria Defesa Civil, uma escala de
CINCO estágios: normalidade 0–3 m · observação 3–4 · atenção 4–6 · alerta 6–8 ·
alerta máximo acima de 8 m. Se essa for a vigente, a tela pinta atenção dois
metros TARDE — o lado perigoso do erro.

O ambiente de desenvolvimento não alcança o host; a VPS alcança, e o
`coleta_alertablu.py` já lê `static/data/nivel_oficial.json`, que segundo
docs/fontes-tempo-real.md traz "faixas de condição" junto da série horária. Este
script baixa o mesmo JSON e imprime TUDO o que não é a série — a resposta está
em algum desses campos, com o nome que a fonte der. Não grava nada; decidir a
cota continua sendo trabalho de quem lê a saída.

Uso (na VPS, ou com um JSON salvo do navegador):
    python3 scripts/conferir_faixas_blumenau.py
    python3 scripts/conferir_faixas_blumenau.py --arquivo nivel_oficial.json
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

#: Chave da série horária — a única parte do JSON que NÃO interessa aqui.
SERIE = "niveis"

#: Nomes de campo que costumam carregar faixa de cota. A varredura é por
#: SUBSTRING, sem acento, para não depender de adivinhar o esquema da fonte.
PISTAS = re.compile(r"faixa|cota|nivel|limite|band|condi|estagio|alerta|atenc|observ|normal|emerg|maxim")


def sem_acento(texto: str) -> str:
    return (texto.lower().replace("ã", "a").replace("á", "a").replace("â", "a").replace("é", "e")
            .replace("ê", "e").replace("í", "i").replace("ó", "o").replace("ô", "o").replace("ú", "u")
            .replace("ç", "c"))


def sem_serie(dados: Any) -> dict[str, Any]:
    """O JSON inteiro menos a série, que vira só contagem e última leitura."""
    if not isinstance(dados, dict):
        return {"_raiz": dados}
    fora = {k: v for k, v in dados.items() if k != SERIE}
    serie = dados.get(SERIE)
    if isinstance(serie, list):
        fora[SERIE] = {"quantos": len(serie), "ultima": serie[-1] if serie else None}
    return fora


def candidatas_a_faixa(dados: Any, caminho: str = "") -> list[tuple[str, Any]]:
    """Todo número (ou texto com número) sob uma chave que cheira a faixa, fora da série."""
    achados: list[tuple[str, Any]] = []
    if isinstance(dados, dict):
        for k, v in dados.items():
            if k == SERIE:
                continue
            aqui = f"{caminho}.{k}" if caminho else str(k)
            if isinstance(v, (dict, list)):
                achados += candidatas_a_faixa(v, aqui)
            elif PISTAS.search(sem_acento(aqui)) and (
                isinstance(v, (int, float)) and not isinstance(v, bool)
                or isinstance(v, str) and re.search(r"\d", v)
            ):
                achados.append((aqui, v))
    elif isinstance(dados, list):
        for n, v in enumerate(dados):
            achados += candidatas_a_faixa(v, f"{caminho}[{n}]")
    return achados


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--arquivo", metavar="JSON", help="ler um nivel_oficial.json salvo, sem rede")
    args = ap.parse_args()

    if args.arquivo:
        dados = json.loads(Path(args.arquivo).read_text(encoding="utf-8"))
    else:
        from coleta_alertablu import URL, baixar  # noqa: PLC0415 — só com rede
        try:
            dados = baixar()
        except Exception as erro:  # rede, TLS, HTTP
            print(f"não deu para baixar {URL}: {erro}", file=sys.stderr)
            return 1

    print("=== tudo menos a série horária ===")
    print(json.dumps(sem_serie(dados), ensure_ascii=False, indent=2))
    print()
    print("=== candidatas a faixa (chave ~ faixa/cota/nível/estágio…) ===")
    achados = candidatas_a_faixa(dados)
    if not achados:
        print("nenhuma — a escala não está neste JSON; resta a página /d/nivel-do-rio no navegador.")
    for caminho, valor in achados:
        print(f"  {caminho} = {valor!r}")
    print()
    print("Nada foi gravado. Compare com cotas_divergencias de Blumenau em data/estacoes.json.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
