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

**Não dá.** "Nível" não é a mesma grandeza entre as fontes, e a prova não
depende de onde fica estação nenhuma — é a MESMA estrutura, nomeada igual nos
dois lugares, no mesmo intervalo de horas:

    Barragem Sul Ituporanga:  Gaspar 392,62 m   estadual 22,79 m   (369,83 m)
    Barragem Oeste Taió:      Gaspar 351,81 m   estadual 12,97 m   (338,84 m)

Isso é cota do reservatório acima do mar contra altura na escala do próprio
barramento. E a rede estadual **concorda** com a nossa em outras estações —
Brusque 4,48 contra 4,42 —, que é exatamente o que "não é a mesma grandeza entre
estações" significa: não dá para saber, por estação, qual das duas coisas se
está lendo.

Havia uma segunda prova, o par de Ilhota (estadual 10,67 m contra 3,34 m na
nossa DC-11), e ela **saiu de sustentação**: em que município fica a DC-11 está
em aberto, e se for Itajaí o par compara duas cidades diferentes. Fica em
`EVIDENCIA_CONTESTADA`, marcada, sem segurar nada.

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

#: A prova de que "nível" não é a mesma grandeza entre fontes, sem depender de
#: onde fica estação nenhuma: a MESMA estrutura, nomeada igual nas duas fontes,
#: no mesmo intervalo de horas. Cada item é
#: (estrutura, valor no município de Gaspar, valor na rede estadual, código).
#:
#: 370 m de diferença é cota do reservatório acima do mar contra altura na
#: escala do próprio barramento. Nenhuma leitura de rio explica isso, e nenhum
#: argumento sobre limite municipal a desfaz.
EVIDENCIA_INDEPENDENTE = [
    ("Barragem Sul Ituporanga", 392.62, 22.79, "DCSC-00038"),
    ("Barragem Oeste Taió", 351.81, 12.97, "DCSC-00040"),
]

#: A evidência que ANTES sustentava sozinha este portão, e por que ela nunca
#: devia ter sustentado.
#:
#: O par era: rede estadual em Ilhota (DCSC-00030) contra a nossa DC-11. Ficou
#: provado (Plano de Contingência da COMPDEC Itajaí, Tabela 11 + Zona 1) que a
#: DC-11 é de **Itajaí**, não de Ilhota — ou seja, o par comparava DUAS CIDADES
#: DIFERENTES e nunca provou zero diferente nenhum. Foi por pouco: a decisão de
#: reassentar o portão nas barragens foi tomada enquanto a dúvida ainda estava
#: aberta, e a resolução só confirmou que estava certa em não confiar nele.
#:
#: Continua aqui, marcado, como lembrete: quem sustenta o portão é a evidência
#: das barragens acima, que não depende de município nenhum.
EVIDENCIA_CONTESTADA = [
    ("2026-08-31", "DCSC-00030", 10.34, 3.25, "DC-11 Santa Regina — é de Itajaí, não de Ilhota"),
    ("2026-09-01", "DCSC-00030", 10.67, 3.34, "DC-11 Santa Regina — é de Itajaí, não de Ilhota"),
]

#: Diferença acima da qual duas leituras da mesma cidade não podem ser o mesmo
#: zero. Uma régua sobe centímetros por hora numa cheia; sete metros não é
#: defasagem de horário.
LIMITE_DE_COERENCIA_M = 1.0

#: Distância máxima, em minutos, entre as duas leituras de um par.
#:
#: Sem isto o script faria a pior coisa que ele existe para impedir: um número
#: que PARECE medido e não é. Parear a leitura do município de 31/08 22:59 com
#: a estadual de 01/09 03:24 — o caso real que apareceu na primeira execução —
#: dá 4h25 de intervalo, e numa cheia o rio sobe nesse tempo. A diferença seria
#: parte deslocamento de régua, parte subida do rio, sem como separar.
#: Trinta minutos porque, a 20 cm/h (subida forte no médio Itajaí), a parcela de
#: subida fica em ~10 cm — uma ordem de grandeza abaixo do limite de coerência.
JANELA_MAXIMA_MIN = 30

