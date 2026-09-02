#!/usr/bin/env python3
"""
Coleta a chuva acumulada da Rede Integrada da Defesa Civil de SC.

Fonte: https://monitoramento.defesacivil.sc.gov.br/graphql (Tags_data).
O `robots.txt` de lá traz `Disallow:` vazio — permissão explícita para tudo.
Conferido na VPS em 31/08/2026 pela `sonda_fontes_novas.py`.

POR QUE SÓ CHUVA, E NUNCA NÍVEL
-------------------------------
A mesma resposta traz `data.rio.rio_nivel`, e é tentador usá-lo: são 61 estações
na bacia, contra as 14 que temos. A sonda mostrou que **não dá**, por dois
motivos, um deles medido contra os nossos próprios números no mesmo instante:

* **O "nível" não é a mesma grandeza entre estações.** Ilhota veio 10,34 m
  enquanto a nossa régua da mesma cidade marcava 3,25 m — sete metros de
  diferença. As estações com sufixo `(H)` trazem 342, 385, 456, 877, 914: isso
  é altitude ou outra coisa, não leitura de régua. Brusque (3,25 contra 3,21) e
  Rio do Sul (5,52 contra 5,44) batem, mas nessas duas já temos leitura.
* **Não vem cota de referência.** Os campos de uma estação são `codigo`,
  `name`, `timestamp`, `position`, `rio_nome`, `rio_nivel`,
  `rio_nivel_tendencia` e `chuva.acumulado`. Sem a cota DAQUELA régua, nenhuma
  leitura pode virar aviso: ela seria comparada com a cota de outra.

É a terceira vez que este projeto encontra um campo chamado "nível" ou "cota"
que não é o que parece — antes foram o `Relevo_Ponto_Cotado_Altimetrico` de
Itajaí e o KML de Brusque. Ambos estão em `docs/cotas-de-ruas.md`.

**Chuva não tem esse problema.** Milímetro é milímetro em qualquer lugar: não
depende de régua, de zero nem de datum. Por isso ela entra e o nível não.

O QUE ISTO RESOLVE
------------------
Chuva em cidades que hoje não têm nenhuma na tela: Blumenau, Timbó, Ibirama,
Apiúna, Botuverá, Guabiruba, Vidal Ramos, Taió, Ituporanga, Gaspar e Indaial.
A fonte de Itajaí só publica pluviômetro em quatro cidades.

O MAPA É EXPLÍCITO, NÃO ADIVINHADO
----------------------------------
Casar "SDC-SC Timbó 1" com uma cidade por semelhança de nome é como se erra
calado: há "Timbó 1" e "Timbó 2", "Botuverá 1" e "Botuverá 2", "Brusque" e
"Brusque (M)", e sufixos `(H)`/`(M)` que não sabemos o que significam. Estação
que não estiver no mapa abaixo é ignorada, e o script diz quantas ignorou.

Uso:
    python3 scripts/coleta_chuva_sc.py --seco    # mostra o que colheria
    python3 scripts/coleta_chuva_sc.py
"""

import argparse
import json
import sys
from datetime import datetime, timedelta, timezone

from coleta_chuva import incoerencias
from comum import DADOS, USER_AGENT, espera_turno

GRAPHQL = "https://monitoramento.defesacivil.sc.gov.br/graphql"
CLIENTE = "secretaria-de-defesa-civil"

CONSULTA = """query Tags_data { tags_data(clients: ["%s"]) { qualle_meteorologia {
  codigo name { prefix general local } timestamp
  position { bacia }
  data { chuva { acumulado { h001 { value } h024 { value } } } } } } }""" % CLIENTE

#: Fuso das medições no resto do projeto: `medido_em` é hora de Brasília SEM
#: fuso, e o GraphQL devolve UTC com fuso. Converter errado desloca a idade de
#: toda leitura em três horas — e a idade é o que diz se o número serve.
FUSO_BRASILIA = timezone(timedelta(hours=-3))

#: Código DCSC -> id de cidade em `data/estacoes.json`.
#:
#: Só entram estações cuja cidade existe no projeto e cujo nome não é ambíguo.
#: As numeradas (Botuverá 1/2) entram as duas: são pluviômetros distintos da
#: mesma cidade, e o site já mostra o maior de vários.
#:
#: TIMBÓ FICA DE FORA, de propósito, e não por engano. Ela é cidade do projeto,
#: mas mora em `afluentes_monitorados`, não na sequência dos rios: fica no Rio
#: Benedito e tem relógio próprio, então `comum.cidades()` não a devolve e nem
#: o site nem o bot conseguem mostrá-la. Coletar a chuva dela agora seria
#: encher o arquivo com número que ninguém vê — cobertura aparente, que é pior
#: do que buraco declarado. As estações existem e estão anotadas aqui para o
#: dia em que os afluentes ganharem tela: DCSC-00023 (Timbó 1) e DCSC-00034
#: (Timbó 2).
POR_CIDADE = {
    "DCSC-00005": "gaspar",
    "DCSC-00006": "indaial",
    "DCSC-00013": "rio-do-sul",
    "DCSC-00018": "botuvera",
    "DCSC-00019": "brusque",
    "DCSC-00020": "ibirama",
    "DCSC-00024": "vidal-ramos",
    "DCSC-00026": "blumenau",
    "DCSC-00027": "botuvera",
    "DCSC-00029": "guabiruba",
    "DCSC-00030": "ilhota",
    "DCSC-00039": "ituporanga",
    "DCSC-00041": "taio",
    "DCSC-00178": "apiuna",
}

