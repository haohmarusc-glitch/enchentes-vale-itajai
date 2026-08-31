#!/usr/bin/env python3
"""
Testes da análise do KML de Brusque.

Estes testes existem para travar uma RECUSA. O KML traz 1.679 pontos com um
campo `cota`, e veio junto um conversor que os gravaria como `referencia:
"régua", confianca: "alta"`. A análise mostrou que isso não se sustenta. Se
alguém apontar o importador para este arquivo mais tarde, sem refazer a conta, o
site passa a responder "sua rua alaga a X metros" com um número que pode errar
por 19 m. É o tipo de erro que este projeto recusa por princípio.

Por isso se testa tanto a mecânica (as funções fazem a conta certa) quanto a
conclusão (sobre o arquivo real, ela continua sendo "não importar").
"""

import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from analisar_kml_brusque import (
    e_numero,
    ANO_DA_PASTA, CIDADE, PASTA_COM_COTA, acima_de, carregar_bruto,
    censo_por_pasta, com_cota, cota_por_distancia, cruzar_com_cadastro,
    importavel, normalizar, pico_da_cidade, probabilidade_por_acaso,
)
from comum import DADOS

#: `data_fonte` dos registros que vieram da camada conferida de 2023.
CAMADA_2023 = "2023-11"


class TestNormalizar(unittest.TestCase):
    def test_tira_acento_e_prefixo(self):
        self.assertEqual(normalizar("Rua México"), "MEXICO")
        self.assertEqual(normalizar("Av. Beira Rio"), "BEIRA RIO")
        self.assertEqual(normalizar("Rua  Coelho   Neto "), "COELHO NETO")

    def test_tira_so_o_primeiro_prefixo(self):
        self.assertEqual(normalizar("Rua Rua Nova"), "RUA NOVA")

    def test_aguenta_nada(self):
        self.assertEqual(normalizar(None), "")
        self.assertEqual(normalizar(""), "")


class TestComCota(unittest.TestCase):
    def test_booleano_nao_e_cota(self):
        self.assertEqual(com_cota([{"cota": True}, {"cota": False}]), [])

    def test_texto_nao_e_cota(self):
        self.assertEqual(com_cota([{"cota": "9,4"}, {"cota": None}, {}]), [])

    def test_numero_e_cota(self):
        self.assertEqual(len(com_cota([{"cota": 9.4}, {"cota": 7}])), 2)


class TestENumero(unittest.TestCase):
    def test_booleano_nao_e_numero(self):
        self.assertFalse(e_numero(True))
        self.assertFalse(e_numero(False))

    def test_numero_e_numero(self):
        self.assertTrue(e_numero(0))
        self.assertTrue(e_numero(9.4))

    def test_texto_e_nada_nao_sao(self):
        self.assertFalse(e_numero("9,4"))
        self.assertFalse(e_numero(None))


class TestCenso(unittest.TestCase):
    def test_separa_pasta_com_e_sem_numero(self):
        censo = censo_por_pasta([
            {"pasta": "A", "cota": 5.0}, {"pasta": "A", "cota": 9.0},
            {"pasta": "B", "cota": None}, {"pasta": "B"},
        ])
        self.assertEqual(censo["A"], {"total": 2, "com_cota": 2, "min": 5.0, "mediana": 7.0, "max": 9.0})
        self.assertEqual(censo["B"]["com_cota"], 0)
        self.assertIsNone(censo["B"]["max"], "pasta sem número não inventa faixa")


class TestPicoDaCidade(unittest.TestCase):
    EVENTOS = [
        {"cidade": "brusque", "data": "2011-09", "pico_m": 10.03},
        {"cidade": "brusque", "data": "1984-08", "pico_m": 10.5},
        {"cidade": "blumenau", "data": "2011-09", "pico_m": 12.8},
        {"cidade": "brusque", "data": "2020-12-15", "pico_m": None},
    ]

    def test_pico_do_ano(self):
        self.assertEqual(pico_da_cidade(self.EVENTOS, "brusque", "2011"), 10.03)

    def test_pico_da_serie(self):
        self.assertEqual(pico_da_cidade(self.EVENTOS, "brusque"), 10.5)

    def test_nao_mistura_cidade(self):
        self.assertEqual(pico_da_cidade(self.EVENTOS, "blumenau", "2011"), 12.8)

    def test_cidade_sem_pico_devolve_nada(self):
        self.assertIsNone(pico_da_cidade(self.EVENTOS, "gaspar"))


class TestAcimaDe(unittest.TestCase):
    def test_conta_so_quem_passa(self):
        pontos = [{"cota": 9.0}, {"cota": 10.03}, {"cota": 10.04}, {"cota": None}]
        self.assertEqual(acima_de(pontos, 10.03), (1, 3), "o próprio limite não está acima")


