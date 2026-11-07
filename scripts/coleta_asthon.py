#!/usr/bin/env python3
"""Nível de Vidal Ramos e de Rio do Sul pela API Asthon do Alto Vale.

`public.asthon.com.br` é a API que o portal da Defesa Civil de Rio do Sul usa.
De todas as estações dela, só DUAS entram na tela por aqui, por **lista fechada
de station_id**, nunca por nome, e só o que foi conferido:

* **Vidal Ramos** — régua fluvial do próprio município, uma das cidades sem
  nível nenhum na tela até 31/08/2026. Sem cota ainda: mostra, não pinta.
* **Rio do Sul, Ponte Dom Tito Buss** (desde 09/09/2026) — é a régua de
  referência da cidade na API (`reference_station_id`) e a DONA das cotas
  4,50 / 5,50 / 6,50 que `estacoes.json` guarda (`band_thresholds`). Até então
  a leitura de Rio do Sul vinha da "Estação MKS", pela página da Defesa Civil de
  Itajaí, e o site pintava a MKS com a cota da Tito Buss — o par nunca foi
  provado (`conferir_par_regua.py`), e em 09/09/2026 foi DESMENTIDO: no mesmo
  instante, MKS 4,64 m e Tito Buss (DCSC) 4,63 m contra Tito Buss (Asthon)
  4,46 m. Zeros diferentes, ~0,17 m; com atenção em 4,50 m, o site pintava
  amarelo enquanto o município mostrava NORMAL na régua dona das cotas. Cadência
  de 5 min contra ~1 h da MKS. A MKS saiu da coleta (`comum._FALLBACK`,
  `saude_coleta.ESTACOES_APOSENTADAS`), e NÃO virou resgate: resgate é para a
  MESMA régua por outro canal, e esta é outra régua.

As demais estações da API são barragem (reservatório, escala do barramento),
altitude ou a cota de Rio do Sul copiada para outra régua; `analisar_asthon.py`
mostra por quê.

Desde 07/11/2026 o nível das duas vem do **histórico da própria estação**
(`station-history`, mesmo station_id), não do painel: o painel publicou um valor
parado com carimbo de agora por três dias (ver `baixar_historico`).

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
from datetime import datetime, timedelta, timezone
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
    # `reference_station_id` da cidade 4214805 na própria API; é a régua cujas
    # `band_thresholds` são as cotas de Rio do Sul em estacoes.json.
    "f6360951-219f-4859-935f-b2e2d13962f1": ("itajai-acu", "rio-do-sul"),
}

#: Título da régua na tela, por cidade. É a chave de ligação com
#: `estacoes_tempo_real` em estacoes.json e com o estado do vigia — não mudar
#: sem migrar os dois.
TITULO = {
    "vidal-ramos": "Vidal Ramos (Asthon)",
    "rio-do-sul": "Rio do Sul, Ponte Dom Tito Buss (Asthon)",
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


# --- Histórico da estação: a hora REAL da medição (07/11/2026) ----------------
#
# O painel mentiu a idade. De 04/11 08:26 a 07/11 12:16 (Brasília) a Ponte Dom
# Tito Buss (f6360951) não mediu nada — o `station-history` mostra a lacuna —,
# mas o painel seguiu publicando o último valor, 3,27 m, com `last_reading_at`
# de agora. Em 05/11, com o rio a ~7,5 m na mesma ponte (espelho estadual
# d2f60af1, `owner_id: DCSC`), o site mostrou Rio do Sul fresco e NORMAL. Em
# 07/11 a estação voltou a medir, mas o painel a tirou da lista e pôs no lugar
# o espelho estadual — outra régua (~0,2 m de zero), que não é a das cotas.
#
# Por isso o nível destas duas réguas vem do histórico, pelo MESMO station_id:
# cada ponto traz o carimbo da medição. Sem ponto nas últimas horas, não há
# leitura — e a tela fica cinza, que é o certo para estação parada. O painel
# não é mais lido para o nível delas.

URL_HISTORICO = f"{BASE}station-history"
#: Janela pedida ao histórico. Leitura com mais de 3 h já é "velha" na tela.
JANELA_HISTORICO_H = 3
#: O histórico destas réguas declara o nível no zero da régua. Outro datum
#: (altitude, absoluto) seria outra grandeza: não entra.
DATUM_ESPERADO = "gauge_zero"


def ultimo_do_historico(corpo, codigo: str) -> dict | None:
    """O ponto mais recente do `station-history`, com o carimbo da medição.

    Devolve `{"nivel_m", "medido_em"}` (Brasília, sem fuso) ou None quando a
    resposta é de outra estação, tem outro datum, não tem ponto válido ou o
    último ponto é implausível (0,0 de sensor parado, altitude).
    """
    if not isinstance(corpo, dict):
        return None
    if corpo.get("station_id") not in (None, codigo):
        return None
    if corpo.get("level_datum") != DATUM_ESPERADO:
        return None
    pontos = []
    for p in corpo.get("level") or []:
        if not isinstance(p, dict) or not isinstance(p.get("timestamp"), str):
            continue
        try:
            quando = datetime.fromisoformat(p["timestamp"].replace("Z", "+00:00"))
        except ValueError:
            continue
        if quando.tzinfo is None:
            continue
        pontos.append((quando, p.get("value")))
    if not pontos:
        return None
    quando, valor = max(pontos, key=lambda x: x[0])
    # O último ponto manda: se ele é implausível, a régua está com problema
    # agora, e um ponto anterior apresentado como atual mentiria a idade.
    if not isinstance(valor, (int, float)) or isinstance(valor, bool) or not nivel_plausivel(valor):
        return None
    return {
        "nivel_m": round(float(valor), 2),
        "medido_em": quando.astimezone(FUSO_BRASILIA).replace(tzinfo=None).strftime("%Y-%m-%dT%H:%M:%S"),
    }


def baixar_historico(codigo: str, agora: datetime | None = None) -> dict:
    import requests

    from comum import espera_turno

    fim = agora or datetime.now(timezone.utc)
    ini = fim - timedelta(hours=JANELA_HISTORICO_H)
    espera_turno()
    r = requests.get(
        URL_HISTORICO,
        params={
            "station_id": codigo,
            "start": ini.strftime("%Y-%m-%dT%H:%M:%S.000Z"),
            "end": fim.strftime("%Y-%m-%dT%H:%M:%S.000Z"),
            "fields": "level",
            "resolution": "raw",
        },
        headers={"User-Agent": USER_AGENT},
        timeout=20,
    )
    r.raise_for_status()
    return r.json()


def coletar(baixar_hist=baixar_historico) -> list[dict]:
    """Uma leitura por régua da lista fechada, do histórico da própria estação."""
    leituras = []
    for codigo, (rio, cidade) in POR_ESTACAO.items():
        try:
            ultimo = ultimo_do_historico(baixar_hist(codigo), codigo)
        except Exception as e:  # rede, HTTP, JSON: esta régua fica sem leitura, a outra segue
            print(f"aviso: histórico Asthon de {TITULO[cidade]} não veio ({e}).", file=sys.stderr)
            continue
        if ultimo is None:
            print(f"aviso: {TITULO[cidade]} (station_id={codigo}) sem medição válida nas últimas "
                  f"{JANELA_HISTORICO_H} h no histórico da Asthon; fica sem leitura, sem trocar de régua.",
                  file=sys.stderr)
            continue
        leituras.append({"estacao": TITULO.get(cidade, cidade), "rio": rio, "cidade": cidade, **ultimo})
    return leituras


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
