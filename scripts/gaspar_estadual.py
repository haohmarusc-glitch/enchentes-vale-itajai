#!/usr/bin/env python3
"""
Mede se o nível que a rede estadual publica para Gaspar serve para o aviso.

NÃO é um coletor. É a medição que precisa vir antes de um.

O PROBLEMA
----------
Gaspar tem cota de régua desde 01/09/2026 — 5,00 / 6,00 / 7,00 m, do Plano de
Contingência (`conferir_gaspar_plano.py`) — e não tem leitura: o host do
município não responde de fora. A rede estadual (GraphQL da Defesa Civil de SC)
tem uma estação em Gaspar, `DCSC-00005`, e é tentador ligar uma coisa na outra.

**Não dá, ainda.** O `rio_nivel` da rede estadual não é a mesma grandeza entre
estações, e isso está medido duas vezes, com sete metros de diferença:

    Ilhota, 31/08/2026:  estadual 10,34 m   nossa régua 3,25 m   (7,09 m)
    Ilhota, 01/09/2026:  estadual 10,67 m   nossa régua 3,34 m   (7,33 m)

Não é ruído nem leitura velha: é outro zero. Nas mesmas duas ocasiões Brusque
bate (4,48 contra 4,42) — ou seja, a rede concorda em algumas estações e está
7 m fora em outras, que é exatamente o que "não é a mesma grandeza" significa.

POR QUE ISSO SERIA GRAVE EM GASPAR
----------------------------------
As faixas do Plano são 5 / 6 / 7 m. Um número com deslocamento tipo Ilhota
mostraria **RESPOSTA com o rio no leito** — ou, deslocado para o outro lado,
mostraria normalidade com a água na rua. Das duas, a segunda mata. E não há
como saber qual seria: **nunca houve um par** (nível estadual de Gaspar e
leitura da tabela do município no mesmo instante) para medir o deslocamento.

O QUE ESTE SCRIPT FAZ
---------------------
Junta esse par, quando ele existir, e diz o número. Enquanto o deslocamento não
estiver medido e escrito em `DESLOCAMENTO_CONHECIDO_M`, ele **se recusa** a
propor o valor para aviso — e diz isso em voz alta, em vez de devolver silêncio.

Silêncio, aliás, era o defeito da primeira tentativa em shell: `jq -r
'select(.codigo=="DCSC-00005")'` sai com código 0 quando não acha nada, então o
`|| { fallback }` nunca rodava. Numa coleta em que a estação não devolveu nível
— o caso real de 01/09/2026 03:09Z — a saída era nenhuma linha e um alegre
"snapshot salvo". Fonte que falha calada é pior que fonte fora do ar.

Uso:
    python3 scripts/gaspar_estadual.py            # mede e relata
    python3 scripts/gaspar_estadual.py --salvar   # guarda o bruto também
"""

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from comum import DADOS, USER_AGENT, espera_turno

URL = "https://monitoramento.defesacivil.sc.gov.br/graphql"
CLIENTE = "secretaria-de-defesa-civil"

#: A estação da rede estadual em Gaspar. Ela publica chuva (77,2 mm/24h em
#: 01/09/2026) — e chuva pode ser usada: milímetro é milímetro em qualquer
#: lugar. É só o NÍVEL que está em questão aqui.
CODIGO_GASPAR = "DCSC-00005"

#: Deslocamento entre a régua estadual e a régua do Plano, em metros.
#: `None` = não medido. Enquanto for `None`, nenhum nível estadual de Gaspar
#: pode ser comparado com as cotas 5/6/7. Preencher SÓ com par medido, e num
#: commit que registre o par em `docs/fontes-tempo-real.md`.
DESLOCAMENTO_CONHECIDO_M: float | None = None

#: A prova de que a rede não está num zero só. Cada item é
#: (data, código, nível estadual, nossa régua, nome da nossa estação).
EVIDENCIA_DE_ZEROS_DIFERENTES = [
    ("2026-08-31", "DCSC-00030", 10.34, 3.25, "DC-11 Santa Regina (Ilhota)"),
    ("2026-09-01", "DCSC-00030", 10.67, 3.34, "DC-11 Santa Regina (Ilhota)"),
]

#: Diferença acima da qual duas leituras da mesma cidade não podem ser o mesmo
#: zero. Uma régua sobe centímetros por hora numa cheia; sete metros não é
#: defasagem de horário.
LIMITE_DE_COERENCIA_M = 1.0

Q_TAGS = """query Tags_data { tags_data(clients: ["%s"]) { qualle_meteorologia {
  codigo name { general local } timestamp
  data { rio { rio_nivel { value } rio_nivel_tendencia { value } }
         chuva { acumulado { h024 { value } } } } } } }""" % CLIENTE


def consultar(transporte=None) -> Any:
    """POST no GraphQL estadual. `transporte` existe para o teste não sair na rede."""
    if transporte is not None:
        return transporte(URL, Q_TAGS)
    import requests

    espera_turno()
    r = requests.post(
        URL,
        json={"operationName": "Tags_data", "query": Q_TAGS},
        headers={"User-Agent": USER_AGENT, "Content-Type": "application/json"},
        timeout=30,
    )
    r.raise_for_status()
    return r.json()


def estacoes(resposta: Any) -> list[dict]:
    try:
        return list(resposta["data"]["tags_data"]["qualle_meteorologia"] or [])
    except (KeyError, TypeError):
        return []


