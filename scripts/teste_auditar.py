#!/usr/bin/env python3
"""Testes do auditor.

O auditor existe para dizer se a coleta está viva e se a defasagem publicada
faz sentido. Se ELE errar, erra em silêncio — ninguém audita o auditor durante
uma cheia. Daí estes casos, com atrasos plantados e falhas injetadas.

    python3 scripts/teste_auditar.py
"""

import math
import unittest
from datetime import datetime, timedelta

from auditar import (
    CORRELACAO_MINIMA,
    TRAVADO_H,
    VAZIO_GRAVE_H,
    cobertura,
    correlacao,
    defasagem,
)

INICIO = datetime(2026, 8, 1, 0, 0)


def onda(passos, atraso_h=0.0, passo_min=30, base=3.0, ruido=0.0, semente=1):
    """Série com variação suave, opcionalmente atrasada."""
    import random
    r = random.Random(semente)
    pontos = []
    for i in range(passos):
        t = INICIO + timedelta(minutes=passo_min * i)
        th = i * (passo_min / 60) - atraso_h
        v = base + 0.55 * math.sin(th / 17.0) + 0.30 * math.sin(th / 5.3 + 1.1)
        pontos.append((t, round(v + (r.gauss(0, ruido) if ruido else 0), 3)))
    return pontos


def plana(passos, valor=1.19, passo_min=30):
    return [(INICIO + timedelta(minutes=passo_min * i), valor) for i in range(passos)]


class TesteDefasagem(unittest.TestCase):
    def test_recupera_o_atraso_plantado(self):
        montante = onda(720)
        jusante = onda(720, atraso_h=8)
        m = defasagem(montante, jusante)
        self.assertIsNotNone(m)
        self.assertAlmostEqual(m["horas"], 8.0, places=2)
        self.assertGreater(m["correlacao"], 0.99)

    def test_recupera_atraso_com_ruido(self):
        m = defasagem(onda(720, ruido=0.02, semente=3), onda(720, atraso_h=5, ruido=0.02, semente=4))
        self.assertIsNotNone(m)
        self.assertAlmostEqual(m["horas"], 5.0, delta=0.5)

    def test_rio_parado_nao_produz_defasagem(self):
        """Com o rio parado qualquer atraso alinha igual; devolver número seria inventar."""
        self.assertIsNone(defasagem(plana(720), plana(720, valor=2.0)))

    def test_uma_ponta_parada_ja_basta_para_recusar(self):
        self.assertIsNone(defasagem(onda(720), plana(720)))

    def test_serie_curta_demais(self):
        self.assertIsNone(defasagem(onda(2), onda(2, atraso_h=3)))

    def test_correlacao_de_series_sem_relacao_fica_baixa(self):
        import random
        r = random.Random(7)
        a = [r.gauss(0, 1) for _ in range(200)]
        b = [r.gauss(0, 1) for _ in range(200)]
        self.assertLess(abs(correlacao(a, b)), CORRELACAO_MINIMA)


class TesteCobertura(unittest.TestCase):
    def test_serie_saudavel_passa(self):
        pontos = onda(720, ruido=0.01)
        c = cobertura(pontos, dias=15, agora=pontos[-1][0] + timedelta(minutes=20))
        self.assertEqual(c["veredito"], "ok")
        self.assertEqual(c["problemas"], [])

    def test_sensor_travado_e_apontado(self):
        pontos = plana(int(TRAVADO_H * 4))
        c = cobertura(pontos, dias=15, agora=pontos[-1][0])
        self.assertEqual(c["veredito"], "atencao")
        self.assertTrue(any("travado" in p for p in c["problemas"]))

    def test_buraco_na_serie_e_apontado(self):
        pontos = onda(100, ruido=0.01)
        pulo = [(t + timedelta(hours=VAZIO_GRAVE_H + 2), v) for t, v in onda(100, ruido=0.01, semente=9)]
        todos = pontos + [(pulo[-1][0], pulo[-1][1])]
        c = cobertura(todos, dias=15, agora=todos[-1][0])
        self.assertTrue(any("vazio" in p for p in c["problemas"]), c["problemas"])

    def test_serie_com_menos_de_duas_leituras(self):
        self.assertEqual(cobertura([], dias=15, agora=INICIO)["veredito"], "sem-serie")
        self.assertEqual(cobertura(plana(1), dias=15, agora=INICIO)["veredito"], "sem-serie")

    def test_estacao_que_parou_de_publicar_e_apontada(self):
        """O caso que a coleta real precisa pegar antes da cheia, não durante."""
        pontos = onda(200, ruido=0.01)
        c = cobertura(pontos, dias=15, agora=pontos[-1][0] + timedelta(hours=30))
        self.assertEqual(c["veredito"], "atencao")
        self.assertTrue(any("sem leitura nova" in p for p in c["problemas"]), c["problemas"])

    def test_leitura_fora_de_faixa_e_apontada(self):
        pontos = onda(50, ruido=0.01) + [(INICIO + timedelta(days=1), 97.0)]
        c = cobertura(sorted(pontos), dias=15, agora=sorted(pontos)[-1][0])
        self.assertTrue(any("fora de faixa" in p for p in c["problemas"]), c["problemas"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
