#!/usr/bin/env python3
"""
Testes da medição do nível estadual de Gaspar.

O que se trava aqui é um portão fechado. Gaspar acabou de ganhar cota de régua
(5 / 6 / 7 m, do Plano de Contingência) e não tem leitura — a tentação de ligar
o primeiro número disponível nas faixas é grande, e a rede estadual publica um
número que PARECE servir. Na mesma rede, Ilhota vem 7,3 m acima da nossa régua.

Um deslocamento desses aplicado às faixas de Gaspar mostraria RESPOSTA com o rio
no leito ou, para o outro lado, normalidade com a água na rua. Por isso os
testes centrais aqui são sobre o que o script SE RECUSA a fazer.
"""

import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import gaspar_estadual as m
from gaspar_estadual import (CODIGO_GASPAR, EVIDENCIA_DE_ZEROS_DIFERENTES,
                             LIMITE_DE_COERENCIA_M, estacoes, medir_deslocamento,
                             nivel_da_estacao, usavel_para_aviso)


def resposta(*estacoes_) -> dict:
    return {"data": {"tags_data": {"qualle_meteorologia": list(estacoes_)}}}


def estacao(codigo, nivel=None, quando="2026-09-01T03:09:00Z") -> dict:
    rio = {"rio_nivel": ({"value": nivel} if nivel is not None else {})}
    return {"codigo": codigo, "timestamp": quando, "data": {"rio": rio}}


class TestPortao(unittest.TestCase):
    """O portão fecha por padrão e só abre com número medido."""

    def test_sem_deslocamento_medido_nao_serve_para_aviso(self):
        self.assertIsNone(m.DESLOCAMENTO_CONHECIDO_M,
                          "se alguém preencheu isto, o par medido precisa estar "
                          "em docs/fontes-tempo-real.md e este teste, revisto")
        ok, motivo = usavel_para_aviso()
        self.assertFalse(ok)
        self.assertIn("NÃO medido", motivo)

    def test_o_portao_abre_quando_o_deslocamento_for_medido(self):
        """Fechado para sempre seria só um script morto; ele tem de poder abrir."""
        antes = m.DESLOCAMENTO_CONHECIDO_M
        try:
            m.DESLOCAMENTO_CONHECIDO_M = 0.0
            ok, motivo = usavel_para_aviso()
            self.assertTrue(ok)
            self.assertIn("medido", motivo)
        finally:
            m.DESLOCAMENTO_CONHECIDO_M = antes


class TestSemLeituraNaoEhSilencio(unittest.TestCase):
    """
    O defeito da primeira tentativa em shell: `jq select` sai 0 sem achar nada,
    o fallback nunca rodava, e a saída era nenhuma linha mais "snapshot salvo".
    Aqui os dois casos de ausência têm de ser distinguíveis e explícitos.
    """

    def test_estacao_ausente_da_resposta(self):
        nivel, quando = nivel_da_estacao(resposta(estacao("DCSC-00030", 10.67)),
                                         CODIGO_GASPAR)
        self.assertIsNone(nivel)
        self.assertIsNone(quando)

    def test_estacao_presente_e_sem_valor(self):
        """O caso real de 01/09/2026 03:09Z: Gaspar respondeu, sem nível."""
        nivel, quando = nivel_da_estacao(resposta(estacao(CODIGO_GASPAR, None)),
                                         CODIGO_GASPAR)
        self.assertIsNone(nivel)
        self.assertEqual(quando, "2026-09-01T03:09:00Z")

    def test_estacao_presente_com_valor(self):
        nivel, _ = nivel_da_estacao(resposta(estacao(CODIGO_GASPAR, 4.12)),
                                    CODIGO_GASPAR)
        self.assertEqual(nivel, 4.12)

    def test_resposta_quebrada_nao_explode(self):
        for ruim in ({}, {"data": None}, {"data": {"tags_data": None}}, [], "erro"):
            self.assertEqual(estacoes(ruim), [])
            self.assertEqual(nivel_da_estacao(ruim, CODIGO_GASPAR), (None, None))

    def test_zero_e_leitura_nao_ausencia(self):
        """0,00 m é um nível; tratá-lo como ausente esconderia rio seco."""
        nivel, _ = nivel_da_estacao(resposta(estacao(CODIGO_GASPAR, 0.0)),
                                    CODIGO_GASPAR)
        self.assertEqual(nivel, 0.0)


