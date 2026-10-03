"""Conversão da série de Blumenau para a régua de hoje.

Sem argumento, é simulação: não grava nada em `data/enchentes.json`. Lê os
registros de Blumenau, decide em que referência cada um foi PUBLICADO e quanto
somar para chegar à régua de hoje, e escreve o relatório `docs/CONVERSAO-BLUMENAU.md`.
Com `--aplicar`, grava só os de certeza alta (ver o fim desta docstring).

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

Uso:
    python3 converter_blumenau.py            simulação: escreve o relatório e imprime o resumo
    python3 converter_blumenau.py --aplicar  grava em enchentes.json SÓ os de certeza `alta`

APLICADO em 03/10/2026, por decisão do Jefferson, aos 57 registros de certeza alta. Os
outros 67 (60 em disputa, 4 inferidos, 3 pendentes) ficam como estavam. O registro
convertido guarda o valor como foi publicado (`pico_publicado_m`) e em que referência
(`referencia_publicada`); `pico_m` passa a ser a régua de hoje e `referencia`, "régua".
Rodar de novo não soma duas vezes: registro com `referencia_publicada` é pulado.
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

#: Como `referencia_publicada` fica gravado. Conjunto fechado (o validador confere).
ROTULO_PUBLICADO = {"IBGE": ROTULO_IBGE, "régua antiga": "régua antiga", "régua de hoje": "régua de hoje"}
DE_ROTULO = {v: k for k, v in ROTULO_PUBLICADO.items()}

#: Referência de cada divergência guardada nos registros convertidos, quando a fonte
#: permite dizer. As demais ficam `null` (não declarada) e são mostradas como publicadas.
REFERENCIA_DA_DIVERGENCIA = {
    ("1977-08-18", 9.15): ROTULO_IBGE,         # lista do AlertaBlu, que até 2001 é a Tabela 4
    ("2011-09-09", 13.0): "régua de hoje",     # CEOPS/ABRH, 13,00 m = GPS (FURB)
    ("2011-09-09", 12.6): "régua antiga",      # Defesa Civil, 12,60 m "na régua" (FURB)
}

DATA_DA_CONVERSAO = "03/10/2026"
NOME_DA_REFERENCIA = {"IBGE": "referência do IBGE", "régua antiga": "régua antiga", "régua de hoje": "régua de hoje"}


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
    if "referencia_publicada" in e:
        return _r(DE_ROTULO.get(e["referencia_publicada"]), "convertido", f"já convertido em {DATA_DA_CONVERSAO}")
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
        if c["certeza"] == "convertido":
            linhas.append({"data": e["data"], "publicado": e.get("pico_publicado_m", e["pico_m"]),
                           "rotulo_atual": e["referencia"], "na_lista": lista.get(e["data"]),
                           "na_planilha": gps.get(e["data"]), "novo": e["pico_m"], **c,
                           "divergencias": [d["pico_m"] for d in e.get("divergencias", [])], "fonte": e["fonte"]})
            continue
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
    convertidos = sum(1 for l in linhas if l["certeza"] == "convertido")
    if convertidos:
        cabecalho = [
            "# Conversão da série de Blumenau para a régua de hoje",
            "",
            f"> **Aplicada em {DATA_DA_CONVERSAO} a {convertidos} registros** (certeza alta), por decisão do Jefferson,",
            "> com `scripts/converter_blumenau.py --aplicar`. Os demais ficam como publicados e fora da comparação",
            "> com o nível de agora. A regra bloqueante continua para eles.",
        ]
    else:
        cabecalho = [
            "# Conversão da série de Blumenau para a régua de hoje — PROPOSTA",
            "",
            "> **Simulação. Nada foi gravado em `data/enchentes.json`.** Gerado por `scripts/converter_blumenau.py`.",
            "> A regra bloqueante continua valendo até o Jefferson aprovar a conversão.",
        ]
    out = [
        *cabecalho,
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


def _texto_conversao(publicado: float, ref: str, ja_regua: bool = False) -> str:
    soma = SOMA[ref]
    fonte = ("Fonte: Prof. Ademar Cordero (FURB), e-mails e planilha de 02/10/2026: régua antiga + 0,20 m = IBGE; "
             "IBGE + 0,20 m = GPS = régua de hoje. Ver docs/CONVERSAO-BLUMENAU.md.")
    if ja_regua:
        return (f"Rótulo conferido em {DATA_DA_CONVERSAO}: leitura posterior à troca de régua, logo já na régua de "
                f"hoje; nada somado. {fonte}")
    if soma == 0:
        return (f"Rótulo definido em {DATA_DA_CONVERSAO}, por decisão do Jefferson: o valor já está na régua de hoje "
                f"(a lista do AlertaBlu de 2014 em diante está na régua nova). {fonte}")
    return (f"Convertido em {DATA_DA_CONVERSAO} para a régua de hoje, por decisão do Jefferson: publicado como "
            f"{_m(publicado)} m na {NOME_DA_REFERENCIA[ref]}, + {_m(soma)} m. {fonte}")


def converter_registro(e: dict, ref: str) -> dict:
    """Devolve o registro na régua de hoje, guardando o valor como foi publicado."""
    soma = SOMA[ref]
    novo: dict = {}
    confirmam: list[dict] = []
    for k, v in e.items():
        if k == "pico_m":
            novo["pico_m"] = round(v + soma, 2)
            if soma:
                novo["pico_publicado_m"] = v
        elif k == "referencia":
            novo["referencia"] = "régua"
            novo["referencia_publicada"] = ROTULO_PUBLICADO[ref]
        elif k == "divergencias":
            # Uma divergência que, convertido o adotado, ficou IGUAL a ele deixa de ser
            # divergência: é outra fonte confirmando o mesmo número na régua de hoje.
            novo_pico = round(e["pico_m"] + soma, 2)
            restam = [d for d in v if abs(d["pico_m"] - novo_pico) >= 0.005]
            confirmam.extend(d for d in v if abs(d["pico_m"] - novo_pico) < 0.005)
            if restam:
                novo["divergencias"] = [
                    {**d, "referencia_publicada": REFERENCIA_DA_DIVERGENCIA.get((e["data"], d["pico_m"]))}
                    for d in restam]
        else:
            novo[k] = v
    texto = _texto_conversao(e["pico_m"], ref, ja_regua=e.get("referencia") == "régua")
    for d in confirmam:
        texto += (f" Confere com {_m(d['pico_m'])} m de outra fonte (antes guardado como divergência): "
                  f"{d['fonte']}.")
    novo["conversao"] = texto
    return novo


def aplicar(dados: dict, lista: dict[str, float], gps: dict[str, float]) -> int:
    """Converte em `dados` (no lugar) só os registros de certeza `alta`. Devolve quantos."""
    alvo = {(l["data"], l["publicado"]): l["referencia_publicada"]
            for l in proposta(dados["eventos"], lista, gps) if l["certeza"] == "alta"}
    n = 0
    for i, e in enumerate(dados["eventos"]):
        if e.get("cidade") != "blumenau" or "referencia_publicada" in e:
            continue
        ref = alvo.get((e["data"], e["pico_m"]))
        if ref is not None:
            dados["eventos"][i] = converter_registro(e, ref)
            n += 1
    return n


def main() -> int:
    caminho = DADOS / "enchentes.json"
    dados = json.loads(caminho.read_text(encoding="utf-8"))
    lista, gps = lista_alertablu(), planilha_gps()
    if "--aplicar" in sys.argv[1:]:
        n = aplicar(dados, lista, gps)
        caminho.write_text(json.dumps(dados, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"convertidos agora: {n}")
    eventos = dados["eventos"]
    linhas = proposta(eventos, lista, gps)
    RELATORIO.write_text(relatorio(linhas), encoding="utf-8")
    from collections import Counter
    print(Counter((l["referencia_publicada"] or "pendente", l["certeza"]) for l in linhas))
    print(f"relatório: {RELATORIO.relative_to(RAIZ)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
