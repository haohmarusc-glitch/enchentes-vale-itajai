#!/usr/bin/env python3
"""
Testes da conferência de Gaspar contra o Plano de Contingência.

O que estes testes travam é a coisa que Gaspar não tinha até agora: uma cota de
régua que dispare aviso. Ela veio de UM documento, e é fácil alguém "arredondar"
ou "reconciliar" 5/6/7 mais tarde sem voltar ao PDF. Então a transcrição das
faixas está pinada aqui, e o que ela precisa sustentar — margem antes da primeira
rua, escala igual à da leitura em tempo real, chave 'emergencia' e não
'inundacao' — está pinado junto. Se alguém mexer, quebra alto.
"""

import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from conferir_gaspar_plano import (FAIXAS_DO_PLANO, NIVEL_EM_31_08_2026_M,
                                   RUAS_DO_PLANO, confere_escala, confere_faixas,
                                   confere_margem, confere_ruas, cotas_de_gaspar,
                                   normalizar, ruas_de_gaspar)

RAIZ = Path(__file__).resolve().parent.parent


class TestFaixasDoPlano(unittest.TestCase):
    """A transcrição do fluxograma da p. 25, pinada contra o PDF."""

    def test_sao_as_quatro_faixas_do_fluxograma(self):
        self.assertEqual([f["nome"] for f in FAIXAS_DO_PLANO],
                         ["NORMALIDADE", "ATENÇÃO/ALERTA", "ALERTA/ALARME", "RESPOSTA"])
        self.assertEqual([f["de"] for f in FAIXAS_DO_PLANO], [0.0, 5.0, 6.0, 7.0])

    def test_a_faixa_de_resposta_nao_tem_teto(self):
        """
        O PDF pinta uma caixa opaca sobre a imagem e escreve "Acima de 7 metros".
        A imagem por baixo diz "7 a 8 metros" — e é ela que sai de qualquer
        extração de imagem. Ler o teto errado inventaria um limite que o
        documento vigente removeu.
        """
        self.assertIsNone(FAIXAS_DO_PLANO[-1]["ate"])

    def test_as_faixas_sao_contiguas_e_crescentes(self):
        for anterior, seguinte in zip(FAIXAS_DO_PLANO, FAIXAS_DO_PLANO[1:]):
            self.assertEqual(anterior["ate"], seguinte["de"])
            self.assertLess(anterior["de"], seguinte["de"])

    def test_normalidade_nao_vira_cota(self):
        """Cadastrar o leito como cota faria o aviso tocar em dia de sol."""
        self.assertIsNone(FAIXAS_DO_PLANO[0]["chave"])

    def test_a_faixa_de_7_m_e_emergencia_e_nao_inundacao(self):
        """
        7,00 m é a fase de RESPOSTA do Plano, não o nível em que Gaspar alaga —
        a primeira rua alaga a 6,20 m. Chamar de 'inundacao' diria ao morador
        que a água chega 80 cm depois do que chega.
        """
        self.assertEqual(FAIXAS_DO_PLANO[-1]["chave"], "emergencia")
        self.assertNotIn("inundacao", [f["chave"] for f in FAIXAS_DO_PLANO])


class TestCadastro(unittest.TestCase):
    """As cotas gravadas em estacoes.json são as do Plano."""

    def test_as_cotas_de_gaspar_batem_com_o_plano(self):
        self.assertEqual(confere_faixas(), [])

    def test_gaspar_tem_as_tres_cotas(self):
        self.assertEqual(cotas_de_gaspar(),
                         {"atencao": 5.0, "alerta": 6.0, "emergencia": 7.0})

    def test_a_fonte_das_cotas_esta_registrada(self):
        estacoes = json.loads((RAIZ / "data/estacoes.json").read_text())
        g = next(c for c in estacoes["rios"]["itajai-acu"]["cidades"] if c["id"] == "gaspar")
        self.assertIn("Plano de Contingência", g["fonte_cotas"])
        self.assertEqual(g["referencia"], "régua")

    def test_o_pdf_de_origem_esta_no_repositorio(self):
        """Cota de vida não pode depender de arquivo que só existe fora daqui."""
        self.assertTrue((RAIZ / "data/brutos/gaspar-plano-de-contingencia.pdf").exists())


