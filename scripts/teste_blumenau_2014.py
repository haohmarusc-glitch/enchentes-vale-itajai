#!/usr/bin/env python3
"""
Testes do PDF de 2014 de Blumenau: extração, conferência e aplicação.

Esta é a operação mais delicada do cadastro até aqui, porque **mexe em registro
que já estava publicado**: sobe 1.891 cotas de `media` para `alta` e escreve
abrigo em 2.018. Subir confiança é dizer para quem lê "pode confiar mais neste
número"; se a conferência que autoriza isso estiver frouxa, o carimbo vale nada
e ninguém percebe.

Por isso o que se testa aqui é, antes de tudo, o portão: que ele feche com uma
divergência, que ele feche com poucos pares, e que a confiança NÃO suba por um
casamento circular.
"""

import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from conferir_blumenau_2014 import (DATA_FONTE, MINIMO_DE_PARES, carregar_pdf,
                                    confirmado, deslocamento, normalizar_ponto,
                                    normalizar_rua, parear, sem_par_no_cadastro)
from extrair_blumenau_2014 import analisar, bairros_do_texto, separar_rua_e_bairro
from importar_blumenau_2014 import (LOGRADOURO, como_registro, enriquecer,
                                    nome_da_rua)

RAIZ = Path(__file__).resolve().parent.parent

TRECHO = """R São Rafael ITOUPAVA NORTE
E9 Igreja Evangélica Livre de Blumenau - IELBLU-
. 7,40Cota:Bairro:
Abrigo:
Final da rua (pega só uma casa)Observação:
R Martha Cordeiro ITOUPAVA NORTE
E9 Igreja Evangélica Livre de Blumenau - IELBLU-
. 7,60Cota:Bairro:
Abrigo:
Ponto mais baixo da ruaObservação:
R Albert Goll ITOUPAVA NORTE
E9 Igreja Evangélica Livre de Blumenau - IELBLU-
. 7,65Cota:Bairro:
Abrigo:
Esquina - Rua 1º de JaneiroObservação:
"""


class TestExtrair(unittest.TestCase):
    def test_le_os_cinco_campos_de_cada_registro(self):
        registros, recusas = analisar(TRECHO)
        self.assertEqual(recusas, [])
        self.assertEqual(registros[0], {
            "rua": "R São Rafael",
            "bairro": "ITOUPAVA NORTE",
            "cota_rotulo": "7,40",
            "abrigo_codigo": "E9",
            "abrigo": "Igreja Evangélica Livre de Blumenau - IELBLU",
            "observacao": "Final da rua (pega só uma casa)",
        })

    def test_o_bairro_sai_do_proprio_documento_e_nao_de_lista_a_mao(self):
        """Lista escrita à mão envelhece calada quando a fonte muda."""
        self.assertEqual(bairros_do_texto(TRECHO.splitlines()), {"ITOUPAVA NORTE"})

    def test_nome_de_rua_que_acaba_em_caixa_alta_nao_vira_bairro(self):
        """
        "R Do CVV VELHA" é a rua "Do CVV" no bairro "VELHA". A regra gulosa
        engoliria o CVV junto, e o registro sairia com bairro inventado.
        """
        rua, bairro = separar_rua_e_bairro("R Do CVV VELHA", {"VELHA"})
        self.assertEqual((rua, bairro), ("R Do CVV", "VELHA"))

    def test_casa_o_maior_bairro_conhecido(self):
        """"ITOUPAVA NORTE" e "ITOUPAVA CENTRAL" começam igual."""
        rua, bairro = separar_rua_e_bairro(
            "R X ITOUPAVA CENTRAL", {"ITOUPAVA", "ITOUPAVA CENTRAL"})
        self.assertEqual((rua, bairro), ("R X", "ITOUPAVA CENTRAL"))

    def test_bairro_com_e_sem_acento_e_o_mesmo_bairro(self):
        """A fonte escreve "AGUA VERDE" 58 vezes e "ÁGUA VERDE" uma."""
        self.assertEqual(separar_rua_e_bairro("R X ÁGUA VERDE", {"AGUA VERDE"})[1],
                         "ÁGUA VERDE")


