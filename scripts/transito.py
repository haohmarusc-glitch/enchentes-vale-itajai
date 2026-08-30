"""
Tempo que a cheia leva para descer de uma cidade até a outra.

Porte fiel de `web/src/logica/transito.ts`. Existem duas implementações porque
o site é TypeScript e o bot do Telegram é Python — e duas contas de vida podem
divergir em silêncio, o site dizendo uma coisa e o bot outra, sem ninguém
perceber até a noite errada.

O que impede isso é `data/transito-esperado.json`: o resultado de TODO par de
cidades, gerado a partir do `transito.ts` do site (`npm run gabarito`). Os dois
lados têm teste que o reproduz. Se qualquer um mudar de comportamento, a CI
fica vermelha.

Ao mexer aqui: mexa lá também, rode `npm run gabarito`, confira o diff e rode
os dois testes.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

#: Quanto pior, maior. Um elo fraco derruba a confiança do caminho inteiro.
_PESO = {"alta": 0, "media": 1, "baixa": 2}


class Caminho:
    __slots__ = ("horas_min", "horas_max", "direto", "trechos", "confianca", "fontes")

    def __init__(self, trechos: list[dict], direto: bool):
        self.trechos = trechos
        self.direto = direto
        self.horas_min = sum(t["horas_min"] for t in trechos)
        self.horas_max = sum(t["horas_max"] for t in trechos)
        self.confianca = pior_confianca([t["confianca"] for t in trechos])
        # dict.fromkeys preserva a ordem e tira repetido, como o Set do TS.
        self.fontes = list(dict.fromkeys(t["fonte"] for t in trechos))


def pior_confianca(cs: list[str]) -> str:
    pior = "alta"
    for c in cs:
        if _PESO.get(c, 2) > _PESO.get(pior, 0):
            pior = c
    return pior


def caminho(trechos: list[dict], rio_id: str, de: str, para: str) -> Caminho | None:
    """
    Menor cadeia de trechos de `de` até `para`, dentro do mesmo rio.

    Busca em largura: prefere o caminho com menos elos, porque cada elo soma
    incerteza. Sem caminho, devolve None — e quem chama diz "sem dado de
    trânsito", nunca um palpite.
    """
    if de == para:
        return None
    do_rio = [t for t in trechos if t["rio"] == rio_id]

    for t in do_rio:
        if t["de"] == de and t["para"] == para:
            return Caminho([t], True)

    fila: list[tuple[str, list[dict]]] = [(de, [])]
    visitadas = {de}
    while fila:
        cidade, rota = fila.pop(0)
        for t in do_rio:
            if t["de"] != cidade or t["para"] in visitadas:
                continue
            nova = rota + [t]
            if t["para"] == para:
                return Caminho(nova, False)
            visitadas.add(t["para"])
            fila.append((t["para"], nova))
    return None


def faixa_horas(c: Caminho) -> str:
    """`14–17 h`, ou `cerca de 6 h` quando a fonte traz valor único."""
    def fmt(h: float) -> str:
        return f"{h:g}".replace(".", ",")
    if c.horas_min == c.horas_max:
        return f"cerca de {fmt(c.horas_min)} h"
    return f"{fmt(c.horas_min)}–{fmt(c.horas_max)} h"


def janela_chegada(partida: datetime, c: Caminho) -> tuple[datetime, datetime]:
    """Janela de chegada a partir de um horário de pico informado."""
    return (partida + timedelta(hours=c.horas_min), partida + timedelta(hours=c.horas_max))


def como_gabarito(c: Caminho | None) -> dict[str, Any] | None:
    """A forma que `data/transito-esperado.json` guarda, para comparar."""
    if c is None:
        return None
    return {
        "horas_min": c.horas_min,
        "horas_max": c.horas_max,
        "direto": c.direto,
        "confianca": c.confianca,
        "trechos": [[t["de"], t["para"]] for t in c.trechos],
    }
