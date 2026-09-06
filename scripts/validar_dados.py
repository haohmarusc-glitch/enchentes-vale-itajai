#!/usr/bin/env python3
"""Valida os JSONs de `data/`. Sai com código 1 se algo estiver errado.

Este é o portão de qualidade do projeto: o site mostra o que estiver nestes
arquivos, e um número errado aqui vira número errado na tela de alguém que
está decidindo se sai de casa. Rode antes de todo commit que mexa em `data/`.

    python3 scripts/validar_dados.py
"""

from __future__ import annotations

import json
import math
import re
import sys
from collections import defaultdict
from datetime import date
from pathlib import Path

from comum import le_json

RAIZ = Path(__file__).resolve().parent.parent

CONFIANCAS = {"alta", "media", "baixa"}
RE_DATA = re.compile(r"^\d{4}(-\d{2}(-\d{2})?)?$")
RE_HORA = re.compile(r"^\d{2}:\d{2}$")

#: Nenhuma régua da bacia chega perto disso. Valor acima é erro de digitação.
PICO_MAXIMO_M = 25.0
#: A cheia de 1852 é o registro mais antigo citado na bibliografia local.
ANO_MINIMO = 1850

#: Braços válidos de um rio ramificado. Só se compara posição DENTRO do ramo.
RAMOS_VALIDOS = {
    "itajai_do_oeste", "itajai_do_sul", "itajai_do_norte", "tronco_acu",
    "benedito", "luiz_alves", "mirim_tronco", "canal_retificado",
    "curso_antigo", "reunido", "ribeirao_murta", "ribeirao_canhanduba", "acu",
    # Entraram em 04/09/2026 com as cidades de afluente. Cada nome é o RIO em
    # que a cidade fica — é o que a fonte municipal afirma. Onde esse rio
    # encontra o eixo é outra pergunta, e mora em `afluentes_laterais`: quando
    # não se sabe, a cidade fica fora daquela lista e a tela a mostra em
    # "Outros pontos", que é o honesto.
    "rio_dos_cedros", "trombudo",
}
RE_DCSC = re.compile(r"^DCSC-\d{5}$")

#: Estação estadual que DEVE continuar ligada a cada cidade (ligação por
#: coordenada, verificada no mapa/Overpass 02/09/2026). Trava contra um
#: codigo_dcsc sumir ou trocar em silêncio numa edição futura — foi documentar
#: sem travar que deixou o JSON errado por versões seguidas.
CODIGO_DCSC_ESPERADO = {
    ("itajai-acu", "taio"): "DCSC-00041",
    ("itajai-acu", "ituporanga"): "DCSC-00039",
    ("itajai-acu", "rio-do-sul"): "DCSC-00013",
    ("itajai-acu", "ibirama"): "DCSC-00020",
    ("itajai-acu", "ascurra"): "DCSC-00003",
    ("itajai-acu", "indaial"): "DCSC-00006",
    ("itajai-acu", "blumenau"): "DCSC-00026",
    ("itajai-acu", "gaspar"): "DCSC-00005",
    ("itajai-acu", "ilhota"): "DCSC-00030",
}

erros: list[str] = []
avisos: list[str] = []


def erro(msg: str) -> None:
    erros.append(msg)


def aviso(msg: str) -> None:
    avisos.append(msg)


def valida_data(valor: str, onde: str) -> None:
    if not isinstance(valor, str) or not RE_DATA.match(valor):
        erro(f"{onde}: data '{valor}' fora do formato ISO (AAAA, AAAA-MM ou AAAA-MM-DD)")
        return
    ano = int(valor[:4])
    if ano < ANO_MINIMO or ano > date.today().year:
        erro(f"{onde}: ano {ano} fora da faixa plausível ({ANO_MINIMO}–{date.today().year})")
    if len(valor) >= 7:
        mes = int(valor[5:7])
        if not 1 <= mes <= 12:
            erro(f"{onde}: mês inválido em '{valor}'")
    if len(valor) == 10:
        try:
            date.fromisoformat(valor)
        except ValueError:
            erro(f"{onde}: '{valor}' não é uma data que existe no calendário")


def valida_topologia(rio_id: str, rio: dict, ids: set[str]) -> None:
    """A árvore de um rio ramificado: o tronco tem de ser a única fila afirmada,
    e cada id citado tem de existir (ou, para nao_e_regua_de_rio, NÃO existir)."""
    topo = rio["_topologia"]
    onde = f"estacoes.json / {rio_id} / _topologia"
    tronco = topo.get("tronco_sequencia", [])
    if not tronco:
        erro(f"{onde}: tronco_sequencia vazio")
    for cid in tronco:
        if cid not in ids:
            erro(f"{onde}: tronco_sequencia cita '{cid}', que não está em cidades")
    # O tronco_sequencia tem de ser EXATAMENTE as cidades de ramo tronco_acu, na
    # ordem de ordem_no_ramo — senão a fila da tela discordaria dos dados.
    tronco_cidades = [c for c in rio["cidades"] if c.get("ramo") == "tronco_acu"]
    ordenadas = [c["id"] for c in sorted(tronco_cidades, key=lambda c: c.get("ordem_no_ramo") or 0)]
    if ordenadas != tronco:
        erro(f"{onde}: tronco_sequencia {tronco} não bate com as cidades de ramo tronco_acu "
             f"por ordem_no_ramo {ordenadas}")
    for cid in topo.get("cabeceiras_paralelas", []):
        if cid not in ids:
            erro(f"{onde}: cabeceira '{cid}' não está em cidades")
    for a in topo.get("afluentes_laterais", []):
        if a.get("id") not in ids:
            erro(f"{onde}: afluente '{a.get('id')}' não está em cidades")
        if a.get("entra_perto_de") not in ids:
            erro(f"{onde}: afluente '{a.get('id')}' entra_perto_de "
                 f"'{a.get('entra_perto_de')}' que não existe")
    for x in topo.get("nao_e_regua_de_rio", []):
        if x.get("id") in ids:
            erro(f"{onde}: '{x.get('id')}' está em nao_e_regua_de_rio mas ainda aparece em cidades")


