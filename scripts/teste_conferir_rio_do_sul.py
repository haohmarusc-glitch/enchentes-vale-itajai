#!/usr/bin/env python3
"""
Testes da conferência de Rio do Sul contra a transcrição da NSC.

Duas leituras independentes da mesma tabela oficial são a conferência mais
barata que este projeto tem. Estes testes garantem que a comparação continua
sendo feita de verdade — e que a rua que faltava não some de novo.
"""

import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from conferir_rio_do_sul_nsc import (
    BRUTO, CIDADE, comparar, e_numero, normalizar, por_rua,
)
from comum import DADOS


class TestNormalizar(unittest.TestCase):
    def test_grafias_diferentes_da_mesma_rua_nao_se_juntam_sozinhas(self):
        # Meneghetti/Menegetti diferem por uma letra: são chaves distintas.
        # A conferência não tenta adivinhar; ela mostra e a pessoa decide.
        self.assertNotEqual(normalizar("Frederico Menegetti"), normalizar("FREDERICO MENEGHETTI"))

    def test_acento_e_caixa_nao_separam(self):
        self.assertEqual(normalizar("Visconde de Cairu"), normalizar("VISCONDE DE CAIRU"))
        self.assertEqual(normalizar("Jurací"), normalizar("JURACI"))

    def test_prefixo_e_pontuacao_somem(self):
        self.assertEqual(normalizar("Rua Dr. Blumenau"), "DR BLUMENAU")
        self.assertEqual(normalizar("Av. Sete-de-Setembro"), "SETE DE SETEMBRO")

    def test_so_o_primeiro_prefixo(self):
        self.assertEqual(normalizar("Rua Estrada Nova"), "ESTRADA NOVA")


class TestPorRua(unittest.TestCase):
    def test_guarda_a_menor_cota_da_rua(self):
        r = por_rua([{"rua": "X", "c": 9.0}, {"rua": "Rua X", "c": 7.5}, {"rua": "X", "c": 8.0}], "c")
        self.assertEqual(r, {"X": 7.5})

    def test_ignora_quem_nao_tem_numero(self):
        r = por_rua([{"rua": "X", "c": None}, {"rua": "Y", "c": True}, {"rua": "Z", "c": 3.0}], "c")
        self.assertEqual(r, {"Z": 3.0})

    def test_booleano_nao_e_numero(self):
        self.assertFalse(e_numero(True))
        self.assertTrue(e_numero(0))


class TestComparar(unittest.TestCase):
    def test_acha_divergencia_de_valor(self):
        r = comparar({"A": 5.0, "B": 7.0}, {"A": 5.0, "B": 7.5})
        self.assertEqual(r["iguais"], 1)
        self.assertEqual(r["divergentes"], [{"rua": "B", "nosso_m": 7.0, "deles_m": 7.5}])

    def test_diferenca_menor_que_um_centavo_nao_conta(self):
        r = comparar({"A": 5.0}, {"A": 5.004})
        self.assertEqual(r["divergentes"], [])

    def test_separa_o_que_e_de_cada_lado(self):
        r = comparar({"A": 1.0, "SO_NOSSO": 2.0}, {"A": 1.0, "SO_DELES": 3.0})
        self.assertEqual(r["so_nosso"], ["SO_NOSSO"])
        self.assertEqual(r["so_deles"], ["SO_DELES"])


class TestArquivosReais(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.brutos = json.loads((DADOS / BRUTO).read_text(encoding="utf-8"))["cotas"]
        cls.nossos = [
            r
            for r in json.loads((DADOS / "cotas-ruas.json").read_text(encoding="utf-8"))["cotas"]
            if r.get("cidade") == CIDADE
        ]

    def test_as_duas_fontes_nao_divergem_em_nenhum_valor(self):
        r = comparar(por_rua(self.nossos, "cota_m"), por_rua(self.brutos, "cota_minima_m"))
        self.assertEqual(r["divergentes"], [], "duas leituras da mesma tabela têm de bater")
        self.assertGreater(r["iguais"], 500, "a conferência precisa cobrir a lista quase toda")

    def test_temos_as_555_ruas_que_o_portal_declara(self):
        self.assertEqual(len(self.nossos), 555)

    def test_visconde_de_cairu_esta_no_cadastro(self):
        achado = [r for r in self.nossos if normalizar(r["rua"]) == "VISCONDE DE CAIRU"]
        self.assertEqual(len(achado), 1, "a rua que faltava não pode sumir de novo")
        self.assertEqual(achado[0]["cota_m"], 19.01)

    def test_cairu_e_maua_continuam_sendo_ruas_diferentes(self):
        nomes = {normalizar(r["rua"]) for r in self.nossos}
        self.assertIn("VISCONDE DE CAIRU", nomes)
        self.assertIn("VISCONDE DE MAUA", nomes)

    def test_cairu_nao_se_passa_por_dado_do_portal(self):
        """Veio do jornal, não do portal: confiança media e sem cota máxima."""
        cairu = next(r for r in self.nossos if normalizar(r["rua"]) == "VISCONDE DE CAIRU")
        self.assertEqual(cairu["confianca"], "media")
        self.assertIsNone(cairu.get("cota_max_m"))
        self.assertIn("NSC", cairu["fonte"])

    def test_as_outras_continuam_vindo_do_portal(self):
        do_portal = [r for r in self.nossos if r.get("confianca") == "alta"]
        self.assertEqual(len(do_portal), 554)


if __name__ == "__main__":
    unittest.main(verbosity=2)
