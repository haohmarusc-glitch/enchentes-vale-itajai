#!/usr/bin/env python3
"""Testes da estimativa do zero das réguas de Itajaí pela maré.

Trava: a regressão devolve a leitura de quando a água está no nível médio do
mar; o rio alto fica fora da conta; e o terreno é lido só perto da régua.

    python3 scripts/teste_estimar_zero_reguas_itajai.py
"""

import math
import unittest

from estimar_zero_reguas_itajai import (
    BLUMENAU_RIO_BAIXO_M,
    NIVEL_MEDIO_NR_M,
    leitura_no_nivel_medio,
    minimos_quadrados,
    terreno_perto,
)

N = 24 * 20


class Regressao(unittest.TestCase):
    def test_minimos_quadrados_recupera_os_coeficientes(self):
        linhas = [[1.0, math.cos(i / 2), (i % 7) / 3] for i in range(60)]
        y = [0.4 + 0.8 * a + 0.1 * b for _, a, b in linhas]
        for c, esperado in zip(minimos_quadrados(linhas, y), (0.4, 0.8, 0.1)):
            self.assertAlmostEqual(c, esperado, places=9)

    def test_leitura_no_nivel_medio(self):
        # Régua com zero 1,0 m abaixo do nível médio: no nível médio, lê 1,0 m.
        mare = [NIVEL_MEDIO_NR_M + 0.5 * math.cos(2 * math.pi * i / 12.42) for i in range(N)]
        blu = [2.3 + 0.8 * (i % 50) / 50 for i in range(N)]
        regua = [1.0 + 0.9 * (m - NIVEL_MEDIO_NR_M) + 0.05 * (b - BLUMENAU_RIO_BAIXO_M) for m, b in zip(mare, blu)]
        r = leitura_no_nivel_medio(regua, mare, blu, 0)
        self.assertAlmostEqual(r["leitura_m"], 1.0, places=6)

    def test_rio_alto_fica_fora(self):
        mare = [NIVEL_MEDIO_NR_M + 0.5 * math.cos(2 * math.pi * i / 12.42) for i in range(N)]
        blu = [8.0] * N  # cheia o tempo todo: não há hora de rio baixo
        self.assertIsNone(leitura_no_nivel_medio([1.0] * N, mare, blu, 0))


class Terreno(unittest.TestCase):
    def test_so_pontos_dentro_do_raio(self):
        pontos = [(-26.9, -48.65, 2.0), (-26.9005, -48.65, 3.0), (-26.95, -48.65, 9.0)]
        t = terreno_perto(pontos, -26.9, -48.65, raio=300)
        self.assertEqual(t["n"], 2)
        self.assertEqual(t["min"], 2.0)
        self.assertIsNone(terreno_perto(pontos, -27.5, -48.65, raio=300))


if __name__ == "__main__":
    unittest.main()