def valida_estacoes() -> set[tuple[str, str]]:
    estacoes = le_json("estacoes.json")
    conhecidas: set[tuple[str, str]] = set()
    no_eixo: set[tuple[str, str]] = set()

    for rio_id, rio in estacoes["rios"].items():
        # Árvore x fila. Rio ramificado (tem _topologia) NÃO usa ordem global:
        # ela afirmaria uma sequência que não existe (Taió antes de Ibirama). A
        # posição vem de ramo + ordem_no_ramo, e a única fila é o tronco. Rio em
        # fila (o Mirim) segue com ordem 1..N. As duas coisas nunca no mesmo rio.
        ramificado = "_topologia" in rio
        ordens: list = []
        por_ramo: dict[str, list[int]] = defaultdict(list)
        ids: set[str] = set()
        for cidade in rio["cidades"]:
            onde = f"estacoes.json / {rio_id} / {cidade.get('id', '???')}"
            for campo in ("id", "nome", "ordem", "codigo_ana", "verificado", "cotas_m"):
                if campo not in cidade:
                    erro(f"{onde}: falta o campo '{campo}'")
            if cidade["id"] in ids:
                erro(f"{onde}: id repetido dentro do mesmo rio")
            ids.add(cidade["id"])
            ordens.append(cidade.get("ordem"))
            conhecidas.add((rio_id, cidade["id"]))
            no_eixo.add((rio_id, cidade["id"]))

            ramo = cidade.get("ramo")
            if ramificado:
                if cidade.get("ordem") is not None:
                    erro(f"{onde}: 'ordem' global em rio ramificado deve ser null "
                         f"(a bacia é árvore, não fila; use ordem_no_ramo). Veio {cidade.get('ordem')!r}")
                if ramo not in RAMOS_VALIDOS:
                    erro(f"{onde}: 'ramo' ausente ou inválido ({ramo!r}) em rio ramificado")
                onr = cidade.get("ordem_no_ramo")
                if not isinstance(onr, int):
                    erro(f"{onde}: 'ordem_no_ramo' ausente ou não inteiro ({onr!r})")
                elif ramo in RAMOS_VALIDOS:
                    por_ramo[ramo].append(onr)
            elif ramo is not None:
                erro(f"{onde}: tem 'ramo' mas o rio não é ramificado (sem _topologia) "
                     f"— árvore e fila não se misturam")

            dcsc = cidade.get("codigo_dcsc")
            if dcsc is not None and not RE_DCSC.match(str(dcsc)):
                erro(f"{onde}: codigo_dcsc '{dcsc}' fora do formato DCSC-NNNNN")
            esperado_dcsc = CODIGO_DCSC_ESPERADO.get((rio_id, cidade["id"]))
            if esperado_dcsc and dcsc != esperado_dcsc:
                erro(f"{onde}: codigo_dcsc deveria ser {esperado_dcsc} (ligação verificada por "
                     f"coordenada) e veio {dcsc!r} — não deixar sumir/trocar sem reverificar no mapa")

            codigo = cidade.get("codigo_ana")
            if codigo is not None and not re.fullmatch(r"\d{8}", str(codigo)):
                erro(f"{onde}: codigo_ana '{codigo}' não tem os 8 dígitos do HidroWeb")
            if codigo is not None and not cidade.get("verificado"):
                aviso(f"{onde}: codigo_ana {codigo} ainda não conferido na fonte oficial")

            for chave, valor in (cidade.get("cotas_m") or {}).items():
                if not isinstance(valor, (int, float)) or not 0 < valor < PICO_MAXIMO_M:
                    erro(f"{onde}: cota '{chave}' = {valor} fora de faixa plausível")

        if ramificado:
            for ramo_id, lista in por_ramo.items():
                esperado = list(range(1, len(lista) + 1))
                if sorted(lista) != esperado:
                    erro(f"estacoes.json / {rio_id} / ramo {ramo_id}: 'ordem_no_ramo' deveria "
                         f"ser {esperado}, veio {sorted(lista)}")
            valida_topologia(rio_id, rio, ids)
        else:
            esperado = list(range(1, len(ordens) + 1))
            if sorted(ordens) != esperado:
                erro(f"estacoes.json / {rio_id}: 'ordem' deveria ser {esperado}, veio {sorted(ordens)}")

    # Trava contra sumiço: toda cidade ligada a uma estação estadual conhecida
    # tem de continuar no eixo, com o mesmo codigo_dcsc. Documentar não impediu
    # o JSON de ficar errado por versões; travar impede.
    for (rio_id, cid), cod in CODIGO_DCSC_ESPERADO.items():
        cidades_do_rio = estacoes["rios"].get(rio_id, {}).get("cidades", [])
        achou = next((c for c in cidades_do_rio if c.get("id") == cid), None)
        if achou is None:
            erro(f"estacoes.json / {rio_id}: cidade '{cid}' (codigo_dcsc {cod}) sumiu do eixo — "
                 "se foi de propósito, tire de CODIGO_DCSC_ESPERADO com uma justificativa")

    # Afluentes com régua própria: existem nos dados, mas ficam fora da sequência do eixo.
    for afluente in estacoes.get("afluentes_monitorados", []):
        onde = f"estacoes.json / afluentes_monitorados / {afluente.get('id', '???')}"
        for campo in ("id", "nome", "rio", "desagua_em", "observacao"):
            if campo not in afluente:
                erro(f"{onde}: falta o campo '{campo}'")
        for rio_id in estacoes["rios"]:
            conhecidas.add((rio_id, afluente["id"]))
        if any(afluente["id"] == c for r in estacoes["rios"].values() for c in
               (x["id"] for x in r["cidades"])):
            erro(f"{onde}: está ao mesmo tempo no eixo e fora dele — escolha um lugar só")

    # Estações de tempo real: o título é a chave de ligação com a fonte, e a
    # cota fica aqui porque cada régua tem seu zero.
    registro = estacoes.get("estacoes_tempo_real", [])
    # Quantas réguas cada cidade tem. Com uma só, a cota da cidade serve; com
    # várias, cada régua precisa da sua, porque os zeros são diferentes.
    #
    # Pluviômetro NÃO é régua e fica fora desta conta. A distinção não é
    # cosmética: a estação Guarani mede chuva em Brusque e está cadastrada no
    # mesmo (rio, cidade) da régua de Brusque. Contada como régua, a cidade
    # passaria a "ter duas", e a regra de recusar cota de cidade onde há mais
    # de uma régua calaria o aviso de cota no Itajaí-Mirim inteiro.
    reguas: dict[tuple[str, str], int] = {}
    for e in registro:
        if e.get("tipo") == "pluviometro":
            continue
        chave = (e.get("rio"), e.get("cidade"))
        reguas[chave] = reguas.get(chave, 0) + 1

    titulos: set[str] = set()
    for i, e in enumerate(registro):
        onde = f"estacoes.json / estacoes_tempo_real[{i}] ({e.get('titulo', '???')})"
        for campo in ("titulo", "rio", "cidade", "cotas_m", "verificado"):
            if campo not in e:
                erro(f"{onde}: falta o campo '{campo}'")
                continue
        if not str(e.get("titulo", "")).strip():
            erro(f"{onde}: título vazio — é por ele que o coletor liga a leitura à cidade")
        if e.get("titulo") in titulos:
            erro(f"{onde}: título repetido; a ligação com a fonte ficaria ambígua")
        titulos.add(e.get("titulo"))
        for chave, valor in (e.get("cotas_m") or {}).items():
            if not isinstance(valor, (int, float)) or not 0 < valor < PICO_MAXIMO_M:
                erro(f"{onde}: cota '{chave}' = {valor} fora de faixa plausível")
        # Régua que não dispara aviso (as do estuário, que sobem com a maré)
        # PRECISA dizer por quê. Sem o motivo, a cota apareceria na tela como
        # qualquer outra e alguém a leria como perigo — é a régua marcada como
        # "não pinta faixa sozinha" que não pode virar faixa em silêncio.
        if e.get("alerta_automatico") is False and not str(e.get("motivo_sem_alerta", "")).strip():
            erro(f"{onde}: alerta_automatico=false sem 'motivo_sem_alerta' — a régua que "
                 "não dispara aviso tem de dizer por que, ou vira faixa de perigo enganosa")
        if (
            e.get("tipo") != "pluviometro"
            and not (e.get("cotas_m") or {})
            and reguas.get((e.get("rio"), e.get("cidade")), 0) > 1
        ):
            aviso(
                f"{onde}: sem cota própria, e {e.get('cidade')} tem "
                f"{reguas[(e.get('rio'), e.get('cidade'))]} réguas neste rio — "
                "extrair_picos.py não analisa esta estação"
            )

    globals()["_no_eixo"] = no_eixo
    return conhecidas


#: Conjunto fechado. Ver REGRA_REFERENCIA_BLUMENAU em enchentes.json.
REFERENCIAS_VALIDAS = ("régua", "IBGE (régua + 0,20 m)")


def valida_referencias() -> None:
    """
    Todo registro de Blumenau tem de DECLARAR sua referência.

    Duas circulam para a cidade: a régua local e a do IBGE, 20 cm acima. A série
    longa (Cordero & Medeiros) é IBGE; as cotas de atenção, alerta e inundação
    de estacoes.json são régua. Um registro que não diz qual usa faz o leitor
    supor régua — e supor errado superestima o pico em 20 cm justamente na
    cidade com a série mais longa do projeto.

    `null` é resposta válida e significa "a fonte não declara". O que não vale é
    o campo ausente, que é silêncio disfarçado de certeza.
    """
    dados = le_json("enchentes.json")
    eventos = dados["eventos"]
    regra_viva = "REGRA_REFERENCIA_BLUMENAU" in dados.get("_meta", {})

    for e in eventos:
        if regra_viva and e.get("cidade") == "blumenau" and "referencia" not in e:
            erro(
                f"enchentes.json: Blumenau {e.get('data')} não declara 'referencia'. "
                f"Use {REFERENCIAS_VALIDAS[1]!r}, {REFERENCIAS_VALIDAS[0]!r}, ou null "
                "quando a fonte não diz."
            )
        if "referencia" not in e:
            continue
        ref = e["referencia"]
        if ref is None:
            continue
        if ref not in REFERENCIAS_VALIDAS:
            # Conjunto fechado de propósito. Uma string livre como
            # "desconhecida — provavelmente IBGE" mistura o que se sabe com o
            # que se suspeita, e daqui a seis meses alguém varre o arquivo para
            # converter e lê "provavelmente" como "sim". Hipótese vai em
            # 'referencia_hipotese' ou 'nota'.
            erro(
                f"enchentes.json: {e.get('cidade')} {e.get('data')} tem referencia "
                f"{ref!r}, fora do conjunto fechado {REFERENCIAS_VALIDAS}. "
                "Hipótese vai em 'referencia_hipotese' ou 'nota'."
            )

    # Item 2 da regra: conflito é divergência, não registro duplicado.
    vistos: dict[tuple, int] = {}
    for e in eventos:
        chave = (e.get("rio"), e.get("cidade"), e.get("data"))
        vistos[chave] = vistos.get(chave, 0) + 1
    for chave, n in sorted(vistos.items()):
        if n > 1:
            erro(
                f"enchentes.json: {chave[1]} {chave[2]} aparece {n} vezes. "
                "Conflito de valor usa 'divergencias' — um adotado, os demais "
                "guardados com fonte —, não registros duplicados."
            )


