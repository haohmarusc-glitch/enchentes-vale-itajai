#!/usr/bin/env python3
"""Converte um KML do Google My Maps (cotas de rua) no JSON bruto que os importadores leem.

POR QUE EXISTE (10/09/2026)
Os dois KMLs que o projeto já recebeu vieram em formatos DIFERENTES, e a
conversão de agosto foi feita fora do repo, sem código — por isso o de Brusque
perdeu `obs`, `esquina` e as coordenadas UTM ("perda_conhecida" no bruto) e
ninguém pode refazer. Este script é a conversão com teste, para os dois:

* **Brusque** — `<ExtendedData>` de verdade: `descrição`, `cota`, `obs`,
  `bairro`, `coord_x`, `coord_y`, `ruas`, `esquina`, `esquina_co`. Decimal
  com PONTO (`15.55`).
* **Gaspar** — sem `ExtendedData`: os campos vêm como texto solto no
  `<description>`, separados por `<br>`: `FID`, `sequencia`, `cota`,
  `refer_1`, `refer_2`, `bairro`, `coord_x`, `coord_y`, `latitude`,
  `longitu` (truncado assim na fonte). Decimal com VÍRGULA (`8,25`). O
  `<name>` traz a cota com três casas (`8,246`) e o campo `cota` com duas
  (`8,25`) — não misturar.
* **Brusque, camada "Cotas de cheia 2023"** (KML original lido em 10/09/2026,
  357 pontos) — `ExtendedData` com nomes por extenso: `descrição`, `Bairro`,
  `Rua`, `Esquina`, `Nível registrado no local`, `Conferência`, `gx_media_links`
  (foto). **"Nível registrado no local" NÃO é a cota: é a LÂMINA d'água medida
  no ponto** (0,06–5,20 m, mediana 0,90; às vezes com unidade, "0,40 m"). A
  cota da rua é o `<name>` (7,65): em 337 dos 343 pontos com os dois números,
  `<name>` + lâmina = **8,96 m**, o pico de 17/11/2023 na Ponte Estaiada — a
  Defesa Civil derivou a cota de cada rua como pico menos lâmina. Por isso a
  lâmina vai para `lamina_local_m`/`lamina_local_rotulo`, e a cota sai do
  nome (`cota_campo = "nome_marcador"`). A busca de sinônimos ignora
  maiúsculas e acentos.
* **Ituporanga, ruas** (60 pontos) — nem `ExtendedData` nem campos: o
  `<name>` É a cota ("3,38 metros") e o `<description>` é a rua. Só quando
  não há campo de cota o `<name>` vale como cota, e aí `cota_campo` é
  `"nome_marcador"`.
* **Ituporanga, manchas** — 25 polígonos em pastas "COTA - 3,00" … "COTA - 6,50".
  Não são pontos de rua: este script os conta como "sem cota" e recusa o
  arquivo. Precisam de um conversor de polígono (GeoJSON por cota), como as
  manchas de Itajaí — pendência no README.

⚠️ FALHA SILENCIOSA É O INIMIGO. Um parser que só conhece um formato lê o
outro e devolve 1.615 pontos com tudo vazio — arquivo válido, contagem certa,
conteúdo nenhum. Por isso: ponto sem cota é contado e listado; se NENHUM
ponto tiver cota, o script sai com erro e não grava.

O que o JSON de saída NÃO afirma: que o campo `cota` é nível de régua. Foi a
armadilha da camada "Cotas de Cheia 2011" de Brusque. Quem decide isso é
`analisar_kml_gaspar.py` / `analisar_kml_brusque.py`, depois.

Uso:
    python3 scripts/kml_para_json.py data/brutos/gaspar-cotas-ruas-mymaps.kml --saida data/brutos/gaspar-cotas-2020.json
    python3 scripts/kml_para_json.py brusque.kml --saida data/brutos/brusque-mymaps-cotas.json --forcar
"""

from __future__ import annotations

import argparse
import hashlib
import html
import json
import re
import sys
import unicodedata
import xml.etree.ElementTree as ET
from datetime import date
from pathlib import Path

