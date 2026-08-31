#!/usr/bin/env python3
"""
Testes do importador das cotas de Blumenau.

O que se testa aqui é o que decide se alguém sai de casa: se o número que entra
é o que a fonte publicou, se pontos diferentes com descrição igual continuam
sendo pontos diferentes, e se importar duas vezes não estraga o que já estava.
"""

import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from importar_cotas_blumenau import (
    BRUTO, chave, como_registro, mesclar, normalizar, separar,
)


class TestSeparar(unittest.TestCase):
    def test_recusa_cota_fora_da_faixa_de_rio(self):
        bons, recusas = separar([
            {"rua": "Rua Alta", "cota_m": 340.0},
            {"rua": "Rua Negativa", "cota_m": -1},
            {"rua": "Rua Boa", "cota_m": 9.4},
        ])
        self.assertEqual([b["rua"] for b in bons], ["Rua Boa"])
        self.assertEqual(len(recusas), 2)

    def test_recusa_cota_que_nao_e_numero(self):
        bons, recusas = separar([{"rua": "X", "cota_m": None},
                                 {"rua": "Y", "cota_m": "9,4"},
                                 {"rua": "Z", "cota_m": True}])
        self.assertEqual(bons, [])
        self.assertEqual(len(recusas), 3, "booleano não é cota")

    def test_recusa_registro_sem_rua(self):
        bons, recusas = separar([{"rua": "  ", "cota_m": 9.4}])
        self.assertEqual(bons, [])
        self.assertIn("sem nome de rua", recusas[0])


class TestIdentidade(unittest.TestCase):
    """
    Vinte e dois pares (rua, ponto) se repetem na fonte com cotas diferentes —
    pontos distintos que ela descreve igual. Sem a cota na identidade, eles
    viram um registro só e 22 pontos somem calados.
    """

    def test_mesmo_ponto_com_cotas_diferentes_sao_registros_diferentes(self):
        a = {"cidade": "blumenau", "rua": "Rua Franz Volles", "ponto": "Sem número",
             "cota_m": 11.1}
        b = {"cidade": "blumenau", "rua": "Rua Franz Volles", "ponto": "Sem número",
             "cota_m": 16.95}
        self.assertNotEqual(chave(a), chave(b))

    def test_acento_e_caixa_nao_criam_registro_novo(self):
        a = {"cidade": "blumenau", "rua": "Rua São Rafael", "ponto": "Final", "cota_m": 7.4}
        b = {"cidade": "blumenau", "rua": "RUA SAO RAFAEL", "ponto": "final", "cota_m": 7.4}
        self.assertEqual(chave(a), chave(b))

    def test_normalizar_tira_acento_ponto_e_espaco_dobrado(self):
        self.assertEqual(normalizar("R. Dr.  Pedro   Zimmermann"), "r dr pedro zimmermann")


class TestMesclar(unittest.TestCase):
    def antigos(self) -> list[dict]:
        return [
            # O que já estava: mesmo ponto, com acento e outro texto de ponto.
            {"cidade": "blumenau", "rua": "Rua São Rafael", "ponto": "final da rua",
             "cota_m": 7.4, "confianca": "media"},
            {"cidade": "brusque", "rua": "Rua Coelho Neto", "ponto": None, "cota_m": 5.64},
        ]

    def test_nao_sobrescreve_o_nome_com_acento_pelo_sem_acento(self):
        novos = [{"cidade": "blumenau", "rua": "Rua Sao Rafael",
                  "ponto": "Final da rua (pega só uma casa)", "cota_m": 7.4}]
        saida, n, pulados = mesclar(self.antigos(), novos)
        self.assertEqual((n, pulados), (0, 1))
        self.assertEqual(saida[0]["rua"], "Rua São Rafael", "o texto melhor fica")

    def test_nao_toca_em_registro_de_outra_cidade(self):
        novos = [{"cidade": "blumenau", "rua": "Rua Nova", "ponto": "x", "cota_m": 9.0}]
        saida, n, _ = mesclar(self.antigos(), novos)
        self.assertEqual(n, 1)
        self.assertEqual(saida[1]["cidade"], "brusque")

    def test_importar_duas_vezes_da_o_mesmo_arquivo(self):
        novos = [{"cidade": "blumenau", "rua": "Rua Nova", "ponto": "x", "cota_m": 9.0}]
        uma, _, _ = mesclar(self.antigos(), novos)
        duas, n, _ = mesclar(uma, novos)
        self.assertEqual(uma, duas)
        self.assertEqual(n, 0)

    def test_mesma_rua_em_cota_diferente_entra_como_ponto_novo(self):
        novos = [{"cidade": "blumenau", "rua": "Rua São Rafael", "ponto": "Casa nº 169",
                  "cota_m": 7.75}]
        saida, n, _ = mesclar(self.antigos(), novos)
        self.assertEqual(n, 1, "outra cota é outro ponto da mesma rua")