def valida_cotas_ruas() -> None:
    """
    Cotas de rua: o nível em que cada rua começa a alagar.

    Além da conferência de forma, esta função faz a pergunta que importa:
    **o aviso de cota chega antes ou depois da primeira rua alagar?** Se a cota
    mais baixa cadastrada para a cidade for MAIOR que a cota da primeira rua, o
    telefone toca depois que a água já entrou — e um aviso atrasado é pior que
    inútil, porque dá a impressão de que havia tempo.
    """
    try:
        dados = le_json("cotas-ruas.json")
    except FileNotFoundError:
        return
    registros = dados.get("cotas", [])
    if not registros:
        aviso("cotas-ruas.json: nenhuma cota de rua cadastrada")
        return

    estacoes = le_json("estacoes.json")
    das_cidades: dict[str, dict] = {}
    rio_da_cidade: dict[str, set[str]] = {}
    for rio_id, rio in estacoes["rios"].items():
        for c in rio["cidades"]:
            das_cidades.setdefault(c["id"], {}).update(c.get("cotas_m") or {})
            rio_da_cidade.setdefault(c["id"], set()).add(rio_id)

    # Réguas que TÊM cota e podem disparar aviso. Ilhota e Itajaí só têm cota
    # aqui, e não em `cotas_m` da cidade: sem isto o validador diria que elas
    # não têm cota nenhuma. As de estuário ficam de fora porque não disparam
    # aviso — é essa a pergunta desta checagem.
    reguas_com_aviso: dict[str, list[str]] = {}
    for e in estacoes.get("estacoes_tempo_real") or []:
        if e.get("tipo") == "pluviometro" or e.get("alerta_automatico") is False:
            continue
        if not any(isinstance(v, (int, float)) for v in (e.get("cotas_m") or {}).values()):
            continue
        cidade_id = e.get("cidade")
        if cidade_id:
            reguas_com_aviso.setdefault(cidade_id, []).append(
                e.get("codigo") or e.get("titulo") or "?"
            )

    primeira_rua: dict[str, float] = {}
    sem_aviso: dict[str, list[str]] = {}
    for i, r in enumerate(registros):
        onde = f"cotas-ruas.json / cotas[{i}] ({r.get('rua', '???')})"
        for campo in ("cidade", "rio", "rua", "cota_m", "fonte", "confianca"):
            if campo not in r:
                erro(f"{onde}: falta o campo '{campo}'")
        cidade = r.get("cidade")
        if cidade not in rio_da_cidade:
            erro(f"{onde}: cidade '{cidade}' não existe em estacoes.json")
            continue
        if r.get("rio") not in rio_da_cidade[cidade]:
            erro(f"{onde}: rio '{r.get('rio')}' não passa por {cidade}")
        if r.get("confianca") not in ("alta", "media", "baixa"):
            erro(f"{onde}: confiança '{r.get('confianca')}' inválida")

        cota = r.get("cota_m")
        if cota is None:
            # Sem número é legítimo: a fonte cita a rua e não publica a cota.
            # Mas então precisa dizer isso, senão vira buraco silencioso.
            if not r.get("nota"):
                aviso(f"{onde}: sem cota e sem nota explicando por quê")
            continue
        if not isinstance(cota, (int, float)) or not 0 < cota < PICO_MAXIMO_M:
            erro(f"{onde}: cota_m = {cota} fora de faixa plausível")
            continue

        # `cota_max_m` é o nível em que a rua alaga INTEIRA, quando a fonte
        # publica os dois números (Rio do Sul publica). Abaixo da mínima seria
        # leitura trocada, e trocado é pior que ausente: diria que a rua está
        # toda embaixo d'água antes de a água chegar nela.
        maxima = r.get("cota_max_m")
        if maxima is not None:
            if not isinstance(maxima, (int, float)) or not 0 < maxima < PICO_MAXIMO_M:
                erro(f"{onde}: cota_max_m = {maxima} fora de faixa plausível")
            elif maxima < cota:
                erro(f"{onde}: cota_max_m {maxima} é MENOR que cota_m {cota} — "
                     "a rua alagaria inteira antes de a água chegar")
        # Registro marcado para não mover aviso fica fora desta conta. É o caso
        # das cotas que a fonte publica abaixo do nível normal do rio: exigir
        # que a cidade baixe a cota de atenção por causa de um número que
        # ninguém conferiu faria o aviso tocar em dia de sol.
        if r.get("usar_para_aviso") is False:
            sem_aviso.setdefault(cidade, []).append(f"{r.get('rua', '?')} ({cota:.2f} m)")
            continue
        anterior = primeira_rua.get(cidade)
        primeira_rua[cidade] = cota if anterior is None else min(anterior, cota)

    for cidade, ruas in sorted(sem_aviso.items()):
        aviso(f"cotas-ruas.json: {cidade} tem {len(ruas)} cota(s) marcada(s) para não "
              f"mover aviso, por ficarem abaixo do nível normal do rio: "
              f"{', '.join(ruas[:5])}. Aparecem na tela com a ressalva; conferir com a "
              "Defesa Civil para virarem aviso.")

    for cidade, rua_mais_baixa in sorted(primeira_rua.items()):
        cot = das_cidades.get(cidade) or {}
        numericas = {k: v for k, v in cot.items() if isinstance(v, (int, float))}
        if not numericas:
            reguas = reguas_com_aviso.get(cidade) or []
            if reguas:
                # A cota existe, mas na régua da Defesa Civil, não na régua da
                # cidade. Comparar as duas seria somar zeros diferentes — o
                # erro que o item 4 da REGRA BLOQUEANTE do CLAUDE.md proíbe.
                aviso(
                    f"cotas-ruas.json: {cidade} tem rua alagando a {rua_mais_baixa:.2f} m e "
                    f"não tem cota de cidade, só a(s) régua(s) {', '.join(sorted(reguas))}. "
                    "Conferir se a cota de rua foi levantada contra essa mesma régua antes "
                    "de confiar na comparação"
                )
            else:
                aviso(
                    f"cotas-ruas.json: {cidade} tem rua alagando a {rua_mais_baixa:.2f} m, "
                    f"mas a cidade não tem NENHUMA cota cadastrada em estacoes.json — "
                    "o aviso por Telegram não cobre esta cidade"
                )
            continue
        menor_cota, nome = min((v, k) for k, v in numericas.items())
        if menor_cota > rua_mais_baixa:
            erro(
                f"cotas-ruas.json: em {cidade} a primeira rua alaga a "
                f"{rua_mais_baixa:.2f} m, mas a cota mais baixa cadastrada é "
                f"'{nome}' = {menor_cota:.2f} m. O aviso dispara "
                f"{menor_cota - rua_mais_baixa:.2f} m DEPOIS da água entrar."
            )


def valida_enchentes(conhecidas: set[tuple[str, str]]) -> None:
    eventos = le_json("enchentes.json")["eventos"]
    if not eventos:
        erro("enchentes.json: nenhum evento")
        return

    vistos: dict[tuple[str, str, str], int] = defaultdict(int)
    for i, ev in enumerate(eventos):
        onde = f"enchentes.json[{i}] ({ev.get('cidade', '???')} {ev.get('data', '???')})"

        for campo in ("rio", "cidade", "data", "pico_m", "confianca", "fonte"):
            if campo not in ev:
                erro(f"{onde}: falta o campo obrigatório '{campo}'")
        if len(erros) and any(c not in ev for c in ("rio", "cidade", "data", "pico_m")):
            continue

        valida_data(ev["data"], onde)

        pico = ev["pico_m"]
        if not isinstance(pico, (int, float)) or not 0 < pico < PICO_MAXIMO_M:
            erro(f"{onde}: pico_m = {pico} fora da faixa plausível (0 a {PICO_MAXIMO_M} m)")

        if ev.get("confianca") not in CONFIANCAS:
            erro(f"{onde}: confianca '{ev.get('confianca')}' não é alta/media/baixa")
        if not str(ev.get("fonte", "")).strip():
            erro(f"{onde}: sem fonte — a regra do projeto é não aceitar dado sem procedência")
        if "hora" in ev and not RE_HORA.match(str(ev["hora"])):
            erro(f"{onde}: hora '{ev['hora']}' fora do formato HH:MM")
        if "nota" in ev and not str(ev["nota"]).strip():
            erro(f"{onde}: campo 'nota' vazio — remova-o em vez de deixar em branco")

        # Valores divergentes publicados para o MESMO pico. Guardar em vez de descartar
        # é o que impede alguém de "corrigir" o arquivo de volta para um número pior.
        for j, div in enumerate(ev.get("divergencias", [])):
            ondiv = f"{onde} / divergencias[{j}]"
            if not isinstance(div.get("pico_m"), (int, float)) or not 0 < div["pico_m"] < PICO_MAXIMO_M:
                erro(f"{ondiv}: pico_m = {div.get('pico_m')} fora da faixa plausível")
            elif abs(div["pico_m"] - pico) < 1e-9:
                erro(f"{ondiv}: repete o valor adotado ({pico} m) — não é divergência")
            if not str(div.get("fonte", "")).strip():
                erro(f"{ondiv}: divergência sem fonte")

        if (ev["rio"], ev["cidade"]) not in conhecidas:
            aviso(f"{onde}: cidade não está em estacoes.json — não vai aparecer no diagrama")

        vistos[(ev["rio"], ev["cidade"], ev["data"])] += 1

    for (rio, cidade, data), n in vistos.items():
        if n > 1:
            erro(
                f"enchentes.json: {n} registros para ({rio}, {cidade}, {data}). "
                "O pareamento descarta eventos ambíguos — resolva a duplicata."
            )


def valida_transito(conhecidas: set[tuple[str, str]]) -> None:
    trechos = le_json("transito.json")["trechos"]
    # Posição comparável para pegar trecho que sobe o rio. Em rio em fila é a
    # `ordem`; em rio ramificado só o TRONCO tem sequência (ordem_no_ramo) —
    # cabeceiras e afluentes entram no tronco de lado e não se comparam por
    # número. NÃO usar `ordem` para existência: no Açu ela é null de propósito.
    ordem: dict[tuple[str, str], int] = {}
    estacoes = le_json("estacoes.json")
    for rio_id, rio in estacoes["rios"].items():
        ramificado = "_topologia" in rio
        for cidade in rio["cidades"]:
            if ramificado:
                if cidade.get("ramo") == "tronco_acu" and isinstance(cidade.get("ordem_no_ramo"), int):
                    ordem[(rio_id, cidade["id"])] = cidade["ordem_no_ramo"]
            elif isinstance(cidade.get("ordem"), int):
                ordem[(rio_id, cidade["id"])] = cidade["ordem"]

    for i, t in enumerate(trechos):
        onde = f"transito.json[{i}] ({t.get('de', '???')} -> {t.get('para', '???')})"
        for campo in ("rio", "de", "para", "horas_min", "horas_max", "confianca", "fonte"):
            if campo not in t:
                erro(f"{onde}: falta o campo '{campo}'")
                return

        if t["de"] == t["para"]:
            erro(f"{onde}: origem e destino iguais")
        if not isinstance(t["horas_min"], (int, float)) or not isinstance(
            t["horas_max"], (int, float)
        ):
            erro(f"{onde}: horas_min/horas_max precisam ser números")
        elif not 0 < t["horas_min"] <= t["horas_max"] <= 120:
            erro(f"{onde}: faixa {t['horas_min']}–{t['horas_max']} h fora de ordem ou implausível")
        if t["confianca"] not in CONFIANCAS:
            erro(f"{onde}: confianca '{t['confianca']}' não é alta/media/baixa")

        if (t["rio"], t["de"]) not in conhecidas:
            aviso(f"{onde}: '{t['de']}' não está em estacoes.json; trecho fica invisível na tela")
        if (t["rio"], t["para"]) not in conhecidas:
            aviso(f"{onde}: '{t['para']}' não está em estacoes.json; trecho fica invisível na tela")
        # Só compara sentido quando os dois lados têm posição no MESMO trecho
        # comparável (fila, ou tronco↔tronco). Feeder de cabeceira/afluente para
        # o tronco não tem "ordem" entre si — e não é subir o rio.
        de = ordem.get((t["rio"], t["de"]))
        para = ordem.get((t["rio"], t["para"]))
        if de is not None and para is not None and de >= para:
            erro(
                f"{onde}: o trecho sobe o rio (ordem {de} -> {para}). "
                "A água desce; isso inverteria o sentido da previsão."
            )
        if (t["rio"], t["de"]) not in conhecidas and (t["rio"], t["para"]) not in conhecidas:
            aviso(f"{onde}: nenhuma das pontas existe em estacoes.json")
        fora = [p for p in (t["de"], t["para"]) if (t["rio"], p) not in globals().get("_no_eixo", set())]
        if fora:
            erro(
                f"{onde}: {', '.join(fora)} tem régua própria, fora da sequência do eixo. "
                "Encadear tempo de descida por essa cidade daria resultado errado."
            )


