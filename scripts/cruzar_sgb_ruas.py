#!/usr/bin/env python3
"""Cruza os pontos de cota de rua com o mapeamento do Serviço Geológico do Brasil (SGB): contexto, nunca cota.

POR QUE EXISTE (decisão do Jefferson de 04/11/2026, pendência 2 do relatório de ganhos: "suscetibilidade/risco do SGB
na 'minha rua' como camada de contexto"). O geoportal do SGB publica, por município, duas coisas que o projeto não
tinha: a **carta de suscetibilidade a inundação** (classes Alta/Média/Baixa, modelagem do IPT de 2013 validada em
campo, publicada em 2016–2019) e a **setorização de risco** (setores com grau Alto/Muito alto, com tipologia —
deslizamento, inundação, enxurrada… — e a data do levantamento). `baixar_sgb_suscetibilidade.py` baixa os GeoJSON
pelo GitHub Actions (branch `sondagem-fontes`); este script lê essa pasta e grava `data/sgb-ruas.json`.

O QUE ELE DIZ E O QUE NÃO DIZ.
- Para cada ponto de cota de rua COM coordenada (hoje Gaspar e Brusque; Blumenau e Rio do Sul não têm `lat`/`lon`),
  diz em que classe de suscetibilidade o ponto cai e em que setores de risco **de água** (Inundação, Enxurrada,
  Enchente, Alagamento) ele está. Setor de deslizamento não entra: não é o assunto deste site.
- É classificação do TERRENO feita pelo SGB, com os critérios e a data dele. Não é cota, não é previsão, não muda
  a cota da Defesa Civil nem a cor de nada. "Baixa" não quer dizer que não alaga; "Alta" não quer dizer que vai
  alagar hoje. A tela repete isso.
- Ponto fora de qualquer polígono fica `null` (a carta cobre o que foi mapeado). Ponto em mais de uma classe fica
  com a mais alta (acontece na borda entre polígonos).
- Resumo por cidade (todas as que o SGB cobre, com ou sem coordenada de rua): quantos polígonos de cada classe e
  quantos setores de risco de água, com o ano — para a tela dizer "o SGB mapeou X aqui" mesmo sem ponto.

Uso:
    python3 scripts/cruzar_sgb_ruas.py --sgb /caminho/da/pasta --gravar      # grava data/sgb-ruas.json
    python3 scripts/cruzar_sgb_ruas.py --sgb /caminho/da/pasta               # só imprime o resumo
A pasta é a do branch `sondagem-fontes` (sgb-*.geojson + sgb-resumo.json). Regerar quando o SGB publicar carta nova.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from comum import DADOS, grava_json, le_json  # noqa: E402

ARQUIVO = "sgb-ruas.json"
BASE = "https://geoportal.sgb.gov.br/server/rest/services/gestaoterritorial"
#: Tipologias dos setores de risco que falam de água. O resto (Deslizamento, Rastejo, Queda, Erosão, Colapso) fica fora.
TIPOLOGIAS_DE_AGUA = ("Inundação", "Enxurrada", "Enchente", "Alagamento")
ORDEM_CLASSE = {"Alta": 3, "Média": 2, "Baixa": 1}
ORDEM_GRAU = {"Muito alto": 4, "Alto": 3, "Médio": 2, "Baixo": 1}

Coordenada = tuple[float, float]


# --- geometria (a mesma conta de `web/src/logica/pontoNaMancha.ts`: semirreta para a direita, ímpar é dentro)

def dentro_do_anel(ponto: Coordenada, anel: list) -> bool:
    x, y = ponto
    dentro = False
    j = len(anel) - 1
    for i in range(len(anel)):
        xi, yi = anel[i][0], anel[i][1]
        xj, yj = anel[j][0], anel[j][1]
        if (yi > y) != (yj > y) and x < (xj - xi) * (y - yi) / (yj - yi) + xi:
            dentro = not dentro
        j = i
    return dentro


def dentro_do_poligono(ponto: Coordenada, poligono: list) -> bool:
    if not poligono or not dentro_do_anel(ponto, poligono[0]):
        return False
    return not any(dentro_do_anel(ponto, buraco) for buraco in poligono[1:])


def caixa(geometria: dict) -> tuple[float, float, float, float]:
    xs: list[float] = []
    ys: list[float] = []
    pols = [geometria["coordinates"]] if geometria.get("type") == "Polygon" else geometria.get("coordinates") or []
    for pol in pols:
        for anel in pol:
            for c in anel:
                xs.append(c[0])
                ys.append(c[1])
    return min(xs), min(ys), max(xs), max(ys)


def dentro_da_geometria(ponto: Coordenada, geometria: dict) -> bool:
    tipo = geometria.get("type")
    if tipo == "Polygon":
        return dentro_do_poligono(ponto, geometria["coordinates"])
    if tipo == "MultiPolygon":
        return any(dentro_do_poligono(ponto, p) for p in geometria["coordinates"])
    return False


class Camada:
    """Feições com caixa envolvente pré-calculada, para não testar cada polígono contra cada ponto."""

    def __init__(self, geojson: dict):
        self.itens = []
        for f in geojson.get("features") or []:
            g = f.get("geometry")
            if not g or g.get("type") not in ("Polygon", "MultiPolygon"):
                continue
            self.itens.append((caixa(g), g, f.get("properties") or {}))

    def contendo(self, ponto: Coordenada) -> list[dict]:
        x, y = ponto
        return [p for (x0, y0, x1, y1), g, p in self.itens if x0 <= x <= x1 and y0 <= y <= y1 and dentro_da_geometria(ponto, g)]


# --- leitura dos atributos do SGB

def data_do_setor(valor) -> str | None:
    """`data_setor` vem em milissegundos desde 1970 (UTC). Vira AAAA-MM-DD; ano solto fica como está."""
    if isinstance(valor, (int, float)) and valor > 10**11:
        return datetime.fromtimestamp(valor / 1000, tz=timezone.utc).date().isoformat()
    if isinstance(valor, (int, float)):
        return str(int(valor))
    if isinstance(valor, str) and valor.strip():
        return valor.strip()
    return None


def tipologias_do_setor(p: dict) -> list[str]:
    return [str(p.get(f"tipolo_g{i}")).strip() for i in range(1, 6) if str(p.get(f"tipolo_g{i}") or "").strip()]


def setor_de_agua(p: dict) -> bool:
    return any(t in TIPOLOGIAS_DE_AGUA for t in tipologias_do_setor(p))


def suscetibilidade_do_ponto(camada: Camada, ponto: Coordenada) -> dict | None:
    achados = camada.contendo(ponto)
    if not achados:
        return None
    melhor = max(achados, key=lambda p: ORDEM_CLASSE.get(str(p.get("classe")), 0))
    return {"classe": melhor.get("classe"), "ano": melhor.get("ano"), "executor": melhor.get("executor") or melhor.get("execucao")}


def riscos_do_ponto(camada: Camada, ponto: Coordenada) -> list[dict]:
    saida = []
    for p in camada.contendo(ponto):
        if not setor_de_agua(p):
            continue
        saida.append({"setor": p.get("num_setor"), "grau": p.get("grau_risco"),
                      "tipologias": [t for t in tipologias_do_setor(p) if t in TIPOLOGIAS_DE_AGUA],
                      "data": data_do_setor(p.get("data_setor")), "local": (p.get("local") or "").strip() or None})
    saida.sort(key=lambda r: -ORDEM_GRAU.get(str(r["grau"]), 0))
    return saida


def resumo_da_camada(nome: str, geojson: dict) -> dict:
    feicoes = geojson.get("features") or []
    if nome == "inundacao":
        classes: dict[str, int] = {}
        anos: set[str] = set()
        for f in feicoes:
            p = f.get("properties") or {}
            classes[str(p.get("classe"))] = classes.get(str(p.get("classe")), 0) + 1
            if p.get("ano"):
                anos.add(str(p["ano"]))
        return {"poligonos": len(feicoes), "classe": classes, "anos": sorted(anos)}
    graus: dict[str, int] = {}
    anos = set()
    agua = 0
    for f in feicoes:
        p = f.get("properties") or {}
        if not setor_de_agua(p):
            continue
        agua += 1
        graus[str(p.get("grau_risco"))] = graus.get(str(p.get("grau_risco")), 0) + 1
        d = data_do_setor(p.get("data_setor"))
        if d:
            anos.add(d[:4])
    return {"setores": len(feicoes), "setores_de_agua": agua, "grau": graus, "anos": sorted(anos)}


# --- o cruzamento

def cruzar(cotas: list[dict], pasta: Path, resumo_sgb: dict) -> dict:
    cidades: dict[str, dict] = {}
    for servico in ("inundacao", "risco"):
        for cidade_nome, info in (resumo_sgb.get("servicos", {}).get(servico, {}).get("cidades") or {}).items():
            arquivo = pasta / info["arquivo"]
            if not arquivo.exists():
                continue
            cid = info["arquivo"].removeprefix(f"sgb-{servico}-").removesuffix(".geojson")
            geojson = json.loads(arquivo.read_text(encoding="utf-8"))
            bloco = cidades.setdefault(cid, {"nome": cidade_nome, "camadas": {}, "pontos": []})
            bloco["camadas"][servico] = {**resumo_da_camada(servico, geojson), "arquivo": info["arquivo"], "sha256": info["sha256"],
                                         "nome_no_sgb": info.get("nome_no_sgb")}
            bloco.setdefault("_camada_" + servico, Camada(geojson))
    for c in cotas:
        if c.get("lat") is None or c.get("lon") is None or c["cidade"] not in cidades:
            continue
        bloco = cidades[c["cidade"]]
        ponto = (float(c["lon"]), float(c["lat"]))
        susc = suscetibilidade_do_ponto(bloco["_camada_inundacao"], ponto) if "_camada_inundacao" in bloco else None
        riscos = riscos_do_ponto(bloco["_camada_risco"], ponto) if "_camada_risco" in bloco else []
        bloco["pontos"].append({"rua": c["rua"], "bairro": c.get("bairro"), "ponto": c.get("ponto"), "lat": c["lat"], "lon": c["lon"],
                                "suscetibilidade": susc, "risco": riscos})
    for bloco in cidades.values():
        for k in [k for k in bloco if k.startswith("_camada_")]:
            del bloco[k]
        contagem: dict[str, int] = {}
        for p in bloco["pontos"]:
            chave = (p["suscetibilidade"] or {}).get("classe") or "fora da carta"
            contagem[chave] = contagem.get(chave, 0) + 1
        bloco["pontos_por_classe"] = contagem
        bloco["pontos_em_setor_de_risco"] = sum(1 for p in bloco["pontos"] if p["risco"])
    return dict(sorted(cidades.items()))


def montar(cidades: dict, resumo_sgb: dict) -> dict:
    return {
        "_meta": {
            "descricao": "Contexto do Serviço Geológico do Brasil (SGB) para os pontos de cota de rua: classe de suscetibilidade a "
                         "inundação do terreno e setores de risco de água (inundação, enxurrada, enchente, alagamento) em que cada "
                         "ponto cai. Derivado: gerado por scripts/cruzar_sgb_ruas.py a partir dos GeoJSON do geoportal do SGB.",
            "fonte": "Serviço Geológico do Brasil — geoportal, serviços gestaoterritorial/inundacao (Cartas de Suscetibilidade a "
                     "Movimentos Gravitacionais de Massa e Inundações, tema Inundação; modelagem IPT 2013 validada em campo) e "
                     "gestaoterritorial/risco (Setorização de Risco Geológico)",
            "fonte_urls": [f"{BASE}/inundacao/MapServer/0", f"{BASE}/risco/MapServer/0"],
            "acesso": {"quando": resumo_sgb.get("gerado_em"), "como": "GitHub Actions (sondar-fontes.yml), branch sondagem-fontes, "
                                                                     "só GET depois do robots.txt (404 = nada proibido)"},
            "gerado_em": datetime.now(tz=timezone.utc).isoformat(timespec="seconds"),
            "regras": [
                "É classificação do TERRENO pelo SGB, com os critérios e a data dele: não é cota, não é previsão, não muda a cota "
                "da Defesa Civil nem a cor de nada no site.",
                "'Baixa' não quer dizer que não alaga; 'Alta' não quer dizer que vai alagar hoje. Ponto fora da carta é null, "
                "não 'sem risco'.",
                "Só setores de risco de ÁGUA entram (" + ", ".join(TIPOLOGIAS_DE_AGUA) + "); deslizamento e afins ficam fora.",
                "Ponto em mais de uma classe fica com a mais alta (borda entre polígonos).",
                "Só pontos com lat/lon em data/cotas-ruas.json (hoje Gaspar e Brusque). Blumenau e Rio do Sul têm só o resumo da cidade.",
                "Não é alerta. Em emergência, ligue 199.",
            ],
            "campos": {
                "camadas.inundacao": "polígonos da carta por classe, anos de publicação, arquivo e sha256 do GeoJSON lido",
                "camadas.risco": "setores da setorização; setores_de_agua são os que entram; grau só deles",
                "pontos[].suscetibilidade": "{classe, ano, executor} do polígono que contém o ponto, ou null",
                "pontos[].risco": "setores de água que contêm o ponto: {setor, grau, tipologias, data, local}",
                "pontos_por_classe": "quantos pontos da cidade caem em cada classe (ou 'fora da carta')",
            },
        },
        "cidades": cidades,
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    ap.add_argument("--sgb", type=Path, required=True, help="pasta com sgb-*.geojson e sgb-resumo.json (branch sondagem-fontes)")
    ap.add_argument("--gravar", action="store_true", help=f"grava data/{ARQUIVO}")
    a = ap.parse_args(argv)
    resumo_sgb = json.loads((a.sgb / "sgb-resumo.json").read_text(encoding="utf-8"))
    cotas = le_json("cotas-ruas.json")["cotas"]
    cidades = cruzar(cotas, a.sgb, resumo_sgb)
    for cid, b in cidades.items():
        cam = b["camadas"]
        inund = cam.get("inundacao", {})
        risco = cam.get("risco", {})
        print(f"{b['nome']}: carta {inund.get('classe', '—')} {inund.get('anos', '')} · risco de água {risco.get('setores_de_agua', 0)}/"
              f"{risco.get('setores', 0)} setores {risco.get('grau', '')} · {len(b['pontos'])} pontos: {b['pontos_por_classe']}, "
              f"{b['pontos_em_setor_de_risco']} em setor de risco")
    if a.gravar:
        grava_json(ARQUIVO, montar(cidades, resumo_sgb))
        print(f"→ {DADOS / ARQUIVO}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
