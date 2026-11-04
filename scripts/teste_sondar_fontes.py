#!/usr/bin/env python3
"""Testes de `sondar_fontes.py`: só GET, só depois do robots.txt, e o relatório diz o que cada host devolveu."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import sondar_fontes as sf  # noqa: E402


class Resposta:
    def __init__(self, status, texto="", tipo="text/plain"):
        self.status_code, self.text, self.headers = status, texto, {"Content-Type": tipo}
        self.content = texto.encode("utf-8")


def transporte_falso(respostas: dict, pedidos: list):
    def t(url, cabecalhos, timeout):
        pedidos.append((url, cabecalhos["User-Agent"]))
        r = respostas.get(url)
        if r is None:
            raise ConnectionError(f"sem rota para {url}")
        return r
    return t


class Sondagem(unittest.TestCase):
    def test_robots_decide_e_o_relatorio_descreve(self):
        respostas = {
            "https://a.exemplo/robots.txt": Resposta(200, "User-agent: *\nDisallow: /fechado/\n"),
            "https://a.exemplo/aberto.json": Resposta(200, '{"features": [1, 2]}', "application/json"),
            "https://b.exemplo/robots.txt": Resposta(404),
            "https://b.exemplo/x": Resposta(500, "<html>erro</html>", "text/html"),
        }
        pedidos: list = []
        alvos = [("aberto", "https://a.exemplo/aberto.json"), ("fechado", "https://a.exemplo/fechado/dados"),
                 ("sem-robots", "https://b.exemplo/x"), ("sem-rota", "https://c.exemplo/y")]
        s = sf.sondar(alvos, transporte_falso(respostas, pedidos))
        self.assertEqual(s["alvos"]["aberto"]["status"], 200)
        self.assertEqual(s["alvos"]["aberto"]["json"], {"tipo": "dict", "chaves": ["features"], "itens": 1})
        self.assertEqual(s["alvos"]["fechado"]["resultado"], "robots.txt não permite; não pedido")
        self.assertEqual(s["alvos"]["sem-robots"]["status"], 500, "robots 404 = tudo liberado")
        self.assertEqual(s["alvos"]["sem-rota"]["resultado"],
                         "robots.txt sem resposta (ConnectionError: sem rota para https://c.exemplo/robots.txt); não pedido",
                         "o relatório diz POR QUE o robots não respondeu")
        urls = [u for u, _ in pedidos]
        self.assertNotIn("https://a.exemplo/fechado/dados", urls, "o que o robots fecha não é pedido")
        self.assertEqual(urls.count("https://a.exemplo/robots.txt"), 1, "um robots por host")
        self.assertTrue(all(ua == sf.USER_AGENT for _, ua in pedidos))

    def test_robots_com_erro_de_servidor_fecha_tudo(self):
        respostas = {"https://d.exemplo/robots.txt": Resposta(503), "https://d.exemplo/x": Resposta(200, "ok")}
        s = sf.sondar([("x", "https://d.exemplo/x")], transporte_falso(respostas, []))
        self.assertEqual(s["alvos"]["x"]["resultado"], "robots.txt não permite; não pedido")

    def test_alvos_sao_so_get_de_leitura(self):
        for nome, url in sf.ALVOS:
            self.assertTrue(url.startswith("https://"), nome)
            self.assertNotIn("applyEdits", url)
            self.assertNotIn("addFeatures", url)


if __name__ == "__main__":
    unittest.main()
