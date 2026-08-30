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

    return conhecidas


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


def main() -> int:
    conhecidas = valida_estacoes()
    valida_enchentes(conhecidas)
    valida_transito(conhecidas)

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
