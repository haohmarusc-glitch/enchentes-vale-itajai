#!/usr/bin/env python3
"""
Testes dos vãos do Ribeirão da Murta, sem rede.

Fixam o que decide gravar: os vãos têm de estar abertos no bruto dos ribeirões, a cadeia tem de ligar as duas pontas
de cada vão TERMINANDO nelas (não a 100 m), só com vias que ainda não estão no bruto, e com comprimento de travessia,
não de volta por outro curso.
"""
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import baixar_vao_murta as bm

V1, V2 = bm.VAOS


def via(id_, pontos, nome=None, tipo="stream", **tags):
    return {"type": "way", "id": id_,
            "geometry": [{"lon": p[0], "lat": p[1]} for p in pontos],
            "tags": {"waterway": tipo, **({"name": nome} if nome else {}), **tags}}


def meio(vao, fracao, desvio_lat=0.0):
    a, b = vao.montante, vao.jusante
    return (a[0] + (b[0] - a[0]) * fracao, a[1] + (b[1] - a[1]) * fracao + desvio_lat)


def deslocado(p, metros_norte):
    return (p[0], p[1] + metros_norte / 111_320.0)


class VaosAbertos(unittest.TestCase):
    def test_o_bruto_dos_ribeiroes_tem_os_dois_vaos(self):
        ribeiroes = json.loads(bm.BRUTO_RIBEIROES.read_text(encoding="utf-8"))["elements"]
        self.assertEqual([v.nome for v in bm.vaos_abertos(ribeiroes)], ["vao-1", "vao-2"])
        # As pontas cadastradas são as pontas das vias ditas, ao centímetro.
        por_id = {e["id"]: e for e in ribeiroes if e.get("type") == "way"}
        for vao in bm.VAOS:
            fim_montante = bm.pontas(por_id[vao.via_montante])[1]
            ini_jusante = bm.pontas(por_id[vao.via_jusante])[0]
            self.assertLess(bm.m(fim_montante, vao.montante), 1.0, vao.nome)
            self.assertLess(bm.m(ini_jusante, vao.jusante), 1.0, vao.nome)

    def test_os_vaos_medem_dezenas_de_metros(self):
        self.assertAlmostEqual(bm.m(V1.montante, V1.jusante), 78, delta=3)
        self.assertAlmostEqual(bm.m(V2.montante, V2.jusante), 38, delta=3)

    def test_vao_fechado_por_uma_via_da_murta_nao_e_vao(self):
        montante = via(1, [(-48.73, -26.90), V1.montante], bm.NOME_MURTA)
        ponte = via(2, [V1.montante, V1.jusante], bm.NOME_MURTA)
        jusante = via(3, [V1.jusante, (-48.71, -26.89)], bm.NOME_MURTA)
        self.assertFalse(bm.vao_aberto(V1, bm.vias_da_murta([montante, ponte, jusante])))
        self.assertTrue(bm.vao_aberto(V1, bm.vias_da_murta([montante, jusante])))
        # Via de outro nome ligando as pontas não fecha o vão "pela Murta": é emenda, não correção do OSM.
        bueiro = via(4, [V1.montante, V1.jusante])
        self.assertTrue(bm.vao_aberto(V1, bm.vias_da_murta([montante, bueiro, jusante])))

    def test_osm_corrigido_e_so_quando_a_propria_murta_liga_as_pontas(self):
        montante = via(1, [(-48.73, -26.90), V1.montante], bm.NOME_MURTA)
        jusante = via(3, [V1.jusante, (-48.71, -26.89)], bm.NOME_MURTA)
        self.assertFalse(bm.fechado_pela_murta(V1, []), "resposta sem a Murta não é correção")
        self.assertFalse(bm.fechado_pela_murta(V1, [montante, jusante]))
        self.assertFalse(bm.fechado_pela_murta(V1, [montante, via(4, [V1.montante, V1.jusante]), jusante]))
        self.assertTrue(bm.fechado_pela_murta(V1, [montante, via(2, [V1.montante, V1.jusante], bm.NOME_MURTA), jusante]))


class EmendaGravada(unittest.TestCase):
    def test_a_emenda_do_repositorio_fecha_os_vaos(self):
        if not bm.SAIDA.exists():
            self.skipTest("sem data/brutos/vao-murta-osm.json")
        for vao in bm.VAOS:
            self.assertTrue(bm.emenda_gravada_fecha(vao), vao.nome)

    def test_sem_emenda_ou_com_emenda_que_nao_liga_o_vao_segue_aberto(self):
        with tempfile.TemporaryDirectory() as d:
            falsa = Path(d) / "vao.json"
            with mock.patch.object(bm, "SAIDA", falsa):
                self.assertFalse(bm.emenda_gravada_fecha(V1))
                falsa.write_text(json.dumps({"elements": [via(1, [V1.montante, meio(V1, 0.5)])]}), encoding="utf-8")
                self.assertFalse(bm.emenda_gravada_fecha(V1))
                falsa.write_text(json.dumps({"elements": [via(1, [V1.montante, V1.jusante])]}), encoding="utf-8")
                self.assertTrue(bm.emenda_gravada_fecha(V1))
                self.assertFalse(bm.emenda_gravada_fecha(V2), "a emenda do vão 1 não fecha o vão 2")

    def test_rodada_com_a_emenda_nao_consulta_o_overpass(self):
        if not bm.SAIDA.exists():
            self.skipTest("sem data/brutos/vao-murta-osm.json")
        with mock.patch.object(bm, "buscar_consulta", side_effect=AssertionError("consultou o Overpass")), \
                mock.patch("sys.argv", ["baixar_vao_murta.py"]):
            self.assertEqual(bm.main(), 0)


