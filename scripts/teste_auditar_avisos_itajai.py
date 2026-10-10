#!/usr/bin/env python3
"""Testes da auditoria de travas e histerese de Itajaí (10/10/2026), com séries sintéticas."""

import sys
import unittest
from datetime import date, datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import auditar_avisos_itajai as A  # noqa: E402

COTAS = {"atencao": 3.0, "alerta": 4.0, "emergencia": 5.0}
T0 = datetime(2026, 9, 1, 0, 0)


def serie(*niveis, passo_min=10):
    return [(T0 + timedelta(minutes=passo_min * i), v) for i, v in enumerate(niveis)]


class TesteReproduzir(unittest.TestCase):
    def test_subida_avisa_na_mesma_leitura_com_ou_sem_histerese(self):
        s = serie(2.8, 2.9, 3.0, 3.1)
        for h in (0.0, 0.30):
            m = A.reproduzir(s, COTAS, h)
            self.assertEqual(m[0][0], s[2][0])
            self.assertEqual(m[0][3], "atencao")

    def test_reentrada_dentro_da_histerese_nao_repete_e_fora_dela_repete(self):
        dentro = serie(3.1, 2.9, 3.1)  # desceu 0,10 abaixo da cota
        fora = serie(3.1, 2.6, 3.1)    # desceu 0,40 abaixo da cota
        self.assertEqual(len(A.reproduzir(dentro, COTAS, 0.30)), 1)
        self.assertEqual(len(A.reproduzir(dentro, COTAS, 0.0)), 3)
        self.assertEqual(len(A.reproduzir(fora, COTAS, 0.30)), 3, "atenção, normal, atenção")

    def test_subida_para_faixa_mais_alta_nunca_e_segurada(self):
        s = serie(3.1, 2.9, 4.1)
        m = A.reproduzir(s, COTAS, 0.30)
        self.assertEqual([x[3] for x in m], ["atencao", "alerta"])

    def test_repeticao_por_30_cm_depois_de_3_h(self):
        s = serie(*([3.0] + [3.1] * 17 + [3.31]))  # 3 h depois, 31 cm acima do aviso
        m = A.reproduzir(s, COTAS, 0.30)
        self.assertEqual([x[2] == x[3] for x in m], [False, True])


class TesteComparar(unittest.TestCase):
    def test_conta_o_que_some_e_prova_que_nenhuma_faixa_mais_alta_some(self):
        s = serie(3.1, 2.9, 3.1, 2.95, 4.2, 3.8, 4.1)
        r = A.comparar_histerese(s, COTAS, 0.30)
        self.assertEqual(r["faixa_mais_alta_perdida"], [])
        self.assertTrue(all(x["horas_abaixo"] < 1 for x in r["reentradas"]))
        self.assertTrue(all(not x["desceu_alem_da_histerese"] for x in r["reentradas"]))
        self.assertEqual(r["episodios"][0]["atraso_h"], 0.0)

    def test_liberacao_por_tempo_devolve_o_aviso_de_nova_subida(self):
        # 7 h a 2,90 m (abaixo da cota, dentro da histerese) e nova subida.
        s = serie(*([3.1] + [2.9] * 42 + [3.1]))
        self.assertEqual(len(A.reproduzir(s, COTAS, 0.30)), 1)
        self.assertEqual(len(A.com_liberacao_por_tempo(s, COTAS, 0.30, 6)), 3)
        # A reprodução com a regra do motor (`liberar_por_tempo`) dá o mesmo.
        self.assertEqual(len(A.reproduzir(s, COTAS, 0.30, 6)), 3)


class TesteZero(unittest.TestCase):
    def test_base_em_dia_parado_separa_antes_e_depois_da_troca(self):
        pts = []
        for dia, base in ((date(2026, 9, 17), 0.96), (date(2026, 9, 27), 1.01)):
            inicio = datetime(dia.year, dia.month, dia.day)
            pts += [(inicio + timedelta(minutes=20 * i), base) for i in range(72)]
        self.assertEqual(A.base_em_dia_parado(pts), ([0.96], [1.01]))


if __name__ == "__main__":
    unittest.main()
