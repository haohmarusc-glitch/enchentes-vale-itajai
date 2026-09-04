#!/usr/bin/env python3
"""
Testes da conferência "o afluente chega no rio?".

Afluente cortado é pior que afluente ausente. Ausente, quem olha sabe que não
sabe. Cortado, o mapa AFIRMA que a água pára ali — e quem mora entre a ponta do
traçado e o rio conclui que o ribeirão não chega perto de casa.
"""
import json
import tempfile
import unittest
from pathlib import Path

import conferir_afluentes_chegam as cf

RAIZ = Path(__file__).resolve().parent.parent


def geojson(linhas):
    return {"type": "Feature", "properties": {},
            "geometry": {"type": "MultiLineString", "coordinates": linhas}}


class Medida(unittest.TestCase):
    """Contra arquivos inventados, para o cálculo não depender do dado real."""

    def monta(self, arquivos: dict) -> Path:
        tmp = Path(tempfile.mkdtemp())
        for nome, linhas in arquivos.items():
            (tmp / f"{nome}.geojson").write_text(
                json.dumps(geojson(linhas)), encoding="utf-8")
        return tmp

    def com(self, arquivos, **kw):
        antigo = cf.RIOS
        cf.RIOS = self.monta(arquivos)
        try:
            return cf.avaliar(**kw)
        finally:
            cf.RIOS = antigo

    def test_afluente_que_encosta_no_tronco_nao_e_cortado(self):
        rs = self.com({
            "itajai-mirim": [[[-48.70, -26.93], [-48.68, -26.93]]],
            "ribeirao-x": [[[-48.69, -26.95], [-48.69, -26.93]]],  # toca a linha
        })
        self.assertEqual(len(rs), 1)
        self.assertFalse(rs[0]["cortado"], rs[0])
        self.assertEqual(rs[0]["chega_em"], "itajai-mirim")

    def test_afluente_que_para_longe_e_cortado(self):
        rs = self.com({
            "itajai-mirim": [[[-48.70, -26.93], [-48.68, -26.93]]],
            "ribeirao-x": [[[-48.69, -26.98], [-48.69, -26.96]]],  # ~3 km antes
        })
        self.assertTrue(rs[0]["cortado"])
        self.assertGreater(rs[0]["metros"], 1000)

    def test_a_PONTA_e_que_conta_nao_a_passagem_perto(self):
        """
        Um afluente pode roçar o tronco no meio do curso e desaguar longe. Medir
        o ponto mais próximo de QUALQUER vértice diria "chega" para um traçado
        que não chega.
        """
        rs = self.com({
            "itajai-mirim": [[[-48.70, -26.93], [-48.60, -26.93]]],
            # Passa colado ao tronco no meio, mas as duas pontas ficam longe.
            "ribeirao-x": [[[-48.65, -26.99], [-48.65, -26.9301], [-48.65, -26.87]]],
        })
        self.assertTrue(rs[0]["cortado"], "passar perto no meio não é desaguar")

    def test_o_tronco_nao_e_avaliado_como_afluente(self):
        rs = self.com({
            "itajai-acu": [[[-48.70, -26.90], [-48.60, -26.90]]],
            "itajai-mirim": [[[-48.70, -26.93], [-48.60, -26.93]]],
        })
        self.assertEqual(rs, [])


class ContraOsDadosReais(unittest.TestCase):
    def setUp(self):
        self.rs = {r["rio"]: r for r in cf.avaliar()}

    def test_o_Murta_chega_no_Acu(self):
        """Regra permanente: este afluente está completo e tem de continuar."""
        r = self.rs["ribeirao-murta"]
        self.assertEqual(r["chega_em"], "itajai-acu")
        self.assertFalse(r["cortado"], f"o Murta se afastou do Açu: {r['metros']} m")

    def test_o_Canhanduba_e_o_BURACO_CONHECIDO_de_578_m(self):
        """
        RETRATO QUE DEVE ENVELHECER, como o das quatro réguas que faltavam.

        Em 04/09/2026 o traçado do Canhanduba morre a 578 m do Itajaí-Mirim: o
        último trecho antes da foz não casou com nenhum nome da consulta, e não
        está no bruto (`data/brutos/tracado-ribeiroes-osm.json` só tem 19
        elementos, e os três perto da ponta já foram convertidos).

        Quando o trecho for rebaixado, este teste FALHA — e a falha é a notícia
        boa. Aí: apague este teste, deixe o `test_o_Murta_chega_no_Acu` valer
        para todos, e feche a pendência do README.
        """
        r = self.rs["ribeirao-canhanduba"]
        self.assertEqual(r["chega_em"], "itajai-mirim",
                         "o Canhanduba deságua no Mirim — se mudou de tronco, "
                         "o traçado foi trocado")
        self.assertAlmostEqual(
            r["metros"], 578, delta=30,
            msg=f"o vão do Canhanduba mudou ({r['metros']} m). Se DIMINUIU, o "
                "trecho que faltava foi rebaixado: apague este teste e feche a "
                "pendência. Se AUMENTOU, o traçado perdeu vias.")


if __name__ == "__main__":
    unittest.main()
