#!/usr/bin/env python3
"""Busca no inventário público da ANA a COORDENADA e o TIPO das estações que faltam.

POR QUE EXISTE (07/09/2026)
O cruzamento de 06/09 com o inventário (`docs/INVENTARIO-ANA.md`) deixou oito
candidatos a `codigo_ana` com metade da prova. A regra emendada do projeto exige
**coordenada E tipo** — porque quatro pluviômetros caem a menos de 750 m de uma
régua nossa, com o nome certo e o município certo, e um deles viraria "série
histórica de nível" que na verdade é chuva. Falta a coordenada de quase todos, e
sem ela o vínculo não se escreve.

Este script pega essa metade que falta, para as estações que a gente já sabe
quais são. Ele **não escreve** em `estacoes.json`: imprime o que achou e a
distância até o pino de cada cidade, e a decisão de gravar continua humana —
mesma divisão de `ana_hidroweb.py`.

⚠️ **DE ONDE ESTE SCRIPT NÃO RODA.** O ambiente de desenvolvimento deste
projeto tem `*.ana.gov.br` bloqueado na saída (403 no CONNECT do proxy, medido
em 07/09/2026). Rodar daqui devolve erro de rede, não dado vazio — e o script
diz isso em vez de gravar silêncio. Rode da máquina do Jefferson ou da VPS.

⚠️ **OS NOMES DOS CAMPOS NÃO FORAM CONFERIDOS CONTRA O SERVIÇO REAL**, pela
mesma razão. Por isso o parser é tolerante: procura cada informação por uma
LISTA de nomes possíveis, sem diferenciar maiúscula de minúscula, e quando não
encontra ele **imprime os nomes que o XML realmente trouxe** — para o conserto
ser de uma linha, e não uma caçada. Mesma disciplina de `ana_hidroweb.py`: não
chutar caminho de URL nem nome de campo e fingir que deu certo.

Uso:
    python3 scripts/ana_inventario.py                      # as pendentes
    python3 scripts/ana_inventario.py --estacao 83250000
    python3 scripts/ana_inventario.py --arquivo resposta.xml   # XML já salvo
    python3 scripts/ana_inventario.py --json data/brutos/ana-inventario.json
"""

from __future__ import annotations

import argparse
import json
import math
import sys
import xml.etree.ElementTree as ET
from datetime import date
from pathlib import Path

from comum import DADOS, USER_AGENT, baixar, espera_turno, le_json

#: Endpoint público do inventário, o mesmo que a página do HidroWeb consome.
#: NÃO exige autenticação — diferente da API de séries, que é a do
#: `ana_hidroweb.py` e continua esperando credencial.
BASE = "http://telemetriaws1.ana.gov.br/ServiceANA.asmx/HidroInventario"

#: As oito que travam um `codigo_ana`, com a cidade que cada uma destravaria.
#: Fonte da lista: `docs/INVENTARIO-ANA.md`, seção "Os vínculos que não foram
#: escritos". Brusque saiu daqui em 07/09/2026 — fechou por outro caminho.
PENDENTES = {
    "83250000": ("ituporanga", "ITUPORANGA — fluviométrica no Itajaí do Sul, 1.650 km², desde 1929"),
    "83145140": ("ituporanga", "DCSC BARRAGEMSUL JUSANTE — a 45 m da DCSC-00039; falta o TIPO"),
    "83520000": ("indaial", "WARNOW — sucessora da 83690000, 9.790 km², desde 1927"),
    "83870001": ("ilhota", "ILHOTA-JUSANTE — sucessora, 12.357 km²"),
    "83440000": ("ibirama", "IBIRAMA — escala encerrada em 12/2021, precisa de sucessora"),
    "83892998": ("botuvera", "BOTUVERA-MONTANTE — 827 km², a 3,5 km da DCSC-00018 (provável OUTRA)"),
    "83094000": ("rio-do-sul", "RIO DO SUL (Oeste) — a 35 m da DCSC-00013; conflita com a 83300200"),
    "83030000": ("taio", "BARRAGEM OESTE — a 30 m da DCSC-00040; é barragem, não cidade"),
}