class TestRegistro(unittest.TestCase):
    def test_campos_obrigatorios_e_referencia_regua(self):
        r = como_registro({"rua": "Rua X", "bairro": "Centro", "ponto": "Casa nº 1",
                           "cota_m": 9.4}, "2026-08-31")
        for campo in ("cidade", "rio", "rua", "cota_m", "fonte", "confianca", "referencia"):
            self.assertIn(campo, r)
        # REGRA BLOQUEANTE do CLAUDE.md, item 4: cota de rua é comparada com o
        # nível ao vivo, que é régua. Outra referência não pode entrar.
        self.assertEqual(r["referencia"], "régua")
        self.assertEqual(r["confianca"], "media", "é reprodução de imprensa, não o original")

    def test_bairro_e_ponto_vazios_viram_nulo_e_nao_string_vazia(self):
        r = como_registro({"rua": "Rua X", "bairro": "", "ponto": "", "cota_m": 9.4}, "2026")
        self.assertIsNone(r["bairro"])
        self.assertIsNone(r["ponto"])


class TestBrutoReal(unittest.TestCase):
    """
    Contra o arquivo bruto de verdade: é ele que vai virar 1.931 registros.
    """

    def setUp(self):
        self.brutos = json.loads(BRUTO.read_text(encoding="utf-8"))["cotas"]

    def test_o_bruto_esta_no_repositorio_e_tem_o_tamanho_declarado(self):
        meta = json.loads(BRUTO.read_text(encoding="utf-8"))["_meta"]
        self.assertEqual(len(self.brutos), meta["total"])
        self.assertEqual(len(self.brutos), 1938)

    def test_nenhum_registro_do_bruto_e_recusado(self):
        bons, recusas = separar(self.brutos)
        self.assertEqual(recusas, [])
        self.assertEqual(len(bons), 1938)

    def test_a_referencia_bate_com_os_sete_que_ja_tinhamos(self):
        """
        A prova de que é a régua da Ponte Adolfo Konder, e não outra referência:
        os sete registros que já estavam — mesma relação, outro caminho —
        aparecem aqui com o MESMO valor.
        """
        arquivo = Path(__file__).resolve().parent.parent / "data" / "cotas-ruas.json"
        atuais = [c for c in json.loads(arquivo.read_text(encoding="utf-8"))["cotas"]
                  if c["cidade"] == "blumenau" and c.get("data_fonte") == "2022-05"]
        self.assertTrue(atuais, "os sete originais precisam continuar no arquivo")
        pares = {(normalizar(b["rua"]), b["cota_m"]) for b in self.brutos}
        for a in atuais:
            with self.subTest(rua=a["rua"], cota=a["cota_m"]):
                self.assertIn((normalizar(a["rua"]), a["cota_m"]), pares)

    def test_nenhuma_cota_do_bruto_passa_do_teto_da_bacia(self):
        for b in self.brutos:
            self.assertLess(b["cota_m"], 25.0, b["rua"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
