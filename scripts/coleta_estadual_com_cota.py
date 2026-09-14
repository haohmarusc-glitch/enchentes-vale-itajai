#!/usr/bin/env python3
"""Rede estadual (DCSC) que PODE pintar: estações cujas faixas municipais estão na própria escala.

REGRA DE FUNDO (a nº 1 do projeto): uma cota só pinta quando está amarrada à MESMA
régua da leitura. O nível da rede estadual sai do `coleta_nivel_sc.py` com
`usar_para_cota=False` em todas as estações, porque o zero da estação não é o zero
das cotas municipais — e um ponto de coincidência não prova nada (Brusque, 01/09:
"offset ~0" às 17 h virou 1,9 m às 23 h).

A EXCEÇÃO, e a única: quando a COMPDEC declara, por escrito, que as faixas do
município foram DEFINIDAS NA ESCALA DA ESTAÇÃO ESTADUAL. Aí não há offset a
calibrar — a régua das cotas é a estação. Foi o que Ascurra respondeu ao C18 em
11/09/2026 (`docs/resposta-ascurra-c18-2026-09-11.md`): "A DCSC-00003 está na Ponte
do Beber [...] faixas: até 8,50 monitoramento, 8,50 a 9,76 atenção, 9,76 a 10,76
alerta, acima de 10,76 emergência, estabelecidas por mim a partir de dados das
elevações anteriores [...] não existe referência de faixa estabelecida pelo estado
em cima de nossas cotas."

Cada entrada de REGUAS_COM_COTA_PROPRIA precisa de TRÊS coisas casando, e o teste
`TesteOParEstaTrancadoNoEstacoesJson` cobra: (1) a cidade em `estacoes.json` tem
`codigo_dcsc` igual ao código; (2) tem `cotas_m` com `atencao`; (3) tem
`regua_das_cotas_fonte` citando a resposta. Sem as três, a estação não entra —
melhor cinza do que colorido pelo zero errado.

A leitura sai no formato de `leituras` (o que o site lê), com `usar_para_cota: True`
e `origem: "estadual"`, e entra pelo `coleta_niveis.py` como Taió, Gaspar e Indaial.
Falha aqui NUNCA derruba a coleta: devolve lista vazia e o resto segue.

Uma chamada a mais à API por ciclo (15 min) — a mesma que o próprio site da DCSC
faz ao abrir o mapa. Respeita o User-Agent do projeto (`coleta_nivel_sc.UA`).
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

#: código DCSC -> como a leitura entra em `leituras`. Só entra aqui com a prova
#: escrita da COMPDEC de que as faixas estão na escala DESTA estação.
REGUAS_COM_COTA_PROPRIA: dict[str, dict[str, str]] = {
    "DCSC-00003": {
        "cidade": "ascurra",
        "rio": "itajai-acu",
        "estacao": "Ascurra — Ponte do Beber (DCSC-00003)",
        "fonte": ("Rede estadual (Defesa Civil de SC), estação DCSC-00003, Ponte do Beber. "
                  "Faixas definidas pela COMPDEC de Ascurra NESTA escala — resposta ao C18 em "
                  "11/09/2026 (docs/resposta-ascurra-c18-2026-09-11.md)."),
    },
}


def montar(leituras_estaduais: list[dict]) -> list[dict]:
    """Das leituras brutas do `coleta_nivel_sc.converter`, as que podem pintar, no formato do site."""
    saida: list[dict] = []
    for l in leituras_estaduais:
        cfg = REGUAS_COM_COTA_PROPRIA.get(l.get("codigo") or "")
        if not cfg:
            continue
        nivel = l.get("nivel_bruto_m")
        quando = l.get("medido_em")
        if nivel is None or not quando:
            continue  # sem número ou sem carimbo não é leitura; o site não pinta o que não sabe
        saida.append({
            "estacao": cfg["estacao"],
            "cidade": cfg["cidade"],
            "rio": cfg["rio"],
            "nivel_m": float(nivel),
            "medido_em": quando,           # já em hora de Brasília, sem fuso (coleta_nivel_sc.hora_local)
            "fonte": cfg["fonte"],
            "codigo_dcsc": l["codigo"],
            "origem": "estadual",
            "datum": "regua_das_cotas",    # a régua das cotas É esta estação, por declaração da COMPDEC
            "usar_para_cota": True,
        })
    return saida


def coletar(buscar=None, converter=None) -> list[dict]:
    """Busca a rede estadual e devolve só o que pode pintar. Nunca levanta exceção."""
    try:
        if buscar is None or converter is None:
            from coleta_nivel_sc import buscar as _buscar, converter as _converter
            buscar = buscar or _buscar
            converter = converter or _converter
        brutas, _sem, _susp, _nao_mede = converter(buscar(), so_cadeia=False)
        return montar(brutas)
    except Exception as e:  # noqa: BLE001 — uma fonte a mais nunca derruba a coleta
        print(f"aviso: rede estadual com cota própria não coletada ({e}).", file=sys.stderr)
        return []


if __name__ == "__main__":
    for l in coletar():
        print(f"{l['nivel_m']:6.2f} m  {l['medido_em']}  {l['estacao']}  [{l['cidade']} ({l['rio']})]")
