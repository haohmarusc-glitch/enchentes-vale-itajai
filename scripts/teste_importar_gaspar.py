#!/usr/bin/env python3
"""
Testes do importador das cotas de Gaspar.

Esta é a maior importação do projeto — 1.613 pontos de uma vez. Quando ela foi
escrita, Gaspar não tinha cota nenhuma em `estacoes.json`, e o número na tela era
tudo o que o morador tinha. As faixas da régua chegaram depois, pelo Plano de
Contingência (5 / 6 / 7 m, ver `conferir_gaspar_plano.py`) — e o que sustenta
tratá-las como a mesma régua destes pontos é justamente a prova de escala que se
testa aqui. Ou seja: o portão ficou mais importante, não menos. O que se testa é
ele (que feche se a prova de escala cair), a substituição (que ela só alcance
registro realmente superado) e a identidade (que ponto nenhum apague outro em
silêncio).
"""

import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from analisar_kml_brusque import cruzar_com_cadastro, normalizar
from analisar_kml_gaspar import carregar_bruto, minima_por_rua, separacao_dos_grupos
from importar_cotas_gaspar import (CIDADE, COTA_MAXIMA_M, DATA_FONTE, chave,
                                   como_registro, mesclar, superados)

RAIZ = Path(__file__).resolve().parent.parent


def ponto(cota, rua="Rua Adriano Kormann", esquina=None, bairro="Bela Vista") -> dict:
    return {"cota": cota, "rua": rua, "esquina": esquina, "bairro": bairro}


class TestComoRegistro(unittest.TestCase):
    def test_registro_bom_sai_como_regua_e_confianca_alta(self):
        r = como_registro(ponto(8.25, esquina="Rua Nilton Cardoso"))
        self.assertEqual(r["cota_m"], 8.25)
        self.assertEqual(r["referencia"], "régua")
        self.assertEqual(r["confianca"], "alta")
        self.assertEqual(r["cidade"], "gaspar")
        self.assertEqual(r["rio"], "itajai-acu")
        self.assertEqual(r["ponto"], "Rua Nilton Cardoso")
        self.assertEqual(r["data_fonte"], DATA_FONTE)

    def test_ponto_sem_rua_nao_entra(self):
        self.assertIsNone(como_registro(ponto(8.25, rua="   ")))

    def test_cota_que_nao_e_numero_nao_entra(self):
        for c in (None, "8,25", True):
            with self.subTest(c=c):
                self.assertIsNone(como_registro(ponto(c)))

    def test_cota_fora_da_faixa_de_rio_nao_entra(self):
        """30 m foi o valor que denunciou a camada de 2011 de Brusque."""
        self.assertIsNone(como_registro(ponto(29.53)))
        self.assertIsNone(como_registro(ponto(-1.0)))
        self.assertIsNone(como_registro(ponto(0.0)))
        self.assertIsNotNone(como_registro(ponto(COTA_MAXIMA_M - 0.01)))


class TestIdentidade(unittest.TestCase):
    def test_mesma_rua_e_ponto_com_cotas_diferentes_sao_pontos_diferentes(self):
        a = {"cidade": CIDADE, "rua": "Rua Frei Canisio", "ponto": "251", "cota_m": 7.10}
        b = {"cidade": CIDADE, "rua": "Rua Frei Canisio", "ponto": "251", "cota_m": 8.91}
        self.assertNotEqual(chave(a), chave(b))

    def test_acento_e_caixa_nao_criam_registro_novo(self):
        a = {"cidade": CIDADE, "rua": "Rua Maestro Egon Bohn",
             "ponto": "Rua José Humberto Zimmermann", "cota_m": 6.58}
        b = {"cidade": CIDADE, "rua": "RUA MAESTRO EGON BOHN",
             "ponto": "rua jose  humberto zimmermann", "cota_m": 6.58}
        self.assertEqual(chave(a), chave(b))

    def test_registro_sem_cota_tem_identidade_propria(self):
        r = {"cidade": CIDADE, "rua": "Rua X", "ponto": None, "cota_m": None}
        self.assertEqual(chave(r)[-1], None)


