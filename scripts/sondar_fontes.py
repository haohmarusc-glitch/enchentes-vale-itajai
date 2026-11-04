#!/usr/bin/env python3
"""Sonda, só com GET, as fontes que a varredura de 04/11/2026 deixou "não conferidas daqui".

POR QUE EXISTE. O ambiente das sessões de código e a rede do Jefferson não alcançam o serviço de camadas do
CEMADEN (`mapservices`/`resources`), e o geoportal do SGB e o WordPress da Defesa Civil de SC só abriram no
navegador. O runner do GitHub Actions é um terceiro ponto de vista: `sondar-fontes.yml` roda isto e publica o
relatório no branch `sondagem-fontes`, para a sessão ler.

O QUE FAZ. Para cada endereço da lista: confere o `robots.txt` do host (na dúvida, não pede), faz UM GET com o
`User-Agent` do projeto e guarda status, tipo, tamanho, os primeiros caracteres e, quando é JSON, as chaves.
Não escreve em serviço nenhum, não envia formulário, não tenta credencial.

Uso:
    python3 scripts/sondar_fontes.py --relatorio sondagem.json
"""

from __future__ import annotations

import argparse
import json
import sys
import urllib.parse
import urllib.robotparser
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from comum import HTTP_TIMEOUT_S, USER_AGENT  # noqa: E402

#: (nome, url). Os ids do serviço de camadas do CEMADEN não estão escritos no JS do mapa (ele os monta em
#: `createImageLayer`): sondam-se os primeiros, só para ver se o serviço responde e o que devolve.
ALVOS: list[tuple[str, str]] = [
    ("cemaden-mapservices-layer-1", "https://mapservices.cemaden.gov.br/MapaInterativoWS/resources/layer/id/1"),
    ("cemaden-mapservices-layer-2", "https://mapservices.cemaden.gov.br/MapaInterativoWS/resources/layer/id/2"),
    ("cemaden-mapservices-layer-3", "https://mapservices.cemaden.gov.br/MapaInterativoWS/resources/layer/id/3"),
    ("cemaden-resources-311_24", "https://resources.cemaden.gov.br/dados/311_24.json"),
    ("cemaden-wms-capabilities", "https://gsc.cemaden.gov.br/geoserver/cemaden_dev/wms?service=WMS&request=GetCapabilities&version=1.3.0"),
    ("cemaden-grafico-pcd-exemplo", "https://mapainterativo.cemaden.gov.br/graficos/interativo/grafico_CEMADEN.php?idpcd=0"),
    ("dcsc-wp-json-avisos", "https://www.defesacivil.sc.gov.br/wp-json/wp/v2/posts?categories=7,6&per_page=3&_fields=id,date,date_gmt,link,title,categories"),
    ("dcsc-feed", "https://www.defesacivil.sc.gov.br/feed/"),
    ("sgb-inundacao-distintos-sc", "https://geoportal.sgb.gov.br/server/rest/services/gestaoterritorial/inundacao/MapServer/0/query?where=uf%3D%27SC%27&outFields=municipio&returnDistinctValues=true&returnGeometry=false&f=json"),
    ("sgb-risco-distintos", "https://geoportal.sgb.gov.br/server/rest/services/gestaoterritorial/risco/MapServer/0/query?where=1%3D1&outFields=munic&returnDistinctValues=true&returnGeometry=false&f=json"),
    ("furb-geonode-layers", "https://monitora.furb.br/api/layers/?limit=5"),
    ("mendeley-dataset", "https://data.mendeley.com/datasets/cj64gycsw8"),
    # Copernicus (pendência 4 do relatório de ganhos de 04/11/2026): daqui e da rede do Jefferson nada abre.
    ("copernicus-ems-portal", "https://emergency.copernicus.eu/"),
    ("copernicus-ems-activations", "https://mapping.emergency.copernicus.eu/activations/"),
    ("copernicus-gfm-portal", "https://global-flood.emergency.copernicus.eu/"),
    ("copernicus-gfm-api-eodc", "https://api.gfm.eodc.eu/v2/"),
]
AMOSTRA = 300


def _robots(host_url: str, transporte) -> tuple[urllib.robotparser.RobotFileParser | None, str]:
    """(robots do host, motivo). Sem resposta → (None, o erro), para o relatório dizer POR QUE não pediu
    (a primeira rodada na Actions, 04/11/2026, só dizia "sem resposta" e não dava para saber se era rota,
    TLS ou recusa). 404 = não há robots = tudo liberado; outro erro do servidor = tudo fechado."""
    p = urllib.parse.urlsplit(host_url)
    try:
        r = transporte(f"{p.scheme}://{p.netloc}/robots.txt", {"User-Agent": USER_AGENT}, HTTP_TIMEOUT_S)
    except Exception as e:  # noqa: BLE001
        return None, f"{type(e).__name__}: {e}"
    rp = urllib.robotparser.RobotFileParser()
    if r.status_code >= 400:
        rp.parse([] if r.status_code == 404 else ["User-agent: *", "Disallow: /"])
        return rp, f"HTTP {r.status_code}"
    rp.parse(r.text.splitlines())
    return rp, f"HTTP {r.status_code}"


def sondar(alvos: list[tuple[str, str]], transporte) -> dict:
    """Um GET por alvo, depois do robots do host. `transporte(url, cabecalhos, timeout)` como em `comum.baixar`."""
    saida: dict = {"gerado_em": datetime.now(timezone.utc).isoformat(timespec="seconds"), "user_agent": USER_AGENT,
                   "alvos": {}}
    robots_por_host: dict[str, tuple[urllib.robotparser.RobotFileParser | None, str]] = {}
    for nome, url in alvos:
        host = urllib.parse.urlsplit(url).netloc
        if host not in robots_por_host:
            robots_por_host[host] = _robots(url, transporte)
        rp, motivo = robots_por_host[host]
        if rp is None:
            saida["alvos"][nome] = {"url": url, "resultado": f"robots.txt sem resposta ({motivo}); não pedido"}
            continue
        if not rp.can_fetch(USER_AGENT, url):
            saida["alvos"][nome] = {"url": url, "resultado": "robots.txt não permite; não pedido"}
            continue
        try:
            r = transporte(url, {"User-Agent": USER_AGENT}, HTTP_TIMEOUT_S)
        except Exception as e:  # noqa: BLE001
            saida["alvos"][nome] = {"url": url, "resultado": f"falhou: {e}"}
            continue
        item = {"url": url, "status": r.status_code, "tipo": (r.headers or {}).get("Content-Type"),
                "bytes": len(r.content or b""), "amostra": (r.text or "")[:AMOSTRA]}
        if "json" in (item["tipo"] or ""):
            try:
                d = json.loads(r.text)
                item["json"] = {"tipo": type(d).__name__, "chaves": sorted(d.keys())[:40] if isinstance(d, dict) else None,
                                "itens": len(d) if isinstance(d, (list, dict)) else None}
            except ValueError:
                item["json"] = "inválido"
        saida["alvos"][nome] = item
    return saida


def _transporte_requests(url, cabecalhos, timeout):
    import requests
    return requests.get(url, headers=cabecalhos, timeout=timeout)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    ap.add_argument("--relatorio", type=Path, required=True)
    a = ap.parse_args(argv)
    saida = sondar(ALVOS, _transporte_requests)
    a.relatorio.write_text(json.dumps(saida, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    for nome, item in saida["alvos"].items():
        resumo = item.get("resultado") or "HTTP {status} {tipo} {bytes} B".format(**item)
        print(f"{nome}: {resumo}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