class TestMargem(unittest.TestCase):
    """O aviso sai antes de a água entrar — é isso que faz a cota valer."""

    def test_a_atencao_fica_abaixo_da_primeira_rua(self):
        primeira, problemas = confere_margem()
        self.assertEqual(problemas, [])
        self.assertIsNotNone(primeira)
        self.assertLess(cotas_de_gaspar()["atencao"], primeira)

    def test_a_margem_e_de_pelo_menos_um_metro(self):
        """
        Não é exigência do Plano, é a medida do que Gaspar ganhou: 1,20 m entre
        a atenção e a primeira rua. Se uma importação futura trouxer rua mais
        baixa que 6,00 m, este teste cai e a margem tem de ser reavaliada — não
        descoberta durante uma cheia.
        """
        primeira, _ = confere_margem()
        self.assertGreaterEqual(primeira - cotas_de_gaspar()["atencao"], 1.0)


class TestEscala(unittest.TestCase):
    """Faixas, cotas de rua e leitura em tempo real são a mesma régua."""

    def test_a_leitura_real_cai_na_normalidade(self):
        self.assertEqual(confere_escala(), [])

    def test_a_leitura_pinada_e_a_da_tabela_do_municipio(self):
        self.assertEqual(NIVEL_EM_31_08_2026_M, 3.85)

    def test_leitura_fora_da_escala_seria_denunciada(self):
        """A prova de escala só serve se ela puder falhar."""
        import conferir_gaspar_plano as m
        antes = m.NIVEL_EM_31_08_2026_M
        try:
            m.NIVEL_EM_31_08_2026_M = 9.9
            self.assertTrue(m.confere_escala())
        finally:
            m.NIVEL_EM_31_08_2026_M = antes


class TestQuadroDeRuas(unittest.TestCase):
    """As 26 vias da p. 23-24 contra o cadastro vindo do KML."""

    def test_sao_26_vias(self):
        self.assertEqual(len(RUAS_DO_PLANO), 26)

    def test_nenhuma_via_do_plano_esta_ausente_do_cadastro(self):
        """
        A Rua Santa Isabel estava — e quem morasse nela buscava o próprio
        endereço e não achava nada. Este teste impede que volte a acontecer.
        """
        linhas, _ = confere_ruas()
        ausentes = [l["rua"] for l in linhas if l["estado"] == "ausente"]
        self.assertEqual(ausentes, [])

    def test_a_grande_maioria_bate_ao_centavo(self):
        """
        24 de 26. É a terceira conferência independente da mesma Defesa Civil, e
        é o que sustenta tratar as faixas e as cotas de rua como a mesma régua.
        """
        linhas, _ = confere_ruas()
        batem = sum(1 for l in linhas if l["estado"] == "bate")
        self.assertGreaterEqual(batem, 24)

    def test_as_duas_divergencias_conhecidas_estao_anotadas(self):
        """
        Imaruí (7,02 × 7,00) e Maria da Silva (6,99 × 7,00). Divergência sem
        nota vira número órfão: daqui a um ano ninguém sabe se foi conferido.
        """
        linhas, _ = confere_ruas()
        divergem = {l["rua"] for l in linhas if l["estado"] == "difere"}
        self.assertEqual(divergem, {"Rua Imaruí", "Rua Maria da Silva"})
        cotas = json.loads((RAIZ / "data/cotas-ruas.json").read_text())["cotas"]
        for nome in divergem:
            registros = [r for r in cotas if r["cidade"] == "gaspar" and r["rua"] == nome]
            self.assertTrue(registros, nome)
            self.assertTrue(any("Plano de Contingência" in (r.get("nota") or "")
                                for r in registros), nome)

    def test_as_duas_divergencias_sao_de_centimetros(self):
        """Se uma delas crescer, deixou de ser arredondamento e vira pergunta."""
        linhas, _ = confere_ruas()
        for l in linhas:
            if l["estado"] == "difere":
                self.assertLessEqual(abs(l["mais_proxima_m"] - l["plano_m"]), 0.05, l["rua"])


class TestNormalizar(unittest.TestCase):
    def test_ignora_prefixo_acento_e_caixa(self):
        self.assertEqual(normalizar("Rua Imaruí"), normalizar("IMARUI"))
        self.assertEqual(normalizar("Avenida Hilberto Gaertner"),
                         normalizar("Av. Hilberto Gaertner"))

    def test_nao_junta_ruas_diferentes(self):
        self.assertNotEqual(normalizar("Rua Lírio"), normalizar("Rua Lino"))

    def test_o_cadastro_de_gaspar_e_lido(self):
        ruas = ruas_de_gaspar()
        self.assertGreater(len(ruas), 100)
        self.assertTrue(all(v == sorted(v) for v in ruas.values()))


if __name__ == "__main__":
    unittest.main()
