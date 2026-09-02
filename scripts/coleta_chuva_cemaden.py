#!/usr/bin/env python3
"""
Coleta a chuva acumulada em 24 h da rede de pluviômetros do CEMADEN na bacia.

Fonte: Mapa Interativo do CEMADEN (mapainterativo.cemaden.gov.br) — camadas
OpenLayers servidas como JSONP em
`https://resources.cemaden.gov.br/dados/{311,332,333,327mi}_24.json?callback=estacoes`.
Sem auth. O `fetch` do navegador bate em CORS, mas de script é um GET simples.
O `_24` no nome é o acumulado de 24 h que o mapa pinta. Endpoint e campos
descobertos por inspeção no Chrome (02/09/2026).

CAMPOS DO REGISTRO BRUTO (confirmados na fonte)
-----------------------------------------------
`estacao_cod` (ex. 420290901A), `estacao_id`, `estacao_nome`,
`estacao_munic` ("BRUSQUE-SC" — município COM o `-UF`), `estacao_uf`,
`estacao_latlon` ("[lat][lon]"), `icon` (flag_verde=ativo, flag_cinza=sem dado),
`lbl` (chuva acumulada em mm, o valor pintado no mapa).

**Não há carimbo por estação.** O arquivo `_24` é um retrato do acumulado de
24 h no momento em que o CEMADEN o gera; a leitura não traz a hora do último
pulso de cada pluviômetro. Por isso `medido_em` recebe a HORA DA COLETA (hora de
Brasília, sem fuso, o contrato do projeto) — é o que se sabe: "este é o
acumulado de 24 h vigente agora". Como toda chuva aqui, é CONTEXTO: nunca vira
cota nem dispara aviso sozinha.

POR QUE CEMADEN, E SÓ CHUVA
---------------------------
A rede mais densa da região — 137 pluviômetros ativos na caixa da bacia
(Blumenau sozinha tem 14). Chuva por bairro, onde as outras redes discordam ou
não têm sensor. NÍVEL não entra: as hidrológicas/Acqua do CEMADEN na área são
poucas e quase todas inativas ou fora do Açu/Mirim (`_meta.nota_nivel` do
catálogo). E, como em `coleta_chuva_sc.py`, milímetro é milímetro em qualquer
lugar — não depende de régua, de zero nem de datum.

O MAPA É EXPLÍCITO — NÃO ADIVINHADO
-----------------------------------
O vínculo estação→cidade sai do município (`estacao_munic`, sem o `-UF`) contra
`MUNICIPIO_PARA_CIDADE`, restrito às cidades que o projeto sabe mostrar. As
coordenadas de cada pluviômetro estão em `data/cemaden-estacoes-bacia.json`,
conferidas por lat/lon. Município fora do projeto é ignorado em silêncio (o feed
traz SC inteira). Timbó fica de fora, como em `coleta_chuva_sc.py`: mora em
`afluentes_monitorados`, então o site e o bot ainda não a mostram.

Uso:
    python3 scripts/coleta_chuva_cemaden.py --seco            # mostra o que colheria
    python3 scripts/coleta_chuva_cemaden.py --seco --amostra  # + registro bruto
    python3 scripts/coleta_chuva_cemaden.py                   # grava
"""

import argparse
import json
import sys
from datetime import datetime, timezone

from coleta_chuva import incoerencias
from coleta_chuva_sc import CHUVA_MAXIMA_MM, FUSO_BRASILIA, e_numero
from comum import DADOS, USER_AGENT, espera_turno

#: Os quatro recortes regionais do Mapa Interativo que, juntos, cobrem SC.
REGIOES = ("311_24", "332_24", "333_24", "327mi_24")
URL_BASE = "https://resources.cemaden.gov.br/dados/{}.json"

#: Catálogo conferido por coordenada. Referência (estação→coordenada→município).
CATALOGO = DADOS / "cemaden-estacoes-bacia.json"

#: Município do CEMADEN (MAIÚSCULAS, SEM o `-UF`) -> id da cidade em
#: `data/estacoes.json`. Só as cidades que o projeto sabe mostrar; Timbó de fora
#: (afluente sem tela), igual ao `coleta_chuva_sc.py`.
MUNICIPIO_PARA_CIDADE = {
    "TAIÓ": "taio",
    "ITUPORANGA": "ituporanga",
    "RIO DO SUL": "rio-do-sul",
    "IBIRAMA": "ibirama",
    "INDAIAL": "indaial",
    "BLUMENAU": "blumenau",
    "GASPAR": "gaspar",
    "ILHOTA": "ilhota",
    "ITAJAÍ": "itajai",
    "VIDAL RAMOS": "vidal-ramos",
    "BOTUVERÁ": "botuvera",
    "GUABIRUBA": "guabiruba",
    "BRUSQUE": "brusque",
}


def _municipio_sem_uf(bruto) -> str:
    """"BRUSQUE-SC" -> "BRUSQUE". Tira só um sufixo `-<2 letras>` no fim."""
    s = str(bruto or "").strip()
    if len(s) > 3 and s[-3] == "-" and s[-2:].isalpha():
        s = s[:-3]
    return s.upper()


def _numero(valor) -> float | None:
    """
    `lbl` como número, ou None quando não é chuva.

    A fonte manda `lbl` numérico nas ativas e string vazia nas inativas
    (flag_cinza). Aceita número e string numérica; `True` não é milímetro.
    """
    if e_numero(valor):
        return float(valor)
    if isinstance(valor, str):
        try:
            return float(valor.strip().replace(",", "."))
        except ValueError:
            return None
    return None