class Encadeamento(unittest.TestCase):
    def test_a_cadeia_tem_de_terminar_na_ponta_de_jusante(self):
        # Para no meio do vão (a 39 m da ponta): no Canhanduba, com alvo de 100 m, contaria como chegada.
        curta = via(10, [V1.montante, meio(V1, 0.5)])
        self.assertEqual(bm.encadear([curta], V1.montante, V1.jusante), [])
        inteira = via(11, [V1.montante, V1.jusante], tunnel="culvert")
        self.assertEqual([v["id"] for v in bm.encadear([curta, inteira], V1.montante, V1.jusante)], [11])

    def test_vias_ja_no_bruto_nao_servem_de_emenda(self):
        ponte = via(V1.via_montante, [V1.montante, V1.jusante])   # o mesmo ID da via da Murta, redesenhada
        self.assertEqual(bm.encadear([ponte], V1.montante, V1.jusante, excluir={V1.via_montante}), [])
        self.assertEqual(len(bm.encadear([ponte], V1.montante, V1.jusante)), 1)

    def test_acha_a_ponte_em_duas_vias_e_ignora_o_que_nao_liga(self):
        solta = via(30, [deslocado(meio(V1, 0.5), 200), deslocado(meio(V1, 0.5), 400)], "Ribeirão Qualquer")
        a1 = via(31, [V1.montante, meio(V1, 0.5)])
        a2 = via(32, [V1.jusante, meio(V1, 0.5)])  # desenhada ao contrário: também liga
        self.assertEqual([v["id"] for v in bm.encadear([solta, a1, a2], V1.montante, V1.jusante)], [31, 32])


class ConferirCadeia(unittest.TestCase):
    def test_sem_cadeia_nao_grava(self):
        problemas, medidas = bm.conferir_cadeia(V2, [])
        self.assertTrue(problemas)
        self.assertEqual(medidas["reta_m"], 38)

    def test_bueiro_sem_nome_quase_reto_passa(self):
        cadeia = [via(10, [V2.montante, meio(V2, 0.5, 0.00002), V2.jusante], tunnel="culvert")]
        problemas, medidas = bm.conferir_cadeia(V2, cadeia)
        self.assertEqual(problemas, [])
        self.assertGreaterEqual(medidas["sinuosidade"], 1.0)
        self.assertEqual(medidas["vias"][0]["tunnel"], "culvert")
        self.assertIsNone(medidas["vias"][0]["name"])

    def test_bueiro_reto_entre_os_mesmos_nos_passa_apesar_do_arredondamento(self):
        # O caso da 1ª rodada: via de dois pontos nos nós das pontas, com a sétima casa decimal que `VAOS` não tem.
        cadeia = [via(556881887, [(-48.7169990, -26.8913440), (-48.7167101, -26.8911139)], tunnel="culvert")]
        problemas, medidas = bm.conferir_cadeia(V2, cadeia)
        self.assertEqual(problemas, [])
        self.assertEqual(medidas["cadeia_m"], 38)
        # Mas uma via que pare 2 m antes continua sendo medida errada.
        curta = [via(1, [V2.montante, meio(V2, 0.94)])]
        self.assertTrue(any("mais curta" in p for p in bm.conferir_cadeia(V2, curta)[0]))

    def test_volta_longa_por_outro_curso_e_recusada(self):
        longe = deslocado(V1.montante, -400)
        cadeia = [via(20, [V1.montante, longe]), via(21, [longe, V1.jusante])]
        problemas, medidas = bm.conferir_cadeia(V1, cadeia)
        self.assertTrue(any("outro curso" in p for p in problemas), problemas)
        self.assertGreater(medidas["sinuosidade"], bm.SINUOSIDADE_MAX)


class Caixa(unittest.TestCase):
    def test_a_caixa_contem_as_quatro_pontas_com_folga(self):
        s, o, n, l = bm.caixa()
        for vao in bm.VAOS:
            for lon, lat in (vao.montante, vao.jusante):
                self.assertTrue(s < lat < n and o < lon < l)
        self.assertIn('way["waterway"]', bm.consulta())
        self.assertLess((n - s) * 111.32, 2.0, "caixa de mais de 2 km para vãos de dezenas de metros")


