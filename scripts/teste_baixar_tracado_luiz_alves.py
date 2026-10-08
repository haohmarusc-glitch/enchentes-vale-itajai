#!/usr/bin/env python3
"""Testes do download do Rio Luiz Alves, sem rede: o que decide gravar."""
import unittest

import baixar_tracado_luiz_alves as bl

ACU = [(-48.83, -26.90), (-48.80, -26.91)]


def via(nome, pontos):
    return {"type": "way", "id": 1, "tags": {"waterway": "river", "name": nome},
            "geometry": [{"lon": p[0], "lat": p[1]} for p in pontos]}


#: ~11 km de norte a sul, terminando no primeiro ponto do Açu.
RIO = [(-48.83, -26.80), (-48.83, -26.85), (-48.83, -26.90)]


class Conferir(unittest.TestCase):
    def test_rio_que_chega_ao_acu_passa(self):
        self.assertEqual(bl.conferir(bl.linhas([via("Rio Luiz Alves", RIO)]), ACU), [])

    def test_as_tres_grafias_do_nome_contam(self):
        for nome in ("Rio Luiz Alves", "Rio Luís Alves", "Rio Luis Alves"):
            self.assertEqual(list(bl.linhas([via(nome, RIO)])), [nome])
        self.assertEqual(bl.linhas([via("Ribeirão Luiz Alves", RIO)]), {})

    def test_rio_que_nao_chega_ao_acu_e_recusado(self):
        longe = [(lon, lat + 0.05) for lon, lat in RIO]  # ~5,5 km ao norte
        problemas = bl.conferir(bl.linhas([via("Rio Luiz Alves", longe)]), ACU)
        self.assertTrue(any("não chega ao Açu" in p for p in problemas), problemas)

    def test_pedaco_curto_e_recusado(self):
        curto = [(-48.83, -26.89), (-48.83, -26.90)]  # ~1 km
        problemas = bl.conferir(bl.linhas([via("Rio Luiz Alves", curto)]), ACU)
        self.assertTrue(any("pedaço" in p for p in problemas), problemas)

    def test_sem_nada_e_recusado(self):
        self.assertTrue(bl.conferir({}, ACU))

    def test_consulta_pede_as_tres_grafias(self):
        texto = bl.consulta()
        for nome in bl.NOMES:
            self.assertIn(nome, texto)


if __name__ == "__main__":
    unittest.main()
