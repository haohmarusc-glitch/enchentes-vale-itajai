#!/usr/bin/env python3
"""Testes do trânsito em Python, amarrados ao gabarito do site.

Este é o teste que impede o bot e o site de darem respostas diferentes para a
mesma pergunta. O gabarito (`data/transito-esperado.json`) é gerado a partir do
`transito.ts` do site; aqui a implementação Python tem de reproduzi-lo par a
par, sem exceção.

Se este teste ficar vermelho, NÃO ajuste o gabarito para calar o teste: ou o
Python divergiu do site, ou alguém mudou o site sem regerar. Nos dois casos a
pergunta é qual dos dois está certo.

    python3 scripts/teste_transito.py
"""

import unittest
from datetime import datetime

from comum import le_json
from transito import caminho, como_gabarito, faixa_horas, janela_chegada, pior_confianca


class TestGabarito(unittest.TestCase):
    def setUp(self):
        self.trechos = le_json("transito.json")["trechos"]
        self.gabarito = le_json("transito-esperado.json")["caminhos"]

    def test_o_gabarito_nao_esta_vazio(self):
        """Um gabarito vazio passaria em tudo sem provar nada."""
        self.assertGreater(len(self.gabarito), 50)
        com_caminho = [g for g in self.gabarito if g["resultado"] is not None]
        self.assertGreater(len(com_caminho), 10, "nenhum caminho conhecido: gabarito suspeito")

    def test_python_reproduz_o_site_par_a_par(self):
        divergentes = []
        for g in self.gabarito:
            obtido = como_gabarito(caminho(self.trechos, g["rio"], g["de"], g["para"]))
            if obtido != g["resultado"]:
                divergentes.append(
                    f"{g['rio']} {g['de']}->{g['para']}: "
                    f"site={g['resultado']} python={obtido}"
                )
        self.assertEqual(divergentes, [], "\n".join(divergentes))


class TestRegras(unittest.TestCase):
    TRECHOS = [
        {"rio": "r", "de": "a", "para": "b", "horas_min": 2, "horas_max": 3,
         "confianca": "alta", "fonte": "F1"},
        {"rio": "r", "de": "b", "para": "c", "horas_min": 1, "horas_max": 1,
         "confianca": "baixa", "fonte": "F2"},
        {"rio": "r", "de": "a", "para": "c", "horas_min": 9, "horas_max": 9,
         "confianca": "media", "fonte": "F3"},
        {"rio": "outro", "de": "c", "para": "d", "horas_min": 1, "horas_max": 1,
         "confianca": "alta", "fonte": "F4"},
    ]

    def test_trecho_direto_ganha_do_encadeado(self):
        """Menos elos, menos incerteza acumulada — mesmo com número maior."""
        c = caminho(self.TRECHOS, "r", "a", "c")
        self.assertTrue(c.direto)
        self.assertEqual((c.horas_min, c.horas_max), (9, 9))

    def test_encadeia_quando_nao_ha_direto(self):
        sem_direto = [t for t in self.TRECHOS if not (t["de"] == "a" and t["para"] == "c")]
        c = caminho(sem_direto, "r", "a", "c")
        self.assertFalse(c.direto)
        self.assertEqual((c.horas_min, c.horas_max), (3, 4))
        self.assertEqual(c.confianca, "baixa", "o elo mais fraco derruba o conjunto")
        self.assertEqual(c.fontes, ["F1", "F2"])

    def test_nao_atravessa_rios(self):
        self.assertIsNone(caminho(self.TRECHOS, "r", "a", "d"))

    def test_cidade_para_ela_mesma_nao_e_caminho(self):
        self.assertIsNone(caminho(self.TRECHOS, "r", "a", "a"))

    def test_sem_caminho_devolve_none_e_nao_palpite(self):
        self.assertIsNone(caminho(self.TRECHOS, "r", "c", "a"))

    def test_pior_confianca(self):
        self.assertEqual(pior_confianca(["alta", "alta"]), "alta")
        self.assertEqual(pior_confianca(["alta", "baixa", "media"]), "baixa")
        self.assertEqual(pior_confianca([]), "alta")


class TestTexto(unittest.TestCase):
    def um(self, mn, mx):
        return caminho([{"rio": "r", "de": "a", "para": "b", "horas_min": mn,
                         "horas_max": mx, "confianca": "alta", "fonte": "F"}], "r", "a", "b")

    def test_faixa_em_portugues(self):
        self.assertEqual(faixa_horas(self.um(14, 17)), "14–17 h")
        self.assertEqual(faixa_horas(self.um(6, 6)), "cerca de 6 h")
        self.assertEqual(faixa_horas(self.um(1.5, 2.5)), "1,5–2,5 h")

    def test_janela_de_chegada(self):
        inicio, fim = janela_chegada(datetime(2026, 8, 30, 18, 0), self.um(14, 17))
        self.assertEqual(inicio, datetime(2026, 8, 31, 8, 0))
        self.assertEqual(fim, datetime(2026, 8, 31, 11, 0))


if __name__ == "__main__":
    unittest.main(verbosity=2)
