#!/usr/bin/env python3
"""
Nível de Taió e o ESTADO DAS COMPORTAS da Barragem Oeste.

Por que este coletor é diferente dos outros: ele traz o único dado de OPERAÇÃO
DE BARRAGEM que a bacia publica. O relatório da JICA (2011, seção 4.2.2) aponta
exatamente essa ausência como a causa de a previsão de Rio do Sul não funcionar:

    "Defesa Civil in Rio do Sul city tries to conduct flood forecasting;
     however, the present forecasting is not appropriate for practical use. One
     of the reasons is that DEINFRA, the operator of the Oeste dam and Sul
     dams... has not recorded and informed the outflow discharges from the dams
     to the downstream rivers."

A API de Taió não dá vazão de saída — ninguém dá. Mas dá **quantas comportas
estão abertas**, que é o proxy operacional mais próximo, e o que separa os dois
regimes da Barragem Oeste: RETENDO (amortece a chuva de montante) e VERTENDO (a
água passa direto). Correlação calibrada num regime subestima o outro. Sem esse
campo, o site mostra o nível de Rio do Sul sem dizer se a barragem acima está
segurando ou soltando — e são duas situações diferentes com o mesmo número.

A JICA também explica por que a Oeste enche: bastam ~80 mm de chuva sobre a
bacia dela para encher o reservatório (Tabela 3.2.4), metade do que a Norte
precisa. Ela verteu em 2001 e 2010.

A ARMADILHA DAS DUAS RÉGUAS — o que este arquivo existe para não deixar acontecer
O mesmo JSON traz `nivelCentro` (~5 m, a régua da CIDADE) e `montante` (~17 m, o
reservatório da BARRAGEM). Ler o segundo como nível da cidade pintaria
emergência todo santo dia: a cota de emergência de Taió é 9,00 m. E a régua de
plausibilidade do projeto NÃO pega esse erro — 17,2 m está dentro da faixa
0–25 m que `nivel_plausivel` aceita. A separação tem de ser estrutural: o nível
da cidade sai de um campo, o da barragem de outro, e o da barragem nunca vira
leitura de cidade. Há teste travando isso.

FUSO — diferente do coletor da Asthon
A Asthon publica em UTC e o `coleta_asthon.py` converte na entrada. Aqui NÃO se
converte: `dataUltimaAtualizacao` já vem no horário de Brasília, que é o mesmo
contrato do `medido_em` (ver CLAUDE.md). Converter "para garantir" jogaria a
idade três horas fora — e foi assim que uma fonte de resgate custou uma sessão.

O QUE A API NÃO DÁ
`cotasAlagamento` e `cotaEmergencia` vêm SEMPRE null. As faixas de Taió (5 / 7 /
8 / 9 m) estão no cadastro estático, vindas do Plano de Contingência da COMPDEC.
Não esperar cota desta API.

Uso:
    python3 scripts/coleta_taio.py            # imprime o que coletaria
    python3 scripts/coleta_taio.py --gravar   # grava data/tempo-real/ultimo_taio.json
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime

from comum import DADOS, USER_AGENT, nivel_plausivel

BASE = "https://api-scr.uniparking.com.br/v1/defesa-civil-taio/dados"
URL_CARDS = f"{BASE}/cards?v=1"
URL_HISTORICO = f"{BASE}/historico?v=1"

SAIDA = "tempo-real/ultimo_taio.json"

#: A régua da CIDADE. Só este campo vira nível de cidade — ver a armadilha no
#: cabeçalho.
CAMPO_NIVEL_CIDADE = "nivelCentro"
#: A régua da BARRAGEM. Nunca vira nível de cidade.
CAMPO_NIVEL_BARRAGEM = "montante"

#: A Barragem Oeste tem 7 condutos com comporta (JICA, Tabela 3.2.4) — bate com
#: o "N de 7" que a API publica. O total vem do texto, não daqui: se a fonte
#: mudar, é a fonte que manda.
RE_COMPORTAS = re.compile(r"(\d+)\s*de\s*(\d+)", re.I)


def numero(texto) -> float | None:
    """`"5.25"` -> 5.25. Vazio, `"–"` e null viram None — a API usa os três."""
    if isinstance(texto, (int, float)) and not isinstance(texto, bool):
        return float(texto)
    if not isinstance(texto, str):
        return None
    t = texto.strip().replace(",", ".")
    if not t or t in {"-", "–", "—"}:
        return None
    try:
        return float(t)
    except ValueError:
        return None


def comportas(texto) -> dict | None:
    """
    `"7 de 7"` -> {abertas: 7, total: 7, todas_abertas: True}.

    O texto é o dado; não se infere total. `"0 de 7"` é informação boa (barragem
    retendo), então zero NÃO é ausência aqui — diferente de nível.
    """
    if not isinstance(texto, str):
        return None
    m = RE_COMPORTAS.search(texto)
    if not m:
        return None
    abertas, total = int(m.group(1)), int(m.group(2))
    if total <= 0 or abertas > total:
        return None  # "8 de 7" é erro da fonte, não estado de barragem
    return {
        "abertas": abertas,
        "total": total,
        "todas_abertas": abertas == total,
        # O que muda a leitura do rio a jusante: qualquer comporta aberta já é
        # água passando. "Retendo" é só com todas fechadas.
        "regime": "retendo" if abertas == 0 else "vertendo",
    }


def quando(texto) -> str | None:
    """
    `"03/09/2026 20:41:58"` -> `"2026-09-03T20:41:58"`.

    Sem conversão de fuso: já é horário de Brasília, que é o contrato de
    `medido_em`. Ver o cabeçalho.
    """
    if not isinstance(texto, str):
        return None
    try:
        return datetime.strptime(texto.strip(), "%d/%m/%Y %H:%M:%S").strftime(
            "%Y-%m-%dT%H:%M:%S")
    except ValueError:
        return None


def parse(cards: dict) -> dict:
    """
    O JSON de `cards` virado no formato do projeto.

    Devolve sempre as três partes, mesmo vazias: quem consome não precisa
    adivinhar se a chave existe.
    """
    if not isinstance(cards, dict):
        return {"leituras": [], "barragem": {}, "chuva_mm": {}}

    medido = quando(cards.get("dataUltimaAtualizacao"))
    nivel = numero(cards.get(CAMPO_NIVEL_CIDADE))

    leituras = []
    # Sem carimbo não há idade, e sem idade o número não serve para decidir nada.
    if nivel is not None and medido and nivel_plausivel(nivel):
        leituras.append({
            "estacao": "Taió — Rio Itajaí do Oeste, Centro",
            "rio": "itajai-acu",
            "cidade": "taio",
            "nivel_m": round(nivel, 2),
            "medido_em": medido,
            # As cotas de Taió (5/7/8/9) vêm do Plano de Contingência, no
            # cadastro. Esta régua é a que elas descrevem, então a leitura PODE
            # virar faixa — ao contrário do nível bruto da rede estadual.
            "usar_para_cota": True,
        })

    barragem = {
        "nome": "Barragem Oeste (Taió)",
        # Nível do RESERVATÓRIO. Fica fora de `leituras` de propósito: não é
        # nível de rio de cidade nenhuma, e passaria na régua de plausibilidade.
        "montante_m": numero(cards.get(CAMPO_NIVEL_BARRAGEM)),
        "jusante_m": numero(cards.get("jusante")),
        "comportas": comportas(cards.get("comportasAbertas")),
        "extravasor": (cards.get("aberturaExtravasor") or "").strip() or None,
        "medido_em": medido,
    }

    chuva = {}
    for campo, nome in (("chuva1Hora", "h1"), ("chuva12Horas", "h12"),
                        ("chuva24Horas", "h24"), ("chuva48Horas", "h48")):
        v = numero(cards.get(campo))
        if v is not None:
            chuva[nome] = v

    return {"leituras": leituras, "barragem": barragem, "chuva_mm": chuva}


def parse_historico(pontos) -> list[dict]:
    """Série horária: nível do Centro e comportas, para ver o regime mudar."""
    saida = []
    for p in pontos or []:
        if not isinstance(p, dict):
            continue
        medido = quando(p.get("dataUltimaAtualizacao"))
        nivel = numero(p.get("nivel"))
        if not medido or nivel is None:
            continue
        abertas = numero(p.get("comportaAberta"))
        saida.append({
            "medido_em": medido,
            "nivel_m": round(nivel, 2),
            "montante_m": numero(p.get("montante")),
            "comportas_abertas": int(abertas) if abertas is not None else None,
        })
    return saida


def baixar_json(url: str) -> object:
    import requests

    r = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=20)
    r.raise_for_status()
    return r.json()


def coletar() -> dict:
    dados = parse(baixar_json(URL_CARDS))
    try:
        dados["historico"] = parse_historico(baixar_json(URL_HISTORICO))
    except Exception as e:  # o histórico é extra; a falha dele não perde o card
        print(f"aviso: histórico de Taió não veio ({e})", file=sys.stderr)
        dados["historico"] = []
    return dados


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--gravar", action="store_true", help=f"grava data/{SAIDA}")
    ap.add_argument("--de-arquivo", help="lê um JSON de cards salvo (para teste)")
    args = ap.parse_args()

    try:
        if args.de_arquivo:
            with open(args.de_arquivo, encoding="utf-8") as f:
                dados = parse(json.load(f))
            dados["historico"] = []
        else:
            dados = coletar()
    except Exception as e:
        print(f"ERRO ao coletar Taió: {e}", file=sys.stderr)
        return 1

    for l in dados["leituras"]:
        print(f"{l['nivel_m']:6.2f} m  {l['medido_em']}  {l['estacao']}")
    if not dados["leituras"]:
        print("sem nível de cidade nesta coleta (campo vazio ou sem carimbo).",
              file=sys.stderr)

    b = dados["barragem"]
    c = b.get("comportas")
    if c:
        print(f"\n{b['nome']}: {c['abertas']} de {c['total']} comportas abertas "
              f"— {c['regime'].upper()}")
    else:
        print(f"\n{b['nome']}: estado das comportas não veio")
    if b.get("montante_m") is not None:
        print(f"  montante (reservatório): {b['montante_m']:.2f} m "
              "— NÃO é o nível da cidade")
    if dados["chuva_mm"]:
        print("  chuva: " + " · ".join(f"{k} {v:g} mm" for k, v in dados["chuva_mm"].items()))

    if args.gravar:
        from comum import grava_json
        grava_json(SAIDA, {
            "fonte": URL_CARDS,
            "coletado_em": datetime.now().astimezone().isoformat(),
            **dados,
        })
        print(f"\ngravado em data/{SAIDA}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
