#!/usr/bin/env python3
"""
Testes da análise das camadas do ArcGIS de Itajaí.

O teste que mais importa aqui é o do item 3. A camada
`Hidrografia_Terreno_Sujeito_Inundacao` tem um nome que promete "a área
inundável da cidade" e entrega 38,7 hectares — 183 vezes menos que a mancha de
1983. Mostrar isso na tela com esse rótulo diria a quem mora fora dos polígonos
que sua rua não alaga.

Um erro assim não aparece em nenhum teste de formato: o arquivo é válido, os
polígonos são reais, as coordenadas estão certas. Só a comparação de ordem de
grandeza denuncia.
"""

import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from analisar_itajai_arcgis import (AREA_OFICIAL_HA, FRACAO_MINIMA_DA_MANCHA,
                                    INUNDACOES, TERRENO, TOLERANCIA_AREA,
                                    area_ha, carregar, mesma_geometria,
                                    por_camada, terreno_descreve_a_cidade)

RAIZ = Path(__file__).resolve().parent.parent


def quadrado(lon, lat, lado_graus):
    d = lado_graus
    return {"type": "Feature", "properties": {},
            "geometry": {"type": "Polygon", "coordinates": [[
                [lon, lat], [lon + d, lat], [lon + d, lat + d], [lon, lat + d], [lon, lat]]]}}


class TestArea(unittest.TestCase):
    def test_area_de_um_quadrado_conhecido(self):
        """0,01° de lado perto de Itajaí é ~1,1 km × 1,1 km ≈ 122 ha."""
        a = area_ha([quadrado(-48.7, -26.9, 0.01)])
        self.assertGreater(a, 100)
        self.assertLess(a, 140)

    def test_buraco_e_descontado(self):
        f = quadrado(-48.7, -26.9, 0.01)
        anel = f["geometry"]["coordinates"][0]
        buraco = [[x + 0.0025 if i in (1, 2) else x + 0.0025, y + 0.0025] for i, (x, y) in
                  enumerate(anel)]
        cheio = area_ha([f])
        f["geometry"]["coordinates"].append(buraco)
        self.assertLess(area_ha([f]), cheio)

    def test_geometria_que_nao_e_poligono_nao_soma_area(self):
        self.assertEqual(area_ha([{"geometry": {"type": "Point", "coordinates": [-48.7, -26.9]}}]), 0)
        self.assertEqual(area_ha([{}]), 0)


class TestTrocaDasManchas(unittest.TestCase):
    def test_contagem_igual_quer_dizer_que_a_troca_nao_traz_geometria(self):
        arc = {0: [1], 1: [1, 2]}
        nosso = [{"feicoes": 1}, {"feicoes": 2}]
        self.assertEqual(mesma_geometria(arc, nosso), [])

    def test_contagem_diferente_e_relatada(self):
        arc = {0: [1, 2, 3]}
        self.assertTrue(mesma_geometria(arc, [{"feicoes": 1}]))


class TestOTerrenoNaoDescreveACidade(unittest.TestCase):
    def test_camada_minuscula_nao_pode_virar_area_inundavel(self):
        self.assertFalse(terreno_descreve_a_cidade(38.7, 7061.0))

    def test_camada_da_ordem_da_mancha_poderia(self):
        self.assertTrue(terreno_descreve_a_cidade(5000.0, 7061.0))

    def test_o_limiar_e_um_quarto_da_mancha(self):
        self.assertAlmostEqual(FRACAO_MINIMA_DA_MANCHA, 0.25)
        a_1983 = 1000.0
        self.assertTrue(terreno_descreve_a_cidade(a_1983 * 0.25, a_1983))
        self.assertFalse(terreno_descreve_a_cidade(a_1983 * 0.24, a_1983))

    def test_sem_mancha_para_comparar_nao_autoriza(self):
        self.assertFalse(terreno_descreve_a_cidade(38.7, 0.0))


class TestArquivosReais(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.inundacoes = por_camada(carregar(INUNDACOES))
        cls.terreno = por_camada(carregar(TERRENO))[0]

    def test_as_dez_camadas_de_inundacao_vieram(self):
        self.assertEqual(sorted(self.inundacoes), list(range(10)))

    def test_a_contagem_bate_com_as_manchas_que_ja_temos(self):
        indice = json.loads(
            (RAIZ / "data" / "manchas" / "index.json").read_text(encoding="utf-8"))["manchas"]
        self.assertEqual(mesma_geometria(self.inundacoes, indice), [])

    def test_a_area_publicada_confere_com_a_calculada(self):
        for camada, (evento, publicada) in AREA_OFICIAL_HA.items():
            with self.subTest(evento=evento):
                calculada = area_ha(self.inundacoes[camada])
                self.assertLessEqual(abs(calculada - publicada) / publicada, TOLERANCIA_AREA)

    def test_a_area_de_2011_nao_entra_na_tabela_oficial(self):
        """
        Os 32 polígonos de 2011 se sobrepõem: somar o campo `areas` dá 6.995 ha
        contra 7.634 calculados. Soma de polígono sobreposto não é área.
        """
        self.assertNotIn(4, AREA_OFICIAL_HA)
        soma = sum(f["properties"].get("areas", 0) for f in self.inundacoes[4]) / 10000
        self.assertGreater(abs(soma - area_ha(self.inundacoes[4])) / soma, 0.05)

    def test_o_terreno_continua_pequeno_demais_para_ir_para_a_tela(self):
        """
        O guarda que importa. Se alguém trocar o arquivo por um levantamento de
        verdade, este teste passa a falhar — e aí é hora de rediscutir a tela.
        Enquanto falhar do jeito atual, a camada não entra.
        """
        a_terreno = area_ha(self.terreno)
        a_1983 = area_ha(self.inundacoes[0])
        self.assertFalse(terreno_descreve_a_cidade(a_terreno, a_1983),
                         f"a camada passou a cobrir {a_terreno:.0f} ha de {a_1983:.0f} — "
                         "rediscutir se ela pode ir para a tela")
        self.assertLess(a_terreno, 100, "38,7 ha era o total quando isto foi analisado")

    def test_o_bruto_do_ponto_cotado_avisa_o_que_ele_nao_e(self):
        meta = carregar("brutos/itajai-pontos-cotados-altimetricos.geojson.json")["_meta"]
        self.assertIn("não cota de régua", json.dumps(meta, ensure_ascii=False))


if __name__ == "__main__":
    unittest.main(verbosity=2)