def nivel_da_estacao(resposta: Any, codigo: str) -> tuple[float | None, str | None]:
    """
    Nível daquela estação, e o horário da medição.

    Devolve `(None, ...)` quando a estação não está na resposta OU está e não
    trouxe nível — os dois casos existem de verdade, e nenhum deles pode virar
    silêncio: em 01/09/2026 03:09Z Gaspar e Blumenau estavam na resposta e
    vieram sem valor.
    """
    for e in estacoes(resposta):
        if e.get("codigo") != codigo:
            continue
        rio = ((e.get("data") or {}).get("rio") or {})
        valor = (rio.get("rio_nivel") or {}).get("value")
        if isinstance(valor, (int, float)):
            return float(valor), e.get("timestamp")
        return None, e.get("timestamp")
    return None, None


def nivel_do_municipio() -> tuple[float | None, str | None]:
    """
    A leitura da tabela do próprio município, se alguma foi coletada.

    É o outro lado do par. Sem ela não há deslocamento a medir — só um número
    solto de origem desconhecida.
    """
    caminho = DADOS / "tempo-real" / "ultimo.json"
    if not caminho.exists():
        return None, None
    try:
        dados = json.loads(caminho.read_text(encoding="utf-8"))
    except (ValueError, OSError):
        return None, None
    for l in dados.get("leituras") or []:
        if l.get("cidade") == "gaspar" and isinstance(l.get("nivel_m"), (int, float)):
            return float(l["nivel_m"]), l.get("medido_em")
    return None, None


def usavel_para_aviso() -> tuple[bool, str]:
    """
    O nível estadual de Gaspar pode ser comparado com as cotas 5/6/7?

    Este é o portão. Ele fecha por padrão, e só abre com número medido — não
    com plausibilidade, não com "os outros batem".
    """
    if DESLOCAMENTO_CONHECIDO_M is None:
        return False, (
            "deslocamento entre a régua estadual e a do Plano NÃO medido. "
            "Na mesma rede, Ilhota vem 7,3 m acima da nossa régua; se Gaspar "
            "tiver deslocamento parecido, 5/6/7 m viram faixa errada nos dois "
            "sentidos — e o sentido que esconde a cheia é o que mata."
        )
    return True, f"deslocamento medido: {DESLOCAMENTO_CONHECIDO_M:+.2f} m"


def medir_deslocamento(estadual: float | None,
                       municipal: float | None) -> tuple[float | None, str]:
    """
    O par que destrava a fonte: estadual menos municipal, no mesmo instante.

    Não grava nada. Um par só não fecha a questão — o deslocamento tem de se
    repetir em leituras de níveis diferentes antes de virar constante.
    """
    if estadual is None and municipal is None:
        return None, "nenhum dos dois lados tem leitura"
    if estadual is None:
        return None, "a rede estadual não trouxe nível de Gaspar"
    if municipal is None:
        return None, "não há leitura da tabela do município para parear"
    d = estadual - municipal
    if abs(d) <= LIMITE_DE_COERENCIA_M:
        return d, (f"os dois lados batem dentro de {LIMITE_DE_COERENCIA_M:.2f} m "
                   "— indício de mesma régua, a confirmar em outro nível")
    return d, ("os dois lados NÃO são a mesma régua: "
               f"{abs(d):.2f} m de diferença no mesmo instante")


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--salvar", action="store_true",
                   help="guarda a resposta bruta em data/brutos/")
    args = p.parse_args()

    print("Gaspar na rede estadual (DCSC-00005) — medição, não coleta\n")
    for data, cod, deles, nosso, quem in EVIDENCIA_DE_ZEROS_DIFERENTES:
        print(f"  evidência {data}: {cod} veio {deles:.2f} m; {quem} marcava "
              f"{nosso:.2f} m — {deles - nosso:.2f} m de diferença")

    try:
        resposta = consultar()
    except Exception as e:                     # noqa: BLE001 — a rede falha de muitos jeitos
        print(f"\n✗ não consegui consultar {URL}: {type(e).__name__}: {e}")
        print("  (o ambiente de dev bloqueia este host; rodar na VPS)")
        return 2

    if args.salvar:
        carimbo = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        destino = DADOS / "brutos" / f"estadual-{carimbo}.json"
        destino.write_text(json.dumps(resposta, ensure_ascii=False, indent=2) + "\n",
                           encoding="utf-8")
        print(f"\nbruto salvo em {destino}")

    estadual, quando_e = nivel_da_estacao(resposta, CODIGO_GASPAR)
    municipal, quando_m = nivel_do_municipio()

    print(f"\n  rede estadual  : "
          f"{f'{estadual:.2f} m' if estadual is not None else 'SEM LEITURA'}"
          f"  ({quando_e or 'sem horário'})")
    print(f"  tabela do munic: "
          f"{f'{municipal:.2f} m' if municipal is not None else 'SEM LEITURA'}"
          f"  ({quando_m or 'sem horário'})")

    d, porque = medir_deslocamento(estadual, municipal)
    print(f"\n  deslocamento   : "
          f"{f'{d:+.2f} m' if d is not None else 'não medível'} — {porque}")

    ok, motivo = usavel_para_aviso()
    print(f"\n  {'✓' if ok else '✗'} usar no aviso de Gaspar: "
          f"{'SIM' if ok else 'NÃO'} — {motivo}")
    if not ok:
        print("\n  Este script não escreve em data/tempo-real/ultimo.json e não "
              "alimenta alerta_cotas.py. Enquanto o portão estiver fechado, o "
              "número acima serve para OLHAR, nunca para avisar.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