def _janela_ate(trechos: list[dict], rio_id: str, de: str, para: str) -> tuple[float, float] | None:
    """
    Soma da menor cadeia de trechos de `de` até `para` — a mesma busca do site.

    Precisa ser a MESMA regra do `caminho()` de web/src/logica/transito.ts (direto
    quando existe, senão busca em largura): validar um percurso que a tela não usa
    aprovaria um dado que a tela mostra errado.
    """
    doRio = [t for t in trechos if t["rio"] == rio_id]
    direto = next((t for t in doRio if t["de"] == de and t["para"] == para), None)
    if direto:
        return (direto["horas_min"], direto["horas_max"])
    fila: list[tuple[str, list[dict]]] = [(de, [])]
    visto = {de}
    while fila:
        atual, rota = fila.pop(0)
        for t in doRio:
            if t["de"] != atual or t["para"] in visto:
                continue
            nova = rota + [t]
            if t["para"] == para:
                return (sum(x["horas_min"] for x in nova), sum(x["horas_max"] for x in nova))
            visto.add(t["para"])
            fila.append((t["para"], nova))
    return None


def valida_monotonia_transito() -> None:
    """
    A janela de chegada não pode contradizer a ordem do rio.

    CORREÇÃO DE 04/09/2026 — ISTO NÃO É MAIS ERRO, É AVISO
    Este teste nasceu tratando `min_montante > max_jusante` como IMPOSSÍVEL:
    "não existe tempo que satisfaça as duas janelas". A Tabela 7.5.1 da JICA
    (Vol. III-A, p. A-80), lida na fonte, mostra que a premissa é falsa. Nas
    colunas de 25 e 50 anos, **Blumenau pica ANTES de Indaial** (+7 h contra
    +8 h) — e Indaial fica a MONTANTE. Não é erro da tabela: o Rio Benedito
    entra justamente em Indaial, e num hidrograma de projeto a contribuição do
    afluente pode adiantar o pico de baixo. Jusante picar antes de montante é
    fisicamente possível quando há afluente no meio.

    Manter isso como erro rejeitaria dado oficial verdadeiro. Vira aviso.

    O QUE DE FATO CAUSA A INVERSÃO NO NOSSO DADO
    Não é fonte diferente — é COLUNA diferente da mesma tabela. Conferido célula
    a célula: `rio-do-sul->indaial = 10 h` é a coluna de 5 anos; o mínimo de
    `rio-do-sul->blumenau = 7 h` é a de 25/50 anos. Empilhar período de retorno
    diferente fabrica o paradoxo. Dentro de uma coluna só, Indaial e Blumenau
    ficam a 0–1 h um do outro.

    Por isso o aviso NOMEIA as três causas possíveis, em vez de sugerir defeito:
    mistura de colunas, afluente entrando no meio, ou dado realmente errado.
    Quem for arrumar precisa saber qual das três é — tratar tudo como defeito
    empurraria alguém a "consertar" trocando valor de fonte por interpolação,
    que é perder dado, não ganhar precisão.
    """
    trechos = le_json("transito.json")["trechos"]
    estacoes = le_json("estacoes.json")
    for rio_id, rio in estacoes["rios"].items():
        topo = rio.get("_topologia")
        if topo:
            sequencia = topo.get("tronco_sequencia", [])
        else:
            com_ordem = [c for c in rio["cidades"] if isinstance(c.get("ordem"), int)]
            sequencia = [c["id"] for c in sorted(com_ordem, key=lambda c: c["ordem"])]
        if len(sequencia) < 2:
            continue

        origem = sequencia[0]
        janelas: list[tuple[str, float, float]] = []
        for cidade in sequencia[1:]:
            j = _janela_ate(trechos, rio_id, origem, cidade)
            if j:
                janelas.append((cidade, j[0], j[1]))

        for i, (cima, cima_min, cima_max) in enumerate(janelas):
            for baixo, baixo_min, baixo_max in janelas[i + 1:]:
                if baixo_min >= cima_min:
                    continue
                grave = cima_min > baixo_max
                aviso(
                    f"transito.json / {rio_id}: a janela de {baixo} ({baixo_min}–{baixo_max} h "
                    f"desde {origem}) começa antes da de {cima} ({cima_min}–{cima_max} h), que "
                    f"fica a montante"
                    + (" — e nem chega a encostar nela" if grave else "")
                    + ". Três causas possíveis, nesta ordem de probabilidade: (1) os dois números "
                    "vêm de COLUNAS diferentes da Tabela 7.5.1 da JICA (períodos de retorno "
                    "diferentes), que é o caso conhecido no Açu; (2) há afluente entrando entre as "
                    "duas cidades, e ele adianta o pico de baixo — a própria tabela mostra "
                    "Blumenau picando antes de Indaial nas colunas de 25 e 50 anos, por causa do "
                    "Benedito; (3) dado errado. Conferir qual antes de mexer. "
                    "Ver docs/JANELA-DE-CHEGADA.md e docs/JICA-2011-VERIFICADO.md."
                )


def valida_meses_pareados() -> None:
    """
    Evento do mesmo ano em duas cidades do tronco tem de cair no mesmo MÊS.

    A cheia desce o Açu em horas — Rio do Sul → Blumenau são 7 a 10 h. Então
    duas cidades do tronco que registram o mesmo evento registram no mesmo dia,
    e no mesmo mês com folga de sobra. Mês diferente não é imprecisão: são
    eventos distintos, ou uma das datas está errada.

    A comparação é por MÊS, e não por dia, porque a série de Rio do Sul é quase
    toda de precisão mensal (7 de 9 registros). Exigir o dia recusaria dado bom.

    O teste é "existe ALGUM evento de jusante no mesmo mês", não "o evento de
    jusante mais próximo bate": Blumenau tem 113 registros, vários no mesmo ano,
    e uma cheia de montante casa com UMA delas, não com todas. Comparar contra
    todas produziria alarme em cima de dado correto.

    Vira AVISO, nunca erro: a data pode estar certa e ser evento distinto —
    quem decide é a fonte, não este script. O que ele faz é não deixar a
    divergência passar em silêncio.
    """
    eventos = le_json("enchentes.json")["eventos"]
    estacoes = le_json("estacoes.json")
    for rio_id, rio in estacoes["rios"].items():
        topo = rio.get("_topologia")
        tronco = topo.get("tronco_sequencia", []) if topo else []
        if len(tronco) < 2:
            continue

        # Só cidades do tronco: cabeceira e afluente entram no tronco de lado,
        # e um pico neles não é o mesmo evento descendo.
        por_cidade: dict[str, list[str]] = {}
        for e in eventos:
            if e.get("rio") != rio_id or e.get("cidade") not in tronco:
                continue
            por_cidade.setdefault(e["cidade"], []).append(str(e.get("data", "")))

        for i, cima in enumerate(tronco):
            for baixo in tronco[i + 1:]:
                for data_cima in por_cidade.get(cima, []):
                    if len(data_cima) < 7:
                        continue  # só o ano: não dá para comparar mês
                    ano, mes = data_cima[:4], data_cima[5:7]
                    do_ano = [d for d in por_cidade.get(baixo, []) if d[:4] == ano and len(d) >= 7]
                    if not do_ano:
                        continue  # jusante não registrou aquele ano: nada a concluir
                    if any(d[5:7] == mes for d in do_ano):
                        continue
                    aviso(
                        f"enchentes.json: {cima} {data_cima} não tem evento de {baixo} no mesmo "
                        f"mês (o ano tem {', '.join(sorted(do_ano))}). A cheia desce em horas, "
                        "então ou são eventos distintos, ou uma das datas está errada — "
                        "conferir na fonte antes de parear."
                    )


#: Qual traçado desenha cada RAMO da árvore. Ramo sem entrada aqui não é
#: checado — é o caso de quem não tem rio desenhado nenhum (Benedito, Hercílio).
TRACADO_DO_RAMO = {
    "tronco_acu": "itajai-acu",
    "itajai_do_oeste": "itajai-acu",   # o Oeste vem DENTRO do arquivo do Açu (OSM)
    "itajai_do_sul": "itajai-do-sul",
}