class TestCruzamento(unittest.TestCase):
    CADASTRO = [
        {"rua": "Rua México", "cota_m": 7.80},
        {"rua": "Rua Celia Zen", "cota_m": 6.72},
        {"rua": "Rua Sem Par", "cota_m": 5.00},
        {"rua": "Rua Sem Numero", "cota_m": None},
    ]
    KML = [
        {"rua": "México", "cota": 10.10}, {"rua": "Rua México", "cota": 7.80},
        {"rua": "Celia Zen", "cota": 8.34},
    ]

    def setUp(self):
        self.comuns = cruzar_com_cadastro(self.KML, self.CADASTRO)

    def test_so_as_ruas_em_comum(self):
        self.assertEqual([c["rua"] for c in self.comuns], ["Rua México", "Rua Celia Zen"])

    def test_marca_quem_bate_no_centavo(self):
        bate = {c["rua"]: c["bate"] for c in self.comuns}
        self.assertTrue(bate["Rua México"])
        self.assertFalse(bate["Rua Celia Zen"])

    def test_junta_os_valores_da_rua_ordenados(self):
        mexico = next(c for c in self.comuns if c["rua"] == "Rua México")
        self.assertEqual(mexico["kml_m"], [7.80, 10.10])
        self.assertTrue(mexico["bate_no_menor"])

    def test_registro_sem_cota_fica_de_fora(self):
        self.assertNotIn("Rua Sem Numero", [c["rua"] for c in self.comuns])


class TestProbabilidade(unittest.TestCase):
    def test_acerto_impossivel_tem_probabilidade_zero(self):
        comuns = [{"bate": True, "kml_m": [7.8]}, {"bate": True, "kml_m": [9.1]}]
        # Nenhuma das cotas do sorteio bate nesses valores.
        self.assertEqual(probabilidade_por_acaso(comuns, [1.0, 2.0, 3.0], rodadas=200), 0.0)

    def test_acerto_garantido_tem_probabilidade_um(self):
        comuns = [{"bate": True, "kml_m": [1.0, 2.0, 3.0]}, {"bate": True, "kml_m": [1.0, 2.0, 3.0]}]
        self.assertEqual(probabilidade_por_acaso(comuns, [1.0, 2.0, 3.0], rodadas=200), 1.0)

    def test_e_reproduzivel(self):
        comuns = [{"bate": True, "kml_m": [1.0]}, {"bate": False, "kml_m": [9.0]}]
        cotas = [1.0, 2.0, 3.0, 4.0]
        a = probabilidade_por_acaso(comuns, cotas, rodadas=500, semente=7)
        b = probabilidade_por_acaso(comuns, cotas, rodadas=500, semente=7)
        self.assertEqual(a, b, "a mesma semente tem de dar o mesmo número")


class TestVeredito(unittest.TestCase):
    def test_recusa_quando_muita_coisa_passa_do_pico(self):
        self.assertFalse(importavel(0.64, 13, 13))

    def test_recusa_quando_o_cadastro_nao_confirma(self):
        self.assertFalse(importavel(0.0, 4, 13))

    def test_so_aceita_com_as_duas_coisas(self):
        self.assertTrue(importavel(0.01, 13, 13))

    def test_recusa_sem_rua_em_comum(self):
        self.assertFalse(importavel(0.0, 0, 0), "sem cruzamento não há confirmação")


