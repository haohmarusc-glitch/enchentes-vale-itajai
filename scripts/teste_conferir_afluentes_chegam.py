#!/usr/bin/env python3
"""
Testes da conferência "o afluente chega no rio?".

Afluente cortado é pior que afluente ausente. Ausente, quem olha sabe que não
sabe. Cortado, o mapa AFIRMA que a água pára ali — e quem mora entre a ponta do
traçado e o rio conclui que o ribeirão não chega perto de casa.
"""
import json
import tempfile
import unittest
from pathlib import Path

import conferir_afluentes_chegam as cf

RAIZ = Path(__file__).resolve().parent.parent


def geojson(linhas):
    return {"type": "Feature", "properties": {},
            "geometry": {"type": "MultiLineString", "coordinates": linhas}}


class Medida(unittest.TestCase):
    """Contra arquivos inventados, para o cálculo não depender do dado real."""

    def monta(self, arquivos: dict) -> Path:
        tmp = Path(tempfile.mkdtemp())
        for nome, linhas in arquivos.items():
            (tmp / f"{nome}.geojson").write_text(
                json.dumps(geojson(linhas)), encoding="utf-8")
        return tmp

    def com(self, arquivos, **kw):
        antigo = cf.RIOS
        cf.RIOS = self.monta(arquivos)
        try:
            return cf.avaliar(**kw)
        finally:
            cf.RIOS = antigo

    def test_afluente_que_encosta_no_tronco_nao_e_cortado(self):
        rs = self.com({
            "itajai-mirim": [[[-48.70, -26.93], [-48.68, -26.93]]],
            "ribeirao-x": [[[-48.69, -26.95], [-48.69, -26.93]]],  # toca a linha
        })
        self.assertEqual(len(rs), 1)
        self.assertFalse(rs[0]["cortado"], rs[0])
        self.assertEqual(rs[0]["chega_em"], "itajai-mirim")

    def test_afluente_que_para_longe_e_cortado(self):
        rs = self.com({
            "itajai-mirim": [[[-48.70, -26.93], [-48.68, -26.93]]],
            "ribeirao-x": [[[-48.69, -26.98], [-48.69, -26.96]]],  # ~3 km antes
        })
        self.assertTrue(rs[0]["cortado"])
        self.assertGreater(rs[0]["metros"], 1000)

    def test_a_PONTA_e_que_conta_nao_a_passagem_perto(self):
        """
        Um afluente pode roçar o tronco no meio do curso e desaguar longe. Medir
        o ponto mais próximo de QUALQUER vértice diria "chega" para um traçado
        que não chega.
        """
        rs = self.com({
            "itajai-mirim": [[[-48.70, -26.93], [-48.60, -26.93]]],
            # Passa colado ao tronco no meio, mas as duas pontas ficam longe.
            "ribeirao-x": [[[-48.65, -26.99], [-48.65, -26.9301], [-48.65, -26.87]]],
        })
        self.assertTrue(rs[0]["cortado"], "passar perto no meio não é desaguar")

    def test_afluente_que_chega_PELO_VIZINHO_nao_e_cortado(self):
        """
        O caso real do Canhanduba: ele não toca o Mirim — deságua no Rio
        Conceição, que deságua no Mirim. É geografia, não defeito, e foi por
        isso que a busca por nome nunca fechou o vão.
        """
        rs = {r["rio"]: r for r in self.com({
            "itajai-mirim": [[[-48.70, -26.93], [-48.60, -26.93]]],
            # O vizinho toca o tronco.
            "rio-conceicao": [[[-48.65, -26.95], [-48.65, -26.9301]]],
            # E o afluente toca o vizinho, longe do tronco.
            "ribeirao-x": [[[-48.65, -26.98], [-48.65, -26.9501]]],
        })}
        self.assertFalse(rs["ribeirao-x"]["cortado"], rs["ribeirao-x"])
        self.assertEqual(rs["ribeirao-x"]["via"], ["rio-conceicao"])
        self.assertEqual(rs["ribeirao-x"]["chega_em"], "itajai-mirim")

    def test_chegar_por_vizinho_que_TAMBEM_esta_cortado_nao_vale(self):
        """
        Encostar num curso que não chega a lugar nenhum não faz a água chegar.
        Sem esta regra, dois afluentes cortados se validariam um ao outro.
        """
        rs = {r["rio"]: r for r in self.com({
            "itajai-mirim": [[[-48.70, -26.93], [-48.60, -26.93]]],
            "solto-a": [[[-48.65, -26.99], [-48.65, -26.97]]],
            "solto-b": [[[-48.65, -26.9701], [-48.65, -26.96]]],
        })}
        self.assertTrue(rs["solto-a"]["cortado"])
        self.assertTrue(rs["solto-b"]["cortado"])

    def test_quem_chega_DIRETO_nao_ganha_via(self):
        rs = {r["rio"]: r for r in self.com({
            "itajai-mirim": [[[-48.70, -26.93], [-48.60, -26.93]]],
            "ribeirao-x": [[[-48.65, -26.95], [-48.65, -26.9301]]],
        })}
        self.assertEqual(rs["ribeirao-x"]["via"], [])

    def test_o_tronco_nao_e_avaliado_como_afluente(self):
        rs = self.com({
            "itajai-acu": [[[-48.70, -26.90], [-48.60, -26.90]]],
            "itajai-mirim": [[[-48.70, -26.93], [-48.60, -26.93]]],
        })
        self.assertEqual(rs, [])


