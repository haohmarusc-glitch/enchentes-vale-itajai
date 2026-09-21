#!/usr/bin/env python3
"""
Histórico de Cheias de Rio do Sul: da página municipal ao relatório de reconciliação.

O QUE É A FONTE
---------------
A página "Histórico de Cheias" do portal da Defesa Civil de Rio do Sul
(defesacivil.riodosul.sc.gov.br) traz UMA tabela com as colunas Ano, Data do
Pico, Nível (m), Volume (mm) e Dias de Chuva. É a tabela que o Jefferson
capturou no navegador em 21/09/2026 (`data/brutos/riodosul-historico-cheias-
2026-09-21.html`, 77 linhas, 1911–2024), e é a mesma fonte dos 13 picos de Rio
do Sul que já estão em `enchentes.json`.

O QUE ESTE SCRIPT FAZ, E O QUE NÃO FAZ
--------------------------------------
* Lê a tabela do HTML salvo (nunca da rede: a captura é a evidência).
* Converte cada linha para o formato do projeto: data ISO com a precisão que a
  fonte dá (`2024-07-12` quando há dia, `2024-07` quando só há mês), nível em
  metros, volume e dias de chuva, com `-` virando null e não zero.
* Valida: duplicata exata, nível ausente, data ilegível, empate de nível no
  mesmo ano, ano e nível fora do plausível.
* Reconcilia com os registros de Rio do Sul em `enchentes.json`: quais linhas
  já estão cadastradas, quais são candidatas a inclusão, quais são um segundo
  pico no mesmo mês de um pico cadastrado, e quais registros do JSON não têm
  linha na tabela.
* **Não escreve em `enchentes.json`.** Há teste que trava isso. Registro entra
  na série só por decisão explícita do Jefferson, e o relatório existe para
  ele decidir com a comparação na mão (inclusões, alterações, divergências),
  como o "Plano seguro" de 21/09/2026 manda.

A DECISÃO DE INCLUSÃO (Jefferson, 21/09/2026) — `plano_de_inclusao()`
------------------------------------------------------------------------
* Opção (a): entram os 57 candidatos, sem corte em 1992 nem em 8 m — cortes
  seriam artificiais; a tabela apresenta as 77 linhas como ocorrências
  históricas, e ausência de chuva antiga não invalida o pico.
* Os 7 segundos picos em meses já cadastrados NÃO entram: quase todos só têm
  mês, e `enchentes.json` exige unicidade por (rio, cidade, data). Incluí-los
  criaria registro duplicado ou exigiria inventar dia. Ficam preservados na
  conversão bruta, nunca como `divergencias` (são cristas diferentes).
* Entre os próprios 57 há 5 colisões de mês: entra o MAIOR pico do mês; o
  menor fica na camada bruta até existir dia exato ou identificador próprio.
* Resultado: 52 registros novos, Rio do Sul de 13 para 65; 12 cristas
  preservadas e explicitamente pendentes, sem perda nem data inventada.
Quem grava é `importar_riodosul_historico.py`, que lê o plano daqui.

DUAS ARMADILHAS DA TABELA
-------------------------
1. A mesma coluna traz "12 de julho" e "Julho": a precisão varia linha a linha,
   e a saída guarda isso em `precisao`. Comparar "julho de 2024" com
   "12/07/2024" por igualdade de string perderia o par.
2. Há vários picos no mesmo mês (nov/2023 tem quatro linhas: 8,33; 6,77; 13,04;
   8,20). Não são duplicatas: são cristas distintas do mesmo mês, e o
   validador só chama de duplicata a linha idêntica.

Uso:
    python3 scripts/riodosul_historico.py data/brutos/riodosul-historico-cheias-2026-09-21.html
    python3 scripts/riodosul_historico.py ARQUIVO.html --escrever   # grava o JSON em data/brutos/
"""

from __future__ import annotations

import argparse
import hashlib
import html as _html
import json
import re
import sys
import unicodedata
from datetime import date, datetime, timezone
from html.parser import HTMLParser
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
DIR_BRUTOS = RAIZ / "data" / "brutos"

FONTE = ("Defesa Civil de Rio do Sul — Histórico de Cheias (defesacivil.riodosul.sc.gov.br), "
         "tabela 'Exportação de Dados'")
