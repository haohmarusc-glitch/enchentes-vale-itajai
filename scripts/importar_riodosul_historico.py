#!/usr/bin/env python3
"""
Grava em `enchentes.json` o plano de inclusão de Rio do Sul — e só ele.

É o único script que escreve os picos de Rio do Sul, e escreve por decisão
explícita: a de 21/09/2026 (opção a, o maior de cada mês, segundos picos
preservados na camada bruta), que `riodosul_historico.plano_de_inclusao()`
transforma em registros. Este script não decide nada: lê o plano do JSON
convertido (`data/brutos/riodosul-historico-cheias-2026-09-21.json`) e aplica.

REGRAS
------
* Sem `--escrever` é ensaio: mostra o que entraria e não toca em nada.
* Idempotente: registro já presente com o mesmo (rio, cidade, data) e o mesmo
  `pico_m` é pulado. Rodar duas vezes dá o mesmo arquivo.
* Conflito ABORTA: mesma chave com outro `pico_m` não é sobrescrito nem
  duplicado — é a divergência que o mecanismo `divergencias` existe para
  guardar, e isso é decisão de gente, não de script.
* Nunca apaga registro. Insere no bloco de Rio do Sul, em ordem de data, e
  registra os campos novos (`chuva_mm`, `dias_de_chuva`) em `_meta.campos`.

Uso:
    python3 scripts/importar_riodosul_historico.py                 # ensaio
    python3 scripts/importar_riodosul_historico.py --escrever      # grava
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from comum import grava_json, le_json

RAIZ = Path(__file__).resolve().parent.parent
PLANO_PADRAO = RAIZ / "data" / "brutos" / "riodosul-historico-cheias-2026-09-21.json"

CAMPOS_NOVOS = {
    "chuva_mm": "Volume de chuva (mm) que a fonte associa ao pico, quando publica. Só Rio do "
                "Sul, da tabela municipal, de 1992 em diante. Ausente = a fonte não deu.",
    "dias_de_chuva": "Dias de chuva que a fonte associa ao pico, quando publica. Só Rio do Sul, "
                     "da tabela municipal. Ausente = a fonte não deu.",
}


def chave(e: dict) -> tuple:
    return (e.get("rio"), e.get("cidade"), e.get("data"))


def aplicar(base: dict, entram: list[dict]) -> dict:
    """{novos, pulados, conflitos}; altera `base` no lugar só se não houver conflito."""
    eventos = base["eventos"]
    existentes = {chave(e): e for e in eventos}
    novos, pulados, conflitos = [], [], []
    for n in entram:
        atual = existentes.get(chave(n))
        if atual is None:
            novos.append(n)
        elif abs(float(atual["pico_m"]) - float(n["pico_m"])) < 0.005:
            pulados.append(n)
        else:
            conflitos.append((atual, n))
    if conflitos:
        return {"novos": [], "pulados": pulados, "conflitos": conflitos}

    if novos:
        # o bloco de Rio do Sul é contíguo e em ordem de data; insere dentro dele
        idx = [i for i, e in enumerate(eventos) if e.get("cidade") == novos[0]["cidade"]
               and e.get("rio") == novos[0]["rio"]]
        inicio, fim = (idx[0], idx[-1] + 1) if idx else (len(eventos), len(eventos))
        bloco = sorted(eventos[inicio:fim] + novos, key=lambda e: e["data"])
        base["eventos"] = eventos[:inicio] + bloco + eventos[fim:]
        campos = base.setdefault("_meta", {}).setdefault("campos", {})
        for k, v in CAMPOS_NOVOS.items():
            campos.setdefault(k, v)
    return {"novos": novos, "pulados": pulados, "conflitos": []}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--plano", type=Path, default=PLANO_PADRAO,
                    help="JSON convertido com `plano_de_inclusao` (riodosul_historico.py --escrever)")
    ap.add_argument("--escrever", action="store_true", help="grava enchentes.json")
    args = ap.parse_args()

    plano = json.loads(args.plano.read_text(encoding="utf-8"))["plano_de_inclusao"]
    base = le_json("enchentes.json")
    antes = sum(1 for e in base["eventos"] if e.get("cidade") == "rio-do-sul")
    r = aplicar(base, plano["entram"])

    print(f"Decisão: {plano['decisao']}")
    print(f"Rio do Sul antes: {antes}  |  entram no plano: {len(plano['entram'])}  |  "
          f"pendentes na camada bruta: {len(plano['pendentes'])}")
    print(f"novos: {len(r['novos'])}  pulados (já iguais): {len(r['pulados'])}  "
          f"conflitos: {len(r['conflitos'])}")
    for atual, n in r["conflitos"]:
        print(f"  CONFLITO {n['data']}: cadastrado {atual['pico_m']} m, tabela {n['pico_m']} m "
              "— não gravado; resolver com `divergencias`, por decisão", file=sys.stderr)
    if r["conflitos"]:
        return 2
    for n in r["novos"]:
        print(f"  + {n['data']:<10} {n['pico_m']:>6.2f} m")
    if not args.escrever:
        print("\nEnsaio: nada gravado. Rode com --escrever para gravar.")
        return 0
    if not r["novos"]:
        print("\nNada a gravar: enchentes.json já tem tudo.")
        return 0
    grava_json("enchentes.json", base)
    depois = sum(1 for e in base["eventos"] if e.get("cidade") == "rio-do-sul")
    print(f"\nGravado: enchentes.json — Rio do Sul de {antes} para {depois} registros.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
