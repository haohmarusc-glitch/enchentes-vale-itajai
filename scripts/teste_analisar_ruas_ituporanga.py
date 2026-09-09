#!/usr/bin/env python3
"""Testes do analisador das cotas de rua de Ituporanga.

O que não pode falhar: o ponto de 27,77 m tem de ser recusado (não somado), e
o bruto real tem de continuar com 60 pontos, 59 válidos, de 3,38 a 10,48 m.

    python3 scripts/teste_analisar_ruas_ituporanga.py
"""

import unittest

from analisar_ruas_ituporanga import (BRUTO, acima_do_teto, carregar, cercam,
                                      fora_do_perimetro, resumo, separar_lixo)

P = [
    {"cota_m": 3.38, "local": "A", "lat": -27.43, "lon": -49.60},
    {"cota_m": 3.10, "local": "B", "lat": -27.42, "lon": -49.60},
    {"cota_m": 7.00, "local": "C", "lat": -27.42, "lon": -49.61},
    {"cota_m": 27.77, "local": "Garagem", "lat": -27.42, "lon": -49.60},
    {"cota_m": 5.00, "local": "Longe", "lat": -27.50, "lon": -49.60},
]


class Lixo(unittest.TestCase):
    def test_27_77_e_recusado_e_nao_entra_na_conta(self):
        validos, lixo = separar_lixo(P)
        self.assertEqual([p["local"] for p in lixo], ["Garagem"])
        self.assertEqual(len(validos), 4)
        r = resumo(P)
        self.assertEqual(r["max_m"], 7.0)
        self.assertEqual(r["lixo"], [("Garagem", 27.77)])


class Leituras(unittest.TestCase):
    def test_acima_do_teto_das_manchas(self):
        self.assertEqual([p["local"] for p in acima_do_teto(P[:3])], ["C"])

    def test_cercam_3_25(self):
        a, b = cercam(P[:3])
        self.assertEqual((a["local"], b["local"]), ("B", "A"))

    def test_ponto_a_9_km_fica_fora_do_perimetro(self):
        fora = fora_do_perimetro([p for p in P if p["local"] != "Garagem"])
        self.assertEqual([p["local"] for p, _ in fora], ["Longe"])


class BrutoReal(unittest.TestCase):
    def test_o_bruto_transcrito_tem_60_pontos_59_validos(self):
        if not BRUTO.exists():
            self.skipTest("bruto ausente")
        r = resumo(carregar())
        self.assertEqual((r["total"], r["validos"]), (60, 59))
        self.assertEqual((r["min_m"], r["max_m"]), (3.38, 10.48))
        self.assertEqual(r["lixo"], [("Prefeitura Garagem", 27.77)])
        self.assertEqual(r["fora_do_perimetro"], [])


if __name__ == "__main__":
    unittest.main()
