#!/usr/bin/env python3
"""
Coletor da API da Defesa Civil de Santa Catarina (monitoramento.defesacivil.sc.gov.br).

Endpoint GraphQL publico, sem autenticacao.

Dois modos:
  python coletar_dcsc.py snapshot
      -> data/snapshot.json   (leitura atual de todas as 174 estacoes)
      -> data/estacoes.csv    (catalogo: codigo, nome, tipo, lat, lon, bacia, regiao)

  python coletar_dcsc.py historico [--dias 88] [--intervalo HOUR_1] [--codigos DCSC-00006,DCSC-00013]
      -> data/historico/<CODIGO>.csv  (append incremental, sem duplicar timestamps)

IMPORTANTE: a API so devolve os ultimos ~89 dias. Rode o modo `historico`
em cron (semanal basta) para o arquivo local crescer alem dessa janela.
Enchentes antigas (1983, 1984, 2008, 2011, 2023) NAO estao nesta API --
vem da ANA/Hidroweb, do CEOPS/FURB ou do ArcGIS da Prefeitura de Itajai.
"""

import argparse
import csv
import json
import os
import sys
import time
from datetime import datetime, timedelta, timezone

import requests

ENDPOINT = "https://monitoramento.defesacivil.sc.gov.br/graphql"
CLIENT = "secretaria-de-defesa-civil"
HEADERS = {
    "content-type": "application/json",
    "origin": "https://monitoramento.defesacivil.sc.gov.br",
    "referer": "https://monitoramento.defesacivil.sc.gov.br/mapa",
    "user-agent": "Mozilla/5.0 (coletor enchentes-vale-itajai)",
}

# A API rejeita operacoes cujo operationName nao seja um dos conhecidos
# (Tags_data, Historic, Radares, Nowcasting) -> erro "Operacao bloqueada.".
# Os campos dentro da query podem ser escolhidos livremente.

Q_TAGS = """query Tags_data {
  tags_data(clients: ["%s"]) {
    qualle_meteorologia {
      codigo type timestamp
      name { prefix general local }
      position { bacia regiao latitude longitude altitude }
      data {
        rio {
          rio_nome { value }
          rio_nivel { value unit { value } }
          rio_nivel_tendencia { value }
          rio_area_drenagem { value }
          rio_vazao { value }
          rio_alarmes {
            inundacao { ativo { value } status { value }
                        atencao { value } alerta { value } emergencia { value } }
            estiagem  { atencao { value } alerta { value } emergencia { value } }
          }
        }
        chuva { acumulado {
          min005 { value } h001 { value } h003 { value } h006 { value }
          h012 { value } h024 { value } h048 { value } h072 { value } h168 { value }
        } }
      }
    }
  }
}""" % CLIENT

Q_HIST = """query Historic($stationCode: String!, $startDate: String!, $endDate: String!, $interval: QueryInterval) {
  historic(system: Qualle_Hidrometeorologia, client: "%s",
           stationCode: $stationCode, startDate: $startDate, endDate: $endDate,
           interval: $interval, opts: { ordenacao: ASC })
}""" % CLIENT

MAX_DIAS_JANELA = 60   # intervalo maximo por requisicao (90 dias ja e recusado)
MAX_DIAS_PASSADO = 88  # o quanto da para voltar no tempo


def gql(operation_name, query, variables=None, tentativas=4):
    payload = {"operationName": operation_name, "query": query}
    if variables:
        payload["variables"] = variables
    erro = None
    for i in range(tentativas):
        try:
            r = requests.post(ENDPOINT, headers=HEADERS, json=payload, timeout=60)
            r.raise_for_status()
            j = r.json()
            if j.get("errors"):
                erro = j["errors"][0].get("message")
                # "Operacao bloqueada." tambem aparece em rate limit -> vale tentar de novo
                time.sleep(2 * (i + 1))
                continue
            return j["data"]
        except Exception as e:  # noqa: BLE001
            erro = str(e)
            time.sleep(2 * (i + 1))
    raise RuntimeError(f"{operation_name} falhou: {erro}")


def iso(dt):
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z")


