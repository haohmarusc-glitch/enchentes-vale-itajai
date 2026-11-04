#!/usr/bin/env python3
"""Transcreve a tabela "Histórico de enchentes em Blumenau" (Mendeley Data) e a cruza com `enchentes.json`.

Fonte: Melchioretto, Loos e Silva & Warwar da Fonseca (Senac SC), *Histórico de enchentes em Blumenau*,
Mendeley Data, v2, 23/09/2025, DOI 10.17632/cj64gycsw8.2, CC BY 4.0. Bruto e ficha em
`data/brutos/varredura-fontes-2026-11-04/` (sha256 conferido no handoff de 04/11/2026).

O QUE ESTE SCRIPT FAZ E O QUE NÃO FAZ. Ele só lê. `--transcrever` regrava o CSV a partir do xlsx, para a
transcrição ser reproduzível (o teste confere que o CSV commitado é o que o xlsx dá). O cruzamento imprime um
relatório em Markdown: pares pela data, divergências de cota, o que só a tabela tem e o que só o projeto tem.
**Nada entra em `enchentes.json`**: a tabela não declara em que régua está cada número (régua antiga, IBGE ou
régua de hoje — `CLAUDE.md`, regra bloqueante de Blumenau), então o máximo que ela vale é cruzamento, e cada
número que bater com uma das três referências é dito com qual bateu. Decisão de cadastro é do Jefferson.

Uso:
    python3 scripts/cruzar_mendeley_blumenau.py                      # relatório em Markdown (stdout)
    python3 scripts/cruzar_mendeley_blumenau.py --transcrever        # regrava o CSV a partir do xlsx
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from comum import DADOS, le_json  # noqa: E402

PASTA = DADOS / "brutos" / "varredura-fontes-2026-11-04"
XLSX = PASTA / "Tabela de enchentes.xlsx"
CSV = PASTA / "mendeley-blumenau-enchentes.csv"
COLUNAS = ("ano", "mes", "dia", "cota_m", "categoria")

#: Como a tabela se chama nas mensagens; a referência altimétrica NÃO é declarada por ela.
FONTE = "Mendeley Data, DOI 10.17632/cj64gycsw8.2 (v2, 23/09/2025)"

#: Deslocamentos entre as três referências da régua de Blumenau (CLAUDE.md): régua de hoje = IBGE + 0,20 m =
#: régua antiga + 0,40 m. Um número da tabela que bata com `pico_m − d` está na referência de nome `nome`.
REFERENCIAS = (
    ("régua de hoje", 0.0),
    ("IBGE (régua + 0,20 m)", 0.20),
    ("régua antiga", 0.40),
)
TOLERANCIA_M = 0.005          # igualdade de centímetro, com folga de arredondamento
DIAS_PROXIMOS = 3             # "data próxima": mesmo evento com dia diferente entre as fontes


# --- Transcrição ----------------------------------------------------------------------------------------

def _data_de_completa(valor) -> tuple[int, int, int] | None:
    """A coluna COMPLETA vem em dois formatos (texto `d/m/aaaa` e data do Excel); devolve (ano, mês, dia)."""
    if isinstance(valor, dt.datetime):
        return valor.year, valor.month, valor.day
    if isinstance(valor, str):
        partes = valor.strip().split("/")
        if len(partes) == 3 and all(p.isdigit() for p in partes):
            d, m, a = (int(p) for p in partes)
            return a, m, d
    return None


def transcrever(caminho: Path = XLSX) -> tuple[list[dict], list[str]]:
    """Lê o xlsx e devolve (linhas, anomalias). Cada linha: ano, mes, dia, cota_m, categoria, data (ISO)."""
    try:
        import openpyxl
    except ImportError:  # pragma: no cover
        raise SystemExit("Para ler .xlsx é preciso o openpyxl: pip install -r scripts/requirements.txt")
    wb = openpyxl.load_workbook(caminho, read_only=True, data_only=True)
    ws = wb.worksheets[0]
    linhas: list[dict] = []
    anomalias: list[str] = []
    for i, (ano, mes, dia, completa, cota, categoria, *_) in enumerate(ws.iter_rows(min_row=2, values_only=True), 2):
        if ano is None:
            continue
        ano, mes, dia = int(ano), int(mes), int(dia)
        cota = float(cota)
        cat = str(categoria).strip() if categoria not in (None, "") else ""
        completa_amd = _data_de_completa(completa)
        if completa_amd is None:
            anomalias.append(f"linha {i}: COMPLETA ilegível ({completa!r})")
        elif completa_amd != (ano, mes, dia):
            anomalias.append(f"linha {i}: Ano/Mês/Dia = {dia:02d}/{mes:02d}/{ano} mas COMPLETA = "
                             f"{completa_amd[2]:02d}/{completa_amd[1]:02d}/{completa_amd[0]}")
        linhas.append({"ano": ano, "mes": mes, "dia": dia, "cota_m": cota, "categoria": cat,
                       "data": f"{ano:04d}-{mes:02d}-{dia:02d}"})
    datas = [x["data"] for x in linhas]
    repetidas = sorted({d for d in datas if datas.count(d) > 1})
    if repetidas:
        anomalias.append("datas repetidas: " + ", ".join(repetidas))
    return linhas, anomalias


def gravar_csv(linhas: list[dict], destino: Path = CSV) -> None:
    with open(destino, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(COLUNAS)
        for x in linhas:
            w.writerow([x["ano"], x["mes"], x["dia"], f"{x['cota_m']:g}", x["categoria"]])


def ler_csv(caminho: Path = CSV) -> list[dict]:
    with open(caminho, encoding="utf-8", newline="") as f:
        linhas = []
        for r in csv.DictReader(f):
            ano, mes, dia = int(r["ano"]), int(r["mes"]), int(r["dia"])
            linhas.append({"ano": ano, "mes": mes, "dia": dia, "cota_m": float(r["cota_m"]),
                           "categoria": r["categoria"], "data": f"{ano:04d}-{mes:02d}-{dia:02d}"})
        return linhas


# --- Cruzamento -----------------------------------------------------------------------------------------

def _iso(d: str) -> dt.date | None:
    try:
        return dt.date.fromisoformat(d)
    except ValueError:
        return None


def bate_com(cota: float, registro: dict) -> str | None:
    """Com qual referência do registro o número da tabela bate, ou None."""
    pico = registro.get("pico_m")
    if isinstance(pico, (int, float)):
        ref = registro.get("referencia")
        for nome, desloc in REFERENCIAS:
            if abs(cota - (pico - desloc)) < TOLERANCIA_M:
                if ref == "régua":
                    return nome
                # O pico do projeto ainda não está na régua de hoje (os 67 não convertidos, CLAUDE.md): "igual" aqui
                # é igual ao número guardado, que está em IBGE ou sem referência — não é prova de régua de hoje.
                if desloc == 0.0:
                    return f"igual ao projeto, que está em {ref or 'referência null'}"
                return f"{desloc:.2f} m abaixo de um pico em {ref or 'referência null'}"
    publicado = registro.get("pico_publicado_m")
    if isinstance(publicado, (int, float)) and abs(cota - publicado) < TOLERANCIA_M:
        return f"como publicado ({registro.get('referencia_publicada')})"
    for d in registro.get("divergencias") or []:
        v = d.get("pico_m")
        if isinstance(v, (int, float)) and abs(cota - v) < TOLERANCIA_M:
            return "divergência já cadastrada"
    return None


def cruzar(linhas: list[dict], eventos: list[dict]) -> dict:
    blu = [e for e in eventos if e.get("cidade") == "blumenau"]
    por_data = {e["data"]: e for e in blu if _iso(str(e.get("data")))}
    pares, proximos, so_tabela = [], [], []
    usados: set[str] = set()
    for x in linhas:
        e = por_data.get(x["data"])
        if e is None:
            d0 = dt.date.fromisoformat(x["data"])
            cand = [r for r in blu if _iso(str(r.get("data"))) and abs((_iso(str(r["data"])) - d0).days) <= DIAS_PROXIMOS
                    and r["data"] not in usados]
            if cand:
                e = min(cand, key=lambda r: abs((_iso(str(r["data"])) - d0).days))
                proximos.append((x, e, bate_com(x["cota_m"], e)))
                usados.add(e["data"])
            else:
                so_tabela.append(x)
            continue
        usados.add(e["data"])
        pares.append((x, e, bate_com(x["cota_m"], e)))
    so_projeto = [e for e in blu if e.get("data") not in usados]
    return {"pares": pares, "proximos": proximos, "so_tabela": so_tabela, "so_projeto": so_projeto,
            "total_tabela": len(linhas), "total_projeto": len(blu)}


def _num(v) -> str:
    return "—" if not isinstance(v, (int, float)) else f"{v:.2f}".replace(".", ",")


def relatorio_md(r: dict, anomalias: list[str]) -> str:
    out = ["## Cruzamento: tabela do Mendeley × `enchentes.json` (Blumenau)", "",
           f"Tabela: {r['total_tabela']} linhas · projeto: {r['total_projeto']} registros de Blumenau · "
           f"pares pela mesma data: {len(r['pares'])} · data próxima (≤ {DIAS_PROXIMOS} dias): {len(r['proximos'])} · "
           f"só na tabela: {len(r['so_tabela'])} · só no projeto: {len(r['so_projeto'])}.", ""]
    if anomalias:
        out += ["**Anomalias da transcrição:**"] + [f"- {a}" for a in anomalias] + [""]
    out += ["### Pares (mesma data)", "", "| data | tabela (m) | projeto `pico_m` (ref.) | publicado | bate com |", "|---|---|---|---|---|"]
    for x, e, bate in r["pares"]:
        out.append(f"| {x['data']} | {_num(x['cota_m'])} | {_num(e.get('pico_m'))} ({e.get('referencia') or 'null'}) | "
                   f"{_num(e.get('pico_publicado_m'))} | {bate or '**diferente**'} |")
    out += ["", "### Data próxima (mesmo evento, dia diferente?)", "", "| tabela | projeto | tabela (m) | projeto (m) | bate com |", "|---|---|---|---|---|"]
    for x, e, bate in r["proximos"]:
        out.append(f"| {x['data']} | {e['data']} | {_num(x['cota_m'])} | {_num(e.get('pico_m'))} ({e.get('referencia') or 'null'}) | {bate or '**diferente**'} |")
    out += ["", "### Só na tabela", "", "| data | cota (m) | categoria |", "|---|---|---|"]
    out += [f"| {x['data']} | {_num(x['cota_m'])} | {x['categoria']} |" for x in r["so_tabela"]]
    out += ["", "### Só no projeto", "", "| data | `pico_m` (ref.) | confiança |", "|---|---|---|"]
    out += [f"| {e.get('data')} | {_num(e.get('pico_m'))} ({e.get('referencia') or 'null'}) | {e.get('confianca')} |"
            for e in r["so_projeto"]]
    contagem: dict[str, int] = {}
    for _, _, bate in r["pares"] + r["proximos"]:
        chave = bate or "diferente"
        contagem[chave] = contagem.get(chave, 0) + 1
    out += ["", "### Com que referência a tabela bate", "", "| bate com | pares |", "|---|---|"]
    out += [f"| {k} | {v} |" for k, v in sorted(contagem.items(), key=lambda kv: -kv[1])]
    return "\n".join(out) + "\n"


#: O que `--anotar` grava em cada registro de Blumenau que a tabela também tem (decisão do Jefferson, 04/11/2026:
#: "citar nas notas dos registros de Blumenau como fonte de cruzamento"). Vai num campo próprio, `cruzamentos`,
#: para não misturar com `nota` (que a tela mostra) nem com `divergencias` (que exige valor adotado × outro).
FONTE_CRUZAMENTO = ("Histórico de enchentes em Blumenau (Melchioretto, Loos e Silva & Warwar da Fonseca, Senac SC), "
                    "Mendeley Data, DOI 10.17632/cj64gycsw8.2, v2 de 23/09/2025, CC BY 4.0 — compilação da Defesa "
                    "Civil de Blumenau; não declara a régua")
DOC_CRUZAMENTO = "docs/VARREDURA-FONTES-2026-11-04-CRUZAMENTO-BLUMENAU.md"
#: Descrição do campo, gravada em `_meta.campos` de enchentes.json junto com a anotação.
CAMPO_CRUZAMENTOS = (
    "Fontes independentes que trazem o MESMO pico, só para cruzamento: cada entrada tem fonte, valor_m (o número "
    "como a fonte publica), data_na_fonte, bate_com (com que referência de Blumenau o número bate, ou 'diferente'), "
    "confianca, em (data da conferência) e doc. Não é nível: nada aqui entra em recorde, gráfico, 'minha rua', "
    "simulador ou bot, e não muda pico_m nem referencia. Hoje só a tabela do Mendeley em Blumenau (04/11/2026)."
)


def anotar(eventos: list[dict], resultado: dict, em: str = "2026-11-04") -> int:
    """Grava `cruzamentos` nos registros pareados (idempotente: substitui a entrada da mesma fonte). Devolve quantos."""
    n = 0
    for x, e, bate in resultado["pares"] + resultado["proximos"]:
        entrada = {"fonte": FONTE_CRUZAMENTO, "valor_m": x["cota_m"], "data_na_fonte": x["data"],
                   "bate_com": bate or "diferente", "confianca": "media", "em": em, "doc": DOC_CRUZAMENTO}
        outros = [c for c in e.get("cruzamentos") or [] if c.get("fonte") != FONTE_CRUZAMENTO]
        e["cruzamentos"] = outros + [entrada]
        n += 1
    return n


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    ap.add_argument("--xlsx", type=Path, default=XLSX)
    ap.add_argument("--csv", type=Path, default=CSV)
    ap.add_argument("--transcrever", action="store_true", help="regrava o CSV a partir do xlsx")
    ap.add_argument("--anotar", action="store_true",
                    help="grava `cruzamentos` nos registros de Blumenau de enchentes.json (decisão do Jefferson)")
    a = ap.parse_args(argv)
    if a.transcrever:
        linhas, anomalias = transcrever(a.xlsx)
        gravar_csv(linhas, a.csv)
        print(f"{len(linhas)} linhas → {a.csv}", file=sys.stderr)
        for an in anomalias:
            print(f"anomalia: {an}", file=sys.stderr)
        return 0
    linhas = ler_csv(a.csv)
    anomalias = transcrever(a.xlsx)[1] if a.xlsx.exists() else []
    dados = le_json("enchentes.json")
    resultado = cruzar(linhas, dados["eventos"])
    if a.anotar:
        from comum import grava_json
        n = anotar(dados["eventos"], resultado)
        dados.setdefault("_meta", {}).setdefault("campos", {})["cruzamentos"] = CAMPO_CRUZAMENTOS
        grava_json("enchentes.json", dados)
        print(f"{n} registro(s) de Blumenau anotados com `cruzamentos` → data/enchentes.json", file=sys.stderr)
        return 0
    print(relatorio_md(resultado, anomalias))
    return 0


if __name__ == "__main__":
    sys.exit(main())