CIDADE = "rio-do-sul"

MESES = {"janeiro": 1, "fevereiro": 2, "marco": 3, "abril": 4, "maio": 5, "junho": 6,
         "julho": 7, "agosto": 8, "setembro": 9, "outubro": 10, "novembro": 11, "dezembro": 12}
COLUNAS_ESPERADAS = ("ano", "data do pico", "nivel (m)", "volume (mm)", "dias de chuva")

#: Faixa plausível de um pico de cheia em Rio do Sul, em metros de régua
#: municipal: o "normal" da página é 4,34 m e a maior da série é 13,58 m.
NIVEL_MIN_M, NIVEL_MAX_M = 3.0, 20.0
ANO_MIN, ANO_MAX = 1850, 2100


def sem_acento(texto: str) -> str:
    s = unicodedata.normalize("NFD", texto)
    return "".join(c for c in s if unicodedata.category(c) != "Mn").lower().strip()


class _Tabela(HTMLParser):
    """Extrai as linhas da PRIMEIRA <table> da página como listas de células."""

    def __init__(self) -> None:
        super().__init__()
        self.linhas: list[list[str]] = []
        self._em_tabela = 0
        self._linha: list[str] | None = None
        self._celula: list[str] | None = None
        self._pronta = False

    def handle_starttag(self, tag, attrs):
        if self._pronta:
            return
        if tag == "table":
            self._em_tabela += 1
        elif self._em_tabela and tag == "tr":
            self._linha = []
        elif self._em_tabela and tag in ("td", "th"):
            self._celula = []

    def handle_endtag(self, tag):
        if self._pronta:
            return
        if tag in ("td", "th") and self._celula is not None and self._linha is not None:
            self._linha.append(" ".join("".join(self._celula).split()))
            self._celula = None
        elif tag == "tr" and self._linha is not None:
            if self._linha:
                self.linhas.append(self._linha)
            self._linha = None
        elif tag == "table" and self._em_tabela:
            self._em_tabela -= 1
            if self._em_tabela == 0 and self.linhas:
                self._pronta = True

    def handle_data(self, data):
        if self._celula is not None:
            self._celula.append(data)


def ler_tabela(pagina: str) -> tuple[list[str], list[list[str]]]:
    """(cabeçalho, linhas) da primeira tabela. Falha alto se as colunas mudaram."""
    p = _Tabela()
    p.feed(_html.unescape(pagina) if "&" in pagina and "<" not in pagina else pagina)
    if not p.linhas:
        raise ValueError("nenhuma tabela na página — não é a página do Histórico de Cheias")
    cabecalho = [sem_acento(c) for c in p.linhas[0]]
    if tuple(cabecalho) != COLUNAS_ESPERADAS:
        raise ValueError(f"colunas inesperadas: {p.linhas[0]!r}; esperava {COLUNAS_ESPERADAS}")
    return p.linhas[0], p.linhas[1:]


def numero(bruto: str) -> float | None:
    """'7,49m' -> 7.49; '-' e vazio -> None (ausência, não zero); lixo falha alto."""
    b = (bruto or "").strip().lower().replace("m", "").replace(" ", "")
    if b in ("", "-", "—", "–"):
        return None
    return float(b.replace(".", "").replace(",", ".")) if "," in b else float(b)


def data_do_pico(ano: int, bruto: str) -> tuple[str | None, str]:
    """('2024-07-12', 'dia') | ('2024-07', 'mes') | (None, 'invalida')."""
    b = sem_acento(bruto)
    m = re.fullmatch(r"(\d{1,2})[oº°]?\s+de\s+([a-z]+)", b)
    if m and m.group(2) in MESES:
        dia, mes = int(m.group(1)), MESES[m.group(2)]
        try:
            return date(ano, mes, dia).isoformat(), "dia"
        except ValueError:
            return None, "invalida"
    if b in MESES:
        return f"{ano:04d}-{MESES[b]:02d}", "mes"
    return None, "invalida"


