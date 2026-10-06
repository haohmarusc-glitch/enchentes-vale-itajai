#!/usr/bin/env python3
"""
Testes do inventário das réguas (scripts/inventario_reguas.py, auditoria de 06/10/2026).

Trava: o relatório em docs/ está em dia com o cadastro; toda cidade com código DCSC bate com a ficha da
MESMA estação (até 50 m), fora Blumenau, cujo código é de pluviômetro e que o cadastro já declara sem
régua; e a estação que o cadastro diz que não é régua (DCSC-00178) nunca vira candidata.
"""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import inventario_reguas as inv  # noqa: E402


class Inventario(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.estacoes, cls.dcsc, cls.tracados = inv.carregar()
        cls.linhas = {l["id"]: l for l in inv.inventario(cls.estacoes, cls.dcsc, cls.tracados)}

    def test_relatorio_em_dia(self):
        esperado = inv.relatorio(list(self.linhas.values()), self.estacoes)
        self.assertEqual(
            inv.SAIDA.read_text(encoding="utf-8"),
            esperado,
            "docs/INVENTARIO-REGUAS.md desatualizado: rode python3 scripts/inventario_reguas.py --gravar",
        )

    def test_codigo_dcsc_bate_com_a_ficha_da_mesma_estacao(self):
        for l in self.linhas.values():
            if not l["codigo"] or l["sao_da_regua"] is False:
                continue
            self.assertEqual(l["tipo"], "Hidro", f"{l['id']}: {l['codigo']} não é estação de nível")
            self.assertLess(l["dist_ficha_km"], 0.05, f"{l['id']}: {l['dist_ficha_km']:.3f} km da ficha {l['codigo']}")

    def test_blumenau_marcada_aproximada(self):
        b = self.linhas["blumenau"]
        self.assertEqual(b["tipo"], "Meteo")
        self.assertIs(b["sao_da_regua"], False)
        self.assertIn("aproximada", inv.situacao(b))

    def test_estacao_que_nao_e_regua_nunca_vira_candidata(self):
        for l in self.linhas.values():
            self.assertNotIn("DCSC-00178", [c[0] for c in l["candidatas"]], l["id"])

    def test_distancia(self):
        # 0,01° de latitude ≈ 1,112 km em qualquer longitude.
        self.assertAlmostEqual(inv.km(-27.0, -49.0, -27.01, -49.0), 1.112, places=2)


if __name__ == "__main__":
    unittest.main()
