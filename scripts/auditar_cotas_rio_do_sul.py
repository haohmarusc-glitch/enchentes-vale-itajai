#!/usr/bin/env python3
"""
Audita as 555 cotas de rua de Rio do Sul contra o bruto guardado — SÓ LÊ.

POR QUE EXISTE (04/10/2026)
---------------------------
Decisão do Jefferson: as cotas de rua de Rio do Sul "podem voltar a receber cor
depois de conferir amostra, fonte e referência da camada atual. Até essa
revisão, manter false; não liberar cor somente porque os registros existem."
Este script é a parte reproduzível dessa revisão. O relatório com a conclusão
está em `docs/AUDITORIA-COTAS-RIO-DO-SUL-2026-10-04.md`.

CONTRA O QUÊ SE CONFERE
-----------------------
O importador (`importar_cotas_rio_do_sul.py`, 31/08/2026) leu as ruas do pacote
JavaScript do portal da Defesa Civil de Rio do Sul (`assets/index-Ds6Xl8sw.js`),
e esse pacote NÃO foi guardado no repositório. O que está guardado, com hash
no manifesto, é uma versão POSTERIOR do mesmo pacote, baixada na rodada 7 da
pesquisa externa (`assets/index-DyPsDK0O.js`, relatório gerado em 01/10/2026):

    data/brutos/pesquisa-picos-2026-09-24/rodada7/originais/
        DCRioDoSul_portal_bundle_index-DyPsDK0O.js

A tabela das ruas viaja nele como `const oo=[{name:…,min:…,max:…}, …]`. É
contra ESSE bruto que a camada atual se confere. Se o hash não bater com o
manifesto, o script para: conferir contra arquivo trocado não prova nada.

O QUE ELE FAZ
-------------
1. Fonte: confere o sha256 do pacote contra o manifesto da rodada 7.
2. Referência: procura no pacote a frase em que a fonte declara a régua das
   cotas e a tabela de correção de zero que o portal aplica a outras estações.
   Só RELATA o que está escrito; não conclui equivalência de régua.
3. Censo: compara as 555 linhas do cadastro com as 555 do bruto, campo a campo
   (cota mínima, máxima, teto de 20 m, `usar_para_aviso`, referência, bairro,
   coordenada), e procura duplicatas e valores implausíveis.
4. Amostra: sorteia 30 ruas com semente fixa e confere cada uma contra o
   pacote e contra a transcrição da NSC, linha por linha.

NÃO GRAVA NADA. Não muda `cotas_verificado`, cota nem estação: mudar isso é
decisão do Jefferson.

Uso:
    python3 scripts/auditar_cotas_rio_do_sul.py            # relatório em texto
    python3 scripts/auditar_cotas_rio_do_sul.py --json     # o mesmo, em JSON

Saída: 0 sem divergência; 2 com divergência de valor; 3 se o bruto não confere
com o hash do manifesto (ou falta).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import random
import re
import sys
import unicodedata
from pathlib import Path
from typing import Any

from comum import DADOS
from conferir_rio_do_sul_nsc import normalizar as normalizar_nsc

CIDADE = "rio-do-sul"
RIO = "itajai-acu"

RODADA7 = DADOS / "brutos" / "pesquisa-picos-2026-09-24" / "rodada7"
NOME_PACOTE = "originais/DCRioDoSul_portal_bundle_index-DyPsDK0O.js"
PACOTE = RODADA7 / NOME_PACOTE
MANIFESTO = RODADA7 / "Manifesto_SHA256.json"
NSC = DADOS / "brutos" / "rio-do-sul-nsc-2026-08-14.json"
COTAS = DADOS / "cotas-ruas.json"
ESTACOES = DADOS / "estacoes.json"
ASTHON = DADOS / "brutos" / "rio-do-sul-asthon-2026-08-31.json"

#: Semente da amostra: a data da auditoria. Mudar a semente muda a amostra, e o
#: relatório deixa de bater com o script — se mudar, refaça o relatório.
SEMENTE = 20261004
TAMANHO_AMOSTRA = 30

#: Ao centavo: os dois lados publicam duas casas.
TOLERANCIA_M = 0.005

#: A fonte marca "20,00+" como interdição total acima de 20 m: é o teto da
#: escala dela, não a cota em que a rua alaga inteira (ver o importador).
TETO_DA_FONTE = 20.0

#: Nenhuma régua desta bacia chega perto disso; acima é outra grandeza.
COTA_MAXIMA_M = 25.0

#: A frase com que o pacote declara a régua das cotas de rua.
FRASE_REGUA = "Cotas em metros na régua da Ponte Dom Tito Buss"

RE_INICIO_TABELA = "const oo=["
RE_ITEM = re.compile(
    r"\{name:`([^`]*)`,min:(null|-?\d+(?:\.\d+)?),max:(null|-?\d+(?:\.\d+)?)(,maxOpen:!0)?\}"
)
RE_CORRECOES = re.compile(r"Object\.freeze\((\{\"[0-9a-f-]{36}\":-?[\d.]+(?:,\"[0-9a-f-]{36}\":-?[\d.]+)*\})\)")
RE_PAR_CORRECAO = re.compile(r"\"([0-9a-f-]{36})\":(-?[\d.]+)")


# --------------------------------------------------------------------------
# leitura
# --------------------------------------------------------------------------

def sha256_de(caminho: Path) -> str:
    return hashlib.sha256(caminho.read_bytes()).hexdigest()


def hash_no_manifesto(manifesto: list[dict], nome: str) -> str | None:
    for item in manifesto:
        if item.get("arquivo") == nome:
            return item.get("sha256")
    return None


def chave(nome: Any) -> str:
    """Nome de rua sem acento, em caixa alta, espaços colapsados."""
    sem = unicodedata.normalize("NFD", str(nome or "")).encode("ascii", "ignore").decode()
    return " ".join(sem.upper().split())


def _numero(texto: str) -> float | None:
    return None if texto == "null" else float(texto)


def extrair_tabela(js: str) -> list[dict]:
    """
    As ruas do pacote, na ordem em que aparecem.

    Para em erro, em vez de devolver uma lista parcial, quando: a tabela não
    está lá, aparece mais de uma vez, ou algum `{name:` do trecho não casou com
    o formato — foi exatamente uma lista parcial em silêncio que fez o
    importador perder a Visconde de Cairu (`min:null`) em 31/08/2026.
    """
    if js.count(RE_INICIO_TABELA) != 1:
        raise ValueError(f"esperava uma tabela `{RE_INICIO_TABELA}` no pacote, "
                         f"achei {js.count(RE_INICIO_TABELA)}")
    inicio = js.index(RE_INICIO_TABELA) + len(RE_INICIO_TABELA) - 1
    fim = js.find("}]", inicio)
    if fim < 0:
        raise ValueError("tabela sem fim `}]`")
    trecho = js[inicio:fim + 2]
    itens = [
        {
            "rua": m.group(1),
            "min": _numero(m.group(2)),
            "max": _numero(m.group(3)),
            "max_aberto": bool(m.group(4)),
        }
        for m in RE_ITEM.finditer(trecho)
    ]
    declarados = trecho.count("{name:")
    if len(itens) != declarados:
        raise ValueError(f"{declarados} itens no trecho, {len(itens)} lidos: formato mudou")
    return itens


def declaracao_de_regua(js: str) -> str | None:
    """O trecho em que a fonte diz em que régua estão as cotas, ou None."""
    i = js.find(FRASE_REGUA)
    if i < 0:
        return None
    # Do começo da frase da legenda até o fim dela, como está no pacote.
    comeco = js.rfind("`", 0, i) + 1
    fim = js.find("`", i)
    return js[comeco:fim].strip()


def correcoes_de_zero(js: str) -> dict[str, float]:
    """A tabela `{station_id: deslocamento_m}` que o portal soma a estações."""
    m = RE_CORRECOES.search(js)
    if not m:
        return {}
    # `-.17` é número em JavaScript e não em JSON: lê par a par.
    return {k: float(v) for k, v in RE_PAR_CORRECAO.findall(m.group(1))}


def nomes_de_estacao(asthon: dict) -> dict[str, str]:
    return {e["station_id"]: e.get("name", "") for e in asthon.get("stations_list", [])
            if e.get("station_id")}


def cidade_do_cadastro(estacoes: dict) -> dict:
    for c in estacoes["rios"][RIO]["cidades"]:
        if c["id"] == CIDADE:
            return c
    raise KeyError(CIDADE)


def piso_da_cidade(cidade: dict) -> float | None:
    valores = [v for v in (cidade.get("cotas_m") or {}).values()
               if isinstance(v, (int, float)) and not isinstance(v, bool)]
    return min(valores) if valores else None


# --------------------------------------------------------------------------
# conferência
# --------------------------------------------------------------------------

def esperado(item: dict, piso: float | None) -> dict:
    """O que o importador deveria ter gravado para esta linha do bruto."""
    saida: dict[str, Any] = {"cota_m": item["min"]}
    mx = item["max"]
    if mx is not None and mx < TETO_DA_FONTE and not item["max_aberto"]:
        saida["cota_max_m"] = mx
    else:
        saida["cota_max_m"] = None
    saida["teto"] = mx is not None and (mx >= TETO_DA_FONTE or item["max_aberto"])
    saida["abaixo_do_piso"] = (piso is not None and item["min"] is not None
                               and item["min"] < piso)
    return saida


def _difere(a: float | None, b: float | None) -> bool:
    if a is None or b is None:
        return a is not b
    return abs(a - b) >= TOLERANCIA_M


def conferir_registro(reg: dict, item: dict | None, piso: float | None) -> list[str]:
    """As divergências de UMA linha do cadastro contra o bruto. Vazio = confere."""
    if item is None:
        return ["rua ausente no bruto"]
    exp = esperado(item, piso)
    problemas = []
    if _difere(reg.get("cota_m"), exp["cota_m"]):
        problemas.append(f"cota mínima: cadastro {reg.get('cota_m')} × bruto {exp['cota_m']}")
    if _difere(reg.get("cota_max_m"), exp["cota_max_m"]):
        problemas.append(f"cota máxima: cadastro {reg.get('cota_max_m')} × bruto "
                         f"{item['max']}{' (teto)' if exp['teto'] else ''}")
    if exp["teto"] and "teto da escala" not in (reg.get("nota") or ""):
        problemas.append("bruto marca o teto de 20 m e o cadastro não traz a nota")
    bloqueado = reg.get("usar_para_aviso") is False
    if exp["abaixo_do_piso"] != bloqueado:
        problemas.append(f"usar_para_aviso: esperado {'false' if exp['abaixo_do_piso'] else 'ausente'}, "
                         f"cadastro {reg.get('usar_para_aviso')}")
    if reg.get("referencia") != "régua":
        problemas.append(f"referencia {reg.get('referencia')!r}")
    return problemas


def implausiveis(itens: list[dict], piso: float | None) -> list[str]:
    """Linhas do bruto que não passam por nível de rio plausível nesta régua."""
    saida = []
    for it in itens:
        mn, mx = it["min"], it["max"]
        if mn is None:
            saida.append(f"{it['rua']}: sem cota mínima (máxima {mx})")
            continue
        if not 0 < mn < COTA_MAXIMA_M:
            saida.append(f"{it['rua']}: mínima {mn} fora de 0–{COTA_MAXIMA_M:g} m")
        if mx is not None and mx < mn:
            saida.append(f"{it['rua']}: máxima {mx} abaixo da mínima {mn}")
        if piso is not None and mn < piso:
            saida.append(f"{it['rua']}: mínima {mn} abaixo da menor cota da cidade ({piso})")
    return saida


def duplicatas(nomes: list[str]) -> list[str]:
    vistos: dict[str, int] = {}
    for n in nomes:
        vistos[chave(n)] = vistos.get(chave(n), 0) + 1
    return sorted(k for k, v in vistos.items() if v > 1)


def censo(cadastro: list[dict], itens: list[dict], piso: float | None) -> dict:
    por_chave = {chave(it["rua"]): it for it in itens}
    nomes_cad = {chave(r["rua"]) for r in cadastro}
    divergentes = []
    for r in cadastro:
        problemas = conferir_registro(r, por_chave.get(chave(r["rua"])), piso)
        if problemas:
            divergentes.append({"rua": r["rua"], "fonte": r.get("fonte", ""),
                                "problemas": problemas})
    return {
        "cadastro": len(cadastro),
        "bruto": len(itens),
        "so_no_cadastro": sorted(nomes_cad - set(por_chave)),
        "so_no_bruto": sorted(set(por_chave) - nomes_cad),
        "duplicatas_cadastro": duplicatas([r["rua"] for r in cadastro]),
        "duplicatas_bruto": duplicatas([it["rua"] for it in itens]),
        "divergentes": divergentes,
        "implausiveis": implausiveis(itens, piso),
        "com_bairro": sum(1 for r in cadastro if r.get("bairro")),
        "com_coordenada": sum(1 for r in cadastro if "lat" in r or "lon" in r),
        "teto_no_bruto": sum(1 for it in itens if it["max_aberto"]),
    }


def sortear(cadastro: list[dict], semente: int = SEMENTE,
            n: int = TAMANHO_AMOSTRA) -> list[dict]:
    """Amostra reprodutível: ordena pela chave do nome e sorteia com semente fixa."""
    ordenado = sorted(cadastro, key=lambda r: chave(r["rua"]))
    return random.Random(semente).sample(ordenado, min(n, len(ordenado)))


def linhas_da_amostra(amostra: list[dict], itens: list[dict], nsc: list[dict],
                      piso: float | None) -> list[dict]:
    por_chave = {chave(it["rua"]): it for it in itens}
    nsc_por_rua = {normalizar_nsc(r.get("rua")): r.get("cota_minima_m") for r in nsc}
    saida = []
    for r in amostra:
        item = por_chave.get(chave(r["rua"]))
        problemas = conferir_registro(r, item, piso)
        nsc_min = nsc_por_rua.get(normalizar_nsc(r["rua"]))
        if nsc_min is not None and _difere(r.get("cota_m"), nsc_min):
            problemas.append(f"NSC publica mínima {nsc_min}")
        saida.append({
            "rua": r["rua"],
            "cad_min": r.get("cota_m"),
            "cad_max": r.get("cota_max_m"),
            "bruto_min": item["min"] if item else None,
            "bruto_max": item["max"] if item else None,
            "teto": bool(item and item["max_aberto"]),
            "nsc_min": nsc_min,
            "bairro": r.get("bairro"),
            "coordenada": ("lat" in r and "lon" in r),
            "resultado": "confere" if not problemas else "DIVERGE",
            "problemas": problemas,
        })
    return saida


# --------------------------------------------------------------------------
# relatório
# --------------------------------------------------------------------------

def auditar() -> dict:
    manifesto = json.loads(MANIFESTO.read_text(encoding="utf-8"))
    esperado_sha = hash_no_manifesto(manifesto, NOME_PACOTE)
    if not PACOTE.exists():
        return {"erro": f"pacote ausente: {PACOTE}"}
    sha = sha256_de(PACOTE)
    if sha != esperado_sha:
        return {"erro": f"sha256 do pacote {sha} não é o do manifesto {esperado_sha}"}

    js = PACOTE.read_text(encoding="utf-8")
    itens = extrair_tabela(js)
    cidade = cidade_do_cadastro(json.loads(ESTACOES.read_text(encoding="utf-8")))
    piso = piso_da_cidade(cidade)
    cadastro = [r for r in json.loads(COTAS.read_text(encoding="utf-8"))["cotas"]
                if r.get("cidade") == CIDADE]
    nsc = json.loads(NSC.read_text(encoding="utf-8"))["cotas"]
    asthon = json.loads(ASTHON.read_text(encoding="utf-8"))
    nomes = nomes_de_estacao(asthon)
    correcoes = {k: {"deslocamento_m": v, "estacao": nomes.get(k)}
                 for k, v in correcoes_de_zero(js).items()}

    return {
        "fonte": {
            "pacote": str(PACOTE.relative_to(DADOS.parent)),
            "sha256": sha,
            "sha256_manifesto": esperado_sha,
            "nsc": str(NSC.relative_to(DADOS.parent)),
            "nsc_sha256": sha256_de(NSC),
        },
        "referencia": {
            "declaracao_no_pacote": declaracao_de_regua(js),
            "correcoes_de_zero_no_pacote": correcoes,
            "regua_no_cadastro": cidade.get("regua"),
            "regua_das_cotas_no_cadastro": cidade.get("regua_das_cotas"),
            "cotas_verificado": cidade.get("cotas_verificado"),
            "piso_da_cidade_m": piso,
        },
        "censo": censo(cadastro, itens, piso),
        "amostra": {
            "semente": SEMENTE,
            "tamanho": TAMANHO_AMOSTRA,
            "linhas": linhas_da_amostra(sortear(cadastro), itens, nsc, piso),
        },
    }


def _m(v: float | None) -> str:
    return "—" if v is None else f"{v:.2f}".replace(".", ",")


def imprimir(rel: dict) -> None:
    f, ref, c, a = rel["fonte"], rel["referencia"], rel["censo"], rel["amostra"]
    print("FONTE")
    print(f"  pacote: {f['pacote']}")
    print(f"  sha256: {f['sha256']} (manifesto: {'confere' if f['sha256'] == f['sha256_manifesto'] else 'NÃO confere'})")
    print(f"  NSC:    {f['nsc']} sha256 {f['nsc_sha256']}")
    print("\nREFERÊNCIA (só o que está escrito)")
    print(f"  pacote diz: {ref['declaracao_no_pacote']!r}")
    for sid, d in ref["correcoes_de_zero_no_pacote"].items():
        print(f"  pacote soma {d['deslocamento_m']:+.2f} m à estação {sid} ({d['estacao']})")
    print(f"  cadastro: regua={ref['regua_no_cadastro']!r} regua_das_cotas={ref['regua_das_cotas_no_cadastro']!r} "
          f"cotas_verificado={ref['cotas_verificado']}")
    print("\nCENSO")
    print(f"  cadastro {c['cadastro']} · bruto {c['bruto']} · só no cadastro {len(c['so_no_cadastro'])} "
          f"· só no bruto {len(c['so_no_bruto'])}")
    print(f"  duplicatas: cadastro {c['duplicatas_cadastro'] or 'nenhuma'} · bruto {c['duplicatas_bruto'] or 'nenhuma'}")
    print(f"  com bairro: {c['com_bairro']} · com coordenada: {c['com_coordenada']} · teto 20 m no bruto: {c['teto_no_bruto']}")
    print(f"  divergentes: {len(c['divergentes'])}")
    for d in c["divergentes"]:
        print(f"    {d['rua']}: {'; '.join(d['problemas'])}")
    print(f"  implausíveis no bruto: {len(c['implausiveis'])}")
    for t in c["implausiveis"]:
        print(f"    {t}")
    print(f"\nAMOSTRA (semente {a['semente']}, {len(a['linhas'])} ruas)")
    print("| # | Rua | Cadastro mín/máx | Bruto mín/máx | NSC mín | Bairro | Coord. | Resultado |")
    print("|---|---|---|---|---|---|---|---|")
    for i, l in enumerate(a["linhas"], 1):
        bruto_max = "20,00+" if l["teto"] else _m(l["bruto_max"])
        res = l["resultado"] + (f" — {'; '.join(l['problemas'])}" if l["problemas"] else "")
        print(f"| {i} | {l['rua']} | {_m(l['cad_min'])} / {_m(l['cad_max'])} | "
              f"{_m(l['bruto_min'])} / {bruto_max} | {_m(l['nsc_min'])} | "
              f"{l['bairro'] or '—'} | {'sim' if l['coordenada'] else 'não'} | {res} |")
    ok = sum(1 for l in a["linhas"] if l["resultado"] == "confere")
    print(f"\n{ok} de {len(a['linhas'])} conferem.")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    ap.add_argument("--json", action="store_true", help="saída em JSON")
    args = ap.parse_args()

    rel = auditar()
    if "erro" in rel:
        print(rel["erro"], file=sys.stderr)
        return 3
    if args.json:
        print(json.dumps(rel, ensure_ascii=False, indent=2))
    else:
        imprimir(rel)
    divergiu = rel["censo"]["divergentes"] or any(
        l["resultado"] != "confere" for l in rel["amostra"]["linhas"])
    return 2 if divergiu else 0


if __name__ == "__main__":
    raise SystemExit(main())
