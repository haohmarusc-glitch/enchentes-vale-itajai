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


def tipo_do_elo(estacoes: dict, rio_id: str, de: str, para: str) -> tuple[str, str]:
    """
    Se este trecho for MEDIDO numa cheia, o vão entre os picos é um tempo de
    trânsito? Devolve (tipo, explicação).

    POR QUE EXISTE (07/09/2026). `por_que_falta_o_elo` responde "adianta
    procurar na FONTE?". Esta responde outra coisa: "adianta MEDIR?". Elas se
    separaram quando a série da rede estadual passou a permitir datar picos em
    dez cidades que não têm régua municipal — de repente todos os elos ficaram
    mensuráveis, e mensurável não é o mesmo que significativo.

    * **`roteamento`** — a cheia VIAJA de um ponto ao outro, pelo mesmo curso.
      O vão entre os picos é o tempo de viagem. Vale medir.
      É o caso de tronco→tronco (`rio-do-sul → lontras`) e de afluente→afluente
      dentro do mesmo afluente (`rio-dos-cedros → timbo`, os dois no Benedito).

    * **`confluencia`** — uma ponta é afluente lateral e a outra é o tronco.
      Aqui NÃO há viagem: o pico do tronco vem da cheia que desce o tronco, e o
      do afluente vem da chuva na sub-bacia dele. O vão entre os dois é a
      coincidência de dois hidrogramas independentes — muda de valor, e até de
      SINAL, de cheia para cheia. Medir produziria um número com cara de tempo
      de trânsito que não é um.

    É a mesma família do `nao_positivo` de `indaial → blumenau`, e por isso a
    conclusão é a mesma: não é falta de busca nem de medição, é uma grandeza
    que não existe.

    O QUE ESTA FUNÇÃO NÃO SABE. O caso de Indaial → Blumenau — tronco→tronco
    COM um afluente desaguando no meio — não é pego aqui: `afluentes_laterais`
    diz `entra_perto_de`, e "perto de" não diz entre QUAIS duas cidades a
    confluência cai. Aquele elo continua sendo pego pelo `nao_positivo`, que
    olha os números da JICA. Enquanto a posição da confluência não estiver no
    dado, esta função classifica pelas PONTAS e não pelo trecho.
    """
    rio = estacoes["rios"][rio_id]
    topo = rio.get("_topologia")
    if not topo:
        return ("roteamento", "rio em fila: todo elo é viagem pelo mesmo curso")

    laterais = {a["id"]: a for a in topo.get("afluentes_laterais", ())}

    de_lateral, para_lateral = de in laterais, para in laterais
    if de_lateral != para_lateral:
        lateral = de if de_lateral else para
        return ("confluencia", (
            f"{lateral} é afluente lateral ({laterais[lateral]['rio']}) e a outra ponta está no "
            "tronco: o pico do tronco vem da cheia que desce o tronco, o do afluente vem da chuva "
            "na sub-bacia dele. O vão entre os dois é coincidência de hidrogramas, não viagem — "
            "muda de valor e até de sinal a cada cheia"))
    return ("roteamento", "as duas pontas estão no mesmo curso: o vão entre os picos é a viagem")


