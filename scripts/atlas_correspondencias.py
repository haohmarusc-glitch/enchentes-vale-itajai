#!/usr/bin/env python3
"""
Cruza os picos de `enchentes.json` com as ocorrências oficiais do Atlas.

POR QUE EXISTE, E O QUE NÃO É
-----------------------------
Um registro do Atlas de Desastres comprova uma ocorrência municipal
reconhecida: data do decreto, COBRADE, danos, status. **Não informa nível
máximo, horário do pico nem estação.** Por isso ele é uma camada à parte —
"ocorrências oficiais" — e nunca entra na série de cotas. Este script NÃO
escreve em `enchentes.json`, `estacoes.json` nem `transito.json`; há teste
que trava isso.

CORRESPONDÊNCIA POR JANELA, NÃO POR DATA EXATA
----------------------------------------------
A `data_evento` do S2ID é o começo do desastre decretado, e a crista vem
depois (nov/2023 em Rio do Sul: Atlas 16/11, crista na virada de 17 para 18).
Então o pareamento tolera `JANELA_DIAS` para cada lado e guarda as duas datas
e a diferença, em vez de afirmar que são o mesmo dia. Classificação:

    confirmado          |diferença| <= 1 dia
    provável            |diferença| <= JANELA_DIAS
    provável (mês)      pico só com mês, e há ocorrência no mesmo mês
    sem correspondência nada dentro da janela
    sem base            pico só com ano: não dá para comparar

Cada linha da saída leva: cidade, data do pico, data do Atlas, diferença em
dias, classificação, protocolo, COBRADE, tipo, status, danos. É a decisão do
Jefferson de 21/09/2026, escrita como código.

QUE OCORRÊNCIAS ENTRAM
----------------------
12100 inundação, 12200 enxurrada, 12300 alagamento e 13214 chuvas intensas.
Vendaval, granizo, estiagem etc. não entram na camada de enchentes.

ENTRADA
-------
`data/desastres/eventos.json` (saída do `atlas_desastres.py`, lista plana) ou
um recorte no esquema por rio (`{"eventos": [{"registros": [...]}]}`), como
os recebidos em 21/09/2026. Os dois esquemas são aceitos porque o segundo é
o que existe hoje: o Atlas recusa este ambiente e a VPS.

Uso:
    python3 scripts/atlas_correspondencias.py ARQUIVO [ARQUIVO...]
    python3 scripts/atlas_correspondencias.py ARQUIVO --escrever
"""

from __future__ import annotations

import argparse
import json
import sys
import unicodedata
from datetime import date, datetime, timezone
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
DIR_SAIDA = RAIZ / "data" / "desastres"

#: Tolerância para cada lado. Cinco dias cobre o intervalo entre o decreto e
#: a crista nas cheias conhecidas (0 a 4 dias) com folga de um.
JANELA_DIAS = 5
#: Até aqui é a mesma ocorrência sem dúvida razoável.
CONFIRMADO_DIAS = 1

COBRADES_DE_ENCHENTE = {"12100", "12200", "12300", "13214"}


def sem_acento(texto: str) -> str:
    s = unicodedata.normalize("NFD", texto)
    return "".join(c for c in s if unicodedata.category(c) != "Mn").lower().strip()


def carregar_registros(caminho: Path) -> list[dict]:
    """Aceita a lista plana do nosso script ou o recorte por rio."""
    dados = json.loads(Path(caminho).read_text(encoding="utf-8"))
    brutos = dados if isinstance(dados, list) else [
        r for e in dados.get("eventos", []) for r in e.get("registros", [])]
    saida = []
    for r in brutos:
        cobrade = str(r.get("cobrade", "")).split(".")[0]
        if cobrade not in COBRADES_DE_ENCHENTE:
            continue
        saida.append({
            "protocolo": r.get("protocolo"),
            "cod_ibge": str(r.get("cod_ibge", "")),
            "municipio": r.get("municipio", ""),
            "data_evento": str(r.get("data_evento", ""))[:10],
            "cobrade": cobrade,
            "tipo": r.get("tipo") or r.get("tipologia") or "",
            "status": r.get("status", ""),
            "mortos": r.get("mortos", 0),
            "desabrigados": r.get("desabrigados", 0),
            "desalojados": r.get("desalojados", 0),
        })
    return saida


def cidades_por_nome(estacoes: dict) -> dict[str, str]:
    """nome sem acento -> id da cidade, lido do cadastro."""
    saida = {}
    for rio in estacoes["rios"].values():
        for c in rio["cidades"]:
            saida[sem_acento(c["nome"])] = c["id"]
    return saida


def data_do_pico(valor) -> tuple[date | None, str]:
    """(data, precisão): precisão é 'dia', 'mes' ou 'ano'."""
    v = str(valor)
    try:
        if len(v) == 10:
            return date.fromisoformat(v), "dia"
        if len(v) == 7:
            return date.fromisoformat(v + "-01"), "mes"
    except ValueError:
        return None, "invalida"
    return None, "ano"