#: Pinos que podem cair longe do traçado do ramo deles, com o MOTIVO. Exceção
#: sem motivo escrito vira lixo em seis meses; cada uma aqui diz por que existe
#: e o que a remove.
LONGE_ACEITO = {
    # CORRIGIDO em 06/09/2026 pelo inventário da ANA. O motivo escrito aqui
    # dizia "a coordenada é a da ESTAÇÃO" e dava a entender que era a régua de
    # nível. Não é: a DCSC-00026 é do tipo `Meteo`, com `tem_nivel_do_rio:
    # false` — mede CHUVA. A fluviométrica da ANA em Blumenau (83800002) fica a
    # 6,93 km deste pino e a 49 m do traçado. A exceção continua, porque mover o
    # pino trocaria uma coordenada errada por uma de OUTRA REDE; o que muda é
    # que o motivo agora diz a verdade, e o que a remove ficou concreto.
    "blumenau": (3.5, "a coordenada publicada é a da DCSC-00026, que é estação de "
                      "CHUVA (type Meteo, tem_nivel_do_rio false) e fica a ~3 km do "
                      "talvegue — não é a régua de nível de Blumenau. Remove esta "
                      "exceção: a coordenada da régua do AlertaBlu/Defesa Civil, que "
                      "é a fonte do tempo real mostrado na tela"),
    "ituporanga": (25.0, "o traçado do Itajaí do Sul é PARCIAL (10,5 km, cobertura "
                         "municipal de Rio do Sul). Falta o trecho Ituporanga->Rio do Sul, "
                         "que sai do Overpass — ver docs/TRACADO-ITAJAI-DO-SUL.md. "
                         "Baixe o trecho e este número cai para <1 km."),
    # ACHADO POR ESTA PRÓPRIA TRAVA, na primeira execução (05/09/2026), sem que
    # ninguém tivesse reportado: Guabiruba fica a 4,24 km do Mirim e longe de
    # todo o resto. Não é erro de coordenada — a cidade fica no RIBEIRÃO
    # Guabiruba, afluente que não está desenhado. Duas fontes concordam: o
    # `coleta_nivel_sc.py` já chamava a leitura dela de "implausível PARA O
    # RIBEIRÃO". É a MESMA omissão do Itajaí do Sul e dos ribeirões de Itajaí: a
    # consulta do Overpass só pediu `waterway=river` com os nomes do tronco.
    "guabiruba": (5.0, "fica no Ribeirão Guabiruba, afluente do Mirim que não está "
                       "desenhado — mesma lacuna do Overpass do Itajaí do Sul. Baixar o "
                       "ribeirão (docs/TRACADO-ITAJAI-DO-SUL.md) derruba este número."),
}

#: Acima disto o pino flutua: aparece sobre o satélite, sem rio embaixo.
LIMITE_PINO_KM = 1.0


def _km_ao_segmento(p, a, b) -> float:
    """Distância em km do ponto ao SEGMENTO ab (não só aos vértices)."""
    kx = 111.32 * math.cos(math.radians(p[1]))
    ax, ay = (a[0] - p[0]) * kx, (a[1] - p[1]) * 110.57
    bx, by = (b[0] - p[0]) * kx, (b[1] - p[1]) * 110.57
    dx, dy = bx - ax, by - ay
    if dx == 0 and dy == 0:
        return math.hypot(ax, ay)
    t = max(0.0, min(1.0, -(ax * dx + ay * dy) / (dx * dx + dy * dy)))
    return math.hypot(ax + t * dx, ay + t * dy)


def _linhas(caminho) -> list:
    g = json.loads(caminho.read_text(encoding="utf-8"))
    feats = g.get("features") if g.get("type") == "FeatureCollection" else [g]
    saida = []
    for f in feats or []:
        geo = f.get("geometry") or {}
        co = geo.get("coordinates") or []
        if geo.get("type") == "MultiLineString":
            saida.extend(l for l in co if len(l) >= 2)
        elif geo.get("type") == "LineString" and len(co) >= 2:
            saida.append(co)
    return saida


def valida_pinos_no_tracado() -> None:
    """
    Cada cidade com pino cai em cima do traçado do RAMO DELA?

    POR QUE EXISTE (05/09/2026). O Itajaí do Sul não estava desenhado: a
    consulta do Overpass pediu Açu, Mirim e Oeste, e nunca o Sul. Na tela,
    Ituporanga e a Barragem Sul flutuavam a 28 e 31 km de qualquer linha — e a
    linha que passava perto delas era o OESTE, o que faz o mapa sugerir
    Taió -> Ituporanga -> Rio do Sul EM SÉRIE. Os dados diziam a árvore certa; o
    DESENHO dizia a fila, e o desenho é o que o morador lê primeiro.

    Ninguém viu por meses porque "parecer certo" não é medida. Agora é: um pino
    novo que flutue reprova aqui, antes de ir ao ar.

    O QUE ESTE NÚMERO NÃO É: não mede erro de coordenada. Um pino pode estar
    corretamente longe do talvegue (Blumenau, cuja coordenada é a da estação).
    Por isso as exceções são NOMEADAS, com motivo — e cada uma tem um teto
    próprio, para que piorar também reprove.
    """
    est = le_json("estacoes.json")
    rios_dir = RAIZ / "data" / "rios"
    cache: dict[str, list] = {}

    # Uma cidade pode estar em DOIS rios com UMA coordenada — Itajaí está no Açu
    # e no Mirim, e o pino dela fica no Açu (0,87 km) e a 2,11 km do Mirim.
    # Cobrar rio a rio a reprovaria por estar no lugar certo. O que interessa é
    # se o pino cai em ALGUM rio dela.
    alvos_por_cidade: dict[str, tuple[list, set[str]]] = {}
    for rio_id, rio in est.get("rios", {}).items():
        for c in rio.get("cidades", []):
            ramo = c.get("ramo")
            alvo = TRACADO_DO_RAMO.get(ramo) if ramo else rio_id
            if not alvo:
                continue
            coord = c.get("coordenadas")
            if not isinstance(coord, list) or len(coord) != 2:
                continue
            atual = alvos_por_cidade.setdefault(c["id"], (coord, set()))
            atual[1].add(alvo)

    for cidade_id, (coord, alvos) in sorted(alvos_por_cidade.items()):
        lat, lon = coord
        distancias: dict[str, float] = {}
        for alvo in sorted(alvos):
            caminho = rios_dir / f"{alvo}.geojson"
            if not caminho.exists():
                erro(f"estacoes.json / {cidade_id}: o rio {alvo!r} deveria ser desenhado por "
                     f"{alvo}.geojson, que NÃO EXISTE. Sem traçado, o pino flutua e a linha "
                     "vizinha vira o rio dele aos olhos de quem lê.")
                continue
            if alvo not in cache:
                cache[alvo] = _linhas(caminho)
            distancias[alvo] = min(
                (_km_ao_segmento((lon, lat), l[i], l[i + 1])
                 for l in cache[alvo] for i in range(len(l) - 1)),
                default=math.inf,
            )
        if not distancias:
            continue
        alvo, d = min(distancias.items(), key=lambda kv: kv[1])
        teto, motivo = LONGE_ACEITO.get(cidade_id, (LIMITE_PINO_KM, ""))
        if d > teto:
            extra = f" (exceção aceita até {teto:g} km: {motivo})" if motivo else ""
            erro(f"estacoes.json / {cidade_id}: fica a {d:.2f} km do traçado mais perto "
                 f"({alvo}); limite {teto:g} km{extra}. Ou falta desenhar o rio dele, ou a "
                 "coordenada está errada — nos dois casos o pino flutua no mapa.")


#: Chaves de cota que PINTAM cor no mapa. Fora daqui, a chave é marca de
#: referência e não vira faixa (ver logica/faixaDaCidade e docs/kikikuru.md).
CHAVES_QUE_PINTAM = {"atencao", "alerta", "inundacao", "emergencia"}


#: Abaixo disto, um `cota_m` de rua é lâmina d'água disfarçada. Ver a guarda.
PISO_COTA_DE_RUA_M = 3.0


def valida_cota_de_rua_nao_e_lamina() -> None:
    """
    Um `cota_m` baixo demais é LÂMINA D'ÁGUA, não cota de rua.

    POR QUE EXISTE (06/09/2026). O ArcGIS da Prefeitura de Itajaí publica 3.434
    pontos num app chamado **"Cotas de Inundação"**, com um campo chamado
    **`cota`** — e ele NÃO é cota de rua. Os valores vão de 0 a 2,86 m, mediana
    0,60: é a **lâmina**, quanto a água subiu NAQUELE endereço durante o evento.
    Cota de rua é outra coisa: o **nível do rio** a partir do qual a rua alaga.

    A confusão é fácil e o estrago é grande. Se essas linhas entrassem em
    `cotas-ruas.json` porque "as duas têm cota", o site diria "a sua rua alaga
    com o rio em 0,60 m" — e o rio está nesse nível quase sempre.

    A separação é MEDIDA, não estipulada. As 4.588 cotas de rua do cadastro:

        blumenau    mín  7,40    rio-do-sul  mín  3,11
        gaspar      mín  6,20    brusque     mín  3,76

    **Nenhuma abaixo de 3,00 m.** As lâminas de Itajaí, nenhuma acima de 2,86.
    As duas faixas não se tocam, e o piso cai no vão entre elas.

    Se um dia existir cota de rua legítima abaixo do piso — cidade de várzea com
    régua de zero alto —, o registro declara `cota_baixa_conferida: true` com a
    nota de quem conferiu. O que não pode é entrar em silêncio.
    """
    dados = le_json("cotas-ruas.json")
    baixas = []
    for c in dados.get("cotas", []):
        v = c.get("cota_m")
        if not isinstance(v, (int, float)) or v >= PISO_COTA_DE_RUA_M:
            continue
        if c.get("cota_baixa_conferida") is True:
            continue
        baixas.append((c.get("cidade"), c.get("rua"), v))
    if baixas:
        amostra = "; ".join(f"{cid}/{rua}={v:.2f}" for cid, rua, v in baixas[:4])
        erro(f"cotas-ruas.json: {len(baixas)} rua(s) com cota_m abaixo de "
             f"{PISO_COTA_DE_RUA_M:.2f} m ({amostra}). Cota de rua é o NÍVEL DO RIO em que a rua "
             "alaga; valor tão baixo é lâmina d'água (quanto a água subiu no endereço) entrando no "
             "lugar errado — o ArcGIS de Itajaí chama a lâmina de 'cota'. A menor cota real do "
             "cadastro é 3,11 m. Se a cota baixa for legítima, marque `cota_baixa_conferida: true`.")


