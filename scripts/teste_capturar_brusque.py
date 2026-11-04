#!/usr/bin/env python3
"""Testes de `capturar_brusque.py`: robots antes de tudo, só o próprio host, endpoints achados no HTML e no JS."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import capturar_brusque as cb  # noqa: E402

HTML = """<html><head><script src="/js/mapa.js"></script><script src="https://cdn.exemplo/x.js"></script></head>
<body><a href="/estacao/ver/31">Salseiro</a><div data-url="/monitoramento/estacoes.json"></div>
<img src="/img/mapa.png"></body></html>"""
JS = """fetch('/api/estacoes?tipo=rio').then(r=>r.json()); var u = "https://outro.host/api/x"; const t = `/api/leitura/${id}`;"""


class Extracao(unittest.TestCase):
    def test_endpoints_so_do_host_sem_imagem_nem_template(self):
        self.assertEqual(cb.caminhos_de_dados(HTML), ["https://defesacivil.brusque.sc.gov.br/estacao/ver/31",
                                                      "https://defesacivil.brusque.sc.gov.br/monitoramento/estacoes.json"])
        self.assertEqual(cb.caminhos_de_dados(JS), ["https://defesacivil.brusque.sc.gov.br/api/estacoes?tipo=rio"])
        self.assertEqual(cb.scripts_do_host(HTML), ["https://defesacivil.brusque.sc.gov.br/js/mapa.js"])


class Rodada(unittest.TestCase):
    def _rodar(self, respostas):
        pedidos = []

        def pedir(url):
            pedidos.append(url)
            r = respostas.get(url)
            if r is None:
                raise ConnectionError("sem rota")
            return r

        cb.PAUSA_S = 0
        with tempfile.TemporaryDirectory() as d:
            rel = cb.Captura(Path(d), pedir).rodar()
        return rel, pedidos

    def test_robots_sem_resposta_nao_pede_nada(self):
        rel, pedidos = self._rodar({})
        self.assertEqual(pedidos, ["https://defesacivil.brusque.sc.gov.br/robots.txt"])
        self.assertIn("nada pedido", rel["robots"])

    def test_robots_fecha_o_mapa(self):
        rel, pedidos = self._rodar({"https://defesacivil.brusque.sc.gov.br/robots.txt": (200, "text/plain", b"User-agent: *\nDisallow: /\n")})
        self.assertEqual(len(pedidos), 1)
        self.assertTrue(all(i["resultado"].startswith("robots.txt não permite") for i in rel["itens"]))

    def test_rodada_completa_segue_html_e_js(self):
        b = "https://defesacivil.brusque.sc.gov.br"
        rel, pedidos = self._rodar({
            f"{b}/robots.txt": (404, "text/html", b""),
            f"{b}/monitoramento/mapa": (200, "text/html", HTML.encode()),
            f"{b}/js/mapa.js": (200, "application/javascript", JS.encode()),
            f"{b}/monitoramento/estacoes.json": (200, "application/json", b"[]"),
            f"{b}/api/estacoes?tipo=rio": (200, "application/json", b"[]"),
        })
        self.assertIn(f"{b}/api/estacoes?tipo=rio", pedidos)
        self.assertIn(f"{b}/estacao/ver/79", pedidos)
        self.assertIn(f"{b}/estacao/ver/31", pedidos, "estação citada na página também é lida")
        self.assertNotIn("https://cdn.exemplo/x.js", pedidos, "só o próprio host")
        self.assertTrue(all(u.startswith(b) for u in pedidos))
        self.assertEqual(len(pedidos), len(set(pedidos)), "nada é pedido duas vezes")


if __name__ == "__main__":
    unittest.main()