def desembrulhar_jsonp(texto: str) -> list[dict]:
    """
    `estacoes([...])`  ->  a lista de estações.

    Aceita o envelope JSONP (com ou sem `;` final) e também JSON puro, caso o
    endpoint mude. Erro de parse sobe para o chamador, que pula a região.
    """
    t = texto.strip()
    if t.endswith(";"):
        t = t[:-1].strip()
    ini, fim = t.find("("), t.rfind(")")
    if t and t[0] not in "[{" and 0 <= ini < fim:
        t = t[ini + 1:fim]
    dados = json.loads(t)
    if isinstance(dados, dict):
        for chave in ("features", "estacoes"):
            if isinstance(dados.get(chave), list):
                return dados[chave]
        for v in dados.values():
            if isinstance(v, list):
                return v
        return []
    return dados if isinstance(dados, list) else []


def _campos(reg: dict) -> dict:
    """O registro achatado: alguns envelopes aninham em `attributes`."""
    return reg.get("attributes", reg) if isinstance(reg, dict) else {}


def converter(estacoes: list[dict], momento: str | None = None) -> tuple[list[dict], list[str], int]:
    """
    As leituras de chuva utilizáveis, as recusas e quantas ficaram SEM DADO.

    `momento` é a hora de Brasília (sem fuso) a carimbar em cada leitura; o
    padrão é agora, porque a fonte não traz hora por estação.
    """
    if momento is None:
        momento = (datetime.now(timezone.utc).astimezone(FUSO_BRASILIA)
                   .replace(tzinfo=None).isoformat(timespec="seconds"))

    leituras, recusadas, sem_dado = [], [], 0
    for reg in estacoes:
        a = _campos(reg)
        if not a:
            continue
        cidade = MUNICIPIO_PARA_CIDADE.get(_municipio_sem_uf(a.get("estacao_munic")))
        if not cidade:
            continue  # fora das cidades do projeto — silencioso: o feed traz SC inteira

        codigo = a.get("estacao_cod")
        nome = str(a.get("estacao_nome") or codigo or "?").strip()
        rotulo = f"{codigo} {nome}".strip()
        inativa = "cinza" in str(a.get("icon") or "")

        mm24 = _numero(a.get("lbl"))
        if mm24 is None:
            # Sem número (inativa/sem leitura): não é erro, é ausência de dado.
            sem_dado += 1
            continue
        if not (0 <= mm24 <= CHUVA_MAXIMA_MM):
            recusadas.append(f"{rotulo} ({cidade}): 24h={mm24:g} mm fora da faixa plausível")
            continue
        if inativa:
            # Número numa estação marcada sem-dado: valor provavelmente velho.
            sem_dado += 1
            continue

        mm24 = round(mm24, 2)
        mm = {"min10": None, "h1": None, "h12": None, "h24": mm24, "h48": None}
        problemas = incoerencias(mm)
        leituras.append({
            "estacao": rotulo,
            "rio": None,        # a fonte dá o município, não a calha; não se inventa
            "cidade": cidade,
            "mm": mm,
            "medido_em": momento,
            "coerente": not problemas,
            "incoerencias": problemas,
            "fonte": "CEMADEN — Mapa Interativo (pluviômetros automáticos)",
        })
    return leituras, recusadas, sem_dado


def baixar_estacoes() -> list[dict]:
    """As estações das quatro regiões, concatenadas. Região que falha é pulada."""
    import requests

    todas: list[dict] = []
    for reg in REGIOES:
        url = URL_BASE.format(reg)
        try:
            espera_turno()
            r = requests.get(url, params={"callback": "estacoes"},
                             headers={"User-Agent": USER_AGENT}, timeout=60)
            r.raise_for_status()
            todas.extend(desembrulhar_jsonp(r.text))
        except Exception as e:  # noqa: BLE001 — uma região fora do ar não derruba as outras
            print(f"aviso: região {reg} não coletada ({e}).", file=sys.stderr)
    return todas


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--seco", action="store_true", help="mostra o que colheria, sem gravar")
    ap.add_argument("--amostra", action="store_true",
                    help="imprime um registro bruto (conferir formato)")
    args = ap.parse_args()

    try:
        estacoes = baixar_estacoes()
    except Exception as e:  # noqa: BLE001
        print(f"ERRO ao coletar: {e}", file=sys.stderr)
        return 1

    if args.amostra and estacoes:
        print("registro bruto (uma estação):")
        print(json.dumps(_campos(estacoes[0]), ensure_ascii=False, indent=2)[:1500])
        print()

    leituras, recusadas, sem_dado = converter(estacoes)
    print(f"{len(estacoes)} estações nas regiões · {len(leituras)} viraram leitura de chuva "
          f"· {sem_dado} sem dado nas cidades do projeto")
    for l in sorted(leituras, key=lambda x: (x["cidade"], x["estacao"])):
        h24 = l["mm"]["h24"]
        marca = "" if l["coerente"] else "  ⚠ " + "; ".join(l["incoerencias"])
        print(f"  {l['cidade']:12} {h24:6.1f} mm/24h  {l['medido_em']}  {l['estacao']}{marca}")
    if recusadas:
        print(f"\n{len(recusadas)} recusa(s):")
        for r in recusadas[:20]:
            print(f"  {r}")

    if args.seco:
        return 0

    if not leituras:
        print("\nnada gravado: nenhuma leitura utilizável (confira o formato com --amostra).",
              file=sys.stderr)
        return 1

    destino = DADOS / "tempo-real" / "chuva-cemaden.json"
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_text(json.dumps({
        "coletado_em": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "fonte": "CEMADEN — Mapa Interativo",
        "leituras": leituras,
    }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"\ngravado em {destino}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