class TestArquivoReal(unittest.TestCase):
    """A conclusão, refeita sobre o arquivo que está no repositório."""

    @classmethod
    def setUpClass(cls):
        cls.pontos = carregar_bruto()
        cls.numerados = [p for p in cls.pontos if p.get("pasta") == PASTA_COM_COTA]
        cls.eventos = json.loads((DADOS / "enchentes.json").read_text(encoding="utf-8"))["eventos"]
        cls.cadastro = [
            r
            for r in json.loads((DADOS / "cotas-ruas.json").read_text(encoding="utf-8"))["cotas"]
            if r.get("cidade") == CIDADE
        ]
        # A análise desta pasta cruza a camada de 2011 com o que se sabia de
        # Brusque ANTES dela — a lista oficial de out/2023. Cruzar com a camada
        # de 2023, importada depois, seria comparar o KML com ele mesmo.
        cls.oficiais = [r for r in cls.cadastro if r.get("data_fonte") != CAMADA_2023]

    def test_so_uma_pasta_tem_numero(self):
        censo = censo_por_pasta(self.pontos)
        com_numero = [p for p, l in censo.items() if l["com_cota"]]
        self.assertEqual(com_numero, [PASTA_COM_COTA])

    def test_a_maioria_passa_do_pico_do_proprio_ano(self):
        pico = pico_da_cidade(self.eventos, CIDADE, ANO_DA_PASTA)
        acima, total = acima_de(self.numerados, pico)
        self.assertGreater(acima / total, 0.5,
                           "se isso deixar de valer, a análise mudou — refazer antes de importar")

    def test_o_maior_valor_e_absurdo_para_uma_regua(self):
        maior = max(p["cota"] for p in com_cota(self.numerados))
        serie = pico_da_cidade(self.eventos, CIDADE)
        self.assertGreater(maior - serie, 15.0,
                           "19 m acima do recorde não é nível de régua")

    def test_parte_do_arquivo_bate_com_o_cadastro(self):
        comuns = cruzar_com_cadastro(self.numerados, self.oficiais)
        acertos = sum(1 for c in comuns if c["bate"])
        self.assertGreater(acertos, 0, "há cotas de régua verdadeiras aqui dentro")
        self.assertLess(acertos, len(comuns), "mas não são todas — é mistura")

    def test_os_acertos_nao_sao_acaso(self):
        comuns = cruzar_com_cadastro(self.numerados, self.oficiais)
        nossas = [r["cota_m"] for r in self.oficiais if isinstance(r.get("cota_m"), (int, float))]
        self.assertLess(probabilidade_por_acaso(comuns, nossas, rodadas=5000), 0.01)

    def test_a_mediana_sobe_com_a_distancia(self):
        faixas = cota_por_distancia(self.numerados)
        self.assertGreater(faixas[-1][2], faixas[0][2],
                           "comportamento de altitude de terreno, não de cota de uma cheia só")

    def test_o_veredito_continua_sendo_nao_importar(self):
        pico = pico_da_cidade(self.eventos, CIDADE, ANO_DA_PASTA)
        acima, total = acima_de(self.numerados, pico)
        comuns = cruzar_com_cadastro(self.numerados, self.oficiais)
        acertos = sum(1 for c in comuns if c["bate"])
        self.assertFalse(importavel(acima / total, acertos, len(comuns)))

    def test_nenhum_registro_de_brusque_veio_desta_pasta(self):
        """
        A camada de 2023 do mesmo arquivo foi importada — ela fecha a conta
        `cota + lâmina = 8,96 m` e é cota de régua provada. Esta aqui, não.
        O guarda continua, apertado no que importa: nenhum registro pode citar
        a pasta de 2011, e todo registro que venha do KML tem de nomear a
        camada de 2023 e a conferência que a autorizou.
        """
        for registro in self.cadastro:
            fonte = str(registro.get("fonte") or "").lower()
            with self.subTest(rua=registro.get("rua")):
                self.assertNotIn(ANO_DA_PASTA, fonte,
                                 f"{registro.get('rua')}: {registro.get('fonte')}")
                self.assertNotIn(PASTA_COM_COTA.lower(), fonte,
                                 f"{registro.get('rua')}: {registro.get('fonte')}")
                if "my maps" in fonte:
                    self.assertIn("cotas de cheia 2023", fonte)
                    self.assertIn("8,96", fonte,
                                  "quem vem do KML precisa dizer contra que pico foi conferido")

    def test_a_lista_oficial_de_brusque_nao_passa_do_pico_historico(self):
        """
        Ao contrário de Blumenau e Rio do Sul, cuja lista oficial traz ruas altas que
        nunca alagaram, os 27 pontos de out/2023 vêm de uma lista que só desceu até
        8,01 m. Qualquer valor acima do recorde da cidade aqui seria contaminação.
        """
        serie = pico_da_cidade(self.eventos, CIDADE)
        for registro in self.oficiais:
            if e_numero(registro.get("cota_m")):
                self.assertLess(registro["cota_m"], serie, registro.get("rua"))

    def test_cota_acima_do_recorde_so_entra_dizendo_que_esta(self):
        """
        A camada de 2023 traz pontos altos legítimos — o mais alto, 11,01 m, é
        um poste que nenhuma cheia conhecida alcançou. Pode entrar, mas não
        calado: quem lê precisa saber que ali nunca chegou água.
        """
        serie = pico_da_cidade(self.eventos, CIDADE)
        for registro in self.cadastro:
            if e_numero(registro.get("cota_m")) and registro["cota_m"] > serie:
                with self.subTest(rua=registro.get("rua")):
                    self.assertIn("maior pico já registrado",
                                  str(registro.get("nota") or ""))

    def test_nada_em_brusque_alcanca_a_escala_da_pasta_de_2011(self):
        """
        A pasta de 2011 vai a 29,53 m. Se ela vazar para o cadastro algum dia,
        é por aqui que aparece — sem depender de como a fonte foi escrita.
        """
        teto_da_pasta = max(p["cota"] for p in com_cota(self.numerados))
        for registro in self.cadastro:
            if e_numero(registro.get("cota_m")):
                self.assertLess(registro["cota_m"], 12.0, registro.get("rua"))
        self.assertGreater(teto_da_pasta, 25.0, "a pasta de 2011 continua fora de escala")

    def test_brusque_tem_a_lista_oficial_mais_a_camada_conferida_e_nada_mais(self):
        """
        377 = 27 da lista oficial de out/2023 + 350 da camada conferida. A pasta
        de 2011 tem 1.679 pontos: se ela entrar, este número explode.
        """
        self.assertEqual(len(self.oficiais), 27)
        self.assertLess(len(self.cadastro), 500,
                        "a pasta de 2011 tem 1.679 pontos; centenas a mais "
                        "significam importação indevida")


if __name__ == "__main__":
    unittest.main(verbosity=2)