#: Cada informação por vários nomes possíveis. O serviço da ANA já publicou
#: essas colunas com grafias diferentes ao longo dos anos, e o inventário em
#: `.mdb` usa outras ainda. Procurar por lista custa nada e evita o parser
#: devolver `None` por causa de um acento.
ALIASES = {
    "codigo": ("codigo", "codigoestacao", "estacaocodigo"),
    "nome": ("nome", "estacaonome", "nmestacao"),
    "lat": ("latitude", "lat"),
    "lon": ("longitude", "lon", "long"),
    "altitude_m": ("altitude", "cotaaltitude"),
    "area_km2": ("areadrenagem", "area", "areadrenagemkm2"),
    "tipo": ("tipoestacao", "tipo", "tipoestacaocodigo"),
    "rio": ("nomerio", "nmrio", "rio"),
    "municipio": ("nomemunicipio", "nmmunicipio", "municipio"),
    "escala_inicio": ("periodoescalainicio", "escalainicio", "datainiescala"),
    "escala_fim": ("periodoescalafim", "escalafim", "datafimescala"),
}

#: A ANA codifica o tipo como 1 = fluviométrica, 2 = pluviométrica. É a
#: distinção que a regra emendada existe para checar, então ela fica explícita
#: aqui em vez de virar um `== "1"` solto no meio do código.
TIPOS = {"1": "fluviometrica", "2": "pluviometrica"}


def normaliza(nome: str) -> str:
    """`PeriodoEscalaInicio` e `periodo_escala_inicio` viram a mesma chave."""
    return "".join(ch for ch in nome.lower() if ch.isalnum())


def campo(registro: dict[str, str], qual: str):
    """O valor de `qual`, procurado por todos os nomes que ele pode ter."""
    for alias in ALIASES[qual]:
        if alias in registro and registro[alias] not in (None, ""):
            return registro[alias]
    return None


def numero(valor):
    """Vírgula decimal e ponto decimal convivem nas respostas da ANA."""
    if valor in (None, ""):
        return None
    try:
        return float(str(valor).strip().replace(",", "."))
    except ValueError:
        return None


def registros_do_xml(texto: str) -> list[dict[str, str]]:
    """Cada `<Table>` da resposta vira um dicionário de chaves normalizadas."""
    raiz = ET.fromstring(texto)
    saida = []
    for tabela in raiz.iter():
        filhos = list(tabela)
        if not filhos or any(len(f) for f in filhos):
            continue  # nó de estrutura, não registro
        reg = {normaliza(f.tag.split("}")[-1]): (f.text or "").strip() for f in filhos}
        if any(a in reg for a in ALIASES["codigo"]):
            saida.append(reg)
    return saida


def estacao(reg: dict[str, str]) -> dict:
    tipo_bruto = campo(reg, "tipo")
    return {
        "codigo": campo(reg, "codigo"),
        "nome": campo(reg, "nome"),
        "lat": numero(campo(reg, "lat")),
        "lon": numero(campo(reg, "lon")),
        "altitude_m": numero(campo(reg, "altitude_m")),
        "area_drenagem_km2": numero(campo(reg, "area_km2")),
        "tipo": TIPOS.get(str(tipo_bruto).strip(), None),
        "tipo_bruto": tipo_bruto,
        "rio": campo(reg, "rio"),
        "municipio": campo(reg, "municipio"),
        "escala_inicio": campo(reg, "escala_inicio"),
        "escala_fim": campo(reg, "escala_fim"),
        "campos_no_xml": sorted(reg),
    }


