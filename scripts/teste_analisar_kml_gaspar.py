#!/usr/bin/env python3
"""
Testes da análise do KML de Gaspar.

A análise de Brusque existia para RECUSAR um arquivo; esta existe para
AUTORIZAR um. A segunda é a mais perigosa das duas: recusar erra para o lado de
não ter dado, autorizar erra para o lado de publicar 1.615 números de
significado desconhecido como se fossem cota de régua. Então o que se testa
aqui é o portão — que ele feche sozinho assim que a evidência deixar de existir.
"""

import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from analisar_kml_gaspar import (BRUTO, CIDADE, PRIMEIRAS_RUAS, RUAS_SEGUINTES,
                                 carregar_bruto, importavel, minima_por_rua,
                                 numero, p_da_ordem, separacao_dos_grupos)
from analisar_kml_brusque import cruzar_com_cadastro, e_numero, normalizar
from comum import DADOS

#: `data_fonte` dos registros gerados por esta importação.
CAMADA_2020 = "2020-04"


class TestNumero(unittest.TestCase):
    def test_le_virgula_e_ponto(self):
        self.assertEqual(numero("8,25"), 8.25)
        self.assertEqual(numero("8.25"), 8.25)

    def test_o_que_nao_e_numero_vira_none(self):
        for t in (None, "", "sem cota", "8,25 m"):
            with self.subTest(t=t):
                self.assertIsNone(numero(t))


class TestMinimaPorRua(unittest.TestCase):
    """
    A mínima é a grandeza comparável: o cadastro guarda o ponto em que a rua
    COMEÇA a alagar, não a média nem o ponto mais alto dela.
    """

    def test_pega_o_menor_da_rua(self):
        pontos = [{"rua": "Rua X", "cota": 9.0}, {"rua": "Rua X", "cota": 6.5},
                  {"rua": "Rua Y", "cota": 7.0}]
        self.assertEqual(minima_por_rua(pontos), {"X": 6.5, "Y": 7.0})

    def test_ignora_ponto_sem_numero(self):
        self.assertEqual(minima_por_rua([{"rua": "Rua X", "cota": None}]), {})

    def test_booleano_nao_e_cota(self):
        self.assertEqual(minima_por_rua([{"rua": "Rua X", "cota": True}]), {})


class TestOrdemDosGrupos(unittest.TestCase):
    def test_grupo_separado_de_verdade_tem_p_pequeno(self):
        baixos = [1.0 + i / 10 for i in range(12)]
        altos = [9.0 + i / 10 for i in range(6)]
        self.assertLess(p_da_ordem(baixos, altos), 0.05)

    def test_amostra_pequena_nao_alcanca_significancia(self):
        """
        Com cinco e três valores, nem a separação perfeita desce de 0,05: há
        poucos embaralhamentos possíveis. O portão continua fechado, e é assim
        que tem de ser — três ruas não provam a régua de uma cidade.
        """
        self.assertGreater(p_da_ordem([1.0, 1.1, 1.2, 1.3, 1.4], [9.0, 9.1, 9.2]), 0.05)

    def test_grupos_embaralhados_nao_passam(self):
        self.assertGreater(p_da_ordem([1.0, 9.0, 1.1, 9.1], [1.2, 9.2]), 0.05)

    def test_grupo_vazio_nao_vira_prova(self):
        self.assertNotEqual(p_da_ordem([], [1.0]), p_da_ordem([], [1.0]),
                            "sem dado o resultado é NaN, que não passa em comparação")


class TestPortao(unittest.TestCase):
    """
    `importavel` é a única função deste arquivo que decide alguma coisa.
    """

    def test_uma_divergencia_ja_barra(self):
        self.assertFalse(importavel(acertos=3, total_comum=4, na_ordem=True, p_ordem=0.001),
                         "em Brusque era exatamente assim que a mistura aparecia")

    def test_ordem_errada_barra_mesmo_com_todos_os_acertos(self):
        self.assertFalse(importavel(acertos=4, total_comum=4, na_ordem=False, p_ordem=0.001))

    def test_ordem_certa_por_acaso_barra(self):
        self.assertFalse(importavel(acertos=4, total_comum=4, na_ordem=True, p_ordem=0.30))

    def test_poucas_ruas_em_comum_nao_provam_nada(self):
        self.assertFalse(importavel(acertos=2, total_comum=2, na_ordem=True, p_ordem=0.001))

    def test_autoriza_so_com_tudo(self):
        self.assertTrue(importavel(acertos=4, total_comum=4, na_ordem=True, p_ordem=0.0014))