def por_que_falta_o_elo(de: str, para: str, fonte: dict, tabela: dict,
                        tipo: str = "roteamento") -> tuple[str, list[str]]:
    """
    Por que este trecho não existe — e, sobretudo, se procurar mais resolve.

    POR QUE EXISTE (07/09/2026). A primeira versão desta auditoria imprimiu os
    dez elos ausentes numa tabela só, sob o título "os elos que faltam". Lido
    como lista de tarefas, e não é: fui à fonte e **um deles não é coisa a
    procurar** — é perigoso de preencher.

    A pergunta que a classificação responde é uma só: **adianta procurar?**

    * **`sem_tempo_de_fonte`** — adianta. Ou a Tabela 7.5.1 da JICA não lista a
      cidade (Lontras, Ascurra, Vidal Ramos, Botuverá, Guabiruba, Rio dos
      Cedros), ou lista mas o número dela é o relógio da SUB-BACIA e não a
      viagem da cheia do Açu (Timbó no Benedito, Ibirama no Hercílio, Brusque
      no Mirim). Nos dois casos falta FONTE, e outra fonte resolveria.
    * **`nao_positivo`** — NÃO adianta. A JICA tem as duas pontas e a diferença
      é zero ou negativa. É Indaial -> Blumenau: +0 h nas cheias de 5 e 10 anos
      e **-1 h** nas de 25 e 50, porque o Rio Benedito entra entre as duas e
      ADIANTA o pico de baixo. Inventar um positivo aqui diria a quem está em
      Blumenau que tem horas que não tem. O elo não falta por falta de busca:
      ele não é um tempo de trânsito.

    Devolve todos os motivos que se aplicam, não só o primeiro. Rio dos Cedros
    -> Timbó tem dois (a cidade de cima não está na tabela E a de baixo tem
    relógio próprio), e ficar com um só esconderia metade do problema.

    ERRO QUE ESTA VERSÃO CONSERTA: a primeira olhava `relogio_proprio` nas duas
    pontas sem checar antes se a cidade está na tabela, e classificou
    Guabiruba -> Brusque como "relógio próprio". Não é: o relógio próprio de
    Brusque vale em relação ao AÇU; Guabiruba é vizinha dela no MIRIM, e o que
    falta ali é a JICA não listar Guabiruba.
    """
    # Elo de confluência não é pergunta de FONTE: a grandeza não existe, e
    # responder "falta procurar" mandaria alguém atrás de um número que não há.
    # Quem sabe disso é `tipo_do_elo`, que enxerga a topologia; esta função
    # recebe o veredito em vez de tentar deduzi-lo dos nomes.
    if tipo == "confluencia":
        proprio = set(fonte.get("relogio_proprio", ()))
        donos = [c for c in (de, para) if c in proprio]
        motivo = (
            f"{' e '.join(donos)} tem relógio próprio — o pico vem da chuva na sub-bacia, "
            "não da cheia descendo o Açu, então nem a tabela nem uma cheia medida dão tempo "
            "de roteamento aqui"
        ) if donos else (
            "uma ponta é afluente lateral e a outra está no tronco: não há viagem entre elas"
        )
        return ("confluencia", [motivo])

    na_tabela = set(fonte.get("cidades_na_tabela", ()))
    motivos = []

    fora = [c for c in (de, para) if c not in na_tabela]
    if fora:
        motivos.append(f"a Tabela 7.5.1 da JICA não lista {' nem '.join(fora)}")

    # RELÓGIO PRÓPRIO SAIU DAQUI EM 07/09/2026, e o motivo importa.
    #
    # `relogio_proprio` diz que o pico daquela cidade vem da chuva na SUB-BACIA
    # dela, e não da cheia descendo o AÇU. Isso é uma afirmação sobre o elo com
    # o TRONCO — e todo elo desses agora é classificado como `confluencia` por
    # `tipo_do_elo`, antes de chegar aqui.
    #
    # Onde a marca ainda disparava, ela dizia o contrário do certo:
    #
    #   * `rio-dos-cedros → timbo` — os dois no Benedito/Cedros. É roteamento
    #     DENTRO do afluente, e o relógio próprio de Timbó é justamente o que
    #     uma viagem Rio dos Cedros → Timbó explica. Dar isso como motivo para
    #     não haver o trecho inverte a leitura.
    #   * `guabiruba → brusque` — os dois no MIRIM. O relógio próprio de Brusque
    #     vale em relação ao Açu; aqui não tem nada a ver. A docstring acima já
    #     registrava esse erro como corrigido, mas só o TIPO tinha sido: o texto
    #     do motivo continuava saindo.
    #
    # Em ambos, o que falta mesmo é a JICA não listar a cidade de cima — e isso
    # o primeiro motivo já diz.

    if not fora:
        difs = {p: tabela[para][p] - tabela[de][p] for p in tabela[de]}
        if min(difs.values()) <= 0:
            faixa = ", ".join(f"{p} anos {d:+d} h"
                              for p, d in sorted(difs.items(), key=lambda x: int(x[0])))
            return ("nao_positivo", [
                f"a JICA tem as DUAS pontas e a diferença não é positiva ({faixa})",
                "o Rio Benedito entra entre as duas e adianta o pico de baixo",
                "não é um tempo de trânsito: inventar um positivo daria horas que não existem",
            ])
        motivos.append("a fonte cobre as duas pontas — o trecho simplesmente não foi escrito")

    return ("sem_tempo_de_fonte", motivos)


