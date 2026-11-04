#!/usr/bin/env python3
"""Testes de `baixar_sgb_suscetibilidade.py`: casamento de nomes sem adivinhar, URLs de consulta e resumo."""

from __future__ import annotations

import sys
import unittest
import urllib.parse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import baixar_sgb_suscetibilidade as sgb  # noqa: E402


class Nomes(unittest.TestCase):
    def test_so_as_cidades_da_lista_e_sem_parecido(self):
        distintos = {"features": [{"attributes": {"municipio": "BLUMENAU"}}, {"attributes": {"municipio": "Itajai"}},
                                  {"attributes": {"municipio": "Itajaí"}}, {"attributes": {"municipio": "Rodeio Bonito"}},
                                  {"attributes": {"municipio": "Gaspar"}}, {"attributes": {"municipio": None}}]}
        self.assertEqual(sgb.nomes_na_bacia(distintos, "municipio"),
                         {"BLUMENAU": "Blumenau", "Itajai": "Itajaí", "Itajaí": "Itajaí", "Gaspar": "Gaspar"})

    def test_urls_de_consulta(self):
        u = sgb.url_feicoes("https://x/MapServer/0", "municipio", "Rio do Sul", "uf='SC'")
        q = urllib.parse.parse_qs(urllib.parse.urlsplit(u).query)
        self.assertEqual(q["where"], ["uf='SC' AND municipio='Rio do Sul'"])
        self.assertEqual(q["f"], ["geojson"])
        self.assertEqual(q["outSR"], ["4326"])
        d = sgb.url_distintos("https://x/MapServer/0", "munic", None)
        qd = urllib.parse.parse_qs(urllib.parse.urlsplit(d).query)
        self.assertEqual((qd["where"], qd["returnDistinctValues"], qd["returnGeometry"]), (["1=1"], ["true"], ["false"]))

    def test_aspas_no_nome_nao_quebram_a_consulta(self):
        u = sgb.url_feicoes("https://x/0", "munic", "D'Oeste", None)
        self.assertIn("munic%3D%27D%27%27Oeste%27", u, "aspas simples dobrada, como o SQL do ArcGIS exige")


class Resumo(unittest.TestCase):
    def test_contagem_por_classe_e_anos(self):
        g = {"features": [{"properties": {"classe": "Alta", "ano": 2013}}, {"properties": {"classe": "Alta", "ano": 2013}},
                          {"properties": {"classe": "Baixa", "ano": 2013}}]}
        self.assertEqual(sgb.resumir("inundacao", g), {"feicoes": 3, "classe": {"Alta": 2, "Baixa": 1}, "anos": ["2013"]})
        r = {"features": [{"properties": {"grau_risco": "Muito Alto", "data_setor": "2025-09"}}]}
        self.assertEqual(sgb.resumir("risco", r)["grau_risco"], {"Muito Alto": 1})

    def test_robots(self):
        self.assertTrue(sgb.robots_libera("User-agent: *\nDisallow: /admin/\n"))
        self.assertFalse(sgb.robots_libera("User-agent: *\nDisallow: /\n"))


if __name__ == "__main__":
    unittest.main()
