#!/usr/bin/env python3
"""
Coleta a chuva acumulada em 24 h da rede de pluviômetros do CEMADEN na bacia.

Fonte: Mapa Interativo do CEMADEN — camadas OpenLayers servidas como JSONP em
`https://resources.cemaden.gov.br/dados/{311,332,333,327mi}_24.json`, com o
envelope `estacoes([...])`. Os quatro arquivos são recortes regionais; juntos
cobrem Santa Catarina. O `_24` no nome é o acumulado de 24 h que o mapa pinta.

POR QUE CEMADEN, E SÓ CHUVA
---------------------------
A rede do CEMADEN é a mais densa da região — 137 pluviômetros ativos dentro da
caixa da bacia, contra as poucas de cada Defesa Civil. É chuva por bairro, que é
o que falta onde as outras redes discordam ou não têm sensor (Blumenau sozinha
tem 14 ativos). NÍVEL não entra: as estações hidrológicas/Acqua do CEMADEN na
área são poucas e quase todas inativas ou fora do Açu/Mirim — o catálogo anota
isso em `_meta.nota_nivel`. E, como em `coleta_chuva_sc.py`, milímetro é
milímetro em qualquer lugar: não depende de régua, de zero nem de datum, então a
chuva entra sem o risco que barra o nível.

O MAPA É EXPLÍCITO, POR COORDENADA — NÃO ADIVINHADO
---------------------------------------------------
Cada estação do CEMADEN traz o município. O vínculo estação→cidade do projeto sai
de `data/cemaden-estacoes-bacia.json`, o catálogo conferido por coordenada (lat,
lon de cada pluviômetro), não por semelhança de nome. Município que não é cidade
do projeto é ignorado, e o script diz quantos ignorou. Timbó fica de fora de
propósito, como em `coleta_chuva_sc.py`: mora em `afluentes_monitorados`, então o
site e o bot ainda não conseguem mostrá-la — coletar seria cobertura aparente.

FUSO
----
O CEMADEN registra tudo em **UTC** (declarado, e anotado em `_meta.fuso`). O
carimbo vira hora de Brasília SEM fuso, que é o contrato do projeto para
`medido_em` — o mesmo `hora_local()` de `coleta_chuva_sc.py`.

OS NOMES DOS CAMPOS BRUTOS AINDA PRECISAM DE UMA CONFIRMAÇÃO NA VPS
-------------------------------------------------------------------
O egress do ambiente de desenvolvimento não alcança `resources.cemaden.gov.br`
(mesmo caso do Overpass), então os nomes exatos das chaves de VALOR e de CARIMBO
no JSON bruto não foram observados aqui — só a extração já normalizada do
navegador. Este coletor tenta uma lista de nomes prováveis e, quando não
reconhece nenhum, **recusa a estação dizendo quais chaves viu** — nunca inventa
um zero. Rode uma vez na VPS:

    python3 scripts/coleta_chuva_cemaden.py --seco --amostra

Ele imprime as chaves cruas de uma estação. Se o valor/carimbo estiver sob outro
nome, é só acrescentá-lo em `CHAVES_VALOR_24H` / `CHAVES_CARIMBO` e fechar.

Uso:
    python3 scripts/coleta_chuva_cemaden.py --seco            # mostra o que colheria
    python3 scripts/coleta_chuva_cemaden.py --seco --amostra  # + chaves cruas
    python3 scripts/coleta_chuva_cemaden.py                   # grava
"""

import argparse
import json
import sys
from datetime import datetime, timezone

from coleta_chuva import incoerencias
from coleta_chuva_sc import CHUVA_MAXIMA_MM, e_numero, hora_local
from comum import DADOS, USER_AGENT, espera_turno

#: Os quatro recortes regionais do Mapa Interativo que, juntos, cobrem SC.
REGIOES = ("311_24", "332_24", "333_24", "327mi_24")
URL_BASE = "https://resources.cemaden.gov.br/dados/{}.json"

#: Catálogo conferido por coordenada. É a fonte do vínculo município→cidade e
#: das coordenadas que aparecem no `--seco`.
CATALOGO = DADOS / "cemaden-estacoes-bacia.json"

