#!/usr/bin/env python3
"""Baixa a série histórica da rede estadual (DCSC) pela query GraphQL `historic`.

É a metade que faltava do par: este script **busca** as janelas e grava a resposta CRUA;
o `consolidar_historico_dcsc.py` **interpreta** (sentinelas, picos de sensor, cristas) e
escreve `data/series/dcsc/<CODIGO>.csv`. Um só lugar interpreta o dado — de propósito.
Por isso o formato de saída aqui é exatamente o que o consolidador já lê:

    {"variables": {"stationCode": "...", "startDate": "...Z", "endDate": "...Z", ...},
     "coletado_em_utc": "...",
     "resposta": {"data": {"historic": {"items": [...], "totalCount": n}}}}

DE ONDE VEIO (13/09/2026). Levantamento do Jefferson a partir do bundle do próprio site,
registrado em `docs/API-DEFESA-CIVIL-SC.md`. O que este script assume, e que foi MEDIDO lá:

  * O servidor recusa qualquer `operationName` que não seja um dos quatro do site, com
    `{"errors":[{"message":"Operação bloqueada."}]}`. Os CAMPOS dentro da query são livres;
    o nome da operação e o `client` não.
  * **Janela por requisição:** ~70 dias passa, 90 é recusado → `JANELA_MAX_DIAS = 60`.
  * **Profundidade:** `startDate` só volta ~89 dias. Além disso tudo vira "Operação bloqueada",
    qualquer que seja o tamanho da janela → `PROFUNDIDADE_MAX_DIAS = 88`.
  * Rajada é bloqueada → 1 s entre chamadas.

CONSEQUÊNCIA QUE NÃO PODE SER ESQUECIDA: a API é uma **janela móvel de 90 dias**, não um
arquivo histórico. 1983, 1984, 2008, 2011 e 2023 não estão aqui — continuam vindo da
ANA/Hidroweb, do CEOPS/FURB e do ArcGIS da Prefeitura de Itajaí. O jeito de ter série longa
é rodar isto em cron e ACUMULAR; por isso a gravação é idempotente e nunca reescreve janela
já baixada.

FUSO. O `ts` que volta não tem fuso e é hora de BRASÍLIA — provado duas vezes, ver o cabeçalho
do `consolidar_historico_dcsc.py`. As datas ENVIADAS (`startDate`/`endDate`) são UTC com "Z".
São coisas diferentes: pede-se em UTC e recebe-se em Brasília. Este script não converte nada;
grava a resposta como veio.

ACUMULAR (09/10/2026). `--acumular` é o modo do cron (`.github/workflows/acumular-historico-dcsc.yml`):
semanas FECHADAS, de segunda 00:00 UTC a segunda 00:00 UTC, inteiras dentro do alcance e terminadas há mais
de um dia. Como a semana é fixa no calendário, o nome do arquivo é o mesmo em toda execução, e a que já está no
acervo (`--ja-baixadas`, a lista do branch `historico-dcsc`) não é pedida de novo. Grava `.json.gz` (13 KB por
estação-semana, contra 260 KB), que o consolidador também lê. Semana vazia NÃO vira arquivo (a próxima
execução tenta de novo, enquanto estiver no alcance), e item de outra estação reprova a semana inteira.

Uso:
    python3 scripts/baixar_historico_dcsc.py DCSC-00006 DCSC-00013 --dias 88 --intervalo MIN_10
    python3 scripts/baixar_historico_dcsc.py --cadeia --acumular --ja-baixadas lista.txt --destino novas/
    python3 scripts/baixar_historico_dcsc.py --cadeia            # as estações da CADEIA do Açu/Mirim
    python3 scripts/consolidar_historico_dcsc.py data/series/dcsc-baixado
"""

from __future__ import annotations

import argparse
import gzip
import json
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from comum import DADOS  # noqa: E402

URL = "https://monitoramento.defesacivil.sc.gov.br/graphql"
CLIENT = "secretaria-de-defesa-civil"
UA = "enchentes-vale-itajai (projeto comunitario de dados de enchentes)"

JANELA_MAX_DIAS = 60      # ~70 passa, 90 é recusado (medido)
PROFUNDIDADE_MAX_DIAS = 88  # startDate não volta além de ~89 dias (medido)
PAUSA_ENTRE_CHAMADAS_S = 1.0
TIMEOUT_S = 60