class ContraOsDadosReais(unittest.TestCase):
    def setUp(self):
        self.rs = {r["rio"]: r for r in cf.avaliar()}

    def test_o_Murta_chega_no_Acu(self):
        """Regra permanente: este afluente está completo e tem de continuar."""
        r = self.rs["ribeirao-murta"]
        self.assertEqual(r["chega_em"], "itajai-acu")
        self.assertFalse(r["cortado"], f"o Murta se afastou do Açu: {r['metros']} m")

    def test_o_Canhanduba_e_o_BURACO_CONHECIDO_de_578_m(self):
        """
        RETRATO QUE DEVE ENVELHECER, como o das quatro réguas que faltavam.

        Em 04/09/2026 o traçado do Canhanduba morre a 578 m do Itajaí-Mirim: o
        último trecho antes da foz não casou com nenhum nome da consulta, e não
        está no bruto (`data/brutos/tracado-ribeiroes-osm.json` só tem 19
        elementos, e os três perto da ponta já foram convertidos).

        Quando o trecho for rebaixado, este teste FALHA — e a falha é a notícia
        boa. Aí: apague este teste, deixe o `test_o_Murta_chega_no_Acu` valer
        para todos, e feche a pendência do README.
        """
        r = self.rs["ribeirao-canhanduba"]
        self.assertEqual(r["chega_em"], "itajai-mirim",
                         "o Canhanduba deságua no Mirim — se mudou de tronco, "
                         "o traçado foi trocado")
        if (cf.RIOS / "rio-conceicao.geojson").exists():
            # VÃO FECHADO. O `baixar_vao_canhanduba.py` mostrou (04/09/2026) que
            # o trecho final se chama Rio Conceição: 3 vias, ~650 m de canal
            # para 578 m em linha reta — sinuosidade 1,12, normal em várzea.
            # Com ele desenhado, o Canhanduba chega ao Mirim PELO Conceição.
            self.assertFalse(r["cortado"], f"o Conceição está em data/rios/ mas "
                                           f"o Canhanduba segue a {r['metros']} m")
            self.assertEqual(r["via"], ["rio-conceicao"])
            return
        # AINDA ABERTO: retrato dos 578 m, que deve envelhecer.
        self.assertAlmostEqual(
            r["metros"], 578, delta=30,
            msg=f"o vão do Canhanduba mudou ({r['metros']} m) e o Conceição não "
                "está em data/rios/. Se o traçado perdeu vias, investigue; se o "
                "vão fechou por outro caminho, atualize este teste.")


if __name__ == "__main__":
    unittest.main()
