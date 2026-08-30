#!/usr/bin/env python3
"""
Baixa as manchas de inundação de Itajaí publicadas pela própria prefeitura.

A prefeitura de Itajaí mantém a organização GeoItajaí no GitHub, e o
repositório `geoitajai/sie` traz, sob licença MIT, os polígonos das áreas
atingidas em nove eventos entre 1983 e 2015. É dado oficial, aberto e
reutilizável — o oposto do resto do que este projeto coleta, que é raspado de
página HTML.

Dois tipos de arquivo:

* `enchenteAAAA` — a mancha total do evento, sem atributo nenhum;
* `inundaMÊSAAAA` — polígonos com `situa`, a **profundidade da lâmina d'água**
  por trecho. É o dado mais útil: não diz só "aqui alagou", diz "aqui a água
  bateu entre 40 e 60 cm".

O QUE ESTE SCRIPT NÃO FAZ: ligar polígono a nível de rio. Os arquivos não
trazem cota, e inventar essa ligação seria o erro mais grave possível aqui —
alguém olharia o mapa de 2011 e concluiria que a sua rua alaga a tal metro. A
ligação evento → pico é feita pela DATA, cruzando com `data/enchentes.json`, e
só aparece quando o pico daquele evento estiver registrado lá.

Idempotente: só baixa o que falta, a não ser com `--forcar`.

Uso:
    python3 scripts/baixar_manchas_itajai.py
    python3 scripts/baixar_manchas_itajai.py --forcar
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

from comum import DADOS, baixar, espera_turno, le_json

BASE = "https://raw.githubusercontent.com/geoitajai/sie/master/data"
REPO = "https://github.com/geoitajai/sie"
LICENCA = "MIT"
DESTINO = DADOS / "manchas" / "itajai"

#: (arquivo, data do evento, o que é). A data é o que liga a mancha ao pico
#: registrado em enchentes.json — quando ele existir.
ARQUIVOS: list[tuple[str, str, str]] = [
    ("enchente1983.geojson", "1983-07", "mancha total"),
    ("enchente1984.geojson", "1984-08", "mancha total"),
    ("enchente2001.geojson", "2001", "mancha total"),
    ("enchente2008.geojson", "2008-11", "mancha total"),
    ("enchente2011.geojson", "2011-09", "mancha total"),
    ("inundasetembro2011.geojson", "2011-09", "lâmina d'água"),
    ("inundajulho2013.geojson", "2013-07", "lâmina d'água"),
    ("inundasetembro2013.geojson", "2013-09", "lâmina d'água"),
    ("inundajunho2014.geojson", "2014-06", "lâmina d'água"),
    ("inundaoutubro2015.geojson", "2015-10", "lâmina d'água"),
]

RE_FAIXA = re.compile(r"^\s*([\d,]+)\s*(?:a\s*([\d,]+))?\s*$")


def faixa_da_lamina(situa: str) -> tuple[float | None, float | None]:
    """
    Converte a classe de lâmina em metros. `0,41 a 0,60` -> (0.41, 0.60).

    Classe de valor único (`0,20`) vira (None, 0.20): a fonte escreve o topo da
    faixa, e supor um piso seria inventar. Texto irreconhecível vira (None, None)
    em vez de zero — zero de lâmina significaria "não alagou".
    """
    m = RE_FAIXA.match(situa or "")
    if not m:
        return None, None
    def num(s: str | None) -> float | None:
        return float(s.replace(",", ".")) if s else None
    a, b = num(m.group(1)), num(m.group(2))
    return (a, b) if b is not None else (None, a)


def resumo_do_arquivo(caminho: Path) -> dict:
    """Lê o GeoJSON e descreve o que ele tem, sem confiar no que eu supus."""
    dados = json.loads(caminho.read_text(encoding="utf-8"))
    feicoes = dados.get("features") or []
    classes: dict[str, tuple[float | None, float | None]] = {}
    for f in feicoes:
        situa = (f.get("properties") or {}).get("situa")
        if isinstance(situa, str) and situa not in classes:
            classes[situa] = faixa_da_lamina(situa)

    # A fonte publica classes que se sobrepõem (em 2015, "0,41 a 0,60" e
    # "0,51 a 1"). Não se conserta calando: quem olhar o mapa precisa saber.
    # Classe de valor único ("0,20") é a faixa de 0 até 0,20 — é assim que a
    # fonte a usa, como a mais rasa. Por isso o piso ausente vira 0 aqui, só
    # para ordenar e comparar; no índice ele continua null, que é a verdade.
    faixas = sorted(
        ((mn if mn is not None else 0.0), mx)
        for mn, mx in classes.values() if mx is not None
    )
    sobrepostas = any(b[0] < a[1] for a, b in zip(faixas, faixas[1:]))

    return {
        "feicoes": len(feicoes),
        "geometrias": sorted({(f.get("geometry") or {}).get("type") for f in feicoes if f.get("geometry")}),
        "crs": ((dados.get("crs") or {}).get("properties") or {}).get("name"),
        "classes_lamina": [
            {"rotulo": rotulo, "lamina_min_m": mn, "lamina_max_m": mx}
            for rotulo, (mn, mx) in sorted(classes.items())
        ],
        "classes_sobrepostas": sobrepostas,
    }


def pico_registrado(eventos: list[dict], data: str) -> dict | None:
    """O pico de Itajaí naquele evento, se já estiver em enchentes.json."""
    for e in eventos:
        if e.get("cidade") != "itajai":
            continue
        if str(e.get("data", "")).startswith(data):
            return {"data": e["data"], "pico_m": e.get("pico_m"), "fonte": e.get("fonte")}
    return None


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--forcar", action="store_true", help="baixa de novo o que já existe")
    args = ap.parse_args()

    DESTINO.mkdir(parents=True, exist_ok=True)
    eventos = le_json("enchentes.json")["eventos"]

    indice = []
    baixados = pulados = 0
    for arquivo, data, tipo in ARQUIVOS:
        alvo = DESTINO / arquivo
        if alvo.exists() and not args.forcar:
            pulados += 1
        else:
            espera_turno()
            try:
                conteudo = baixar(f"{BASE}/{arquivo}")
            except Exception as e:
                print(f"ERRO em {arquivo}: {e}", file=sys.stderr)
                return 1
            try:
                json.loads(conteudo)  # não grava lixo por cima de arquivo bom
            except ValueError as e:
                print(f"ERRO: {arquivo} não é JSON válido: {e}", file=sys.stderr)
                return 1
            alvo.write_text(conteudo, encoding="utf-8")
            baixados += 1

        resumo = resumo_do_arquivo(alvo)
        indice.append({
            "cidade": "itajai",
            "evento": data,
            "tipo": tipo,
            "arquivo": f"manchas/itajai/{arquivo}",
            "tem_lamina": bool(resumo["classes_lamina"]),
            "pico_registrado": pico_registrado(eventos, data),
            "licenca": LICENCA,
            "fonte": f"{REPO} (GeoItajaí / Prefeitura de Itajaí)",
            **resumo,
        })

    (DADOS / "manchas" / "index.json").write_text(
        json.dumps({
            "_meta": {
                "descricao": "Manchas de inundação históricas, por evento.",
                "aviso": (
                    "Os polígonos NÃO trazem nível de rio. A ligação com o pico é feita "
                    "pela data, e só aparece quando o pico daquele evento está registrado "
                    "em enchentes.json. Mancha não é previsão: mostra onde a água chegou "
                    "naquele evento, com a cidade que existia naquele ano."
                ),
                "licenca": LICENCA,
                "fonte": REPO,
            },
            "manchas": indice,
        }, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    print(f"{baixados} baixado(s), {pulados} já existia(m).")
    com_pico = sum(1 for m in indice if m["pico_registrado"])
    print(f"{len(indice)} manchas no índice; {com_pico} com pico de Itajaí registrado.")
    if com_pico < len(indice):
        print(f"AVISO: {len(indice) - com_pico} evento(s) sem pico em enchentes.json — "
              "a legenda do mapa fica sem o nível do rio até alguém levantar.")
    for m in indice:
        if m["classes_sobrepostas"]:
            print(f"AVISO: {m['arquivo']} tem classes de lâmina que se sobrepõem "
                  f"na fonte: {[c['rotulo'] for c in m['classes_lamina']]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
