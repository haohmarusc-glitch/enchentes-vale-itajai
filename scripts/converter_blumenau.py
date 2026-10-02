"""Proposta de conversão da série de Blumenau para a régua de hoje (SIMULAÇÃO).

Não grava nada em `data/enchentes.json`. Lê os registros de Blumenau, decide em
que referência cada um foi PUBLICADO e quanto somar para chegar à régua de hoje,
e escreve o relatório `docs/CONVERSAO-BLUMENAU.md` para o Jefferson decidir.

As três referências, pela fonte (Prof. Ademar Cordero, FURB, e-mails e planilha
de 02/10/2026; `docs/fontes-academicas.md`):

    régua antiga (até a troca, depois de set/2011)    = R
    zero do IBGE (Tabela 4, 1852–2001)                = R + 0,20 m
    GPS = régua de hoje (pilar da ponte, AlertaBlu)   = R + 0,40 m

Logo, para chegar à régua de hoje: IBGE + 0,20 m; régua antiga + 0,40 m;
régua nova + 0. A troca ficou entre set/2011 e set/2013 (data exata não
lembrada pela fonte; a planilha marca 2013).

Como cada registro é classificado — e com que certeza:

* Em 1929–1983, todo registro cujo valor convertido não bate com a coluna "régua nova" da
  planilha do Cordero vira `disputada`: a Tabela 4 e a planilha discordam nesse trecho.
* `referencia == "IBGE (régua + 0,20 m)"` → IBGE (+0,20). Certeza: alta (a FURB
  confirmou que a Tabela 4 é IBGE).
* `referencia == "régua"`, de 2014 em diante → régua de hoje (+0). Alta.
* `referencia is None`:
  - até 2001, com o mesmo valor na lista do AlertaBlu → IBGE (+0,20). Alta: até
    2001 a lista reproduz a Tabela 4 ao centavo (58 pares).
  - até 2001, sem par na lista → IBGE (+0,20), INFERIDO (mesma família de fonte).
  - de 2002 até a cheia de set/2011, com o valor da lista → régua antiga
    (+0,40). Alta: 2008 e 2011 batem com a planilha (IBGE − 0,20) e a FURB deu
    12,60 m "na régua" para 2011.
  - nesse trecho, sem par na lista → régua antiga (+0,40), INFERIDO.
  - 09/09/2011 = 12,80 m (CEOPS/Esboços) → IBGE (+0,20). Alta (FURB: 12,80 IBGE).
  - entre set/2011 e set/2013 → PENDENTE: cai na janela da troca.
  - de 2014 em diante, com o valor da lista → régua de hoje (+0). Alta.
  - de 2014 em diante, sem par (imprensa, monitoramento estadual) → PENDENTE:
    a fonte não diz de qual régua é.

Uso: python3 converter_blumenau.py   (escreve o relatório e imprime o resumo)
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import conferir_blumenau_alertablu as alertablu

RAIZ = Path(__file__).resolve().parent.parent
DADOS = RAIZ / "data"
RELATORIO = RAIZ / "docs" / "CONVERSAO-BLUMENAU.md"
PLANILHA = DADOS / "brutos" / "furb-cordero-2026-10-02" / "transcricao.tsv"
# Trecho em que a planilha do Cordero e a Tabela 4 publicada discordam em ~0,20–0,30 m
# (docs/fontes-academicas.md). Nele, só converte com certeza o que a planilha confirma.
DISPUTA = ("1929", "1983")

ROTULO_IBGE = "IBGE (régua + 0,20 m)"
SOMA = {"IBGE": 0.20, "régua antiga": 0.40, "régua de hoje": 0.0}
FIM_REGUA_ANTIGA = "2011-09-30"  # depois da cheia de 09/09/2011
INICIO_REGUA_NOVA = "2014-01-01"  # 2013 inteiro fica na janela da troca


def lista_alertablu() -> dict[str, float]:
    """Data ISO → cota da lista "Enchentes Registradas" (HTML guardado)."""
    texto = (alertablu.DADOS / alertablu.BRUTO_HTML).read_text(encoding="utf-8", errors="replace")
    return {f"{e['ano']}-{e['mes']}-{e['dia']}": e["cota_m"] for e in alertablu.eventos_do_html(texto)}


def planilha_gps() -> dict[str, float]:
    """Data ISO → coluna "IBGE-GPS (Régua Nova)" da planilha do Cordero (ano da coluna B)."""
    gps = {}
    for linha in PLANILHA.read_text(encoding="utf-8").splitlines()[1:]:
        _n, ano, dia_mes, _ibge, g, _obs, _bruta = linha.split("\t")
        dia, mes = dia_mes.split("/")
        gps[f"{ano}-{mes}-{dia}"] = float(g)
    return gps


def classificar(e: dict, lista: dict[str, float]) -> dict:
    """Decide a referência publicada de um registro e quanto somar.

    Devolve: referencia_publicada (chave de SOMA, ou None quando pendente),
    certeza ('alta' | 'inferida' | 'pendente') e o motivo, em português.
    """
    data, ref, v = e["data"], e.get("referencia", "<ausente>"), e["pico_m"]
    na_lista = lista.get(data)
    bate = na_lista is not None and abs(na_lista - v) < 0.005

    if ref == ROTULO_IBGE:
        return _r("IBGE", "alta", "rotulado IBGE (Tabela 4); a FURB confirmou")
    if ref == "régua":
        if data >= INICIO_REGUA_NOVA:
            return _r("régua de hoje", "alta", "leitura de régua depois da troca")
        return _r(None, "pendente", "rotulado régua, mas antes de 2014: qual régua?")
    if ref is not None:
        return _r(None, "pendente", f"referência inesperada: {ref!r}")

    if data[:10] == "2011-09-09" and abs(v - 12.80) < 0.005:
        return _r("IBGE", "alta", "12,80 m = IBGE pela FURB (12,60 régua · 12,80 IBGE · 13,00 GPS)")
    if data < "2002":
        if bate:
            return _r("IBGE", "alta", "mesmo valor da lista do AlertaBlu, que até 2001 é a Tabela 4")
        return _r("IBGE", "inferida", "sem par na lista; mesma família de fonte (até 2001 = IBGE)")
    if data <= FIM_REGUA_ANTIGA:
        if bate:
            return _r("régua antiga", "alta", "mesmo valor da lista, que em 2008–2011 está na régua antiga")
        return _r("régua antiga", "inferida", "sem par na lista; trecho em que a lista usa a régua antiga")
    if data < INICIO_REGUA_NOVA:
        return _r(None, "pendente", "cai na janela da troca de régua (set/2011 a 2013)")
    if bate:
        return _r("régua de hoje", "alta", "mesmo valor da lista, que de 2014 em diante está na régua nova")
    return _r(None, "pendente", "fonte não diz a régua (imprensa ou rede estadual)")


def _r(referencia: str | None, certeza: str, motivo: str) -> dict:
    return {"referencia_publicada": referencia, "certeza": certeza, "motivo": motivo}


def proposta(eventos: list[dict], lista: dict[str, float], gps: dict[str, float] | None = None) -> list[dict]:
    gps = gps or {}
    linhas = []
    for e in sorted((x for x in eventos if x["cidade"] == "blumenau"), key=lambda x: x["data"]):
        c = classificar(e, lista)
        ref = c["referencia_publicada"]
        novo = None if ref is None else round(e["pico_m"] + SOMA[ref], 2)
        na_planilha = gps.get(e["data"])
        confirma = na_planilha is not None and novo is not None and abs(na_planilha - novo) < 0.005
        if DISPUTA[0] <= e["data"][:4] <= DISPUTA[1] and novo is not None and not confirma:
            c = {**c, "certeza": "disputada",
                 "motivo": c["motivo"] + "; mas a planilha do Cordero dá outro valor (ou não tem a data) neste trecho"}
        linhas.append({"data": e["data"], "publicado": e["pico_m"], "rotulo_atual": e.get("referencia", "<ausente>"),
                       "na_lista": lista.get(e["data"]), "na_planilha": na_planilha, "novo": novo, **c,
                       "divergencias": [d["pico_m"] for d in e.get("divergencias", [])],
                       "fonte": e["fonte"]})
    return linhas


def _m(v: float | None) -> str:
    return "—" if v is None else f"{v:.2f}".replace(".", ",")


def relatorio(linhas: list[dict]) -> str:
    from collections import Counter
    n = Counter((l["referencia_publicada"] or "pendente", l["certeza"]) for l in linhas)
    out = [
        "# Conversão da série de Blumenau para a régua de hoje — PROPOSTA",
        "",
        "> **Simulação. Nada foi gravado em `data/enchentes.json`.** Gerado por `scripts/converter_blumenau.py`.",
        "> A regra bloqueante continua valendo até o Jefferson aprovar a conversão.",
        "",
        "Régua de hoje = GPS = IBGE + 0,20 m = régua antiga + 0,40 m (Prof. Cordero, FURB, 02/10/2026).",
        "",
        "## Resumo",
        "",
        "| Referência publicada | Soma | Certeza | Registros |",
        "|---|---|---|---|",
    ]
    for (ref, cer), q in sorted(n.items()):
        soma = "—" if ref == "pendente" else _m(SOMA[ref]).replace("0,00", "0") + " m"
        out.append(f"| {ref} | {soma} | {cer} | {q} |")
    out += ["", f"Total: {len(linhas)} registros.", "",
            "## Em disputa: Tabela 4 × planilha do Cordero (1929–1983)", "",
            "Neste trecho a Tabela 4 publicada (e a lista do AlertaBlu) fica quase sempre 0,20–0,31 m acima da coluna",
            "IBGE da planilha que o Prof. Cordero enviou. Em vários casos o valor publicado é IGUAL à coluna \"régua nova\"",
            "da planilha (ex.: 02/08/1957, 10,60 m). Se a planilha estiver certa, somar 0,20 m aqui superestima a cheia em",
            "~0,20–0,25 m. Por isso estes registros ficam marcados até a FURB dizer qual das duas vale.", "",
            "| Data | Publicado | +0,20 (proposta) | Planilha, régua nova |", "|---|---|---|---|"]
    for l in linhas:
        if l["certeza"] == "disputada":
            out.append(f"| {l['data']} | {_m(l['publicado'])} | {_m(l['novo'])} | {_m(l['na_planilha'])} |")
    out += ["",
            "## Pendentes e inferidos (precisam de decisão)", "",
            "| Data | Publicado | Rótulo atual | Lista AlertaBlu | Proposta | Motivo |",
            "|---|---|---|---|---|---|"]
    for l in linhas:
        if l["certeza"] in ("inferida", "pendente"):
            out.append(f"| {l['data']} | {_m(l['publicado'])} | {l['rotulo_atual']} | {_m(l['na_lista'])} | "
                       f"{_m(l['novo'])} ({l['certeza']}) | {l['motivo']} |")
    out += ["", "## O que muda além dos números (quando aplicar)", "",
            "* **Modelo do registro:** `pico_m` passa a ser a régua de hoje e `referencia` vira `\"régua\"`. O valor como foi",
            "  publicado fica em `pico_publicado_m`, com `referencia_publicada` e a fonte da conversão (FURB, 02/10/2026).",
            "  A tela mostra os dois: \"15,54 m na régua de hoje (publicado como 15,34 m, zero do IBGE)\".",
            "* **Divergências:** cada valor guardado é convertido pela referência da fonte dele (ex.: 13,00 m de set/2011",
            "  já é GPS e fica igual ao adotado).",
            "* **Regra bloqueante:** sai `_meta.REGRA_REFERENCIA_BLUMENAU`; `aviso_blumenau`, o validador e o `CLAUDE.md`",
            "  são atualizados no mesmo commit, com a decisão registrada em `docs/fontes-academicas.md`.",
            "* **Site:** Blumenau passa a comparar o nível de hoje com as cheias antigas (painel \"e isso é muito?\",",
            "  previsão a jusante). O teste que trava \"Blumenau nunca produz distância\" é trocado por um que confere a",
            "  comparação na régua de hoje.",
            "* **Ainda sem referência confirmada:** `_meta.periodos_retorno_blumenau_m` (Tabela 5, \"nível na régua\",",
            "  série 1852–2002) e `_meta.curva_chave_blumenau` (H \"na régua\"). Nenhum dos dois é lido pelo site hoje;",
            "  ficam como estão, com nota.",
            "* **Bot e arquivos gerados:** textos com 15,34 m / 15,46 m revistos; `data/desastres/correspondencias.json`",
            "  regerado pelo script dele.",
            "", "## Todos os registros", "",
            "| Data | Publicado | Referência publicada | Régua de hoje | Planilha (régua nova) | Certeza | Divergências guardadas |",
            "|---|---|---|---|---|---|---|"]
    for l in linhas:
        div = ", ".join(_m(x) for x in l["divergencias"]) or ""
        out.append(f"| {l['data']} | {_m(l['publicado'])} | {l['referencia_publicada'] or 'pendente'} | "
                   f"{_m(l['novo'])} | {_m(l['na_planilha'])} | {l['certeza']} | {div} |")
    return "\n".join(out) + "\n"


def main() -> int:
    eventos = json.loads((DADOS / "enchentes.json").read_text(encoding="utf-8"))["eventos"]
    linhas = proposta(eventos, lista_alertablu(), planilha_gps())
    RELATORIO.write_text(relatorio(linhas), encoding="utf-8")
    from collections import Counter
    print(Counter((l["referencia_publicada"] or "pendente", l["certeza"]) for l in linhas))
    print(f"relatório: {RELATORIO.relative_to(RAIZ)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
