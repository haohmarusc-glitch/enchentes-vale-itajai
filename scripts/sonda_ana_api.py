#!/usr/bin/env python3
"""Descobre o FORMATO de duas rotas da API da ANA, sem gravar dado no projeto.

POR QUE UMA SONDA, E NÃO UM COLETOR (08/09/2026)
No mesmo dia em que o acesso saiu, a `HidroSerieCotas` ensinou que o formato da
resposta é o que decide tudo: uma consulta devolve VÁRIAS linhas para o mesmo
mês, e a de rótulo melhor (`nivelconsistencia: 2`) apagava uma cheia de 4 m.
Escrever coletor contra formato suposto seria repetir isso de olhos fechados —
ver `docs/ANA-API-2026-09-08.md`.

Esta sonda chama, mede e IMPRIME. Não escreve em `data/estacoes.json` nem em
`data/enchentes.json`. O único arquivo que ela grava é o bruto do inventário,
em `data/brutos/`, porque bruto é evidência e o projeto tem um guarda que cobra
evidência citada (`valida_brutos_citados`).

DUAS PERGUNTAS, uma execução:

1. `HidroInventarioEstacoes` — quais estações da ANA existem em SC, e o que a
   API diz de cada uma? É o que fecha a pendência do inventário e o que responde
   se a 83800002 e as outras estão nesta rede.

2. `HidroinfoanaSerieTelemetricaAdotada` — a série telemétrica tem NÍVEL AO VIVO
   para estações da bacia? Doze cidades estão com o pino cinza no mapa, e esse é
   o item que mais escurece a tela. Aqui a sonda só olha; quem decide se vira
   fonte é a conferência de régua, que é outra conversa.

   ❌ RESPONDIDO EM 08/09/2026, E É NÃO. Onze chamadas — cinco estações, quatro
   variantes de data/range, e as rotas Detalhada/v1 e Adotada/v2 — todas com
   "Não houve retorno de registros" e items vazio. E o INVENTÁRIO DA MESMA API
   discorda: para a 83900000 (BRUSQUE PCD) ele afirma telemétrica, operando, e
   telemetria aberta desde 05/1996. A rota `OAUthPermissoes/v1`, que diria se a
   credencial cobre telemetria, devolve HTTP 400.
   Manter esta parte da sonda tem valor: ela é o teste que se refaz em UMA
   execução quando a ANA responder ao ofício. O que NÃO se faz é continuar
   chutando parâmetro — ver docs/ANA-API-2026-09-08.md.

   ✅ REVISTO EM 09/09/2026, E É SIM — NO PASSADO, PARA AS QUATRO ATIVAS. A
   EPAGRI/CIRAM explicou o vazio: as cinco candidatas de 08/09 estavam todas
   DESATIVADAS. Com `--data 2023-11-17 --intervalo DIAS_7`, as quatro que
   seguem ativas (83029900, 83050000, 83250000, 83892990) devolveram 672
   leituras cada — uma a cada 15 min, 7 dias TERMINANDO na data pedida —, com
   `Cota_Adotada` em CENTÍMETROS e muitos `null`. A Saltinho (83050000) foi de
   6,34 m a 10,32 m e ainda subia no último registro: a janela acabou ANTES do
   pico. Por isso o resumo por estação avisa quando o máximo é a última leitura
   e sugere a janela seguinte. NADA disso vira registro em enchentes.json por
   conta própria — a régua da série ainda precisa ser conferida contra a régua
   da cidade (Taió: a 83050000 fica a 0,56 km do pino; a SDC republica a mesma
   rede, segundo a EPAGRI — hipótese a testar comparando uma leitura ao vivo).

Uso:
    python3 scripts/sonda_ana_api.py
    python3 scripts/sonda_ana_api.py --uf SC --estacoes 83900000,83870001
    python3 scripts/sonda_ana_api.py --sem-inventario \
        --estacoes 83029900,83050000,83250000,83892990 \
        --data 2023-11-24 --intervalo DIAS_7 --gravar

⚠️ NÃO RODA DESTE AMBIENTE: `*.ana.gov.br` é bloqueado no proxy (403 no
CONNECT). Rode na VPS, com o `.env` preenchido por `scripts/configurar_ana.sh`.

"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import date

try:
    import requests
except ImportError:  # pragma: no cover - ambiente sem dependências
    print("Falta a dependência: pip install -r scripts/requirements.txt", file=sys.stderr)
    raise SystemExit(2)

from ana_hidroweb import autentica, base_url
from comum import DADOS, USER_AGENT, carrega_env, espera_turno

ROTA_INVENTARIO = "/EstacoesTelemetricas/HidroInventarioEstacoes/v1"
ROTA_TELEMETRIA = "/EstacoesTelemetricas/HidroinfoanaSerieTelemetricaAdotada/v1"

#: Candidatas a nível ao vivo, escolhidas por terem escala ABERTA no nosso
#: cadastro. Não são "as réguas das cidades" — a conferência de régua é outra
#: etapa, e confundir as duas é como o Salseiro quase entrou em Vidal Ramos.
CANDIDATAS = ["83900000", "83870001", "83520000", "83840000", "83800002"]

#: Quantas chaves de exemplo imprimir por item. O objetivo é DESENHAR o
#: coletor, não ler o inventário inteiro na tela.
AMOSTRA = 3


def _pede(sessao: requests.Session, token: str, rota: str, params: dict) -> dict:
    espera_turno()
    r = sessao.get(f"{base_url()}{rota}", headers={"Authorization": f"Bearer {token}"},
                   params=params, timeout=120)
    if r.status_code != 200:
        return {"_erro": f"HTTP {r.status_code}", "_corpo": r.text[:300]}
    return r.json()


def _resumo(corpo: dict) -> tuple[str, list]:
    if "_erro" in corpo:
        return corpo["_erro"] + " — " + corpo.get("_corpo", ""), []
    itens = corpo.get("items")
    if not isinstance(itens, list):
        return f"resposta sem lista 'items' (chaves: {list(corpo)})", []
    return f"{corpo.get('message')!r} — {len(itens)} item(ns)", itens


def _grava_bruto(nome: str, corpo: dict) -> str:
    """Grava a resposta crua em data/brutos/ e devolve o caminho relativo.

    É o único lugar onde a sonda escreve. Bruto é evidência: o projeto tem um
    guarda que cobra a existência de todo bruto citado (`valida_brutos_citados`).
    """
    destino = DADOS / "brutos" / nome
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_text(json.dumps(corpo, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return f"{destino.relative_to(DADOS.parent)} ({destino.stat().st_size // 1024} KB)"


def _cota_m(item: dict) -> float | None:
    """`Cota_Adotada` vem em CENTÍMETROS, como string ("1032.00"), ou `null`."""
    bruto = item.get("Cota_Adotada")
    if bruto in (None, ""):
        return None
    try:
        return round(float(bruto) / 100, 2)
    except (TypeError, ValueError):
        return None


def resumo_cotas(itens: list) -> dict:
    """Resume a série telemétrica de UMA estação sem interpretar além do que há.

    Devolve `n` (linhas), `n_cota` (com cota), `primeira`/`ultima`/`maxima`/
    `minima` como (Data_Hora_Medicao, metros) ou None, e `pico_pode_estar_depois`
    — verdadeiro quando a MAIOR cota é a ÚLTIMA leitura com valor: a janela de
    7 dias termina na data pedida, e um rio que ainda sobe no último registro
    tem o pico fora dela. Esse máximo é piso, não pico.
    """
    com_cota = [(it.get("Data_Hora_Medicao"), _cota_m(it)) for it in itens]
    com_cota = [(q, c) for q, c in com_cota if c is not None]
    resumo = {"n": len(itens), "n_cota": len(com_cota), "primeira": None, "ultima": None,
              "maxima": None, "minima": None, "pico_pode_estar_depois": False}
    if not com_cota:
        return resumo
    resumo["primeira"] = com_cota[0]
    resumo["ultima"] = com_cota[-1]
    resumo["maxima"] = max(com_cota, key=lambda qc: qc[1])
    resumo["minima"] = min(com_cota, key=lambda qc: qc[1])
    resumo["pico_pode_estar_depois"] = resumo["maxima"][1] == resumo["ultima"][1]
    return resumo


def _imprime_resumo_cotas(resumo: dict, data: str | None, intervalo: str) -> None:
    n, n_cota = resumo["n"], resumo["n_cota"]
    print(f"      cotas: {n_cota} de {n} linhas têm Cota_Adotada"
          + (f" ({n - n_cota} null)" if n_cota < n else ""))
    if not n_cota:
        print("      ⚠️ nenhuma cota na janela — a estação pode não ter transmitido nível "
              "neste período; não conclua que não existe série.")
        return
    for rotulo in ("primeira", "ultima", "maxima", "minima"):
        quando, metros = resumo[rotulo]
        print(f"      {rotulo:8s}: {metros:6.2f} m em {quando}")
    if resumo["pico_pode_estar_depois"]:
        print("      ⚠️ a MAIOR cota é a ÚLTIMA leitura: o rio ainda subia quando a janela "
              f"({intervalo}, terminando em {data or 'hoje'}) acabou. Esse valor é PISO, não "
              "pico. Repita com --data uma janela adiante antes de citar qualquer máximo.")


def sonda_inventario(sessao, token, uf: str) -> list:
    print(f"\n{'=' * 70}\n1. INVENTÁRIO — Unidade Federativa = {uf}\n{'=' * 70}")
    corpo = _pede(sessao, token, ROTA_INVENTARIO, {"Unidade Federativa": uf})
    linha, itens = _resumo(corpo)
    print(f"   {linha}")
    if not itens:
        return []

    print(f"\n   CAMPOS de um item ({len(itens[0])}):")
    for k, v in itens[0].items():
        print(f"      {k} = {v!r}")

    print(f"\n   AMOSTRA de {min(AMOSTRA, len(itens))}:")
    for it in itens[:AMOSTRA]:
        print(f"      {json.dumps(it, ensure_ascii=False)[:200]}")

    onde = _grava_bruto(f"ana-inventario-api-{date.today().isoformat()}.json", corpo)
    print(f"\n   bruto gravado em {onde} — COMMITAR: é o que fecha a pendência do "
          "ana-inventario-2026-09-07.json (BRUTOS_PENDENTES do validador), citado por "
          "cinco blocos do estacoes.json que hoje apontam para um arquivo que não existe.")
    return itens


def sonda_telemetria(sessao, token, codigos: list[str], data: str | None = None,
                     intervalo: str = "HORA_24", gravar: bool = False) -> None:
    """
    `data` e `intervalo` entraram em 09/09/2026: as cinco estações testadas em
    08/09 estavam todas DESATIVADAS (EPAGRI/CIRAM, resposta ao C5), e 'vazio' era
    a resposta certa. As quatro ativas são 83029900, 83050000, 83250000 e
    83892990 — e um evento passado (--data 2023-11-17 --intervalo DIAS_7) é o
    teste que diz se a série telemétrica histórica existe.
    """
    print(f"\n{'=' * 70}\n2. SÉRIE TELEMÉTRICA — {data or 'hoje'}, {intervalo}\n{'=' * 70}")
    for codigo in codigos:
        corpo = _pede(sessao, token, ROTA_TELEMETRIA, {
            "Código da Estação": codigo,
            "Tipo Filtro Data": "DATA_LEITURA",
            "Data de Busca (yyyy-MM-dd)": data or date.today().isoformat(),
            "Range Intervalo de busca": intervalo,
        })
        linha, itens = _resumo(corpo)
        print(f"\n   {codigo}: {linha}")
        if not itens:
            continue
        print(f"      CAMPOS ({len(itens[0])}): {list(itens[0])}")
        print(f"      primeiro: {json.dumps(itens[0], ensure_ascii=False)[:260]}")
        print(f"      ultimo:   {json.dumps(itens[-1], ensure_ascii=False)[:260]}")
        _imprime_resumo_cotas(resumo_cotas(itens), data, intervalo)
        if gravar:
            onde = _grava_bruto(
                f"ana-telemetria-{codigo}-{data or date.today().isoformat()}-{intervalo}.json",
                corpo)
            print(f"      bruto gravado em {onde}")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--uf", default="SC")
    ap.add_argument("--estacoes", default=",".join(CANDIDATAS),
                    help="códigos separados por vírgula")
    ap.add_argument("--data", default=None, help="Data de Busca (AAAA-MM-DD); padrão hoje")
    ap.add_argument("--intervalo", default="HORA_24",
                    help="Range Intervalo de busca: HORA_24, DIAS_7 … (o que a spec listar)")
    ap.add_argument("--sem-inventario", action="store_true",
                    help="pula o inventário (5 MB por chamada) quando só a série interessa")
    ap.add_argument("--gravar", action="store_true",
                    help="grava a série telemétrica crua em data/brutos/ana-telemetria-<código>-"
                         "<data>-<intervalo>.json — é o bruto que um registro futuro citaria")
    args = ap.parse_args()

    carrega_env()
    sessao = requests.Session()
    sessao.headers["User-Agent"] = USER_AGENT
    try:
        token = autentica(sessao)
    except RuntimeError as e:
        print(f"ERRO: {e}", file=sys.stderr)
        return 1
    print("Autenticado na API da ANA.")

    if not args.sem_inventario:
        sonda_inventario(sessao, token, args.uf)
    sonda_telemetria(sessao, token, [c.strip() for c in args.estacoes.split(",") if c.strip()],
                     args.data, args.intervalo, gravar=args.gravar)

    print(f"\n{'=' * 70}\nSonda terminada. Nada foi gravado em data/estacoes.json "
          "nem em data/enchentes.json.\n" + "=" * 70)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
