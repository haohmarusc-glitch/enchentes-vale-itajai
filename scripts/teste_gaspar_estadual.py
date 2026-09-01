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
                             JANELA_MAXIMA_MIN, LIMITE_DE_COERENCIA_M,
                             ROTULO_MUNICIPIO, estacoes, medir_deslocamento,
                             minutos_entre, nivel_da_estacao, nivel_do_municipio,
                             usavel_para_aviso)


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


class TestLadoDoMunicipio(unittest.TestCase):
    """
    A primeira versão procurava em `ultimo.json` — arquivo da coleta geral, onde
    Gaspar não está, que é justamente o problema. Resultado: dizia "SEM LEITURA"
    com 3,85 m guardados no repositório ao lado. Um lado do par existia e o
    script não via.
    """

    def caminho(self):
        return Path(__file__).resolve().parent.parent / "data/tempo-real/ultimo_gaspar.json"

    def test_le_o_arquivo_que_o_coletor_de_gaspar_escreve(self):
        if not self.caminho().exists():
            self.skipTest("ultimo_gaspar.json ainda não coletado neste checkout")
        nivel, quando = nivel_do_municipio()
        self.assertIsNotNone(nivel, "há leitura no arquivo e o script não a achou")
        self.assertIsNotNone(quando)

    def test_o_rotulo_procurado_e_o_que_a_tabela_publica(self):
        if not self.caminho().exists():
            self.skipTest("ultimo_gaspar.json ainda não coletado neste checkout")
        rotulos = [e.get("rotulo")
                   for e in json.loads(self.caminho().read_text())["estacoes"]]
        self.assertIn(ROTULO_MUNICIPIO, rotulos)

    def test_ultimo_json_da_coleta_geral_nao_serve_de_fonte(self):
        """
        Gaspar não está no `ultimo.json` — é essa a lacuna. Um `ultimo.json`
        cheio, sem `ultimo_gaspar.json`, tem de dar "sem leitura": ler dali
        traria o nível de OUTRA cidade para o par de calibração de Gaspar.
        """
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            raiz = Path(tmp)
            (raiz / "tempo-real").mkdir()
            (raiz / "tempo-real" / "ultimo.json").write_text(json.dumps(
                {"leituras": [{"cidade": "gaspar", "nivel_m": 9.99,
                               "medido_em": "2026-09-01T03:00:00"}]}))
            antes = m.DADOS
            try:
                m.DADOS = raiz
                self.assertEqual(nivel_do_municipio(), (None, None))
            finally:
                m.DADOS = antes

    def test_leitura_marcada_implausivel_nao_vira_meio_par(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            raiz = Path(tmp)
            (raiz / "tempo-real").mkdir()
            (raiz / "tempo-real" / "ultimo_gaspar.json").write_text(json.dumps(
                {"estacoes": [{"rotulo": ROTULO_MUNICIPIO, "nivel_m": 392.62,
                               "nivel_plausivel": False,
                               "medido_em_iso": "2026-09-01T03:00:00"}]}))
            antes = m.DADOS
            try:
                m.DADOS = raiz
                nivel, quando = nivel_do_municipio()
                self.assertIsNone(nivel)
                self.assertEqual(quando, "2026-09-01T03:00:00")
            finally:
                m.DADOS = antes


class TestJanelaDeTempo(unittest.TestCase):
    """
    A falha mais perigosa da primeira versão: ela pareava leituras a horas de
    distância e devolvia a diferença como se fosse deslocamento de régua. Numa
    cheia o rio sobe nesse intervalo, e a parcela de subida não se separa da de
    régua — sairia um número que PARECE medido e não é.
    """

    def test_par_fora_da_janela_e_recusado(self):
        """O caso real: município 31/08 22:59 x estadual 01/09 03:24 = 266 min."""
        d, porque = medir_deslocamento(4.10, 3.85,
                                       "2026-09-01T03:24:30.759+00:00",
                                       "2026-08-31T22:59:00")
        self.assertIsNone(d)
        self.assertIn("266 min", porque)

    def test_par_dentro_da_janela_e_medido(self):
        d, _ = medir_deslocamento(4.10, 3.85,
                                  "2026-08-31T23:10:00", "2026-08-31T22:59:00")
        self.assertAlmostEqual(d, 0.25)

    def test_a_borda_da_janela(self):
        base = "2026-09-01T00:00:00"
        dentro = f"2026-09-01T00:{JANELA_MAXIMA_MIN:02d}:00"
        fora = f"2026-09-01T00:{JANELA_MAXIMA_MIN:02d}:01"
        self.assertIsNotNone(medir_deslocamento(4.1, 3.85, dentro, base)[0])
        self.assertIsNone(medir_deslocamento(4.1, 3.85, fora, base)[0])

    def test_horario_faltando_de_um_lado_recusa(self):
        """Sem horário não dá para afirmar que são o mesmo instante."""
        d, porque = medir_deslocamento(4.1, 3.85, None, "2026-08-31T22:59:00")
        self.assertIsNone(d)
        self.assertIn("sem horário", porque)

    def test_a_janela_e_curta_o_bastante_para_a_subida_ser_desprezivel(self):
        """
        A 20 cm/h — subida forte no médio Itajaí — a parcela de subida dentro da
        janela precisa ficar bem abaixo do limite de coerência, senão o veredito
        "batem" poderia ser só o rio parado por sorte.
        """
        subida_na_janela_m = 0.20 * (JANELA_MAXIMA_MIN / 60)
        self.assertLess(subida_na_janela_m, LIMITE_DE_COERENCIA_M / 5)

    def test_minutos_entre_aguenta_formatos_e_lixo(self):
        self.assertAlmostEqual(
            minutos_entre("2026-09-01T03:24:30.759+00:00", "2026-09-01T03:00:00Z"),
            24.5, places=1)
        for ruim in (None, "", "ontem", "2026-13-45"):
            self.assertIsNone(minutos_entre(ruim, "2026-09-01T03:00:00Z"))


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
