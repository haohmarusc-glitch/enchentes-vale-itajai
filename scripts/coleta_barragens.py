#!/usr/bin/env python3
"""
Estado das duas barragens do Alto Vale: nível, capacidade e COMPORTA POR COMPORTA.

    GET https://public.asthon.com.br/public/dams?city_id=4214805

Sem autenticação. Devolve uma lista com as DUAS barragens do sistema — Oeste
(Taió, Itajaí do Oeste) e Sul (Ituporanga, Itajaí do Sul) —, apesar de o
`city_id` ser o de Rio do Sul: a consulta é pela cidade de INTERESSE, não pela
cidade onde a barragem fica.

POR QUE ISTO IMPORTA
--------------------
Um rio a 5,4 m com as comportas ABERTAS significa o oposto de um rio a 5,4 m com
elas fechadas:

* comportas **fechadas** + rio subindo → a barragem está segurando; o pior ainda
  pode vir;
* comportas **abertas** + rio estável ou caindo → esvaziamento controlado; o
  pico já passou.

O site mostra só o número. Foi por não ter isto que uma análise nossa concluiu
que a cota de Rio do Sul estava errada, quando o rio estava sendo mantido alto
de propósito enquanto o sistema esvaziava (ver `docs/RIO-DO-SUL-COMPORTAS.md`).

Fecha a lacuna registrada em `docs/AUDITORIA-JICA-2011.md`: *"não implica que o
site da Asthon exponha estado de cada comporta — isso continua lacuna"*.

⚠️ AS QUATRO ARMADILHAS DESTE CORPO — todas com teste
------------------------------------------------------
1. **`montante_m` é ALTITUDE, não régua.** Vem 353,66 na Oeste e 392,58 na Sul —
   metros acima do nível do mar. A leitura da régua da barragem é `nivel_m`
   (14,66 e 22,58), e a relação é exata: `nivel_m = montante_m − gauge_zero_m`.
   Comparar `montante_m` com régua de rio é comparar altitude com zero local, e
   erra por centenas de metros. Aqui os dois saem com nomes que não se confundem.

   E cuidado com a PALAVRA: `docs/TAIO-E-BARRAGEM-OESTE.md` chama de "montante"
   o que esta API chama de `nivel_m` (registrou 17,2 m em 03/09). A mesma
   palavra, duas grandezas, em duas fontes nossas.

2. **`measured_at` é UTC, com `Z`** (`2026-09-05T17:05:06.43Z`) — o contrário da
   convenção do projeto, em que `medido_em` é Brasília sem fuso. Converter é
   obrigatório: confundir os dois já custou uma sessão (ver CLAUDE.md).

3. **`percent_use` NÃO é sempre `capacidade_atual / capacidade_maxima`.** Na
   Oeste bate ao quinto decimal; na Sul diverge 0,057 pp (35,4734 publicado
   contra 35,4163 calculado). Vale o publicado — recalcular por conta própria
   inventaria um número que a fonte não afirma. A divergência é registrada.

4. **`vertido` vem 0 nas duas, com 12 comportas abertas.** Não sabemos o que o
   campo mede — vertimento pelo extravasor, provavelmente, e não a vazão de
   saída pelas comportas. É gravado cru, com o significado marcado como
   desconhecido, e **não** deve ser lido como vazão: o JICA aponta justamente
   que a DEINFRA não publica a vazão de saída, e continua não publicando.

O SCRIPT NÃO DECIDE NADA sobre aviso. Ele mede e grava.

Uso:
    python3 scripts/coleta_barragens.py
    python3 scripts/coleta_barragens.py --arquivo dams.json   # sem rede
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from comum import baixar, espera_turno, grava_json

BASE = "https://public.asthon.com.br/public/dams?city_id="

#: Cidades a consultar. `city_id` NÃO é hidrologia, é CADASTRO: conferido em
#: 05/09/2026, na VPS, `dams?city_id=4207106` (Ibirama) e `dams?city_id=4202404`
#: (Blumenau) devolveram `[]`. Blumenau fica a jusante das TRÊS barragens; se a
#: API devolvesse "barragens a montante da cidade", como este comentário afirmava
#: antes, Blumenau traria ao menos a Oeste e a Sul. Não trouxe nada. Logo o
#: endpoint devolve as barragens CADASTRADAS PARA AQUELE MUNICÍPIO CLIENTE da
#: Asthon — e o cliente é a Defesa Civil de Rio do Sul, que cadastrou as duas
#: que a afetam (Oeste e Sul).
#:
#: Consequência: a Barragem Norte (José Boiteux, Rio Hercílio, que entra no
#: tronco ABAIXO de Rio do Sul, entre Lontras e Ascurra — docs/TOPOLOGIA-CANONICA.md)
#: NÃO vem por este endpoint, a menos que algum município cliente da Asthon a
#: tenha cadastrado. Não se sabe qual, nem se existe. A lista fica com UMA
#: cidade: consultar cidade que devolve `[]` a cada 15 min é pedido vazio mais
#: aviso permanente no log, e aviso que ninguém lê mais é aviso perdido.
#: `_meta.cobertura` declara a ausência para quem lê o JSON.
#:
#: Se aparecer um município que devolva a Norte NO CORPO, ele entra aqui; as
#: respostas são DEDUPLICADAS por `station_id`, então repetir Oeste e Sul não
#: as conta duas vezes.
CITY_IDS = (4214805,)
URL = BASE + str(CITY_IDS[0])  # mantido para quem só quer o endpoint canônico

#: `medido_em` sem fuso é Brasília — convenção do projeto (CLAUDE.md).
FUSO_BRASILIA = ZoneInfo("America/Sao_Paulo")

#: `nivel_m = montante_m − gauge_zero_m` foi conferido nas duas barragens em
#: 05/09/2026, exato. Se passar desta tolerância, a fonte mudou o significado de
#: algum dos três campos e o resto das contas deixa de valer.
TOLERANCIA_NIVEL_M = 0.01

#: Divergência aceita entre `percent_use` e a razão das capacidades. Medida:
#: 0,000 pp na Oeste e 0,057 pp na Sul. Acima disto é outra coisa, não
#: arredondamento.
TOLERANCIA_PERCENT_PP = 0.5


def para_brasilia(carimbo: str | None) -> str | None:
    """`"2026-09-05T17:05:06.43Z"` (UTC) -> `"2026-09-05T14:05:06"` (Brasília)."""
    if not carimbo:
        return None
    try:
        d = datetime.fromisoformat(str(carimbo).strip().replace("Z", "+00:00"))
    except ValueError:
        return None
    if d.tzinfo is None:
        d = d.replace(tzinfo=timezone.utc)
    return d.astimezone(FUSO_BRASILIA).replace(tzinfo=None).isoformat(timespec="seconds")


def numero(v) -> float | None:
    return float(v) if isinstance(v, (int, float)) and not isinstance(v, bool) else None


def converter(bruto: list) -> tuple[list[dict], list[str]]:
    """
    Devolve (barragens, avisos). Aviso é incoerência da FONTE — não derruba a
    coleta, mas fica gravado: o dado segue utilizável e o problema fica à vista.
    """
    saida: list[dict] = []
    avisos: list[str] = []

    for b in bruto if isinstance(bruto, list) else []:
        nome = str(b.get("name") or "?")
        montante = numero(b.get("montante_m"))
        nivel = numero(b.get("nivel_m"))
        zero = numero(b.get("gauge_zero_m"))

        # Guarda 1: a relação altitude/zero/régua. Se quebrar, algum dos três
        # campos mudou de significado e não dá para seguir tratando como antes.
        if None not in (montante, nivel, zero):
            erro = abs((montante - zero) - nivel)
            if erro > TOLERANCIA_NIVEL_M:
                avisos.append(
                    f"{nome}: nivel_m ({nivel:.2f}) não é montante_m − gauge_zero_m "
                    f"({montante:.2f} − {zero:.2f} = {montante - zero:.2f}); "
                    f"diferença {erro:.2f} m — a fonte mudou o significado de algum campo")

        # Guarda 2: a contagem publicada contra a lista de verdade.
        lista = b.get("comportas") or []
        abertas = [c for c in lista if c.get("aberta") is True]
        contagem = b.get("comportas_abertas")
        total = b.get("comportas_total")
        if isinstance(contagem, int) and contagem != len(abertas):
            avisos.append(f"{nome}: comportas_abertas={contagem} mas {len(abertas)} "
                          f"de {len(lista)} têm aberta=true")
        if isinstance(total, int) and total != len(lista):
            avisos.append(f"{nome}: comportas_total={total} mas a lista tem {len(lista)}")

        # Guarda 3: o percentual publicado contra o calculado. NÃO recalcula.
        pu = numero(b.get("percent_use"))
        ca, cm = numero(b.get("capacidade_atual")), numero(b.get("capacidade_maxima"))
        divergencia = None
        if None not in (pu, ca, cm) and cm:
            divergencia = round(pu - (ca / cm * 100.0), 4)
            if abs(divergencia) > TOLERANCIA_PERCENT_PP:
                avisos.append(f"{nome}: percent_use {pu:.2f}% diverge {divergencia:+.2f} pp "
                              f"da razão das capacidades")

        saida.append({
            "estacao": b.get("station_id"),
            "nome": nome,
            "rio": b.get("river_name"),
            "lat": numero(b.get("latitude")),
            "lon": numero(b.get("longitude")),
            "medido_em": para_brasilia(b.get("measured_at")),
            # Os dois níveis, com o nome dizendo qual é qual.
            "altitude_montante_m": montante,
            "nivel_na_regua_da_barragem_m": nivel,
            "zero_da_regua_m": zero,
            "jusante_m": numero(b.get("jusante_m")),
            "percent_use": pu,
            "percent_use_divergencia_pp": divergencia,
            "capacidade_atual": ca,
            "capacidade_maxima": cm,
            "comportas_abertas": len(abertas),
            "comportas_total": len(lista),
            "comportas": [{"nome": c.get("nome"), "aberta": c.get("aberta") is True}
                          for c in lista],
            "vertido_bruto": b.get("vertido"),
        })
    return saida, avisos


def coletar(buscador=None, city_ids=CITY_IDS) -> dict:
    """
    Consulta cada cidade de interesse e junta as barragens, uma vez cada
    (deduplicação por `station_id`): a Oeste e a Sul vêm tanto por Rio do Sul
    quanto por qualquer cidade a jusante, e não podem entrar duas vezes.
    Uma cidade que falhe (rede, código errado) vira aviso — as outras seguem.
    """
    if buscador is None:
        def buscador(city_id: int):
            espera_turno()
            return json.loads(baixar(BASE + str(city_id)))
    bruto_total: list = []
    vistos: set = set()
    avisos_rede: list[str] = []
    for cid in city_ids:
        try:
            resposta = buscador(cid)
        except Exception as e:  # noqa: BLE001 — uma cidade fora não derruba as outras
            avisos_rede.append(f"city_id={cid} falhou ({e}); seguindo com as outras")
            continue
        lista = resposta if isinstance(resposta, list) else []
        if not lista:
            # `[]` não é sucesso: ou a cidade não tem barragem cadastrada, ou o
            # código não existe na fonte. Sem este aviso, um código errado pareceria
            # saúde — foi exatamente o que 4207106 devolveu em 05/09/2026.
            avisos_rede.append(f"city_id={cid} devolveu lista vazia — nenhuma barragem cadastrada "
                               f"para essa cidade na fonte, ou código sem cadastro; nada inventado")
            continue
        for b in lista:
            chave = b.get("station_id") or b.get("name")
            if chave in vistos:
                continue
            vistos.add(chave)
            bruto_total.append(b)
    barragens, avisos = converter(bruto_total)
    avisos = avisos_rede + avisos
    return {
        "_meta": {
            "descricao": "Estado das barragens Oeste (Taió) e Sul (Ituporanga), comporta a comporta.",
            "fonte": [BASE + str(c) for c in city_ids],
            "cobertura": "Oeste (Taió) e Sul (Ituporanga). A BARRAGEM NORTE (José Boiteux, Rio "
                         "Hercílio) NÃO está aqui: a bacia tem três barragens de contenção, e a fonte "
                         "devolveu lista vazia para Ibirama (4207106) e para Blumenau (4202404) em "
                         "05/09/2026 — o endpoint é cadastro do município cliente, não hidrologia. Quem "
                         "lê 'todas as comportas abertas' neste arquivo está lendo DUAS das três.",
            "coletado_em": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "fuso": "`medido_em` é Brasília sem fuso, convertido do `measured_at` da fonte, que "
                    "vem em UTC com Z. `coletado_em` é UTC — campos diferentes, não confundir.",
            "ALTITUDE_NAO_E_REGUA": "`altitude_montante_m` é metros acima do NÍVEL DO MAR (353,66 na "
                                    "Oeste); `nivel_na_regua_da_barragem_m` é a leitura da régua "
                                    "(14,66). A relação é exata: régua = altitude − zero. Comparar a "
                                    "altitude com régua de rio erra por centenas de metros. Atenção "
                                    "ao nome: docs/TAIO-E-BARRAGEM-OESTE.md chama de 'montante' o que "
                                    "aqui é `nivel_na_regua_da_barragem_m`.",
            "percent_use": "Vale o valor PUBLICADO. Ele bate com capacidade_atual/capacidade_maxima "
                           "na Oeste e diverge ~0,06 pp na Sul; a divergência fica em "
                           "`percent_use_divergencia_pp` em vez de o script recalcular.",
            "vertido": "Gravado cru como `vertido_bruto`. SIGNIFICADO DESCONHECIDO — veio 0 nas duas "
                       "com 12 comportas abertas, então NÃO é a vazão de saída. O JICA aponta que a "
                       "DEINFRA não publica essa vazão, e ela continua não publicada.",
            "para_que_serve": "Comportas fechadas + rio subindo = a barragem está segurando, o pior "
                              "pode vir. Comportas abertas + rio estável ou caindo = esvaziamento "
                              "controlado, o pico já passou. O mesmo nível significa coisas opostas.",
            "avisos_da_fonte": avisos,
        },
        "barragens": barragens,
    }


def contar(doc: dict) -> None:
    for b in doc["barragens"]:
        print(f"{b['nome']}  ({b['rio']})")
        print(f"  medido em {b['medido_em']} (Brasília)")
        print(f"  régua da barragem {b['nivel_na_regua_da_barragem_m']:.2f} m "
              f"· altitude {b['altitude_montante_m']:.2f} m · zero {b['zero_da_regua_m']:.0f} m")
        print(f"  jusante {b['jusante_m']:.2f} m · capacidade {b['percent_use']:.1f}%")
        fechadas = [c["nome"] for c in b["comportas"] if not c["aberta"]]
        print(f"  comportas: {b['comportas_abertas']} de {b['comportas_total']} abertas"
              + (f" · fechadas: {', '.join(fechadas)}" if fechadas else ""))
    for a in doc["_meta"]["avisos_da_fonte"]:
        print(f"aviso: {a}", file=sys.stderr)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    p.add_argument("--arquivo", help="JSON já baixado, para conferir sem rede")
    p.add_argument("--gravar", action="store_true", help="grava em data/tempo-real/")
    a = p.parse_args(argv)

    if a.arquivo:
        with open(a.arquivo, encoding="utf-8") as f:
            corpo = json.load(f)
        # Um arquivo só representa UMA consulta; a lista vira uma cidade.
        doc = coletar(buscador=lambda _cid: corpo, city_ids=(0,))
    else:
        doc = coletar()

    if not doc["barragens"]:
        print("erro: nenhuma barragem no corpo — nada gravado", file=sys.stderr)
        return 1
    contar(doc)

    if a.arquivo and not a.gravar:
        print("\n(nada gravado — use --gravar)")
        return 0
    grava_json("tempo-real/ultimo_barragens.json", doc)
    print("\n-> data/tempo-real/ultimo_barragens.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