def converter(linhas: list[list[str]]) -> list[dict]:
    saida = []
    for i, cels in enumerate(linhas, start=2):
        if len(cels) != 5:
            saida.append({"linha": i, "erro": f"{len(cels)} células em vez de 5", "bruto": cels})
            continue
        ano_s, data_s, nivel_s, vol_s, dias_s = cels
        try:
            ano = int(ano_s)
        except ValueError:
            saida.append({"linha": i, "erro": f"ano ilegível: {ano_s!r}", "bruto": cels})
            continue
        data, precisao = data_do_pico(ano, data_s)
        try:
            nivel = numero(nivel_s)
            volume = numero(vol_s)
            dias = numero(dias_s)
        except ValueError as e:
            saida.append({"linha": i, "erro": f"número ilegível: {e}", "bruto": cels})
            continue
        saida.append({
            "linha": i, "ano": ano, "data": data, "precisao": precisao,
            "data_na_fonte": data_s, "nivel_m": nivel, "volume_mm": volume,
            "dias_chuva": int(dias) if dias is not None else None,
        })
    return saida


def validar(registros: list[dict]) -> list[str]:
    avisos = []
    vistos: dict[tuple, int] = {}
    por_ano_nivel: dict[tuple, list[int]] = {}
    for r in registros:
        if "erro" in r:
            avisos.append(f"linha {r['linha']}: {r['erro']}")
            continue
        chave = (r["ano"], r["data_na_fonte"], r["nivel_m"], r["volume_mm"], r["dias_chuva"])
        if chave in vistos:
            avisos.append(f"linha {r['linha']}: duplicata exata da linha {vistos[chave]}")
        vistos.setdefault(chave, r["linha"])
        if r["nivel_m"] is None:
            avisos.append(f"linha {r['linha']}: sem nível")
        elif not NIVEL_MIN_M <= r["nivel_m"] <= NIVEL_MAX_M:
            avisos.append(f"linha {r['linha']}: nível {r['nivel_m']} m fora de "
                          f"{NIVEL_MIN_M}–{NIVEL_MAX_M} m")
        if r["precisao"] == "invalida":
            avisos.append(f"linha {r['linha']}: data ilegível {r['data_na_fonte']!r}")
        if not ANO_MIN <= r["ano"] <= ANO_MAX:
            avisos.append(f"linha {r['linha']}: ano {r['ano']} fora de {ANO_MIN}–{ANO_MAX}")
        if r["nivel_m"] is not None:
            por_ano_nivel.setdefault((r["ano"], r["nivel_m"]), []).append(r["linha"])
    for (ano, nivel), ls in por_ano_nivel.items():
        if len(ls) > 1:
            avisos.append(f"{ano}: nível {nivel} m repetido nas linhas {ls} — empate, conferir "
                          "se são dois picos ou uma linha dobrada")
    return avisos


def _mes(iso: str | None) -> str | None:
    return iso[:7] if isinstance(iso, str) and len(iso) >= 7 else None


