#!/usr/bin/env python3
"""Testes do coletor de chuva do CEMADEN (funções puras — sem rede)."""

import json
import unittest

from coleta_chuva_cemaden import (
    CATALOGO,
    MUNICIPIO_PARA_CIDADE,
    _municipio_sem_uf,
    _numero,
    converter,
    desembrulhar_jsonp,
)

MOMENTO = "2026-09-02T09:00:00"  # hora de Brasília fixa, para os testes não dependerem do relógio


def _reg(munic, lbl, cod="420290901A", nome="Centro", icon="flag_verde.png"):
    """Um registro bruto como o CEMADEN publica (nomes de campo reais)."""
    return {
        "estacao_cod": cod,
        "estacao_nome": nome,
        "estacao_munic": munic,
        "estacao_uf": "SC",
        "estacao_latlon": "[-27.098][-48.925]",
        "icon": f"https://x/{icon}",
        "lbl": lbl,
    }


class DesembrulhaJsonp(unittest.TestCase):
    def test_envelope_estacoes(self):
        self.assertEqual(desembrulhar_jsonp('estacoes([{"a":1}])'), [{"a": 1}])

    def test_envelope_com_ponto_e_virgula(self):
        self.assertEqual(desembrulhar_jsonp('estacoes([{"a":1}]);'), [{"a": 1}])

    def test_json_puro(self):
        self.assertEqual(desembrulhar_jsonp('[{"a":1}]'), [{"a": 1}])

    def test_objeto_com_features(self):
        self.assertEqual(desembrulhar_jsonp('cb({"features":[{"a":1}]})'), [{"a": 1}])


class MunicipioSemUf(unittest.TestCase):
    def test_tira_sufixo_uf(self):
        self.assertEqual(_municipio_sem_uf("BRUSQUE-SC"), "BRUSQUE")

    def test_sem_sufixo_fica_igual(self):
        self.assertEqual(_municipio_sem_uf("BLUMENAU"), "BLUMENAU")

    def test_nome_composto_com_uf(self):
        self.assertEqual(_municipio_sem_uf("Rio do Sul-SC"), "RIO DO SUL")

    def test_none_vira_vazio(self):
        self.assertEqual(_municipio_sem_uf(None), "")


class Numero(unittest.TestCase):
    def test_inteiro_e_float(self):
        self.assertEqual(_numero(12), 12.0)
        self.assertEqual(_numero(3.5), 3.5)

    def test_string_numerica(self):
        self.assertEqual(_numero("25"), 25.0)
        self.assertEqual(_numero("1,5"), 1.5)

    def test_vazio_e_bool_viram_none(self):
        self.assertIsNone(_numero(""))
        self.assertIsNone(_numero(None))
        self.assertIsNone(_numero(True))  # True não é milímetro


class Converter(unittest.TestCase):
    def test_mapeia_municipio_com_uf_para_cidade(self):
        leituras, recusadas, sem_dado = converter([_reg("BRUSQUE-SC", 12.0)], MOMENTO)
        self.assertEqual(len(leituras), 1)
        self.assertEqual(leituras[0]["cidade"], "brusque")
        self.assertEqual(leituras[0]["mm"]["h24"], 12.0)
        self.assertEqual((recusadas, sem_dado), ([], 0))

    def test_carimba_o_momento_da_coleta(self):
        # A fonte não traz hora por estação; medido_em é a hora da coleta.
        leituras, _, _ = converter([_reg("GASPAR-SC", 5.0)], MOMENTO)
        self.assertEqual(leituras[0]["medido_em"], MOMENTO)

    def test_so_h24_preenchido(self):
        leituras, _, _ = converter([_reg("ITAJAÍ-SC", 8.0)], MOMENTO)
        mm = leituras[0]["mm"]
        self.assertEqual(mm["h24"], 8.0)
        self.assertIsNone(mm["h1"])
        self.assertIsNone(mm["min10"])

    def test_municipio_fora_do_projeto_e_silencioso(self):
        leituras, recusadas, sem_dado = converter([_reg("FLORIANÓPOLIS-SC", 3.0)], MOMENTO)
        self.assertEqual((leituras, recusadas, sem_dado), ([], [], 0))

    def test_estacao_inativa_vira_sem_dado_nao_leitura(self):
        # flag_cinza = sem dado: não vira leitura, mesmo com número velho.
        leituras, recusadas, sem_dado = converter(
            [_reg("BLUMENAU-SC", 4.0, icon="flag_cinza.png")], MOMENTO)
        self.assertEqual(leituras, [])
        self.assertEqual((recusadas, sem_dado), ([], 1))

    def test_lbl_vazio_vira_sem_dado(self):
        leituras, recusadas, sem_dado = converter([_reg("BLUMENAU-SC", "")], MOMENTO)
        self.assertEqual(leituras, [])
        self.assertEqual((recusadas, sem_dado), ([], 1))

    def test_valor_absurdo_recusado(self):
        leituras, recusadas, sem_dado = converter([_reg("BRUSQUE-SC", 9999.0)], MOMENTO)
        self.assertEqual(leituras, [])
        self.assertEqual(len(recusadas), 1)
        self.assertIn("fora da faixa plausível", recusadas[0])

    def test_attributes_aninhado(self):
        # Envelope GeoJSON-like: campos dentro de "attributes".
        leituras, _, _ = converter([{"attributes": _reg("GUABIRUBA-SC", 2.0)}], MOMENTO)
        self.assertEqual(len(leituras), 1)
        self.assertEqual(leituras[0]["cidade"], "guabiruba")


class CatalogoBate(unittest.TestCase):
    """O mapa município->cidade tem de bater com o catálogo conferido."""

    @classmethod
    def setUpClass(cls):
        cls.cat = json.loads(CATALOGO.read_text(encoding="utf-8"))
        cls.municipios = {p["municipio"] for p in cls.cat["pluviometros"]}

    def test_todo_municipio_mapeado_existe_no_catalogo(self):
        faltando = set(MUNICIPIO_PARA_CIDADE) - self.municipios
        self.assertEqual(faltando, set(), f"município mapeado sem estação no catálogo: {faltando}")

    def test_ids_de_cidade_sao_do_projeto(self):
        validos = {
            "taio", "ituporanga", "rio-do-sul", "ibirama", "apiuna", "indaial",
            "blumenau", "gaspar", "ilhota", "itajai", "vidal-ramos", "botuvera",
            "guabiruba", "brusque", "timbo",
        }
        self.assertTrue(set(MUNICIPIO_PARA_CIDADE.values()) <= validos)

    def test_timbo_fica_de_fora(self):
        self.assertNotIn("timbo", MUNICIPIO_PARA_CIDADE.values())


if __name__ == "__main__":
    unittest.main()
