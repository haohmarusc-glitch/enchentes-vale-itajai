#!/usr/bin/env python3
"""
Nível do rio em Blumenau pelo AlertaBlu — fonte de RESGATE.

A fonte primária de nível (coleta_itajai, página da Defesa Civil de Itajaí) publica
Blumenau vazio de forma intermitente. O AlertaBlu publica a série oficial de Blumenau
como JSON estático, independente daquela página. Serve para quando a primária falha.

parse() devolve leituras no MESMO formato de coleta_itajai.parse() — {estacao, rio,
cidade, nivel_m, medido_em} — para conviver na mesma lista de coleta_niveis.
"""
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

import os
import requests

CA_BLUMENAU = os.path.join(os.path.dirname(__file__), "certs", "blumenau.pem")

URL = "https://defesacivil.blumenau.sc.gov.br/static/data/nivel_oficial.json"
UA = "enchentes-vale-itajai/0.1 (+https://github.com/haohmarusc-glitch/enchentes-vale-itajai)"


def baixar(url: str = URL) -> dict:
    r = requests.get(url, headers={"User-Agent": UA}, timeout=30, verify=CA_BLUMENAU)
    r.raise_for_status()
    return r.json()


def parse(dados: dict) -> list[dict]:
    """A última leitura da série horária do AlertaBlu, como uma leitura de nível."""
    niveis = (dados or {}).get("niveis") or []
    if not niveis:
        return []
    ult = niveis[-1]
    nivel = ult.get("nivel")
    if nivel is None:
        return []
    # horaLeitura vem como ISO (ex.: 2026-09-01T12:00:00Z); normaliza para dd/mm/aaaa hh:mm
    quando = ult.get("horaLeitura")
    medido_em = quando
    try:
        dt = datetime.fromisoformat(str(quando).replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        medido_em = dt.astimezone(ZoneInfo("America/Sao_Paulo")).strftime("%Y-%m-%dT%H:%M:%S")
    except (ValueError, TypeError):
        pass
    return [{
        "estacao": "Blumenau (AlertaBlu)",
        "rio": "itajai-acu",
        "cidade": "blumenau",
        "nivel_m": float(nivel),
        "medido_em": medido_em,
        "resgate_de": "Blumenau",
    }]


if __name__ == "__main__":
    ls = parse(baixar())
    for l in ls:
        print(f"{l['nivel_m']} m  {l['medido_em']}  {l['estacao']}")
    if not ls:
        print("sem leitura no AlertaBlu (conferir estrutura de nivel_oficial.json)")
