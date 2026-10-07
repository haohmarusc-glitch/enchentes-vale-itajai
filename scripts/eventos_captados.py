#!/usr/bin/env python3
"""Resume as cheias que a PRÓPRIA COLETA do site já captou, para o chat responder sobre elas.

Por que existe (pedido do Jefferson, 07/10/2026): o morador pergunta "qual foi a última cheia
em Blumenau?", "como foi a cheia de setembro?", "quantas vezes o rio passou da cota de alerta
desde que o site acompanha?". A resposta está na série de 15 em 15 min que o coletor grava
(`data/tempo-real/*.ndjson`, copiada semanalmente para o branch `arquivo-series`), mas essa
série não vai para o site: é grande e fica na VPS. Este script destila dela um arquivo pequeno,
`data/eventos-captados.json`, com os EPISÓDIOS acima da cota de referência de cada régua.

O que ele é e o que não é:
  - É um RESUMO DA CAPTURA: "a maior leitura que o site captou foi X às HH:MM". Não é pico
    conferido nem registro oficial. A série tem lacunas (coleta parada, fonte fora do ar), e o
    arquivo guarda a maior lacuna de cada episódio para o chat dizer isso.
  - NÃO escreve em `enchentes.json`. Quem propõe registro para lá é `extrair_picos.py`, com
    uma pessoa conferindo; aqui só se anota se o episódio JÁ tem registro lá (mesma cidade, data
    até um dia de diferença), para o chat dizer "conferido e registrado".
  - Reaproveita as regras de `extrair_picos.py`: régua por `comum.regua_de` (primária e resgate
    são UMA régua), cota da própria estação ou da cidade com uma régua só, 18 h sem cheia
    separam episódios, mínimo de 2 leituras, e o relógio defasado do repasse de Blumenau
    (3 h atrás do real, E12): o VALOR vale, o HORÁRIO vem do AlertaBlu quando houver.
  - Horários em horário de Brasília, sem fuso, como a série (`CLAUDE.md`, "Fuso dos carimbos").

Uso:
    python3 scripts/eventos_captados.py                 # imprime o resumo, não grava
    python3 scripts/eventos_captados.py --gravar        # grava data/eventos-captados.json
    python3 scripts/eventos_captados.py --serie /caminho/tempo-real --gravar
"""

from __future__ import annotations

import argparse
import sys
from datetime import datetime, timezone
from pathlib import Path

import extrair_picos as ep
from comum import estacao_por_titulo, grava_json, le_json

SAIDA = "eventos-captados.json"

#: As chaves de cota que pintam faixa, da mais branda à mais grave — a mesma escada do site
#: (`web/src/logica/cotasOperacionais.ts`).
ORDEM_COTAS = ("monitoramento", "atencao", "alerta", "inundacao", "emergencia")


def _iso(d: datetime) -> str:
    return d.strftime("%Y-%m-%dT%H:%M:%S")


def cotas_da_cidade(estacoes: dict, rio: str, cidade: str) -> dict[str, float]:
    for c in estacoes["rios"].get(rio, {}).get("cidades", []):
        if c["id"] == cidade:
            return {k: float(v) for k, v in c.get("cotas_m", {}).items()
                    if k in ORDEM_COTAS and isinstance(v, (int, float))}
    return {}


def cotas_da_estacao(estacoes: dict, titulo: str) -> dict[str, float]:
    e = estacao_por_titulo(titulo)
    return {k: float(v) for k, v in (e or {}).get("cotas_m", {}).items()
            if k in ORDEM_COTAS and isinstance(v, (int, float))}


def faixa_alcancada(cidade: str, nivel: float, cotas: dict[str, float]) -> str | None:
    """A cota mais alta que o nível alcançou, na escada da própria régua; Gaspar pela legenda."""
    if cidade == "gaspar":
        # Legenda da estação 21: "maior que" (não >=); 5 m exatos não estão definidos.
        return "emergencia" if nivel > 7 else "atencao" if nivel > 5 else None
    alcancada = None
    for chave in ORDEM_COTAS:
        valor = cotas.get(chave)
        if valor is not None and nivel >= valor:
            alcancada = chave
    return alcancada