class TestSuperados(unittest.TestCase):
    def antigos(self) -> list[dict]:
        return [
            # sem número, e a rua entra na importação: sai
            {"cidade": CIDADE, "rua": "Rua Alfazema", "ponto": None, "cota_m": None},
            # com número, mesmo repetido pela fonte oficial: FICA — é a prova
            # de escala desta importação
            {"cidade": CIDADE, "rua": "Rua Costa Rica", "ponto": None, "cota_m": 6.20},
            # rua que a importação não cobre: fica
            {"cidade": CIDADE, "rua": "Rua Lino", "ponto": None, "cota_m": 6.57},
            # outra cidade: nunca sai
            {"cidade": "blumenau", "rua": "Rua Alfazema", "ponto": None, "cota_m": None},
        ]

    def novos(self) -> list[dict]:
        return [
            {"cidade": CIDADE, "rua": "Rua Alfazema", "ponto": "A", "cota_m": 6.46,
             "data_fonte": DATA_FONTE},
            {"cidade": CIDADE, "rua": "Rua Costa Rica", "ponto": "B", "cota_m": 6.20,
             "data_fonte": DATA_FONTE},
        ]

    def test_so_sai_registro_sem_numero_de_rua_que_a_importacao_numera(self):
        self.assertEqual(superados(self.antigos(), self.novos()), [0])

    def test_a_prova_de_escala_nao_e_apagada_pela_importacao_que_ela_autoriza(self):
        """
        As cinco cotas numéricas do CEOPS são o único contra o que a escala
        deste KML foi conferida. Se a importação as apagasse por serem "o mesmo
        número, de fonte pior", a conferência ficaria sem contra o que rodar na
        próxima vez — a evidência sumiria junto com o registro.
        """
        saida, *_ = mesclar(self.antigos(), self.novos())
        antigo = [r for r in saida
                  if r["rua"] == "Rua Costa Rica" and r.get("data_fonte") != DATA_FONTE]
        self.assertEqual([r["cota_m"] for r in antigo], [6.20])

    def test_rua_fora_da_importacao_nao_perde_a_cota_que_tinha(self):
        saida, *_ = mesclar(self.antigos(), self.novos())
        ruas = [(r["cidade"], r["rua"], r["cota_m"]) for r in saida]
        self.assertIn((CIDADE, "Rua Lino", 6.57), ruas)
        self.assertIn(("blumenau", "Rua Alfazema", None), ruas)

    def test_nenhuma_rua_de_gaspar_fica_sem_registro_nenhum(self):
        """Substituir não pode virar sumir: toda rua que existia continua existindo."""
        antes = {normalizar(r["rua"]) for r in self.antigos() if r["cidade"] == CIDADE}
        saida, *_ = mesclar(self.antigos(), self.novos())
        depois = {normalizar(r["rua"]) for r in saida if r["cidade"] == CIDADE}
        self.assertEqual(antes - depois, set())


class TestMesclar(unittest.TestCase):
    def test_importar_duas_vezes_nao_duplica(self):
        """
        E, sobretudo, não apaga: sem cuidado, a segunda passada trataria os
        registros da primeira como "superados" e os removeria — se a fonte
        tivesse encolhido no meio, removeria sem repor.
        """
        novos = [{"cidade": CIDADE, "rua": "Rua X", "ponto": "A", "cota_m": 7.0,
                  "data_fonte": DATA_FONTE},
                 {"cidade": CIDADE, "rua": "Rua X", "ponto": "B", "cota_m": 8.0,
                  "data_fonte": DATA_FONTE}]
        saida, n, _, _ = mesclar([], novos)
        self.assertEqual(n, 2)
        de_novo, n2, repetidos, trocados = mesclar(saida, novos)
        self.assertEqual((n2, repetidos, trocados), (0, 2, []))
        self.assertEqual(len(de_novo), 2)

    def test_registro_de_outra_cidade_nunca_e_tocado(self):
        antigos = [{"cidade": "blumenau", "rua": "Rua São Rafael", "ponto": "final",
                    "cota_m": 7.4, "confianca": "media"}]
        saida, *_ = mesclar(antigos, [{"cidade": CIDADE, "rua": "Rua X", "ponto": None,
                                       "cota_m": 7.0}])
        self.assertEqual(saida[0], antigos[0])