def valida_pico_copiado_de_outra_cidade() -> None:
    """
    Um pico igual ao de OUTRA cidade no mesmo evento é cópia até prova em contrário.

    POR QUE EXISTE (06/09/2026). A busca pelos picos de Itajaí devolveu resultado
    NEGATIVO: tudo que circula com metro nas datas das dez manchas é régua de
    BLUMENAU. 15,34 em 1983, 15,46 em 1984, 11,02 em 2001, 11,52 em 2008 — todos
    de Blumenau, todos aparecendo em textos que falam de Itajaí. A "Itajaipedia"
    copia a série de Blumenau; a estação ANA da cidade (02648008) é PLUVIOMÉTRICA;
    e não há código fluviométrico da barra no cadastro.

    Ou seja: os números errados estão a um copiar-e-colar de distância, com o nome
    do evento certo ao lado. Gravar 15,34 m como pico de Itajaí aplicaria a régua
    de uma cidade a 70 km rio acima — a régua de Blumenau, cujo zero não tem
    relação nenhuma com a foz.

    Dois picos podem coincidir de verdade? Podem, por acaso, ao centímetro — e por
    isso a saída é declarar `coincidencia_conferida: true` no registro, com a nota
    de quem conferiu. O que não pode é passar em silêncio.
    """
    dados = le_json("enchentes.json")
    por_evento: dict = {}
    for e in dados.get("eventos", []):
        # O campo é `pico_m`. A primeira versão desta guarda leu `nivel_m`, que
        # não existe em enchentes.json: ela passava em silêncio, sem nunca poder
        # disparar. Guarda que não morde é pior que guarda nenhuma, porque
        # parece proteger.
        nivel = e.get("pico_m")
        if not isinstance(nivel, (int, float)):
            continue
        chave = (e.get("data") or e.get("ano"), round(float(nivel), 2))
        por_evento.setdefault(chave, []).append(e)
    for (quando, nivel), registros in sorted(por_evento.items(), key=lambda kv: str(kv[0])):
        cidades = {r.get("cidade") for r in registros}
        if len(cidades) < 2:
            continue
        nao_conferidos = [r for r in registros if r.get("coincidencia_conferida") is not True]
        if len(nao_conferidos) < 2:
            continue
        erro(f"enchentes.json: {sorted(cidades)} têm o MESMO nível {nivel:.2f} m em {quando!r}. "
             "Cada cidade tem a sua régua, com zero próprio; nível idêntico entre cidades é cópia "
             "até prova em contrário — o caso conhecido é a série de Blumenau reaparecendo como se "
             "fosse de Itajaí. Se a coincidência foi conferida na fonte, marque "
             "`coincidencia_conferida: true` no registro, com a nota de quem conferiu.")


def valida_regua_das_cotas() -> None:
    """
    Cidade que PINTA cor no mapa declara de qual régua são as cotas?

    POR QUE EXISTE (06/09/2026). A regra nº 1 do projeto é não aplicar a cota de
    uma régua à leitura de outra. Medido: NOVE cidades pintam e, até este
    commit, NENHUMA declarava a régua das cotas — e as dezesseis estações ao
    vivo têm `regua: null`. Ou seja, a regra existia em palavras e não havia
    campo onde ela pudesse ser conferida.

    Rio do Sul é o caso em que alguém sabia os nomes: as cotas 4,50/5,50/6,50
    são da **Ponte Dom Tito Buss** e a leitura chega como **Estação MKS**
    (scripts/conferir_par_regua.py). São réguas de nome diferente, e a cor do
    mapa sai desse par não provado.

    É AVISO, não erro, de propósito: virar erro reprovaria as nove de uma vez e
    o conserto seria apagar cota — tirar cor do mapa numa cidade durante cheia é
    decisão de quem mantém o projeto, não efeito colateral de um validador. O
    aviso mantém a lacuna VISÍVEL a cada rodada, que é o que faltava.
    """
    est = le_json("estacoes.json")
    sem_regua = []
    for rio in est.get("rios", {}).values():
        for c in rio.get("cidades", []):
            if not (set(c.get("cotas_m") or {}) & CHAVES_QUE_PINTAM):
                continue
            if not str(c.get("regua_das_cotas") or "").strip():
                sem_regua.append(c["id"])
    if sem_regua:
        aviso(f"estacoes.json: {len(sem_regua)} cidade(s) pintam cor no mapa sem declarar de qual "
              f"régua são as cotas ({', '.join(sorted(sem_regua))}). A cor sai de um par "
              "cota<->leitura que ninguém pode conferir. Preencher `regua_das_cotas` com o nome que "
              "a FONTE dá, ou registrar por que não se sabe.")


def valida_hidraulica() -> None:
    """
    Confere `hidraulica.json` — o dado do JICA que explica a bacia.

    O que se confere aqui NÃO é o valor: é que cada bloco continue com FONTE, e
    que os números que o site poderia confundir com cota fiquem fora do alcance.
    Vazão em m³/s e cota em metros são grandezas diferentes; o dia em que uma
    virar a outra na tela, alguém decide errado.

    Trava também a ressalva que a auditoria levantou: as áreas de drenagem das
    barragens divergem entre o JICA e a API estadual, e as duas têm de continuar
    gravadas lado a lado. Fundir seria escolher em silêncio.
    """
    d = le_json("hidraulica.json")
    if "_meta" not in d or "fonte" not in d.get("_meta", {}):
        erro("hidraulica.json: falta _meta.fonte — dado sem fonte não entra neste projeto")

    for bloco in ("declividade_por_trecho", "capacidade_de_vazao", "barragens",
                  "curva_chave_2008", "divisao_do_mirim", "areas_drenagem"):
        if bloco not in d:
            erro(f"hidraulica.json: falta o bloco '{bloco}'")
        elif not str(d[bloco].get("_fonte", "")).strip():
            erro(f"hidraulica.json / {bloco}: falta '_fonte'")

    # As duas delimitações de área têm de coexistir — ver o comentário acima.
    for nome in ("oeste", "sul"):
        b = d.get("barragens", {}).get(nome, {})
        for campo in ("area_drenagem_km2_jica", "area_drenagem_km2_api_estadual"):
            if not isinstance(b.get(campo), (int, float)):
                erro(f"hidraulica.json / barragens / {nome}: falta '{campo}'. As duas "
                     "delimitações ficam lado a lado; fundir seria escolher em silêncio.")

    # A tela de início nomeia as barragens a partir daqui, sem texto fixo. Sem
    # estes campos ela ficaria muda sobre uma delas — ou inventaria o nome.
    est_h = le_json("estacoes.json")
    abaixo_de_barragem: dict[str, str] = {}
    # Toda entrada com `nome` é barragem: as três de CONTENÇÃO da bacia e as
    # LOCAIS (Pinhal, Rio Bonito), que o PLANCON de Rio dos Cedros cita e que
    # NÃO amortecem a cheia do Açu. Sem `tipo`, a tela as listaria lado a lado
    # e diria que a bacia tem cinco barragens de contenção. Tem três.
    for nome, b in d.get("barragens", {}).items():
        if nome.startswith("_") or not isinstance(b, dict) or not b.get("nome"):
            continue
        tipo = b.get("tipo")
        if tipo not in ("contencao_estadual", "local"):
            erro(f"hidraulica.json / barragens / {nome}: 'tipo' tem de ser 'contencao_estadual' "
                 f"ou 'local' (veio {tipo!r}). É o que impede a tela de somar as duas classes.")
        for campo in ("nome", "municipio_nome", "rio", "rio_id"):
            if not str(b.get(campo, "")).strip():
                erro(f"hidraulica.json / barragens / {nome}: falta '{campo}' (a tela lê daqui)")
        rio_id = b.get("rio_id")
        ids = {c["id"] for c in est_h.get("rios", {}).get(rio_id, {}).get("cidades", [])}

        if tipo == "local":
            # Barragem local NÃO declara `a_montante_de`: dizer que ela fica logo
            # acima da régua de uma cidade é afirmar posição hidráulica, e a fonte
            # das locais (PLANCON municipal) não diz isso. Ela declara só ONDE FICA.
            if b.get("a_montante_de"):
                erro(f"hidraulica.json / barragens / {nome}: barragem 'local' não pode ter "
                     "'a_montante_de' — isso afirma posição acima de uma régua que a fonte não dá. "
                     "Use 'no_municipio'.")
            municipio = b.get("no_municipio")
            if not municipio:
                erro(f"hidraulica.json / barragens / {nome}: falta 'no_municipio'")
            elif municipio not in ids:
                erro(f"hidraulica.json / barragens / {nome}: no_municipio={municipio!r} não é "
                     f"cidade de {rio_id!r}")
            continue

        # A cidade logo abaixo da parede tem de existir no rio da barragem — senão
        # a tela diria "acima de X" para um X sem página e sem régua.
        abaixo = b.get("a_montante_de")
        if not abaixo:
            erro(f"hidraulica.json / barragens / {nome}: falta 'a_montante_de' (a tela lê daqui)")
        elif abaixo not in ids:
            erro(f"hidraulica.json / barragens / {nome}: a_montante_de={abaixo!r} não é cidade de {rio_id!r}")
        # Duas barragens de contenção não são a de logo acima da MESMA cidade: a
        # árvore as penduraria no mesmo galho e uma apareceria no ramo errado — a
        # Norte, que está no Hercílio, encostada na cabeceira do Oeste, por
        # exemplo. Sem isto, uma troca de cidade passa calada.
        if abaixo:
            outra = abaixo_de_barragem.get(abaixo)
            if outra:
                erro(f"hidraulica.json / barragens / {nome}: a_montante_de={abaixo!r} já é de "
                     f"{outra!r}. Cada barragem de contenção tem a SUA cidade logo abaixo da parede.")
            abaixo_de_barragem[abaixo] = nome

    # As três de contenção continuam existindo, com esses nomes. Se uma sumir ou
    # for rebaixada a 'local', a bacia passaria a ter duas — e o site diria isso.
    contencao = {n for n, b in d.get("barragens", {}).items()
                 if isinstance(b, dict) and b.get("tipo") == "contencao_estadual"}
    if contencao != {"oeste", "sul", "norte"}:
        erro(f"hidraulica.json / barragens: as de contenção da bacia são oeste, sul e norte; "
             f"vieram {sorted(contencao)}")

    # As TRÊS delimitações de área das barragens têm de continuar visíveis, e a
    # nota tem de dizer que o lado isolado é o Vol. II. Medido em 04/09/2026:
    # Vol. III-A dá Oeste 851,2 e Sul 1.165,4, contra 1.042 e 1.273 do Vol. II —
    # e a API estadual (851 e 1.164) concorda com o Vol. III-A. Perder isso faria
    # alguém recalcular a `chuva_equivalente_mm` com a área errada: a da Oeste
    # sai 79,7 mm por um caminho e 97,5 mm pelo outro.
    areas = d.get("areas_drenagem", {})
    for nome, esperado in (("barragem_oeste", 851.2), ("barragem_sul", 1165.4)):
        obtido = areas.get("estacoes_km2", {}).get(nome)
        if obtido != esperado:
            erro(f"hidraulica.json / areas_drenagem: {nome} deixou de ser {esperado} km² "
                 f"(Vol. III-A). Se a fonte mudou, atualize também a nota de divergência.")
    if "Vol. II" not in str(areas.get("_divergencia_interna_do_JICA", "")):
        erro("hidraulica.json / areas_drenagem: a nota de divergência sumiu ou deixou de "
             "nomear o Vol. II. As três delimitações ficam lado a lado; sem a nota, "
             "alguém recalcula a chuva equivalente com a área errada.")

    # Curva-chave: par nível->vazão só serve se os dois lados existirem, e o
    # nível tem de ser plausível como régua de rio.
    for i, p_ in enumerate(d.get("curva_chave_2008", {}).get("pontos", [])):
        onde = f"hidraulica.json / curva_chave_2008[{i}] ({p_.get('cidade', '???')})"
        if not isinstance(p_.get("nivel_m"), (int, float)) or not 0 < p_["nivel_m"] < PICO_MAXIMO_M:
            erro(f"{onde}: nivel_m fora de faixa plausível")
        if not isinstance(p_.get("vazao_m3s"), (int, float)) or p_["vazao_m3s"] <= 0:
            erro(f"{onde}: vazao_m3s ausente ou não positiva")

    # O número que a auditoria NÃO conseguiu confirmar não pode voltar como
    # VALOR. Procurar a string seria pior que inútil: o próprio texto que avisa
    # para não gravá-lo cita o número, e o guarda acusaria a advertência.
    if _tem_valor(d, 8400):
        erro("hidraulica.json: 8.400 aparece como VALOR. O retorno de '8.400 anos' para 2008 "
             "não foi confirmado na fonte — a auditoria achou 270 anos para 1 dia em "
             "Blumenau. Citar em texto, com a ressalva, tudo bem; gravar como número, não.")


