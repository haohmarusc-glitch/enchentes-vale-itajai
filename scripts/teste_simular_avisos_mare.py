#!/usr/bin/env python3
"""Testes da simulação de avisos com maré (proposta da DC-11, 08/10/2026).

A simulação só conta mensagens; ela precisa contar como o `alerta_cotas.decidir` de hoje, senão a
comparação entre as opções mente.

    python3 scripts/teste_simular_avisos_mare.py
"""

import math
import unittest
from datetime import datetime, timedelta

from simular_avisos_mare import episodios, faixa_com_histerese, simular

COTAS = {"atencao": 3.0, "alerta": 4.0, "emergencia": 5.0}
INICIO = datetime(2026, 9, 1)


def mare(dias: float, base: float, amplitude: float, passo_min: int = 10, subida_por_h: float = 0.0):
    """Senoide de 12,42 h em volta de `base`, com subida opcional da base (cheia)."""
    n = int(dias * 24 * 60 / passo_min)
    return [(INICIO + timedelta(minutes=i * passo_min),
             base + subida_por_h * i * passo_min / 60 + amplitude / 2 * math.sin(2 * math.pi * i * passo_min / 60 / 12.42))
            for i in range(n)]


class RegraDeHoje(unittest.TestCase):
    def test_mare_em_volta_da_cota_manda_ida_e_volta_a_cada_preamar(self):
        msgs = simular(mare(2, base=2.80, amplitude=0.70), COTAS)
        # Duas preamares por dia passam de 3,00; cada uma manda "atenção" e "normal".
        self.assertGreaterEqual(len(msgs), 6)
        self.assertEqual({f for _, f, _ in msgs}, {"atencao", "normal"})

    def test_nunca_manda_normal_para_quem_nunca_saiu_dele(self):
        self.assertEqual(simular(mare(2, base=1.0, amplitude=0.5), COTAS), [])

    def test_repete_a_mesma_faixa_so_com_3_h_e_30_cm(self):
        pts = [(INICIO + timedelta(hours=h), 3.0 + 0.11 * h) for h in range(9)]  # 3,00 → 3,88 em 8 h
        msgs = simular(pts, COTAS)
        self.assertEqual([f for _, f, _ in msgs], ["atencao", "atencao", "atencao"])


class Alternativas(unittest.TestCase):
    def test_histerese_corta_as_voltas_ao_normal_sem_atrasar_a_subida(self):
        # Base 2,95 m e 0,40 m de maré: a baixa-mar (2,75) não desce 0,30 abaixo da cota.
        pts = mare(2, base=2.95, amplitude=0.40)
        hoje, com = simular(pts, COTAS), simular(pts, COTAS, histerese_m=0.30)
        self.assertGreaterEqual(len(hoje), 6)
        self.assertEqual([f for _, f, _ in com], ["atencao"])
        self.assertEqual(hoje[0][0], com[0][0], "a primeira subida tem de sair na mesma leitura")

    def test_histerese_so_segura_na_descida(self):
        self.assertEqual(faixa_com_histerese(2.85, COTAS, "atencao", 0.30), "atencao")
        self.assertEqual(faixa_com_histerese(2.65, COTAS, "atencao", 0.30), "normal")
        self.assertEqual(faixa_com_histerese(4.10, COTAS, "atencao", 0.30), "alerta")

    def test_persistencia_atrasa_no_maximo_o_proprio_prazo_numa_cheia_de_verdade(self):
        # Base subindo 10 cm/h a partir de 2,50, sem maré: passa de 3,00 em 5 h e fica.
        pts = mare(2, base=2.50, amplitude=0.0, subida_por_h=0.10)
        hoje = simular(pts, COTAS)
        com = simular(pts, COTAS, persistencia_min=120)
        atraso = (com[0][0] - hoje[0][0]).total_seconds() / 60
        self.assertGreaterEqual(atraso, 120)
        self.assertLessEqual(atraso, 130)
        self.assertTrue(any(f == "alerta" for _, f, _ in com), "a cheia de verdade ainda chega ao alerta")

    def test_persistencia_cala_a_preamar_que_mal_toca_a_cota(self):
        pts = mare(2, base=2.70, amplitude=0.62)  # pico em 3,01: fica minutos acima
        self.assertTrue(simular(pts, COTAS))
        self.assertEqual(simular(pts, COTAS, persistencia_min=120), [])


class Episodios(unittest.TestCase):
    def test_separa_por_18_h_abaixo(self):
        pts = [(INICIO, 3.2), (INICIO + timedelta(hours=10), 3.1), (INICIO + timedelta(hours=40), 3.3)]
        self.assertEqual(len(episodios(pts, 3.0)), 2)


if __name__ == "__main__":
    unittest.main()