#: Chuva acima disto em 24 h não é medição, é defeito. O recorde diário do
#: Vale, em nov/2008, ficou perto de 250 mm. O teto é folgado de propósito:
#: recusar chuva real numa cheia seria pior do que deixar passar um absurdo,
#: que o teste de coerência ainda pega.
CHUVA_MAXIMA_MM = 500.0


def e_numero(valor) -> bool:
    """`isinstance(True, int)` é True em Python, e True não é milímetro."""
    return isinstance(valor, (int, float)) and not isinstance(valor, bool)


def valor_de(caixa) -> float | None:
    """
    O `{"value": x}` do GraphQL, ou None quando a fonte não publicou.

    Arredonda para 2 casas: a API devolve float IEEE cru (0.009999999776… mm),
    que sem isto vaza para o JSON e para a tela. Pluviômetro tem passo de 0,1–0,2
    mm; 2 casas guardam tudo que a fonte tem e somem com o ruído do float.
    """
    if not isinstance(caixa, dict):
        return None
    v = caixa.get("value")
    return round(float(v), 2) if e_numero(v) else None


def hora_local(carimbo: str | None) -> str | None:
    """UTC do GraphQL -> hora de Brasília sem fuso, que é o formato do projeto."""
    if not carimbo:
        return None
    try:
        t = datetime.fromisoformat(carimbo.replace("Z", "+00:00"))
    except ValueError:
        return None
    if t.tzinfo is None:
        t = t.replace(tzinfo=timezone.utc)
    return t.astimezone(FUSO_BRASILIA).replace(tzinfo=None).isoformat(timespec="seconds")


def converter(estacoes: list[dict]) -> tuple[list[dict], list[str]]:
    """As leituras de chuva que dá para usar, e o motivo de cada recusa."""
    leituras, recusadas = [], []
    for e in estacoes:
        codigo = e.get("codigo")
        nome = ((e.get("name") or {}).get("general") or codigo or "?").strip()
        cidade = POR_CIDADE.get(codigo)
        if not cidade:
            recusadas.append(f"{nome}: fora do mapa de cidades")
            continue

        acumulado = (((e.get("data") or {}).get("chuva") or {}).get("acumulado") or {})
        mm = {
            "min10": None,
            "h1": valor_de(acumulado.get("h001")),
            "h12": None,
            "h24": valor_de(acumulado.get("h024")),
            "h48": None,
        }
        if all(v is None for v in mm.values()):
            recusadas.append(f"{nome}: sem nenhuma janela de chuva")
            continue

        fora = [f"{j}={mm[j]:g} mm" for j in ("h1", "h24")
                if mm[j] is not None and not (0 <= mm[j] <= CHUVA_MAXIMA_MM)]
        if fora:
            recusadas.append(f"{nome}: {', '.join(fora)} fora da faixa plausível")
            continue

        problemas = incoerencias(mm)
        leituras.append({
            "estacao": f"{codigo} {nome}",
            "rio": None,       # a fonte dá a bacia, não a calha; não se inventa
            "cidade": cidade,
            "mm": mm,
            "medido_em": hora_local(e.get("timestamp")),
            "coerente": not problemas,
            "incoerencias": problemas,
            "fonte": "Defesa Civil de SC — Rede Integrada (GraphQL)",
        })
    return leituras, recusadas


def baixar_estacoes() -> list[dict]:
    import requests

    espera_turno()
    r = requests.post(GRAPHQL, json={"query": CONSULTA, "operationName": "Tags_data"},
                      headers={"User-Agent": USER_AGENT}, timeout=60)
    r.raise_for_status()
    corpo = r.json()
    if corpo.get("errors"):
        raise RuntimeError(f"consulta recusada: {corpo['errors']}")
    return (((corpo.get("data") or {}).get("tags_data") or {})
            .get("qualle_meteorologia") or [])


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--seco", action="store_true", help="mostra o que colheria, sem gravar")
    args = ap.parse_args()

    try:
        estacoes = baixar_estacoes()
    except Exception as e:
        print(f"ERRO ao coletar: {e}", file=sys.stderr)
        return 1

    leituras, recusadas = converter(estacoes)
    print(f"{len(estacoes)} estações no estado · {len(leituras)} viraram leitura de chuva")
    for l in sorted(leituras, key=lambda x: x["cidade"]):
        h24 = l["mm"]["h24"]
        marca = "" if l["coerente"] else "  ⚠ " + "; ".join(l["incoerencias"])
        print(f"  {l['cidade']:12} {(f'{h24:6.1f} mm/24h' if h24 is not None else '     — '):>14}"
              f"  {l['medido_em']}  {l['estacao']}{marca}")
    if recusadas:
        print(f"\n{len(recusadas)} estação(ões) fora do mapa ou sem dado usável.")

    if args.seco:
        return 0

    destino = DADOS / "tempo-real" / "chuva-sc.json"
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_text(json.dumps({
        "coletado_em": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "fonte": GRAPHQL,
        "leituras": leituras,
    }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"\ngravado em {destino}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
