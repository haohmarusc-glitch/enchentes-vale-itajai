#!/usr/bin/env python3
"""Testes de `cruzar_sgb_ruas.py`: ponto dentro/fora, classe mais alta na borda, só setores de água, datas do SGB.

    python3 scripts/teste_cruzar_sgb_ruas.py
"""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import cruzar_sgb_ruas as cs  # noqa: E402

QUADRADO = [[[-49.0, -27.0], [-48.0, -27.0], [-48.0, -26.0], [-49.0, -26.0], [-49.0, -27.0]]]
# Metade leste do quadrado, sobreposta: ponto na borda cai nos dois.
LESTE = [[[-48.5, -27.0], [-48.0, -27.0], [-48.0, -26.0], [-48.5, -26.0], [-48.5, -27.0]]]
COM_BURACO = QUADRADO + [[[-48.7, -26.7], [-48.3, -26.7], [-48.3, -26.3], [-48.7, -26.3], [-48.7, -26.7]]]


def feicao(coords, **props):
    return {"type": "Feature", "geometry": {"type": "Polygon", "coordinates": coords}, "properties": props}


class Geometria(unittest.TestCase):
    def test_dentro_fora_e_buraco(self):
        self.assertTrue(cs.dentro_do_poligono((-48.9, -26.9), QUADRADO))
        self.assertFalse(cs.dentro_do_poligono((-47.9, -26.9), QUADRADO))
        self.assertFalse(cs.dentro_do_poligono((-48.5, -26.5), COM_BURACO), "no buraco é fora")
        self.assertTrue(cs.dentro_do_poligono((-48.9, -26.9), COM_BURACO))
        multi = {"type": "MultiPolygon", "coordinates": [QUADRADO, [[[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]]]]}
        self.assertTrue(cs.dentro_da_geometria((0.5, 0.5), multi))

    def test_classe_mais_alta_na_borda_e_fora_e_none(self):
        camada = cs.Camada({"features": [feicao(QUADRADO, classe="Baixa", ano=2013, executor="IPT"),
                                          feicao(LESTE, classe="Alta", ano=2013, executor="IPT")]})
        self.assertEqual(cs.suscetibilidade_do_ponto(camada, (-48.2, -26.5))["classe"], "Alta", "ponto nos dois: a mais alta")
        self.assertEqual(cs.suscetibilidade_do_ponto(camada, (-48.8, -26.5))["classe"], "Baixa")
        self.assertIsNone(cs.suscetibilidade_do_ponto(camada, (-47.0, -26.5)))


class Setores(unittest.TestCase):
    def test_so_setores_de_agua_e_data_em_milissegundos(self):
        camada = cs.Camada({"features": [
            feicao(QUADRADO, num_setor="SC_X_SR_1_CPRM", grau_risco="Alto", tipolo_g1="Deslizamento", data_setor=1540339200000, local="Morro"),
            feicao(QUADRADO, num_setor="SC_X_SR_2_CPRM", grau_risco="Muito alto", tipolo_g1="Deslizamento", tipolo_g2="Inundação",
                   data_setor=1540339200000, local=" Beira Rio "),
            feicao(QUADRADO, num_setor="SC_X_SR_3_CPRM", grau_risco="Alto", tipolo_g1="Enxurrada", data_setor="2025-09", local=" "),
        ]})
        riscos = cs.riscos_do_ponto(camada, (-48.5, -26.9))
        self.assertEqual([r["setor"] for r in riscos], ["SC_X_SR_2_CPRM", "SC_X_SR_3_CPRM"], "o de deslizamento puro fica fora; muito alto primeiro")
        self.assertEqual(riscos[0]["tipologias"], ["Inundação"], "só a tipologia de água do setor misto")
        self.assertEqual(riscos[0]["data"], "2018-10-24", "data_setor em milissegundos vira AAAA-MM-DD")
        self.assertEqual(riscos[0]["local"], "Beira Rio")
        self.assertIsNone(riscos[1]["local"])
        resumo = cs.resumo_da_camada("risco", {"features": camada and [
            feicao(QUADRADO, grau_risco="Alto", tipolo_g1="Deslizamento", data_setor=1540339200000),
            feicao(QUADRADO, grau_risco="Alto", tipolo_g1="Inundação", data_setor=1540339200000)]})
        self.assertEqual(resumo, {"setores": 2, "setores_de_agua": 1, "grau": {"Alto": 1}, "anos": ["2018"]})


class Cruzamento(unittest.TestCase):
    def test_pontos_so_com_coordenada_e_contagens(self):
        with tempfile.TemporaryDirectory() as d:
            pasta = Path(d)
            (pasta / "sgb-inundacao-x.geojson").write_text(json.dumps({"features": [feicao(QUADRADO, classe="Média", ano=2013, executor="IPT")]}), encoding="utf-8")
            (pasta / "sgb-risco-x.geojson").write_text(json.dumps({"features": [feicao(LESTE, num_setor="S1", grau_risco="Alto", tipolo_g1="Inundação", data_setor=1540339200000)]}), encoding="utf-8")
            resumo_sgb = {"gerado_em": "2026-11-04T16:43:00+00:00", "servicos": {
                "inundacao": {"cidades": {"X": {"arquivo": "sgb-inundacao-x.geojson", "sha256": "a" * 64, "nome_no_sgb": "X"}}},
                "risco": {"cidades": {"X": {"arquivo": "sgb-risco-x.geojson", "sha256": "b" * 64, "nome_no_sgb": "X"}}},
            }}
            cotas = [
                {"cidade": "x", "rua": "A", "bairro": None, "ponto": None, "lat": -26.9, "lon": -48.2},   # dentro, no setor
                {"cidade": "x", "rua": "B", "bairro": "C", "ponto": "nº 1", "lat": -26.9, "lon": -48.9},  # dentro, fora do setor
                {"cidade": "x", "rua": "C", "bairro": None, "ponto": None, "lat": -25.0, "lon": -48.9},   # fora da carta
                {"cidade": "x", "rua": "D", "bairro": None, "ponto": None},                              # sem coordenada: não entra
                {"cidade": "y", "rua": "E", "bairro": None, "ponto": None, "lat": -26.9, "lon": -48.2},   # cidade sem SGB: não entra
            ]
            cidades = cs.cruzar(cotas, pasta, resumo_sgb)
            self.assertEqual(list(cidades), ["x"])
            b = cidades["x"]
            self.assertEqual([p["rua"] for p in b["pontos"]], ["A", "B", "C"])
            self.assertEqual(b["pontos_por_classe"], {"Média": 2, "fora da carta": 1})
            self.assertEqual(b["pontos_em_setor_de_risco"], 1)
            self.assertEqual(b["pontos"][0]["risco"][0]["setor"], "S1")
            self.assertEqual(b["camadas"]["inundacao"]["sha256"], "a" * 64)
            self.assertNotIn("_camada_inundacao", b, "a geometria não vai para o arquivo")
            saida = cs.montar(cidades, resumo_sgb)
            self.assertIn("não é cota", " ".join(saida["_meta"]["regras"]))
            self.assertIn("199", " ".join(saida["_meta"]["regras"]))
            self.assertEqual(saida["_meta"]["acesso"]["quando"], "2026-11-04T16:43:00+00:00")


if __name__ == "__main__":
    unittest.main()