INTERVALOS = ("MIN_5", "MIN_10", "MIN_15", "MIN_30", "HOUR_1", "HOUR_3", "HOUR_6",
              "HOUR_12", "HOUR_24", "HOUR_48", "HOUR_72", "HOUR_96", "HOUR_168")

DESTINO_PADRAO = DADOS / "series" / "dcsc-baixado"

QUERY = """query Historic($stationCode: String!, $startDate: String!, $endDate: String!, $interval: QueryInterval) {
  historic(system: Qualle_Hidrometeorologia, client: "%s",
           stationCode: $stationCode, startDate: $startDate, endDate: $endDate,
           interval: $interval, opts: { ordenacao: ASC })
}""" % CLIENT


class Bloqueado(RuntimeError):
    """A API respondeu `errors` — quase sempre janela fora dos ~89 dias, ou rajada.

    Separado de erro de rede de propósito: insistir numa janela fora do alcance nunca
    funciona, e gastar quatro tentativas nela atrasa as estações seguintes.
    """


def iso_utc(dt: datetime) -> str:
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z")


def nome_da_janela(inicio: datetime, fim: datetime) -> str:
    """`20231101T000000_20231115T000000.json` — o mesmo nome das janelas baixadas no PC."""
    return f"{inicio.strftime('%Y%m%dT%H%M%S')}_{fim.strftime('%Y%m%dT%H%M%S')}.json"


def janelas(inicio: datetime, fim: datetime,
            maximo_dias: int = JANELA_MAX_DIAS) -> list[tuple[datetime, datetime]]:
    """Quebra o período em pedaços contíguos de no máximo `maximo_dias`, sem buraco nem sobra."""
    if fim <= inicio:
        return []
    saida = []
    cur = inicio
    while cur < fim:
        ate = min(cur + timedelta(days=maximo_dias), fim)
        saida.append((cur, ate))
        cur = ate
    return saida


def limitar_profundidade(inicio: datetime, agora: datetime,
                         maximo_dias: int = PROFUNDIDADE_MAX_DIAS) -> tuple[datetime, bool]:
    """Puxa `inicio` para dentro dos ~89 dias que a API responde. Devolve (inicio, cortou)."""
    limite = agora - timedelta(days=maximo_dias)
    if inicio < limite:
        return limite, True
    return inicio, False


def _transporte_requests(payload: dict) -> dict:
    import requests

    r = requests.post(URL, json=payload, headers={"User-Agent": UA}, timeout=TIMEOUT_S)
    r.raise_for_status()
    return r.json()


def pedir(codigo: str, inicio: datetime, fim: datetime, intervalo: str,
          transporte=None, tentativas: int = 2, dormir=time.sleep) -> tuple[dict, dict]:
    """Faz uma janela. Devolve (variaveis, resposta crua). Levanta `Bloqueado` se a API recusar.

    Duas tentativas, não quatro: "Operação bloqueada." também é a resposta permanente para
    janela fora do alcance, e insistir nela só atrasa as estações seguintes.
    """
    transporte = transporte or _transporte_requests
    variaveis = {"stationCode": codigo, "startDate": iso_utc(inicio),
                 "endDate": iso_utc(fim), "interval": intervalo}
    payload = {"operationName": "Historic", "query": QUERY, "variables": variaveis}
    ultimo = None
    for tentativa in range(1, tentativas + 1):
        try:
            resposta = transporte(payload)
        except Exception as exc:  # noqa: BLE001 — rede; a API só fala por `errors`
            ultimo = f"rede: {exc}"
            if tentativa < tentativas:
                dormir(2 * tentativa)
            continue
        if resposta.get("errors"):
            ultimo = (resposta["errors"][0] or {}).get("message") or "errors"
            if tentativa < tentativas:
                dormir(2 * tentativa)
            continue
        return variaveis, resposta
    raise Bloqueado(f"{codigo} {variaveis['startDate']}..{variaveis['endDate']}: {ultimo}")


def envelope(variaveis: dict, resposta: dict, agora: datetime | None = None) -> dict:
    """O formato que o `consolidar_historico_dcsc.ler_pasta` já sabe ler."""
    agora = agora or datetime.now(timezone.utc)
    return {"variables": variaveis,
            "coletado_em_utc": agora.astimezone(timezone.utc).isoformat(),
            "resposta": resposta}


def quantos_itens(resposta: dict) -> int:
    try:
        return len(resposta["data"]["historic"]["items"] or [])
    except (KeyError, TypeError):
        return 0


