#!/usr/bin/env python3
"""Valida os JSONs de `data/`. Sai com código 1 se algo estiver errado.

Este é o portão de qualidade do projeto: o site mostra o que estiver nestes
arquivos, e um número errado aqui vira número errado na tela de alguém que
está decidindo se sai de casa. Rode antes de todo commit que mexa em `data/`.

    python3 scripts/validar_dados.py
"""

from __future__ import annotations

import re
import sys
from collections import defaultdict
from datetime import date

from comum import le_json

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


def main() -> int:
    conhecidas = valida_estacoes()
    valida_enchentes(conhecidas)
    valida_transito(conhecidas)
    valida_monotonia_transito()
    valida_meses_pareados()
    valida_hidraulica()
    valida_cotas_ruas()
    valida_referencias()

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