def primeira_frase(texto: str, limite: int = 140) -> str:
    """
    A primeira frase, sem partir número decimal nem coordenada ao meio.

    POR QUE EXISTE (08/09/2026). Cortar no primeiro `.` transformou
    "6,8 km entre a nossa régua (-27.38547 / -49.35812, ...)" em
    "...a nossa régua (-27" — um pedaço de coordenada, numa tabela sobre
    coordenadas. O corte é por `. ` (ponto seguido de espaço), que é fim de
    frase; `-27.38547` não tem espaço depois do ponto e sobrevive inteiro.
    """
    frase = (texto or "").split(". ")[0].strip().rstrip(".")
    if len(frase) > limite:
        frase = frase[:limite].rsplit(" ", 1)[0] + "…"
    return frase


def estado_da_busca_ana(c: dict) -> tuple[str, str]:
    """
    O que falta de fato para esta cidade ter série da ANA — três coisas, não uma.

    POR QUE EXISTE (08/09/2026). O item 5 listava as doze cidades sem código
    como se todas precisassem da mesma busca. Cinco não precisam:

    * `recusada` — a busca JÁ FOI FEITA e achou uma estação, que foi **rejeitada
      com distância medida**. Vidal Ramos é o caso: a SALSEIRO está a 6,8 km, no
      mesmo município e em outro ponto do rio. Mandar "procurar a estação de
      Vidal Ramos" sem dizer isso convida a trazer de volta a mesma estação
      recusada — que é exatamente como um pareamento errado entra. O projeto já
      pagou por isso em Brusque e no próprio Salseiro.
    * `decisao` — Ibirama tem candidata a 476 m e o que falta **não é busca**: é
      critério, e o traçado do Hercílio que o resolveria não está em `data/rios/`.
      Pedir busca aqui aponta para a tarefa errada.
    * `sem_busca` — ninguém olhou ainda. Só estas são busca de verdade.

    É a mesma divisão que o item 7 já faz para os elos de trânsito.
    """
    if c.get("codigo_ana_nao_e"):
        recusada = c["codigo_ana_nao_e"]
        return ("recusada", f"{recusada.get('codigo', '?')} {recusada.get('nome', '')}".strip())
    if c.get("codigo_ana_candidatos"):
        cands = c["codigo_ana_candidatos"]
        return ("decisao", ", ".join(
            f"{x.get('codigo', '?')} {x.get('nome', '')}".strip() for x in cands))
    return ("sem_busca", "")


def cotas_nas_reguas(estacoes: dict, cidade_id: str) -> dict:
    """
    Quantas RÉGUAS daquela cidade têm a escala completa — e quantas conferidas.

    POR QUE EXISTE (08/09/2026). O auditor só olhava `cotas_m` do nó da cidade,
    e por isso dizia **"Itajaí: sem cota nenhuma"** — mandando procurar o PDF do
    PLANCON de uma cidade cujas ONZE réguas citam esse PDF por URL e cujos onze
    valores foram conferidos, 11 de 11, contra a versão 17.

    O `cotas_m` vazio da cidade está CERTO: Itajaí não tem uma escala, tem onze,
    uma por régua, e um número só ali seria mentira. Errado era o auditor ler
    esse vazio como buraco. Buraco falso gasta o tempo de quem procura e, pior,
    ensina a desconfiar da lista inteira.
    """
    reguas = [e for e in estacoes.get("estacoes_tempo_real", [])
              if e.get("cidade") == cidade_id]
    com_escala = [e for e in reguas if all(f in (e.get("cotas_m") or {})
                                           for f in FAIXAS_ESSENCIAIS)]
    return {
        "total": len(reguas),
        "com_escala": len(com_escala),
        "conferidas": sum(1 for e in com_escala if e.get("verificado")),
    }


