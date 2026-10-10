#!/usr/bin/env python3
"""
Auditoria das travas e da histerese das réguas de Itajaí sobre a série coletada (10/10/2026).

Pedido do Jefferson (10/10/2026):
  1. verificar o motivo das travas da DC-03 e da DC-06 antes de removê-las;
  2. validar a histerese da DC-05 (0,10 m) e da DC-11 (0,30 m) com o histórico, preservando os avisos de novas
     subidas;
  3. conferir se 1,80 m (Plano v17) e 1,70 m (portal) da DC-08 são da mesma régua e do mesmo zero;
  4. conferir a cota e a régua da DC-07, para habilitar a Murta.

Só lê e conta, sem mudar aviso nem cadastro. A reprodução do aviso é o mesmo laço de `alerta_cotas.decidir`,
leitura a leitura: faixa mais alta alcançada, `faixa_com_histerese`, repetição só depois de 3 h e 30 cm de subida.
O relatório está em `docs/AUDITORIA-TRAVAS-ITAJAI-2026-10-10.md`.

Uso:
    git show origin/arquivo-series:tempo-real/2026-09.ndjson > /tmp/serie/2026-09.ndjson   # e os outros meses
    python3 scripts/auditar_avisos_itajai.py --serie /tmp/serie
"""

from __future__ import annotations

import argparse
import json
import statistics
from collections import defaultdict
from datetime import date, datetime, timedelta
from pathlib import Path

from alerta_cotas import FAIXAS, REPETE_H, SUBIDA_M, faixa_com_histerese, faixa_de, liberar_por_tempo
from comum import DADOS, estacoes_tempo_real

#: Episódios acima da cota de atenção separados por mais que isto contam como dois (o mesmo de
#: `simular_avisos_mare.py` e de `extrair_picos.py`).
SEPARA_EPISODIOS_H = 18

#: Dia "parado": ao menos 48 leituras e menos que isto entre o máximo e o mínimo.
PARADO_M = 0.03

#: Dia em que o coletor trocou a página antiga da Defesa Civil de Itajaí pelo portal novo.
TROCA_DE_PORTAL = date(2026, 9, 19)

Serie = list[tuple[datetime, float]]
Mensagem = tuple[datetime, float, str, str]  # (quando, nível, faixa de antes, faixa nova)


def ler_series(pasta: Path, glob: str = "20[0-9][0-9]-[0-9][0-9].ndjson", chave: str = "nivel_m") -> dict[str, list]:
    """{"DC-03": [(t, valor), ...]} pelo código no começo do título (o título mudou com o portal novo)."""
    pontos: dict[str, dict[datetime, object]] = defaultdict(dict)
    for arq in sorted(pasta.glob(glob)):
        for linha in arq.open(encoding="utf-8"):
            try:
                r = json.loads(linha)
            except json.JSONDecodeError:
                continue
            titulo = r.get("estacao") or ""
            if not titulo.startswith("DC-") or r.get(chave) is None or not r.get("medido_em"):
                continue
            pontos[titulo[:5]][datetime.fromisoformat(r["medido_em"][:19])] = r[chave]
    return {c: sorted(d.items()) for c, d in pontos.items()}


def reproduzir(serie: Serie, cotas: dict, histerese_m: float = 0.0, libera_apos_h: float = 0.0) -> list[Mensagem]:
    """As mensagens que `alerta_cotas.decidir` mandaria para esta régua, leitura a leitura (com a liberação
    por tempo de 10/10/2026, `liberar_por_tempo`, quando `libera_apos_h` > 0)."""
    estado: dict = {}
    msgs: list[Mensagem] = []
    for t, nivel in serie:
        antes = estado.get("faixa", "normal")
        crua = faixa_de(nivel, cotas)
        faixa = faixa_com_histerese(float(nivel), cotas, crua, antes, histerese_m)
        faixa, segurada = liberar_por_tempo(faixa, crua, estado.get("segurada_desde"), t, libera_apos_h)
        manda = False
        if faixa != antes:
            manda = not (faixa == "normal" and not estado)
        elif faixa != "normal" and estado.get("avisado_em"):
            horas = (t - estado["avisado_em"]).total_seconds() / 3600
            manda = horas >= REPETE_H and round(nivel - estado["nivel_m"], 2) >= SUBIDA_M
        if manda:
            msgs.append((t, nivel, antes, faixa))
            estado = {"faixa": faixa, "nivel_m": nivel, "avisado_em": t}
        else:
            estado = {**estado, "faixa": faixa, "segurada_desde": segurada}
    return msgs