def _tem_valor(no, alvo: float) -> bool:
    """O número aparece em alguma POSIÇÃO DE VALOR da árvore? Texto não conta."""
    if isinstance(no, dict):
        return any(_tem_valor(v, alvo) for v in no.values())
    if isinstance(no, list):
        return any(_tem_valor(v, alvo) for v in no)
    return isinstance(no, (int, float)) and not isinstance(no, bool) and float(no) == alvo


#: Estações da ANA já lidas no INVENTÁRIO PÚBLICO (`Inventario31_08_2026.mdb`,
#: tabela `Estacao`, 1.099.296 registros, aberto com `mdbtools` em 06/09/2026).
#: Campos: (nome, tipo, lat, lon, fim_da_escala). `lat`/`lon` só quando o
#: inventário foi transcrito ponto a ponto; None = conhecido o tipo, não a
#: coordenada. `fim_da_escala` = último ano/mês com régua convencional; None =
#: ativa.
#:
#: POR QUE ESTA TABELA EXISTE. O cruzamento de 06/09/2026 mediu a distância
#: entre as réguas do projeto e TODAS as estações da ANA em SC. Cinco "bateram"
#: por coordenada — e QUATRO delas são PLUVIÔMETROS. O caso que ensina é Taió:
#: a `2750017 TAIÓ` fica a 53 m da nossa régua e não mede rio nenhum. Um
#: pluviômetro e uma régua cabem no mesmo poste.
#:
#: É a emenda à regra nº 1 do projeto: o vínculo é por coordenada E POR TIPO.
#: Coordenada é condição necessária, não suficiente.
ESTACOES_ANA_CONHECIDAS = {
    # --- fluviométricas (medem NÍVEL DE RIO) ---
    "83050000": ("TAIÓ", "fluviometrica", -27.1139, -49.9953, None),
    "83300200": ("RIO DO SUL - NOVO", "fluviometrica", -27.2078, -49.6292, None),
    "83800002": ("BLUMENAU (PCD)", "fluviometrica", -26.9186, -49.0656, "2021-12"),
    "83920000": ("PORTO ITAJAÍ", "fluviometrica", -26.9167, -48.65, "1937-11"),
    # sem coordenada transcrita: o tipo basta para a trava de tipo
    "83030000": ("BARRAGEM OESTE", "fluviometrica", None, None, None),
    "83094000": ("RIO DO SUL (Itajaí do Oeste)", "fluviometrica", None, None, None),
    "83250000": ("ITUPORANGA", "fluviometrica", None, None, None),
    "83300000": ("RIO DO SUL (Itajaí do Sul)", "fluviometrica", None, None, None),
    "83440000": ("IBIRAMA", "fluviometrica", None, None, "2021-12"),
    "83520000": ("WARNOW", "fluviometrica", None, None, None),
    "83690000": ("INDAIAL", "fluviometrica", None, None, "2021-12"),
    "83800003": ("BLUMENAU (PCD)", "fluviometrica", None, None, None),
    "83840000": ("GASPAR (MONTANTE ETA)", "fluviometrica", None, None, "2021-12"),
    "83870001": ("ILHOTA-JUSANTE", "fluviometrica", None, None, None),
    "83892990": ("SALSEIRO", "fluviometrica", None, None, None),
    "83892998": ("BOTUVERA-MONTANTE", "fluviometrica", None, None, None),
    "83900000": ("BRUSQUE (PCD)", "fluviometrica", None, None, None),
    # --- pluviométricas: SÓ CHUVA. Estão aqui para REPROVAR quem as usar como
    # régua. Todas ficam a menos de 750 m de uma régua nossa — é essa vizinhança
    # que faz o erro parecer acerto.
    "2750017": ("TAIÓ", "pluviometrica", None, None, None),
    "2648065": ("ITAJAÍ_Centro", "pluviometrica", None, None, None),
    "2648008": ("ITAJAÍ", "pluviometrica", None, None, None),
    "2649084": ("INDAIAL", "pluviometrica", None, None, None),
    "2749097": ("VIDAL RAMOS_Centro", "pluviometrica", None, None, None),
}


def valida_codigo_ana() -> None:
    """
    O `codigo_ana` de cada cidade mede NÍVEL DE RIO, e a estação fica no rio?

    POR QUE EXISTE (06/09/2026). O inventário público da ANA foi cruzado com as
    réguas do projeto por coordenada, que é a regra nº 1. Cinco estações caíram
    a menos de 750 m de uma régua nossa; QUATRO são pluviômetros. Se uma delas
    entrasse como `codigo_ana`, o projeto passaria a chamar de "série histórica
    de nível" uma série de CHUVA — e ninguém veria, porque o código está certo,
    o nome está certo, o município está certo e a coordenada está certa.

    Três coisas reprovam aqui:

    1. `codigo_ana` que a ANA cadastra como PLUVIOMÉTRICA.
    2. estação fluviométrica cuja coordenada cai longe do traçado do ramo da
       cidade — ou a coordenada está errada, ou é estação de outro rio.
    3. (aviso) estação com a escala ENCERRADA e sem sucessora declarada em
       `codigo_ana_sucessor`. Quatro réguas da bacia morreram em 12/2021; a
       série histórica continua valendo, o presente não.
    """
    dados = le_json("estacoes.json")
    cache: dict[str, list] = {}

    for rio_id, rio in dados["rios"].items():
        for cidade in rio["cidades"]:
            codigo = cidade.get("codigo_ana")
            if not codigo:
                continue
            cid = cidade["id"]
            chave = str(codigo).lstrip("0") or "0"
            conhecida = ESTACOES_ANA_CONHECIDAS.get(chave)
            if conhecida is None:
                continue

            nome, tipo, lat, lon, fim = conhecida

            if tipo != "fluviometrica":
                erro(f"estacoes.json / {cid}: codigo_ana {codigo} ({nome}) é "
                     f"{tipo.upper()} no inventário da ANA — mede CHUVA, não nível de "
                     "rio. Estar no município certo e a poucos metros da régua não "
                     "faz dela a régua: o vínculo é por coordenada E POR TIPO.")
                continue

            # `codigo_ana_sucessor: null` COM nota é resposta válida: em Gaspar
            # a ANA não tem sucessora nenhuma, e exigir um código faria inventar
            # um. O que não pode é a chave faltar.
            declarou = ("codigo_ana_sucessor" in cidade
                        and (cidade["codigo_ana_sucessor"]
                             or cidade.get("codigo_ana_sucessor_nota")))
            if fim and not declarou:
                aviso(f"estacoes.json / {cid}: a escala da estação {codigo} ({nome}) "
                      f"ENCERROU em {fim}. Serve para série histórica, não para o "
                      "presente. Declare `codigo_ana_sucessor` (ou null com o motivo, "
                      "quando a ANA não tem sucessora).")

            if lat is None or lon is None:
                continue

            arquivo = TRACADO_DO_RAMO.get(cidade.get("ramo") or "")
            if rio_id == "itajai-mirim":
                arquivo = "itajai-mirim"
            if not arquivo:
                continue
            caminho = RAIZ / "data" / "rios" / f"{arquivo}.geojson"
            if not caminho.exists():
                continue
            if arquivo not in cache:
                cache[arquivo] = _linhas(caminho)

            p = (lon, lat)
            d = min((_km_ao_segmento(p, l[i], l[i + 1])
                     for l in cache[arquivo] for i in range(len(l) - 1)), default=None)
            if d is not None and d > LIMITE_PINO_KM:
                erro(f"estacoes.json / {cid}: a estação ANA {codigo} ({nome}) fica a "
                     f"{d:.2f} km do traçado de {arquivo}; limite {LIMITE_PINO_KM:g} km. "
                     "Estação fluviométrica fica NO rio — ou a coordenada está errada, "
                     "ou a estação é de outro curso d'água.")


