#!/usr/bin/env python3
"""
Testes da conferência que decide a referência da série de Blumenau.

Este é o script que vai autorizar (ou proibir) somar 0,20 m em 113 registros
históricos. Se ele errar para o lado permissivo, o site passa a exibir a série
inteira deslocada — e um gráfico deslocado 20 cm é lido como se estivesse certo,
porque não há nada na tela que denuncie.

Por isso o que se testa aqui é sobretudo o que faz o veredito **não** concluir:
poucos pares, dispersão alta, e o caso em que os dois grupos discordam entre si.
"""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from conferir_blumenau_alertablu import (DESLOCAMENTO_IBGE_M, MINIMO_POR_GRUPO,
                                         ROTULO_IBGE, chave_de_data,
                                         eventos_do_alertablu, numero, parear,
                                         resumo, veredito)


def pares(n, diferenca, rotulado=True, ano=1900):
    return [{"data": f"{ano + i}-01-01", "ano": ano + i, "nosso_m": 10.0,
             "deles_m": 10.0 + diferenca, "diferenca": diferenca,
             "rotulado_ibge": rotulado} for i in range(n)]


class TestNumero(unittest.TestCase):
    def test_le_virgula_ponto_e_texto_com_unidade(self):
        for valor in ("12,60", "12.60", 12.6, "12,60 m", "12.60m"):
            with self.subTest(valor=valor):
                self.assertAlmostEqual(numero(valor), 12.60, places=2)

    def test_o_que_nao_e_numero_vira_none(self):
        for valor in (None, "", "sem cota", True):
            with self.subTest(valor=valor):
                self.assertIsNone(numero(valor))


class TestData(unittest.TestCase):
    def test_le_data_completa_mes_e_ano_solto(self):
        self.assertEqual(chave_de_data("2011-09-09"), ("2011", "09", "09"))
        self.assertEqual(chave_de_data("1984-08"), ("1984", "08", None))
        self.assertEqual(chave_de_data("1880"), ("1880", None, None))

    def test_texto_sem_ano_nao_vira_data(self):
        self.assertIsNone(chave_de_data("sem data"))


class TestLeituraDoArquivo(unittest.TestCase):
    """O formato exato do arquivo ainda não se conhece; a leitura é tolerante."""

    def test_aceita_lista_solta_e_objeto_com_invólucro(self):
        esperado = [{"data": "2011-09-09", "cota": "12,60"}]
        for dados in (esperado, {"enchentes": esperado}, {"eventos": esperado}):
            with self.subTest(dados=type(dados)):
                lido = eventos_do_alertablu(dados)
                self.assertEqual(len(lido), 1)
                self.assertAlmostEqual(lido[0]["cota_m"], 12.60)

    def test_aceita_nomes_alternativos_de_campo(self):
        lido = eventos_do_alertablu([{"ano": "1984", "nivel_m": 15.46}])
        self.assertEqual((lido[0]["ano"], lido[0]["cota_m"]), ("1984", 15.46))

    def test_item_sem_data_ou_sem_cota_e_descartado(self):
        self.assertEqual(eventos_do_alertablu([{"cota": 12.6}, {"data": "2011"}]), [])


