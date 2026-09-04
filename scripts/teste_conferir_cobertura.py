#!/usr/bin/env python3
"""
Testes da conferência de cobertura.

Cinza no mapa não é defeito — é o site se recusando a afirmar o que não mediu.
O que este script mede é o TAMANHO dessa recusa, e a CAUSA de cada pedaço, para
ordenar a quem pedir o quê. Confundir "sem leitura" com "sem cota" manda o
ofício para a pessoa errada.
"""
import json
import unittest
from pathlib import Path

import conferir_cobertura as cc

RAIZ = Path(__file__).resolve().parent.parent


def leitura(cidade, rio, nivel=1.0):
    return {"estacao": cidade, "rio": rio, "cidade": cidade, "nivel_m": nivel,
            "medido_em": "2026-09-04T12:00:00"}


class Causas(unittest.TestCase):
    """A causa tem de distinguir os três casos — eles se destravam diferente."""

    def monta(self, cotas, tem_leitura):
        est = {"rios": {"r": {"cidades": [
            {"id": "a", "coordenadas": [-27.0, -49.0], "cotas_m": {}},
            {"id": "b", "coordenadas": [-27.0, -48.6], "cotas_m": cotas},
        ]}}}
        ls = [leitura("b", "r")] if tem_leitura else []
        return est, ls

    def causa_de(self, cotas, tem_leitura, monkey_geo=True):
        est, ls = self.monta(cotas, tem_leitura)
        r = cc.avaliar("r", est, ls)
        return {a["cidade"]: a for a in r["ancoras"]}["b"]

    def setUp(self):
        # Um "rio" reto e denso, escrito num geojson temporário.
        self.tmp = RAIZ / "data" / "rios" / "r.geojson"
        linha = [[-49.0 + i * 0.001, -27.0] for i in range(401)]
        self.tmp.write_text(json.dumps(
            {"type": "Feature", "properties": {},
             "geometry": {"type": "MultiLineString", "coordinates": [linha]}}), encoding="utf-8")

    def tearDown(self):
        self.tmp.unlink(missing_ok=True)

    def test_com_cota_e_leitura_a_cidade_PINTA(self):
        a = self.causa_de({"atencao": 5.0}, True)
        self.assertTrue(a["pinta"], a)
        self.assertEqual(a["causa"], "")

    def test_cota_sem_leitura_e_SEM_LEITURA(self):
        a = self.causa_de({"atencao": 5.0}, False)
        self.assertFalse(a["pinta"])
        self.assertEqual(a["causa"], "sem leitura")

    def test_leitura_sem_cota_e_SEM_COTA(self):
        a = self.causa_de({}, True)
        self.assertFalse(a["pinta"])
        self.assertEqual(a["causa"], "sem cota")

    def test_sem_nada_diz_as_DUAS_coisas(self):
        a = self.causa_de({}, False)
        self.assertEqual(a["causa"], "sem leitura e sem cota")

    def test_o_km_atribuido_soma_o_tracado_inteiro(self):
        est, ls = self.monta({"atencao": 5.0}, True)
        r = cc.avaliar("r", est, ls)
        self.assertAlmostEqual(sum(a["km"] for a in r["ancoras"]), r["km_total"], places=6)


class ContraOsDadosReais(unittest.TestCase):
    def test_o_eixo_do_Acu_exclui_os_afluentes_laterais(self):
        """
        Quem pinta é o eixo. Se um afluente lateral voltasse a entrar, ele
        levaria km do tronco para a conta dele — e a prioridade sairia errada.
        """
        est = json.loads((RAIZ / "data/estacoes.json").read_text(encoding="utf-8"))
        r = cc.avaliar("itajai-acu", est, [])
        if r is None:
            self.skipTest("traçado do Açu ausente neste checkout")
        ids = {a["cidade"] for a in r["ancoras"]}
        for lateral in ("timbo", "rio-dos-cedros", "ibirama", "trombudo-central"):
            self.assertNotIn(lateral, ids, f"{lateral} voltou a pintar o Açu")
        self.assertIn("blumenau", ids)

    def test_Ituporanga_fica_de_fora_pela_guarda_geometrica(self):
        """
        É cabeceira (logo, no eixo), mas o rio dela não está desenhado: fica a
        28 km do traçado. Sem a guarda, ela levaria km que não são dela.
        """
        est = json.loads((RAIZ / "data/estacoes.json").read_text(encoding="utf-8"))
        r = cc.avaliar("itajai-acu", est, [])
        if r is None:
            self.skipTest("traçado do Açu ausente neste checkout")
        self.assertNotIn("ituporanga", {a["cidade"] for a in r["ancoras"]})


if __name__ == "__main__":
    unittest.main()