NS = {"k": "http://www.opengis.net/kml/2.2"}

#: Como cada nome de campo da fonte vira o nome que os importadores esperam.
#: Gaspar chama a rua de `refer_1` e a transversal de `refer_2`; Brusque, de
#: `ruas` e `esquina`. O importador lê `rua` e `esquina`.
SINONIMOS = {
    "refer_1": "rua", "ruas": "rua", "rua": "rua",
    "refer_2": "esquina", "esquina": "esquina",
    "longitu": "longitude", "longitude": "longitude", "latitude": "latitude",
    "bairro": "bairro", "conferencia": "conferencia",
}
#: Nomes de campo que carregam a cota, por ordem de preferência. Comparados
#: sem maiúsculas nem acentos (ver `_norm`).
CAMPOS_DE_COTA = ("cota",)
#: Campos que são LÂMINA d'água no ponto, não cota de régua (Brusque 2023).
CAMPOS_DE_LAMINA = ("nivel registrado no local",)
#: `<name>` que É a cota: "3,38 metros", "4,00 m", "8,246". Só vale quando
#: não há campo de cota.
RE_COTA_NO_NOME = re.compile(r"^(\d+[.,]\d+)\s*(m|metros)?$", re.I)

RE_BR = re.compile(r"<br\s*/?>", re.I)
RE_TAG = re.compile(r"<[^>]+>")
#: Nome de campo como o My Maps exporta: identificador simples (FID, refer_1, longitu).
RE_CHAVE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def numero(texto) -> float | None:
    """'8,25' e '15.55' viram 8.25 e 15.55; '698098,862749' vira 698098.862749.

    Unidade colada no fim ('0,40 m', '3,38 metros') é descartada — aparece em
    parte da camada 2023 de Brusque e nos nomes de Ituporanga.
    """
    if texto is None:
        return None
    t = re.sub(r"\s*(m|metros)\s*$", "", str(texto).strip(), flags=re.I).strip()
    if not t:
        return None
    if "," in t and "." not in t:
        t = t.replace(",", ".")
    elif "," in t and "." in t:
        # '1.234,56' (milhar com ponto) — não apareceu nas fontes; trata por segurança.
        t = t.replace(".", "").replace(",", ".")
    try:
        return float(t)
    except ValueError:
        return None


