#!/usr/bin/env python3
"""Confere se dois resumos do histórico DCSC descrevem os MESMOS dados.

POR QUE EXISTE (B5). O resumo `data/brutos/dcsc-historico-resumo-2026-09-10.json` foi
gerado no PC do Jefferson. O B5 manda levar os zips para a VPS, rodar lá o
`consolidar_historico_dcsc.py` e conferir que o resultado é "IGUAL ao resumo do repo".

"Igual" conferido a olho, em 13 estações × 19 campos, é 247 comparações — e o erro que
importa é justamente o de uma linha só. Este script faz a conferência inteira e diz onde
divergiu, com os dois valores lado a lado.

O QUE PODE DIFERIR SEM SER ERRO: só `_meta.gerado_em`, que é a data da execução. Todo o
resto sai dos zips: se a entrada é a mesma, a saída tem que ser idêntica — inclusive
contagens de sentinela, buracos e cristas candidatas. **Divergência aqui é sinal de que a
entrada não é a mesma** (zip faltando, cópia truncada) ou de que o consolidador mudou de
comportamento. Nos dois casos, não commitar antes de entender.

Uso:
    python3 scripts/conferir_resumo_dcsc.py <resumo-novo.json> [<resumo-de-referência.json>]

Sem o segundo argumento, compara com o resumo mais recente já commitado em data/brutos/.
Sai com código 1 se houver qualquer divergência — serve em cron e em CI.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
BRUTOS = RAIZ / "data" / "brutos"

# Fora da comparação porque é carimbo da execução, não do dado.
IGNORAR_META = {"gerado_em"}


def referencia_mais_recente() -> Path:
    achados = sorted(BRUTOS.glob("dcsc-historico-resumo-*.json"))
    if not achados:
        sys.exit(f"erro: nenhum dcsc-historico-resumo-*.json em {BRUTOS}")
    return achados[-1]


def por_codigo(resumo: dict) -> dict[str, dict]:
    return {e["codigo"]: e for e in resumo.get("estacoes", [])}


def comparar(novo: dict, ref: dict) -> list[str]:
    """Devolve a lista de divergências, em linguagem de gente."""
    problemas: list[str] = []

    meta_n = {k: v for k, v in novo.get("_meta", {}).items() if k not in IGNORAR_META}
    meta_r = {k: v for k, v in ref.get("_meta", {}).items() if k not in IGNORAR_META}
    for chave in sorted(set(meta_n) | set(meta_r)):
        if meta_n.get(chave) != meta_r.get(chave):
            problemas.append(f"_meta.{chave}: novo={meta_n.get(chave)!r} ref={meta_r.get(chave)!r}")

    est_n, est_r = por_codigo(novo), por_codigo(ref)
    faltando = sorted(set(est_r) - set(est_n))
    sobrando = sorted(set(est_n) - set(est_r))
    for c in faltando:
        problemas.append(f"{c}: está na referência e NÃO no novo — zip faltando?")
    for c in sobrando:
        problemas.append(f"{c}: está no novo e não na referência — estação a mais")

    for codigo in sorted(set(est_n) & set(est_r)):
        a, b = est_n[codigo], est_r[codigo]
        for campo in sorted(set(a) | set(b)):
            if a.get(campo) != b.get(campo):
                va, vb = a.get(campo), b.get(campo)
                # Listas longas (cristas) não cabem na linha: resume.
                if isinstance(va, list) or isinstance(vb, list):
                    problemas.append(
                        f"{codigo}.{campo}: novo tem {len(va or [])} item(ns), "
                        f"referência tem {len(vb or [])} — e o conteúdo difere"
                    )
                else:
                    problemas.append(f"{codigo}.{campo}: novo={va!r} ref={vb!r}")
    return problemas


def main() -> int:
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    caminho_novo = Path(sys.argv[1])
    caminho_ref = Path(sys.argv[2]) if len(sys.argv) > 2 else referencia_mais_recente()

    novo = json.loads(caminho_novo.read_text())
    ref = json.loads(caminho_ref.read_text())

    print(f"novo:       {caminho_novo}")
    print(f"referência: {caminho_ref}")
    print(f"estações:   {len(novo.get('estacoes', []))} no novo, {len(ref.get('estacoes', []))} na referência")
    print()

    problemas = comparar(novo, ref)
    if not problemas:
        print("✓ IGUAL ao resumo do repo — mesmas estações, mesmas contagens, mesmas cristas.")
        print("  (só `_meta.gerado_em` difere, que é a data da execução)")
        return 0

    print(f"✗ {len(problemas)} divergência(s):\n")
    for p in problemas:
        print(f"  - {p}")
    print(
        "\nNão commite antes de entender. As duas causas prováveis são entrada diferente "
        "(zip faltando ou cópia truncada) e mudança de comportamento do consolidador."
    )
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
