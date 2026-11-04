#!/usr/bin/env python3
"""Baixa, do geoportal do SGB/CPRM, a suscetibilidade a inundação e a setorização de risco das cidades da bacia.

POR QUE EXISTE (varredura de 04/11/2026, `docs/VARREDURA-FONTES-2026-11-04-NAVEGADOR.md`, seção 4). O geoportal
do SGB (ArcGIS Server) tem dois serviços com consulta por atributo:
  * `gestaoterritorial/inundacao/MapServer/0` — suscetibilidade a inundação (classes Alta/Média/Baixa), com
    `uf, municipio, processo, classe, fonte, ano, executor`; na bacia há Apiúna, Benedito Novo, Blumenau,
    Brusque, Gaspar, Ilhota, Itajaí, José Boiteux, Luiz Alves, Navegantes, Rodeio, Taió e Timbó;
  * `gestaoterritorial/risco/MapServer/0` — setores de risco alto/muito alto (`munic, num_setor, data_setor,
    local, grau_risco, num_pess, …`), com Ascurra, Brusque, Gaspar, Ilhota, Indaial, Itajaí, Navegantes,
    Pomerode, Rio do Sul, Timbó.

POR QUE NO ACTIONS. O host não responde ao ambiente das sessões de código; o runner do GitHub alcança. O
resultado vai para o branch `sondagem-fontes` (ver `.github/workflows/sondar-fontes.yml`), nunca para o main.

O QUE É E O QUE NÃO É. Suscetibilidade e setorização são **contexto**: dizem onde o terreno tende a alagar e
onde há risco alto mapeado, não em que cota a água chega nem o que vai acontecer. Nada daqui vira faixa, cota,
previsão ou aviso (regra 4 do handoff de 04/11/2026). Decidir se e como aparece na "minha rua" é do Jefferson.

Uso:
    python3 scripts/baixar_sgb_suscetibilidade.py --saida pasta/ [--relatorio resumo.json]
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import unicodedata
import urllib.parse
import urllib.robotparser
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from comum import USER_AGENT, baixar  # noqa: E402

BASE = "https://geoportal.sgb.gov.br/server/rest/services/gestaoterritorial"
ROBOTS = "https://geoportal.sgb.gov.br/robots.txt"
SERVICOS = {
    # nome → (camada, campo do município, filtro extra)
    "inundacao": (f"{BASE}/inundacao/MapServer/0", "municipio", "uf='SC'"),
    "risco": (f"{BASE}/risco/MapServer/0", "munic", None),
}
#: As cidades do projeto e as vizinhas da bacia que o SGB cobre (lista fechada; nome como o IBGE escreve).
CIDADES = ("Apiúna", "Ascurra", "Benedito Novo", "Blumenau", "Botuverá", "Brusque", "Gaspar", "Guabiruba",
           "Ibirama", "Ilhota", "Indaial", "Itajaí", "Ituporanga", "José Boiteux", "Lontras", "Luiz Alves",
           "Navegantes", "Pomerode", "Rio do Sul", "Rio dos Cedros", "Rodeio", "Taió", "Timbó",
           "Trombudo Central", "Vidal Ramos")


def normal(nome: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", nome or "") if unicodedata.category(c) != "Mn").strip().lower()


def robots_libera(texto_robots: str) -> bool:
    rp = urllib.robotparser.RobotFileParser()
    rp.parse(texto_robots.splitlines())
    return rp.can_fetch(USER_AGENT, BASE + "/inundacao/MapServer/0/query")


def _status_http(e: BaseException) -> int | None:
    """O status da resposta que causou a exceção. `comum.baixar` reembrulha o HTTPError num RequestException sem
    `response` (a 2ª rodada na Actions ainda leu o 404 como "sem resposta"): procura na cadeia de causas."""
    visto: BaseException | None = e
    while visto is not None:
        status = getattr(getattr(visto, "response", None), "status_code", None)
        if isinstance(status, int):
            return status
        visto = visto.__cause__ or visto.__context__
    return None


def robots_do_geoportal(baixar_fn=None) -> tuple[bool, str]:
    """(pode pedir?, motivo). O geoportal NÃO publica robots.txt (404 na Actions em 04/11/2026): 404 é "nada
    proibido", como em `sondar_fontes._robots` — a primeira rodada tratou o 404 como "sem resposta" e não pediu
    nada. Qualquer outra falha continua fechando tudo: na dúvida não se pede."""
    baixar_fn = baixar_fn or baixar
    try:
        texto = baixar_fn(ROBOTS)
    except Exception as e:  # noqa: BLE001
        if _status_http(e) == 404:
            return True, "robots.txt não existe (404): nada proibido"
        return False, f"robots.txt sem resposta ({e}); nada pedido"
    if robots_libera(texto):
        return True, "robots.txt permite a consulta"
    return False, "robots.txt do geoportal não permite a consulta; nada pedido"


def url_distintos(camada: str, campo: str, filtro: str | None) -> str:
    q = {"where": filtro or "1=1", "outFields": campo, "returnDistinctValues": "true", "returnGeometry": "false",
         "f": "json"}
    return f"{camada}/query?{urllib.parse.urlencode(q)}"


def url_feicoes(camada: str, campo: str, nome: str, filtro: str | None) -> str:
    where = f"{campo}='{nome.replace(chr(39), chr(39) * 2)}'"
    if filtro:
        where = f"{filtro} AND {where}"
    q = {"where": where, "outFields": "*", "returnGeometry": "true", "outSR": "4326", "f": "geojson"}
    return f"{camada}/query?{urllib.parse.urlencode(q)}"


def nomes_na_bacia(distintos: dict, campo: str) -> dict[str, str]:
    """Nome como o SGB escreve → nome do projeto, só para as cidades da lista. Sem adivinhar por parecido."""
    nossos = {normal(c): c for c in CIDADES}
    achados: dict[str, str] = {}
    for f in distintos.get("features") or []:
        valor = (f.get("attributes") or {}).get(campo)
        if isinstance(valor, str) and normal(valor) in nossos:
            achados[valor] = nossos[normal(valor)]
    return achados


def _ano(valor) -> str | None:
    """`ano` vem como inteiro; `data_setor` (risco) vem em milissegundos desde 1970 — a 3ª rodada na Actions imprimiu
    "1540339200000" como ano. Os dois viram o ano com quatro dígitos."""
    if isinstance(valor, (int, float)) and valor > 10**11:
        return str(datetime.fromtimestamp(valor / 1000, tz=timezone.utc).year)
    if isinstance(valor, (int, float)):
        return str(int(valor))
    if isinstance(valor, str) and valor.strip():
        return valor.strip()[:4]
    return None


def resumir(nome_servico: str, geojson: dict) -> dict:
    feicoes = geojson.get("features") or []
    chave = "classe" if nome_servico == "inundacao" else "grau_risco"
    contagem: dict[str, int] = {}
    tipologias: dict[str, int] = {}
    anos: set[str] = set()
    for f in feicoes:
        p = f.get("properties") or {}
        v = str(p.get(chave))
        contagem[v] = contagem.get(v, 0) + 1
        a = _ano(p.get("ano") if nome_servico == "inundacao" else p.get("data_setor"))
        if a:
            anos.add(a)
        # Setor de risco tem tipologia (deslizamento, inundação, enxurrada…): a maioria não é de água, e isso importa.
        for i in range(1, 6):
            t = str(p.get(f"tipolo_g{i}") or "").strip()
            if t:
                tipologias[t] = tipologias.get(t, 0) + 1
    saida = {"feicoes": len(feicoes), chave: contagem, "anos": sorted(anos)}
    if nome_servico == "risco":
        saida["tipologias"] = tipologias
    return saida


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    ap.add_argument("--saida", type=Path, required=True, help="pasta onde gravar os GeoJSON")
    ap.add_argument("--relatorio", type=Path, help="JSON com o resumo da rodada")
    a = ap.parse_args(argv)
    a.saida.mkdir(parents=True, exist_ok=True)
    relatorio: dict = {"gerado_em": datetime.now(timezone.utc).isoformat(timespec="seconds"), "base": BASE,
                       "servicos": {}, "erros": []}
    libera, motivo = robots_do_geoportal()
    relatorio["robots"] = motivo
    if not libera:
        relatorio["erros"].append(motivo)
        _grava(a.relatorio, relatorio)
        return 1
    for nome, (camada, campo, filtro) in SERVICOS.items():
        bloco: dict = {"camada": camada, "campo": campo, "cidades": {}}
        relatorio["servicos"][nome] = bloco
        try:
            distintos = json.loads(baixar(url_distintos(camada, campo, filtro)))
        except Exception as e:  # noqa: BLE001
            relatorio["erros"].append(f"{nome}: valores distintos de {campo} ({e})")
            continue
        bloco["nomes_no_servico"] = sorted(str((f.get("attributes") or {}).get(campo)) for f in distintos.get("features") or [])
        for nome_sgb, cidade in nomes_na_bacia(distintos, campo).items():
            try:
                geojson = json.loads(baixar(url_feicoes(camada, campo, nome_sgb, filtro)))
            except Exception as e:  # noqa: BLE001
                relatorio["erros"].append(f"{nome}/{cidade}: {e}")
                continue
            destino = a.saida / f"sgb-{nome}-{normal(cidade).replace(' ', '-')}.geojson"
            texto = json.dumps(geojson, ensure_ascii=False)
            destino.write_text(texto + "\n", encoding="utf-8")
            bloco["cidades"][cidade] = {**resumir(nome, geojson), "arquivo": destino.name,
                                       "sha256": hashlib.sha256(texto.encode("utf-8")).hexdigest(),
                                       "nome_no_sgb": nome_sgb}
    _grava(a.relatorio, relatorio)
    for nome, bloco in relatorio["servicos"].items():
        print(f"{nome}: {len(bloco.get('cidades', {}))} cidade(s) da bacia")
        for cidade, r in bloco.get("cidades", {}).items():
            print(f"  {cidade}: {r['feicoes']} feição(ões) {r.get('classe') or r.get('grau_risco')} anos {r['anos']}")
    for e in relatorio["erros"]:
        print("erro:", e, file=sys.stderr)
    return 1 if relatorio["erros"] and not any(b.get("cidades") for b in relatorio["servicos"].values()) else 0


def _grava(caminho: Path | None, relatorio: dict) -> None:
    if caminho:
        caminho.write_text(json.dumps(relatorio, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")


if __name__ == "__main__":
    sys.exit(main())
