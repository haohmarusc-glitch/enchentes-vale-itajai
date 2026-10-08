#!/usr/bin/env python3
"""Testes do achar_confluencias: ordem pela água e o guarda 'não toca'."""

import importlib
import json
import unittest
from contextlib import contextmanager

from comum import DADOS
import achar_confluencias as ac


def _coord(cidade_id):
    d = json.loads((DADOS / "estacoes.json").read_text(encoding="utf-8"))
    return next(c for c in d["rios"]["itajai-acu"]["cidades"] if c["id"] == cidade_id)["coordenadas"]


@contextmanager
def luiz_alves_trocado(conteudo):
    """
    Troca o data/rios/luiz-alves.geojson pelo `conteudo` (ou o tira, com None) e devolve o REAL no fim.

    Antes de 08/10/2026 o arquivo não existia, e os testes escreviam um falso e o apagavam. Com o traçado
    baixado, apagar no fim levava junto o arquivo de verdade.
    """
    caminho = DADOS / "rios" / "luiz-alves.geojson"
    original = caminho.read_bytes() if caminho.exists() else None
    try:
        if conteudo is None:
            caminho.unlink(missing_ok=True)
        else:
            caminho.write_text(json.dumps(conteudo))
        importlib.reload(ac)
        yield
    finally:
        if original is None:
            caminho.unlink(missing_ok=True)
        else:
            caminho.write_bytes(original)
        importlib.reload(ac)


class Confluencias(unittest.TestCase):
    def test_sem_geojson_reporta_e_nao_inventa(self):
        # Sem o GeoJSON do afluente, nada é medido.
        with luiz_alves_trocado(None):
            r = ac.analisar()
        self.assertEqual(r["ilhota"]["status"], "sem_geojson")

    def test_o_luiz_alves_baixado_entra_depois_de_ilhota(self):
        # 08/10/2026: com o traçado do OSM (baixar_tracado_luiz_alves.py), a confluência é medida.
        if not (DADOS / "rios" / "luiz-alves.geojson").exists():
            self.skipTest("sem data/rios/luiz-alves.geojson")
        r = ac.analisar()["ilhota"]
        self.assertEqual(r["status"], "ok")
        self.assertIn("depois de Ilhota (", r["texto"])
        self.assertIn("e antes de Itajaí (", r["texto"])
        self.assertEqual(r["ponto"], (-26.87302, -48.78871))

    def test_o_benedito_baixado_entra_entre_indaial_e_blumenau(self):
        # 06/10/2026: com o traçado do Benedito (baixar_tracados_afluentes.py), a confluência é medida.
        if not (DADOS / "rios" / "benedito.geojson").exists():
            self.skipTest("sem data/rios/benedito.geojson")
        r = ac.analisar()["indaial"]
        self.assertEqual(r["status"], "ok")
        self.assertIn("depois de Indaial (", r["texto"])
        self.assertIn("e antes de Blumenau (", r["texto"])
        # A junção do OSM: o nó 1575465793, ponta do Rio Benedito e junção de dois ways do Açu.
        self.assertEqual(r["ponto"], (-26.89134, -49.23557))

    def test_gravar_so_mexe_na_entrada_do_afluente_medido(self):
        import shutil
        import tempfile
        from pathlib import Path
        with tempfile.TemporaryDirectory() as d:
            copia = Path(d) / "estacoes.json"
            shutil.copy(DADOS / "estacoes.json", copia)
            antes = json.loads(copia.read_text(encoding="utf-8"))
            n = ac.gravar({"indaial": {"status": "ok", "texto": "MEDIDO"},
                           "ilhota": {"status": "sem_geojson", "texto": "x"}}, copia)
            depois = json.loads(copia.read_text(encoding="utf-8"))
        self.assertEqual(n, 1)
        ar = depois["rios"]["itajai-acu"]["_topologia"]["afluentes_rios"]
        self.assertEqual(next(a for a in ar if a["entra_perto_de"] == "indaial")["ponto_exato"], "MEDIDO")
        # Tudo o mais fica igual: devolvendo o texto antigo, o arquivo volta a ser o de antes.
        ant = antes["rios"]["itajai-acu"]["_topologia"]["afluentes_rios"]
        next(a for a in ar if a["entra_perto_de"] == "indaial")["ponto_exato"] = next(
            a for a in ant if a["entra_perto_de"] == "indaial")["ponto_exato"]
        self.assertEqual(depois, antes)

    def test_afluente_colado_no_tronco_diz_entre_quais_cidades(self):
        # Afluente falso tocando o tronco perto de Gaspar (montante de Ilhota):
        # tem de sair "antes de Ilhota", pela distância REAL pela água.
        gaspar = _coord("gaspar")
        with luiz_alves_trocado({
            "type": "Feature",
            "geometry": {"type": "LineString",
                         "coordinates": [[gaspar[1], gaspar[0]], [gaspar[1] + 0.02, gaspar[0] + 0.02]]},
        }):
            r = ac.analisar()["ilhota"]
        self.assertEqual(r["status"], "ok")
        self.assertIn("antes de Ilhota", r["texto"])

    def test_ponto_longe_do_tracado_nao_toca(self):
        # Um ponto longe do traçado NÃO vira confluência inventada.
        with luiz_alves_trocado({
            "type": "Feature",
            "geometry": {"type": "LineString", "coordinates": [[-49.9, -27.6], [-49.8, -27.5]]},
        }):
            r = ac.analisar()["ilhota"]
        self.assertEqual(r["status"], "nao_toca")


if __name__ == "__main__":
    unittest.main()