class TestConferir(unittest.TestCase):
    def pdf(self):
        return [{"rua": "R São Rafael", "observacao": "Final da rua",
                 "cota_rotulo": "7,40", "abrigo": "IELBLU", "abrigo_codigo": "E9"}]

    def test_pareia_pelo_ponto_e_nao_pela_cota(self):
        """
        Casar pela cota esconderia o que se quer ver: só acharia par onde os
        números já são iguais, e a conferência sempre daria certo.
        """
        cadastro = [{"rua": "Rua São Rafael", "ponto": "final da rua", "cota_m": 9.99}]
        pares = parear(self.pdf(), cadastro)
        self.assertEqual(len(pares), 1)
        self.assertFalse(pares[0]["bate"], "o par existe e a divergência aparece")

    def test_prefixo_de_logradouro_nao_impede_o_par(self):
        pares = parear(self.pdf(), [{"rua": "Rua São Rafael", "ponto": "Final da rua",
                                     "cota_m": 7.40}])
        self.assertEqual(len(pares), 1)
        self.assertTrue(pares[0]["bate"])

    def test_uma_divergencia_derruba_a_confirmacao(self):
        pares = [{"bate": True}] * (MINIMO_DE_PARES + 10) + [{"bate": False}]
        self.assertFalse(confirmado(pares))

    def test_poucos_pares_nao_confirmam_nada(self):
        self.assertFalse(confirmado([{"bate": True}] * (MINIMO_DE_PARES - 1)))

    def test_confirma_com_pares_suficientes_e_zero_divergencia(self):
        self.assertTrue(confirmado([{"bate": True}] * MINIMO_DE_PARES))

    def test_deslocamento_acha_o_caso_regua_ibge(self):
        """
        Se as duas listas estivessem em referências diferentes, o número
        apareceria como deslocamento constante de 0,20 m. É a regra bloqueante
        do CLAUDE.md, e esta função é quem a vigia.
        """
        pares = [{"nosso_m": 7.40, "pdf_m": 7.60}, {"nosso_m": 9.00, "pdf_m": 9.20},
                 {"nosso_m": 11.0, "pdf_m": 11.2}]
        self.assertAlmostEqual(deslocamento(pares), 0.20, places=2)
        self.assertIsNone(deslocamento([]))

    def test_ponto_que_o_cadastro_ja_tem_com_outra_redacao_nao_entra_de_novo(self):
        """
        "final da rua" e "Final da rua (pega só uma casa)" são o mesmo lugar. A
        segunda tentativa, pela cota, é o que impede o ponto de entrar duplicado.
        """
        cadastro = [{"rua": "Rua São Rafael", "ponto": "final da rua", "cota_m": 7.40}]
        self.assertEqual(sem_par_no_cadastro(self.pdf(), cadastro), [])


class TestNomeDaRua(unittest.TestCase):
    def test_expande_a_abreviacao_do_logradouro(self):
        self.assertEqual(nome_da_rua("R 1º de Janeiro"), "Rua 1º de Janeiro")
        self.assertEqual(nome_da_rua("AL Rio Branco"), "Alameda Rio Branco")

    def test_nao_mexe_no_resto_do_nome(self):
        self.assertEqual(nome_da_rua("R Dr. Hans Gaertner"), "Rua Dr. Hans Gaertner")

    def test_nome_sem_abreviacao_conhecida_passa_inteiro(self):
        self.assertEqual(nome_da_rua("Gustav Michel"), "Gustav Michel")

    def test_toda_abreviacao_do_dicionario_vira_palavra_inteira(self):
        for curta, longa in LOGRADOURO.items():
            self.assertEqual(nome_da_rua(f"{curta.upper()} Teste"), f"{longa} Teste")


class TestComoRegistro(unittest.TestCase):
    def bruto(self, **kw):
        base = {"rua": "R Bruno Dietrich", "bairro": "RIBEIRAO FRESCO",
                "cota_rotulo": "9,15", "abrigo": "Paróquia Luterana Centro",
                "abrigo_codigo": "S3", "observacao": "Final da rua"}
        base.update(kw)
        return base

    def test_registro_bom_sai_como_regua_e_confianca_alta(self):
        r = como_registro(self.bruto())
        self.assertEqual(r["cota_m"], 9.15)
        self.assertEqual(r["referencia"], "régua")
        self.assertEqual(r["confianca"], "alta")
        self.assertEqual(r["rua"], "Rua Bruno Dietrich")
        self.assertEqual(r["bairro"], "Ribeirao Fresco", "caixa alta na tela é grito")
        self.assertEqual(r["abrigo"], "Paróquia Luterana Centro")

    def test_rua_que_a_propria_fonte_nao_identificou_nao_entra(self):
        """
        "Não Localizado" é a ausência de um nome, não um nome. Entraria como
        "Rua Não Localizado", que ninguém procura e ninguém acha.
        """
        self.assertIsNone(como_registro(self.bruto(rua="R Não Localizado Não Localizado")))

    def test_cota_fora_da_faixa_de_rio_nao_entra(self):
        for cota in ("0", "-1", "30,00", "abc"):
            with self.subTest(cota=cota):
                self.assertIsNone(como_registro(self.bruto(cota_rotulo=cota)))


