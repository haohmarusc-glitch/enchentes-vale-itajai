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
    divergente          há ocorrência na mesma cidade entre 6 e DIVERGENTE_DIAS
                        dias do pico: episódio próximo cujas datas NÃO fecham;
                        pede olho humano, nunca vira par
    sem correspondência pico dentro da cobertura do Atlas e nada por perto
    fora da cobertura   pico anterior a 1991 (ou posterior ao fim da base):
                        o Atlas não pode confirmar nem negar — jul/1983 é isto
    sem base            pico só com ano dentro da cobertura: não dá para comparar

Quando mais de uma ocorrência cabe na janela (set/2011 em Rio do Sul tem uma
enxurrada em 08/09 e uma inundação reconhecida em 12/09), a linha leva a mais
próxima e guarda as outras em `outras_no_periodo` — nenhuma é descartada.

O CAMINHO INVERSO: LACUNAS
--------------------------
Ocorrência oficial sem pico cadastrado por perto é **candidata a
investigação** (onde procurar boletim com régua), nunca registro. Sai em
`lacunas`, por cidade. Pico sem ocorrência no Atlas continua pico: a linha
diz "sem correspondência" e nada mais.

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
#: Além da janela e até aqui, "divergente": perto demais para ignorar, longe
#: demais para afirmar. Um mês cobre decreto tardio e cheia dupla no mesmo mês.
DIVERGENTE_DIAS = 30
#: Cobertura da base consolidada v1.1. O recorte por rio declara a sua em
#: `periodo`; quando declara, ela vale.
COBERTURA_PADRAO = (1991, 2025)

COBRADES_DE_ENCHENTE = {"12100", "12200", "12300", "13214"}


def sem_acento(texto: str) -> str:
    s = unicodedata.normalize("NFD", texto)
    return "".join(c for c in s if unicodedata.category(c) != "Mn").lower().strip()


def cobertura_de(caminho: Path) -> tuple[int, int]:
    """Anos (início, fim) que a entrada declara cobrir; o padrão é o da v1.1."""
    dados = json.loads(Path(caminho).read_text(encoding="utf-8"))
    periodo = dados.get("periodo") if isinstance(dados, dict) else None
    if isinstance(periodo, str) and len(periodo) == 9 and periodo[4] == "-":
        return int(periodo[:4]), int(periodo[5:])
    return COBERTURA_PADRAO


def filtro_de(caminho: Path) -> str | None:
    """O filtro que o recorte diz ter aplicado (ex.: 'Cobrade 12xxx'); None na lista plana."""
    dados = json.loads(Path(caminho).read_text(encoding="utf-8"))
    return dados.get("filtro") if isinstance(dados, dict) else None


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


def ano_do_pico(valor) -> int | None:
    v = str(valor)
    return int(v[:4]) if len(v) >= 4 and v[:4].isdigit() else None


def _resumo_da_ocorrencia(r: dict, d: date) -> dict:
    return {"data_atlas": d.isoformat(), "protocolo": r["protocolo"], "cobrade": r["cobrade"],
            "tipo": r["tipo"], "status": r["status"]}


def parear(picos: list[dict], registros: list[dict], nomes: dict[str, str],
           cobertura: tuple[int, int] = COBERTURA_PADRAO) -> list[dict]:
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
        ano = ano_do_pico(p.get("data"))
        dentro = ano is not None and cobertura[0] <= ano <= cobertura[1]
        linha = {"cidade": cid, "data_pico": p.get("data"), "pico_m": p.get("pico_m"),
                 "referencia": p.get("referencia"), "precisao_do_pico": precisao,
                 "classificacao": "sem base", "data_atlas": None, "diferenca_dias": None,
                 "protocolo": None, "cobrade": None, "tipo": None, "status": None,
                 "mortos": None, "desabrigados": None, "desalojados": None,
                 "outras_no_periodo": []}
        candidatos = por_cidade.get(cid, [])

        if quando is None:
            # só ano (ou data inválida): não dá para comparar, mas dá para dizer
            # se o Atlas poderia ter algo
            if ano is not None and not dentro:
                linha["classificacao"] = "fora da cobertura"
            saida.append(linha)
            continue

        na_janela: list[tuple[int, date, dict]] = []
        proxima: tuple[int, date, dict] | None = None
        for r in candidatos:
            try:
                d = date.fromisoformat(r["data_evento"])
            except ValueError:
                continue
            if precisao == "mes":
                if (d.year, d.month) == (quando.year, quando.month):
                    na_janela.append((0, d, r))
                continue
            dist = abs((d - quando).days)
            if dist <= JANELA_DIAS:
                na_janela.append((dist, d, r))
            elif dist <= DIVERGENTE_DIAS and (proxima is None or dist < proxima[0]):
                proxima = (dist, d, r)

        if na_janela:
            na_janela.sort(key=lambda t: (t[0], t[1]))
            dist, d, r = na_janela[0]
            if precisao == "mes":
                linha["classificacao"] = "provável (mês)"
            else:
                linha["classificacao"] = "confirmado" if dist <= CONFIRMADO_DIAS else "provável"
                linha["diferenca_dias"] = (d - quando).days
            linha.update(_resumo_da_ocorrencia(r, d))
            linha.update({"mortos": r["mortos"], "desabrigados": r["desabrigados"],
                          "desalojados": r["desalojados"]})
            linha["outras_no_periodo"] = [_resumo_da_ocorrencia(r2, d2)
                                          for _, d2, r2 in na_janela[1:]]
        elif not dentro:
            linha["classificacao"] = "fora da cobertura"
        elif proxima is not None:
            dist, d, r = proxima
            linha["classificacao"] = "divergente"
            linha["diferenca_dias"] = (d - quando).days
            linha.update(_resumo_da_ocorrencia(r, d))
        else:
            linha["classificacao"] = "sem correspondência"
        saida.append(linha)
    return saida


