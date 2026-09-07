#!/usr/bin/env python3
"""O que FALTA na base, cidade por cidade — e o que cada buraco custa na tela.

POR QUE EXISTE (07/09/2026)
`conferir_cobertura.py` já mede quanto do rio fica cinza no mapa. Este script
responde a pergunta vizinha: **o que precisa ser procurado, e em que ordem.**
Ele não estima nada e não inventa nada; só cruza os arquivos de `data/` e diz,
para cada cidade, quais das sete camadas existem:

  1. leitura ao vivo     nível publicado agora (ultimo.json do branch tempo-real)
  2. cotas oficiais      atenção / alerta / emergência no Plano de Contingência
  3. cotas conferidas    `cotas_verificado: true` — lidas na fonte, não em resumo
  4. picos históricos    registros em enchentes.json (5+ para a previsão v1)
  5. série da ANA        `codigo_ana` conferido no HidroWeb
  6. cotas de rua        endereços com cota em cotas-ruas.json
  7. trânsito a jusante  trecho em transito.json ligando a cidade à de baixo

Cada camada acende uma parte diferente do site, e é isso que ordena a busca:
sem leitura o pino fica cinza; sem cota a cor não existe nem com leitura; sem
pico a previsão a jusante diz "dados insuficientes"; sem hora de pico o tempo
de trânsito continua sendo tabela de projeto, nunca medida.

CINZA NÃO É DEFEITO — é o site se recusando a afirmar o que não mediu. O que
este relatório mede é o tamanho da recusa.

Uso:
    python3 scripts/auditar_lacunas.py
    python3 scripts/auditar_lacunas.py --ao-vivo /tmp/ultimo.json
    python3 scripts/auditar_lacunas.py --markdown docs/LACUNAS-DE-DADOS.md
"""

from __future__ import annotations

import argparse
import collections
import json
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
DADOS = RAIZ / "data"

#: Mínimo de pares por trecho para a previsão a jusante v1 (CLAUDE.md).
PARES_MINIMOS = 5

#: As três faixas que a tela precisa para pintar cor. `monitoramento`,
#: `inundacao` e afins são extras de cada município, não substituem estas.
FAIXAS_ESSENCIAIS = ("atencao", "alerta")


def le(nome: str) -> dict:
    return json.loads((DADOS / nome).read_text(encoding="utf-8"))


def cidades_do_eixo(estacoes: dict) -> list[dict]:
    """Uma linha por (rio, cidade) — Itajaí aparece nos dois rios, de propósito."""
    saida = []
    for rio_id, rio in estacoes["rios"].items():
        for c in rio["cidades"]:
            saida.append({"rio": rio_id, **c})
    return saida


def proxima_a_jusante(estacoes: dict, rio_id: str, cidade: dict) -> str | None:
    """Quem recebe a água desta cidade, segundo a topologia canônica.

    No Açu a posição vem de `ramo` + `ordem_no_ramo` (é ÁRVORE, não fila); a
    última de um ramo lateral deságua no tronco, e aí o elo é declarado em
    `_topologia.afluentes_laterais`, não deduzido.
    """
    rio = estacoes["rios"][rio_id]
    topo = rio.get("_topologia")
    if not topo:
        ordem = cidade.get("ordem")
        if ordem is None:
            return None
        for outra in rio["cidades"]:
            if outra.get("ordem") == ordem + 1:
                return outra["id"]
        return None

    tronco = topo["tronco_sequencia"]
    if cidade["id"] in tronco:
        i = tronco.index(cidade["id"])
        return tronco[i + 1] if i + 1 < len(tronco) else None

    ramo, pos = cidade.get("ramo"), cidade.get("ordem_no_ramo")
    if ramo and pos is not None:
        for outra in rio["cidades"]:
            if outra.get("ramo") == ramo and outra.get("ordem_no_ramo") == pos + 1:
                return outra["id"]
    if cidade["id"] in topo.get("cabeceiras_paralelas", []):
        return topo["confluencia_cabeceiras"]["nasce"]
    for af in topo.get("afluentes_laterais", []):
        if af["id"] == cidade["id"]:
            return af["entra_perto_de"]
    return None