def _local(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def _norm(chave: str) -> str:
    """'Nível registrado no local' → 'nivel registrado no local'; 'Rua' → 'rua'."""
    sem_acento = unicodedata.normalize("NFKD", chave).encode("ascii", "ignore").decode()
    return " ".join(sem_acento.lower().split())


def campos_da_descricao(descricao: str | None) -> dict[str, str]:
    """Os campos do `<description>` do My Maps, nos dois jeitos que ele escreve.

    O export real de Gaspar (lido na VPS em 10/09/2026) NÃO usa dois-pontos:
    cada campo é um trecho entre `<br>`, com o NOME e o VALOR separados por
    uma corrida de espaços, e o primeiro trecho é só o nome da rua, sem chave:

        Rua Adriano Kormann    <br>   FID   0    <br>   cota   8,25    <br>   refer_2
          Rua Nilton Cardoso    <br>   coord_x   698098,862749 …

    O valor pode ter espaço simples ("Rua Nilton Cardoso") e quebra de linha
    depois da chave; a quebra vira espaço antes de separar. `campo: valor` (o
    formato descrito nos documentos de sessão) continua aceito. Trecho sem
    chave reconhecível (a rua do topo) vai para `_titulo`.
    """
    if not descricao:
        return {}
    texto = html.unescape(descricao)
    saida: dict[str, str] = {}
    for pedaco in RE_BR.split(texto):
        pedaco = RE_TAG.sub("", pedaco).strip()
        if not pedaco:
            continue
        chave, valor = None, None
        if ":" in pedaco:
            c, v = pedaco.split(":", 1)
            if RE_CHAVE.match(c.strip()):
                chave, valor = c.strip(), " ".join(v.split())
        if chave is None:
            # Nome e valor separados por CORRIDA de espaços (ou quebra de linha);
            # o valor em si só tem espaços simples ("Rua Nilton Cardoso").
            partes = [x for x in re.split(r"\s{2,}|\n", pedaco) if x.strip()]
            if len(partes) >= 2 and RE_CHAVE.match(partes[0].strip()):
                chave = partes[0].strip()
                valor = " ".join(" ".join(x.split()) for x in partes[1:])
            elif len(partes) == 1 and RE_CHAVE.match(partes[0].strip()) and saida:
                chave, valor = partes[0].strip(), ""   # campo vazio, depois do primeiro
        if chave is None:
            saida.setdefault("_titulo", " ".join(pedaco.split()))
            continue
        saida[chave] = valor
    return saida


def campos_do_extended(placemark) -> dict[str, str]:
    saida: dict[str, str] = {}
    for data in placemark.iter():
        nome_tag = _local(data.tag)
        if nome_tag == "Data":
            valor = data.find("k:value", NS)
            if valor is None:
                valor = next((f for f in data if _local(f.tag) == "value"), None)
            saida[data.get("name", "").strip()] = (valor.text or "").strip() if valor is not None else ""
        elif nome_tag == "SimpleData":
            saida[data.get("name", "").strip()] = (data.text or "").strip()
    saida.pop("", None)
    return saida


def coordenadas(placemark) -> tuple[float | None, float | None]:
    for el in placemark.iter():
        if _local(el.tag) == "coordinates" and el.text:
            partes = el.text.strip().split()[0].split(",")
            if len(partes) >= 2:
                return numero(partes[0]), numero(partes[1])
    return None, None


def ponto_de(placemark, pasta: str | None) -> dict:
    nome = next((el.text for el in placemark if _local(el.tag) == "name"), None)
    descricao = next((el.text for el in placemark if _local(el.tag) == "description"), None)
    brutos = campos_do_extended(placemark)
    formato = "extended_data"
    if not brutos:
        brutos = campos_da_descricao(descricao)
        formato = "description"
    lon, lat = coordenadas(placemark)

    ponto: dict = {
        "pasta": pasta,
        "nome_marcador": (nome or "").strip() or None,
        "formato": formato,
        "campos": brutos,
    }
    # Chaves que os importadores leem — as mesmas do gaspar-cotas-2020.json.
    por_norm = {_norm(k): (k, v) for k, v in brutos.items()}
    ponto["cota_rotulo"], ponto["cota"], ponto["cota_campo"] = None, None, None
    for candidato in CAMPOS_DE_COTA:
        if candidato in por_norm:
            original, valor = por_norm[candidato]
            ponto["cota_rotulo"], ponto["cota"], ponto["cota_campo"] = valor, numero(valor), original
            break
    if ponto["cota_campo"] is None and nome and RE_COTA_NO_NOME.match(nome.strip()):
        m = RE_COTA_NO_NOME.match(nome.strip())
        ponto["cota_rotulo"], ponto["cota"], ponto["cota_campo"] = nome.strip(), numero(m.group(1)), "nome_marcador"
    for candidato in CAMPOS_DE_LAMINA:
        if candidato in por_norm:
            ponto["lamina_local_rotulo"] = por_norm[candidato][1].strip() or None
            ponto["lamina_local_m"] = numero(por_norm[candidato][1])
            break
    for origem, destino in SINONIMOS.items():
        if origem in por_norm and destino not in ponto:
            ponto[destino] = por_norm[origem][1].strip() or None
    for chave in ("sequencia", "obs", "esquina_co", "descrição", "coord_x", "coord_y", "_titulo"):
        if chave in brutos:
            ponto[chave] = brutos[chave].strip() or None
    ponto["lon"], ponto["lat"] = lon, lat
    return ponto


def pontos_do_kml(texto_xml: str) -> list[dict]:
    raiz = ET.fromstring(texto_xml)
    saida: list[dict] = []

    def visita(no, pasta):
        for filho in no:
            tag = _local(filho.tag)
            if tag == "Folder":
                nome = next((el.text for el in filho if _local(el.tag) == "name"), None)
                visita(filho, (nome or "").strip() or pasta)
            elif tag == "Placemark":
                saida.append(ponto_de(filho, pasta))
            elif tag in ("Document", "kml"):
                visita(filho, pasta)
    visita(raiz, None)
    return saida


def resumo(pontos: list[dict]) -> dict:
    sem_cota = [p for p in pontos if p["cota"] is None]
    pastas: dict[str, int] = {}
    formatos: dict[str, int] = {}
    for p in pontos:
        pastas[p["pasta"] or "(sem pasta)"] = pastas.get(p["pasta"] or "(sem pasta)", 0) + 1
        formatos[p["formato"]] = formatos.get(p["formato"], 0) + 1
    return {"total": len(pontos), "com_cota": len(pontos) - len(sem_cota),
            "sem_cota": len(sem_cota), "pastas": pastas, "formatos": formatos}


def montar(pontos: list[dict], origem: Path, texto: str) -> dict:
    r = resumo(pontos)
    return {
        "_meta": {
            "descricao": "Pontos de um KML do Google My Maps, convertidos por scripts/kml_para_json.py.",
            "origem": str(origem),
            "sha256_do_kml": hashlib.sha256(texto.encode("utf-8")).hexdigest(),
            "convertido_em": date.today().isoformat(),
            "total": r["total"], "com_cota": r["com_cota"], "sem_cota": r["sem_cota"],
            "pastas": r["pastas"], "formatos": r["formatos"],
            "o_que_e_cada_campo": {
                "campos": "TODOS os campos da fonte, como vieram (ExtendedData ou linhas do <description>)",
                "cota_rotulo": "o campo de cota da fonte, como texto; `cota` é o mesmo em número",
                "cota_campo": ("de onde a cota saiu: 'cota' (Gaspar, Brusque 2011) ou 'nome_marcador' "
                               "(Brusque 2023 e Ituporanga, onde o <name> é a cota)"),
                "lamina_local_m": ("'Nível registrado no local' (Brusque 2023): LÂMINA d'água medida no ponto, "
                                   "não cota — cota + lâmina = 8,96 m (pico de 17/11/2023) em 337 de 343 pontos"),
                "rua/esquina": "refer_1/refer_2 (Gaspar) ou ruas/esquina (Brusque)",
                "nome_marcador": "o <name> do marcador — em Gaspar é a cota com três casas; não é a cota_rotulo",
                "lon/lat": "do <coordinates> do ponto",
            },
            "atencao": ("Um campo chamado 'cota' NÃO prova ser nível de régua — ver analisar_kml_gaspar.py "
                        "e analisar_kml_brusque.py antes de importar."),
        },
        "pontos": pontos,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("kml", type=Path)
    ap.add_argument("--saida", type=Path, default=None, help="JSON de destino (padrão: só imprime o resumo)")
    ap.add_argument("--forcar", action="store_true", help="sobrescreve o destino se já existir")
    args = ap.parse_args()

    texto = args.kml.read_text(encoding="utf-8")
    pontos = pontos_do_kml(texto)
    r = resumo(pontos)
    print(f"{r['total']} placemark(s); {r['com_cota']} com cota, {r['sem_cota']} sem; "
          f"formatos {r['formatos']}; pastas {r['pastas']}")
    for p in [p for p in pontos if p["cota"] is None][:10]:
        print(f"   sem cota: {p['nome_marcador']!r} campos={list(p['campos'])[:6]}", file=sys.stderr)
    if r["total"] and r["com_cota"] == 0:
        print("ERRO: nenhum ponto tem cota — o formato não foi reconhecido. Nada gravado.", file=sys.stderr)
        return 2
    if args.saida is None:
        return 0
    if args.saida.exists() and not args.forcar:
        print(f"{args.saida} já existe; use --forcar para sobrescrever.", file=sys.stderr)
        return 3
    args.saida.write_text(json.dumps(montar(pontos, args.kml, texto), ensure_ascii=False, indent=2) + "\n",
                          encoding="utf-8")
    print(f"gravado em {args.saida}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
