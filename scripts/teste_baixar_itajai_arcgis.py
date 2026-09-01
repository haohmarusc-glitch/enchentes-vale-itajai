#!/usr/bin/env python3
"""
Testes do baixador do ArcGIS de Itajaí.

Um baixador erra de dois jeitos que não aparecem no resultado: **para cedo** e
grava um acervo pela metade com cara de inteiro, ou **não para nunca** e roda
até o disco acabar. Os dois são silenciosos, e é neles que os testes batem.

O terceiro é específico do ArcGIS: ele responde **HTTP 200 com corpo de erro**,
que sem checagem vira uma camada de zero feições salva como se estivesse
completa.
"""

import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from baixar_itajai_arcgis import (CAMADAS, MAXIMO_DE_PAGINAS, POR_PAGINA,
                                  baixar_camada, ler_pagina, permitido,
                                  url_da_pagina)


def pagina(n: int, excedeu: bool = False) -> str:
    return json.dumps({
        "type": "FeatureCollection",
        "features": [{"type": "Feature", "properties": {"i": i}} for i in range(n)],
        "exceededTransferLimit": excedeu,
    })


class TestUrl(unittest.TestCase):
    def test_pede_geojson_em_4326_com_todos_os_campos(self):
        url = url_da_pagina("servico/MapServer", 0, 0)
        for pedaco in ("f=geojson", "outSR=4326", "outFields=*", "where=1%3D1"):
            self.assertIn(pedaco, url)

    def test_o_deslocamento_entra_na_url(self):
        self.assertIn("resultOffset=2000", url_da_pagina("s", 0, 2000))


class TestLerPagina(unittest.TestCase):
    def test_erro_do_arcgis_vira_excecao_e_nao_camada_vazia(self):
        """
        O ArcGIS manda 200 com corpo de erro. Sem esta checagem, a camada seria
        salva com zero feições como se estivesse completa.
        """
        corpo = json.dumps({"error": {"code": 400, "message": "Invalid or missing token"}})
        with self.assertRaises(ValueError) as caso:
            ler_pagina(corpo)
        self.assertIn("token", str(caso.exception))

    def test_resposta_sem_feicoes_e_recusada(self):
        with self.assertRaises(ValueError):
            ler_pagina(json.dumps({"type": "FeatureCollection"}))

    def test_pagina_boa_passa(self):
        self.assertEqual(len(ler_pagina(pagina(3))["features"]), 3)


class TestPaginacao(unittest.TestCase):
    def buscar(self, paginas):
        chamadas = []

        def buscar(url):
            chamadas.append(url)
            return paginas[len(chamadas) - 1]

        buscar.chamadas = chamadas
        return buscar

    def test_junta_as_paginas_ate_o_servico_dizer_que_acabou(self):
        buscar = self.buscar([pagina(POR_PAGINA, excedeu=True),
                              pagina(POR_PAGINA, excedeu=True),
                              pagina(237, excedeu=False)])
        feicoes = baixar_camada("s", 0, buscar=buscar, pausa=lambda: None)
        self.assertEqual(len(feicoes), 2 * POR_PAGINA + 237)
        self.assertEqual(len(buscar.chamadas), 3)

    def test_pagina_curta_encerra_mesmo_sem_o_campo_do_arcgis(self):
        """Nem todo serviço manda `exceededTransferLimit`."""
        buscar = self.buscar([json.dumps({"features": [{"i": 1}]})])
        self.assertEqual(len(baixar_camada("s", 0, buscar=buscar, pausa=lambda: None)), 1)
        self.assertEqual(len(buscar.chamadas), 1)

    def test_servico_que_ignora_o_deslocamento_nao_roda_para_sempre(self):
        """
        Página cheia e `exceededTransferLimit` eterno: sem teto, o laço não
        termina e o arquivo cresce até o disco acabar.
        """
        buscar = self.buscar([pagina(POR_PAGINA, excedeu=True)] * (MAXIMO_DE_PAGINAS + 5))
        with self.assertRaises(ValueError) as caso:
            baixar_camada("s", 0, buscar=buscar, pausa=lambda: None)
        self.assertIn("resultOffset", str(caso.exception))
        self.assertEqual(len(buscar.chamadas), MAXIMO_DE_PAGINAS)

    def test_respeita_o_turno_entre_paginas(self):
        """Fonte pública de graça: uma pausa por página, sem exceção."""
        pausas = []
        buscar = self.buscar([pagina(POR_PAGINA, excedeu=True), pagina(1)])
        baixar_camada("s", 0, buscar=buscar, pausa=lambda: pausas.append(1))
        self.assertEqual(len(pausas), 2)


class TestRobots(unittest.TestCase):
    def test_disallow_na_raiz_barra(self):
        self.assertFalse(permitido(buscar=lambda u: "User-agent: *\nDisallow: /"))

    def test_disallow_vazio_libera(self):
        self.assertTrue(permitido(buscar=lambda u: "User-agent: *\nDisallow:"))

    def test_sem_robots_txt_e_permissao_por_omissao(self):
        def falha(url):
            raise RuntimeError("404 Client Error: Not Found for url: " + url)
        self.assertTrue(permitido(buscar=falha))

    def test_erro_de_rede_nao_vira_permissao(self):
        """Não saber é motivo para não baixar, e não para baixar assim mesmo."""
        def falha(url):
            raise RuntimeError("Connection reset by peer")
        self.assertFalse(permitido(buscar=falha))


class TestCatalogo(unittest.TestCase):
    def test_as_tres_camadas_do_documento_estao_listadas(self):
        arquivos = {c["arquivo"] for c in CAMADAS}
        self.assertEqual(arquivos, {
            "itajai-arcgis-inundacoes.geojson.json",
            "itajai-pontos-cotados-altimetricos.geojson.json",
            "itajai-terreno-sujeito-inundacao.geojson.json",
        })

    def test_as_dez_camadas_de_inundacao(self):
        inundacoes = next(c for c in CAMADAS if "inundacoes" in c["arquivo"])
        self.assertEqual(inundacoes["camadas"], list(range(10)))

    def test_o_ponto_cotado_avisa_no_proprio_catalogo_o_que_ele_nao_e(self):
        """
        A descrição vai para o `_meta` do arquivo gravado. Quem abrir o bruto
        daqui a seis meses precisa ler, ali, que aquilo é altura de terreno —
        não a cota de régua que o nome do campo sugere.
        """
        cotado = next(c for c in CAMADAS if "cotados" in c["arquivo"])
        self.assertIn("não cota de régua", cotado["descricao"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
