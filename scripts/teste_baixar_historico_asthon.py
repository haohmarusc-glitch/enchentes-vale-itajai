"""O acervo da Asthon: fuso convertido na entrada e mescla sem perder o antigo.

A API guarda ~6 semanas e entrega UTC. Ler UTC como local desloca a série
3 h; sobrescrever o CSV joga fora o que a API já descartou.
"""

from __future__ import annotations

import csv
import tempfile
import unittest
from pathlib import Path

from baixar_historico_asthon import COLUNAS, PADRAO_SAIDA, limpar, mesclar, para_local


class Fuso(unittest.TestCase):
    def test_utc_vira_brasilia_sem_fuso(self):
        self.assertEqual(para_local("2026-09-09T22:56:45.871Z"), "2026-09-09 19:56:45")

    def test_carimbo_invalido_fica_como_veio_e_visivel(self):
        self.assertEqual(para_local("ontem"), "ontem")


class NomeDeArquivo(unittest.TestCase):
    def test_tira_o_que_o_windows_recusa(self):
        self.assertEqual(limpar("Ponte Dom Tito Buss"), "ponte_dom_tito_buss")
        self.assertEqual(limpar('Barragem "Sul": x/y'), "barragem_-sul--_x-y")
        self.assertEqual(limpar("   "), "estacao")


class Mescla(unittest.TestCase):
    def test_acumula_sem_perder_o_antigo_e_substitui_o_mesmo_carimbo(self):
        with tempfile.TemporaryDirectory() as d:
            destino = Path(d) / "x.csv"
            n1 = mesclar(destino, [
                {"timestamp": "2026-09-01T03:00:00.000Z", "value": 1.10},
                {"timestamp": "2026-09-01T03:10:00.000Z", "value": 1.12},
            ], "gauge_zero")
            self.assertEqual(n1, 2)
            n2 = mesclar(destino, [
                {"timestamp": "2026-09-01T03:10:00.000Z", "value": 1.13},   # corrigido pela API
                {"timestamp": "2026-09-01T03:20:00.000Z", "value": None},   # ausente, não zero
                {"timestamp": "2026-09-01T03:30:00.000Z", "value": 1.15},
            ], "gauge_zero")
            self.assertEqual(n2, 3)
            with destino.open(encoding="utf-8", newline="") as f:
                linhas = list(csv.DictReader(f))
            self.assertEqual([l["medido_em"] for l in linhas],
                             ["2026-09-01 00:00:00", "2026-09-01 00:10:00", "2026-09-01 00:30:00"])
            self.assertEqual(linhas[1]["nivel_m"], "1.13")
            self.assertEqual(linhas[0]["medido_em_utc"], "2026-09-01T03:00:00.000Z")
            self.assertEqual(list(linhas[0]), COLUNAS)

    def test_cria_a_pasta_de_destino(self):
        with tempfile.TemporaryDirectory() as d:
            destino = Path(d) / "sub" / "x.csv"
            mesclar(destino, [{"timestamp": "2026-09-01T03:00:00.000Z", "value": 1.0}], "gauge_zero")
            self.assertTrue(destino.exists())


class Destino(unittest.TestCase):
    def test_padrao_e_em_brutos(self):
        self.assertEqual(PADRAO_SAIDA.parts[-2:], ("brutos", "asthon-historico"))


if __name__ == "__main__":
    unittest.main()
