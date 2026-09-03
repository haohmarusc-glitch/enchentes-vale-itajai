#!/usr/bin/env python3
"""Testes do achar_confluencias: ordem pela água e o guarda 'não toca'."""

import importlib
import json
import unittest

from comum import DADOS
import achar_confluencias as ac


def _coord(cidade_id):
    d = json.loads((DADOS / "estacoes.json").read_text(encoding="utf-8"))
    return next(c for c in d["rios"]["itajai-acu"]["cidades"] if c["id"] == cidade_id)["coordenadas"]


class Confluencias(unittest.TestCase):
    def test_sem_geojson_reporta_e_nao_inventa(self):
        # Sem os GeoJSON dos afluentes (não estão no repo), nada é medido.
        r = ac.analisar()
        self.assertEqual(r["indaial"]["status"], "sem_geojson")
        self.assertEqual(r["ilhota"]["status"], "sem_geojson")

    def test_afluente_colado_no_tronco_diz_entre_quais_cidades(self):
        # Afluente falso tocando o tronco perto de Gaspar (montante de Ilhota):
        # tem de sair "antes de Ilhota", pela distância REAL pela água.
        gaspar = _coord("gaspar")
        fake = DADOS / "rios" / "luiz-alves.geojson"
        fake.write_text(json.dumps({
            "type": "Feature",
            "geometry": {"type": "LineString",
                         "coordinates": [[gaspar[1], gaspar[0]], [gaspar[1] + 0.02, gaspar[0] + 0.02]]},
        }))
        try:
            importlib.reload(ac)
            r = ac.analisar()["ilhota"]
        finally:
            fake.unlink()
            importlib.reload(ac)
        self.assertEqual(r["status"], "ok")
        self.assertIn("antes de Ilhota", r["texto"])

    def test_ponto_longe_do_tracado_nao_toca(self):
        # Um ponto longe do traçado NÃO vira confluência inventada.
        fake = DADOS / "rios" / "luiz-alves.geojson"
        fake.write_text(json.dumps({
            "type": "Feature",
            "geometry": {"type": "LineString", "coordinates": [[-49.9, -27.6], [-49.8, -27.5]]},
        }))
        try:
            importlib.reload(ac)
            r = ac.analisar()["ilhota"]
        finally:
            fake.unlink()
            importlib.reload(ac)
        self.assertEqual(r["status"], "nao_toca")


if __name__ == "__main__":
    unittest.main()
