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


def valida_estacoes() -> set[tuple[str, str]]:
    estacoes = le_json("estacoes.json")
    conhecidas: set[tuple[str, str]] = set()
    no_eixo: set[tuple[str, str]] = set()

    for rio_id, rio in estacoes["rios"].items():
        ordens: list[int] = []
        ids: set[str] = set()
        for cidade in rio["cidades"]:
            onde = f"estacoes.json / {rio_id} / {cidade.get('id', '???')}"
            for campo in ("id", "nome", "ordem", "codigo_ana", "verificado", "cotas_m"):
                if campo not in cidade:
                    erro(f"{onde}: falta o campo '{campo}'")
            if cidade["id"] in ids:
                erro(f"{onde}: id repetido dentro do mesmo rio")
            ids.add(cidade["id"])
            ordens.append(cidade["ordem"])
            conhecidas.add((rio_id, cidade["id"]))
            no_eixo.add((rio_id, cidade["id"]))

            codigo = cidade.get("codigo_ana")
            if codigo is not None and not re.fullmatch(r"\d{8}", str(codigo)):
                erro(f"{onde}: codigo_ana '{codigo}' não tem os 8 dígitos do HidroWeb")
            if codigo is not None and not cidade.get("verificado"):
                aviso(f"{onde}: codigo_ana {codigo} ainda não conferido na fonte oficial")

            for chave, valor in (cidade.get("cotas_m") or {}).items():
                if not isinstance(valor, (int, float)) or not 0 < valor < PICO_MAXIMO_M:
                    erro(f"{onde}: cota '{chave}' = {valor} fora de faixa plausível")

        esperado = list(range(1, len(ordens) + 1))
        if sorted(ordens) != esperado:
            erro(f"estacoes.json / {rio_id}: 'ordem' deveria ser {esperado}, veio {sorted(ordens)}")

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
        anterior = primeira_rua.get(cidade)
        primeira_rua[cidade] = cota if anterior is None else min(anterior, cota)

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
    ordem: dict[tuple[str, str], int] = {}
    estacoes = le_json("estacoes.json")
    for rio_id, rio in estacoes["rios"].items():
        for cidade in rio["cidades"]:
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

        de = ordem.get((t["rio"], t["de"]))
        para = ordem.get((t["rio"], t["para"]))
        if de is None:
            aviso(f"{onde}: '{t['de']}' não está em estacoes.json; trecho fica invisível na tela")
        if para is None:
            aviso(f"{onde}: '{t['para']}' não está em estacoes.json; trecho fica invisível na tela")
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


def main() -> int:
    conhecidas = valida_estacoes()
    valida_enchentes(conhecidas)
    valida_transito(conhecidas)
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
