#!/usr/bin/env python3
"""
Coleta os níveis de rio publicados pela Defesa Civil de Itajaí e salva em JSON.

Fonte: https://defesacivil.itajai.sc.gov.br/monitoramento/nivel-rios
A página é HTML simples (sem JavaScript): cada estação é um <h2> seguido de
"Nível do Rio: X,XX m" e "Data e hora da medição: dd/mm/aaaa hh:mm".
Inclui também Brusque, Blumenau e Rio do Sul.

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
    import requests
    from bs4 import BeautifulSoup
except ImportError:
    sys.exit("Instale as dependências: pip install requests beautifulsoup4")

URL = "https://defesacivil.itajai.sc.gov.br/monitoramento/nivel-rios"
UA = "enchentes-vale-itajai/0.1 (+https://github.com/haohmarusc-glitch/enchentes-vale-itajai)"
RAIZ = Path(__file__).resolve().parent.parent
SAIDA = RAIZ / "data" / "tempo-real"

# Mapeia o título da estação -> (rio, cidade) do data/estacoes.json
MAPA = [
    (r"^DC-0[12]\b", "itajai-acu", "itajai"),
    (r"^DC-11\b", "itajai-acu", "ilhota"),
    (r"^DC-0[3456]\b", "itajai-mirim", "itajai"),
    (r"^DC-10\b", "itajai-mirim", "itajai"),
    (r"^DC-0[789]\b", "ribeirao", "itajai"),
    (r"^Brusque", "itajai-mirim", "brusque"),
    (r"^Blumenau", "itajai-acu", "blumenau"),
    (r"^Rio do Sul", "itajai-acu", "rio-do-sul"),
]

RE_NIVEL = re.compile(r"N[ií]vel do Rio:\s*([\d.,]+)\s*m", re.I)
RE_DATA = re.compile(r"Data e hora da medi[cç][aã]o:\s*(\d{2}/\d{2}/\d{4})\s+(\d{2}:\d{2})", re.I)


def classificar(titulo: str):
    for padrao, rio, cidade in MAPA:
        if re.search(padrao, titulo):
            return rio, cidade
    return None, None


def parse(html: str) -> list[dict]:
    soup = BeautifulSoup(html, "html.parser")
    leituras = []
    for h2 in soup.find_all("h2"):
        titulo = h2.get_text(" ", strip=True)
        if not titulo or titulo.startswith("Níveis dos Rios"):
            continue
        # Texto até o próximo h2
        bloco = []
        for el in h2.next_siblings:
            if getattr(el, "name", None) == "h2":
                break
            bloco.append(el.get_text(" ", strip=True) if hasattr(el, "get_text") else str(el))
        texto = " ".join(bloco)
        m_nivel = RE_NIVEL.search(texto)
        if not m_nivel:
            continue  # estação sem leitura (ex.: Blumenau às vezes vem vazio)
        m_data = RE_DATA.search(texto)
        rio, cidade = classificar(titulo)
        medido_em = None
        if m_data:
            medido_em = datetime.strptime(f"{m_data.group(1)} {m_data.group(2)}", "%d/%m/%Y %H:%M").isoformat()
        leituras.append({
            "estacao": titulo,
            "rio": rio,
            "cidade": cidade,
            "nivel_m": float(m_nivel.group(1).replace(".", "").replace(",", ".")),
            "medido_em": medido_em,  # horário local (America/Sao_Paulo), sem fuso
        })
    return leituras


def coletar() -> dict:
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
