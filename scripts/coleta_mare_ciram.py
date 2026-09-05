#!/usr/bin/env python3
"""
Maré MEDIDA da EPAGRI/CIRAM — a primeira do projeto, e o residual junto.

Endpoints JSON sem autenticação, achados em 04/09/2026 em
`ciram.epagri.sc.gov.br/index.php/maregrafos/`:

    https://ciram.epagri.sc.gov.br/graficos/getDataMare{N}_{ID}.php

Formato Google Charts (`{cols, rows}`), cadência 15 min, ~384 linhas cobrindo
DOIS DIAS PASSADOS E DOIS FUTUROS.

POR QUE ESTA FONTE IMPORTA
--------------------------
O projeto já tinha tábua de maré (`data/mare-itajai.json`, planilha da UNIVALI),
que é PREVISÃO astronômica. O CIRAM traz o que a tábua não tem:

* **maré observada** — medida, não prevista;
* **residual = observada − astronômica**, que é a **maré meteorológica**: o
  empilhamento de água por vento e pressão. É exatamente o que a tábua não
  prevê e o que faz a água do rio não escoar. Um residual de 30 cm somado a
  uma preamar de sizígia é a diferença entre o rio vazar e represar.

ITAJAÍ NÃO PUBLICA MARÉ OBSERVADA
---------------------------------
A estação de Itajaí (12/2921) existe na lista e devolve 384 linhas, mas ZERO
com maré observada — só astronômica e previsão MOHID. É a segunda fonte
independente a dizer isso (a primeira foi a página da Defesa Civil, com
"Nenhum dado disponível"). Por isso a referência é **Balneário Camboriú**, a
13 km — muito mais perto que Imbituba (147 km), que era a alternativa.

Quando o marégrafo do Cabeçudas (radar, QualiControl) entrar na telemetria do
município, ele vira a fonte primária e Balneário Camboriú volta a ser contexto.

AS TRÊS ARMADILHAS DESTA FONTE
------------------------------
1. **A unidade é CENTÍMETRO.** 61,80 é 0,618 m. Comparar com régua de rio sem
   dividir por 100 erra por duas ordens de grandeza. Gravamos em cm E em m,
   com o nome do campo dizendo qual é.

2. **O carimbo não traz ano nem fuso** — vem `"dd/mm HH:MM"`. Guardar assim
   quebra na virada do ano (31/12 e 01/01 na mesma série) e não casa com o
   resto do sistema. Aqui vira `medido_em` ISO no horário de BRASÍLIA sem
   fuso, que é a convenção do projeto (ver CLAUDE.md); o ano sai da distância
   até agora, não de `datetime.now().year`.

   ⚠️ O contrato do projeto é o INVERSO do que parece: carimbo sem fuso é
   **Brasília**, não UTC (CLAUDE.md, "Fuso dos carimbos"). Uma versão deste
   coletor enunciou o contrato ao contrário e gravou `medido_em_utc`
   convertendo de Brasília para UTC. É o mesmo engano que a fonte de resgate
   do AlertaBlu cometeu "para honrar o contrato", e que o CLAUDE.md registra
   como tendo custado uma sessão: o vigia passou a ver a leitura no futuro.
   Aqui `medido_em` é Brasília sem fuso, como no `coleta_itajai.py`, no
   `deBrasilia()` do site e no vigia. `coletado_em` é que é UTC.

3. **A série mistura MEDIDO e PREVISTO no mesmo vetor.** Dois dias para trás e
   dois para a frente. Ler uma linha de previsão como medição é o erro que
   faria a tela afirmar maré que ainda não aconteceu. Aqui as duas saem em
   listas SEPARADAS, e cada linha leva `medido: true|false`.

O SINAL DO RESIDUAL
-------------------
A coluna da fonte chama-se "Mare Residual (MA-MO)", que sugere astronômica
menos observada. Os números dizem o contrário: em 04/09 22:30, Balneário
Camboriú tinha observada 61,8, astronômica 45,0 e residual +16,8 — ou seja
**observada − astronômica**. Vale o número, não o rótulo. O sinal importa:
invertê-lo diria que o mar está sendo empurrado para baixo quando está sendo
empurrado para cima, que é a direção perigosa. Há teste travando isso.

Uso:
    python3 scripts/coleta_mare_ciram.py
    python3 scripts/coleta_mare_ciram.py --arquivo <json>   # sem rede
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from comum import DADOS, baixar, espera_turno, grava_json

BASE = "https://ciram.epagri.sc.gov.br/graficos/"

#: `medido_em` sem fuso é Brasília — convenção do projeto (CLAUDE.md).
FUSO_BRASILIA = ZoneInfo("America/Sao_Paulo")

#: (n, id, nome, km até Itajaí). A principal é a mais próxima COM observada.
ESTACOES = {
    "balneario-camboriu": (5, 2927, "Balneário Camboriú", 13),
    "itajai": (12, 2921, "Itajaí", 0),
    "florianopolis": (3, 2951, "Florianópolis", 78),
    "imbituba": (6, 2963, "Imbituba", 147),
}
PRINCIPAL = "balneario-camboriu"

#: Ordem das colunas no `rows[].c`, conferida contra a fonte em 04/09/2026.
COLUNAS = ("quando", "observada", "astronomica", "residual",
           "previsao_mohid", "residual_previsto", "nmm")

#: Leitura mais velha que isto não descreve o mar de agora. Estação fora do ar
#: devolve o ÚLTIMO valor antigo sem avisar, e ele parece atual: com cadência de
#: 15 min, uma hora sem leitura nova já é sinal de que a estação parou.
FRESCA_MIN = 60

#: Maré fora desta faixa (em cm) não é maré: é célula trocada ou unidade errada.
#: A maior amplitude registrada no litoral catarinense fica bem dentro disto.
MIN_CM, MAX_CM = -300.0, 300.0


def numero(celula) -> float | None:
    """Célula do Google Charts -> float. Texto que não é número vira None."""
    v = celula.get("v") if isinstance(celula, dict) else celula
    if v is None:
        return None
    s = str(v).strip()
    if s in ("", "null", "-"):
        return None
    try:
        return float(s.replace(",", "."))
    except ValueError:
        return None


def texto(celula) -> str | None:
    v = celula.get("v") if isinstance(celula, dict) else celula
    s = str(v).strip() if v is not None else ""
    return s or None


def quando_para_iso(bruto: str, agora: datetime) -> str | None:
    """
    `"04/09 22:30"` -> `"2026-09-04T22:30:00"` (Brasília, sem fuso).

    O ano NÃO vem de `agora.year`: a série cobre dois dias para cada lado, e em
    31/12 metade dela é do ano seguinte. Escolhe-se o ano que deixa a data mais
    perto de agora — com quatro dias de janela, nunca há empate.
    """
    if not bruto:
        return None
    try:
        dia_mes, hora = bruto.strip().split()
        dia, mes = (int(x) for x in dia_mes.split("/"))
        h, mi = (int(x) for x in hora.split(":"))
    except (ValueError, AttributeError):
        return None
    melhor: datetime | None = None
    for ano in (agora.year - 1, agora.year, agora.year + 1):
        try:
            d = datetime(ano, mes, dia, h, mi)
        except ValueError:
            continue  # 29/02 em ano não bissexto
        if melhor is None or abs(d - agora) < abs(melhor - agora):
            melhor = d
    return melhor.isoformat(timespec="seconds") if melhor else None


def plausivel(cm: float | None) -> bool:
    return cm is not None and MIN_CM <= cm <= MAX_CM


def idade_min(medido_em: str | None, agora: datetime) -> float | None:
    """
    Minutos entre a última medição e agora, nos DOIS em horário de Brasília.

    Converter para UTC aqui daria 180 minutos de erro — e seria o mesmo engano
    que a fonte de resgate do AlertaBlu cometeu "para honrar o contrato",
    registrado no CLAUDE.md como tendo custado uma sessão.
    """
    if not medido_em:
        return None
    try:
        return round((agora - datetime.fromisoformat(medido_em)).total_seconds() / 60.0, 1)
    except ValueError:
        return None


def converter(bruto: dict, agora: datetime) -> tuple[list[dict], list[dict]]:
    """
    Devolve (medidas, previsoes). Uma linha é MEDIDA quando traz maré observada;
    sem ela é só astronômica/modelo, isto é, previsão.

    Cada linha sai em cm E em m, com o nome do campo dizendo qual. Guardar só
    um dos dois é o caminho para alguém comparar 61,8 com uma régua em metros.
    """
    medidas: list[dict] = []
    previsoes: list[dict] = []
    for linha in bruto.get("rows") or []:
        celulas = linha.get("c") or []
        vals = dict(zip(COLUNAS, celulas + [None] * (len(COLUNAS) - len(celulas))))
        medido_em = quando_para_iso(texto(vals["quando"]) or "", agora)
        if medido_em is None:
            continue
        obs = numero(vals["observada"])
        astr = numero(vals["astronomica"])
        res = numero(vals["residual"])
        registro: dict = {"medido_em": medido_em, "medido": plausivel(obs)}
        for nome, cm in (("observada", obs), ("astronomica", astr), ("residual", res),
                         ("previsao_mohid", numero(vals["previsao_mohid"])),
                         ("nmm", numero(vals["nmm"]))):
            # Fora da faixa plausível o valor é descartado, não corrigido: um
            # número impossível vira ausência, nunca um palpite.
            ok = cm is not None and MIN_CM <= cm <= MAX_CM
            registro[f"{nome}_cm"] = cm if ok else None
            registro[f"{nome}_m"] = round(cm / 100.0, 3) if ok else None
        (medidas if registro["medido"] else previsoes).append(registro)
    return medidas, previsoes


def buscar(n: int, ident: int) -> dict:
    espera_turno()
    return json.loads(baixar(f"{BASE}getDataMare{n}_{ident}.php"))


def coletar(agora: datetime, buscador=buscar) -> dict:
    saida: dict = {
        "_meta": {
            "descricao": "Maré MEDIDA e residual (maré meteorológica) da EPAGRI/CIRAM.",
            "fonte": "EPAGRI/CIRAM — https://ciram.epagri.sc.gov.br/index.php/maregrafos/",
            "coletado_em": datetime.now(tz=FUSO_BRASILIA)
            .astimezone(ZoneInfo("UTC")).isoformat(timespec="seconds"),
            "fuso": "`medido_em` é horário de Brasília sem fuso, como o resto do projeto. "
                    "`coletado_em` é UTC — campos diferentes, não confundir.",
            "unidade": "A fonte publica em CENTÍMETROS. Cada valor sai em `_cm` e em `_m`; "
                       "comparar com régua de rio exige o `_m`.",
            "residual": "residual = observada − astronômica = maré METEOROLÓGICA (vento e pressão). "
                        "É o que a tábua astronômica não prevê e o que faz o rio não escoar. "
                        "A coluna da fonte chama-se '(MA-MO)', mas os números são observada − "
                        "astronômica; vale o número, não o rótulo.",
            "medido_vs_previsto": "A fonte devolve ~2 dias passados e ~2 futuros no MESMO vetor. "
                                  "Aqui saem separados: `medidas` (têm maré observada) e "
                                  "`previsoes` (só astronômica/MOHID). Nunca juntar.",
            "itajai_sem_observada": "A estação de Itajaí (12/2921) responde, mas sem NENHUMA maré "
                                    "observada — só astronômica e MOHID. Segunda fonte independente "
                                    "a confirmar que não há maré medida em Itajaí hoje. Por isso a "
                                    "referência é Balneário Camboriú, a 13 km.",
            "frescor": f"`fresca` é a última medição com até {FRESCA_MIN} min. A estação fora do "
                       "ar devolve o último valor antigo sem avisar, e ele parece atual — com "
                       "cadência de 15 min, uma hora sem leitura nova já é sinal de parada.",
            "estacao_principal": PRINCIPAL,
            "aviso": "Maré de outra cidade é CONTEXTO, nunca nível local. Rotular na tela com a "
                     "distância.",
        },
        "estacoes": {},
    }

    for chave, (n, ident, nome, km) in ESTACOES.items():
        try:
            bruto = buscador(n, ident)
        except Exception as e:  # noqa: BLE001 — uma estação fora não derruba as outras
            print(f"aviso: {nome} falhou ({e})", file=sys.stderr)
            continue
        medidas, previsoes = converter(bruto, agora)
        ultima = medidas[-1] if medidas else None
        idade = idade_min(ultima["medido_em"], agora) if ultima else None
        saida["estacoes"][chave] = {
            "nome": nome,
            "km_de_itajai": km,
            "endpoint": f"getDataMare{n}_{ident}.php",
            "n_medidas": len(medidas),
            "n_previsoes": len(previsoes),
            "ultima_medida": ultima,
            # Sem leitura nenhuma, `fresca` é False — nunca None disfarçado de
            # "talvez": estação muda e estação fora do ar dão a mesma tela.
            "idade_min": idade,
            "fresca": idade is not None and idade <= FRESCA_MIN,
            "medidas": medidas,
            "previsoes": previsoes,
        }
        marca = "  <- PRINCIPAL" if chave == PRINCIPAL else ""
        if ultima:
            res = ultima["residual_cm"]
            idoso = "" if (idade is not None and idade <= FRESCA_MIN) else "  [VELHA]"
            print(f"{nome:<22} {len(medidas):>3} medidas · {ultima['medido_em']}: "
                  f"{ultima['observada_cm']:.1f} cm ({ultima['observada_m']:.3f} m)"
                  f"{f' · residual {res:+.1f} cm' if res is not None else ''}"
                  f"{f' · {idade:.0f} min' if idade is not None else ''}{idoso}{marca}")
        else:
            print(f"{nome:<22} SEM maré observada ({len(previsoes)} linhas só de previsão){marca}")
    return saida


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Coleta a maré medida da EPAGRI/CIRAM.")
    p.add_argument("--arquivo", help="JSON já baixado de UMA estação, para conferir sem rede")
    a = p.parse_args(argv)

    agora = datetime.now(tz=FUSO_BRASILIA).replace(tzinfo=None)

    if a.arquivo:
        bruto = json.loads(open(a.arquivo, encoding="utf-8").read())
        medidas, previsoes = converter(bruto, agora)
        print(f"{len(medidas)} medida(s), {len(previsoes)} previsão(ões)")
        if medidas:
            print("última medida:", json.dumps(medidas[-1], ensure_ascii=False))
        return 0

    saida = coletar(agora)
    if not saida["estacoes"]:
        print("erro: nenhuma estação respondeu — nada gravado", file=sys.stderr)
        return 1
    grava_json("tempo-real/ultimo_mare_ciram.json", saida)
    print("\n-> data/tempo-real/ultimo_mare_ciram.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
