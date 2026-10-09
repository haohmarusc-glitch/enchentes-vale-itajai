#!/usr/bin/env python3
"""
Simula, sobre a série coletada, quantas mensagens uma régua de rio com maré mandaria
pelo aviso automático, com a regra de hoje e com as alternativas da proposta da DC-11.

Não muda nada: só conta. A regra de hoje é a de `alerta_cotas.decidir` (faixa mais alta
alcançada, mensagem a cada troca de faixa, repetição só depois de 3 h e 30 cm de subida),
aplicada a cada leitura da série. As alternativas são:

* **histerese** — a faixa só baixa quando o nível desce `histerese_m` abaixo da cota dela;
* **persistência** — uma faixa nova só vale depois de `persistencia_min` minutos seguidos nela;
* **maré descontada** — a leitura menos `fator × maré prevista` (tábua da Marinha, com atraso).

O resultado é para a decisão de quem mantém o projeto, que está em
`docs/PROPOSTA-DC11-AVISOS-2026-10-08.md`. Nenhum aviso muda por este script.

Uso:
    python3 scripts/simular_avisos_mare.py --serie /caminho/tempo-real
    python3 scripts/simular_avisos_mare.py --serie /caminho/tempo-real --codigo DC-11
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from datetime import datetime, timedelta
from pathlib import Path

from alerta_cotas import FAIXAS, REPETE_H, SUBIDA_M, faixa_de
from comum import DADOS, estacoes_tempo_real

#: Episódios acima da cota de atenção separados por mais que isto contam como dois.
SEPARA_EPISODIOS_H = 18

#: Fator e atraso da maré na DC-11 (docs/ANALISE-CHEGADA-ITAJAI-2026.md, Tabela 1; medido de novo
#: em 08/10/2026 com 36 dias: correlação 0,91, fator 0,69, atraso 1 h).
FATOR_MARE = {"DC-11": (0.69, 1)}

OPCOES = {
    "A · regra de hoje": {},
    "C1 · histerese de 0,30 m": {"histerese_m": 0.30},
    "C2 · persistência de 2 h": {"persistencia_min": 120},
    "C3 · histerese 0,30 m + 2 h": {"histerese_m": 0.30, "persistencia_min": 120},
}


def leituras(pasta: Path, titulo: str) -> list[tuple[datetime, float]]:
    """As leituras desta régua em todos os `AAAA-MM.ndjson` da pasta, sem repetir horário."""
    pontos: dict[datetime, float] = {}
    for arq in sorted(pasta.glob("20[0-9][0-9]-[0-9][0-9].ndjson")):
        for linha in arq.open(encoding="utf-8"):
            try:
                r = json.loads(linha)
            except json.JSONDecodeError:
                continue
            if r.get("estacao") != titulo or r.get("nivel_m") is None or not r.get("medido_em"):
                continue
            pontos[datetime.fromisoformat(r["medido_em"][:19])] = float(r["nivel_m"])
    return sorted(pontos.items())


def faixa_com_histerese(nivel: float, cotas: dict, atual: str, histerese_m: float) -> str:
    """Faixa de `faixa_de`; para BAIXAR de `atual`, o nível tem de descer `histerese_m` abaixo da cota dela."""
    nova = faixa_de(nivel, cotas)
    if histerese_m and FAIXAS.index(nova) < FAIXAS.index(atual):
        cota_atual = cotas.get(atual)
        if isinstance(cota_atual, (int, float)) and nivel > float(cota_atual) - histerese_m:
            return atual
    return nova


def simular(pontos: list[tuple[datetime, float]], cotas: dict, histerese_m: float = 0.0,
            persistencia_min: int = 0) -> list[tuple[datetime, str, float]]:
    """Mensagens (hora, faixa, nível) que o aviso automático mandaria, leitura a leitura."""
    msgs: list[tuple[datetime, str, float]] = []
    estado: str | None = None
    ultimo: tuple[datetime, float] | None = None
    pendente: tuple[str, datetime] | None = None
    for t, v in pontos:
        faixa = faixa_com_histerese(v, cotas, estado or "normal", histerese_m)
        if persistencia_min and faixa != (estado or "normal"):
            if pendente is None or pendente[0] != faixa:
                pendente = (faixa, t)
                continue
            if (t - pendente[1]).total_seconds() / 60 < persistencia_min:
                continue
        pendente = None
        if faixa != (estado or "normal"):
            # Como em `decidir`: nunca "voltou ao normal" para quem nunca saiu dele.
            if not (faixa == "normal" and estado is None):
                msgs.append((t, faixa, v))
                ultimo = (t, v)
            estado = faixa
        elif faixa != "normal" and ultimo:
            if (t - ultimo[0]).total_seconds() >= REPETE_H * 3600 and round(v - ultimo[1], 2) >= SUBIDA_M:
                msgs.append((t, faixa, v))
                ultimo = (t, v)
        estado = faixa
    return msgs


def episodios(pontos: list[tuple[datetime, float]], cota: float) -> list[tuple[datetime, datetime, float]]:
    """(início, fim, máximo) dos trechos acima da cota, separados por SEPARA_EPISODIOS_H abaixo."""
    eps: list[list] = []
    for t, v in pontos:
        if v < cota:
            continue
        if eps and (t - eps[-1][1]).total_seconds() / 3600 <= SEPARA_EPISODIOS_H:
            eps[-1][1] = t
            eps[-1][2] = max(eps[-1][2], v)
        else:
            eps.append([t, t, v])
    return [tuple(e) for e in eps]


def mare_prevista(arquivo: Path):
    """Função t → maré astronômica menos a média de 25 h, interpolada em cosseno entre preamar e baixa-mar."""
    d = json.loads(arquivo.read_text(encoding="utf-8"))
    ext = sorted((datetime.fromisoformat(p["quando"]), float(p["altura_m"]))
                 for p in d["preamares"] + d["baixamares"])

    def altura(t: datetime) -> float | None:
        for (t0, h0), (t1, h1) in zip(ext, ext[1:]):
            if t0 <= t <= t1:
                f = (t - t0) / (t1 - t0)
                return h0 + (h1 - h0) * (1 - math.cos(math.pi * f)) / 2
        return None

    def residuo(t: datetime) -> float | None:
        a = altura(t)
        janela = [altura(t + timedelta(hours=h)) for h in range(-12, 13)]
        janela = [x for x in janela if x is not None]
        if a is None or len(janela) < 20:
            return None
        return a - sum(janela) / len(janela)

    return residuo


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--serie", type=Path, default=DADOS / "tempo-real", help="pasta com os AAAA-MM.ndjson")
    ap.add_argument("--codigo", default="DC-11")
    args = ap.parse_args(argv)

    est = next((e for e in estacoes_tempo_real() if e.get("codigo") == args.codigo), None)
    if not est:
        print(f"{args.codigo} não está no cadastro", file=sys.stderr)
        return 2
    cotas = est.get("cotas_m") or {}
    pontos = leituras(args.serie, est["titulo"])
    if not pontos:
        print(f"nenhuma leitura de {est['titulo']} em {args.serie}", file=sys.stderr)
        return 1
    dias = (pontos[-1][0] - pontos[0][0]).total_seconds() / 86400
    print(f"{est['titulo']}: {len(pontos)} leituras, {pontos[0][0]:%d/%m %H:%M} a {pontos[-1][0]:%d/%m %H:%M} ({dias:.0f} dias)")
    print(f"cotas: {cotas}\n")

    base = simular(pontos, cotas)
    resultados = {nome: simular(pontos, cotas, **kw) for nome, kw in OPCOES.items()}
    if args.codigo in FATOR_MARE:
        fator, atraso = FATOR_MARE[args.codigo]
        residuo = mare_prevista(DADOS / "mare-itajai-chm.json")
        descontada = []
        for t, v in pontos:
            r = residuo(t - timedelta(hours=atraso))
            if r is not None:
                descontada.append((t, v - fator * r))
        resultados["B2 · maré descontada"] = simular(descontada, cotas)

    print("opção | mensagens | de volta ao normal | primeiras de alerta")
    for nome, msgs in resultados.items():
        normal = sum(1 for _, f, _ in msgs if f == "normal")
        alerta = [f"{t:%d/%m %H:%M} ({v:.2f})" for t, f, v in msgs if f == "alerta"][:3]
        print(f"{nome} | {len(msgs)} | {normal} | {', '.join(alerta) or '—'}")

    cota = cotas.get("atencao")
    if isinstance(cota, (int, float)):
        print(f"\nprimeira mensagem acima do normal em cada episódio ≥ {cota:.2f} m (atraso contra a regra de hoje)")
        for ini, fim, maximo in episodios(pontos, float(cota)):
            a = next((t for t, f, _ in base if t >= ini - timedelta(minutes=1) and f != "normal"), None)
            linha = [f"{ini:%d/%m %H:%M} → {fim:%d/%m %H:%M}, máx {maximo:.2f}"]
            for nome, msgs in resultados.items():
                if nome.startswith("A "):
                    continue
                c = next((t for t, f, _ in msgs if ini - timedelta(minutes=1) <= t <= fim + timedelta(hours=1)
                          and f != "normal"), None)
                linha.append(f"{nome.split(' ·')[0]} " + (f"+{(c - a).total_seconds() / 3600:.1f} h" if a and c else "sem aviso"))
            print("  " + " · ".join(linha))
    return 0


if __name__ == "__main__":
    sys.exit(main())
