#!/usr/bin/env python3
"""Testes da ordenação das réguas DC pela descida do rio."""

import json
import unittest

from comum import DADOS
from ordenar_estacoes_itajai import EMPATE_KM, ordenar, reguas_dc


def _r(cod, rio, km):
    return {"codigo": cod, "rio": rio, "titulo": cod, "km_da_foz": km, "afastamento_m": 0}


class Ordenar(unittest.TestCase):
    def test_montante_primeiro_foz_por_ultimo(self):
        por = ordenar([_r("A", "itajai-mirim", 5.0), _r("B", "itajai-mirim", 20.0),
                       _r("C", "itajai-mirim", 12.0)])
        ordem = {r["codigo"]: r["ordem_descida"] for r in por["itajai-mirim"]}
        # 20 km (mais a montante) = ordem 1; 5 km (mais perto da foz) = ordem 3
        self.assertEqual(ordem, {"B": 1, "C": 2, "A": 3})

    def test_empate_compartilha_ordem_e_ganha_nota(self):
        por = ordenar([_r("X", "itajai-mirim", 4.80), _r("Y", "itajai-mirim", 4.80 + EMPATE_KM / 2)])
        m = {r["codigo"]: r for r in por["itajai-mirim"]}
        self.assertEqual(m["X"]["ordem_descida"], m["Y"]["ordem_descida"])
        self.assertIn("ordem_nota", m["X"])
        self.assertIn("indefiní", m["X"]["ordem_nota"])

    def test_diferenca_acima_do_empate_nao_compartilha(self):
        por = ordenar([_r("X", "itajai-mirim", 4.0), _r("Y", "itajai-mirim", 4.0 + EMPATE_KM * 2)])
        ordens = {r["ordem_descida"] for r in por["itajai-mirim"]}
        self.assertEqual(len(ordens), 2)
        for r in por["itajai-mirim"]:
            self.assertNotIn("ordem_nota", r)

    def test_cursos_sao_independentes(self):
        por = ordenar([_r("A", "itajai-acu", 10.0), _r("B", "itajai-mirim", 30.0)])
        # cada curso começa do 1, não se mistura
        self.assertEqual(por["itajai-acu"][0]["ordem_descida"], 1)
        self.assertEqual(por["itajai-mirim"][0]["ordem_descida"], 1)


class ArquivoReal(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.dados = json.loads((DADOS / "estacoes.json").read_text(encoding="utf-8"))

    def test_reguas_dc_pega_so_dc_com_coordenada(self):
        rs = reguas_dc(self.dados)
        cods = {r["codigo"] for r in rs}
        self.assertEqual(len(cods), 11)
        self.assertNotIn("DC-00", cods)
        self.assertTrue(all(r.get("km_da_foz") is not None for r in rs))

    def test_no_mirim_limoeiro_e_o_mais_a_montante_e_04_06_empatam(self):
        por = ordenar(reguas_dc(self.dados))
        mirim = {r["codigo"]: r for r in por["itajai-mirim"]}
        self.assertEqual(mirim["DC-10"]["ordem_descida"], 1)  # Limoeiro, o mais alto
        self.assertEqual(mirim["DC-04"]["ordem_descida"], mirim["DC-06"]["ordem_descida"])
        self.assertIn("ordem_nota", mirim["DC-04"])


if __name__ == "__main__":
    unittest.main()
