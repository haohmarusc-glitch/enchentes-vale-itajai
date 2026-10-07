#!/usr/bin/env python3
"""
Coleta a chuva acumulada publicada pela Defesa Civil de Itajaí.

Fonte: https://monitoramento.defesacivil.itajai.sc.gov.br/monitoramento/chuvas
(portal NOVO, o mesmo de `coleta_itajai_portal.py`).

POR QUE A FONTE MUDOU (07/10/2026)
----------------------------------
O endereço antigo, `defesacivil.itajai.sc.gov.br/monitoramento/chuvas`, passou a
devolver **HTTP 200 com uma casca de aplicação de 641 bytes** (`<div id="root">`,
sem dado nenhum) — a mesma para qualquer caminho do host. O analisador antigo não
achava estação nenhuma, devolvia lista vazia, e lista vazia era lida como "a fonte
não publica pluviômetro": o `ultimo.json` saía com `chuva_ok: true` e nenhuma
estação de Itajaí. A última chuva de Itajaí na cópia das séries (`arquivo-series`)
é de 19/09/2026 17:30–17:31, as doze estações. Bruto da casca:
`data/brutos/itajai-portal-2026-10-07/defesacivil-itajai-casca-spa.html`.

O CONTRATO, lido no corpo real (198.851 bytes, 07/10/2026 14h49 UTC)
---------------------------------------------------------------------
App Inertia, como a página de rios: `<div id="app" data-page="{...}">`, com
`props.municipioId == 1` e `props.estacoes`, doze estações DC00…DC11. De cada uma:

    codigo                    "DC00" … "DC11" — sem hífen
    latitude/longitude        a posição da estação
    chuva_10_min_mm, chuva_1_h_mm, chuva_12_h_mm, chuva_24_h_mm, chuva_48_h_mm
    qualidade.<janela>.{estado, medido_em}   carimbo de cada janela, UTC com offset
    serie_12_h                [{medido_em, chuva_mm}] — incrementos de 10 min

UNIDADE CONFERIDA, não suposta: a soma da `serie_12_h` bate com `chuva_12_h_mm` em
todas as doze (diferença de até 0,4 mm, o balde que cai na borda da janela). Bruto:
`data/brutos/itajai-portal-2026-10-07/itajai-portal-chuvas-municipio-1.html`.

AS REGRAS, herdadas do coletor de rios e pelos mesmos motivos
--------------------------------------------------------------
1. **Identidade pela coordenada**, contra o cadastro (`estacoes_tempo_real`), com a
   mesma folga de `coleta_itajai_portal.TOLERANCIA_COORD_M`. DC-01…DC-11 batem a
   0,0 m. A **DC-00** ("Defesa Civil de Itajaí", pluviômetro puro) não tem
   coordenada no cadastro e por isso fica de fora até alguém decidir cadastrá-la —
   nome igual não prova estação igual.
2. **O título sai do cadastro.** É o MESMO título das séries antigas (conferido nas
   doze, contra `arquivo-series`), então a série de chuva continua sem quebra.
3. **`medido_em` em Brasília, sem fuso.** O carimbo é o das janelas
   (`qualidade.*.medido_em`); se diferirem, vale o MAIS ANTIGO — nunca rejuvenescer
   uma leitura. `consultadoEm` não entra.
4. **Página que não é a esperada é FALHA, não ausência.** HTML sem `data-page`,
   página de outro município, lista de estações vazia, estação sem as cinco janelas
   ou com valor que não é número de chuva: `parse()` levanta erro, e
   `coleta_niveis.baixar_chuva` marca `chuva_ok: false`. Status 200 não prova nada.
   Janela ausente (`null`, ou `estado: "sem_dados"`) continua ausente — nunca zero.

DUAS COISAS QUE A FONTE **NÃO** DÁ, e que não serão inventadas aqui:

* **Não existe acumulado de 6 h.** As janelas publicadas são 10 min, 1 h, 12 h,
  24 h e 48 h. Estimar 6 h dividindo o de 12 h suporia chuva constante, que é
  justamente o que ela não é numa cheia — a metade final de um período de 12 h
  pode conter toda a chuva. Um número inventado com cara de medição é o pior
  resultado possível numa tela que gente usa para decidir sair de casa.
* **Não é radar.** Isto é pluviômetro: mede a chuva que caiu NAQUELE ponto.
  Radar estima intensidade sobre uma área e não vira milímetro acumulado
  confiável.

TRAVA DE COERÊNCIA
------------------
As janelas são encaixadas: os últimos 10 min estão dentro da última hora, que
está dentro das últimas 12 h, e assim por diante. Então o acumulado tem de ser
não-decrescente. A fonte já publicou série que viola isso — a estação Guarani, em
Brusque, registrava 0,20 mm nos últimos 10 minutos e 0,00 mm em 1 h, 12 h, 24 h
e 48 h no mesmo instante. Zero ali quase certamente significa "sem dado", não
"não choveu", e mostrar 0 mm na tela ao lado de uma estação vizinha com 39 mm
mandaria a pessoa exatamente para o lado errado.

Quando a sequência não fecha, a leitura vai marcada (`coerente: false`) com o
que exatamente não fecha, e o site mostra "dado inconsistente na fonte" em vez
de número.

A PÁGINA ANTIGA fica legível por `parse_pagina_antiga()`, só para reler capturas
guardadas (`--antiga --arquivo`); nenhum caminho de coleta a usa.

Uso:
    python3 scripts/coleta_chuva.py             # baixa e mostra
    python3 scripts/coleta_chuva.py --json      # despeja o JSON
    python3 scripts/coleta_chuva.py --arquivo pagina.html   # sem rede
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone

from comum import classificar_estacao, estacoes_tempo_real

URL = "https://monitoramento.defesacivil.itajai.sc.gov.br/monitoramento/chuvas"

#: O endereço antigo — hoje uma casca vazia com HTTP 200. Só para documentação.
URL_ANTIGA = "https://defesacivil.itajai.sc.gov.br/monitoramento/chuvas"

#: `props.municipioId` da página lida.
MUNICIPIO_ITAJAI = 1

#: Campo do portal → janela do projeto, da mais curta para a mais longa.
CAMPOS_PORTAL = (
    ("chuva_10_min_mm", "min10"),
    ("chuva_1_h_mm", "h1"),
    ("chuva_12_h_mm", "h12"),
    ("chuva_24_h_mm", "h24"),
    ("chuva_48_h_mm", "h48"),
)

#: Teto do que pode ser chuva acumulada em 48 h num pluviômetro desta bacia. A
#: maior chuva de 2008 em Blumenau foi ~1.000 mm em semanas; acima disto em 48 h
#: o número não é chuva, é defeito.
CHUVA_MAXIMA_MM = 1000.0

#: Da janela mais curta para a mais longa. A ordem É a regra de coerência.
JANELAS = [
    ("min10", r"Chuva nos [úu]ltimos 10 minutos"),
    ("h1", r"Chuva acumulada 1h"),
    ("h12", r"Chuva acumulada 12h"),
    ("h24", r"Chuva acumulada 24h"),
    ("h48", r"Chuva acumulada 48h"),
]

RE_DATA = re.compile(
    r"Data e hora da medi[cç][aã]o:\s*(\d{2}/\d{2}/\d{4})\s+(\d{2}:\d{2})", re.I
)


def _mm(texto: str, padrao: str) -> float | None:
    """O valor em mm de uma janela, ou None quando a fonte não publicou."""
    m = re.search(padrao + r":?\s*([\d.,]+)\s*mm", texto, re.I)
    if not m:
        return None
    return float(m.group(1).replace(".", "").replace(",", "."))


def bloco_da_estacao(h2):
    """Sobe do <h2> até o <li> da estação — o título fica dentro de um <header>."""
    for candidato in (h2.find_parent("li"), h2.find_parent("article"),
                      h2.parent.parent if h2.parent else None, h2.parent):
        if candidato is not None:
            return candidato
    return h2


def incoerencias(mm: dict, ordem: list[str] | None = None) -> list[str]:
    """
    O que não fecha nesta leitura.

    Janela curta não pode ter mais chuva que janela longa que a contém. Compara
    só pares em que os dois valores existem: janela ausente é ausência de dado,
    não zero.

    `ordem` permite reusar a MESMA regra em fontes que nomeiam as janelas de
    outro jeito — a de Gaspar usa `chuva_atual/chuva_1h/...` e tem uma janela de
    6 h que esta não tem. Uma segunda implementação da regra seria uma regra a
    mais para divergir, e é sempre a cópia esquecida que passa a aceitar lixo.
    """
    problemas = []
    nomes = ordem if ordem is not None else [nome for nome, _ in JANELAS]
    presentes = [(nome, mm[nome]) for nome in nomes if mm.get(nome) is not None]
    for (nome_a, valor_a), (nome_b, valor_b) in zip(presentes, presentes[1:]):
        # Tolerância de 0,05 mm: a fonte publica com uma casa e o balde do
        # pluviômetro tem passo de 0,2 mm. Diferença menor que isso é
        # arredondamento, não contradição.
        if valor_a > valor_b + 0.05:
            problemas.append(f"{nome_a}={valor_a:g} mm > {nome_b}={valor_b:g} mm")
    return problemas


class FonteInvalida(ValueError):
    """A resposta não é a página de chuvas esperada — falha, não ausência."""


def _mm_valido(valor) -> bool:
    return (valor is None) or (isinstance(valor, (int, float)) and not isinstance(valor, bool)
                               and 0.0 <= float(valor) <= CHUVA_MAXIMA_MM)


def _cadastro_por_codigo() -> dict[str, dict]:
    return {e["codigo"]: e for e in estacoes_tempo_real()
            if isinstance(e.get("codigo"), str) and e["codigo"].startswith("DC-")}


def parse(pagina: str) -> list[dict]:
    """
    As leituras de chuva das estações DC do portal novo.

    Levanta `FonteInvalida` quando a resposta não é a página esperada — inclusive
    com HTTP 200. Estação isolada que não passa nas regras é recusada com o motivo
    no stderr; se NENHUMA passar, também é falha.
    """
    from coleta_itajai_portal import (TOLERANCIA_COORD_M, carga, conferir_municipio,
                                      distancia_m, para_brasilia)

    if not isinstance(pagina, str) or not pagina.strip():
        raise FonteInvalida("resposta vazia")
    dados = carga(pagina)
    if not dados:
        raise FonteInvalida(f"a resposta não traz o data-page do portal ({len(pagina)} bytes) — "
                            "provavelmente HTML de erro ou casca vazia")
    motivo = conferir_municipio(dados, MUNICIPIO_ITAJAI)
    if motivo is not None:
        raise FonteInvalida(motivo)
    props = dados.get("props") or {}
    if props.get("secao") not in (None, "chuvas"):
        raise FonteInvalida(f"a página é da seção {props.get('secao')!r}, não de chuvas")
    estacoes = props.get("estacoes")
    if not isinstance(estacoes, list) or not estacoes:
        raise FonteInvalida("a página não traz lista de estações")

    cadastro = _cadastro_por_codigo()
    leituras: list[dict] = []
    recusadas: list[str] = []
    for e in estacoes:
        if not isinstance(e, dict):
            recusadas.append("item que não é estação")
            continue
        cru = str(e.get("codigo") or "")
        m = re.fullmatch(r"DC-?(\d{2})", cru)
        if not m:
            recusadas.append(f"código não reconhecido: {cru!r}")
            continue
        codigo = f"DC-{m.group(1)}"
        nossa = cadastro.get(codigo)
        if nossa is None:
            recusadas.append(f"{codigo}: fora do cadastro")
            continue

        # REGRA 1: coordenada confirma a identidade.
        lat, lon = nossa.get("lat"), nossa.get("lon")
        plat, plon = e.get("latitude"), e.get("longitude")
        if not all(isinstance(v, (int, float)) for v in (lat, lon, plat, plon)):
            recusadas.append(f"{codigo}: sem coordenada dos dois lados — não dá para provar "
                             "que é a mesma estação")
            continue
        dist = distancia_m((lat, lon), (plat, plon))
        if dist > TOLERANCIA_COORD_M:
            recusadas.append(f"{codigo}: publicada a {dist:.0f} m da cadastrada "
                             f"(teto {TOLERANCIA_COORD_M:.0f} m)")
            continue

        # Esquema: as cinco janelas têm de EXISTIR (valor pode ser null).
        faltam = [campo for campo, _ in CAMPOS_PORTAL if campo not in e]
        if faltam:
            recusadas.append(f"{codigo}: sem os campos {', '.join(faltam)} — não é o esquema esperado")
            continue
        qualidade = e.get("qualidade") if isinstance(e.get("qualidade"), dict) else {}
        mm: dict[str, float | None] = {}
        carimbos: list[str] = []
        invalida = None
        for campo, nome in CAMPOS_PORTAL:
            valor = e.get(campo)
            q = qualidade.get(campo) if isinstance(qualidade.get(campo), dict) else {}
            if q.get("estado") == "sem_dados":
                valor = None
            if not _mm_valido(valor):
                invalida = f"{campo}={valor!r} não é chuva em mm"
                break
            mm[nome] = None if valor is None else float(valor)
            if valor is not None:
                quando = para_brasilia(q.get("medido_em")) or para_brasilia(e.get("medido_em"))
                if quando is None:
                    invalida = f"{campo} sem horário de medição legível"
                    break
                carimbos.append(quando)
        if invalida:
            recusadas.append(f"{codigo}: {invalida}")
            continue
        if all(v is None for v in mm.values()):
            recusadas.append(f"{codigo}: nenhuma janela publicada")
            continue

        titulo = nossa["titulo"]  # REGRA 2
        rio, cidade = classificar_estacao(titulo)
        problemas = incoerencias(mm)
        leituras.append({
            "estacao": titulo,
            "rio": rio,
            "cidade": cidade,
            "mm": mm,
            "medido_em": min(carimbos),  # REGRA 3: o mais antigo, Brasília sem fuso
            "coerente": not problemas,
            "incoerencias": problemas,
        })

    for msg in recusadas:
        print(f"chuva de Itajaí recusada — {msg}", file=sys.stderr)
    if not leituras:
        raise FonteInvalida(f"nenhuma das {len(estacoes)} estações passou nas regras")
    return leituras


def parse_pagina_antiga(html: str) -> list[dict]:
    """A página ANTIGA (fora do ar desde set/2026). Só para reler capturas guardadas."""
    try:
        from bs4 import BeautifulSoup
    except ImportError:
        sys.exit("Instale a dependência: pip install beautifulsoup4")
    soup = BeautifulSoup(html, "html.parser")
    leituras: list[dict] = []
    vistos: set[str] = set()

    for h2 in soup.find_all("h2"):
        titulo = h2.get_text(" ", strip=True)
        if not titulo or titulo in vistos:
            continue

        texto = " ".join(bloco_da_estacao(h2).get_text(" ", strip=True).split())
        mm = {nome: _mm(texto, padrao) for nome, padrao in JANELAS}
        if all(v is None for v in mm.values()):
            continue  # cabeçalho da página, ou estação sem dado (Blumenau)
        vistos.add(titulo)

        m_data = RE_DATA.search(texto)
        medido_em = None
        if m_data:
            medido_em = datetime.strptime(
                f"{m_data.group(1)} {m_data.group(2)}", "%d/%m/%Y %H:%M"
            ).isoformat()

        rio, cidade = classificar_estacao(titulo)
        problemas = incoerencias(mm)
        leituras.append({
            "estacao": titulo,
            "rio": rio,
            "cidade": cidade,
            "mm": mm,
            "medido_em": medido_em,  # hora local (America/Sao_Paulo), sem fuso
            "coerente": not problemas,
            "incoerencias": problemas,
        })
    return leituras


def coletar() -> dict:
    from comum import baixar, espera_turno

    espera_turno()
    return {
        "fonte": URL,
        "coletado_em": datetime.now(timezone.utc).isoformat(),
        "chuva": parse(baixar(URL)),
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--json", action="store_true", help="despeja o JSON")
    ap.add_argument("--arquivo", help="analisa um HTML salvo, sem rede")
    ap.add_argument("--antiga", action="store_true",
                    help="com --arquivo: lê a página ANTIGA (capturas de antes de set/2026)")
    args = ap.parse_args()

    if args.arquivo:
        ler = parse_pagina_antiga if args.antiga else parse
        dados = {"fonte": args.arquivo, "chuva": ler(open(args.arquivo, encoding="utf-8").read())}
    else:
        dados = coletar()

    if args.json:
        print(json.dumps(dados, ensure_ascii=False, indent=2))
        return 0

    chuva = dados["chuva"]
    print(f"{len(chuva)} estação(ões) com chuva publicada.\n")
    for c in sorted(chuva, key=lambda x: (str(x["cidade"]), x["estacao"])):
        mm = c["mm"]
        def v(nome):
            return "—" if mm.get(nome) is None else f"{mm[nome]:.1f}".replace(".", ",")
        print(f"  {c['cidade']} · {c['estacao']}")
        print(f"      1h {v('h1')} · 12h {v('h12')} · 24h {v('h24')} · 48h {v('h48')} mm"
              f"   (10 min: {v('min10')})")
        if not c["coerente"]:
            print(f"      ⚠ inconsistente na fonte: {'; '.join(c['incoerencias'])}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
