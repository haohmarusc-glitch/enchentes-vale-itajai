#!/usr/bin/env python3
"""Testes do coletor de chuva do CEMADEN (funções puras — sem rede)."""

import json
import unittest

from coleta_chuva_cemaden import (
    CATALOGO,
    MUNICIPIO_PARA_CIDADE,
    _carimbo_iso,
    converter,
    desembrulhar_jsonp,
)


def _reg(municipio, valor, carimbo="2026-09-02T03:00:00", codigo="42000000A", nome="Centro"):
    """Um registro bruto plausível, com os nomes de chave que o coletor tenta."""
    return {
        "codigo": codigo,
        "nome": nome,
        "municipio": municipio,
        "acumulado24h": valor,
        "datahoraultimovalor": carimbo,
    }


class DesembrulhaJsonp(unittest.TestCase):
    def test_envelope_estacoes(self):
        self.assertEqual(desembrulhar_jsonp('estacoes([{"a":1}])'), [{"a": 1}])

    def test_envelope_com_ponto_e_virgula(self):
        self.assertEqual(desembrulhar_jsonp('estacoes([{"a":1}]);'), [{"a": 1}])

    def test_json_puro(self):
        self.assertEqual(desembrulhar_jsonp('[{"a":1}]'), [{"a": 1}])

    def test_objeto_com_lista_dentro(self):
        self.assertEqual(desembrulhar_jsonp('cb({"estacoes":[{"a":1}]})'), [{"a": 1}])


class Converter(unittest.TestCase):
    def test_mapeia_municipio_para_cidade(self):
        leituras, recusadas = converter([_reg("BLUMENAU", 12.0)])
        self.assertEqual(len(leituras), 1)
        self.assertEqual(leituras[0]["cidade"], "blumenau")
        self.assertEqual(leituras[0]["mm"]["h24"], 12.0)
        self.assertEqual(recusadas, [])

    def test_caixa_do_municipio_nao_importa(self):
        leituras, _ = converter([_reg("Blumenau", 5.0)])
        self.assertEqual(len(leituras), 1)

    def test_municipio_fora_do_projeto_e_silencioso(self):
        # Florianópolis vem no feed estadual, mas não é cidade do projeto.
        leituras, recusadas = converter([_reg("FLORIANÓPOLIS", 3.0)])
        self.assertEqual(leituras, [])
        self.assertEqual(recusadas, [])  # ignorado sem ruído, não é "recusa"

    def test_so_h24_preenchido(self):
        leituras, _ = converter([_reg("GASPAR", 8.0)])
        mm = leituras[0]["mm"]
        self.assertEqual(mm["h24"], 8.0)
        self.assertIsNone(mm["h1"])
        self.assertIsNone(mm["min10"])

    def test_carimbo_utc_vira_brasilia(self):
        # 03:00 UTC -> 00:00 de Brasília (-3h), sem fuso no texto.
        leituras, _ = converter([_reg("ITAJAÍ", 1.0, carimbo="2026-09-02T03:00:00")])
        self.assertEqual(leituras[0]["medido_em"], "2026-09-02T00:00:00")

    def test_chave_de_valor_nao_reconhecida_e_recusa_nao_fabricacao(self):
        # Registro sem nenhuma chave de valor conhecida: recusa explícita,
        # NUNCA vira leitura com zero inventado.
        reg = {"codigo": "x", "municipio": "BLUMENAU", "precipitacao_estranha": 4.0}
        leituras, recusadas = converter([reg])
        self.assertEqual(leituras, [])
        self.assertEqual(len(recusadas), 1)
        self.assertIn("sem chave de chuva reconhecida", recusadas[0])
        self.assertIn("precipitacao_estranha", recusadas[0])

    def test_valor_absurdo_recusado(self):
        leituras, recusadas = converter([_reg("BRUSQUE", 9999.0)])
        self.assertEqual(leituras, [])
        self.assertEqual(len(recusadas), 1)
        self.assertIn("fora da faixa plausível", recusadas[0])

    def test_booleano_nao_e_chuva(self):
        # e_numero rejeita bool; True não é milímetro.
        leituras, recusadas = converter([_reg("GASPAR", True)])
        self.assertEqual(leituras, [])
        self.assertEqual(len(recusadas), 1)


class Carimbo(unittest.TestCase):
    def test_espaco_e_milissegundos(self):
        self.assertEqual(_carimbo_iso("2026-09-02 03:00:00.0"), "2026-09-02T03:00:00")

    def test_nao_texto_vira_none(self):
        self.assertIsNone(_carimbo_iso(None))
        self.assertIsNone(_carimbo_iso(123))


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
        # Ids reais de data/estacoes.json (Açu + Mirim + afluentes com tela).
        validos = {
            "taio", "ituporanga", "rio-do-sul", "ibirama", "apiuna", "indaial",
            "blumenau", "gaspar", "ilhota", "itajai", "vidal-ramos", "botuvera",
            "guabiruba", "brusque", "timbo",
        }
        self.assertTrue(set(MUNICIPIO_PARA_CIDADE.values()) <= validos)

    def test_timbo_fica_de_fora(self):
        # Coerência com coleta_chuva_sc: Timbó é afluente sem tela.
        self.assertNotIn("timbo", MUNICIPIO_PARA_CIDADE.values())


if __name__ == "__main__":
    unittest.main()
