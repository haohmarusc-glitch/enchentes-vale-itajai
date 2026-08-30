#!/usr/bin/env python3
"""
Mede quanto cada régua oscila com a maré, para decidir por dado quais podem
disparar aviso automático.

O problema que este script resolve: as onze estações de Itajaí têm cota oficial
do Plano de Contingência da COMPDEC, mas nove ficam no estuário, onde o nível
sobe e desce com a maré duas vezes por dia. Em 30/08/2026 a DC-01 marcou
1,24 m às 17:21 — acima da sua cota de atenção, 1,16 — e 0,70 m três horas
depois, sem enchente nenhuma. Um aviso disparado ali tocaria com a maré, e
aviso que toca à toa ensina a pessoa a ignorar o que tocar na noite da cheia.

Por isso `estacoes.json` marca essas nove com `alerta_automatico: false`. A
marca foi posta por julgamento, olhando três leituras. Este script troca o
julgamento por medição, sobre a série que a coleta vem juntando.

O que ele calcula, por estação:

* **amplitude diária** — a diferença entre o maior e o menor nível de cada dia,
  e a mediana dessas diferenças. Régua de estuário tem amplitude grande todo
  dia; régua de rio só tem quando chove.
* **folga até a cota** — quanto falta, do nível típico, até a cota de atenção.
  Quando a amplitude diária é MAIOR que a folga, a régua cruza a cota sozinha.
* **travessias** — quantas vezes o nível cruzou a cota de atenção para cima na
  série inteira, e em quantos dias distintos. Muitas travessias em muitos dias
  sem enchente registrada é a assinatura da maré.

O veredito é uma SUGESTÃO com o número ao lado, não uma decisão automática:
mudar quem dispara aviso é decisão de quem mantém o projeto.

Uso:
    python3 scripts/medir_mare.py
    python3 scripts/medir_mare.py --mes 2026-09
"""

from __future__ import annotations

import argparse
import gzip
import json
import statistics
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path

from comum import DADOS, classificar_estacao, cota_de_referencia, estacao_por_titulo

SERIE = DADOS / "tempo-real"

#: Abaixo disto a série não diz nada: um dia de dados não separa maré de cheia.
MIN_DIAS = 3


def leituras_da_serie(mes: str | None) -> dict[str, list[tuple[datetime, float]]]:
    padroes = [f"{mes}.ndjson", f"{mes}.ndjson.gz"] if mes else ["*.ndjson", "*.ndjson.gz"]
    arquivos: list[Path] = []
    for padrao in padroes:
        arquivos.extend(sorted(SERIE.glob(padrao)))

    por_estacao: dict[str, list[tuple[datetime, float]]] = defaultdict(list)
    for arquivo in arquivos:
        abrir = gzip.open if arquivo.suffix == ".gz" else open
        with abrir(arquivo, "rt", encoding="utf-8") as f:
            for linha in f:
                linha = linha.strip()
                if not linha:
                    continue
                try:
                    d = json.loads(linha)
                    quando = datetime.fromisoformat(d["medido_em"])
                    nivel = float(d["nivel_m"])
                except (ValueError, KeyError, TypeError):
                    continue
                por_estacao[d.get("estacao", "?")].append((quando, nivel))
    for pontos in por_estacao.values():
        pontos.sort()
    return por_estacao


def travessias(pontos: list[tuple[datetime, float]], cota: float) -> tuple[int, int]:
    """(quantas subidas atravessaram a cota, em quantos dias distintos)."""
    n, dias = 0, set()
    for (_, antes), (quando, agora) in zip(pontos, pontos[1:]):
        if antes < cota <= agora:
            n += 1
            dias.add(quando.date())
    return n, len(dias)


def menor_cota(titulo: str, reguas_na_cidade: int) -> float | None:
    """
    A menor cota que vale para ESTA régua.

    A da própria estação quando cadastrada; senão a da cidade, mas só se a
    cidade tiver uma régua só — mesma regra do resto do projeto. Em Itajaí são
    onze com zeros diferentes, e emprestar a cota da cidade a todas mediria a
    folga contra a régua errada.
    """
    estacao = estacao_por_titulo(titulo) or {}
    proprias = [v for v in (estacao.get("cotas_m") or {}).values()
                if isinstance(v, (int, float))]
    if proprias:
        return min(proprias)
    if reguas_na_cidade > 1:
        return None
    rio, cidade = classificar_estacao(titulo)
    if not rio or not cidade:
        return None
    valor, _ = cota_de_referencia(rio, cidade)
    return valor