def config_do_cadastro(estacao: dict) -> tuple[float, float]:
    h = estacao.get("aviso_histerese_m")
    libera = estacao.get("aviso_libera_apos_h")
    return (float(h) if isinstance(h, (int, float)) else 0.0, float(libera) if isinstance(libera, (int, float)) else 0.0)


def auditar_cadastro(series: dict[str, Serie], cad: dict[str, dict]) -> list[dict]:
    """
    Cada régua que avisa, com a configuração do cadastro (cotas, histerese, liberação por tempo): mensagens,
    episódios e o primeiro aviso de cada um, a maior rajada em 24 h e se alguma subida de faixa ficou sem aviso.
    É a prova pedida antes de ativar (10/10/2026), a rodar também com a série que inclui 06–07/10.
    """
    saida = []
    for cod in sorted(series):
        e = cad.get(cod) or {}
        if e.get("alerta_automatico") is False or not e.get("cotas_m"):
            continue
        cotas, s = e["cotas_m"], series[cod]
        h, libera = config_do_cadastro(e)
        msgs = reproduzir(s, cotas, h, libera)
        crus = reproduzir(s, cotas)
        tmsgs = [m[0] for m in msgs]
        eps = []
        for ini, _fim, maximo in episodios(s, cotas["atencao"]):
            p = primeiro_aviso(msgs, ini - timedelta(minutes=1))
            eps.append((ini, maximo, None if p is None else (p[0] - ini).total_seconds() / 3600))
        rajada = max((sum(1 for u in tmsgs if t <= u < t + timedelta(hours=24)) for t in tmsgs), default=0)
        faixas_cruas = {(m[0], m[3]) for m in crus if sobe(m)}
        faixas_com = {(m[0], m[3]) for m in msgs if sobe(m)}
        perdidas = []
        for t, faixa in sorted(faixas_cruas - faixas_com):
            vigente = next((m[3] for m in reversed(msgs) if m[0] < t), "normal")
            if FAIXAS.index(faixa) > FAIXAS.index(vigente):
                perdidas.append((t, faixa))
        saida.append({"codigo": cod, "histerese": h, "libera": libera, "mensagens": len(msgs), "sem_regras": len(crus),
                      "episodios": eps, "rajada_24h": rajada, "faixa_mais_alta_perdida": perdidas,
                      "maximo": max(v for _, v in s), "faixas": sorted({m[3] for m in msgs}, key=FAIXAS.index)})
    return saida


def sobe(m: Mensagem) -> bool:
    return FAIXAS.index(m[3]) > FAIXAS.index(m[2])


def episodios(serie: Serie, cota: float, separa_h: float = SEPARA_EPISODIOS_H) -> list[tuple[datetime, datetime, float]]:
    """Trechos com nível >= cota, unidos quando o intervalo abaixo dela é menor que `separa_h`."""
    eps: list[list] = []
    for t, v in serie:
        if v < cota:
            continue
        if eps and (t - eps[-1][1]).total_seconds() <= separa_h * 3600:
            eps[-1][1], eps[-1][2] = t, max(eps[-1][2], v)
        else:
            eps.append([t, t, v])
    return [tuple(e) for e in eps]


def primeiro_aviso(msgs: list[Mensagem], desde: datetime) -> Mensagem | None:
    return next((m for m in msgs if m[0] >= desde and FAIXAS.index(m[3]) >= FAIXAS.index("atencao")), None)