class TestPareamento(unittest.TestCase):
    def nossos(self):
        return [
            {"data": "1983-07-09", "ano": "1983", "mes": "07", "dia": "09",
             "pico_m": 15.34, "referencia": ROTULO_IBGE},
            {"data": "1983-05-20", "ano": "1983", "mes": "05", "dia": "20",
             "pico_m": 12.52, "referencia": ROTULO_IBGE},
            {"data": "1880-09-23", "ano": "1880", "mes": "09", "dia": "23",
             "pico_m": 17.10, "referencia": ROTULO_IBGE},
        ]

    def test_casa_pelo_dia_quando_as_duas_fontes_trazem(self):
        p, _ = parear([{"data": "1983-07-09", "ano": "1983", "mes": "07", "dia": "09",
                        "cota_m": 15.34}], self.nossos())
        self.assertEqual(len(p), 1)
        self.assertEqual(p[0]["diferenca"], 0.0)

    def test_ano_solto_casa_quando_o_ano_tem_um_evento_so(self):
        p, _ = parear([{"data": "1880", "ano": "1880", "mes": None, "dia": None,
                        "cota_m": 17.10}], self.nossos())
        self.assertEqual(len(p), 1)

    def test_ano_solto_com_varios_eventos_nao_casa(self):
        """
        1928 tem cinco eventos e 1973 tem seis. Casar pelo ano ali é sortear
        qual — e um par sorteado envenena a mediana inteira.
        """
        p, ambiguos = parear([{"data": "1983", "ano": "1983", "mes": None, "dia": None,
                               "cota_m": 15.34}], self.nossos())
        self.assertEqual(p, [])
        self.assertEqual(len(ambiguos), 1)

    def test_evento_que_so_uma_fonte_tem_nao_vira_par(self):
        p, _ = parear([{"data": "1852-10-29", "ano": "1852", "mes": "10", "dia": "29",
                        "cota_m": 16.30}], self.nossos())
        self.assertEqual(p, [])

    def test_a_diferenca_e_deles_menos_o_nosso(self):
        p, _ = parear([{"data": "1880-09-23", "ano": "1880", "mes": "09", "dia": "23",
                        "cota_m": 16.90}], self.nossos())
        self.assertAlmostEqual(p[0]["diferenca"], -0.20, places=2)


class TestResumo(unittest.TestCase):
    def test_deslocamento_constante_e_reconhecido(self):
        r = resumo(pares(10, -0.20))
        self.assertAlmostEqual(r["mediana"], -0.20)
        self.assertTrue(r["constante"])

    def test_grupo_espalhado_nao_e_constante(self):
        espalhado = pares(10, 0.0)
        for i, p in enumerate(espalhado):
            p["diferenca"] = i * 0.1
        self.assertFalse(resumo(espalhado)["constante"])

    def test_grupo_vazio_nao_quebra(self):
        self.assertEqual(resumo([])["n"], 0)


class TestVeredito(unittest.TestCase):
    def test_poucos_pares_nao_concluem(self):
        self.assertEqual(veredito(pares(MINIMO_POR_GRUPO - 1, 0.0))[0], "indeciso")

    def test_dispersao_alta_nao_conclui(self):
        espalhado = pares(20, 0.0)
        for i, p in enumerate(espalhado):
            p["diferenca"] = (i % 5) * 0.13
        self.assertEqual(veredito(espalhado)[0], "irregular")

    def test_alertablu_em_ibge(self):
        chave, porque = veredito(pares(20, 0.0))
        self.assertEqual(chave, "alertablu_em_ibge")
        self.assertIn("subtrair", porque)

    def test_alertablu_em_regua(self):
        chave, porque = veredito(pares(20, -DESLOCAMENTO_IBGE_M))
        self.assertEqual(chave, "alertablu_em_regua")
        self.assertIn("RÉGUA", porque)

    def test_deslocamento_que_nao_e_nenhum_dos_dois_vira_terceira_referencia(self):
        self.assertEqual(veredito(pares(20, -0.45))[0], "terceira_referencia")

    def test_grupos_que_discordam_proibem_a_conversao(self):
        """
        O caso que uma mediana única esconderia, e o que os indícios apontam:
        1880/1983/1984 batem ao centavo com o rótulo IBGE, e set/2011 fica
        0,40 m fora. Nenhum número serve para os dois trechos.
        """
        mistura = pares(15, 0.0, rotulado=True) + pares(15, -0.40, rotulado=False, ano=2000)
        chave, porque = veredito(mistura)
        self.assertEqual(chave, "muda_com_a_epoca")
        self.assertIn("NÃO converter", porque)

    def test_so_os_dois_casos_conclusivos_saem_com_sucesso(self):
        """
        A saída do processo é 0 só quando dá para converter. Qualquer outra
        coisa é 2, para um cron ou um Makefile não tratar dúvida como resposta.
        """
        conclusivos = {"alertablu_em_ibge", "alertablu_em_regua"}
        for difs, esperado in ((0.0, True), (-DESLOCAMENTO_IBGE_M, True),
                               (-0.45, False)):
            with self.subTest(difs=difs):
                self.assertEqual(veredito(pares(20, difs))[0] in conclusivos, esperado)


if __name__ == "__main__":
    unittest.main(verbosity=2)