def reconciliar(registros: list[dict], cadastrados: list[dict]) -> dict:
    """
    Tabela × enchentes.json, sem escolher por ninguém.

    Uma linha da tabela está "cadastrada" quando há registro do mesmo mês com o
    mesmo nível (±0,005 m). O dia pode diferir (nov/2023: tabela 17, JSON 18 com
    data_na_fonte 17) e isso é anotado, não é divergência. Linha sem par é
    "candidata a inclusão"; se o mês dela já tem outro pico cadastrado, é
    "segundo pico no mesmo mês". Registro do JSON sem linha na tabela é
    "sem linha na tabela" — não deveria existir, porque a fonte é a mesma.
    """
    validos = [r for r in registros if "erro" not in r and r["nivel_m"] is not None]
    usados: set[int] = set()
    cadastradas, candidatas, segundo_pico, data_difere = [], [], [], []

    meses_cadastrados = {_mes(c.get("data")) for c in cadastrados}
    for r in validos:
        par = None
        for j, c in enumerate(cadastrados):
            if j in usados:
                continue
            if _mes(c.get("data")) == _mes(r["data"]) and abs(float(c["pico_m"]) - r["nivel_m"]) < 0.005:
                par = (j, c)
                break
        if par is None:
            item = {**r, "situacao": "candidata a inclusão"}
            if _mes(r["data"]) in meses_cadastrados:
                item["situacao"] = "segundo pico no mesmo mês de um cadastrado"
                segundo_pico.append(item)
            else:
                candidatas.append(item)
            continue
        j, c = par
        usados.add(j)
        item = {**r, "situacao": "já cadastrada", "cadastrado": {"data": c.get("data"),
                "pico_m": c.get("pico_m"), "data_na_fonte": c.get("data_na_fonte")}}
        if r["precisao"] == "dia" and len(str(c.get("data"))) == 7:
            item["nota"] = f"a tabela dá o dia ({r['data']}) e o cadastro só o mês"
            data_difere.append(item)
        elif r["precisao"] == "dia" and c.get("data") != r["data"] and c.get("data_na_fonte") != r["data"]:
            item["nota"] = f"dia difere: tabela {r['data']}, cadastro {c.get('data')}"
            data_difere.append(item)
        cadastradas.append(item)

    sem_tabela = [c for j, c in enumerate(cadastrados) if j not in usados]
    return {
        "resumo": {"linhas_validas": len(validos), "ja_cadastradas": len(cadastradas),
                   "candidatas_a_inclusao": len(candidatas),
                   "segundo_pico_no_mesmo_mes": len(segundo_pico),
                   "com_dia_diferente_ou_novo": len(data_difere),
                   "cadastrados_sem_linha_na_tabela": len(sem_tabela)},
        "ja_cadastradas": cadastradas,
        "candidatas_a_inclusao": candidatas,
        "segundo_pico_no_mesmo_mes": segundo_pico,
        "cadastrados_sem_linha_na_tabela": sem_tabela,
        "regra": "nada daqui entra em enchentes.json sem decisão explícita; o relatório é para decidir",
    }


RIO = "itajai-acu"


def _registro_novo(r: dict, colisao: dict | None) -> dict:
    """Uma linha da tabela no formato de `enchentes.json`, como os 13 já cadastrados."""
    nota = (f"Tabela municipal 'Histórico de Cheias', linha {r['linha']} da captura de "
            "21/09/2026 (data/brutos/riodosul-historico-cheias-2026-09-21.html). Incluído por "
            "script em 21/09/2026 por decisão do Jefferson (opção a: os 57 candidatos, o maior "
            "de cada mês).")
    if colisao is not None:
        nota += (f" A tabela tem outro pico em {r['data'][:7]}, {colisao['nivel_m']:.2f} m "
                 f"({colisao['data_na_fonte']}); fica na conversão bruta até existir dia exato.")
    novo = {"rio": RIO, "cidade": CIDADE, "data": r["data"], "pico_m": r["nivel_m"],
            "confianca": "media", "fonte": FONTE, "referencia": None, "nota": nota}
    if r["volume_mm"] is not None:
        novo["chuva_mm"] = r["volume_mm"]
    if r["dias_chuva"] is not None:
        novo["dias_de_chuva"] = r["dias_chuva"]
    return novo


def plano_de_inclusao(rec: dict) -> dict:
    """
    Aplica a decisão de 21/09/2026 à reconciliação: {entram, pendentes}.

    `entram` são registros prontos para `enchentes.json`; `pendentes` são as
    cristas preservadas na camada bruta, cada uma com o motivo. Não grava nada.
    """
    por_mes: dict[str, list[dict]] = {}
    for r in rec["candidatas_a_inclusao"]:
        por_mes.setdefault(_mes(r["data"]), []).append(r)

    entram, pendentes = [], []
    for mes, grupo in sorted(por_mes.items()):
        grupo = sorted(grupo, key=lambda r: -r["nivel_m"])
        maior, menores = grupo[0], grupo[1:]
        entram.append(_registro_novo(maior, menores[0] if menores else None))
        for m in menores:
            pendentes.append({**{k: m[k] for k in ("linha", "ano", "data", "precisao",
                                                    "data_na_fonte", "nivel_m", "volume_mm",
                                                    "dias_chuva")},
                              "motivo": f"colisão de mês: entrou o maior de {mes} "
                                        f"({maior['nivel_m']:.2f} m); este espera dia exato ou "
                                        "identificador próprio de ocorrência"})
    for r in rec["segundo_pico_no_mesmo_mes"]:
        pendentes.append({**{k: r[k] for k in ("linha", "ano", "data", "precisao",
                                                "data_na_fonte", "nivel_m", "volume_mm",
                                                "dias_chuva")},
                          "motivo": "segundo pico no mesmo mês de um cadastrado: unicidade por "
                                    "(rio, cidade, data) e só há mês; não é divergência, é outra "
                                    "crista"})
    entram.sort(key=lambda e: e["data"])
    pendentes.sort(key=lambda p: (p["data"] or "", -p["nivel_m"]))
    return {"decisao": "Jefferson, 21/09/2026: opção (a), maior pico por mês, segundos picos "
                       "preservados na camada bruta",
            "entram": entram, "pendentes": pendentes,
            "resumo": {"entram": len(entram), "pendentes": len(pendentes)}}


