#!/usr/bin/env python3
"""
Maré MEDIDA na foz, em Itajaí: marégrafo MRG01, Cabeçudas Iate Clube, no portal da Defesa Civil de Itajaí.

Decisão do Jefferson (23/11/2026): "Ligar um coletor e mostrar essa maré medida em /itajai, no lugar do CIRAM ou
ao lado; registrar a altura da tábua da UNIVALI no zero da DHN, com o portal como fonte; mostrar a diferença entre
o observado e o previsto." Levantamento em `docs/MAREGRAFO-ITAJAI-2026-11-23.md`.

A FONTE
-------
`https://monitoramento.defesacivil.itajai.sc.gov.br/monitoramento/maregrafo` — o mesmo host que o
`coleta_itajai_portal.py` já lê; `robots.txt` sem proibição (conferido em 23/11/2026). A página é Inertia: os dados
vêm no `data-page` do `<div id="app">`, em `props.maregrafo`. Não há endpoint de API para a maré.

* `leituras`: 10 em 10 min, 24 h, `datahora` em UTC com `Z`. Cada uma traz `nivel_bruto` (distância do sensor até a
  água, NÃO é nível), `altitude_ortometrica` (2,838 m), `nivel_ibge`, `nivel_reducao` (0,4455 m) e `nivel_dhn`.
* `previsoes`: 5 em 5 min, 3 dias, `datahora` com `-03:00`, só `nivel_dhn`. Os horários batem com a tábua da UNIVALI
  (±5 min) e as alturas com a da Marinha (±5 cm), que é referida ao nível de redução da DHN.
* Rótulo da página: "MRG01 - Iate Clube - Maré Medida e Maré Prevista (DHN)"; rodapé "Fonte: Parceria Defesa Civil
  Itajai / Univali".

AS REGRAS (maré medida, `CLAUDE.md`)
------------------------------------
1. **Número só com horário, estação, unidade e referência vertical identificados.** A referência é a que a fonte
   escreve: o zero da DHN (`nivel_dhn`, título "(DHN)"). `REFERENCIA_VERTICAL` traz a descrição e a fonte.
2. **As contas da fonte têm de fechar.** `nivel_ibge = altitude_ortometrica − nivel_bruto` e
   `nivel_dhn = nivel_ibge + nivel_reducao`, com folga de `TOLERANCIA_CONTA_M`. Leitura que não fecha não vira
   número: um sensor trocado ou um campo renomeado aparece aqui, não na tela.
3. **Leitura antiga nunca como atual.** Mais de `FRESCA_MIN` (60 min) ou do futuro: sem número.
4. **A diferença** é "diferença entre nível observado e maré astronômica prevista", da MESMA estação, no MESMO
   horário, na MESMA referência: a previsão que o próprio portal publica para o MRG01 no ponto de 5 min mais
   próximo (até `PAR_PREVISAO_MIN`). Nunca a tábua da Marinha nem a planilha anual. Não se atribui só a vento e
   pressão: o marégrafo fica na foz do Itajaí-Açu, e em cheia a diferença tem água do rio dentro.

A ALTURA DA TÁBUA DA UNIVALI NO ZERO DA DHN
-------------------------------------------
A planilha anual da UNIVALI (`data/mare-itajai.json`) não declara referência, e NÃO se converte: em 22–25/11/2026 a
diferença entre a previsão do portal (DHN) e a planilha (`sl_fit`) variou de −0,221 a −0,246 m nos 864 pontos — não
é um deslocamento fixo, e nenhuma fonte escreve a conta. A altura em DHN que tem fonte é a da previsão que o
portal publica (48 h para a frente): ela sai em `previsao.extremos`, com preamares e baixa-mares tiradas da curva
como no `importar_mare_univali.py` (mesmo filtro de ondulação de estofo). A tábua anual continua só com horário.

Uso:
    python3 scripts/coleta_maregrafo_itajai.py               # imprime o resumo
    python3 scripts/coleta_maregrafo_itajai.py --publicar    # grava data/tempo-real/ultimo_maregrafo_itajai.json
    python3 scripts/coleta_maregrafo_itajai.py --arquivo <pagina.html>   # sem rede
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Callable
from zoneinfo import ZoneInfo

sys.path.insert(0, str(Path(__file__).resolve().parent))

from coleta_itajai_portal import carga  # noqa: E402
from importar_mare_univali import ONDULACAO_M, extremos_da_serie, filtrar_ondulacoes  # noqa: E402

URL = "https://monitoramento.defesacivil.itajai.sc.gov.br/monitoramento/maregrafo"
ARQUIVO_PUBLICAVEL = "tempo-real/ultimo_maregrafo_itajai.json"
FUSO_BRASILIA = ZoneInfo("America/Sao_Paulo")

ESTACAO_ID = "MRG01"
ESTACAO = {
    "id": "itajai-cabecudas",
    "nome": "Cabeçudas Iate Clube (MRG01), na foz do Itajaí-Açu",
    "endpoint": "/monitoramento/maregrafo",
    "km_da_foz": 0,
}

#: Cadência de 10 min: uma hora sem leitura nova é marégrafo parado.
FRESCA_MIN = 60
#: Folga das contas entre as referências (a fonte publica com 3–4 casas; fechou com 0,0000 m em 23/11/2026).
TOLERANCIA_CONTA_M = 0.002
#: Previsão de 5 em 5 min: o par da leitura é o ponto previsto a até isto dela.
PAR_PREVISAO_MIN = 3
#: Nível no zero da DHN fora disto não é maré em Itajaí (em 24 h de 22–23/11/2026: 0,31 a 1,51 m).
MIN_M, MAX_M = -1.5, 4.0
#: Quantas preamares/baixa-mares previstas vão para o site.
N_EXTREMOS = 4

#: Referência vertical do `nivel_dhn`, escrita pela fonte. Decisão do Jefferson, 23/11/2026.
REFERENCIA_VERTICAL = {
    "descricao": "zero da DHN (nível de redução)",
    "fonte": ("painel “MRG01 - Iate Clube - Maré Medida e Maré Prevista (DHN)” do portal da Defesa Civil de Itajaí, "
              "campo nivel_dhn, conferido em 23/11/2026"),
}

HORARIO = ("As leituras vêm em UTC com 'Z' e as previsões com '-03:00'; aqui `medido_em` e os extremos são "
           "horário de Brasília sem fuso, como o resto do projeto.")
ASTRONOMICA_FONTE = ("a previsão que o próprio portal publica para o MRG01 (Parceria Defesa Civil Itajaí / UNIVALI), "
                     "no mesmo horário e no zero da DHN")


class Falha(RuntimeError):
    """A página não trouxe o marégrafo esperado."""


def instante(texto: Any) -> datetime | None:
    """Carimbo ISO COM fuso -> datetime ciente. Sem fuso não se adivinha."""
    if not isinstance(texto, str) or not texto:
        return None
    try:
        t = datetime.fromisoformat(texto.replace("Z", "+00:00"))
    except ValueError:
        return None
    return t if t.tzinfo else None


def brasilia(t: datetime) -> str:
    """Datetime ciente -> ISO de Brasília sem fuso, em segundos."""
    return t.astimezone(FUSO_BRASILIA).replace(tzinfo=None).isoformat(timespec="seconds")


def _num(v: Any) -> float | None:
    return float(v) if isinstance(v, (int, float)) and not isinstance(v, bool) else None


def leitura_coerente(l: dict) -> bool:
    """As duas contas da fonte fecham e o nível no zero da DHN é plausível."""
    bruto, orto, ibge, red, dhn = (_num(l.get(k)) for k in
                                   ("nivel_bruto", "altitude_ortometrica", "nivel_ibge", "nivel_reducao", "nivel_dhn"))
    if None in (bruto, orto, ibge, red, dhn):
        return False
    return (abs((orto - bruto) - ibge) <= TOLERANCIA_CONTA_M
            and abs((ibge + red) - dhn) <= TOLERANCIA_CONTA_M
            and MIN_M <= dhn <= MAX_M)


def ler_maregrafo(pagina: str) -> dict:
    """`props.maregrafo` da página, conferido: é o MRG01 e traz as duas listas."""
    dados = carga(pagina)
    m = (dados.get("props") or {}).get("maregrafo")
    if not isinstance(m, dict):
        raise Falha("a página não trouxe props.maregrafo")
    if m.get("id") != ESTACAO_ID:
        raise Falha(f"marégrafo {m.get('id')!r}, esperado {ESTACAO_ID}")
    if not isinstance(m.get("leituras"), list) or not isinstance(m.get("previsoes"), list):
        raise Falha("leituras ou previsões ausentes")
    return m


def leituras_validas(m: dict) -> list[tuple[datetime, float]]:
    """(instante, nível DHN) das leituras coerentes, em ordem. As incoerentes saem caladas: viram ausência."""
    saida = []
    for l in m.get("leituras") or []:
        if not isinstance(l, dict):
            continue
        t = instante(l.get("datahora"))
        if t is None or not leitura_coerente(l):
            continue
        saida.append((t, round(float(l["nivel_dhn"]), 3)))
    return sorted(saida)


def previsoes_validas(m: dict) -> list[tuple[datetime, float]]:
    saida = []
    for p in m.get("previsoes") or []:
        if not isinstance(p, dict):
            continue
        t, v = instante(p.get("datahora")), _num(p.get("nivel_dhn"))
        if t is None or v is None or not (MIN_M <= v <= MAX_M):
            continue
        saida.append((t, v))
    return sorted(saida)


def previsto_em(t: datetime, previsoes: list[tuple[datetime, float]]) -> float | None:
    """O nível previsto no ponto mais próximo de `t`, se estiver a até `PAR_PREVISAO_MIN`."""
    if not previsoes:
        return None
    q, v = min(previsoes, key=lambda p: abs(p[0] - t))
    return round(v, 3) if abs(q - t) <= timedelta(minutes=PAR_PREVISAO_MIN) else None


def proximos_extremos(previsoes: list[tuple[datetime, float]], agora: datetime, n: int = N_EXTREMOS) -> list[dict]:
    """As próximas `n` preamares/baixa-mares da previsão do portal, com a altura no zero da DHN."""
    serie = [(brasilia_dt(t), v) for t, v in previsoes]
    ext, _ = filtrar_ondulacoes(extremos_da_serie(serie), ONDULACAO_M)
    limite = brasilia_dt(agora)
    return [{"tipo": "preamar" if tipo == "P" else "baixamar",
             "quando": q.isoformat(timespec="minutes"),
             "altura_m": round(v, 2)}
            for tipo, q, v in ext if q >= limite][:n]


def brasilia_dt(t: datetime) -> datetime:
    return t.astimezone(FUSO_BRASILIA).replace(tzinfo=None)


def resumo_publicavel(m: dict, agora: datetime, gerado_em_utc: str) -> dict:
    """O arquivo que o site lê, no mesmo formato (versão 1) do `ultimo_mare_medida.json` do CIRAM.

    `agora` é ciente de fuso. Número só com medição recente e coerente; a diferença só com o par previsto da mesma
    estação no mesmo horário.
    """
    leituras = leituras_validas(m)
    previsoes = previsoes_validas(m)
    ultima = leituras[-1] if leituras else None
    idade = round((agora - ultima[0]).total_seconds() / 60, 1) if ultima else None
    if ultima is None:
        situacao = "sem_medicao"
    elif idade is None or idade < -15 or idade > FRESCA_MIN:
        situacao = "sem_medicao_recente"
    else:
        situacao = "medindo"

    medicao: dict | None = None
    if ultima is not None:
        medicao = {"medido_em": brasilia(ultima[0])}
        if situacao == "medindo":
            astr = previsto_em(ultima[0], previsoes)
            medicao["observada_m"] = ultima[1]
            medicao["astronomica_m"] = astr
            medicao["diferenca_observado_astronomica_m"] = (
                round(ultima[1] - astr, 3) if astr is not None else None)

    return {
        "versao": 1,
        "gerado_em": gerado_em_utc,
        "fonte": "Defesa Civil de Itajaí / UNIVALI — marégrafo de Cabeçudas",
        "fonte_url": URL,
        "estacao": ESTACAO,
        "horario": HORARIO,
        "unidade": "m",
        "unidade_na_fonte": "metro (campos nivel_* da página)",
        "referencia_vertical": {"status": "confirmada", **REFERENCIA_VERTICAL},
        "situacao": situacao,
        "frescor_max_min": FRESCA_MIN,
        "idade_min_na_coleta": idade,
        "leituras_coerentes": len(leituras),
        "leituras_na_fonte": len(m.get("leituras") or []),
        "ultima_medicao": medicao,
        "astronomica_fonte": ASTRONOMICA_FONTE,
        "previsao": {
            "fonte": "previsão publicada no mesmo painel (Parceria Defesa Civil Itajaí / UNIVALI)",
            "referencia": REFERENCIA_VERTICAL["descricao"],
            "extremos": proximos_extremos(previsoes, agora),
        },
        "aviso": ("Nível do mar na foz do Itajaí-Açu, no zero da DHN: não é régua de rio e não se compara com cota "
                  "de rio. A diferença para a maré prevista não tem uma causa só: pode vir de vento, pressão, da "
                  "água do rio e de outros efeitos."),
    }


def baixar_pagina() -> str:
    from comum import baixar, espera_turno
    espera_turno()
    return baixar(URL)


def publicar(agora: datetime | None = None, baixador: Callable[[], str] = baixar_pagina) -> int:
    """`--publicar`: uma consulta, um arquivo pequeno. Falha APAGA o anterior: um de outra coleta não passa por atual."""
    from comum import DADOS, grava_json
    destino = DADOS / ARQUIVO_PUBLICAVEL
    agora = agora or datetime.now(timezone.utc)
    gerado = datetime.now(timezone.utc).isoformat(timespec="seconds")
    try:
        m = ler_maregrafo(baixador())
    except Exception as e:  # noqa: BLE001 — a maré nunca segura a publicação do nível
        destino.unlink(missing_ok=True)
        print(f"aviso: marégrafo de Itajaí indisponível ({e}); nada publicado", file=sys.stderr)
        return 1
    saida = resumo_publicavel(m, agora, gerado)
    grava_json(ARQUIVO_PUBLICAVEL, saida)
    u = saida["ultima_medicao"] or {}
    print(f"marégrafo de Itajaí: {saida['situacao']}, {saida['leituras_coerentes']}/{saida['leituras_na_fonte']} "
          f"leituras coerentes, última {u.get('medido_em')} {u.get('observada_m')} m (DHN), "
          f"diferença {u.get('diferenca_observado_astronomica_m')} m -> data/{ARQUIVO_PUBLICAVEL}")
    return 0


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Coleta o marégrafo de Itajaí (MRG01) do portal da Defesa Civil.")
    p.add_argument("--publicar", action="store_true", help="grava o arquivo pequeno que o site lê")
    p.add_argument("--arquivo", help="página HTML já baixada, para conferir sem rede")
    a = p.parse_args(argv)
    if a.publicar:
        return publicar()
    pagina = Path(a.arquivo).read_text(encoding="utf-8") if a.arquivo else baixar_pagina()
    saida = resumo_publicavel(ler_maregrafo(pagina), datetime.now(timezone.utc),
                              datetime.now(timezone.utc).isoformat(timespec="seconds"))
    print(json.dumps(saida, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