def baixar_estacao(codigo: str, inicio: datetime, fim: datetime, intervalo: str,
                   destino: Path, transporte=None, dormir=time.sleep,
                   agora: datetime | None = None) -> dict:
    """Baixa as janelas que faltam da estação. Nunca reescreve janela já no disco.

    Janela que falhou NÃO vira arquivo — assim a próxima execução tenta de novo, em vez de
    deixar um buraco silencioso na série.
    """
    pasta = destino / codigo
    pasta.mkdir(parents=True, exist_ok=True)
    resumo = {"codigo": codigo, "janelas": 0, "puladas": 0, "itens": 0, "falhas": []}
    for ini, ate in janelas(inicio, fim):
        arquivo = pasta / nome_da_janela(ini, ate)
        if arquivo.exists():
            resumo["puladas"] += 1
            continue
        try:
            variaveis, resposta = pedir(codigo, ini, ate, intervalo,
                                        transporte=transporte, dormir=dormir)
        except Bloqueado as exc:
            resumo["falhas"].append(str(exc))
            continue
        finally:
            dormir(PAUSA_ENTRE_CHAMADAS_S)
        arquivo.write_text(
            json.dumps(envelope(variaveis, resposta, agora), ensure_ascii=False),
            encoding="utf-8")
        resumo["janelas"] += 1
        resumo["itens"] += quantos_itens(resposta)
    return resumo


SEMANA = timedelta(days=7)
FOLGA_SEMANA_FECHADA = timedelta(days=1)


def semanas_fechadas(agora: datetime, maximo_dias: int = PROFUNDIDADE_MAX_DIAS,
                     folga: timedelta = FOLGA_SEMANA_FECHADA) -> list[tuple[datetime, datetime]]:
    """As semanas de segunda 00:00 UTC a segunda 00:00 UTC que cabem inteiras no alcance da API e que
    terminaram há mais de `folga` (dado atrasado da telemetria ainda pode chegar no dia seguinte)."""
    agora = agora.astimezone(timezone.utc)
    limite = agora - timedelta(days=maximo_dias)
    seg = (limite - timedelta(days=limite.weekday())).replace(hour=0, minute=0, second=0, microsecond=0)
    if seg < limite:
        seg += SEMANA
    saida = []
    while seg + SEMANA + folga <= agora:
        saida.append((seg, seg + SEMANA))
        seg += SEMANA
    return saida


def nome_acumulado(codigo: str, inicio: datetime, fim: datetime) -> str:
    """`DCSC-00013/20260928T000000_20261005T000000.json.gz`: o caminho no acervo."""
    return f"{codigo}/{nome_da_janela(inicio, fim)}.gz"


def acumular_estacao(codigo: str, semanas: list[tuple[datetime, datetime]], intervalo: str,
                     destino: Path, ja_baixadas: set[str], transporte=None, dormir=time.sleep,
                     agora: datetime | None = None) -> dict:
    """Baixa as semanas que o acervo ainda não tem. Grava só semana com itens, todos desta estação."""
    resumo = {"codigo": codigo, "novas": [], "ja_no_acervo": 0, "vazias": 0, "itens": 0, "falhas": []}
    for ini, ate in semanas:
        nome = nome_acumulado(codigo, ini, ate)
        if nome in ja_baixadas:
            resumo["ja_no_acervo"] += 1
            continue
        try:
            variaveis, resposta = pedir(codigo, ini, ate, intervalo, transporte=transporte, dormir=dormir)
        except Bloqueado as exc:
            resumo["falhas"].append(str(exc))
            continue
        finally:
            dormir(PAUSA_ENTRE_CHAMADAS_S)
        itens = (resposta.get("data") or {}).get("historic", {}).get("items") or []
        if not itens:
            resumo["vazias"] += 1
            continue
        alheios = {it.get("codigo") for it in itens} - {codigo}
        if alheios:
            resumo["falhas"].append(f"{codigo} {variaveis['startDate']}: itens de outra estação {sorted(map(str, alheios))}")
            continue
        arquivo = destino / nome
        arquivo.parent.mkdir(parents=True, exist_ok=True)
        corpo = json.dumps(envelope(variaveis, resposta, agora), ensure_ascii=False).encode("utf-8")
        arquivo.write_bytes(gzip.compress(corpo, mtime=0))
        resumo["novas"].append(nome)
        resumo["itens"] += len(itens)
    return resumo