def auditar(ao_vivo: Path | None) -> dict:
    estacoes = le("estacoes.json")
    eventos = le("enchentes.json")["eventos"]
    transito = le("transito.json")["trechos"]
    ruas = le("cotas-ruas.json")["cotas"]

    picos = collections.Counter(e["cidade"] for e in eventos)
    com_rua = collections.Counter(r["cidade"] for r in ruas)
    com_coord_rua = collections.Counter(r["cidade"] for r in ruas if r.get("lat"))
    elos = {(t["de"], t["para"]) for t in transito}

    vivo: collections.Counter = collections.Counter()
    if ao_vivo and ao_vivo.exists():
        for l in json.loads(ao_vivo.read_text(encoding="utf-8")).get("leituras", []):
            if l.get("nivel_m") is not None:
                vivo[l.get("cidade")] += 1

    linhas = []
    for c in cidades_do_eixo(estacoes):
        cotas = c.get("cotas_m") or {}
        jusante = proxima_a_jusante(estacoes, c["rio"], c)
        linhas.append(
            {
                "rio": c["rio"],
                "id": c["id"],
                "nome": c["nome"],
                "vivo": vivo.get(c["id"], 0),
                "cotas": sorted(cotas),
                "cotas_essenciais": all(f in cotas for f in FAIXAS_ESSENCIAIS),
                "cotas_nenhuma": not cotas,
                "cotas_verificado": bool(c.get("cotas_verificado")),
                "picos": picos.get(c["id"], 0),
                "ana": c.get("codigo_ana"),
                "ana_verificado": bool(c.get("codigo_ana_verificado")),
                "ruas": com_rua.get(c["id"], 0),
                "ruas_com_coordenada": com_coord_rua.get(c["id"], 0),
                "jusante": jusante,
                "transito": (c["id"], jusante) in elos if jusante else None,
            }
        )

    manchas = le("manchas/index.json")["manchas"]
    mare = le("mare-itajai.json")
    dias_de_mare = sorted({p["quando"][:10] for p in mare["preamares"]})

    return {
        "linhas": linhas,
        "eventos": len(eventos),
        "eventos_com_hora": sum(1 for e in eventos if ":" in str(e.get("data", ""))),
        "eventos_so_ano": sum(1 for e in eventos if len(str(e.get("data", ""))) == 4),
        "eventos_sem_referencia": collections.Counter(
            e["cidade"] for e in eventos if e.get("referencia") is None
        ),
        "ruas_sem_coordenada": collections.Counter(
            r["cidade"] for r in ruas if not r.get("lat")
        ),
        "manchas": len(manchas),
        "manchas_por_cidade": collections.Counter(m["cidade"] for m in manchas),
        "manchas_sem_pico": sum(1 for m in manchas if not m.get("pico_registrado")),
        "mare_dias": len(dias_de_mare),
        "mare_ate": dias_de_mare[-1] if dias_de_mare else None,
        "mare_com_altura": any("altura_m" in p for p in mare["preamares"]),
        "mare_fonte": mare["_meta"].get("fonte", ""),
        "ao_vivo_lido": bool(vivo),
    }


def imprime(rel: dict) -> None:
    print(f"=== {rel['eventos']} picos históricos, {rel['eventos_com_hora']} com hora do pico")
    if not rel["ao_vivo_lido"]:
        print("=== SEM ao_vivo: rode com --ao-vivo para a coluna de leitura valer")
    print()
    cab = f"{'cidade':20s} {'rio':7s} {'vivo':>4s} {'cota':>5s} {'conf':>4s} {'pico':>4s} {'ANA':>4s} {'rua':>5s} {'trans':>5s}"
    print(cab)
    print("-" * len(cab))
    for l in rel["linhas"]:
        print(
            f"{l['nome']:20s} {l['rio'].replace('itajai-',''):7s} "
            f"{('sim' if l['vivo'] else '—'):>4s} "
            f"{('sim' if l['cotas_essenciais'] else '—'):>5s} "
            f"{('sim' if l['cotas_verificado'] else '—'):>4s} "
            f"{(str(l['picos']) if l['picos'] else '—'):>4s} "
            f"{('sim' if l['ana_verificado'] else '—'):>4s} "
            f"{(str(l['ruas']) if l['ruas'] else '—'):>5s} "
            f"{('sim' if l['transito'] else ('n/a' if l['transito'] is None else '—')):>5s}"
        )
    print()
    faltas = collections.Counter()
    for l in rel["linhas"]:
        if not l["vivo"]:
            faltas["sem leitura ao vivo"] += 1
        if not l["cotas_essenciais"]:
            faltas["sem cotas de atenção/alerta"] += 1
        if l["cotas_essenciais"] and not l["cotas_verificado"]:
            faltas["cotas não conferidas na fonte"] += 1
        if l["picos"] < PARES_MINIMOS:
            faltas[f"menos de {PARES_MINIMOS} picos"] += 1
        if not l["ana_verificado"]:
            faltas["sem série da ANA conferida"] += 1
        if not l["ruas"]:
            faltas["sem cotas de rua"] += 1
        if l["transito"] is False:
            faltas["sem trecho de trânsito a jusante"] += 1
    print("buracos, por quantas cidades atingem:")
    for k, v in faltas.most_common():
        print(f"  {v:3d}  {k}")


