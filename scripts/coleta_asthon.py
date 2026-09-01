#!/usr/bin/env python3
"""Nível de Vidal Ramos pela API Asthon do Alto Vale.

`public.asthon.com.br` é a API que o portal da Defesa Civil de Rio do Sul usa.
De todas as estações dela, só UMA entra na tela por aqui: **Vidal Ramos**, régua
fluvial do próprio município, mesmo zero das cotas — uma das cidades sem nível
nenhum na tela. As demais são barragem (reservatório, escala do barramento),
altitude ou a cota de Rio do Sul copiada para outra régua; `analisar_asthon.py`
mostra por quê. Por isso este coletor entra por **lista fechada de station_id**,
nunca por nome, e só o que foi conferido.

Dois cuidados que impedem número certo respondendo pergunta errada:

* **Carimbo em UTC.** A Asthon publica `last_reading_at` com `Z` (UTC). O projeto
  grava `medido_em` em hora de Brasília SEM fuso — então a conversão é feita AQUI,
  na entrada, e em lugar nenhum mais. Ler o UTC como se fosse local jogaria a
  idade três horas fora, e a idade é o que diz se o número serve.
* **Sem cota ainda.** Vidal Ramos não tem cota de referência (atenção/alerta)
  levantada. O nível aparece na tela com a idade à vista, mas a faixa fica
  cinza, porque `estacoes.json` traz `cotas_m` vazio para a cidade. É o
  "mostrar, nunca disparar" pela via natural — nenhum aviso sai daqui.

Uso:
    python3 scripts/coleta_asthon.py            # imprime o que coletaria
"""

from __future__ import annotations

import sys
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from comum import USER_AGENT, nivel_plausivel

BASE = "https://public.asthon.com.br/public/"
CITY_ID = 4214805
#: O painel traz, por estação, `level_m` + `last_reading_at` — o que precisamos.
URL_PAINEL = f"{BASE}panel?city_id={CITY_ID}"

FUSO_BRASILIA = ZoneInfo("America/Sao_Paulo")

#: `station_id` -> (rio, id da cidade em estacoes.json). LISTA FECHADA: só a
#: régua conferida em analisar_asthon.py. Crescer aqui exige a mesma conferência
#: (barragem, altitude e cota copiada ficam de fora).
POR_ESTACAO = {
    "bd65df3e-a5e3-4760-a879-56df0fb90787": ("itajai-mirim", "vidal-ramos"),
}

#: Título da régua na tela, por cidade.
TITULO = {
    "vidal-ramos": "Vidal Ramos (Asthon)",
}


def de_utc_para_brasilia(iso_utc: str) -> str | None:
    """`2026-08-31T12:21:50.688Z` (UTC) -> `2026-08-31T09:21:50` (Brasília, sem fuso)."""
    try:
        dt = datetime.fromisoformat(iso_utc.replace("Z", "+00:00"))
    except ValueError:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(FUSO_BRASILIA).replace(tzinfo=None).strftime("%Y-%m-%dT%H:%M:%S")


def parse(dados) -> list[dict]:
    """Leituras de nível das estações conhecidas, do JSON do painel Asthon."""
    estacoes = dados.get("stations") if isinstance(dados, dict) else None
    if estacoes is None and isinstance(dados, list):
        estacoes = dados

    leituras = []
    for e in estacoes or []:
        if not isinstance(e, dict):
            continue
        alvo = POR_ESTACAO.get(e.get("station_id"))
        if not alvo:
            continue
        rio, cidade = alvo

        nivel = e.get("level_m")
        # `nivel_plausivel` recusa 0,0 (sensor parado) e o que passa da faixa de
        # rio da bacia — a mesma régua que a coleta usa em toda fonte.
        if not isinstance(nivel, (int, float)) or not nivel_plausivel(nivel):
            continue

        quando = e.get("last_reading_at")
        medido = de_utc_para_brasilia(quando) if isinstance(quando, str) else None
        # Sem carimbo confiável não dá para dizer a idade — e sem idade o número
        # não serve. Pula em vez de inventar "agora".
        if not medido:
            continue

        leituras.append({
            "estacao": TITULO.get(cidade, cidade),
            "rio": rio,
            "cidade": cidade,
            "nivel_m": round(float(nivel), 2),
            "medido_em": medido,
        })
    return leituras


def baixar(url: str = URL_PAINEL) -> dict:
    import requests

    r = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=20)
    r.raise_for_status()
    return r.json()


def coletar() -> list[dict]:
    return parse(baixar())


def main() -> int:
    try:
        leituras = coletar()
    except Exception as e:  # rede, HTTP, JSON inesperado
        print(f"ERRO ao coletar Asthon: {e}", file=sys.stderr)
        return 1
    for l in leituras:
        print(f"{l['nivel_m']:6.2f} m  {l['medido_em']}  {l['estacao']}  [{l['cidade']}]")
    if not leituras:
        print("Nenhuma estação conhecida trouxe nível — confira a URL do painel.",
              file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