#: Arquivo do site que guarda quantas ruas de cada cidade foram levantadas SEM
#: coordenada. Ver a guarda abaixo.
COTAS_NO_MAPA_TS = "web/src/logica/cotasNoMapa.ts"


# A tábua de maré acaba, e quando acaba o painel da foz fica MUDO. Estes são
# os prazos: aviso quando resta menos que o primeiro, erro quando já acabou.
DIAS_DE_MARE_MINIMOS = 30


def valida_cobertura_da_mare() -> None:
    """
    Até quando a tábua de maré alcança?

    POR QUE EXISTE (07/09/2026). A base tinha preamares e baixamares de
    01/09/2026 a 30/09/2026 e MAIS NADA — um único mês. Em 06/09 isso eram 24
    dias de tábua restantes: no dia 1º de outubro o painel de maré de Itajaí
    ficaria vazio, sem ninguém ser avisado, e a maré é metade da explicação da
    cheia na foz (maré alta trava a saída da água).

    Uma tábua que acaba não avisa que acabou. Este validador avisa.

    A tábua é PREVISÃO ASTRONÔMICA e vem de fonte anual (CHM/Marinha,
    Epagri/Ciram, UNIVALI): renovar é trabalho de importação, não de coleta
    automática — mais uma razão para o alarme tocar com semanas de folga.
    """
    try:
        dados = le_json("mare-itajai.json")
    except FileNotFoundError:
        aviso("mare-itajai.json: ausente — o painel de maré da foz fica sem tábua.")
        return

    hoje = date.today()
    for chave in ("preamares", "baixamares"):
        pontos = dados.get(chave)
        if not isinstance(pontos, list) or not pontos:
            erro(f"mare-itajai.json: '{chave}' vazio ou ausente — o painel da foz fica mudo.")
            continue
        quandos = [p.get("quando") for p in pontos if isinstance(p, dict) and isinstance(p.get("quando"), str)]
        if not quandos:
            erro(f"mare-itajai.json: '{chave}' sem nenhum campo `quando` legível.")
            continue
        try:
            ultimo = max(date.fromisoformat(q[:10]) for q in quandos)
        except ValueError:
            erro(f"mare-itajai.json: '{chave}' tem `quando` fora do formato ISO.")
            continue
        restam = (ultimo - hoje).days
        if restam < 0:
            erro(
                f"mare-itajai.json: '{chave}' terminou em {ultimo.isoformat()}, "
                f"há {-restam} dia(s). O painel de maré da foz JÁ está sem tábua."
            )
        elif restam < DIAS_DE_MARE_MINIMOS:
            aviso(
                f"mare-itajai.json: '{chave}' vai até {ultimo.isoformat()} — restam "
                f"{restam} dia(s). Importar a tábua do ano antes que acabe: fonte anual "
                f"(CHM/Marinha ou Epagri/Ciram), com proveniência por evento e sem "
                f"misturar em silêncio com a série já cadastrada."
            )


def valida_ruas_sem_coordenada() -> None:
    """
    Os números de `RUAS_SEM_COORDENADA` batem com o `cotas-ruas.json`?

    POR QUE EXISTE (06/09/2026). O mapa dizia a TODA cidade sem ponto de rua
    "aproxime para ver as cotas de rua". Blumenau tem o maior levantamento do
    projeto — 2.042 ruas — e NENHUMA com coordenada, porque a lista da Defesa
    Civil publicada pela imprensa traz rua, bairro e cota, sem ponto. Quem mora
    lá aproximava, não achava nada, e podia concluir que a rua dele não tinha
    sido levantada. Foi: está na tela da cidade, por nome.

    A frase certa depende de saber, ANTES de carregar 3 MB de cotas, se a
    cidade tem levantamento não mapeável. Por isso o site guarda dois números
    fixos — e por isso eles precisam desta trava: número copiado à mão envelhece
    calado, e este envelheceria dizendo a uma cidade que ela tem levantamento
    que ela deixou de ter, ou escondendo o que ela passou a ter.
    """
    cotas = le_json("cotas-ruas.json").get("cotas", [])
    por_cidade: dict[str, dict[str, int]] = defaultdict(lambda: {"total": 0, "com": 0})
    for c in cotas:
        cid = c.get("cidade")
        if not cid or not isinstance(c.get("cota_m"), (int, float)):
            continue
        por_cidade[cid]["total"] += 1
        if isinstance(c.get("lat"), (int, float)) and isinstance(c.get("lon"), (int, float)):
            por_cidade[cid]["com"] += 1

    esperado = {cid: n["total"] for cid, n in por_cidade.items() if n["com"] == 0 and n["total"]}

    fonte = (RAIZ / COTAS_NO_MAPA_TS).read_text(encoding="utf-8")
    bloco = re.search(
        r"RUAS_SEM_COORDENADA:[^=]*=\s*\{(.*?)\}", fonte, re.S)
    if not bloco:
        erro(f"{COTAS_NO_MAPA_TS}: não achei RUAS_SEM_COORDENADA. Se o nome mudou, "
             "atualize esta guarda junto — sem ela os números voltam a envelhecer calados.")
        return
    declarado = {
        m.group(1) or m.group(2): int(m.group(3))
        for m in re.finditer(r"(?:'([^']+)'|([A-Za-z_][\w-]*))\s*:\s*(\d+)", bloco.group(1))
    }
    if declarado != esperado:
        erro(f"{COTAS_NO_MAPA_TS}: RUAS_SEM_COORDENADA diz {declarado}, mas o "
             f"cotas-ruas.json tem {esperado}. O mapa usa esses números para escolher "
             "entre 'aproxime para ver as ruas' e 'esta cidade tem N ruas levantadas que "
             "não entram no mapa' — errado, ele manda alguém procurar o que não está lá.")



def valida_referencia_das_cotas_de_rua() -> None:
    """
    Toda cota de rua DECLARA sua referência — inclusive para dizer que não sabe.

    A mesma regra que `valida_referencias` aplica ao enchentes.json, e pelo
    mesmo motivo: `null` é resposta ("a fonte não declara"), campo ausente é
    silêncio disfarçado de certeza.

    POR QUE VIROU TRAVA (06/09/2026). O leitor do site recusava cota fora da
    régua com `c.referencia !== undefined && c.referencia !== 'régua'` — ou
    seja, a cota SEM O CAMPO passava direto e era comparada com o nível ao vivo
    como se fosse régua. Ausência virava permissão.

    Eram 39 cotas. As 7 de Blumenau, de uma lista de imprensa de 2022, divergem
    de 3 a 4 metros das cotas rotuladas da MESMA RUA — 7,40 contra 11,85 na São
    Rafael. Estavam entrando na busca "minha rua" e no simulador sem que nada na
    tela dissesse de onde vinham.

    O buraco não era sobre essas 39, que hoje estão rotuladas: é sobre a próxima
    linha a entrar sem referência, num arquivo que cresce por importação.
    """
    cotas = le_json("cotas-ruas.json").get("cotas", [])
    faltando: list[str] = []
    for c in cotas:
        onde = f"{c.get('cidade')}/{c.get('rua')}"
        if "referencia" not in c:
            faltando.append(onde)
            continue
        ref = c["referencia"]
        if ref is not None and ref not in REFERENCIAS_VALIDAS:
            erro(f"cotas-ruas.json: {onde} tem referencia {ref!r}, fora do conjunto "
                 f"fechado {REFERENCIAS_VALIDAS}. Hipótese vai em 'nota', não no rótulo.")
    if faltando:
        erro(f"cotas-ruas.json: {len(faltando)} cota(s) sem o campo 'referencia' "
             f"(ex.: {', '.join(faltando[:3])}). O site só compara cota em 'régua' com o "
             "nível ao vivo; sem o campo, a cota entra na busca 'minha rua' como se fosse "
             "régua, e ninguém vê. Use 'régua', 'IBGE (régua + 0,20 m)' ou null com o "
             "motivo em 'nota' — null é resposta, campo ausente não é.")



def main() -> int:
    conhecidas = valida_estacoes()
    valida_enchentes(conhecidas)
    valida_transito(conhecidas)
    valida_monotonia_transito()
    valida_meses_pareados()
    valida_hidraulica()
    valida_cotas_ruas()
    valida_referencias()
    valida_pinos_no_tracado()
    valida_regua_das_cotas()
    valida_pico_copiado_de_outra_cidade()
    valida_cota_de_rua_nao_e_lamina()
    valida_codigo_ana()
    valida_ruas_sem_coordenada()
    valida_referencia_das_cotas_de_rua()
    valida_cobertura_da_mare()

    for a in avisos:
        print(f"aviso: {a}")
    for e in erros:
        print(f"ERRO:  {e}", file=sys.stderr)

    print(f"\n{len(erros)} erro(s), {len(avisos)} aviso(s).")
    if erros:
        print("Corrija os erros antes de commitar: o site mostra o que estiver nestes arquivos.")
        return 1
    print("Dados válidos.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