def codigos_da_cadeia() -> list[str]:
    """Os `codigo_dcsc` das cidades do `estacoes.json` — a bacia que o site mostra."""
    from comum import le_json

    vistos: list[str] = []
    def anda(o):
        if isinstance(o, dict):
            c = o.get("codigo_dcsc")
            if isinstance(c, str) and c.startswith("DCSC-") and c not in vistos:
                vistos.append(c)
            for v in o.values():
                anda(v)
        elif isinstance(o, list):
            for v in o:
                anda(v)
    anda(le_json("estacoes.json"))
    return vistos


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("codigos", nargs="*", help="DCSC-00006 DCSC-00013 ...")
    ap.add_argument("--cadeia", action="store_true",
                    help="usa os codigo_dcsc das cidades do estacoes.json")
    ap.add_argument("--dias", type=int, default=PROFUNDIDADE_MAX_DIAS)
    ap.add_argument("--intervalo", default="MIN_10", choices=INTERVALOS)
    ap.add_argument("--destino", type=Path, default=DESTINO_PADRAO)
    ap.add_argument("--acumular", action="store_true",
                    help="semanas fechadas, .json.gz, pulando as de --ja-baixadas (modo do cron)")
    ap.add_argument("--ja-baixadas", type=Path,
                    help="arquivo com os caminhos já no acervo, um por linha (DCSC-00013/....json.gz)")
    args = ap.parse_args(argv)

    codigos = list(args.codigos)
    if args.cadeia:
        codigos += [c for c in codigos_da_cadeia() if c not in codigos]
    if not codigos:
        ap.error("informe ao menos um código, ou --cadeia")

    agora = datetime.now(timezone.utc)
    if args.acumular:
        return acumular(codigos, args.intervalo, args.destino, args.ja_baixadas, agora)
    inicio, cortou = limitar_profundidade(agora - timedelta(days=args.dias), agora)
    if cortou:
        print(f"aviso: a API só volta ~{PROFUNDIDADE_MAX_DIAS} dias; início puxado para "
              f"{inicio:%Y-%m-%d}. Série mais longa só acumulando (rode isto em cron).",
              file=sys.stderr)

    falhou = False
    for i, codigo in enumerate(codigos, 1):
        r = baixar_estacao(codigo, inicio, agora, args.intervalo, args.destino)
        print(f"[{i}/{len(codigos)}] {codigo}: {r['janelas']} janela(s) nova(s), "
              f"{r['itens']} pontos, {r['puladas']} já no disco"
              + (f", {len(r['falhas'])} FALHA(S)" if r["falhas"] else ""))
        for f in r["falhas"]:
            print(f"    falha: {f}", file=sys.stderr)
            falhou = True
    print(f"\nconsolidar: python3 scripts/consolidar_historico_dcsc.py {args.destino}")
    return 1 if falhou else 0


def acumular(codigos: list[str], intervalo: str, destino: Path, lista: Path | None, agora: datetime) -> int:
    ja = set()
    if lista and lista.exists():
        ja = {linha.strip() for linha in lista.read_text(encoding="utf-8").splitlines() if linha.strip()}
    semanas = semanas_fechadas(agora)
    if not semanas:
        print("nenhuma semana fechada no alcance da API", file=sys.stderr)
        return 1
    print(f"semanas fechadas no alcance: {semanas[0][0]:%Y-%m-%d} a {semanas[-1][1]:%Y-%m-%d} "
          f"({len(semanas)}); {len(ja)} arquivo(s) já no acervo")
    falhou = False
    total = 0
    for i, codigo in enumerate(codigos, 1):
        r = acumular_estacao(codigo, semanas, intervalo, destino, ja)
        total += len(r["novas"])
        print(f"[{i}/{len(codigos)}] {codigo}: {len(r['novas'])} semana(s) nova(s), {r['itens']} pontos, "
              f"{r['ja_no_acervo']} já no acervo, {r['vazias']} vazia(s)"
              + (f", {len(r['falhas'])} FALHA(S)" if r["falhas"] else ""))
        for f in r["falhas"]:
            print(f"    falha: {f}", file=sys.stderr)
            falhou = True
    print(f"\n{total} arquivo(s) novo(s) em {destino}")
    return 1 if falhou else 0


if __name__ == "__main__":
    raise SystemExit(main())
