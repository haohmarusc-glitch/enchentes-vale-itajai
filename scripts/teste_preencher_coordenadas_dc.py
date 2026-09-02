#!/usr/bin/env python3
"""Testes do preenchedor de coordenadas das réguas DC de Itajaí."""

import json
import math
import unittest

from comum import DADOS
from preencher_coordenadas_dc import COORDENADAS, preencher


class Coerencia(unittest.TestCase):
    """As coordenadas têm de bater com a geografia — trava contra typo."""

    #: barra do rio Itajaí (foz), aproximada.
    FOZ = (-26.906, -48.642)

    def _dist(self, lat, lon):
        return math.hypot((lat - self.FOZ[0]) * 111.32,
                          (lon - self.FOZ[1]) * 111.32 * math.cos(math.radians(lat)))

    def test_sao_onze(self):
        self.assertEqual(len(COORDENADAS), 11)
        self.assertTrue(all(c.startswith("DC-") for c in COORDENADAS))
        self.assertNotIn("DC-00", COORDENADAS)  # pluviômetro, sem cota

    def test_todas_na_bbox_de_itajai(self):
        for cod, (lat, lon) in COORDENADAS.items():
            self.assertTrue(-27.10 < lat < -26.85, f"{cod} lat fora de Itajaí")
            self.assertTrue(-48.90 < lon < -48.60, f"{cod} lon fora de Itajaí")

    def test_dc01_e_a_mais_perto_da_foz_e_dc10_a_mais_longe(self):
        por_dist = sorted(COORDENADAS, key=lambda c: self._dist(*COORDENADAS[c]))
        self.assertEqual(por_dist[0], "DC-01", "CEPSUL tem de ser a mais próxima do mar")
        self.assertEqual(por_dist[-1], "DC-10", "Limoeiro tem de ser a mais distante")


class Preenche(unittest.TestCase):
    def _raw(self, com_dc, com_lat=()):
        itens = []
        for c in com_dc:
            campos = [f'"codigo": "{c}"', '"titulo": "x"']
            if c in com_lat:
                campos.insert(1, '"lat": -26.9')
                campos.insert(2, '"lon": -48.7')
            itens.append("    {\n      " + ",\n      ".join(campos) + "\n    }")
        return '{\n  "estacoes_tempo_real": [\n' + ",\n".join(itens) + "\n  ]\n}\n"

    def test_preenche_as_que_faltam(self):
        raw = self._raw(list(COORDENADAS))
        novo, feitas, ja = preencher(raw, forcar=False)
        self.assertEqual(len(feitas), 11)
        self.assertEqual(ja, [])
        d = json.loads(novo)
        for e in d["estacoes_tempo_real"]:
            self.assertEqual(e["lat"], COORDENADAS[e["codigo"]][0])
            self.assertIn("fonte_coordenada", e)

    def test_idempotente_nao_repreenche(self):
        raw = self._raw(list(COORDENADAS), com_lat=list(COORDENADAS))
        novo, feitas, ja = preencher(raw, forcar=False)
        self.assertEqual(feitas, [])
        self.assertEqual(len(ja), 11)
        self.assertEqual(novo, raw)  # nada muda

    def test_falta_uma_aborta_sem_gravar(self):
        raw = self._raw([c for c in COORDENADAS if c != "DC-05"])  # sem a DC-05
        with self.assertRaises(SystemExit):
            preencher(raw, forcar=False)


class ArquivoReal(unittest.TestCase):
    def test_as_onze_dc_do_estacoes_json_tem_coordenada(self):
        d = json.loads((DADOS / "estacoes.json").read_text(encoding="utf-8"))
        dc = {e["codigo"]: e for e in d["estacoes_tempo_real"]
              if str(e.get("codigo", "")).startswith("DC-") and e["codigo"] != "DC-00"}
        self.assertEqual(set(dc), set(COORDENADAS))
        for cod, e in dc.items():
            self.assertEqual([e.get("lat"), e.get("lon")], list(COORDENADAS[cod]))


if __name__ == "__main__":
    unittest.main()
