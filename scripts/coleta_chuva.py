#!/usr/bin/env python3
"""
Coleta a chuva acumulada publicada pela Defesa Civil de Itajaí.

Fonte: https://defesacivil.itajai.sc.gov.br/monitoramento/chuvas

Estrutura conferida contra o site no ar em 30/08/2026, pela sonda
`sonda_chuva.py` rodando na VPS — mesma aninhagem da página de níveis: o <h2>
mora dentro de um <header> e os valores são irmãos DESSE header.

    <li class="card point">
      <header><h2>DC-09 Ribeirão da Murta - Ponte da Rua Lidia Puel Peixer</h2></header>
      <div class="content"><ul class="current-telemetria">
        <li><span class="label">Chuva nos últimos 10 minutos: </span> 0,00 mm</li>
        <li><span class="label">Data e hora da medição: </span> 30/08/2026 18:10</li>
        <li><span class="label">Chuva acumulada 1h: </span> 0,40 mm</li>
        <li><span class="label">Chuva acumulada 12h: </span> 39,60 mm</li>
        <li><span class="label">Chuva acumulada 24h: </span> 39,60 mm</li>
        <li><span class="label">Chuva acumulada 48h: </span> 41,40 mm</li>
      </ul></div>
    </li>

DUAS COISAS QUE A FONTE **NÃO** DÁ, e que não serão inventadas aqui:

* **Não existe acumulado de 6 h.** As janelas publicadas são 10 min, 1 h, 12 h,
  24 h e 48 h. Estimar 6 h dividindo o de 12 h suporia chuva constante, que é
  justamente o que ela não é numa cheia — a metade final de um período de 12 h
  pode conter toda a chuva. Um número inventado com cara de medição é o pior
  resultado possível numa tela que gente usa para decidir sair de casa.
* **Não é radar.** Isto é pluviômetro: mede a chuva que caiu NAQUELE ponto.
  Radar estima intensidade sobre uma área e não vira milímetro acumulado
  confiável.

TRAVA DE COERÊNCIA
------------------
As janelas são encaixadas: os últimos 10 min estão dentro da última hora, que
está dentro das últimas 12 h, e assim por diante. Então o acumulado tem de ser
não-decrescente. A fonte publica série que viola isso — a estação Guarani, em
Brusque, registrava 0,20 mm nos últimos 10 minutos e 0,00 mm em 1 h, 12 h, 24 h
e 48 h no mesmo instante. Zero ali quase certamente significa "sem dado", não
"não choveu", e mostrar 0 mm na tela ao lado de uma estação vizinha com 39 mm
mandaria a pessoa exatamente para o lado errado.

Quando a sequência não fecha, a leitura vai marcada (`coerente: false`) com o
que exatamente não fecha, e o site mostra "dado inconsistente na fonte" em vez
de número.

Uso:
    python3 scripts/coleta_chuva.py             # baixa e mostra
    python3 scripts/coleta_chuva.py --json      # despeja o JSON
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone

try:
    from bs4 import BeautifulSoup
except ImportError:
    sys.exit("Instale a dependência: pip install beautifulsoup4")

from comum import USER_AGENT, classificar_estacao

URL = "https://defesacivil.itajai.sc.gov.br/monitoramento/chuvas"

#: Da janela mais curta para a mais longa. A ordem É a regra de coerência.
JANELAS = [
    ("min10", r"Chuva nos [úu]ltimos 10 minutos"),
    ("h1", r"Chuva acumulada 1h"),
    ("h12", r"Chuva acumulada 12h"),
    ("h24", r"Chuva acumulada 24h"),
    ("h48", r"Chuva acumulada 48h"),
]

RE_DATA = re.compile(
    r"Data e hora da medi[cç][aã]o:\s*(\d{2}/\d{2}/\d{4})\s+(\d{2}:\d{2})", re.I
)


def _mm(texto: str, padrao: str) -> float | None:
    """O valor em mm de uma janela, ou None quando a fonte não publicou."""
    m = re.search(padrao + r":?\s*([\d.,]+)\s*mm", texto, re.I)
    if not m:
        return None
    return float(m.group(1).replace(".", "").replace(",", "."))


def bloco_da_estacao(h2):
    """Sobe do <h2> até o <li> da estação — o título fica dentro de um <header>."""
    for candidato in (h2.find_parent("li"), h2.find_parent("article"),
                      h2.parent.parent if h2.parent else None, h2.parent):
        if candidato is not None:
            return candidato
    return h2


def incoerencias(mm: dict) -> list[str]:
    """
    O que não fecha nesta leitura.

    Janela curta não pode ter mais chuva que janela longa que a contém. Compara
    só pares em que os dois valores existem: janela ausente é ausência de dado,
    não zero.
    """
    problemas = []
    presentes = [(nome, mm[nome]) for nome, _ in JANELAS if mm.get(nome) is not None]
    for (nome_a, valor_a), (nome_b, valor_b) in zip(presentes, presentes[1:]):
        # Tolerância de 0,05 mm: a fonte publica com uma casa e o balde do
        # pluviômetro tem passo de 0,2 mm. Diferença menor que isso é
        # arredondamento, não contradição.
        if valor_a > valor_b + 0.05:
            problemas.append(f"{nome_a}={valor_a:g} mm > {nome_b}={valor_b:g} mm")
    return problemas


def parse(html: str) -> list[dict]:
    soup = BeautifulSoup(html, "html.parser")
    leituras: list[dict] = []
    vistos: set[str] = set()

    for h2 in soup.find_all("h2"):
        titulo = h2.get_text(" ", strip=True)
        if not titulo or titulo in vistos:
            continue

        texto = " ".join(bloco_da_estacao(h2).get_text(" ", strip=True).split())
        mm = {nome: _mm(texto, padrao) for nome, padrao in JANELAS}
        if all(v is None for v in mm.values()):
            continue  # cabeçalho da página, ou estação sem dado (Blumenau)
        vistos.add(titulo)

        m_data = RE_DATA.search(texto)
        medido_em = None
        if m_data:
            medido_em = datetime.strptime(
                f"{m_data.group(1)} {m_data.group(2)}", "%d/%m/%Y %H:%M"
            ).isoformat()

        rio, cidade = classificar_estacao(titulo)
        problemas = incoerencias(mm)
        leituras.append({
            "estacao": titulo,
            "rio": rio,
            "cidade": cidade,
            "mm": mm,
            "medido_em": medido_em,  # hora local (America/Sao_Paulo), sem fuso
            "coerente": not problemas,
            "incoerencias": problemas,
        })
    return leituras


def coletar() -> dict:
    from comum import baixar, espera_turno

    espera_turno()
    return {
        "fonte": URL,
        "coletado_em": datetime.now(timezone.utc).isoformat(),
        "chuva": parse(baixar(URL)),
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--json", action="store_true", help="despeja o JSON")
    ap.add_argument("--arquivo", help="analisa um HTML salvo, sem rede")
    args = ap.parse_args()

    if args.arquivo:
        dados = {"fonte": args.arquivo, "chuva": parse(open(args.arquivo, encoding="utf-8").read())}
    else:
        dados = coletar()

    if args.json:
        print(json.dumps(dados, ensure_ascii=False, indent=2))
        return 0

    chuva = dados["chuva"]
    print(f"{len(chuva)} estação(ões) com chuva publicada.\n")
    for c in sorted(chuva, key=lambda x: (str(x["cidade"]), x["estacao"])):
        mm = c["mm"]
        def v(nome):
            return "—" if mm.get(nome) is None else f"{mm[nome]:.1f}".replace(".", ",")
        print(f"  {c['cidade']} · {c['estacao']}")
        print(f"      1h {v('h1')} · 12h {v('h12')} · 24h {v('h24')} · 48h {v('h48')} mm"
              f"   (10 min: {v('min10')})")
        if not c["coerente"]:
            print(f"      ⚠ inconsistente na fonte: {'; '.join(c['incoerencias'])}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
