#!/usr/bin/env python3
"""Testes da medição de distância ao longo do rio (traçado OSM)."""

import unittest

from medir_distancia_rio import (
    AFASTAMENTO_MAX_KM, _hav, carrega_grafo, coords_das_cidades, km_rio_entre,
)


class Distancia(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.grafo, cls.pos = carrega_grafo("itajai-acu")
        cls.cidades, _ = coords_das_cidades("itajai-acu")

    def km(self, de, para):
        return km_rio_entre(self.grafo, self.pos, self.cidades[de], self.cidades[para])

    def test_rio_e_mais_longo_que_a_reta(self):
        # O rio serpenteia: a distância pelo traçado supera a linha reta.
        km, da, db = self.km("rio-do-sul", "indaial")
        self.assertIsNotNone(km, "rio-do-sul e Indaial estão no traçado; deveria haver caminho")
        reta = _hav(self.cidades["rio-do-sul"], self.cidades["indaial"])
        self.assertGreater(km, reta, "distância pelo rio nunca é menor que a reta")
        self.assertLess(km / reta, 3.0, "fator de sinuosidade implausível — provável erro de grafo")

    def test_cidade_longe_do_tracado_nao_recebe_km(self):
        # Blumenau tem a coordenada da ESTAÇÃO, ~3 km do talvegue: fora do traçado.
        km, da, db = self.km("gaspar", "blumenau")
        self.assertIsNone(km, "Blumenau está longe do traçado; km_rio não deve sair")
        self.assertTrue(da > AFASTAMENTO_MAX_KM or db > AFASTAMENTO_MAX_KM)

    def test_valores_gravados_batem_com_o_calculo(self):
        # Os km_rio no transito.json têm de ser reproduzíveis a partir do traçado.
        import json
        from comum import DADOS
        t = json.loads((DADOS / "transito.json").read_text(encoding="utf-8"))
        gravados = {(x["de"], x["para"]): x["km_rio"] for x in t["trechos"] if "km_rio" in x}
        self.assertTrue(gravados, "esperava km_rio gravado em ao menos um trecho")
        for (de, para), v in gravados.items():
            km, _, _ = self.km(de, para)
            self.assertIsNotNone(km, f"{de}->{para} gravado mas sem caminho agora")
            self.assertAlmostEqual(round(km, 1), v, delta=0.2,
                                   msg=f"km_rio de {de}->{para} mudou; regrave com o script")


if __name__ == "__main__":
    unittest.main()