def auditar(ao_vivo: Path | None) -> dict:
    estacoes = le("estacoes.json")
    eventos = le("enchentes.json")["eventos"]
    transito_json = le("transito.json")
    transito = transito_json["trechos"]
    fonte_transito = transito_json["_meta"]["origem_das_faixas"]
    ruas = le("cotas-ruas.json")["cotas"]

    picos = collections.Counter(e["cidade"] for e in eventos)
    com_rua = collections.Counter(r["cidade"] for r in ruas)
    com_coord_rua = collections.Counter(r["cidade"] for r in ruas if r.get("lat"))
    elos = {(t["de"], t["para"]) for t in transito}

    vivo: collections.Counter = collections.Counter()
    ao_vivo_de = None
    if ao_vivo and ao_vivo.exists():
        bruto = json.loads(ao_vivo.read_text(encoding="utf-8"))
        ao_vivo_de = bruto.get("gerado_em") or bruto.get("coletado_em")
        for l in bruto.get("leituras", []):
            if l.get("nivel_m") is not None:
                vivo[l.get("cidade")] += 1

    linhas = []
    for c in cidades_do_eixo(estacoes):
        cotas = c.get("cotas_m") or {}
        reguas = cotas_nas_reguas(estacoes, c["id"])
        jusante = proxima_a_jusante(estacoes, c["rio"], c)
        linhas.append(
            {
                "rio": c["rio"],
                "id": c["id"],
                "nome": c["nome"],
                "vivo": vivo.get(c["id"], 0),
                "cotas": sorted(cotas),
                "cotas_essenciais": all(f in cotas for f in FAIXAS_ESSENCIAIS),
                "cotas_nenhuma": not cotas and not reguas["com_escala"],
                "cotas_verificado": bool(c.get("cotas_verificado")),
                # A escala pode morar nas RÉGUAS em vez de no nó da cidade.
                # Itajaí é assim: onze réguas, onze escalas, nenhuma "cota de
                # Itajaí". A cor da tela sai da régua, então é ela que decide
                # se a cor existe — não o nó.
                "reguas": reguas,
                "escala_por_regua": reguas["com_escala"] > 0 and not cotas,
                "picos": picos.get(c["id"], 0),
                "ana": c.get("codigo_ana"),
                "ana_verificado": bool(c.get("codigo_ana_verificado")),
                "ana_busca": estado_da_busca_ana(c)[0],
                "ana_estacao_fora": estado_da_busca_ana(c)[1],
                "ana_porque_fora": (c.get("codigo_ana_nao_e") or {}).get("por_que_nao", ""),
                "ruas": com_rua.get(c["id"], 0),
                "ruas_com_coordenada": com_coord_rua.get(c["id"], 0),
                "jusante": jusante,
                "transito": (c["id"], jusante) in elos if jusante else None,
            }
        )

    tabela = fonte_transito["tabela_7_5_1"]["matriz_horas_por_periodo_de_retorno"]
    for l in linhas:
        if l["transito"] is not False:
            continue
        # DUAS perguntas, não uma. `tipo_do_elo` diz se MEDIR faz sentido;
        # `por_que_falta_o_elo` diz se PROCURAR resolve. Um elo de confluência
        # não se resolve por nenhum dos dois caminhos — a grandeza não existe —,
        # então ele sai da lista de busca em vez de ficar nela para sempre.
        tipo, porque_tipo = tipo_do_elo(estacoes, l["rio"], l["id"], l["jusante"])
        l["transito_tipo"] = tipo
        l["transito_porque"] = por_que_falta_o_elo(
            l["id"], l["jusante"], fonte_transito, tabela, tipo)
        if tipo == "confluencia":
            # A explicação topológica é mais concreta que a genérica: diz QUAL
            # afluente e em que rio ele corre.
            l["transito_porque"] = ("confluencia", [porque_tipo, *l["transito_porque"][1]])

    manchas = le("manchas/index.json")["manchas"]
    mare = le("mare-itajai.json")
    dias_de_mare = sorted({p["quando"][:10] for p in mare["preamares"]})

    return {
        "linhas": linhas,
        "eventos": len(eventos),
        # CORRIGIDO EM 08/09/2026: contava ":" na DATA, que é ISO e nunca tem
        # dois-pontos — o resultado era 0 por construção, e eu repeti "196 picos,
        # zero com hora" o dia inteiro em cima disso. A hora mora no campo `hora`
        # (HH:MM, validado), e é ele que calibrar_transito.py lê. Eram 2.
        "eventos_com_hora": sum(1 for e in eventos if e.get("hora")),
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
        "ao_vivo_de": ao_vivo_de,
        "ao_vivo_leituras": sum(vivo.values()),
    }


