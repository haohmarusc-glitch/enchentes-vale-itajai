#!/usr/bin/env python3
"""
Prova (ou desmente) que a régua de onde vem a COTA é a mesma de onde vem a
LEITURA — lendo as duas fontes no MESMO instante e comparando o número.

POR QUE ESTE SCRIPT EXISTE (04/09/2026)
---------------------------------------
Cota e leitura quase sempre vêm de páginas ou endpoints DIFERENTES, e nome
igual não prova régua igual. Três coisas mostraram isso no mesmo dia:

* **Rio do Sul** — 88 de 88 leituras das últimas 48 h ficaram ACIMA da cota de
  atenção (mínimo 0,83 m acima). A cota 4,50/5,50/6,50 é da **Ponte Dom Tito
  Buss**; a leitura vem da **Estação MKS**, por outra página (a da Defesa Civil
  de *Itajaí*). O rio nunca desce até o limiar — a cabeceira do Açu fica
  permanentemente amarela no mapa.
* **As onze de Itajaí** — a página que o coletor lê (`/monitoramento/nivel-rios`)
  não publica cota nenhuma; elas vêm do Plano de Contingência.
* **`analisar_asthon.py`** já registrava as faixas de Dom Tito Buss aparecendo
  copiadas em quatro outras réguas, com a regra: aplicar a cota de uma régua a
  outra "cria alarme onde não há e cala onde há".

O MÉTODO
--------
Ler as duas fontes no mesmo instante e comparar o nível. Igual (a menos da
tolerância) = mesma régua. Diferente = réguas diferentes, e a cota não vale
para aquela leitura.

A TOLERÂNCIA NÃO É CHUTE
------------------------
`TOLERANCIA_M` é 0,10 m, e o número saiu de medição: as duas publicações de
Blumenau (Defesa Civil de Itajaí e AlertaBlu), que cobrem a MESMA régua
(estação ANA 83800002), divergem em mediana +0,065 m e máximo +0,245 m. Ou
seja, mesma régua já diverge ~6 cm entre fontes. Abaixo de 0,10 m é
indistinguível; acima de 0,50 m (`CERTEZA_M`) não há como ser a mesma régua.
Entre os dois, o veredito é "não dá para dizer" — e "não sei" é resposta.

O SCRIPT NÃO GRAVA NADA. Ele responde uma pergunta; mudar cota ou quem dispara
aviso é decisão de quem mantém o projeto.

Uso:
    python3 scripts/conferir_par_regua.py rio-do-sul
    python3 scripts/conferir_par_regua.py --listar
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime

from comum import DADOS, baixar

ULTIMO = DADOS / "tempo-real" / "ultimo.json"

#: Mesma régua já diverge ~6 cm entre duas publicações (medido em Blumenau).
TOLERANCIA_M = 0.10
#: Acima disto não há como ser a mesma régua.
CERTEZA_M = 0.50
#: Leituras separadas por mais que isto não se comparam: numa cheia o rio sobe
#: nesse tempo, e a diferença sairia parte régua, parte subida. É a mesma regra
#: que o `gaspar_estadual.py` já usa.
MAX_MINUTOS_ENTRE = 30.0

#: Os pares a conferir: cidade -> (de onde vem a COTA, como buscá-la).
#: Lista fechada de propósito — cada par entra depois de alguém confirmar que
#: as duas fontes falam do mesmo ponto do rio.
PARES = {
    "rio-do-sul": {
        "regua_da_cota": "Ponte Dom Tito Buss",
        "por_que": (
            "As cotas 4,50 / 5,50 / 6,50 em estacoes.json são desta régua "
            "(campo `regua` da cidade). A leitura ao vivo chega como "
            "'Rio do Sul Estação MKS', por outra página."
        ),
        "fonte": "asthon-panel",
        "url": "https://public.asthon.com.br/public/panel?city_id=4214805",
        "casa_nome": "Tito",
    },
}


def nivel_da_asthon(corpo: str, casa_nome: str) -> tuple[float, str] | None:
    """(nível, carimbo) da estação cujo nome contém `casa_nome`, ou None."""
    try:
        d = json.loads(corpo)
    except ValueError:
        return None
    for e in d.get("stations", []) or []:
        if casa_nome.lower() in str(e.get("name", "")).lower():
            nivel = e.get("level_m")
            if isinstance(nivel, (int, float)):
                return float(nivel), str(e.get("last_reading_at") or "")
    return None


def nossa_leitura(cidade: str, ultimo: dict) -> tuple[float, str, str] | None:
    """(nível, carimbo, título) da leitura que o COLETOR usa para esta cidade."""
    for l in ultimo.get("leituras", []) or []:
        if l.get("cidade") == cidade and isinstance(l.get("nivel_m"), (int, float)):
            return float(l["nivel_m"]), str(l.get("medido_em") or ""), str(l.get("estacao") or "")
    return None


def minutos_entre(a: str, b: str) -> float | None:
    """Distância em minutos entre dois carimbos ISO, ou None se não der para ler."""
    def ler(s: str):
        s = s.strip().replace("Z", "+00:00")
        try:
            d = datetime.fromisoformat(s)
        except ValueError:
            return None
        return d.replace(tzinfo=None) if d.tzinfo else d
    x, y = ler(a), ler(b)
    if x is None or y is None:
        return None
    return abs((x - y).total_seconds()) / 60


def veredito(diferenca_m: float) -> tuple[str, str]:
    """(resposta, porquê). Três respostas possíveis, e uma delas é 'não sei'."""
    d = abs(diferenca_m)
    if d <= TOLERANCIA_M:
        return ("MESMA RÉGUA",
                f"as duas fontes diferem {d:.2f} m, dentro dos {TOLERANCIA_M:.2f} m "
                "que duas publicações da mesma régua já divergem (medido em Blumenau)")
    if d >= CERTEZA_M:
        return ("RÉGUAS DIFERENTES",
                f"as duas fontes diferem {d:.2f} m — acima de {CERTEZA_M:.2f} m não há "
                "como ser o mesmo ponto do rio. A cota de uma NÃO vale para a outra")
    return ("NÃO DÁ PARA DIZER",
            f"a diferença ({d:.2f} m) está entre a tolerância e a certeza. "
            "Repita em outro instante, de preferência com o rio parado")


def conferir(cidade: str, ultimo: dict, corpo_fonte: str) -> dict:
    par = PARES[cidade]
    nosso = nossa_leitura(cidade, ultimo)
    if not nosso:
        return {"erro": f"nenhuma leitura de {cidade} em ultimo.json"}
    nivel_nosso, quando_nosso, titulo_nosso = nosso

    outro = nivel_da_asthon(corpo_fonte, par["casa_nome"])
    if not outro:
        return {"erro": f"a fonte da cota não trouxe '{par['regua_da_cota']}'"}
    nivel_outro, quando_outro = outro

    saida = {
        "cidade": cidade,
        "regua_da_cota": par["regua_da_cota"],
        "nivel_da_cota_m": nivel_outro, "quando_cota": quando_outro,
        "regua_da_leitura": titulo_nosso,
        "nivel_da_leitura_m": nivel_nosso, "quando_leitura": quando_nosso,
        "diferenca_m": round(nivel_outro - nivel_nosso, 3),
    }
    minutos = minutos_entre(quando_outro, quando_nosso)
    saida["minutos_entre"] = None if minutos is None else round(minutos, 1)
    if minutos is not None and minutos > MAX_MINUTOS_ENTRE:
        saida["resposta"] = "NÃO DÁ PARA DIZER"
        saida["porque"] = (
            f"as duas leituras estão a {minutos:.0f} min uma da outra, mais que os "
            f"{MAX_MINUTOS_ENTRE:.0f} min do limite. Numa cheia o rio sobe nesse "
            "tempo, e a diferença sairia parte régua, parte subida"
        )
        return saida
    saida["resposta"], saida["porque"] = veredito(saida["diferenca_m"])
    return saida


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("cidade", nargs="?", help="cidade do par a conferir")
    ap.add_argument("--listar", action="store_true", help="mostra os pares cadastrados")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    if args.listar or not args.cidade:
        print("Pares cadastrados:\n")
        for c, p in PARES.items():
            print(f"  {c}\n    cota vem de: {p['regua_da_cota']}\n    {p['por_que']}\n")
        return 0
    if args.cidade not in PARES:
        print(f"'{args.cidade}' não está na lista. Use --listar.", file=sys.stderr)
        return 1
    if not ULTIMO.exists():
        print(f"{ULTIMO} não existe — rode a coleta antes.", file=sys.stderr)
        return 1

    par = PARES[args.cidade]
    try:
        corpo = baixar(par["url"])
    except Exception as e:  # noqa: BLE001 — qualquer falha de rede vira relato, não traceback
        print(f"não deu para ler a fonte da cota: {e}", file=sys.stderr)
        return 1

    r = conferir(args.cidade, json.loads(ULTIMO.read_text(encoding="utf-8")), corpo)
    if args.json:
        print(json.dumps(r, ensure_ascii=False, indent=2))
        return 0 if r.get("resposta") == "MESMA RÉGUA" else 1
    if "erro" in r:
        print(r["erro"], file=sys.stderr)
        return 1

    print(f"{r['cidade']}\n")
    print(f"  régua da COTA      {r['regua_da_cota']}")
    print(f"                     {r['nivel_da_cota_m']:.2f} m  em {r['quando_cota']}")
    print(f"  régua da LEITURA   {r['regua_da_leitura']}")
    print(f"                     {r['nivel_da_leitura_m']:.2f} m  em {r['quando_leitura']}")
    print(f"\n  diferença          {r['diferenca_m']:+.2f} m"
          f"   ({r['minutos_entre']} min entre as leituras)")
    print(f"\n  → {r['resposta']}\n    {r['porque']}\n")
    if r["resposta"] == "RÉGUAS DIFERENTES":
        print("  A cota cadastrada NÃO descreve a régua que o site mostra. Nada foi\n"
              "  alterado — mudar cota é decisão de quem mantém o projeto.")
    return 0 if r["resposta"] == "MESMA RÉGUA" else 1


if __name__ == "__main__":
    raise SystemExit(main())
