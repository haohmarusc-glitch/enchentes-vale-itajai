#!/usr/bin/env python3
"""
Diz o que a API Asthon do Alto Vale pode e o que não pode virar aviso.

`public.asthon.com.br` é a API que o portal da Defesa Civil de Rio do Sul usa.
Traz 29 estações do Alto Vale, duas barragens e histórico horário — e cobre
cidades que hoje não têm nível nenhum na nossa tela. Um dump está em
`data/brutos/rio-do-sul-asthon-2026-08-31.json`.

Este script existe porque a resposta "usar tudo" está errada de três jeitos
diferentes, e nenhum deles aparece olhando a lista de nomes.

1. **Quatro estações leem centenas de metros.** Mirim Doce 349,08 · Salete (H)
   400,4 · Petrolândia 450,74 · Atalanta (H) 454,12. Não é nível de rio; é
   altitude ou outra unidade. É o mesmo problema já visto no monitoramento da
   Defesa Civil de SC, e a resposta é a mesma: fora.

2. **Taió e Ituporanga não têm régua de cidade aqui — têm BARRAGEM.** O que a
   API publica é "Barragem Oeste Taió" e "Barragem Sul Ituporanga", nível do
   reservatório na escala do próprio barramento (a de Taió marca 9,79 m com
   atenção em 11,65 m). Mostrar isso como "o rio em Taió" seria número certo
   respondendo a pergunta errada.

3. **Cinco réguas trazem exatamente a mesma cota — 4,50 / 5,50 / 6,50.** São as
   faixas oficiais de Rio do Sul na Ponte Dom Tito Buss, repetidas em réguas de
   outros rios e até de outro município (Laurentino). Uma delas está certa: a de
   Dom Tito Buss bate com o que já temos em `estacoes.json`, por outro caminho.
   As outras quatro, até alguém confirmar, são a cota de Rio do Sul copiada — e
   aplicar a cota de uma régua a outra é o erro que o CLAUDE.md proíbe, porque
   cria alarme onde não há e cala onde há.

O que sobra de bom: **Vidal Ramos**. É régua de rio, no município de Vidal
Ramos, cabeceira do Itajaí-Mirim, uma das cidades sem nível nenhum na tela hoje.
Só que **sem cota** — dá para mostrar, nunca para disparar.

Uso:
    python3 scripts/analisar_asthon.py
"""

import json
import sys

from comum import DADOS, NIVEL_MAXIMO_M, nivel_plausivel

BRUTO = "brutos/rio-do-sul-asthon-2026-08-31.json"

#: As faixas oficiais de Rio do Sul na Ponte Dom Tito Buss, que já estão em
#: `estacoes.json` por outra fonte. Quando aparecem em OUTRA régua, é cópia até
#: prova em contrário.
COTAS_DE_RIO_DO_SUL = (4.5, 5.5, 6.5)
REGUA_DE_RIO_DO_SUL = "Ponte Dom Tito Buss"


def carregar(caminho=None) -> dict:
    caminho = caminho or (DADOS / BRUTO)
    with open(caminho, encoding="utf-8") as arquivo:
        return json.load(arquivo)


def cotas_da(estacao: dict) -> dict[str, float]:
    return {f["band_key"]: f["cota_m"] for f in (estacao.get("band_thresholds") or [])
            if isinstance(f.get("cota_m"), (int, float))}


def e_barragem(estacao: dict, dump: dict) -> bool:
    nomes = {b.get("name") for b in dump.get("dams") or []}
    return estacao.get("name") in nomes


def veredito(estacao: dict, dump: dict) -> tuple[str, str]:
    """
    O que dá para fazer com esta estação: ("aviso", "mostrar" ou "fora") e o
    porquê. É a única função deste arquivo que decide alguma coisa.
    """
    nivel = estacao.get("level_m")
    nome = estacao.get("name") or "?"

    if not isinstance(nivel, (int, float)):
        return "fora", "não publica nível"
    # A mesma régua de plausibilidade que a coleta já usa. Ter uma só evita que
    # este script aceite o que aquela recusa, ou o contrário.
    if not nivel_plausivel(nivel):
        return "fora", (f"lê {nivel:.2f} m — fora da faixa de nível de rio da bacia "
                        f"(0 a {NIVEL_MAXIMO_M:.0f} m)")
    if e_barragem(estacao, dump):
        return "fora", ("é barragem: nível de reservatório na escala do próprio "
                        "barramento, não o rio na cidade")

    cotas = cotas_da(estacao)
    if not cotas:
        return "mostrar", "sem cota nesta régua — dá para mostrar, nunca para disparar"

    trinca = tuple(round(cotas.get(k), 2) for k in ("atencao", "alerta", "emergencia")
                   if isinstance(cotas.get(k), (int, float)))
    if trinca == COTAS_DE_RIO_DO_SUL and nome != REGUA_DE_RIO_DO_SUL:
        return "mostrar", ("traz a cota de Rio do Sul (4,50/5,50/6,50) numa régua "
                           "que não é a dele — cota copiada não vira aviso")
    return "aviso", "régua com cota própria"


def main() -> int:
    dump = carregar()
    estacoes = dump.get("panel", {}).get("stations") or []
    if not estacoes:
        print("dump sem painel de estações", file=sys.stderr)
        return 1

    grupos: dict[str, list[tuple[str, str, float | None]]] = {}
    for e in estacoes:
        decisao, porque = veredito(e, dump)
        grupos.setdefault(decisao, []).append((e.get("name") or "?", porque, e.get("level_m")))

    for decisao, titulo in (("aviso", "PODE VIRAR AVISO"),
                            ("mostrar", "SÓ PARA MOSTRAR"),
                            ("fora", "FORA")):
        linhas = grupos.get(decisao) or []
        print(f"\n{titulo} — {len(linhas)}")
        for nome, porque, nivel in sorted(linhas):
            valor = f"{nivel:8.2f} m" if isinstance(nivel, (int, float)) else "       —"
            print(f"  {nome[:42]:44}{valor}  {porque}")

    print(f"\n{len(estacoes)} estações no painel. "
          "Antes de coletar: conferir robots.txt e os termos de uso de "
          "public.asthon.com.br, como em toda fonte nova.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