def markdown(rel: dict) -> str:
    """A matriz e a lista de busca, ambas derivadas do relatório — nada escrito à mão."""
    from datetime import date

    sim = lambda b: "sim" if b else "—"
    linhas = rel["linhas"]
    f = []
    f.append("# Lacunas de dados — o que falta e o que procurar\n\n")
    f.append(
        f"Gerado por `scripts/auditar_lacunas.py` em "
        f"{date.today().strftime('%d/%m/%Y')}. **Não editar à mão** — reexecutar.\n\n"
    )
    f.append(
        "Sete camadas por cidade. Cada uma acende uma parte diferente do site, e é\n"
        "isso que ordena a busca: sem leitura o pino fica cinza; sem cota a cor não\n"
        "existe nem com leitura; sem pico a previsão a jusante diz \"dados\n"
        "insuficientes\"; sem hora de pico o tempo de trânsito continua sendo tabela\n"
        "de projeto, nunca medida.\n\n"
    )

    f.append("## Matriz por cidade\n\n")
    f.append(
        "| Cidade | Rio | Leitura ao vivo | Cotas atenção+alerta | Cotas conferidas | "
        "Picos | Série ANA | Cotas de rua | Trânsito a jusante |\n"
        "|---|---|---|---|---|---|---|---|---|\n"
    )
    for l in linhas:
        tr = "n/a" if l["transito"] is None else sim(l["transito"])
        f.append(
            f"| {l['nome']} | {l['rio'].replace('itajai-', '')} | {sim(l['vivo'])} | "
            f"{sim(l['cotas_essenciais'])} | {sim(l['cotas_verificado'])} | "
            f"{l['picos'] or '—'} | {sim(l['ana_verificado'])} | "
            f"{l['ruas'] or '—'} | {tr} |\n"
        )
    f.append(
        "\n`n/a` em trânsito = a cidade é foz, ou entrou sem posição na árvore "
        "(Trombudo Central: a fonte diz o rio, não a confluência).\n"
    )

    def nomes(cond):
        """Nomes únicos — a matriz é por (rio, cidade), a lista é por cidade."""
        vistos, saida = set(), []
        for l in linhas:
            if cond(l) and l["id"] not in vistos:
                vistos.add(l["id"])
                saida.append(f"**{l['nome']}**")
        return ", ".join(saida) or "nenhuma"

    nome_de = {l["id"]: l["nome"] for l in linhas}

    f.append("\n## Lista de busca, por impacto\n")

    f.append("\n### 1. Leitura ao vivo — o pino cinza\n\n")
    f.append(
        f"Sem leitura em: {nomes(lambda l: not l['vivo'])}.\n\n"
        "É o que mais escurece o mapa e o único item que não tem substituto "
        "histórico: nenhuma pesquisa em acervo acende um pino hoje. O pedido é "
        "ofício à Defesa Civil do município pedindo o endpoint que a página de "
        "monitoramento já consome.\n"
    )

    f.append("\n### 2. Cotas oficiais — a cor que não existe nem com leitura\n\n")
    f.append(
        f"Sem cota nenhuma: {nomes(lambda l: l['cotas_nenhuma'])}.\n\n"
        f"Com cota incompleta (falta atenção ou alerta): "
        f"{nomes(lambda l: not l['cotas_nenhuma'] and not l['cotas_essenciais'])} — "
        "a tela não consegue pintar a faixa que falta.\n\n"
        f"Com as duas mas sem conferência na fonte: "
        f"{nomes(lambda l: l['cotas_essenciais'] and not l['cotas_verificado'])} — "
        "valor veio de resumo, levantamento ou imprensa, não de leitura do Plano "
        "de Contingência. Procurar o PDF do PLANCON de cada uma e guardar em "
        "`data/brutos/`.\n"
    )

    f.append("\n### 3. Hora do pico — o que destrava `transito.json`\n\n")
    f.append(
        f"**{rel['eventos']} picos na base, {rel['eventos_com_hora']} com hora.** "
        "Enquanto for zero, todo tempo de trânsito exibido é faixa de tabela de "
        "projeto (JICA/ABRH), nunca medida nesta bacia. `scripts/calibrar_transito.py` "
        "existe e não tem o que calibrar.\n\n"
        "A hora só existe em boletim de cheia: boletim diário da Defesa Civil "
        "estadual, ofício municipal do dia, série horária da ANA/HidroWeb.\n"
    )

    f.append("\n### 4. Picos históricos — a previsão a jusante\n\n")
    f.append(
        f"Menos de {PARES_MINIMOS} eventos (mínimo da previsão v1): "
        f"{nomes(lambda l: l['picos'] < PARES_MINIMOS)}.\n\n"
        f"Sem nenhum: {nomes(lambda l: l['picos'] == 0)}.\n"
    )
    if rel["eventos_so_ano"]:
        f.append(
            f"\n{rel['eventos_so_ano']} registros têm só o ano, sem mês nem dia — "
            "não pareiam com jusante nem com mancha.\n"
        )
    sem_ref = rel["eventos_sem_referencia"]
    if sem_ref:
        detalhe = ", ".join(f"{nome_de.get(c, c)} {n}" for c, n in sem_ref.most_common())
        f.append(
            f"\n{sum(sem_ref.values())} registros com `referencia: null` "
            f"({detalhe}). Em Blumenau isso é a REGRA BLOQUEANTE do "
            "`enchentes.json`: régua ou IBGE (régua + 0,20 m) muda o valor em "
            "20 cm. Resolve no HidroWeb, estação 83800002, cotas de 09/07/1983 e "
            "07/08/1984.\n"
        )

    f.append("\n### 5. Série da ANA — o acervo que fecha as lacunas de uma vez\n\n")
    f.append(
        f"Sem `codigo_ana` conferido no HidroWeb: "
        f"{nomes(lambda l: not l['ana_verificado'])}.\n\n"
        "Cada estação conferida traz série inteira de cota, com hora — resolve os "
        "itens 3 e 4 juntos para aquela cidade. É o item de maior alcance por "
        "unidade de esforço da lista.\n"
    )

    f.append("\n### 6. Cotas de rua — a busca \"minha rua\"\n\n")
    f.append(f"Sem nenhuma cota de rua: {nomes(lambda l: not l['ruas'])}.\n")
    sc = rel["ruas_sem_coordenada"]
    if sc:
        detalhe = ", ".join(f"**{nome_de.get(c, c)}** {n}" for c, n in sc.most_common())
        f.append(
            f"\nCom cota mas **sem coordenada** ({sum(sc.values())} endereços): "
            f"{detalhe}. Aparecem na busca por nome, não no mapa. "
            "Geocodificação pendente.\n"
        )

    f.append("\n### 7. Trânsito — os elos que faltam\n\n")
    faltando = [l for l in linhas if l["transito"] is False]
    if faltando:
        f.append("| De | Para | Rio |\n|---|---|---|\n")
        for l in faltando:
            f.append(
                f"| {l['nome']} | {nome_de.get(l['jusante'], l['jusante'])} | "
                f"{l['rio'].replace('itajai-', '')} |\n"
            )
    else:
        f.append("Todos os elos da topologia têm trecho.\n")

    f.append("\n### 8. Maré de Itajaí\n\n")
    f.append(
        f"Tábua cobre **{rel['mare_dias']} dias, até {rel['mare_ate']}**; "
        f"altura em metros: {'sim' if rel['mare_com_altura'] else '**não** (só horário)'}.\n\n"
        "Depois dessa data a tela da foz fica sem maré. A altura foi omitida de "
        "propósito porque o datum da planilha não está conferido contra o da "
        "DHN — mesmo problema do datum de Blumenau. Procurar a tábua anual do "
        "CHM/Marinha para o porto de Itajaí.\n"
    )

    f.append("\n### 9. Manchas de inundação\n\n")
    porc = ", ".join(
        f"{nome_de.get(c, c)} {n}" for c, n in rel["manchas_por_cidade"].most_common()
    )
    f.append(
        f"{rel['manchas']} manchas, todas de uma cidade ({porc}); "
        f"{rel['manchas_sem_pico']} sem pico associado.\n\n"
        "Sem o pico daquele evento na cidade, a mancha mostra onde a água chegou "
        "mas não a que nível — não dá para ler como \"se o rio chegar a X\". "
        "Nenhuma outra cidade da bacia tem mancha publicada aqui.\n"
    )
    return "".join(f)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--ao-vivo", type=Path, help="ultimo.json do branch tempo-real")
    p.add_argument("--markdown", type=Path, help="grava a matriz em Markdown")
    args = p.parse_args(argv)

    rel = auditar(args.ao_vivo)
    imprime(rel)
    if args.markdown:
        args.markdown.write_text(markdown(rel), encoding="utf-8")
        print(f"\nmatriz gravada em {args.markdown}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