def medir(titulo: str, pontos: list[tuple[datetime, float]],
          reguas_na_cidade: int = 1) -> dict | None:
    if len(pontos) < 4:
        return None
    por_dia: dict[object, list[float]] = defaultdict(list)
    for quando, nivel in pontos:
        por_dia[quando.date()].append(nivel)
    amplitudes = [max(v) - min(v) for v in por_dia.values() if len(v) >= 4]
    if not amplitudes:
        return None

    estacao = estacao_por_titulo(titulo) or {}
    cota = menor_cota(titulo, reguas_na_cidade)
    niveis = [n for _, n in pontos]
    tipico = statistics.median(niveis)

    amplitude = statistics.median(amplitudes)
    folga = None if cota is None else round(cota - tipico, 2)
    cruzou, dias_cruzou = travessias(pontos, cota) if cota is not None else (0, 0)

    return {
        "estacao": titulo,
        "codigo": estacao.get("codigo"),
        "leituras": len(pontos),
        "dias": len(por_dia),
        "nivel_tipico_m": round(tipico, 2),
        "amplitude_diaria_mediana_m": round(amplitude, 2),
        "menor_cota_m": cota,
        "folga_ate_a_cota_m": folga,
        "travessias": cruzou,
        "dias_com_travessia": dias_cruzou,
        "alerta_automatico_hoje": estacao.get("alerta_automatico", True),
    }


def veredito(m: dict) -> tuple[str, str]:
    """(sugestão, porquê). Sugestão, não decisão."""
    if m["dias"] < MIN_DIAS:
        return "sem opinião", f"só {m['dias']} dia(s) de série; um dia não separa maré de cheia"
    if m["menor_cota_m"] is None:
        return "sem opinião", "estação sem cota cadastrada"
    if m["folga_ate_a_cota_m"] is not None and m["amplitude_diaria_mediana_m"] > m["folga_ate_a_cota_m"]:
        return ("NÃO disparar sozinha",
                f"oscila {m['amplitude_diaria_mediana_m']:.2f} m por dia contra "
                f"{m['folga_ate_a_cota_m']:.2f} m de folga até a cota — cruza sozinha")
    if m["dias_com_travessia"] >= max(2, m["dias"] // 3):
        return ("NÃO disparar sozinha",
                f"cruzou a cota em {m['dias_com_travessia']} de {m['dias']} dias")
    return ("pode disparar",
            f"oscila {m['amplitude_diaria_mediana_m']:.2f} m por dia com "
            f"{m['folga_ate_a_cota_m']:.2f} m de folga; "
            f"{m['travessias']} travessia(s) em {m['dias']} dias")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--mes", help="AAAA-MM; sem isso, a série inteira")
    ap.add_argument("--json", action="store_true", help="despeja as medidas em JSON")
    args = ap.parse_args()

    serie = leituras_da_serie(args.mes)
    if not serie:
        print("Nenhuma série em data/tempo-real/. Rode a coleta por alguns dias antes.",
              file=sys.stderr)
        return 1

    # Quantas réguas cada cidade tem NA SÉRIE: é o que decide se a cota da
    # cidade pode ser emprestada à estação.
    reguas: dict[tuple, int] = {}
    for titulo in serie:
        reguas[classificar_estacao(titulo)] = reguas.get(classificar_estacao(titulo), 0) + 1
    medidas = [
        m for m in (medir(t, p, reguas.get(classificar_estacao(t), 1))
                    for t, p in sorted(serie.items()))
        if m
    ]
    if args.json:
        print(json.dumps(medidas, ensure_ascii=False, indent=2))
        return 0

    print(f"{len(medidas)} estação(ões) na série.\n")
    divergem = []
    for m in medidas:
        sugestao, porque = veredito(m)
        hoje = "dispara" if m["alerta_automatico_hoje"] else "não dispara"
        marca = ""
        if sugestao == "pode disparar" and not m["alerta_automatico_hoje"]:
            marca = "   <<< hoje está travada; a medição não confirma a trava"
            divergem.append(m)
        if sugestao == "NÃO disparar sozinha" and m["alerta_automatico_hoje"]:
            marca = "   <<< hoje dispara; a medição diz que não devia"
            divergem.append(m)
        print(f"{m['codigo'] or '—':6} {m['estacao'][:44]:44}")
        print(f"       {m['leituras']:5d} leituras em {m['dias']} dia(s) · "
              f"típico {m['nivel_tipico_m']:.2f} m · oscila {m['amplitude_diaria_mediana_m']:.2f} m/dia")
        print(f"       cota {m['menor_cota_m']} · folga {m['folga_ate_a_cota_m']} · "
              f"{m['travessias']} travessia(s) em {m['dias_com_travessia']} dia(s)")
        print(f"       hoje: {hoje} · medição sugere: {sugestao} — {porque}{marca}\n")

    if divergem:
        print(f"{len(divergem)} estação(ões) em que a medição discorda do cadastro. "
              "Mudar quem dispara aviso é decisão de quem mantém o projeto, não deste script.")
    else:
        print("A medição concorda com o cadastro em todas as estações.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
