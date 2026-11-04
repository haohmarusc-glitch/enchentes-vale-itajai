#!/usr/bin/env python3
"""Testes de `cruzar_mendeley_blumenau.py`: transcrição reproduzível e cruzamento que diz com que régua bateu.

    python3 scripts/teste_cruzar_mendeley_blumenau.py
"""

from __future__ import annotations

import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import cruzar_mendeley_blumenau as cm  # noqa: E402


def registro(data, pico, referencia="régua", publicado=None, ref_pub=None, divergencias=None, cidade="blumenau"):
    return {"cidade": cidade, "data": data, "pico_m": pico, "referencia": referencia,
            "pico_publicado_m": publicado, "referencia_publicada": ref_pub, "divergencias": divergencias}


def linha(data, cota, categoria=""):
    a, m, d = (int(x) for x in data.split("-"))
    return {"ano": a, "mes": m, "dia": d, "cota_m": cota, "categoria": categoria, "data": data}


class BateCom(unittest.TestCase):
    def test_as_tres_referencias(self):
        r = registro("2011-09-09", 13.0)
        self.assertEqual(cm.bate_com(13.0, r), "régua de hoje")
        self.assertEqual(cm.bate_com(12.8, r), "IBGE (régua + 0,20 m)")
        self.assertEqual(cm.bate_com(12.6, r), "régua antiga")
        self.assertIsNone(cm.bate_com(12.7, r))

    def test_como_publicado_e_divergencia(self):
        r = registro("1977-08-18", 9.45, publicado=9.25, ref_pub="IBGE (régua + 0,20 m)",
                     divergencias=[{"pico_m": 9.15, "fonte": "compilação"}])
        self.assertEqual(cm.bate_com(9.25, r), "IBGE (régua + 0,20 m)")   # 9,45 − 0,20
        self.assertEqual(cm.bate_com(9.15, r), "divergência já cadastrada")
        self.assertIsNone(cm.bate_com(9.0, r))

    def test_registro_fora_de_regua_nao_e_chamado_de_regua_de_hoje(self):
        """Os 67 registros não convertidos de Blumenau estão em IBGE ou sem referência: número igual não prova régua."""
        r = registro("1983-05-20", 12.52, referencia="IBGE (régua + 0,20 m)")
        self.assertEqual(cm.bate_com(12.52, r), "igual ao projeto, que está em IBGE (régua + 0,20 m)")
        self.assertEqual(cm.bate_com(12.32, r), "0.20 m abaixo de um pico em IBGE (régua + 0,20 m)")
        self.assertEqual(cm.bate_com(9.0, registro("1973-07-03", 9.0, referencia=None)),
                         "igual ao projeto, que está em referência null")


class Cruzamento(unittest.TestCase):
    def test_pares_proximos_e_exclusivos(self):
        eventos = [registro("2023-10-12", 10.76), registro("2023-10-08", 9.49), registro("1983-07-09", 15.54),
                   registro("2026-09-12", 7.87), registro("2023-10-12", 5.0, cidade="gaspar")]
        linhas = [linha("2023-10-12", 10.76), linha("2023-10-09", 10.19), linha("1900-10-02", 12.8, "Típica")]
        r = cm.cruzar(linhas, eventos)
        self.assertEqual([(x["data"], b) for x, _, b in r["pares"]], [("2023-10-12", "régua de hoje")])
        self.assertEqual([(x["data"], e["data"]) for x, e, _ in r["proximos"]], [("2023-10-09", "2023-10-08")])
        self.assertEqual([x["data"] for x in r["so_tabela"]], ["1900-10-02"])
        self.assertEqual(sorted(e["data"] for e in r["so_projeto"]), ["1983-07-09", "2026-09-12"])
        self.assertEqual(r["total_projeto"], 4, "Gaspar não entra")
        md = cm.relatorio_md(r, ["linha 3: exemplo"])
        self.assertIn("| 2023-10-12 | 10,76 | 10,76 (régua) | — | régua de hoje |", md)
        self.assertIn("**diferente**", md)
        self.assertIn("linha 3: exemplo", md)

    def test_registro_so_com_ano_nao_quebra(self):
        r = cm.cruzar([linha("1862-11-20", 9.0)], [registro("1862-11", 9.0, referencia=None), registro("1862-11-08", 9.2)])
        self.assertEqual(len(r["so_projeto"]), 2, "'1862-11' (só ano-mês) e 08/11 (12 dias de distância) ficam em 'só no projeto'")
        self.assertEqual([x["data"] for x in r["so_tabela"]], ["1862-11-20"], "e a linha da tabela fica só nela, sem casar por mês")


class Transcricao(unittest.TestCase):
    def test_completa_nos_dois_formatos(self):
        import datetime as dt
        self.assertEqual(cm._data_de_completa("21/11/1855"), (1855, 11, 21))
        self.assertEqual(cm._data_de_completa(dt.datetime(2023, 10, 12)), (2023, 10, 12))
        self.assertIsNone(cm._data_de_completa(42))

    @unittest.skipUnless(cm.XLSX.exists(), "xlsx do Mendeley ausente")
    @unittest.skipUnless(importlib.util.find_spec("openpyxl"), "sem openpyxl (a CI instala só requirements-mapas.txt)")
    def test_o_csv_commitado_e_a_transcricao_do_xlsx(self):
        """A transcrição é reproduzível: regerar do xlsx dá o CSV que está no repositório."""
        linhas, anomalias = cm.transcrever(cm.XLSX)
        self.assertEqual(len(linhas), 102)
        self.assertEqual(ler := cm.ler_csv(cm.CSV), linhas, "rode: python3 scripts/cruzar_mendeley_blumenau.py --transcrever")
        self.assertEqual(min(x["cota_m"] for x in ler), 8.06)
        # As duas anomalias conhecidas (handoff de 04/11/2026): 1855 com dia 20 × 21/11 e 1868 gravada como 2868.
        self.assertTrue(any("1855" in a for a in anomalias), anomalias)
        self.assertTrue(any("1868" in a and "2868" in a for a in anomalias), anomalias)
        with tempfile.TemporaryDirectory() as d:
            destino = Path(d) / "x.csv"
            cm.gravar_csv(linhas, destino)
            self.assertEqual(destino.read_text(encoding="utf-8"), cm.CSV.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