def carregar_cadastrados() -> list[dict]:
    from comum import le_json
    return [e for e in le_json("enchentes.json")["eventos"] if e.get("cidade") == CIDADE]


def imprimir(registros: list[dict], avisos: list[str], rec: dict) -> None:
    print(f"{len(registros)} linhas na tabela; {rec['resumo']['linhas_validas']} válidas")
    if avisos:
        print("\nAvisos:")
        for a in avisos:
            print(f"  - {a}")
    print("\nReconciliação com enchentes.json (rio-do-sul):")
    for k, v in rec["resumo"].items():
        print(f"  {k:<34} {v}")
    for titulo, chave in (("Candidatas a inclusão", "candidatas_a_inclusao"),
                          ("Segundo pico no mesmo mês de um cadastrado", "segundo_pico_no_mesmo_mes")):
        print(f"\n{titulo}:")
        for r in sorted(rec[chave], key=lambda r: (r["ano"], r["data"] or ""), reverse=True):
            print(f"  {r['data']:<10} {r['nivel_m']:>6.2f} m  {r['data_na_fonte']:<16} "
                  f"chuva {r['volume_mm'] if r['volume_mm'] is not None else '-'} mm / "
                  f"{r['dias_chuva'] if r['dias_chuva'] is not None else '-'} d")
    if any("nota" in r for r in rec["ja_cadastradas"]):
        print("\nJá cadastradas com observação de data:")
        for r in rec["ja_cadastradas"]:
            if "nota" in r:
                print(f"  {r['data']} {r['nivel_m']} m — {r['nota']}")
    if rec["cadastrados_sem_linha_na_tabela"]:
        print("\nCadastrados SEM linha na tabela (conferir):")
        for c in rec["cadastrados_sem_linha_na_tabela"]:
            print(f"  {c.get('data')} {c.get('pico_m')} m")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("arquivo", type=Path, help="HTML da página Histórico de Cheias, salvo")
    ap.add_argument("--escrever", action="store_true",
                    help="grava o JSON convertido ao lado do HTML, em data/brutos/")
    args = ap.parse_args()

    pagina = args.arquivo.read_text(encoding="utf-8", errors="replace")
    _, linhas = ler_tabela(pagina)
    registros = converter(linhas)
    avisos = validar(registros)
    rec = reconciliar(registros, carregar_cadastrados())
    imprimir(registros, avisos, rec)
    plano = plano_de_inclusao(rec)
    print(f"\nPlano de inclusão ({plano['decisao']}): entram {plano['resumo']['entram']}, "
          f"pendentes {plano['resumo']['pendentes']}")

    if args.escrever:
        DIR_BRUTOS.mkdir(parents=True, exist_ok=True)
        destino = DIR_BRUTOS / (args.arquivo.stem + ".json")
        conteudo = {
            "_meta": {
                "fonte": FONTE,
                "cidade": CIDADE,
                "arquivo_html": args.arquivo.name,
                "sha256_html": hashlib.sha256(pagina.encode("utf-8", "replace")).hexdigest(),
                "convertido_em": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                "regra": "cópia fiel da tabela municipal; NÃO é enchentes.json e não altera "
                         "registro nenhum — inclusão só por decisão explícita",
                "referencia": None,
                "avisos": avisos,
            },
            "registros": registros,
            "reconciliacao": rec,
            "plano_de_inclusao": plano,
        }
        destino.write_text(json.dumps(conteudo, ensure_ascii=False, indent=1) + "\n",
                           encoding="utf-8")
        print(f"\nGravado: {destino.relative_to(RAIZ)}")


if __name__ == "__main__":
    sys.exit(main())
