"""Audita pares de picos de Blumenau/Itajaí; nunca promove relatos a calibração.

Uso: python scripts/calibrar_chegada_itajai.py [--base arquivo.json]
Somente leitura. Estatísticas são descritivas por PAR DE ESTAÇÕES e exigem
cinco eventos independentes conferidos. Não são uma previsão validada.
"""
from __future__ import annotations

import argparse
import json
import math
import statistics
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

BASE = Path(__file__).resolve().parents[1] / "data/historico-chegada-itajai.json"
MIN_EVENTOS = 5


def atraso(evento: dict) -> float | None:
    if (evento.get("status") != "verificado"
            or evento.get("natureza") != "par_de_picos_observados"
            or evento.get("serie_original_conferida") is not True
            or evento.get("efeito_mare_conferido") is not True):
        return None
    if not all(isinstance(evento.get(k), str) and evento[k].strip() for k in
               ("id", "evento", "estacao_montante", "estacao_jusante", "fonte", "url")):
        return None
    try:
        a = datetime.fromisoformat(evento["pico_montante"])
        b = datetime.fromisoformat(evento["pico_jusante"])
        if a.utcoffset() is None or b.utcoffset() is None:
            return None  # Histórico precisa de offset, inclusive no horário de verão.
        horas = (b - a).total_seconds() / 3600
        return horas if math.isfinite(horas) and 0 < horas <= 120 else None
    except (KeyError, TypeError, ValueError):
        return None


def avaliar(base: dict) -> dict:
    eventos = base.get("eventos", [])
    ids = Counter(e.get("id") for e in eventos)
    grupos = defaultdict(list)
    recusados = []
    for e in eventos:
        h = atraso(e)
        if h is None or ids[e.get("id")] != 1:
            recusados.append(e.get("id"))
            continue
        picos = (datetime.fromisoformat(e["pico_montante"]), datetime.fromisoformat(e["pico_jusante"]))
        grupos[(e["estacao_montante"], e["estacao_jusante"])].append((e["evento"], h, picos))
    saida = []
    for (montante, jusante), valores in sorted(grupos.items()):
        contagem = Counter(evento for evento, _, _ in valores)
        picos_repetidos = Counter(picos for _, _, picos in valores)
        # Duas fontes do mesmo evento não são duas cheias; ambiguidade não é média.
        horas = [h for evento, h, picos in valores if contagem[evento] == 1 and picos_repetidos[picos] == 1]
        estatisticas = None
        if len(horas) >= MIN_EVENTOS:
            estatisticas = {
                "media_h": statistics.mean(horas), "mediana_h": statistics.median(horas),
                "min_h": min(horas), "max_h": max(horas),
            }
        saida.append({"montante": montante, "jusante": jusante, "eventos_validos": len(horas),
                      "eventos_ambiguos": sum(c > 1 for c in contagem.values()),
                      "pares_de_horarios_repetidos": sum(c > 1 for c in picos_repetidos.values()),
                      "estatisticas_descritivas": estatisticas})
    return {"min_eventos_por_par": MIN_EVENTOS, "registros_nao_elegiveis": recusados,
            "pares": saida, "previsao_validada": False,
            "nota": "Estatísticas exigem revisão e teste em cheias não usadas no ajuste antes de uso preditivo."}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", type=Path, default=BASE)
    args = parser.parse_args()
    print(json.dumps(avaliar(json.loads(args.base.read_text(encoding="utf-8"))), ensure_ascii=False, indent=2))