def maior_lacuna_min(leituras: list[ep.Leitura]) -> int:
    if len(leituras) < 2:
        return 0
    return int(max((b.quando - a.quando).total_seconds() for a, b in zip(leituras, leituras[1:])) // 60)


def registro_em_enchentes(enchentes: list[dict], rio: str, cidade: str, quando: datetime) -> dict | None:
    """O registro de enchentes.json do mesmo evento (mesma cidade, até 1 dia de diferença), se houver."""
    for e in enchentes:
        if e.get("cidade") != cidade or e.get("rio") not in (rio, None):
            continue
        try:
            data = datetime.fromisoformat(e["data"])
        except (KeyError, ValueError):
            continue
        if abs((data.date() - quando.date()).days) <= 1:
            return e
    return None


def resumir(por_estacao: dict[str, dict], estacoes: dict, enchentes: list[dict]) -> dict:
    for grupo in por_estacao.values():
        atual = estacao_por_titulo(grupo["leituras"][0].estacao) if grupo["leituras"] else None
        if atual and atual.get("cidade") and atual.get("rio"):
            grupo["cidade"], grupo["rio"] = atual["cidade"], atual["rio"]
    # Quantas publicações da MESMA cidade coexistem no tempo com esta. Itajaí tem onze ao mesmo tempo
    # (réguas distintas, cada uma com as suas cotas). Rio do Sul e Brusque trocaram de fonte no meio do
    # caminho (Estação MKS → Ponte Dom Tito Buss; repasse → DCSC-00019): uma publicação de cada vez, e cada
    # uma recebe a cota da cidade no SEU período — nunca se juntam numa série só, porque o zero pode diferir.
    def periodo(g: dict) -> tuple[datetime, datetime]:
        return g["leituras"][0].quando, g["leituras"][-1].quando

    def coexistem(regua: str, grupo: dict) -> int:
        de, ate = periodo(grupo)
        n = 1
        for outra, g in por_estacao.items():
            if outra == regua or g["cidade"] != grupo["cidade"] or not g["leituras"]:
                continue
            de2, ate2 = periodo(g)
            if de2 <= ate and de <= ate2:
                n += 1
        return n

    publicacoes_por_cidade: dict[str, int] = {}
    for grupo in por_estacao.values():
        publicacoes_por_cidade[grupo["cidade"]] = publicacoes_por_cidade.get(grupo["cidade"], 0) + 1

    cobertura: list[dict] = []
    episodios: list[dict] = []
    for regua, grupo in sorted(por_estacao.items()):
        rio, cidade, leituras = grupo["rio"], grupo["cidade"], grupo["leituras"]
        if not leituras:
            continue
        quantas = coexistem(regua, grupo)
        varias = quantas > 1
        limiar, nome_cota = ep.limiar_da_estacao(regua, rio, cidade, quantas)
        cadastro = estacao_por_titulo(regua) or {}
        cotas = cotas_da_estacao(estacoes, regua) or cotas_da_cidade(estacoes, rio, cidade)
        # Régua de estuário (Itajaí): a maré cruza a cota sem enchente, então o site mostra o número e não a
        # cor — e aqui não há episódio, porque cada maré alta viraria "cheia".
        estuario = cadastro.get("alerta_automatico") is False
        sem_faixa = (
            cadastro.get("motivo_sem_alerta") or "régua de estuário: a maré cruza a cota sem enchente"
            if estuario
            else "em Ascurra a faixa é o enquadramento C18 da Defesa Civil de SC, não as cotas do cadastro"
            if cidade == "ascurra"
            else None
        )
        maximo = ep.Evento(leituras)
        cobertura.append({
            "cidade": cidade,
            "rio": rio,
            "regua": regua,
            "no_cadastro": bool(cadastro),
            "varias_ao_mesmo_tempo": varias,
            "publicacoes": sorted({l.estacao for l in leituras}),
            "de": _iso(leituras[0].quando),
            "ate": _iso(leituras[-1].quando),
            "leituras": len(leituras),
            "cota_referencia": ({"chave": nome_cota, "valor_m": limiar} if limiar is not None else None),
            "sem_faixa": sem_faixa,
            "maior_leitura": {
                "nivel_m": round(maximo.pico_m, 2),
                "quando": _iso(maximo.quando),
                "horario_de": maximo.horario_de,
                "relogio_defasado": maximo.relogio_defasado,
                "faixa": None if sem_faixa else faixa_alcancada(cidade, maximo.pico_m, cotas),
            },
        })
        if limiar is None or estuario:
            continue
        for ev in ep.separar_eventos(leituras, limiar):
            reg = registro_em_enchentes(enchentes, rio, cidade, ev.quando)
            episodios.append({
                "id": f"{ev.quando.date().isoformat()}-{cidade}" + (f"-{regua.split(' ')[0].lower()}" if publicacoes_por_cidade[cidade] > 1 else ""),
                "rio": rio,
                "cidade": cidade,
                "regua": regua,
                "no_cadastro": bool(cadastro),
                "inicio": _iso(ev.inicio),
                "fim": _iso(ev.fim),
                "maior_leitura_m": round(ev.pico_m, 2),
                "quando": _iso(ev.quando),
                "horario_de": ev.horario_de,
                "relogio_defasado": ev.relogio_defasado,
                "cota_referencia": {"chave": nome_cota, "valor_m": limiar},
                "faixa_alcancada": None if sem_faixa else faixa_alcancada(cidade, ev.pico_m, cotas),
                "leituras": len(ev.leituras),
                "maior_lacuna_min": maior_lacuna_min(ev.leituras),
                "leituras_suspeitas": len(ev.suspeitos),
                "registro_em_enchentes": (
                    {"data": reg.get("data"), "hora": reg.get("hora"), "pico_m": reg.get("pico_m"),
                     "referencia": reg.get("referencia"), "confianca": reg.get("confianca")}
                    if reg else None
                ),
            })
    episodios.sort(key=lambda e: (e["inicio"], e["cidade"]))
    return {
        "_meta": {
            "o_que_e": (
                "Resumo das cheias que a coleta do site captou, por régua: episódios acima da cota de "
                "referência, com a MAIOR LEITURA CAPTADA e a hora dela. Não é pico conferido nem registro "
                "oficial; a série tem lacunas (maior_lacuna_min). Gerado por scripts/eventos_captados.py "
                "a partir de data/tempo-real/*.ndjson (cópia em arquivo-series). Nunca entra em "
                "enchentes.json por aqui: registro_em_enchentes só aponta o que já foi conferido e gravado."
            ),
            "fuso": "horário de Brasília, sem fuso (como a série)",
            "regras": {
                "regua": "comum.regua_de: primária e resgate são UMA régua",
                "cota": "a da própria estação, ou a da cidade quando ela tem uma régua só",
                "episodio": f"leituras na cota ou acima, separadas por > {ep.INTERVALO_ENTRE_EVENTOS_H} h sem cheia; mínimo {ep.MIN_LEITURAS} leituras",
                "relogio_defasado": ep.RELOGIO_DEFASADO,
            },
        },
        "gerado_em": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "cobertura": cobertura,
        "episodios": episodios,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--serie", type=Path, help="pasta com os *.ndjson (padrão: data/tempo-real)")
    ap.add_argument("--gravar", action="store_true", help=f"grava data/{SAIDA}")
    args = ap.parse_args()
    if args.serie:
        ep.SERIE = args.serie
    por_estacao = ep.ler_serie(None)
    if not por_estacao:
        print(f"Nenhuma leitura em {ep.SERIE}. A série é construída ao longo do tempo (ou copie-a do branch arquivo-series).")
        return 0
    estacoes = le_json("estacoes.json")
    enchentes = le_json("enchentes.json")["eventos"]
    resumo = resumir(por_estacao, estacoes, enchentes)
    print(f"{len(resumo['cobertura'])} réguas acompanhadas; {len(resumo['episodios'])} episódio(s) acima da cota.")
    for e in resumo["episodios"]:
        marca = " [registrado]" if e["registro_em_enchentes"] else ""
        print(f"  {e['quando'][:16]} {e['cidade']:<12} {e['regua'][:28]:<28} {e['maior_leitura_m']:.2f} m "
              f"({e['faixa_alcancada'] or 'sem faixa'}) · {e['inicio'][5:16]} → {e['fim'][5:16]} · "
              f"{e['leituras']} leituras, lacuna máx {e['maior_lacuna_min']} min{marca}")
    if args.gravar:
        grava_json(SAIDA, resumo)
        print(f"gravado data/{SAIDA}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