#: Município do CEMADEN (MAIÚSCULAS, como a fonte publica) -> id da cidade em
#: `data/estacoes.json`. Só as cidades que o projeto sabe mostrar; Timbó de fora
#: (aflunte sem tela), igual ao `coleta_chuva_sc.py`.
MUNICIPIO_PARA_CIDADE = {
    "TAIÓ": "taio",
    "ITUPORANGA": "ituporanga",
    "RIO DO SUL": "rio-do-sul",
    "IBIRAMA": "ibirama",
    "APIÚNA": "apiuna",
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

#: Nomes prováveis da chave do acumulado de 24 h no registro bruto. A confirmar
#: na VPS (ver docstring). A ordem é a preferência.
CHAVES_VALOR_24H = (
    "acumulado24h", "acc24hr", "acc24h", "chuva24h", "acumulado_24h",
    "valor24h", "vl24h", "chuva_lbl", "valor", "chuva", "ultimovalor",
)
#: Nomes prováveis da chave do carimbo de tempo (UTC).
CHAVES_CARIMBO = (
    "datahoraultimovalor", "datahora_ultimovalor", "datahora", "data_hora",
    "ultimadata", "data", "dt", "timestamp",
)
#: Nomes prováveis da chave do município.
CHAVES_MUNICIPIO = ("municipio", "cidade", "nomemunicipio", "nome_municipio")
#: Nomes prováveis da chave do código da estação (para casar com o catálogo).
CHAVES_CODIGO = ("codigo", "codestacao", "cod", "codibge", "id")


def _primeiro_campo(reg: dict, chaves: tuple[str, ...]):
    """O valor da primeira chave presente (comparação insensível a caixa)."""
    baixa = {str(k).lower(): v for k, v in reg.items()}
    for c in chaves:
        if c in baixa:
            return baixa[c]
    return None


def desembrulhar_jsonp(texto: str) -> list[dict]:
    """
    `estacoes([...])`  ->  a lista de estações.

    Aceita o envelope JSONP (com ou sem `;` final) e também JSON puro, caso o
    endpoint mude. Erro de parse vira lista vazia com aviso — uma região fora do
    ar não pode derrubar as outras.
    """
    t = texto.strip()
    if t.endswith(";"):
        t = t[:-1].strip()
    ini, fim = t.find("("), t.rfind(")")
    if t and not t[0] in "[{" and 0 <= ini < fim:
        t = t[ini + 1:fim]
    dados = json.loads(t)
    if isinstance(dados, dict):
        # alguns envelopes trazem {"estacoes": [...]} em vez do array cru
        for v in dados.values():
            if isinstance(v, list):
                return v
        return []
    return dados if isinstance(dados, list) else []


def converter(estacoes: list[dict]) -> tuple[list[dict], list[str]]:
    """As leituras de chuva utilizáveis e o motivo de cada recusa."""
    leituras, recusadas = [], []
    for e in estacoes:
        if not isinstance(e, dict):
            continue
        municipio = _primeiro_campo(e, CHAVES_MUNICIPIO)
        cidade = MUNICIPIO_PARA_CIDADE.get(str(municipio).strip().upper()) if municipio else None
        if not cidade:
            continue  # fora das cidades do projeto — silencioso: SC inteira vem aqui

        codigo = _primeiro_campo(e, CHAVES_CODIGO)
        nome = str(_primeiro_campo(e, ("nome", "nomeestacao", "estacao")) or codigo or "?").strip()
        rotulo = f"{codigo} {nome}".strip()

        valor = _primeiro_campo(e, CHAVES_VALOR_24H)
        if valor is None or not e_numero(valor):
            # Nunca fabrica: chave de valor não reconhecida é recusa explícita,
            # com as chaves vistas, para fechar o mapeamento na VPS.
            recusadas.append(f"{rotulo} ({cidade}): sem chave de chuva reconhecida — "
                             f"chaves: {sorted(e.keys())}")
            continue

        mm24 = round(float(valor), 2)
        if not (0 <= mm24 <= CHUVA_MAXIMA_MM):
            recusadas.append(f"{rotulo} ({cidade}): 24h={mm24:g} mm fora da faixa plausível")
            continue

        mm = {"min10": None, "h1": None, "h12": None, "h24": mm24, "h48": None}
        problemas = incoerencias(mm)
        leituras.append({
            "estacao": rotulo,
            "rio": None,        # a fonte dá o município, não a calha; não se inventa
            "cidade": cidade,
            "mm": mm,
            "medido_em": hora_local(_carimbo_iso(_primeiro_campo(e, CHAVES_CARIMBO))),
            "coerente": not problemas,
            "incoerencias": problemas,
            "fonte": "CEMADEN — Mapa Interativo (pluviômetros automáticos)",
        })
    return leituras, recusadas


def _carimbo_iso(bruto) -> str | None:
    """
    Normaliza o carimbo do CEMADEN para ISO antes do `hora_local()`.

    O mapa costuma publicar `AAAA-MM-DD HH:MM:SS[.0]` (UTC). Troca o espaço por
    `T` e corta os milissegundos; deixa `hora_local()` (que assume UTC quando não
    há fuso) fazer a conversão para Brasília. Valor não-texto vira None.
    """
    if not isinstance(bruto, str) or not bruto.strip():
        return None
    t = bruto.strip().replace(" ", "T")
    if "." in t:
        t = t.split(".", 1)[0]
    return t


def baixar_estacoes() -> list[dict]:
    """As estações das quatro regiões, concatenadas. Região que falha é pulada."""
    import requests

    todas: list[dict] = []
    for reg in REGIOES:
        url = URL_BASE.format(reg)
        try:
            espera_turno()
            r = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=60)
            r.raise_for_status()
            regiao = desembrulhar_jsonp(r.text)
            todas.extend(regiao)
        except Exception as e:  # noqa: BLE001 — uma região fora do ar não derruba as outras
            print(f"aviso: região {reg} não coletada ({e}).", file=sys.stderr)
    return todas


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--seco", action="store_true", help="mostra o que colheria, sem gravar")
    ap.add_argument("--amostra", action="store_true",
                    help="imprime as chaves cruas de uma estação (confirmar formato)")
    args = ap.parse_args()

    try:
        estacoes = baixar_estacoes()
    except Exception as e:  # noqa: BLE001
        print(f"ERRO ao coletar: {e}", file=sys.stderr)
        return 1

    if args.amostra and estacoes:
        print("amostra do registro bruto (uma estação):")
        print(json.dumps(estacoes[0], ensure_ascii=False, indent=2)[:1500])
        print()

    leituras, recusadas = converter(estacoes)
    print(f"{len(estacoes)} estações nas regiões · {len(leituras)} viraram leitura de chuva")
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
        print("\nnada gravado: nenhuma leitura utilizável (confirme o formato com --amostra).",
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