def rotulo_de_cota(l: dict) -> str:
    """
    Três estados, não dois. `sim` = a cidade tem a escala; `11×` = a escala mora
    nas réguas (Itajaí); `—` = não existe em lugar nenhum e vale procurar.

    Achatar os dois primeiros num `—` foi o que criou o buraco falso de Itajaí.
    """
    if l["cotas_essenciais"]:
        return "sim"
    if l["reguas"]["com_escala"]:
        return f"{l['reguas']['com_escala']}×"
    return "—"


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
            f"{rotulo_de_cota(l):>5s} "
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
        # A cidade cuja escala mora nas réguas NÃO entra aqui: a tela pinta a
        # cor a partir da régua, então a cor existe. Contá-la como falta era o
        # buraco falso de Itajaí.
        if not l["cotas_essenciais"] and not l["reguas"]["com_escala"]:
            faltas["sem cotas de atenção/alerta"] += 1
        if l["cotas_essenciais"] and not l["cotas_verificado"]:
            faltas["cotas não conferidas na fonte"] += 1
        if l["escala_por_regua"] and l["reguas"]["conferidas"] < l["reguas"]["com_escala"]:
            faltas["régua com escala não conferida na fonte"] += 1
        if l["picos"] < PARES_MINIMOS:
            faltas[f"menos de {PARES_MINIMOS} picos"] += 1
        if not l["ana_verificado"]:
            faltas["sem série da ANA conferida"] += 1
        if not l["ruas"]:
            faltas["sem cotas de rua"] += 1
        if l["transito"] is False:
            # Separado desde 07/09/2026: o resumo dizia "10 sem trecho" e lia
            # como dez coisas a procurar. Um deles não é — Indaial -> Blumenau
            # tem as duas pontas na JICA e a diferença é zero ou negativa.
            if l["transito_porque"][0] in ("nao_positivo", "confluencia"):
                faltas["trânsito que NÃO é tempo de trânsito (não procurar)"] += 1
            else:
                faltas["sem trecho de trânsito a jusante (falta fonte)"] += 1
    print("buracos, por quantas cidades atingem:")
    for k, v in faltas.most_common():
        print(f"  {v:3d}  {k}")


#: Frase que só existe no Markdown gerado SEM `--ao-vivo`. Serve de marca: um
#: arquivo que não a contém foi gerado com a coluna de leitura MEDIDA.
MARCA_SEM_MEDICAO = "**Não medido nesta execução**"


