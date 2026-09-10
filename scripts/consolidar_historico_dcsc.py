#!/usr/bin/env python3
"""Consolida o histórico da rede estadual (DCSC, GraphQL `historic`) baixado em janelas de 14 dias.

DE ONDE VEM (10/09/2026). O Jefferson baixou no PC, com um script próprio (ainda fora do
repo), a query `historic` de monitoramento.defesacivil.sc.gov.br para 13 estações, em
janelas de 14 dias desde 1980, uma resposta por arquivo:

    historico-dcsc/DCSC00013.zip → DCSC-00013/20231101T000000_20231115T000000.json
    {"variables": {"stationCode": "DCSC-00013", "startDate": "...Z", "endDate": "...Z"},
     "coletado_em_utc": "2026-09-10T02:21:39.033Z",
     "resposta": {"data": {"historic": {"items": [{"ts": "2023-11-01T00:00:00.000",
                  "codigo": "DCSC-00013", "rio_nivel": 5.62, "rio_variacao": 0,
                  "chuva_mm": 0, "chuva_total": 0, "chuva_taxa_med": 0, "chuva_taxa_max": 0,
                  "bateria_v": 13.24, "timestamp": "..."}, ...], "totalCount": N}}}}

Os dados começam entre out/2022 e abr/2023 (antes disso `items` vem vazio), a cada 10 min.

FUSO — PROVADO, não presumido. O `ts` NÃO tem fuso e é hora de BRASÍLIA, o mesmo contrato
do `medido_em` do projeto (CLAUDE.md). Duas provas independentes, 10/09/2026:
  1. a janela pedida com `startDate = 2026-09-01T00:00Z` devolve como primeiro item
     `ts = 2026-08-31T21:10` — 00:00 UTC é 21:00 em Brasília;
  2. a crista de 01/09/2026 em Rio do Sul: DCSC-00013 às 05:20 (7,07 m) e a Asthon da Ponte
     Dom Tito Buss às 05:08 hora local (6,79 m). Se `ts` fosse UTC, a DCSC cristaria 3 h ANTES.
Por isso `medido_em` sai igual ao `ts` (sem o `.000`), sem conversão. A API ao vivo
(`Tags_data`, usada pelo coleta_nivel_sc) manda UTC com fuso — são endpoints diferentes.

SENTINELAS E PICOS DE SENSOR. A DCSC-00039 (Ituporanga) grava `rio_nivel = -35` em parte
da série: é "sem leitura", não nível. Ibirama (DCSC-00020) tem 21474836,47 (2^31/100, estouro
de inteiro), Ascurra 581,0 e Guabiruba 91,0 em leituras isoladas. Regra: `rio_nivel` abaixo
de LIMITE_SENTINELA ou acima de LIMITE_PLAUSIVEL (os 30 m do coleta_nivel_sc: acima disto
não é régua de rio urbano) vira vazio e é contado. Crista cujo máximo é uma leitura solta
(mais de SALTO_ISOLADO_M acima das vizinhas de 10 min dos dois lados) é marcada
`isolada: true` — é pico de sensor até prova em contrário, e não vira candidata.

O QUE GRAVA
  * `data/series/dcsc/DCSC-000NN.csv` — a série inteira, uma linha por carimbo (fora do
    git: 129 MB em 13 estações; `data/series/` é ignorado, reproduzível por este script);
  * `data/brutos/dcsc-historico-resumo-<data>.json` — o que cabe no repo e é citável:
    cobertura, contagens, sentinelas, buracos e as maiores cristas de cada estação.
    Crista aqui é CANDIDATA: nada entra em enchentes.json sem decisão do Jefferson.

Uso:
    python3 scripts/consolidar_historico_dcsc.py <pasta-com-zips-ou-json> [--series data/series/dcsc]
                                                 [--resumo data/brutos/dcsc-historico-resumo-AAAA-MM-DD.json]
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
import zipfile
from collections import Counter
from datetime import date, datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from analisar_telemetria_ana import buracos, crista  # noqa: E402
from comum import DADOS  # noqa: E402

try:
    from coleta_nivel_sc import CADEIA
except Exception:  # pragma: no cover — só para o resumo ficar legível sem o coletor
    CADEIA = {}

COLUNAS = ["medido_em", "rio_nivel", "rio_variacao", "chuva_mm", "chuva_total",
           "chuva_taxa_med", "chuva_taxa_max", "bateria_v"]
LIMITE_SENTINELA = -30.0        # rio_nivel abaixo disto é "sem leitura" (-35 na DCSC-00039)
LIMITE_PLAUSIVEL = 30.0         # o LIMITE_M do coleta_nivel_sc: acima disto não é régua de rio urbano
SALTO_ISOLADO_M = 1.0           # máximo mais de 1 m acima das duas vizinhas de 10 min = leitura solta
SEPARACAO_CRISTAS = timedelta(days=3)
BURACO_MINIMO = timedelta(hours=6)
CADENCIA = timedelta(minutes=10)


def nivel(item: dict) -> float | None:
    v = item.get("rio_nivel")
    if v is None or v == "":
        return None
    try:
        v = float(v)
    except (TypeError, ValueError):
        return None
    return None if v < LIMITE_SENTINELA or v > LIMITE_PLAUSIVEL else v


def quando(item: dict) -> datetime | None:
    ts = item.get("ts") or item.get("timestamp")
    if not ts:
        return None
    try:
        return datetime.fromisoformat(str(ts).replace("Z", "")[:19])
    except ValueError:
        return None


def itens_do_arquivo(corpo: dict) -> list[dict]:
    try:
        return corpo["resposta"]["data"]["historic"]["items"] or []
    except (KeyError, TypeError):
        return []


def ler_pasta(origem: Path) -> dict[str, dict]:
    """{codigo: {'itens': {ts: item}, 'janelas': n, 'coletas': [utc...], 'fim_janelas': max endDate}}.

    Aceita zips (DCSC00013.zip) e pastas já extraídas (DCSC-00013/*.json), misturados.
    """
    por_estacao: dict[str, dict] = {}

    def acumula(corpo: dict) -> None:
        cod = (corpo.get("variables") or {}).get("stationCode")
        if not cod:
            return
        e = por_estacao.setdefault(cod, {"itens": {}, "janelas": 0, "coletas": [], "fim_janelas": ""})
        e["janelas"] += 1
        if corpo.get("coletado_em_utc"):
            e["coletas"].append(corpo["coletado_em_utc"])
        fim = (corpo.get("variables") or {}).get("endDate", "")
        e["fim_janelas"] = max(e["fim_janelas"], fim)
        for it in itens_do_arquivo(corpo):
            if it.get("ts"):
                e["itens"][it["ts"]] = it

    for z in sorted(origem.rglob("*.zip")):
        with zipfile.ZipFile(z) as zf:
            for nome in zf.namelist():
                if nome.endswith(".json"):
                    acumula(json.loads(zf.read(nome)))
    for j in sorted(origem.rglob("*.json")):
        try:
            acumula(json.loads(j.read_text(encoding="utf-8")))
        except (json.JSONDecodeError, UnicodeDecodeError):
            continue
    return por_estacao


def serie_de(itens: dict[str, dict]) -> list[tuple[datetime, float | None]]:
    saida = []
    for ts in sorted(itens):
        t = quando(itens[ts])
        if t is not None:
            saida.append((t, nivel(itens[ts])))
    return saida


def isolada(serie: list[tuple[datetime, float]], quando: datetime, maximo: float,
            salto: float = SALTO_ISOLADO_M) -> bool:
    """Máximo mais de `salto` acima das vizinhas imediatas dos dois lados: leitura solta de sensor."""
    idx = next((i for i, (t, _) in enumerate(serie) if t == quando), None)
    if idx is None:
        return False
    antes = serie[idx - 1][1] if idx > 0 else None
    depois = serie[idx + 1][1] if idx + 1 < len(serie) else None
    vizinhas = [v for v in (antes, depois) if v is not None]
    return bool(vizinhas) and all(maximo - v > salto for v in vizinhas)


def cristas(serie: list[tuple[datetime, float | None]], n: int = 5,
            separacao: timedelta = SEPARACAO_CRISTAS) -> list[dict]:
    """As `n` maiores cristas, cada uma a mais de `separacao` das outras (mesmo evento não conta duas vezes).

    Leituras soltas (ver `isolada`) são descartadas da série antes de procurar a próxima crista,
    e listadas à parte em `descartadas_isoladas` pelo chamador.
    """
    restante = [(t, c) for t, c in serie if c is not None]
    saida: list[dict] = []
    while restante and len(saida) < n:
        c = crista(restante)
        if c is None:
            break
        if isolada(restante, c["quando"], c["maximo_m"]):
            saida.append({"maximo_m": c["maximo_m"], "quando": c["quando"].isoformat(timespec="minutes"),
                          "isolada": True})
            restante = [(t, v) for t, v in restante if t != c["quando"]]
            continue
        saida.append({"maximo_m": c["maximo_m"], "quando": c["quando"].isoformat(timespec="minutes"),
                      "plato_inicio": c["plato_inicio"].isoformat(timespec="minutes"),
                      "plato_fim": c["plato_fim"].isoformat(timespec="minutes"),
                      "plato_leituras": c["plato_leituras"], "na_borda": c["na_borda"], "isolada": False})
        centro = c["quando"]
        restante = [(t, v) for t, v in restante if abs(t - centro) > separacao]
    return saida


def resumo_da_estacao(cod: str, e: dict) -> dict:
    serie = serie_de(e["itens"])
    com_nivel = [(t, c) for t, c in serie if c is not None]
    brutos = [float(it["rio_nivel"]) for it in e["itens"].values()
              if it.get("rio_nivel") is not None and it.get("rio_nivel") != ""]
    sentinelas = sum(1 for v in brutos if v < LIMITE_SENTINELA)
    implausiveis = sum(1 for v in brutos if v > LIMITE_PLAUSIVEL)
    todas = cristas(serie, n=8)
    bur = [(a, b, tipo) for a, b, tipo in buracos(serie, BURACO_MINIMO)] if serie else []
    esperadas = int((serie[-1][0] - serie[0][0]) / CADENCIA) + 1 if len(serie) > 1 else len(serie)
    campos = Counter(k for it in e["itens"].values() for k in it)
    return {
        "codigo": cod,
        "cidade": CADEIA.get(cod),
        "janelas_baixadas": e["janelas"],
        "ultima_janela_pedida_ate_utc": e["fim_janelas"],
        "coletado_entre_utc": [min(e["coletas"]), max(e["coletas"])] if e["coletas"] else None,
        "leituras": len(serie),
        "leituras_com_nivel": len(com_nivel),
        "sentinelas_rio_nivel": sentinelas,
        "implausiveis_acima_30m": implausiveis,
        "primeira": serie[0][0].isoformat(timespec="minutes") if serie else None,
        "ultima": serie[-1][0].isoformat(timespec="minutes") if serie else None,
        "esperadas_a_10_min": esperadas,
        "buracos_maiores_que_6h": len([b for b in bur if b[2] == "dado"]),
        "maior_buraco_h": round(max((b[1] - b[0] for b in bur if b[2] == "dado"), default=timedelta(0))
                                .total_seconds() / 3600, 1),
        "campos": dict(campos),
        "nivel_min_m": min((c for _, c in com_nivel), default=None),
        "nivel_max_m": max((c for _, c in com_nivel), default=None),
        "cristas_candidatas": [c for c in todas if not c["isolada"]][:5],
        "descartadas_isoladas": [c for c in todas if c["isolada"]],
    }


def gravar_csv(destino: Path, itens: dict[str, dict]) -> int:
    destino.parent.mkdir(parents=True, exist_ok=True)
    n = 0
    with destino.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(COLUNAS)
        for ts in sorted(itens):
            it = itens[ts]
            linha = [str(ts)[:19]]
            for c in COLUNAS[1:]:
                v = it.get(c)
                if c == "rio_nivel":
                    v = nivel(it)
                linha.append("" if v is None else v)
            w.writerow(linha)
            n += 1
    return n


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("origem", type=Path, help="pasta com os zips (DCSC000NN.zip) ou os JSON extraídos")
    ap.add_argument("--series", type=Path, default=DADOS / "series" / "dcsc")
    ap.add_argument("--resumo", type=Path,
                    default=DADOS / "brutos" / f"dcsc-historico-resumo-{date.today().isoformat()}.json")
    args = ap.parse_args()

    por_estacao = ler_pasta(args.origem)
    if not por_estacao:
        print(f"nenhuma resposta `historic` encontrada em {args.origem}", file=sys.stderr)
        return 2
    resumos = []
    for cod in sorted(por_estacao):
        e = por_estacao[cod]
        n = gravar_csv(args.series / f"{cod}.csv", e["itens"])
        r = resumo_da_estacao(cod, e)
        resumos.append(r)
        topo = r["cristas_candidatas"][0] if r["cristas_candidatas"] else None
        print(f"{cod} {str(r['cidade'] or '?'):22s} {n:7d} leituras  {r['primeira'] or '—':16s} → "
              f"{r['ultima'] or '—':16s}  sentinelas {r['sentinelas_rio_nivel']:4d}  "
              f"implausíveis {r['implausiveis_acima_30m']:3d}  isoladas {len(r['descartadas_isoladas'])}  "
              f"maior crista {topo['maximo_m'] if topo else '—'} em {topo['quando'] if topo else '—'}")
    corpo = {
        "_meta": {
            "descricao": "Resumo do histórico da rede estadual (DCSC, GraphQL historic), consolidado por "
                         "scripts/consolidar_historico_dcsc.py. As séries inteiras estão em data/series/dcsc/ "
                         "(fora do git).",
            "fuso": "medido_em e todos os carimbos são hora de Brasília SEM fuso (provado — ver docstring "
                    "do script). coletado_entre_utc é UTC.",
            "sentinela": f"rio_nivel < {LIMITE_SENTINELA} ou > {LIMITE_PLAUSIVEL} vira vazio e é contado "
                         "(sentinelas_rio_nivel / implausiveis_acima_30m); leituras soltas (> "
                         f"{SALTO_ISOLADO_M} m acima das vizinhas de 10 min) saem das candidatas e ficam em "
                         "descartadas_isoladas.",
            "cristas": "CANDIDATAS, separadas por 3 dias; datum de cada estação é o bruto estadual "
                       "(usar_para_cota=false no coletor). Nenhuma entra em enchentes.json sem decisão.",
            "gerado_em": date.today().isoformat(),
        },
        "estacoes": resumos,
    }
    args.resumo.parent.mkdir(parents=True, exist_ok=True)
    args.resumo.write_text(json.dumps(corpo, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"resumo em {args.resumo}; séries em {args.series}/")
    return 0


if __name__ == "__main__":
    sys.exit(main())