def lacunas(picos: list[dict], registros: list[dict], nomes: dict[str, str]) -> list[dict]:
    """
    Ocorrências oficiais em cidade do cadastro sem pico por perto.

    "Por perto" segue a precisão de cada pico: dia dentro de ±JANELA_DIAS,
    mês igual, ano igual. É lista de onde PROCURAR nível, não de nível.
    """
    picos_por_cidade: dict[str, list[tuple[date | None, str, int | None]]] = {}
    for p in picos:
        quando, precisao = data_do_pico(p.get("data"))
        picos_por_cidade.setdefault(p.get("cidade"), []).append(
            (quando, precisao, ano_do_pico(p.get("data"))))

    saida = []
    for r in registros:
        cid = nomes.get(sem_acento(r["municipio"]))
        if not cid:
            continue
        try:
            d = date.fromisoformat(r["data_evento"])
        except ValueError:
            continue
        coberta = False
        for quando, precisao, ano in picos_por_cidade.get(cid, []):
            if precisao == "dia" and quando and abs((d - quando).days) <= JANELA_DIAS:
                coberta = True
            elif precisao == "mes" and quando and (d.year, d.month) == (quando.year, quando.month):
                coberta = True
            elif precisao == "ano" and ano == d.year:
                coberta = True
            if coberta:
                break
        if not coberta:
            saida.append({"cidade": cid, **_resumo_da_ocorrencia(r, d),
                          "mortos": r["mortos"], "desabrigados": r["desabrigados"],
                          "desalojados": r["desalojados"],
                          "leitura": "ocorrência oficial sem pico cadastrado por perto: "
                                     "onde procurar boletim com régua, não registro"})
    saida.sort(key=lambda l: (l["cidade"], l["data_atlas"]))
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
    coberturas = {cobertura_de(a) for a in args.arquivos}
    cobertura = (min(c[0] for c in coberturas), max(c[1] for c in coberturas))
    filtros = sorted({f for a in args.arquivos if (f := filtro_de(a))})
    picos = le_json("enchentes.json")["eventos"]
    nomes = cidades_por_nome(le_json("estacoes.json"))
    linhas = parear(picos, registros, nomes, cobertura)
    faltam = lacunas(picos, registros, nomes)

    print(f"{len(picos)} picos × {len(registros)} ocorrências, janela ±{JANELA_DIAS} dias, "
          f"cobertura {cobertura[0]}–{cobertura[1]}"
          + (f", filtro das entradas: {'; '.join(filtros)}" if filtros else "") + "\n")
    for cidade, cont in sorted(resumo(linhas).items()):
        print(f"  {cidade:<18} " + "  ".join(f"{k}: {v}" for k, v in sorted(cont.items())))
    por_cidade: dict[str, int] = {}
    for l in faltam:
        por_cidade[l["cidade"]] = por_cidade.get(l["cidade"], 0) + 1
    print(f"\nLacunas (ocorrência oficial sem pico por perto): {len(faltam)}")
    for cidade, n in sorted(por_cidade.items()):
        print(f"  {cidade:<18} {n}")

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
                "divergente_ate_dias": DIVERGENTE_DIAS,
                "cobertura": {"inicio": cobertura[0], "fim": cobertura[1]},
                "classificacoes": ["confirmado", "provável", "provável (mês)", "divergente",
                                   "sem correspondência", "fora da cobertura", "sem base"],
                "cobrades": sorted(COBRADES_DE_ENCHENTE),
                "entradas": [str(a) for a in args.arquivos],
                "filtro_das_entradas": filtros,
                "gerado_em": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            },
            "correspondencias": linhas,
            "lacunas": faltam,
        }
        destino.write_text(json.dumps(conteudo, ensure_ascii=False, indent=1) + "\n",
                           encoding="utf-8")
        print(f"\nGravado: {destino.relative_to(RAIZ)}")


if __name__ == "__main__":
    main()