def apagaria_medicao(destino: Path, mediu_agora: bool) -> bool:
    """
    Este `--markdown` trocaria uma coluna MEDIDA por `?` em toda a matriz?

    POR QUE EXISTE (08/09/2026). Aconteceu: o auditor foi reexecutado sem
    `--ao-vivo` e o documento commitado perdeu, em silêncio, a lista das doze
    cidades sem leitura — virou `?` nas dezenove linhas. O `?` está certo (uma
    sessão anterior o criou justamente para "não medido" não virar "ausente"),
    mas GRAVAR `?` por cima de medição é perder dado sem avisar.

    O sentido é de mão única: gerar com medição por cima de um "não medido"
    é ganho, nunca perda.
    """
    if mediu_agora or not destino.exists():
        return False
    return MARCA_SEM_MEDICAO not in destino.read_text(encoding="utf-8")


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
    # A coluna de leitura envelhece muito mais rápido que as outras seis: ela
    # vale a hora da coleta, não o dia da geração. Sem o carimbo, uma matriz de
    # semana passada parece tão atual quanto o resto do documento.
    if rel["ao_vivo_lido"]:
        f.append(
            f"Coluna **Leitura ao vivo** medida em `{rel['ao_vivo_de'] or 'sem carimbo'}` "
            f"({rel['ao_vivo_leituras']} réguas com nível). As outras seis colunas "
            "não dependem de coleta.\n\n"
        )
    f.append(
        "Sete camadas por cidade. Cada uma acende uma parte diferente do site, e é\n"
        "isso que ordena a busca: sem leitura o pino fica cinza; sem cota a cor não\n"
        "existe nem com leitura; sem pico a previsão a jusante diz \"dados\n"
        "insuficientes\"; sem hora de pico o tempo de trânsito continua sendo tabela\n"
        "de projeto, nunca medida.\n\n"
    )

    if not rel["ao_vivo_lido"]:
        f.append(
            "> ⚠️ **A coluna \"Leitura ao vivo\" não foi medida nesta execução** e sai como `?`.\n"
            "> O auditor só a preenche quando recebe `--ao-vivo <ultimo.json>` do branch\n"
            "> `tempo-real`. Rodar sem isso e ler `—` faria a matriz afirmar que NENHUMA cidade\n"
            "> publica nível — falso, e mandaria procurar fonte para cidade que já tem.\n"
            ">\n"
            "> ```\n"
            "> curl -sSL -o /tmp/ultimo.json \\\n"
            ">   https://raw.githubusercontent.com/haohmarusc-glitch/enchentes-vale-itajai/tempo-real/ultimo.json\n"
            "> python3 scripts/auditar_lacunas.py --ao-vivo /tmp/ultimo.json --markdown docs/LACUNAS-DE-DADOS.md\n"
            "> ```\n\n"
        )

    f.append("## Matriz por cidade\n\n")
    f.append(
        "| Cidade | Rio | Leitura ao vivo | Cotas atenção+alerta | Cotas conferidas | "
        "Picos | Série ANA | Cotas de rua | Trânsito a jusante |\n"
        "|---|---|---|---|---|---|---|---|---|\n"
    )
    for l in linhas:
        tr = "n/a" if l["transito"] is None else sim(l["transito"])
        # `?` quando a coluna NÃO FOI MEDIDA. Sem isso ela sai `—`, igualzinho a
        # "medido e ausente", e a matriz passa a afirmar que nenhuma cidade tem
        # leitura ao vivo — o que é falso e manda procurar fonte para cidade que
        # já publica. Ausência nunca prova ausência; falta de medição, menos ainda.
        vivo = sim(l["vivo"]) if rel["ao_vivo_lido"] else "?"
        f.append(
            f"| {l['nome']} | {l['rio'].replace('itajai-', '')} | {vivo} | "
            f"{rotulo_de_cota(l)} | {sim(l['cotas_verificado'])} | "
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

    def por_id(cond):
        """As LINHAS que casam, uma por cidade — a foz aparece nos dois rios."""
        vistos, saida = set(), []
        for l in linhas:
            if cond(l) and l["id"] not in vistos:
                vistos.add(l["id"])
                saida.append(l)
        return saida

    nome_de = {l["id"]: l["nome"] for l in linhas}

    f.append("\n## Lista de busca, por impacto\n")

    f.append("\n### 1. Leitura ao vivo — o pino cinza\n\n")
    if not rel["ao_vivo_lido"]:
        f.append(
            f"{MARCA_SEM_MEDICAO} — ver o aviso no topo. A lista abaixo só existe "
            "quando o auditor roda com `--ao-vivo`.\n"
        )
    f.append(
        f"Sem leitura em: {nomes(lambda l: not l['vivo']) if rel['ao_vivo_lido'] else '(não medido)'}.\n\n"
        "É o que mais escurece o mapa e o único item que não tem substituto "
        "histórico: nenhuma pesquisa em acervo acende um pino hoje. O pedido é "
        "ofício à Defesa Civil do município pedindo o endpoint que a página de "
        "monitoramento já consome.\n"
    )

    f.append("\n### 2. Cotas oficiais — a cor que não existe nem com leitura\n\n")
    f.append(
        f"Sem cota nenhuma: {nomes(lambda l: l['cotas_nenhuma'])}.\n\n"
        f"Com cota incompleta (falta atenção ou alerta): "
        f"{nomes(lambda l: not l['cotas_nenhuma'] and not l['cotas_essenciais'] and not l['escala_por_regua'])} — "
        "a tela não consegue pintar a faixa que falta.\n\n"
        "**Com a escala nas RÉGUAS, não na cidade** — não é buraco, não procurar: "
        # Desduplicado por id: a foz aparece nos dois rios, e sem isto a frase
        # sai repetida ("Itajaí 11 de 12 réguas, Itajaí 11 de 12 réguas").
        + (", ".join(
            f"**{l['nome']}** ({l['reguas']['com_escala']} de {l['reguas']['total']} "
            f"réguas com escala, {l['reguas']['conferidas']} conferidas na fonte)"
            for l in por_id(lambda l: l["escala_por_regua"])) or "nenhuma")
        + ". A cidade não tem uma escala porque tem VÁRIAS, uma por régua, e um "
        "número só ali seria mentira. A cor da tela sai da régua, então a cor "
        "existe.\n\n"
        f"Com as duas mas sem conferência na fonte: "
        f"{nomes(lambda l: l['cotas_essenciais'] and not l['cotas_verificado'])} — "
        "valor veio de resumo, levantamento ou imprensa, não de leitura do Plano "
        "de Contingência. Procurar o PDF do PLANCON de cada uma e guardar em "
        "`data/brutos/`.\n"
    )

    f.append("\n### 3. Hora do pico — o que destrava `transito.json`\n\n")
    f.append(
        f"**{rel['eventos']} picos na base, {rel['eventos_com_hora']} com hora.** "
        "Enquanto forem tão poucos (o calibrador exige 3 por par de cidades), todo "
        "tempo de trânsito exibido é faixa de tabela de "
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
        # ⚠️ CORRIGIDO EM 08/09/2026, contra a API de verdade. Esta frase dizia
        # "série inteira de cota, COM HORA — resolve os itens 3 e 4 juntos". A
        # metade da hora era falsa, e mandava a auditoria para o alvo errado: a
        # HidroSerieCotas devolve DIA, não hora (uma linha por mês, Cota_01..31).
        # O item 3 (196 picos, só 2 com hora) NÃO sai daqui. Ver
        # docs/ANA-API-2026-09-08.md.
        "Cada estação conferida traz série inteira de cota **por dia** — resolve o "
        "item 4 para aquela cidade, e é o item de maior alcance por unidade de "
        "esforço da lista. **Não resolve o item 3:** a série da ANA é diária, sem "
        "hora do pico (conferido na API em 08/09/2026 — ver "
        "`docs/ANA-API-2026-09-08.md`).\n\n"
        # Divisão feita em 08/09/2026, pelo mesmo motivo do item 7: a lista
        # dizia doze e lia como doze buscas iguais. Cinco não são busca.
        "**Mas não são doze buscas iguais.** Só as do primeiro grupo são busca:\n\n"
    )
    sem_busca = por_id(lambda l: not l["ana_verificado"] and l["ana_busca"] == "sem_busca")
    recusadas = por_id(lambda l: not l["ana_verificado"] and l["ana_busca"] == "recusada")
    decisao = por_id(lambda l: not l["ana_verificado"] and l["ana_busca"] == "decisao")

    f.append(
        f"**Busca de verdade — ninguém olhou ainda** ({len(sem_busca)}): "
        + (", ".join(f"**{l['nome']}**" for l in sem_busca) or "nenhuma")
        + ".\n\n"
    )
    if recusadas:
        f.append(
            f"⚠️ **A busca JÁ FOI FEITA e a estação achada foi RECUSADA** ({len(recusadas)}) — "
            "o que falta é uma estação **diferente**, e a recusada está nomeada aqui "
            "de propósito, para não voltar:\n\n"
            "| Cidade | Estação recusada | Por quê, em uma linha |\n|---|---|---|\n"
        )
        for l in recusadas:
            porque = primeira_frase(l["ana_porque_fora"])
            f.append(f"| {l['nome']} | `{l['ana_estacao_fora']}` | {porque} |\n")
        f.append(
            "\nO motivo inteiro, com a distância medida e o bruto do inventário, está em "
            "`codigo_ana_nao_e` de cada cidade em `data/estacoes.json`. **Trazer de volta "
            "uma destas é como um pareamento errado entra** — já custou caro em Brusque e "
            "no Salseiro de Vidal Ramos.\n\n"
        )
    if decisao:
        f.append(
            f"⛔ **Não é busca, é DECISÃO** ({len(decisao)}): "
            + ", ".join(f"**{l['nome']}** (candidata `{l['ana_estacao_fora']}`)" for l in decisao)
            + ". A candidata já existe e a distância já foi medida; o que falta é "
            "critério. Pedir busca aqui aponta para a tarefa errada — o desbloqueio "
            "está escrito em `codigo_ana_candidatos`.\n"
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

    f.append("\n### 7. Trânsito — os elos que faltam, e quais valem procurar\n\n")
    faltando = [l for l in linhas if l["transito"] is False]
    if not faltando:
        f.append("Todos os elos da topologia têm trecho.\n")
    else:
        procurar = [l for l in faltando if l["transito_porque"][0] == "sem_tempo_de_fonte"]
        nao = [l for l in faltando
               if l["transito_porque"][0] in ("nao_positivo", "confluencia")]
        f.append(
            f"São {len(faltando)}, e **não são {len(faltando)} coisas a procurar**. "
            f"{len(procurar)} faltam por falta de fonte; "
            f"{len(nao)} não {'é' if len(nao) == 1 else 'são'} tempo de trânsito nenhum.\n"
        )
        if procurar:
            f.append("\n**Vale procurar — falta fonte:**\n\n| De | Para | Rio | Por quê |\n|---|---|---|---|\n")
            for l in procurar:
                porques = "; ".join(l["transito_porque"][1])
                f.append(
                    f"| {l['nome']} | {nome_de.get(l['jusante'], l['jusante'])} | "
                    f"{l['rio'].replace('itajai-', '')} | {porques} |\n"
                )
        if nao:
            f.append("\n**⛔ Não procurar — o elo não é um tempo de trânsito:**\n\n")
            f.append(
                "Nestes, a grandeza não existe: nem outra fonte nem uma cheia medida resolvem. "
                "Um número aqui teria cara de tempo de trânsito sem ser um.\n"
            )
            for l in nao:
                f.append(f"\n`{l['nome']} → {nome_de.get(l['jusante'], l['jusante'])}`\n\n")
                for porque in l["transito_porque"][1]:
                    f.append(f"- {porque}\n")

    f.append("\n### 8. Maré de Itajaí\n\n")
    f.append(
        f"Tábua cobre **{rel['mare_dias']} dias, até {rel['mare_ate']}**; "
        f"altura em metros: {'sim' if rel['mare_com_altura'] else '**não** (só horário)'}.\n\n"
        "Depois dessa data a tela da foz fica sem maré.\n\n"
        # Corrigido em 08/09/2026: este item dizia "procurar a tábua anual do
        # CHM/Marinha". Ela já foi achada — a rodada 2 da busca externa conferiu
        # que o PDF do CHM para o Porto de Itajaí cobre outubro, novembro e
        # dezembro de 2026. Mandar procurar o que já se tem é buraco falso, e
        # buraco falso ensina a desconfiar da lista inteira.
        "**Não é busca, é importação.** A tábua do CHM para o Porto de Itajaí "
        "**já foi encontrada** e cobre outubro, novembro e dezembro de 2026 — os "
        "92 dias que faltam existem e estão disponíveis. A parede real da FONTE "
        "é 31/12/2026, não a data acima, que é da tabela IMPORTADA. **2027 ainda "
        "não existe no portal**: aí sim é espera, não busca.\n\n"
        "A altura em metros foi omitida de propósito: o datum da planilha não "
        "está conferido contra o da DHN — mesmo problema do datum de Blumenau. "
        "Importar o horário sem a altura continua certo enquanto isso.\n"
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
    p.add_argument(
        "--aceitar-perder-a-medicao", action="store_true",
        help="grava por cima de uma matriz medida, trocando a coluna de leitura por `?`",
    )
    args = p.parse_args(argv)

    rel = auditar(args.ao_vivo)
    imprime(rel)
    if args.markdown:
        if apagaria_medicao(args.markdown, rel["ao_vivo_lido"]) and not args.aceitar_perder_a_medicao:
            print(
                f"\nRECUSADO: {args.markdown} tem a coluna de leitura MEDIDA, e esta "
                "execução não mediu.\nGravar agora trocaria a lista de cidades sem "
                "leitura por `?` nas dezenove linhas — perda silenciosa.\n\n"
                "  git fetch origin tempo-real && git show origin/tempo-real:ultimo.json > /tmp/ultimo.json\n"
                "  python3 scripts/auditar_lacunas.py --ao-vivo /tmp/ultimo.json "
                f"--markdown {args.markdown}\n\n"
                "Para gravar mesmo assim, e assumindo a perda: --aceitar-perder-a-medicao",
                file=sys.stderr,
            )
            return 3
        args.markdown.write_text(markdown(rel), encoding="utf-8")
        print(f"\nmatriz gravada em {args.markdown}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