class TestDeslocamento(unittest.TestCase):
    def test_precisa_dos_dois_lados(self):
        self.assertEqual(medir_deslocamento(None, None)[0], None)
        self.assertEqual(medir_deslocamento(4.0, None)[0], None)
        self.assertEqual(medir_deslocamento(None, 4.0)[0], None)

    def test_diz_qual_lado_faltou(self):
        self.assertIn("estadual", medir_deslocamento(None, 4.0)[1])
        self.assertIn("município", medir_deslocamento(4.0, None)[1])

    def test_par_proximo_e_indicio_de_mesma_regua(self):
        d, porque = medir_deslocamento(3.90, 3.85)
        self.assertAlmostEqual(d, 0.05)
        self.assertIn("batem", porque)

    def test_par_de_ilhota_seria_recusado(self):
        """O caso que já aconteceu: 7 m não é defasagem de horário."""
        d, porque = medir_deslocamento(10.67, 3.34)
        self.assertAlmostEqual(d, 7.33)
        self.assertIn("NÃO são a mesma régua", porque)

    def test_o_limite_separa_cheia_de_outro_zero(self):
        self.assertIn("batem", medir_deslocamento(4.0, 4.0 - LIMITE_DE_COERENCIA_M)[1])
        self.assertIn("NÃO", medir_deslocamento(4.0, 4.0 - LIMITE_DE_COERENCIA_M - 0.01)[1])


class TestEvidencia(unittest.TestCase):
    """A prova que sustenta o portão fica no arquivo, não na memória de alguém."""

    def test_a_evidencia_e_de_zeros_diferentes_de_verdade(self):
        self.assertTrue(EVIDENCIA_DE_ZEROS_DIFERENTES)
        for data, cod, deles, nosso, _ in EVIDENCIA_DE_ZEROS_DIFERENTES:
            self.assertGreater(abs(deles - nosso), 5.0,
                               f"{data} {cod}: a evidência precisa ser gritante")

    def test_as_cotas_de_gaspar_estao_na_faixa_que_o_deslocamento_arruinaria(self):
        """
        Não é abstrato: 5/6/7 m e um deslocamento de 7 m se sobrepõem. Se as
        cotas de Gaspar mudarem para uma escala em que isso deixe de valer,
        este teste cai e o raciocínio tem de ser refeito.
        """
        estacoes_json = json.loads(
            (Path(__file__).resolve().parent.parent / "data/estacoes.json").read_text())
        g = next(c for c in estacoes_json["rios"]["itajai-acu"]["cidades"]
                 if c["id"] == "gaspar")
        maior = max(g["cotas_m"].values())
        pior = max(abs(d - n) for _, _, d, n, _ in EVIDENCIA_DE_ZEROS_DIFERENTES)
        self.assertGreater(pior, maior,
                           "o deslocamento medido já passa da maior cota de Gaspar")


class TestNaoAlimentaOAviso(unittest.TestCase):
    def test_o_script_nao_escreve_no_arquivo_que_o_aviso_le(self):
        """
        `alerta_cotas.py` lê data/tempo-real/ultimo.json. Este script não pode
        escrever lá — seria contornar o próprio portão por um caminho de trás.
        """
        fonte = (Path(__file__).resolve().parent / "gaspar_estadual.py").read_text()
        depois_do_docstring = fonte.split('"""', 2)[-1]
        self.assertNotIn("ultimo.json\", \"w", depois_do_docstring)
        for escrita in ("grava_json", "write_text"):
            for linha in depois_do_docstring.splitlines():
                if escrita in linha:
                    self.assertNotIn("ultimo", linha)
                    self.assertNotIn("tempo-real", linha)


if __name__ == "__main__":
    unittest.main()