def horas_abaixo_antes(serie: Serie, t: datetime, cota: float) -> tuple[float, float]:
    """Quanto tempo o nível ficou abaixo de `cota` antes de voltar a ela em `t`, e o mínimo nesse trecho."""
    i = next(k for k, (tt, _) in enumerate(serie) if tt == t)
    j = i - 1
    while j >= 0 and serie[j][1] < cota:
        j -= 1
    trecho = serie[j + 1:i]
    if not trecho:
        return 0.0, serie[i][1]
    return (t - trecho[0][0]).total_seconds() / 3600, min(v for _, v in trecho)


def comparar_histerese(serie: Serie, cotas: dict, histerese_m: float) -> dict:
    """O que a histerese tira e o que ela preserva, com os critérios do pedido de 10/10/2026."""
    sem = reproduzir(serie, cotas, 0.0)
    com = reproduzir(serie, cotas, histerese_m)
    instantes_com = {m[0] for m in com}
    eps = episodios(serie, cotas["atencao"])
    inicio = []
    for ini, _fim, maximo in eps:
        p = primeiro_aviso(com, ini - timedelta(minutes=1))
        inicio.append({"inicio": ini, "maximo": maximo, "atraso_h": None if p is None else (p[0] - ini).total_seconds() / 3600})
    primeira_entrada = {}
    for faixa in FAIXAS[2:]:
        a = next((m[0] for m in sem if sobe(m) and m[3] == faixa), None)
        b = next((m[0] for m in com if sobe(m) and m[3] == faixa), None)
        if a:
            primeira_entrada[faixa] = (a, b)
    sumidas = [m for m in sem if m[0] not in instantes_com and (sobe(m) or m[2] == m[3])]
    faixa_mais_alta_perdida = []
    reentradas = []
    for m in sumidas:
        vigente = next((c[3] for c in reversed(com) if c[0] < m[0]), "normal")
        if FAIXAS.index(m[3]) > FAIXAS.index(vigente):
            faixa_mais_alta_perdida.append(m)
        if sobe(m):
            horas, minimo = horas_abaixo_antes(serie, m[0], cotas[m[3]])
            reentradas.append({"quando": m[0], "faixa": m[3], "horas_abaixo": horas, "minimo": minimo,
                               "desceu_alem_da_histerese": minimo <= cotas[m[3]] - histerese_m})
    return {
        "sem": len(sem), "com": len(com),
        "subidas_sem": sum(sobe(m) for m in sem), "subidas_com": sum(sobe(m) for m in com),
        "repeticoes_sem": [m for m in sem if m[2] == m[3]], "repeticoes_com": [m for m in com if m[2] == m[3]],
        "episodios": inicio, "primeira_entrada": primeira_entrada,
        "faixa_mais_alta_perdida": faixa_mais_alta_perdida, "reentradas": reentradas,
    }


def com_liberacao_por_tempo(serie: Serie, cotas: dict, histerese_m: float, horas: float) -> list[Mensagem]:
    """Alternativa: a histerese segura a faixa, mas a solta se o nível ficar `horas` abaixo da cota dela."""
    estado: dict = {}
    msgs: list[Mensagem] = []
    abaixo_desde = None
    for t, nivel in serie:
        antes = estado.get("faixa", "normal")
        crua = faixa_de(nivel, cotas)
        faixa = faixa_com_histerese(float(nivel), cotas, crua, antes, histerese_m)
        if faixa != crua:
            abaixo_desde = abaixo_desde or t
            if (t - abaixo_desde).total_seconds() / 3600 >= horas:
                faixa = crua
        else:
            abaixo_desde = None
        manda = False
        if faixa != antes:
            manda = not (faixa == "normal" and not estado)
        elif faixa != "normal" and estado.get("avisado_em"):
            manda = ((t - estado["avisado_em"]).total_seconds() / 3600 >= REPETE_H
                     and round(nivel - estado["nivel_m"], 2) >= SUBIDA_M)
        if manda:
            msgs.append((t, nivel, antes, faixa))
            estado = {"faixa": faixa, "nivel_m": nivel, "avisado_em": t}
            abaixo_desde = None
        else:
            estado = {**estado, "faixa": faixa}
    return msgs