#: Como a tabela do município chama a régua do rio, em `ultimo_gaspar.json`.
ROTULO_MUNICIPIO = "Rio Itajaí Açu Gaspar"

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

    O arquivo é `ultimo_gaspar.json`, que o `coleta_gaspar.py` escreve, e NÃO o
    `ultimo.json` da coleta geral: Gaspar não está na coleta geral, que é
    justamente o problema. A primeira versão deste script procurava no arquivo
    errado e dizia "SEM LEITURA" com 3,85 m guardados no repositório ao lado.
    """
    caminho = DADOS / "tempo-real" / "ultimo_gaspar.json"
    if not caminho.exists():
        return None, None
    try:
        dados = json.loads(caminho.read_text(encoding="utf-8"))
    except (ValueError, OSError):
        return None, None
    for e in dados.get("estacoes") or []:
        if e.get("rotulo") != ROTULO_MUNICIPIO:
            continue
        valor = e.get("nivel_m")
        # `nivel_plausivel` é o veredito do próprio coletor. Um número que ele
        # marcou como implausível não vira metade de um par de calibração.
        if isinstance(valor, (int, float)) and e.get("nivel_plausivel"):
            return float(valor), e.get("medido_em_iso")
        return None, e.get("medido_em_iso")
    return None, None


def minutos_entre(a: str | None, b: str | None) -> float | None:
    """Distância entre dois carimbos ISO, em minutos. `None` se algum faltar."""
    def ler(s):
        if not s:
            return None
        try:
            d = datetime.fromisoformat(str(s).replace("Z", "+00:00"))
        except ValueError:
            return None
        return d if d.tzinfo else d.replace(tzinfo=timezone.utc)

    x, y = ler(a), ler(b)
    if x is None or y is None:
        return None
    return abs((x - y).total_seconds()) / 60.0


def usavel_para_aviso() -> tuple[bool, str]:
    """
    O nível estadual de Gaspar pode ser comparado com as cotas 5/6/7?

    Este é o portão. Ele fecha por padrão, e só abre com número medido — não
    com plausibilidade, não com "os outros batem".
    """
    if DESLOCAMENTO_CONHECIDO_M is None:
        return False, (
            "deslocamento entre a régua estadual e a do Plano NÃO medido. "
            "A mesma Barragem Sul aparece como 392,62 m na tabela de Gaspar e "
            "22,79 m na rede estadual: 'nível' não é uma grandeza só. Se Gaspar "
            "tiver deslocamento, 5/6/7 m viram faixa errada nos dois sentidos "
            "— e o sentido que esconde a cheia é o que mata."
        )
    return True, f"deslocamento medido: {DESLOCAMENTO_CONHECIDO_M:+.2f} m"


def medir_deslocamento(estadual: float | None,
                       municipal: float | None,
                       quando_e: str | None = None,
                       quando_m: str | None = None) -> tuple[float | None, str]:
    """
    O par que destrava a fonte: estadual menos municipal, no MESMO instante.

    "No mesmo instante" não é detalhe. Duas leituras separadas por horas numa
    cheia diferem porque o rio subiu, e essa parcela não se separa do
    deslocamento de régua. Um par fora da janela é recusado — devolver o número
    assim mesmo seria fabricar a medição que este script existe para exigir.

    Não grava nada. Um par só também não fecha a questão: o deslocamento tem de
    se repetir em níveis diferentes antes de virar constante.
    """
    if estadual is None and municipal is None:
        return None, "nenhum dos dois lados tem leitura"
    if estadual is None:
        return None, "a rede estadual não trouxe nível de Gaspar"
    if municipal is None:
        return None, "não há leitura da tabela do município para parear"

    intervalo = minutos_entre(quando_e, quando_m)
    if intervalo is None and (quando_e or quando_m):
        return None, "um dos lados veio sem horário — não dá para saber se são o mesmo instante"
    if intervalo is not None and intervalo > JANELA_MAXIMA_MIN:
        return None, (f"as duas leituras estão a {intervalo:.0f} min uma da outra "
                      f"(máximo {JANELA_MAXIMA_MIN} min): numa cheia o rio sobe nesse "
                      "tempo, e a diferença seria parte subida, parte régua")

    d = estadual - municipal
    perto = f" ({intervalo:.0f} min de intervalo)" if intervalo is not None else ""
    if abs(d) <= LIMITE_DE_COERENCIA_M:
        return d, (f"os dois lados batem dentro de {LIMITE_DE_COERENCIA_M:.2f} m{perto} "
                   "— indício de mesma régua, a confirmar em outro nível")
    return d, ("os dois lados NÃO são a mesma régua: "
               f"{abs(d):.2f} m de diferença{perto}")


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--salvar", action="store_true",
                   help="guarda a resposta bruta em data/brutos/")
    args = p.parse_args()

    print("Gaspar na rede estadual (DCSC-00005) — medição, não coleta\n")
    for nome, gaspar, estadual, cod in EVIDENCIA_INDEPENDENTE:
        print(f"  {nome}: tabela de Gaspar {gaspar:.2f} m; rede estadual "
              f"({cod}) {estadual:.2f} m — {gaspar - estadual:.2f} m de diferença")
    for data, cod, deles, nosso, quem in EVIDENCIA_CONTESTADA:
        print(f"  [contestada] {data}: {cod} veio {deles:.2f} m; {quem} marcava "
              f"{nosso:.2f} m — cidades diferentes, não sustenta o portão")

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

    d, porque = medir_deslocamento(estadual, municipal, quando_e, quando_m)
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
