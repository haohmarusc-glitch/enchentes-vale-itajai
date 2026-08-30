#!/usr/bin/env python3
"""
Coleta os níveis de rio publicados pela Defesa Civil de Itajaí e salva em JSON.

Fonte: https://defesacivil.itajai.sc.gov.br/monitoramento/nivel-rios
Inclui também Brusque, Blumenau e Rio do Sul.

Estrutura da página, conferida contra o site no ar:

    <li class="card point ...">
      <header><h2>DC-01 Rio Itajaí-Açu - ICMBio/CEPSUL</h2></header>
      <div class="content">
        <ul class="current-telemetria">
          <li><span class="label">Nível do Rio: </span> 1,39 m</li>
          <li><span class="label">Data e hora da medição: </span> 30/08/2026 15:51</li>
        </ul>
      </div>
    </li>

O título está dentro de um <header>, e os valores são irmãos DESSE header —
não do <h2>. Por isso o bloco de cada estação é procurado subindo do <h2> até
o <li> que o contém, e não caminhando pelos irmãos do título.

Uso:
    python3 scripts/coleta_itajai.py            # imprime e salva em data/tempo-real/
    python3 scripts/coleta_itajai.py --no-save  # só imprime

Idempotente: grava um arquivo por execução (timestamp) e atualiza
data/tempo-real/ultimo.json.
"""
import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

try:
    from bs4 import BeautifulSoup
except ImportError:
    sys.exit("Instale a dependência: pip install beautifulsoup4")

# `requests` entra só no caminho que baixa a página: analisar HTML salvo não
# usa rede, e exigir a biblioteca aqui impediria de importar este módulo para
# reaproveitar o analisador.

URL = "https://defesacivil.itajai.sc.gov.br/monitoramento/nivel-rios"
UA = "enchentes-vale-itajai/0.1 (+https://github.com/haohmarusc-glitch/enchentes-vale-itajai)"
RAIZ = Path(__file__).resolve().parent.parent
SAIDA = RAIZ / "data" / "tempo-real"

from comum import classificar_estacao

RE_NIVEL = re.compile(r"N[ií]vel do Rio:\s*([\d.,]+)\s*m", re.I)
RE_DATA = re.compile(r"Data e hora da medi[cç][aã]o:\s*(\d{2}/\d{2}/\d{4})\s+(\d{2}:\d{2})", re.I)


def bloco_da_estacao(h2):
    """
    O elemento que contém o título E as leituras.

    Sobe do <h2> até o <li> da estação. Se a página mudar e esse <li> deixar de
    existir, cai para o avô e depois para o pai — o suficiente para atravessar
    o <header> que envolve o título.
    """
    for candidato in (h2.find_parent("li"), h2.find_parent("article"),
                      h2.parent.parent if h2.parent else None, h2.parent):
        if candidato is not None:
            return candidato
    return h2


def parse(html: str) -> list[dict]:
    soup = BeautifulSoup(html, "html.parser")
    leituras = []
    vistos = set()
    for h2 in soup.find_all("h2"):
        titulo = h2.get_text(" ", strip=True)
        if not titulo or titulo.lower().startswith("níveis dos rios"):
            continue

        bloco = bloco_da_estacao(h2)
        texto = " ".join(bloco.get_text(" ", strip=True).split())
        m_nivel = RE_NIVEL.search(texto)
        if not m_nivel:
            continue  # estação sem leitura (ex.: Blumenau às vezes vem vazio)
        if titulo in vistos:
            continue  # o mesmo <h2> alcançado por dois caminhos
        vistos.add(titulo)

        m_data = RE_DATA.search(texto)
        rio, cidade = classificar_estacao(titulo)
        medido_em = None
        if m_data:
            medido_em = datetime.strptime(
                f"{m_data.group(1)} {m_data.group(2)}", "%d/%m/%Y %H:%M"
            ).isoformat()
        leituras.append({
            "estacao": titulo,
            "rio": rio,
            "cidade": cidade,
            "nivel_m": float(m_nivel.group(1).replace(".", "").replace(",", ".")),
            "medido_em": medido_em,  # horário local (America/Sao_Paulo), sem fuso
        })
    return leituras


def coletar() -> dict:
    import requests

    r = requests.get(URL, headers={"User-Agent": UA}, timeout=30)
    r.raise_for_status()
    return {
        "fonte": URL,
        "coletado_em": datetime.now(timezone.utc).isoformat(),
        "leituras": parse(r.text),
    }


def salvar(dados: dict) -> Path:
    SAIDA.mkdir(parents=True, exist_ok=True)
    carimbo = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    arq = SAIDA / f"itajai_{carimbo}.json"
    arq.write_text(json.dumps(dados, ensure_ascii=False, indent=2), encoding="utf-8")
    (SAIDA / "ultimo.json").write_text(json.dumps(dados, ensure_ascii=False, indent=2), encoding="utf-8")
    return arq


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-save", action="store_true")
    args = ap.parse_args()
    dados = coletar()
    for l in dados["leituras"]:
        print(f"{l['nivel_m']:6.2f} m  {l['medido_em'] or '   -   '}  {l['estacao']}")
    if not dados["leituras"]:
        print("AVISO: nenhuma leitura encontrada — a estrutura da página pode ter mudado.", file=sys.stderr)
    if not args.no_save:
        print("salvo em", salvar(dados))
