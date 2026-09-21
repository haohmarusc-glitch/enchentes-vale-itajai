#!/usr/bin/env python3
"""Testes do importador de Rio do Sul: idempotente, sem sobrescrever, sem apagar."""
from __future__ import annotations

import copy
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import importar_riodosul_historico as imp  # noqa: E402

FONTE = (Path(__file__).resolve().parent / "importar_riodosul_historico.py").read_text(encoding="utf-8")


def reg(data, pico, cidade="rio-do-sul", rio="itajai-acu", **extra):
    return {"rio": rio, "cidade": cidade, "data": data, "pico_m": pico, "confianca": "media",
            "fonte": "x", "referencia": None, **extra}


BASE = {"_meta": {"campos": {"pico_m": "..."}},
        "eventos": [reg("1852-10-29", 16.3, cidade="blumenau"),
                    reg("1911-10", 12.2), reg("1983-07", 13.58), reg("2023-11-18", 13.04),
                    reg("2023-10-05", 6.85, cidade="brusque", rio="itajai-mirim")]}


class SoEscreveEnchentes(unittest.TestCase):
    def test_grava_so_enchentes_json_e_so_com_escrever(self):
        self.assertEqual(FONTE.count("grava_json("), 1)
        self.assertIn('grava_json("enchentes.json", base)', FONTE)
        self.assertIn("if not args.escrever:", FONTE)
        self.assertNotIn("estacoes.json", FONTE)
        self.assertNotIn("transito.json", FONTE)


class Aplicar(unittest.TestCase):
    def test_insere_no_bloco_de_rio_do_sul_em_ordem_sem_apagar(self):
        base = copy.deepcopy(BASE)
        r = imp.aplicar(base, [reg("2014-06", 9.42, chuva_mm=152.6, dias_de_chuva=6),
                               reg("1931-05", 10.18)])
        self.assertEqual(len(r["novos"]), 2)
        cidades = [e["cidade"] for e in base["eventos"]]
        self.assertEqual(cidades, ["blumenau"] + ["rio-do-sul"] * 5 + ["brusque"])
        datas = [e["data"] for e in base["eventos"] if e["cidade"] == "rio-do-sul"]
        self.assertEqual(datas, sorted(datas))
        self.assertEqual(len(base["eventos"]), len(BASE["eventos"]) + 2)
        self.assertIn("chuva_mm", base["_meta"]["campos"])
        self.assertIn("dias_de_chuva", base["_meta"]["campos"])

    def test_idempotente(self):
        base = copy.deepcopy(BASE)
        entram = [reg("2014-06", 9.42), reg("1931-05", 10.18)]
        imp.aplicar(base, entram)
        depois = copy.deepcopy(base)
        r = imp.aplicar(base, entram)
        self.assertEqual((len(r["novos"]), len(r["pulados"])), (0, 2))
        self.assertEqual(base, depois)

    def test_conflito_aborta_sem_tocar_em_nada(self):
        base = copy.deepcopy(BASE)
        r = imp.aplicar(base, [reg("1931-05", 10.18), reg("1983-07", 13.6)])  # 13,58 cadastrado
        self.assertEqual(len(r["conflitos"]), 1)
        self.assertEqual(r["novos"], [])
        self.assertEqual(base, BASE, "conflito não pode gravar nem o que não conflita")

    def test_o_cadastrado_nunca_e_sobrescrito(self):
        base = copy.deepcopy(BASE)
        imp.aplicar(base, [reg("2023-11-18", 13.04, nota="outra nota")])
        original = next(e for e in base["eventos"] if e["data"] == "2023-11-18")
        self.assertNotIn("nota", original)


if __name__ == "__main__":
    unittest.main()
