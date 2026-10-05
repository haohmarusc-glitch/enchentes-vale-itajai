"""Trava a tabela ruas × manchas de Itajaí (scripts/ruas_por_mancha_itajai.py, 05/10/2026)."""
import json
import unittest

from ruas_por_mancha_itajai import SAIDA, calcular, serializar


class RuasPorMancha(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tabela = calcular()

    def test_arquivo_salvo_e_o_recalculado(self):
        # Mudou a base de vias ou uma mancha? Rodar o script de novo e commitar a tabela.
        self.assertEqual(SAIDA.read_text(encoding="utf-8"), serializar(self.tabela))

    def test_rua_do_exemplo(self):
        r = self.tabela["ruas"]["R.José Domingos Machado"]
        self.assertEqual(r["m"], 1014)
        self.assertEqual(r["ev"]["2011-09"]["pct"], 100)
        self.assertEqual(r["ev"]["2011-09"]["lamina"], {"0,51 a 1": 760, "1,01 a 1,50": 137, "1,51 a 2": 117})
        self.assertEqual(r["ev"]["2001"]["pct"], 52)
        self.assertNotIn("2013-07", r["ev"])

    def test_nove_cheias_e_valores_coerentes(self):
        eventos = {e["evento"] for e in self.tabela["_meta"]["eventos"]}
        self.assertEqual(len(eventos), 9)
        for nome, r in self.tabela["ruas"].items():
            for ev, v in r["ev"].items():
                self.assertIn(ev, eventos)
                self.assertTrue(0 <= v["pct"] <= 100 and v["m"] <= r["m"] + 1, (nome, ev, v))
        json.dumps(self.tabela)  # serializável


if __name__ == "__main__":
    unittest.main()
