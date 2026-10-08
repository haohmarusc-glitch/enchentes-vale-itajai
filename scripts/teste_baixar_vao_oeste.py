#!/usr/bin/env python3
"""
Testes do vão do Itajaí do Oeste, sem rede.

Fixam o que decide gravar: a falha tem de estar aberta no bruto, a cadeia tem de ligar as duas pontas, e o
comprimento dela tem de ser de rio, não de volta por afluente.
"""
import json
import unittest

import baixar_vao_oeste as bo

A = bo.PONTA_MONTANTE
B = bo.PONTA_JUSANTE


def via(id_, pontos, nome=None, tipo="river"):
    return {"type": "way", "id": id_,
            "geometry": [{"lon": p[0], "lat": p[1]} for p in pontos],
            "tags": {"waterway": tipo, **({"name": nome} if nome else {})}}


def meio(fracao, desvio_lat=0.0):
    return (A[0] + (B[0] - A[0]) * fracao, A[1] + (B[1] - A[1]) * fracao + desvio_lat)


class FalhaAberta(unittest.TestCase):
    def test_o_bruto_de_hoje_tem_a_falha(self):
        tronco = json.loads(bo.BRUTO_TRONCO.read_text(encoding="utf-8"))["elements"]
        self.assertTrue(bo.falha_aberta(tronco))

    def test_falha_fechada_por_uma_via_do_oeste_nao_e_falha(self):
        montante = via(1, [(-49.95, -27.13), A], bo.NOME_OESTE)
        ponte = via(2, [A, B], bo.NOME_OESTE)
        jusante = via(3, [B, (-49.86, -27.16)], bo.NOME_OESTE)
        self.assertFalse(bo.falha_aberta([montante, ponte, jusante]))
        self.assertTrue(bo.falha_aberta([montante, jusante]))


class ConferirCadeia(unittest.TestCase):
    def test_sem_cadeia_nao_grava(self):
        problemas, _ = bo.conferir_cadeia([])
        self.assertTrue(problemas)

    def test_cadeia_sem_nome_com_curvas_de_rio_passa(self):
        cadeia = [via(10, [A, meio(0.3, 0.002), meio(0.6, -0.002)]), via(11, [meio(0.6, -0.002), B])]
        problemas, medidas = bo.conferir_cadeia(cadeia)
        self.assertEqual(problemas, [])
        self.assertGreater(medidas["sinuosidade"], 1.0)
        self.assertEqual([v["name"] for v in medidas["vias"]], [None, None])

    def test_volta_longa_por_afluente_e_recusada(self):
        longe = (A[0], A[1] - 0.05)  # ~5,5 km ao sul e de volta
        cadeia = [via(20, [A, longe], tipo="stream"), via(21, [longe, B], tipo="stream")]
        problemas, medidas = bo.conferir_cadeia(cadeia)
        self.assertTrue(any("afluente" in p for p in problemas), problemas)
        self.assertGreater(medidas["sinuosidade"], bo.SINUOSIDADE_MAX)


class Encadeamento(unittest.TestCase):
    def test_acha_a_ponte_entre_as_pontas_e_ignora_o_que_nao_liga(self):
        solta = via(30, [meio(0.5, 0.01), meio(0.5, 0.02)], "Ribeirão Qualquer", "stream")
        a1 = via(31, [A, meio(0.5)])
        a2 = via(32, [B, meio(0.5)])  # desenhada ao contrário: também liga
        cadeia = bo.encadear([solta, a1, a2], A, [B])
        self.assertEqual([v["id"] for v in cadeia], [31, 32])


class Caixa(unittest.TestCase):
    def test_a_caixa_contem_as_duas_pontas_com_folga(self):
        s, o, n, l = bo.caixa()
        for lon, lat in (A, B):
            self.assertTrue(s < lat < n and o < lon < l)
        self.assertIn('way["waterway"]', bo.consulta())


if __name__ == "__main__":
    unittest.main()