def parear(picos: list[dict], registros: list[dict], nomes: dict[str, str]) -> list[dict]:
    """Uma linha por pico. Nunca altera os picos; só os descreve."""
    por_cidade: dict[str, list[dict]] = {}
    for r in registros:
        cid = nomes.get(sem_acento(r["municipio"]))
        if cid:
            por_cidade.setdefault(cid, []).append(r)

    saida = []
    for p in picos:
        cid = p.get("cidade")
        quando, precisao = data_do_pico(p.get("data"))
        linha = {"cidade": cid, "data_pico": p.get("data"), "pico_m": p.get("pico_m"),
                 "referencia": p.get("referencia"), "precisao_do_pico": precisao,
                 "classificacao": "sem base", "data_atlas": None, "diferenca_dias": None,
                 "protocolo": None, "cobrade": None, "tipo": None, "status": None,
                 "mortos": None, "desabrigados": None, "desalojados": None}
        candidatos = por_cidade.get(cid, [])
        if quando is None or not candidatos:
            if quando is not None:
                linha["classificacao"] = "sem correspondência"
            saida.append(linha)
            continue

        melhor = None
        for r in candidatos:
            try:
                d = date.fromisoformat(r["data_evento"])
            except ValueError:
                continue
            if precisao == "mes":
                if (d.year, d.month) == (quando.year, quando.month):
                    dist = 0
                else:
                    continue
            else:
                dist = abs((d - quando).days)
                if dist > JANELA_DIAS:
                    continue
            if melhor is None or dist < melhor[0]:
                melhor = (dist, d, r)

        if melhor is None:
            linha["classificacao"] = "sem correspondência"
        else:
            dist, d, r = melhor
            if precisao == "mes":
                linha["classificacao"] = "provável (mês)"
                linha["diferenca_dias"] = None
            else:
                linha["classificacao"] = "confirmado" if dist <= CONFIRMADO_DIAS else "provável"
                linha["diferenca_dias"] = (d - quando).days
            linha.update({"data_atlas": d.isoformat(), "protocolo": r["protocolo"],
                          "cobrade": r["cobrade"], "tipo": r["tipo"], "status": r["status"],
                          "mortos": r["mortos"], "desabrigados": r["desabrigados"],
                          "desalojados": r["desalojados"]})
        saida.append(linha)
    return saida


def resumo(linhas: list[dict]) -> dict[str, dict[str, int]]:
    """{cidade: {classificação: n}}."""
    out: dict[str, dict[str, int]] = {}
    for l in linhas:
        c = out.setdefault(l["cidade"], {})
        c[l["classificacao"]] = c.get(l["classificacao"], 0) + 1
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("arquivos", nargs="+", type=Path,
                    help="eventos.json do atlas_desastres.py ou recortes por rio")
    ap.add_argument("--escrever", action="store_true",
                    help="grava data/desastres/correspondencias.json")
    args = ap.parse_args()

    from comum import le_json
    registros = [r for a in args.arquivos for r in carregar_registros(a)]
    if not registros:
        sys.exit("Nenhuma ocorrência de enchente (12100/12200/12300/13214) nos arquivos.")
    picos = le_json("enchentes.json")["eventos"]
    nomes = cidades_por_nome(le_json("estacoes.json"))
    linhas = parear(picos, registros, nomes)

    print(f"{len(picos)} picos × {len(registros)} ocorrências, janela ±{JANELA_DIAS} dias\n")
    for cidade, cont in sorted(resumo(linhas).items()):
        print(f"  {cidade:<18} " + "  ".join(f"{k}: {v}" for k, v in sorted(cont.items())))

    if args.escrever:
        DIR_SAIDA.mkdir(parents=True, exist_ok=True)
        destino = DIR_SAIDA / "correspondencias.json"
        conteudo = {
            "_meta": {
                "camada": "ocorrências oficiais (Atlas de Desastres / S2ID) × picos de enchentes.json",
                "regra": "o Atlas comprova ocorrência, COBRADE, danos e reconhecimento; "
                         "NÃO informa nível, hora do pico nem estação, e não altera pico nenhum",
                "janela_dias": JANELA_DIAS,
                "confirmado_ate_dias": CONFIRMADO_DIAS,
                "cobrades": sorted(COBRADES_DE_ENCHENTE),
                "entradas": [str(a) for a in args.arquivos],
                "gerado_em": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            },
            "correspondencias": linhas,
        }
        destino.write_text(json.dumps(conteudo, ensure_ascii=False, indent=1) + "\n",
                           encoding="utf-8")
        print(f"\nGravado: {destino.relative_to(RAIZ)}")


if __name__ == "__main__":
    main()