class TracadoContinuo(unittest.TestCase):
    """Com as duas emendas, a Murta é contínua da DC-07 à foz, e o trecho do futuro vínculo está medido."""

    def test_o_tracado_gravado_tem_as_duas_emendas(self):
        geo = json.loads((bm.RAIZ / "data" / "rios" / "ribeirao-murta.geojson").read_text(encoding="utf-8"))
        self.assertEqual(sorted(e["id"] for e in geo["properties"]["emendas"]), [138922682, 556881887])
        self.assertTrue(all(e["tunnel"] == "culvert" and e["nome_no_osm"] is None for e in geo["properties"]["emendas"]))

    def test_dc07_alcanca_a_dc09_e_a_foz_so_por_arestas_do_tracado(self):
        import medir_alcance_murta as ma
        medidas = ma.medir(ma.linhas_do_tracado(), ma.reguas_da_murta(), ma.foz_da_murta())
        self.assertTrue(medidas["continuo"], medidas)
        self.assertLess(medidas["dc07"]["distancia_ao_tracado_m"], 50)
        self.assertLess(medidas["dc09"]["distancia_ao_tracado_m"], 50)
        self.assertAlmostEqual(medidas["dc07_ate_dc09_km"], 4.86, delta=0.05)
        self.assertAlmostEqual(medidas["dc09_ate_foz_km"], 1.43, delta=0.05)

    def test_sem_as_emendas_o_tracado_volta_a_ser_partido(self):
        import medir_alcance_murta as ma
        linhas = ma.linhas_do_tracado()
        geo = json.loads((bm.RAIZ / "data" / "rios" / "ribeirao-murta.geojson").read_text(encoding="utf-8"))
        n_emendas = len(geo["properties"]["emendas"])
        sem = linhas[:len(linhas) - n_emendas]   # as emendas entram por último no arquivo
        medidas = ma.medir(sem, ma.reguas_da_murta(), ma.foz_da_murta())
        self.assertFalse(medidas["continuo"])
        self.assertIsNone(medidas["dc07_ate_dc09_km"])


class Rodada(unittest.TestCase):
    """O fluxo do `main` com um Overpass fingido, sem rede."""

    def rodar(self, elementos, gravar, saida):
        resposta = {"osm3s": {"timestamp_osm_base": "2026-10-08T12:00:00Z"}, "elements": elementos}
        argv = ["baixar_vao_murta.py"] + (["--gravar"] if gravar else [])
        with mock.patch.object(bm, "SAIDA", saida), \
                mock.patch.object(bm, "buscar_consulta", return_value=(resposta, "espelho-de-teste")), \
                mock.patch("sys.argv", argv):
            return bm.main()

    def test_grava_os_dois_bueiros_e_a_rodada_seguinte_nao_consulta(self):
        b1 = via(901, [V1.montante, V1.jusante], tunnel="culvert")
        b2 = via(902, [V2.montante, V2.jusante], tunnel="culvert")
        with tempfile.TemporaryDirectory() as d:
            saida = Path(d) / "vao.json"
            self.assertEqual(self.rodar([b1, b2], True, saida), 0)
            gravado = json.loads(saida.read_text(encoding="utf-8"))
            self.assertEqual(sorted(v["id"] for v in gravado["elements"]), [901, 902])
            with mock.patch.object(bm, "SAIDA", saida), \
                    mock.patch.object(bm, "buscar_consulta", side_effect=AssertionError("consultou")), \
                    mock.patch("sys.argv", ["baixar_vao_murta.py"]):
                self.assertEqual(bm.main(), 0)

    def test_um_vao_so_grava_o_que_fechou_e_sai_vermelho(self):
        b1 = via(901, [V1.montante, V1.jusante], tunnel="culvert")
        with tempfile.TemporaryDirectory() as d:
            saida = Path(d) / "vao.json"
            self.assertEqual(self.rodar([b1], True, saida), 1)
            self.assertEqual([v["id"] for v in json.loads(saida.read_text(encoding="utf-8"))["elements"]], [901])

    def test_sem_cadeia_nada_e_gravado(self):
        with tempfile.TemporaryDirectory() as d:
            saida = Path(d) / "vao.json"
            self.assertEqual(self.rodar([], True, saida), 1)
            self.assertFalse(saida.exists())

    def test_osm_corrigido_pede_rebaixar_o_bruto_em_vez_de_emendar(self):
        murta = via(V1.via_montante, [(-48.73, -26.90), V1.montante, V1.jusante], bm.NOME_MURTA)
        resto = via(V1.via_jusante, [V1.jusante, V2.montante], bm.NOME_MURTA)
        with tempfile.TemporaryDirectory() as d:
            saida = Path(d) / "vao.json"
            self.assertEqual(self.rodar([murta, resto], True, saida), 1)
            self.assertFalse(saida.exists())


if __name__ == "__main__":
    unittest.main()