def busca(codigo: str) -> list[dict]:
    url = (f"{BASE}?codEstDE={codigo}&codEstATE={codigo}&tpEst=&nmEst=&nmRio="
           "&codSubBacia=&codBacia=&nmMunicipio=&nmEstado=&sgResp=&sgOper=&telemetrica=")
    espera_turno()
    return [estacao(r) for r in registros_do_xml(baixar(url))]


def metros(a: tuple[float, float], b: tuple[float, float]) -> float:
    dy = (b[0] - a[0]) * 111320
    dx = (b[1] - a[1]) * 111320 * math.cos(math.radians((a[0] + b[0]) / 2))
    return math.hypot(dx, dy)


def pino_da_cidade(cidade_id: str):
    for rio in le_json("estacoes.json")["rios"].values():
        for c in rio["cidades"]:
            if c["id"] == cidade_id and c.get("coordenadas"):
                return tuple(c["coordenadas"])
    return None


def relata(achadas: list[dict]) -> None:
    for e in achadas:
        cidade_id, porque = PENDENTES.get(str(e["codigo"]), (None, ""))
        print(f"\n=== {e['codigo']} {e['nome']}")
        if porque:
            print(f"    esperado: {porque}")
        if e["tipo"] is None:
            print(f"    ⚠️ TIPO não reconhecido (bruto: {e['tipo_bruto']!r}). "
                  f"Campos que o XML trouxe: {', '.join(e['campos_no_xml'])}")
        else:
            print(f"    tipo: {e['tipo'].upper()}"
                  + ("  ⛔ MEDE CHUVA — não serve como codigo_ana"
                     if e["tipo"] != "fluviometrica" else ""))
        if e["lat"] is None or e["lon"] is None:
            print(f"    ⚠️ SEM COORDENADA na resposta. "
                  f"Campos que o XML trouxe: {', '.join(e['campos_no_xml'])}")
            continue
        print(f"    coordenada: {e['lat']}, {e['lon']}"
              f"   área: {e['area_drenagem_km2']} km²"
              f"   escala: {e['escala_inicio']} → {e['escala_fim'] or 'aberta'}")
        pino = pino_da_cidade(cidade_id) if cidade_id else None
        if pino:
            d = metros(pino, (e["lat"], e["lon"]))
            print(f"    distância ao pino de {cidade_id}: {d:,.0f} m"
                  + ("   ✅ mesma régua" if d < 200 else
                     "   ⚠️ perto, conferir" if d < 1000 else
                     "   ❌ é OUTRA estação — não vincular"))
        print("    → para gravar: acrescente à ESTACOES_ANA_CONHECIDAS do validador\n"
              f"      \"{e['codigo']}\": ({e['nome']!r}, {e['tipo']!r}, "
              f"{e['lat']}, {e['lon']}, {e['escala_fim']!r}),")


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--estacao", action="append", help="código a buscar (repetível)")
    p.add_argument("--arquivo", type=Path, help="XML já salvo, em vez de baixar")
    p.add_argument("--json", type=Path, help="grava o resultado bruto neste arquivo")
    args = p.parse_args(argv)

    if args.arquivo:
        achadas = [estacao(r) for r in registros_do_xml(args.arquivo.read_text(encoding="utf-8"))]
    else:
        codigos = args.estacao or sorted(PENDENTES)
        achadas = []
        for codigo in codigos:
            try:
                achadas.extend(busca(codigo))
            except Exception as erro:  # rede, XML inválido, serviço fora
                print(f"⚠️ {codigo}: {type(erro).__name__}: {erro}", file=sys.stderr)

    if not achadas:
        print("Nenhuma estação lida. Se o erro acima é de rede, este ambiente "
              "bloqueia *.ana.gov.br — rode de fora. Nada foi gravado.",
              file=sys.stderr)
        return 1

    relata(achadas)

    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(json.dumps(
            {"_meta": {"fonte": BASE, "lido_em": date.today().isoformat(),
                       "user_agent": USER_AGENT},
             "estacoes": achadas}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"\nbruto gravado em {args.json}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
