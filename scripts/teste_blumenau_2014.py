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
                                    normalizar_rua, parear, ponto_canonico,
                                    sem_par_no_cadastro)
from extrair_blumenau_2014 import analisar, bairros_do_texto, separar_rua_e_bairro
from importar_blumenau_2014 import (LOGRADOURO, como_registro, enriquecer,
                                    nome_da_rua, reparar_importacao_anterior)

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

        A fixture mudou em 06/09/2026: "final da rua" e "Final da rua (pega só
        uma casa)" passaram a parear por REDAÇÃO, que é ponto, não cota — e aí
        a confiança sobe de direito (teste abaixo). O caso circular de verdade
        é um ponto que não tem nada a ver com o do PDF e só coincide no número.
        """
        cadastro = [{"rua": "Rua São Rafael", "ponto": "esquina com Rua São Roque",
                     "cota_m": 7.40, "confianca": "media", "fonte": "imprensa"}]
        confirmados, com_abrigo = enriquecer(cadastro, self.PDF)
        self.assertEqual((confirmados, com_abrigo), (0, 1))
        self.assertEqual(cadastro[0]["confianca"], "media")
        self.assertEqual(cadastro[0]["abrigo"], "IELBLU")

    def test_a_confianca_sobe_por_redacao_equivalente(self):
        """O ponto casou pela redação; a cota foi comparada depois e bateu."""
        cadastro = [{"rua": "Rua São Rafael", "ponto": "final da rua",
                     "cota_m": 7.40, "confianca": "media", "fonte": "imprensa"}]
        confirmados, _ = enriquecer(cadastro, self.PDF)
        self.assertEqual(confirmados, 1)
        self.assertEqual(cadastro[0]["confianca"], "alta")

    def test_redacao_equivalente_com_cota_diferente_nao_sobe(self):
        cadastro = [{"rua": "Rua São Rafael", "ponto": "final da rua",
                     "cota_m": 7.60, "confianca": "media", "fonte": "imprensa"}]
        confirmados, _ = enriquecer(cadastro, self.PDF)
        self.assertEqual(confirmados, 0)
        self.assertEqual(cadastro[0]["confianca"], "media")

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


class TestPrefixoRepetido(unittest.TestCase):
    """
    O bug de 01/09/2026: `normalizar_rua` tirava UM prefixo, o PDF escreve
    "AL Alameda Rio Branco", e 21 ruas da imprensa "não existiam" no documento
    oficial. Daí o importador as trouxe de novo, com o nome dobrado — 19
    duplicatas, "Alameda Alameda Adolfo Schmalz" na tela.
    """

    def test_abreviacao_e_palavra_juntas_dao_o_mesmo_nome(self):
        self.assertEqual(normalizar_rua("AL Alameda Rio Branco"), "rio branco")
        self.assertEqual(normalizar_rua("R Alameda Rio Branco"), "rio branco")
        self.assertEqual(normalizar_rua("Alameda Rio Branco"), "rio branco")

    def test_palavra_dobrada_no_inicio_cai(self):
        self.assertEqual(normalizar_rua("Alameda Alameda Adolfo Schmalz"),
                         normalizar_rua("Alameda Adolfo Schmalz"))
        self.assertEqual(normalizar_rua("Praca Praca Victor Konder"),
                         normalizar_rua("R Praça Victor Konder"))
        self.assertEqual(normalizar_rua("Via Expressa Via Expressa Paul Fritz Kuehnrich"),
                         normalizar_rua("R Via Expressa Paul Fritz Kuehnrich"))

    def test_praca_e_rua_do_mesmo_nome_continuam_diferentes(self):
        # "Praça Victor Konder" e "Rua Victor Konder" existem as duas no PDF.
        self.assertNotEqual(normalizar_rua("R Praça Victor Konder"),
                            normalizar_rua("R Victor Konder"))

    def test_o_importador_nao_dobra_mais_a_palavra(self):
        self.assertEqual(nome_da_rua("AL Alameda Rio Branco"), "Alameda Rio Branco")
        self.assertEqual(nome_da_rua("R Praça Victor Konder"), "Praça Victor Konder")
        self.assertEqual(nome_da_rua("R Via Expressa Paul Fritz Kuehnrich"),
                         "Via Expressa Paul Fritz Kuehnrich")
        self.assertEqual(nome_da_rua("R São Rafael"), "Rua São Rafael", "o caso comum não muda")


class TestRedacaoEquivalente(unittest.TestCase):
    """
    A segunda camada do pareamento. Cada equivalência aqui foi vista lado a
    lado no cruzamento de 06/09/2026, e a cota independente bateu em todas.
    """

    def test_as_redacoes_vistas_no_cruzamento(self):
        pares = [
            ("final da rua", "Final da rua (pega só uma casa)"),
            ("ponto mais baixo", "Ponto mais baixo da rua"),
            ("esquina com Rua 1º de Janeiro", "Esquina - Rua 1º de Janeiro"),
            ("próximo ao nº 169", "Casa nº 169"),
            ("início / ponto mais baixo", "Início da rua - ponto mais baixo da rua"),
        ]
        for nosso, deles in pares:
            with self.subTest(nosso=nosso):
                self.assertEqual(ponto_canonico(nosso), ponto_canonico(deles))

    def test_pontos_diferentes_continuam_diferentes(self):
        self.assertNotEqual(ponto_canonico("Casa nº 169"), ponto_canonico("Casa nº 16"))
        self.assertNotEqual(ponto_canonico("Esquina - Rua São Roque"),
                            ponto_canonico("Esquina - Rua 1º de Janeiro"))

    def pdf(self, *pontos):
        return [{"rua": "R Marconi", "observacao": obs, "cota_rotulo": cota}
                for obs, cota in pontos]

    def test_texto_cortado_pareia_quando_e_o_unico_comeco(self):
        # A imprensa cortou: "...a rua foi" em vez de "...a rua foi atingida até essa casa".
        pdf = self.pdf(("Casa nº 144 - na enchente de Set/2011, a rua foi atingida até essa casa", "12,30"),
                       ("Casa nº 35", "10,30"))
        pares = parear(pdf, [{"rua": "Rua Marconi", "cota_m": 12.30,
                              "ponto": "Casa nº 144 - na enchente de Set/2011, a rua foi"}])
        self.assertEqual(len(pares), 1)
        self.assertEqual(pares[0]["nivel"], "canonico")
        self.assertTrue(pares[0]["bate"])

    def test_comeco_so_vale_em_fronteira_de_palavra(self):
        # "Casa nº 1" não é o começo de "Casa nº 144".
        pdf = self.pdf(("Casa nº 144", "12,30"))
        self.assertEqual(parear(pdf, [{"rua": "Rua Marconi", "cota_m": 12.30, "ponto": "Casa nº 1"}]), [])

    def test_ambiguo_nao_pareia(self):
        # Dois pontos do PDF começam do mesmo jeito: não dá para saber qual é.
        pdf = self.pdf(("Entrada do condomínio - direita", "15,30"),
                       ("Entrada do condomínio - esquerda", "16,95"))
        self.assertEqual(parear(pdf, [{"rua": "Rua Marconi", "cota_m": 15.30,
                                       "ponto": "Entrada do condomínio"}]), [])

    def test_a_segunda_camada_tambem_denuncia_divergencia(self):
        """A cota não escolhe o candidato; ela é comparada depois — e pode falhar."""
        pdf = self.pdf(("Ponto mais baixo da rua", "7,60"))
        pares = parear(pdf, [{"rua": "Rua Marconi", "cota_m": 9.99, "ponto": "ponto mais baixo"}])
        self.assertEqual(len(pares), 1)
        self.assertFalse(pares[0]["bate"])

    def test_ponto_ja_tomado_pela_primeira_camada_nao_pareia_de_novo(self):
        pdf = self.pdf(("Ponto mais baixo da rua", "7,60"))
        cadastro = [{"rua": "Rua Marconi", "cota_m": 7.60, "ponto": "Ponto mais baixo da rua"},
                    {"rua": "Rua Marconi", "cota_m": 7.60, "ponto": "ponto mais baixo"}]
        pares = parear(pdf, cadastro)
        self.assertEqual([p["nivel"] for p in pares], ["exato"])

    def test_ponto_com_redacao_equivalente_nao_e_reimportado(self):
        pdf = self.pdf(("Final da rua (pega só uma casa)", "7,40"))
        self.assertEqual(sem_par_no_cadastro(pdf, [{"rua": "Rua Marconi", "cota_m": 9.99,
                                                    "ponto": "final da rua"}]), [])


class TestReparo(unittest.TestCase):
    def test_duplicata_do_pdf_sai_e_o_registro_antigo_fica(self):
        cotas = [
            {"cidade": "blumenau", "rua": "Alameda Rio Branco", "ponto": "Esquina - Rua Amapá",
             "cota_m": 13.70, "data_fonte": "2023-05", "confianca": "media"},
            {"cidade": "blumenau", "rua": "Alameda Alameda Rio Branco", "ponto": "Esquina - Rua Amapá",
             "cota_m": 13.70, "data_fonte": DATA_FONTE, "confianca": "alta"},
        ]
        mantidos, removidos, _ = reparar_importacao_anterior(cotas)
        self.assertEqual(len(mantidos), 1)
        self.assertEqual(mantidos[0]["data_fonte"], "2023-05")
        self.assertEqual(len(removidos), 1)

    def test_ponto_do_pdf_sem_gemeo_nao_sai(self):
        cotas = [{"cidade": "blumenau", "rua": "Alameda Rio Branco", "ponto": "Esquina - Rua Amapá",
                  "cota_m": 13.70, "data_fonte": DATA_FONTE, "confianca": "alta"}]
        mantidos, removidos, _ = reparar_importacao_anterior(cotas)
        self.assertEqual((len(mantidos), removidos), (1, []))

    def test_cota_diferente_nao_e_duplicata(self):
        cotas = [
            {"cidade": "blumenau", "rua": "Alameda Rio Branco", "ponto": "Esquina - Rua Amapá",
             "cota_m": 13.70, "data_fonte": "2023-05"},
            {"cidade": "blumenau", "rua": "Alameda Alameda Rio Branco", "ponto": "Esquina - Rua Amapá",
             "cota_m": 13.75, "data_fonte": DATA_FONTE},
        ]
        self.assertEqual(reparar_importacao_anterior(cotas)[1], [])

    def test_nome_dobrado_perde_a_repeticao_e_nada_mais(self):
        cotas = [{"cidade": "blumenau", "rua": "Praca Praca Victor Konder", "cota_m": 13.1},
                 {"cidade": "blumenau", "rua": "Via Expressa Via Expressa Paul", "cota_m": 18.1},
                 {"cidade": "blumenau", "rua": "Rua Amazonas", "cota_m": 7.2},
                 {"cidade": "gaspar", "rua": "Rua Rua Nova", "cota_m": 6.0}]
        mantidos, _, renomeados = reparar_importacao_anterior(cotas)
        self.assertEqual([c["rua"] for c in mantidos],
                         ["Praca Victor Konder", "Via Expressa Paul", "Rua Amazonas", "Rua Rua Nova"])
        self.assertEqual(len(renomeados), 2, "só Blumenau, que é o que este script importa")



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
        """
        Com a chave de rua CORRIGIDA. A versão anterior deste teste passava com
        19 duplicatas no arquivo, porque "alameda alameda rio branco" e "rio
        branco" eram chaves diferentes — o teste repetia o bug que devia pegar.
        """
        vistos = set()
        for c in self.blumenau:
            chave = (normalizar_rua(c["rua"]), normalizar_ponto(c.get("ponto")), c["cota_m"])
            self.assertNotIn(chave, vistos, f"{c['rua']} ({c.get('ponto')})")
            vistos.add(chave)

    def test_nenhum_nome_de_rua_com_palavra_dobrada(self):
        for c in self.blumenau:
            partes = c["rua"].lower().split()
            self.assertFalse(len(partes) >= 2 and partes[0] == partes[1], c["rua"])
            self.assertFalse(len(partes) >= 4 and partes[0:2] == partes[2:4], c["rua"])

    def test_quase_todo_registro_da_imprensa_esta_confirmado_pelo_pdf(self):
        """
        Ficam em `media` só os que o PDF de fato não descreve: Gustav Michel
        (não está no documento), Inominada 1546, um ponto da Humberto de Campos
        e a Lions Clube/Lions Club, cujo par por nome o projeto recusa de
        propósito. Cinco. Eram 47.
        """
        antigos = [c for c in self.blumenau if c.get("data_fonte") != DATA_FONTE]
        em_media = [c for c in antigos if c.get("confianca") != "alta"]
        self.assertLessEqual(len(em_media), 5, [c["rua"] for c in em_media])


if __name__ == "__main__":
    unittest.main(verbosity=2)
