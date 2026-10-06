"""Trava o download do Benedito, do Itajaí do Sul e do Trombudo (scripts/baixar_tracados_afluentes.py)."""
import unittest

import baixar_tracados_afluentes as ba

TIMBO = ba.pino("timbo")
ITUPORANGA = ba.pino("ituporanga")
TROMBUDO = ba.pino("trombudo-central")
ACU = [(-49.27, -26.92), (-49.63, -27.21)]


def way(nome, pontos):
    return {"type": "way", "tags": {"name": nome, "waterway": "river"},
            "geometry": [{"lon": lo, "lat": la} for lo, la in pontos]}


BENEDITO = way("Rio Benedito", [(-49.27, -26.75), TIMBO, (-49.271, -26.919)])
SUL = way("Rio Itajaí do Sul", [(-49.40, -27.70), ITUPORANGA, (-49.631, -27.209)])
TROMBUDO_W = way("Rio Trombudo", [(-49.85, -27.40), TROMBUDO, (-49.70, -27.25)])


class Conferencia(unittest.TestCase):
    def test_rio_que_chega_e_passa_pela_regua_e_aceito(self):
        self.assertEqual(ba.conferir("benedito", ba.linhas([BENEDITO], ("Rio Benedito",)), {"itajai-acu": ACU}, TIMBO), [])
        self.assertEqual(ba.conferir("itajai-do-sul", ba.linhas([SUL], ("Rio Itajaí do Sul",)), {"itajai-acu": ACU}, ITUPORANGA), [])

    def test_trombudo_pode_chegar_ao_itajai_do_sul_baixado_na_rodada(self):
        sul = [(-49.70, -27.251)]
        ls = ba.linhas([TROMBUDO_W], ("Rio Trombudo",))
        self.assertEqual(ba.conferir("trombudo", ls, {"itajai-acu": [(-48.9, -26.9)], "itajai-do-sul": sul}, TROMBUDO), [])
        self.assertTrue(any("não chega" in p for p in ba.conferir("trombudo", ls, {"itajai-acu": [(-48.9, -26.9)]}, TROMBUDO)))

    def test_nao_passa_pela_regua_e_recusado(self):
        ls = ba.linhas([BENEDITO], ("Rio Benedito",))
        self.assertTrue(any("régua de timbo" in p for p in ba.conferir("benedito", ls, {"itajai-acu": ACU}, (-49.0, -26.5))))

    def test_nome_parecido_nao_entra(self):
        self.assertEqual(ba.linhas([way("Ribeirão Benedito Novo", [(-49.3, -26.8), (-49.2, -26.9)])], ("Rio Benedito",)), [])
        self.assertTrue(any("nenhum way" in p for p in ba.conferir("benedito", [], {"itajai-acu": ACU}, TIMBO)))

    def test_consulta_pede_o_nome_exato_na_caixa_do_rio(self):
        q = ba.consulta("itajai-do-sul")
        self.assertIn('"^Rio (Itajaí do Sul)$"', q)
        self.assertIn("(-27.9,-49.8,-27.15,-49.1)", q)


if __name__ == "__main__":
    unittest.main()
