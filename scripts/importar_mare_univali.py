#!/usr/bin/env python3
"""Importa a tábua de maré de uma planilha do Laboratório de Oceanografia Física – UNIVALI (Itajaí/SC) (previsão harmônica).

POR QUE ESTE SCRIPT EXISTE, SEPARADO DO `coleta_mares.py`
-----------------------------------------------------------
`coleta_mares.py` busca a tábua no endpoint da Defesa Civil de Itajaí — a fonte
"oficial" corrente do projeto. Esse endpoint ficou dias vazio (ver o aviso em
`data/mare-itajai.json._meta`), e o site fica sem o quadro de maré enquanto
durar: `PainelMare` mostra "não temos a tábua deste dia" e o mar do mapa fica
cinza, "maré: sem dado".

O Laboratório de Oceanografia Física – UNIVALI (Itajaí/SC) — a própria fonte que `logica/mare.ts` cita como quem ampliou
o marégrafo de Itajaí — mantém uma planilha de previsão harmônica (maré
astronômica) para o porto. Este script lê essa planilha e preenche a tábua
enquanto o endpoint da Defesa Civil não volta. A PRÓXIMA execução bem-sucedida
de `coleta_mares.py` SUBSTITUI este arquivo inteiro pela tábua oficial — isso é
o comportamento certo, não um bug: a fonte primária sempre tem prioridade
quando volta a publicar.

O QUE NÃO ENTRA: A ALTURA EM METROS
------------------------------------
A planilha traz a maré em **datum IBGE**. O site mostra a altura da tábua junto
de cada preamar em `PainelMare.tsx` ("— X m na tábua"), num contexto que supõe
o mesmo referencial que a Defesa Civil/Marinha (DHN) publicam — e não há como
este script confirmar que os dois batem (é exatamente o problema do datum de
Blumenau, que já custou uma REGRA BLOQUEANTE neste projeto). Por isso o
registro só traz o INSTANTE de cada preamar/baixamar (`quando`), nunca
`altura_m`: a hora do pico de maré não depende de datum, o metro depende.

FORMATO DE ENTRADA
-------------------
Planilha com blocos de 3 colunas repetidos horizontalmente (Data | Hora |
Nível), um bloco por faixa de dias do mês. Dentro de um bloco, `Data` só vem
preenchida na primeira linha de cada dia — as linhas seguintes do mesmo dia
repetem a data "para baixo" (mesma convenção de várias planilhas de maré
publicadas por portos e institutos). Cada evento é uma preamar (máximo local)
ou baixa-mar (mínimo local) da curva astronômica; a planilha já vem só com os
extremos, não com a série contínua — daí a classificação por vizinhança bastar.

Uso:
    python3 scripts/importar_mare_univali.py --arquivo previsao.xlsx --verificar
    python3 scripts/importar_mare_univali.py --arquivo previsao.xlsx
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import date, datetime, time, timezone
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
DESTINO = RAIZ / "data" / "mare-itajai.json"

#: Índices de coluna (0-based) de cada bloco (Data, Hora, Nível). A planilha
#: real tem 3 blocos lado a lado, cada um com uma coluna vazia de separação.
BLOCOS = [(0, 1, 2), (4, 5, 6), (8, 9, 10)]


def extrair_eventos(linhas: list[tuple]) -> list[tuple[datetime, float]]:
    """
    (instante, nível) de cada evento da planilha, em ordem cronológica.

    `linhas` é a lista de tuplas de célula (uma por linha da planilha, já sem o
    cabeçalho). Dentro de cada bloco, a data só vem na primeira linha do dia —
    as linhas seguintes carregam a data anterior (o "forward-fill" abaixo).
    """
    por_bloco: dict[int, list[tuple[date, time, float]]] = {b[0]: [] for b in BLOCOS}
    for linha in linhas:
        for (ci_data, ci_hora, ci_val) in BLOCOS:
            hora = linha[ci_hora] if ci_hora < len(linha) else None
            val = linha[ci_val] if ci_val < len(linha) else None
            if hora is None or val is None:
                continue
            bruta = linha[ci_data] if ci_data < len(linha) else None
            data_da_linha = bruta.date() if isinstance(bruta, datetime) else bruta
            por_bloco[ci_data].append((data_da_linha, hora, float(val)))

    eventos: list[tuple[datetime, float]] = []
    for itens in por_bloco.values():
        dia_atual: date | None = None
        for data_da_linha, hora, val in itens:
            if data_da_linha is not None:
                dia_atual = data_da_linha
            if dia_atual is None:
                continue  # linha antes de qualquer data conhecida: não dá pra datar
            eventos.append((datetime.combine(dia_atual, hora), val))

    eventos.sort(key=lambda e: e[0])
    return eventos


def classificar_extremos(
    eventos: list[tuple[datetime, float]],
) -> tuple[list[tuple[datetime, float]], list[tuple[datetime, float]]]:
    """
    Separa os eventos (já extremos da curva) em preamares e baixa-mares.

    Cada evento é preamar se não for menor que os vizinhos imediatos, e
    baixa-mar se não for maior — comparação simples, porque a entrada já veio
    só com picos e vales (não é a curva contínua). Um evento que empata com os
    dois vizinhos (plô raríssimo numa maré astronômica) não é classificado —
    melhor faltar um ponto do que adivinhar se é pico ou vale.
    """
    preamares: list[tuple[datetime, float]] = []
    baixamares: list[tuple[datetime, float]] = []
    for i, (quando, val) in enumerate(eventos):
        esquerda = eventos[i - 1][1] if i > 0 else None
        direita = eventos[i + 1][1] if i < len(eventos) - 1 else None
        eh_alto = (esquerda is None or val >= esquerda) and (direita is None or val >= direita)
        eh_baixo = (esquerda is None or val <= esquerda) and (direita is None or val <= direita)
        if eh_alto and not eh_baixo:
            preamares.append((quando, val))
        elif eh_baixo and not eh_alto:
            baixamares.append((quando, val))
        # eh_alto and eh_baixo (plô) ou nenhum dos dois: descartado, de propósito.
    return preamares, baixamares


def formatar(pontos: list[tuple[datetime, float]]) -> list[dict]:
    """Só o instante — nunca a altura (ver o cabeçalho do arquivo: datum IBGE)."""
    return [{"quando": q.strftime("%Y-%m-%dT%H:%M")} for q, _ in pontos]


def montar(preamares: list[tuple[datetime, float]], baixamares: list[tuple[datetime, float]]) -> dict:
    return {
        "_meta": {
            "descricao": (
                "Tábua de maré do porto de Itajaí. O site cruza estas preamares com a janela "
                "de chegada da cheia: maré alta trava o escoamento do rio."
            ),
            "fuso": "Horário local (America/Sao_Paulo), sem indicação de fuso — igual ao "
                    "que a fonte publica e ao que o site espera.",
            "fonte": "Planilha de previsão de maré do Laboratório de Oceanografia Física – UNIVALI (Itajaí/SC) (Márcio Piazera), "
                     "importada por scripts/importar_mare_univali.py",
            "fonte_oficial": "Tábuas de maré da Marinha do Brasil (DHN) — porto de Itajaí",
            "metodo": (
                "Preamares e baixa-mares são os máximos e mínimos locais que a própria "
                "planilha já traz — não recalculados aqui."
            ),
            "aviso": (
                "INTERINO: o endpoint da Defesa Civil (scripts/coleta_mares.py) está vazio há "
                "dias; esta tábua veio do Laboratório de Oceanografia Física – UNIVALI (Itajaí/SC) enquanto isso. A ALTURA (metros) foi "
                "OMITIDA de propósito — a planilha usa datum IBGE, e nada aqui garante que bate "
                "com o datum que a Defesa Civil/DHN publicam (mesmo problema do datum de "
                "Blumenau, que já é REGRA BLOQUEANTE neste projeto). Só o HORÁRIO de cada "
                "preamar/baixa-mar entrou, que não depende de datum. A próxima coleta bem-"
                "sucedida de coleta_mares.py substitui este arquivo inteiro pela tábua oficial — "
                "isso é esperado, não um bug."
            ),
            # Curtos, para a TELA (não o prosa acima, que é para quem lê o JSON). A tela nunca
            # deve cravar "Defesa Civil" quando o dado é de outra fonte — foi exatamente esse
            # erro que este par de campos corrige em PainelMare.tsx.
            "fonte_curta": "Laboratório de Oceanografia Física – UNIVALI (Itajaí/SC) — previsão harmônica",
            "aviso_interino": (
                "Tábua interina: o endpoint da Defesa Civil está sem dado. Horários de maré do "
                "Laboratório de Oceanografia Física – UNIVALI (Itajaí/SC), sem a altura (datum não confirmado contra a Defesa Civil)."
            ),
        },
        "porto": "Itajaí",
        "coletado_em": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "pontos_astronomicos": len(preamares) + len(baixamares),
        "pontos_observados": 0,
        "preamares": formatar(preamares),
        "baixamares": formatar(baixamares),
    }


def ler_planilha(caminho: Path) -> list[tuple]:
    try:
        import openpyxl
    except ImportError:
        print(
            "Para ler .xlsx é preciso o openpyxl: pip install -r scripts/requirements.txt",
            file=sys.stderr,
        )
        raise SystemExit(2)
    wb = openpyxl.load_workbook(caminho, data_only=True)
    ws = wb.active
    return [row for row in ws.iter_rows(min_row=2, values_only=True)]


def main() -> int:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument("--arquivo", required=True, help="planilha .xlsx do Laboratório de Oceanografia Física – UNIVALI (Itajaí/SC)")
    ap.add_argument("--verificar", action="store_true", help="mostra o que veio e não grava")
    args = ap.parse_args()

    caminho = Path(args.arquivo)
    if not caminho.exists():
        print(f"ERRO: {caminho} não existe", file=sys.stderr)
        return 1

    linhas = ler_planilha(caminho)
    eventos = extrair_eventos(linhas)
    if not eventos:
        print("ERRO: nenhum evento encontrado na planilha (formato inesperado?)", file=sys.stderr)
        return 1

    preamares, baixamares = classificar_extremos(eventos)
    dados = montar(preamares, baixamares)

    print(f"eventos lidos:  {len(eventos)}")
    print(f"preamares:      {len(preamares)}")
    print(f"baixa-mares:    {len(baixamares)}")
    print(f"período:        {eventos[0][0].date()} a {eventos[-1][0].date()}")
    nao_classificados = len(eventos) - len(preamares) - len(baixamares)
    if nao_classificados:
        print(f"AVISO: {nao_classificados} evento(s) não classificado(s) (empate com os vizinhos)")

    if args.verificar:
        print("\n--verificar: nada foi gravado.")
        return 0

    temporario = DESTINO.with_suffix(".json.tmp")
    temporario.write_text(json.dumps(dados, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporario.replace(DESTINO)
    print(f"\ngravado em {DESTINO.relative_to(RAIZ)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
