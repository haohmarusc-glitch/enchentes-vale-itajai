#!/usr/bin/env python3
"""Testes da velocidade de subida (cm/h) de uma cheia."""
from __future__ import annotations

import json
import sys
import tempfile
import unittest
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import subida_cheia as sc  # noqa: E402

T0 = datetime(2026, 9, 11, 12, 0)


def serie(*niveis: float, passo_min: int = 15) -> list[sc.Ponto]:
    return [(T0 + timedelta(minutes=i * passo_min), v) for i, v in enumerate(niveis)]


class Interpolacao(unittest.TestCase):
    def test_entre_duas_leituras_e_linear(self):
        s = serie(1.0, 2.0)
        self.assertAlmostEqual(sc.interpolar(s, T0 + timedelta(minutes=7.5)), 1.5)

    def test_sobre_uma_leitura_devolve_a_propria(self):
        self.assertEqual(sc.interpolar(serie(1.0, 2.0, 3.0), T0 + timedelta(minutes=15)), 2.0)

    def test_fora_da_serie_e_none(self):
        s = serie(1.0, 2.0)
        self.assertIsNone(sc.interpolar(s, T0 - timedelta(minutes=1)))
        self.assertIsNone(sc.interpolar(s, T0 + timedelta(hours=5)))

    def test_nao_interpola_por_cima_de_buraco_grande(self):
        s = [(T0, 1.0), (T0 + timedelta(hours=4), 5.0)]
        self.assertIsNone(sc.interpolar(s, T0 + timedelta(hours=2)))


class MaiorSubida(unittest.TestCase):
    def test_um_metro_em_uma_hora_e_cem_cm_h(self):
        s = serie(1.0, 1.25, 1.5, 1.75, 2.0, 2.0, 2.0)  # 15 em 15 min
        taxa, quando = sc.maior_subida(s, 1)
        self.assertEqual(taxa, 100.0)
        self.assertEqual(quando, T0)

    def test_serie_so_descendo_da_taxa_negativa(self):
        taxa, _ = sc.maior_subida(serie(3.0, 2.0, 1.0, 0.5, 0.2), 1)
        self.assertLess(taxa, 0)

    def test_serie_curta_demais_e_none(self):
        self.assertIsNone(sc.maior_subida(serie(1.0, 2.0), 1))


class Saltos(unittest.TestCase):
    def test_pega_meio_metro_em_dez_minutos_e_ignora_subida_lenta(self):
        s = [(T0, 1.0), (T0 + timedelta(minutes=10), 1.62), (T0 + timedelta(minutes=40), 1.7)]
        self.assertEqual(sc.saltos_suspeitos(s), [("11/09 12:00", 1.0, 1.62)])
        self.assertEqual(sc.saltos_suspeitos(serie(1.0, 1.3, 1.6, 1.9)), [])


class Leitura(unittest.TestCase):
    def test_resgate_e_estacao_propria_e_nulo_e_ignorado(self):
        linhas = [
            {"estacao": "X", "rio": "r", "cidade": "c", "medido_em": "2026-09-11T12:00:00", "nivel_m": 1.0},
            {"estacao": "X", "rio": "r", "cidade": "c", "medido_em": "2026-09-11T12:00:00", "nivel_m": 1.0},
            {"estacao": "X (resgate)", "rio": "r", "cidade": "c", "medido_em": "2026-09-11T12:00:00", "nivel_m": 1.1, "resgate_de": "X"},
            {"estacao": "X", "rio": "r", "cidade": "c", "medido_em": "2026-09-11T12:15:00", "nivel_m": None},
        ]
        tmp = Path(tempfile.mkdtemp()) / "s.ndjson"
        tmp.write_text("\n".join(json.dumps(x) for x in linhas) + "\n", encoding="utf-8")
        s = sc.ler_ndjson(tmp)
        self.assertEqual(len(s[("X", "r", "c")]), 1)  # duplicata e nulo fora
        self.assertIn(("X (resgate)", "r", "c"), s)


class BrutoReal(unittest.TestCase):
    """Contra a cheia de 11–12/09/2026. Trava os números do doc do evento."""

    @classmethod
    def setUpClass(cls):
        if not sc.PADRAO.exists():
            raise unittest.SkipTest("série da cheia ausente")
        cls.res = {s.estacao: s for s in sc.relatorio()}

    def test_blumenau_alertablu(self):
        s = self.res["Blumenau (AlertaBlu)"]
        self.assertEqual((s.crista_m, s.crista_em), (7.86, "12/09 05:00"))
        self.assertEqual((s.max_1h_cm_h, s.max_1h_em), (62.0, "11/09 18:00"))
        self.assertEqual(s.saltos, [])

    def test_rio_do_sul(self):
        s = self.res["Rio do Sul, Ponte Dom Tito Buss (Asthon)"]
        self.assertEqual((s.crista_m, s.crista_em), (5.89, "11/09 23:12"))
        self.assertEqual(s.max_1h_cm_h, 34.5)

    def test_o_salto_da_dc02_fica_listado_nao_apagado(self):
        s = self.res["DC-02 Rio Itajaí-Açu - Praça Celso Pereira da Silva"]
        self.assertEqual(s.saltos, [("11/09 15:01", 0.95, 1.57)])

    def test_series_de_uma_leitura_ficam_de_fora(self):
        self.assertNotIn("Indaial — fundos da Celesc (Defesa Civil)", self.res)


if __name__ == "__main__":
    unittest.main()