class TestArquivoReal(unittest.TestCase):
    """A conclusão, refeita sobre o arquivo que está no repositório."""

    @classmethod
    def setUpClass(cls):
        cls.pontos = carregar_bruto()
        cls.minimas = minima_por_rua(cls.pontos)
        # Só o que se sabia ANTES desta importação. Cruzar o KML com os
        # registros que ele mesmo gerou seria compará-lo consigo mesmo.
        cls.cadastro = [
            c for c in json.loads(
                (DADOS / "cotas-ruas.json").read_text(encoding="utf-8"))["cotas"]
            if c.get("cidade") == CIDADE and c.get("data_fonte") != CAMADA_2020
        ]

    def test_todo_ponto_tem_numero_e_rua(self):
        for p in self.pontos:
            self.assertTrue(e_numero(p.get("cota")), p.get("rua"))
            self.assertTrue((p.get("rua") or "").strip())

    def test_toda_rua_em_comum_bate_ao_centavo(self):
        """
        O contraste com Brusque é o motivo de este arquivo entrar: lá 4 de 13
        batiam e nove divergiam de 0,5 a 2,3 m. Aqui não há divergência.
        """
        comuns = cruzar_com_cadastro(self.pontos, self.cadastro)
        self.assertGreaterEqual(len(comuns), 4)
        for c in comuns:
            with self.subTest(rua=c["rua"]):
                self.assertTrue(c["bate"], f"{c['rua']}: nosso {c['nosso_m']}, KML {c['kml_m'][:4]}")
                self.assertTrue(c["bate_no_menor"],
                                "o acerto tem de ser no MENOR valor da rua — é ali que a água chega")

    def test_as_duas_listas_publicadas_saem_na_ordem(self):
        g = separacao_dos_grupos(self.minimas)
        self.assertTrue(g["na_ordem"])
        self.assertLess(g["p"], 0.05)
        self.assertGreaterEqual(len(g["primeiras"]), 15)
        self.assertGreaterEqual(len(g["seguintes"]), 5)

    def test_o_veredito_continua_sendo_importar(self):
        comuns = cruzar_com_cadastro(self.pontos, self.cadastro)
        g = separacao_dos_grupos(self.minimas)
        self.assertTrue(importavel(sum(1 for c in comuns if c["bate"]), len(comuns),
                                   g["na_ordem"], g["p"]))

    def test_a_faixa_de_valor_cabe_numa_regua_de_rio(self):
        """
        Rio do Sul publica rua alagando a 19,01 m, então valor alto não é
        anomalia por si — mas 30 m seria, e foi o que denunciou a pasta de 2011
        de Brusque.
        """
        valores = [p["cota"] for p in self.pontos]
        self.assertGreater(min(valores), 3.0)
        self.assertLess(max(valores), 25.0)

    def test_a_menor_cota_do_arquivo_e_a_que_a_fonte_publica(self):
        """O estudo diz "primeiras ruas a partir de 6,00–6,20 m"."""
        self.assertAlmostEqual(min(p["cota"] for p in self.pontos), 6.20, places=2)

    def test_todas_as_ruas_das_duas_listas_estao_no_mapa(self):
        faltando = [n for n in PRIMEIRAS_RUAS + RUAS_SEGUINTES
                    if normalizar(n) not in self.minimas]
        self.assertEqual(faltando, [], "a fonte nomeia estas ruas; o mapa precisa tê-las")

    def test_o_bruto_avisa_que_campo_chamado_cota_nao_prova_nada(self):
        meta = json.loads((DADOS / BRUTO).read_text(encoding="utf-8"))["_meta"]
        self.assertIn("armadilha", json.dumps(meta, ensure_ascii=False))


if __name__ == "__main__":
    unittest.main(verbosity=2)