class TestArquivoReal(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pontos = carregar_bruto()
        cls.registros = [r for r in (como_registro(p) for p in cls.pontos) if r]

    def test_todo_ponto_do_kml_vira_registro(self):
        """Se algum começar a cair, é sinal de que a fonte mudou de forma."""
        self.assertEqual(len(self.registros), len(self.pontos))

    def test_toda_cota_cabe_numa_regua_de_rio(self):
        for r in self.registros:
            with self.subTest(rua=r["rua"]):
                self.assertTrue(0 < r["cota_m"] < COTA_MAXIMA_M)

    def test_todo_registro_tem_fonte_referencia_e_confianca(self):
        for r in self.registros:
            self.assertEqual(r["referencia"], "régua")
            self.assertEqual(r["confianca"], "alta")
            self.assertIn("Gaspar", r["fonte"])

    def test_a_prova_de_escala_ainda_esta_de_pe(self):
        """
        O portão do importador, refeito aqui: se as ruas em comum deixarem de
        bater, a importação não pode mais acontecer — e este teste avisa antes.
        """
        cadastro = [c for c in json.loads(
            (RAIZ / "data" / "cotas-ruas.json").read_text(encoding="utf-8"))["cotas"]
            if c["cidade"] == CIDADE and c.get("data_fonte") != DATA_FONTE]
        comuns = cruzar_com_cadastro(self.pontos, cadastro)
        for c in comuns:
            with self.subTest(rua=c["rua"]):
                self.assertTrue(c["bate"] and c["bate_no_menor"])
        g = separacao_dos_grupos(minima_por_rua(self.pontos))
        self.assertTrue(g["na_ordem"])
        self.assertLess(g["p"], 0.05)


class TestNoArquivoGravado(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cotas = json.loads(
            (RAIZ / "data" / "cotas-ruas.json").read_text(encoding="utf-8"))["cotas"]
        cls.gaspar = [c for c in cotas if c["cidade"] == CIDADE]
        cls.oficiais = [c for c in cls.gaspar if c.get("data_fonte") == DATA_FONTE]

    def test_a_importacao_entrou(self):
        self.assertGreater(len(self.oficiais), 1500)

    def test_a_rua_que_a_importacao_nao_cobre_continua_no_arquivo(self):
        """
        "Rua Lino", 6,57 m, pode ser "Rua Lírio" com erro de transcrição — mas
        "pode ser" não apaga registro.
        """
        self.assertIn("Rua Lino", [c["rua"] for c in self.gaspar])

    def test_nenhuma_rua_de_gaspar_aparece_com_e_sem_numero_ao_mesmo_tempo(self):
        """
        O motivo da substituição: a mesma busca não pode devolver "alaga a
        partir de 6,46 m" e "cota não publicada" para a mesma rua.
        """
        com = {normalizar(c["rua"]) for c in self.gaspar if c["cota_m"] is not None}
        sem = {normalizar(c["rua"]) for c in self.gaspar if c["cota_m"] is None}
        self.assertEqual(com & sem, set())

    def test_a_primeira_rua_de_gaspar_continua_alagando_a_620(self):
        """O estudo publica "primeiras ruas a partir de 6,00–6,20 m"."""
        menor = min(c["cota_m"] for c in self.gaspar if c["cota_m"] is not None)
        self.assertAlmostEqual(menor, 6.20, places=2)


if __name__ == "__main__":
    unittest.main(verbosity=2)