def por_dia(serie: Serie) -> dict[date, list[float]]:
    dias: dict[date, list[float]] = defaultdict(list)
    for t, v in serie:
        dias[t.date()].append(v)
    return {d: v for d, v in dias.items() if len(v) >= 48}


def mare_da_regua(serie: Serie, cota: float) -> dict:
    """A oscilação diária e a distância entre o máximo diário típico e a cota de atenção."""
    dias = por_dia(serie)
    amp = sorted(max(v) - min(v) for v in dias.values())
    maximos = [max(v) for v in dias.values()]
    return {"dias": len(dias), "amplitude_mediana": statistics.median(amp), "amplitude_max": amp[-1],
            "maximo_diario_mediano": statistics.median(maximos),
            "folga_do_maximo_diario": cota - statistics.median(maximos), "maximo": max(v for _, v in serie)}


def maior_variacao_3h(serie: Serie, dia: date) -> tuple[float, float] | None:
    pts = [(t, v) for t, v in serie if t.date() == dia]
    if len(pts) < 2:
        return None
    var = max(abs(b[1] - a[1]) for a in pts for b in pts if 0 < (b[0] - a[0]).total_seconds() <= 3 * 3600)
    return var, max(v for _, v in pts)


def media_25h(serie: Serie, t: datetime) -> float:
    vals = [v for tt, v in serie if abs((tt - t).total_seconds()) <= 12.5 * 3600]
    return sum(vals) / len(vals)


def travessias(serie: Serie, cota: float) -> list[tuple[datetime, float, float]]:
    """Cada passagem da cota para cima, com a média de 25 h no instante (abaixo da cota = empurrada pela maré)."""
    return [(serie[i][0], serie[i][1], media_25h(serie, serie[i][0]))
            for i in range(1, len(serie)) if serie[i - 1][1] < cota <= serie[i][1]]