# --------------------------------------------------------------------------- #
# snapshot
# --------------------------------------------------------------------------- #
def cmd_snapshot(args):
    os.makedirs("data", exist_ok=True)
    d = gql("Tags_data", Q_TAGS)
    estacoes = d["tags_data"]["qualle_meteorologia"]
    agora = datetime.now(timezone.utc).isoformat()

    with open("data/snapshot.json", "w", encoding="utf-8") as f:
        json.dump({"coletado_em": agora, "estacoes": estacoes}, f,
                  ensure_ascii=False, indent=1)

    def g(e, *path):
        cur = e
        for p in path:
            if cur is None:
                return None
            cur = cur.get(p)
        return cur

    with open("data/estacoes.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["codigo", "tipo", "nome", "local", "bacia", "regiao",
                    "latitude", "longitude", "altitude",
                    "nivel", "tendencia", "vazao",
                    "inund_ativo", "inund_status", "chuva_1h", "chuva_24h",
                    "timestamp"])
        for e in estacoes:
            ino = g(e, "data", "rio", "rio_alarmes", "inundacao") or {}
            w.writerow([
                e.get("codigo"), e.get("type"),
                g(e, "name", "general"), g(e, "name", "local"),
                g(e, "position", "bacia"), g(e, "position", "regiao"),
                g(e, "position", "latitude"), g(e, "position", "longitude"),
                g(e, "position", "altitude"),
                g(e, "data", "rio", "rio_nivel", "value"),
                g(e, "data", "rio", "rio_nivel_tendencia", "value"),
                g(e, "data", "rio", "rio_vazao", "value"),
                (ino.get("ativo") or {}).get("value"),
                (ino.get("status") or {}).get("value"),
                g(e, "data", "chuva", "acumulado", "h001", "value"),
                g(e, "data", "chuva", "acumulado", "h024", "value"),
                e.get("timestamp"),
            ])

    print(f"{len(estacoes)} estacoes -> data/snapshot.json e data/estacoes.csv")


# --------------------------------------------------------------------------- #
# historico
# --------------------------------------------------------------------------- #
CAMPOS_HIST = ["ts", "codigo", "rio_nivel", "rio_variacao",
               "chuva_mm", "chuva_total", "chuva_taxa_med", "chuva_taxa_max",
               "bateria_v"]


def buscar_historico(codigo, inicio, fim, intervalo):
    """Quebra o periodo em janelas de MAX_DIAS_JANELA e devolve a lista de pontos."""
    pontos = []
    cur = inicio
    while cur < fim:
        ate = min(cur + timedelta(days=MAX_DIAS_JANELA), fim)
        d = gql("Historic", Q_HIST, {
            "stationCode": codigo,
            "startDate": iso(cur),
            "endDate": iso(ate),
            "interval": intervalo,
        })
        pontos.extend((d.get("historic") or {}).get("items") or [])
        cur = ate
        time.sleep(1.0)  # a API bloqueia rajadas
    return pontos


def salvar_append(codigo, pontos):
    os.makedirs("data/historico", exist_ok=True)
    caminho = f"data/historico/{codigo}.csv"
    existentes = set()
    if os.path.exists(caminho):
        with open(caminho, newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                existentes.add(row["ts"])
    novos = [p for p in pontos if p.get("ts") not in existentes]
    escrever_cabecalho = not os.path.exists(caminho)
    with open(caminho, "a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=CAMPOS_HIST, extrasaction="ignore")
        if escrever_cabecalho:
            w.writeheader()
        for p in sorted(novos, key=lambda x: x.get("ts") or ""):
            w.writerow(p)
    return len(novos), len(existentes) + len(novos)


def cmd_historico(args):
    if args.codigos:
        codigos = [c.strip() for c in args.codigos.split(",") if c.strip()]
    else:
        # sem lista explicita: todas as estacoes hidrologicas da bacia do Itajai
        d = gql("Tags_data", Q_TAGS)
        codigos = [
            e["codigo"] for e in d["tags_data"]["qualle_meteorologia"]
            if e.get("type") == "Hidro"
            and (e.get("position") or {}).get("bacia") == "SC - Rio Itajaí"
        ]

    dias = min(args.dias, MAX_DIAS_PASSADO)
    fim = datetime.now(timezone.utc)
    inicio = fim - timedelta(days=dias)

    for i, codigo in enumerate(codigos, 1):
        try:
            pontos = buscar_historico(codigo, inicio, fim, args.intervalo)
            novos, total = salvar_append(codigo, pontos)
            print(f"[{i}/{len(codigos)}] {codigo}: +{novos} novos "
                  f"({len(pontos)} recebidos, {total} no arquivo)")
        except Exception as e:  # noqa: BLE001
            print(f"[{i}/{len(codigos)}] {codigo}: FALHOU -- {e}", file=sys.stderr)


def main():
    p = argparse.ArgumentParser(description="Coletor Defesa Civil SC")
    sub = p.add_subparsers(dest="cmd", required=True)

    sub.add_parser("snapshot").set_defaults(func=cmd_snapshot)

    h = sub.add_parser("historico")
    h.add_argument("--dias", type=int, default=MAX_DIAS_PASSADO)
    h.add_argument("--intervalo", default="HOUR_1",
                   choices=["MIN_5", "MIN_10", "MIN_15", "MIN_30", "HOUR_1",
                            "HOUR_3", "HOUR_6", "HOUR_12", "HOUR_24", "HOUR_48",
                            "HOUR_72", "HOUR_96", "HOUR_168"])
    h.add_argument("--codigos", default="",
                   help="lista separada por virgula; vazio = todas as Hidro do rio Itajai")
    h.set_defaults(func=cmd_historico)

    args = p.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
