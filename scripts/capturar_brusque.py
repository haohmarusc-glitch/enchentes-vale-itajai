#!/usr/bin/env python3
"""Captura, só leitura, o mapa de monitoramento da Defesa Civil de Brusque e os dados que ele carrega.

POR QUE EXISTE (04/11/2026, cheia em curso). O story da Defesa Civil de Brusque publicou 6,14 m às 19h30 e 6,20 m
às 19h45, com "nível de alerta: 4,51 m a 7,50 m". O site lia a DCSC-00019 (Ponte Estaiada) com 5,86 e 5,92 m nos
mesmos minutos — 28 cm abaixo, com a mesma subida — e pintava "emergência" pela escala 3,00 / 5,00 m do cadastro.
Falta saber DE QUAL ESTAÇÃO sai o número oficial e EM QUAL RÉGUA vale a escala 4,51–7,50 (regra do projeto: régua
da leitura = régua das faixas). O Jefferson pediu: "Extraia os dados de defesacivil.brusque.sc.gov.br/monitoramento/mapa".

O host recusa o ambiente das sessões de código (proxy, desde 08/09/2026); o runner do GitHub alcança a mesma
plataforma em Gaspar. Por isso roda no Actions (`.github/workflows/capturar-brusque.yml`) e publica os brutos no
branch `captura-brusque`. Nada daqui entra em `data/` sem a sessão ler e o Jefferson decidir.

REGRAS: só GET; `robots.txt` antes de tudo (4xx = sem regras, RFC 9309; 5xx ou sem resposta = não pede nada);
User-Agent do projeto; pausa entre pedidos; no máximo `MAX_PEDIDOS` por rodada; só o próprio host.

O QUE PEDE
  1. /monitoramento/mapa (a página pedida);
  2. os scripts do próprio host que a página carrega (para achar os endpoints de dados);
  3. os endpoints de dados citados na página ou nos scripts (JSON, /api, /estacao, /monitoramento, /mapa);
  4. as estações já conhecidas do projeto: 79 (Ponte Estaiada – DCSC), 4 (Ponte Estaiada – ANA) e 23 (Guarani).

Uso:
    python3 scripts/capturar_brusque.py --saida captura
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urljoin, urlparse

sys.path.insert(0, str(Path(__file__).resolve().parent))

from comum import HTTP_TIMEOUT_S, USER_AGENT  # noqa: E402
from importar_cotas_rio_do_sul import robots_permite  # noqa: E402

BASE = "https://defesacivil.brusque.sc.gov.br"
HOST = urlparse(BASE).netloc
MAPA = f"{BASE}/monitoramento/mapa"
ESTACOES_CONHECIDAS = ("79", "4", "23")
MAX_PEDIDOS = 30
PAUSA_S = 1.5
MAX_SCRIPTS = 6

#: Caminhos citados entre aspas que parecem dado: o mapa costuma buscar as estações por fetch/ajax.
RE_CAMINHO = re.compile(r"""["'`]((?:https?://[^"'`\s]+)?/[A-Za-z0-9_\-./?=&%]*?(?:api|json|estac|monitor|mapa|nivel|rio|leitura|cota|grafico|dados)[A-Za-z0-9_\-./?=&%]*)["'`]""", re.I)
RE_SCRIPT = re.compile(r"""<script[^>]+src=["']([^"']+)["']""", re.I)
RE_ESTACAO = re.compile(r"/estacao/ver/(\d+)")


def mesmo_host(url: str) -> bool:
    return urlparse(url).netloc in ("", HOST)


def caminhos_de_dados(texto: str, base: str = BASE) -> list[str]:
    """Os endpoints de dados citados num HTML ou JS, absolutos, só do próprio host, sem repetir, na ordem."""
    vistos: list[str] = []
    for m in RE_CAMINHO.finditer(texto):
        bruto = m.group(1)
        if bruto.split("?")[0].endswith((".js", ".css", ".png", ".jpg", ".jpeg", ".svg", ".ico", ".woff", ".woff2", ".ttf", ".map")):
            continue
        if "{" in bruto or "${" in bruto:
            continue
        url = urljoin(base + "/", bruto)
        if mesmo_host(url) and url not in vistos:
            vistos.append(url)
    return vistos


def scripts_do_host(html: str, base: str = BASE) -> list[str]:
    saida: list[str] = []
    for src in RE_SCRIPT.findall(html):
        url = urljoin(base + "/", src)
        if mesmo_host(url) and url not in saida:
            saida.append(url)
    return saida


def nome_do_arquivo(url: str, tipo: str | None) -> str:
    p = urlparse(url)
    base = (p.path.strip("/") or "raiz").replace("/", "_")
    if p.query:
        base += "_" + re.sub(r"[^A-Za-z0-9]+", "-", p.query)[:60]
    ext = ".json" if "json" in (tipo or "") else ".js" if "javascript" in (tipo or "") else ".html" if "html" in (tipo or "") else ".txt"
    if not base.endswith(ext):
        base += ext
    return base[:150]


class Captura:
    def __init__(self, saida: Path, pedir=None):
        self.saida = saida
        self.pedir = pedir or self._pedir_requests
        self.indice: list[dict] = []
        self.robots: str | None = None
        self.pedidos = 0

    @staticmethod
    def _pedir_requests(url: str):
        import requests
        r = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=(10, HTTP_TIMEOUT_S))
        return r.status_code, r.headers.get("Content-Type", ""), r.content

    def permitido(self, url: str) -> bool:
        return self.robots is not None and robots_permite(self.robots, urlparse(url).path)

    def ler_robots(self) -> str:
        try:
            status, _, corpo = self.pedir(f"{BASE}/robots.txt")
            self.pedidos += 1
        except Exception as e:  # noqa: BLE001
            return f"robots.txt sem resposta ({type(e).__name__}: {e}); nada pedido"
        if 400 <= status < 500:
            self.robots = ""
            return f"robots.txt HTTP {status}: sem regras (RFC 9309)"
        if status >= 500:
            return f"robots.txt HTTP {status}: na dúvida, nada pedido"
        self.robots = corpo.decode("utf-8", errors="replace")
        (self.saida / "robots.txt").write_bytes(corpo)
        return "robots.txt lido"

    def pegar(self, url: str, papel: str) -> bytes | None:
        if any(i["url"] == url for i in self.indice):
            return None
        if self.pedidos >= MAX_PEDIDOS:
            self.indice.append({"url": url, "papel": papel, "resultado": f"não pedido: limite de {MAX_PEDIDOS} pedidos"})
            return None
        if not self.permitido(url):
            self.indice.append({"url": url, "papel": papel, "resultado": "robots.txt não permite; não pedido"})
            return None
        time.sleep(PAUSA_S)
        try:
            status, tipo, corpo = self.pedir(url)
        except Exception as e:  # noqa: BLE001
            self.pedidos += 1
            self.indice.append({"url": url, "papel": papel, "resultado": f"falhou: {type(e).__name__}: {e}"})
            return None
        self.pedidos += 1
        arquivo = nome_do_arquivo(url, tipo)
        (self.saida / arquivo).write_bytes(corpo)
        self.indice.append({"url": url, "papel": papel, "status": status, "tipo": tipo, "bytes": len(corpo),
                            "sha256": hashlib.sha256(corpo).hexdigest(), "arquivo": arquivo})
        return corpo if status == 200 else None

    def rodar(self) -> dict:
        self.saida.mkdir(parents=True, exist_ok=True)
        inicio = datetime.now(timezone.utc).isoformat(timespec="seconds")
        motivo = self.ler_robots()
        if self.robots is not None:
            corpo = self.pegar(MAPA, "a página pedida")
            html = corpo.decode("utf-8", errors="replace") if corpo else ""
            dados = caminhos_de_dados(html)
            for js in scripts_do_host(html)[:MAX_SCRIPTS]:
                c = self.pegar(js, "script do mapa (para achar os endpoints)")
                if c:
                    dados += [u for u in caminhos_de_dados(c.decode("utf-8", errors="replace")) if u not in dados]
            estacoes = list(dict.fromkeys(list(ESTACOES_CONHECIDAS) + RE_ESTACAO.findall(html)))
            for u in dados:
                if RE_ESTACAO.search(u):
                    continue
                self.pegar(u, "endpoint de dados citado na página ou nos scripts")
            for cod in estacoes[:10]:
                self.pegar(f"{BASE}/estacao/ver/{cod}", f"estação {cod}")
        relatorio = {"inicio": inicio, "fim": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                     "user_agent": USER_AGENT, "robots": motivo, "pedidos": self.pedidos, "itens": self.indice}
        (self.saida / "indice.json").write_text(json.dumps(relatorio, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
        return relatorio


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    ap.add_argument("--saida", type=Path, required=True)
    a = ap.parse_args(argv)
    r = Captura(a.saida).rodar()
    print(r["robots"])
    for i in r["itens"]:
        print(f"{i.get('status', '—')} {i.get('bytes', '')} {i['url']} — {i.get('resultado') or i['papel']}")
    return 0 if any(i.get("status") == 200 for i in r["itens"]) else 1


if __name__ == "__main__":
    sys.exit(main())