def base_em_dia_parado(serie: Serie, troca: date = TROCA_DE_PORTAL) -> tuple[list[float], list[float]]:
    """A mediana dos dias parados antes e depois da troca de portal: um salto aqui seria troca de zero."""
    antes, depois = [], []
    for d, v in sorted(por_dia(serie).items()):
        if max(v) - min(v) < PARADO_M:
            (antes if d < troca else depois).append(round(statistics.median(v), 2))
    return antes, depois


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    ap.add_argument("--serie", type=Path, default=DADOS / "tempo-real")
    args = ap.parse_args(argv)
    series = ler_series(args.serie)
    cad = {e["codigo"]: e for e in estacoes_tempo_real() if str(e.get("codigo", "")).startswith("DC-")}
    if not series:
        print(f"nenhuma leitura DC em {args.serie}")
        return 1
    ini = min(s[0][0] for s in series.values())
    fim = max(s[-1][0] for s in series.values())
    print(f"série de {ini:%d/%m/%Y %H:%M} a {fim:%d/%m/%Y %H:%M}\n")

    for cod in ("DC-03", "DC-06"):
        s, cotas = series[cod], cad[cod]["cotas_m"]
        m = mare_da_regua(s, cotas["atencao"])
        v30 = maior_variacao_3h(s, date(2026, 8, 30))
        print(f"## {cod} — trava ({cotas})")
        print(f"  amplitude diária mediana {m['amplitude_mediana']:.2f} m (máx {m['amplitude_max']:.2f}); máximo diário "
              f"mediano {m['maximo_diario_mediano']:.2f}, {m['folga_do_maximo_diario']:.2f} m abaixo da atenção; máximo {m['maximo']:.2f}")
        if v30:
            print(f"  30/08: maior variação em 3 h {v30[0]:.2f} m, máximo do dia {v30[1]:.2f}")
        for t, v, base in travessias(s, cotas["atencao"]):
            print(f"  passou da atenção {t:%d/%m %H:%M} ({v:.2f}); média 25 h {base:.2f}")
        for h in (0.0, 0.10, 0.30):
            print(f"  mensagens com histerese {h:.2f}: {len(reproduzir(s, cotas, h))}")
        print()

    for cod in ("DC-05", "DC-11", "DC-03"):
        s, cotas = series[cod], cad[cod]["cotas_m"]
        h = cad[cod].get("aviso_histerese_m") or 0.30
        r = comparar_histerese(s, cotas, h)
        print(f"## {cod} — histerese {h:.2f} m: {r['sem']} → {r['com']} mensagens")
        print(f"  subidas de faixa {r['subidas_sem']} → {r['subidas_com']}; repetições por +30 cm "
              f"{len(r['repeticoes_sem'])} → {len(r['repeticoes_com'])}")
        for faixa, (a, b) in r["primeira_entrada"].items():
            print(f"  primeira entrada em {faixa}: {a:%d/%m %H:%M} → {b:%d/%m %H:%M}" if b else f"  {faixa}: PERDIDA")
        for e in r["episodios"]:
            atraso = "SEM AVISO" if e["atraso_h"] is None else f"atraso {e['atraso_h']:.1f} h"
            print(f"  episódio {e['inicio']:%d/%m %H:%M} (máx {e['maximo']:.2f}): {atraso}")
        print(f"  subida para faixa mais alta que deixou de sair: {len(r['faixa_mais_alta_perdida'])}")
        if r["reentradas"]:
            hs = [x["horas_abaixo"] for x in r["reentradas"]]
            longe = [x for x in r["reentradas"] if x["desceu_alem_da_histerese"]]
            pior = max(r["reentradas"], key=lambda x: x["horas_abaixo"])
            print(f"  reentradas na mesma faixa que deixam de sair: {len(hs)}; tempo abaixo da cota antes: mediana "
                  f"{statistics.median(hs):.1f} h, > 6 h: {sum(x > 6 for x in hs)}, > 12 h: {sum(x > 12 for x in hs)}; "
                  f"maior {pior['horas_abaixo']:.1f} h ({pior['quando']:%d/%m %H:%M}, mínimo {pior['minimo']:.2f}); "
                  f"desceram além da histerese: {len(longe)}")
        if cod == "DC-11":
            for horas in (3, 6, 12):
                print(f"  alternativa: soltar a faixa após {horas} h abaixo da cota → "
                      f"{len(com_liberacao_por_tempo(s, cotas, h, horas))} mensagens")
        print()

    print("## Configuração do cadastro (o que os avisos fariam com estas regras)")
    for r in auditar_cadastro(series, cad):
        regra = f"histerese {r['histerese']:.2f} m" + (f" + liberação após {r['libera']:.0f} h" if r["libera"] else "")
        print(f"  {r['codigo']} ({regra}): {r['mensagens']} mensagens (sem regras {r['sem_regras']}); máximo "
              f"{r['maximo']:.2f} m; faixas avisadas {r['faixas']}; maior rajada em 24 h {r['rajada_24h']}; "
              f"subida de faixa sem aviso {len(r['faixa_mais_alta_perdida'])}")
        for ini, mx, atraso in r["episodios"]:
            print(f"    episódio {ini:%d/%m %H:%M} (máx {mx:.2f}): " + ("SEM AVISO" if atraso is None else f"atraso {atraso:.1f} h"))
    print()

    for cod in ("DC-07", "DC-08"):
        s, cotas = series[cod], cad[cod]["cotas_m"]
        antes, depois = base_em_dia_parado(s)
        print(f"## {cod} — régua e zero ({cotas})")
        print(f"  base em dia parado antes da troca de portal {antes}; depois {depois}")
        print(f"  máximo {max(v for _, v in s):.2f}; episódios acima da atenção: "
              f"{[f'{a:%d/%m}' for a, _b, _m in episodios(s, cotas['atencao'])]}")
        for h in (0.0, 0.30):
            print(f"  mensagens com histerese {h:.2f}: {len(reproduzir(s, cotas, h))}")
        print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