class TestEnriquecer(unittest.TestCase):
    PDF = [
        {"rua": "R São Rafael", "observacao": "Final da rua (pega só uma casa)",
         "cota_rotulo": "7,40", "abrigo": "IELBLU", "abrigo_codigo": "E9"},
        {"rua": "R Marechal Deodoro", "observacao": "Esquina - Rua Colombo",
         "cota_rotulo": "12,95", "abrigo": "Paróquia Luterana da Velha",
         "abrigo_codigo": "W1"},
        {"rua": "R Marechal Deodoro", "observacao": "Casa nº 560",
         "cota_rotulo": "12,35", "abrigo": "EEB Victor Hering", "abrigo_codigo": "C6"},
    ]

    def test_a_confianca_sobe_onde_a_conferencia_comparou_os_numeros(self):
        cadastro = [{"rua": "Rua São Rafael", "ponto": "Final da rua (pega só uma casa)",
                     "cota_m": 7.40, "confianca": "media", "fonte": "imprensa"}]
        confirmados, _ = enriquecer(cadastro, self.PDF)
        self.assertEqual(confirmados, 1)
        self.assertEqual(cadastro[0]["confianca"], "alta")
        self.assertIn("PDF oficial", cadastro[0]["fonte"])

    def test_a_confianca_nao_sobe_por_casamento_circular(self):
        """
        Um registro que só casa pela COTA ganha o abrigo, mas não o carimbo de
        confiança: casar pela cota provaria só que a cota é igual à cota.
        """
        cadastro = [{"rua": "Rua São Rafael", "ponto": "final da rua",
                     "cota_m": 7.40, "confianca": "media", "fonte": "imprensa"}]
        confirmados, com_abrigo = enriquecer(cadastro, self.PDF)
        self.assertEqual((confirmados, com_abrigo), (0, 1))
        self.assertEqual(cadastro[0]["confianca"], "media")
        self.assertEqual(cadastro[0]["abrigo"], "IELBLU")

    def test_rua_comprida_recebe_o_abrigo_do_ponto_dela(self):
        """A Marechal Deodoro tem dois abrigos, em pontos diferentes."""
        cadastro = [
            {"rua": "Rua Marechal Deodoro", "ponto": "outra redação", "cota_m": 12.95,
             "confianca": "media", "fonte": "imprensa"},
            {"rua": "Rua Marechal Deodoro", "ponto": "outra ainda", "cota_m": 12.35,
             "confianca": "media", "fonte": "imprensa"},
        ]
        enriquecer(cadastro, self.PDF)
        self.assertEqual(cadastro[0]["abrigo"], "Paróquia Luterana da Velha")
        self.assertEqual(cadastro[1]["abrigo"], "EEB Victor Hering")

    def test_rodar_duas_vezes_nao_repete_a_frase_na_fonte(self):
        cadastro = [{"rua": "Rua São Rafael", "ponto": "Final da rua (pega só uma casa)",
                     "cota_m": 7.40, "confianca": "media", "fonte": "imprensa"}]
        enriquecer(cadastro, self.PDF)
        primeira = cadastro[0]["fonte"]
        self.assertEqual(enriquecer(cadastro, self.PDF)[0], 0)
        self.assertEqual(cadastro[0]["fonte"], primeira)

    def test_nenhuma_cota_muda(self):
        """A operação confirma número, não corrige. É isso que a torna segura."""
        cadastro = [{"rua": "Rua São Rafael", "ponto": "Final da rua (pega só uma casa)",
                     "cota_m": 7.40, "confianca": "media", "fonte": "imprensa"}]
        enriquecer(cadastro, self.PDF)
        self.assertEqual(cadastro[0]["cota_m"], 7.40)


class TestArquivoReal(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pdf = carregar_pdf()
        cotas = json.loads(
            (RAIZ / "data" / "cotas-ruas.json").read_text(encoding="utf-8"))["cotas"]
        cls.blumenau = [c for c in cotas if c["cidade"] == "blumenau"]

    def test_o_pdf_tem_os_2034_registros(self):
        self.assertEqual(len(self.pdf), 2034)
        self.assertTrue(all(r.get("abrigo") for r in self.pdf))

    def test_a_conferencia_continua_fechando(self):
        antigos = [c for c in self.blumenau if c.get("data_fonte") != DATA_FONTE]
        pares = parear(self.pdf, antigos)
        self.assertTrue(confirmado(pares),
                        f"{sum(1 for p in pares if not p['bate'])} divergências de "
                        f"{len(pares)} — a relação deixou de bater com o documento")

    def test_as_duas_listas_estao_na_mesma_referencia(self):
        antigos = [c for c in self.blumenau if c.get("data_fonte") != DATA_FONTE]
        self.assertAlmostEqual(deslocamento(parear(self.pdf, antigos)), 0.0, places=2)

    def test_quase_todo_registro_de_blumenau_tem_abrigo(self):
        com = sum(1 for c in self.blumenau if c.get("abrigo"))
        self.assertGreater(com / len(self.blumenau), 0.98)

    def test_nenhuma_rua_nao_localizada_entrou(self):
        for c in self.blumenau:
            self.assertNotIn("localizado", c["rua"].lower())

    def test_nenhum_registro_de_blumenau_perdeu_a_cota(self):
        for c in self.blumenau:
            with self.subTest(rua=c["rua"]):
                self.assertTrue(c["cota_m"] is None or 0 < c["cota_m"] < 25.0)

    def test_a_importacao_nao_criou_ponto_duplicado(self):
        vistos = set()
        for c in self.blumenau:
            chave = (normalizar_rua(c["rua"]), normalizar_ponto(c.get("ponto")), c["cota_m"])
            self.assertNotIn(chave, vistos, f"{c['rua']} ({c.get('ponto')})")
            vistos.add(chave)


if __name__ == "__main__":
    unittest.main(verbosity=2)
