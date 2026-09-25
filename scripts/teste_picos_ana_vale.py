#!/usr/bin/env python3
"""Testes dos picos da ANA no Açu, contra os zips que o Jefferson baixou em 24/09/2026."""
from __future__ import annotations

import json
import sys
import unittest
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import picos_ana_vale as pv  # noqa: E402
from hidroweb_csv import Leitura  # noqa: E402


class SerieDiaria(unittest.TestCase):
    def test_leitura_ganha_da_media_e_a_duvidosa_fica_fora(self):
        d = date(2023, 10, 9)
        leit = [
            Leitura("x", d, "07:00", 1, 1100, 1),
            Leitura("x", d, "17:00", 1, 1232, 1),
            Leitura("x", d, "media_diaria", 2, 1160, 1),
            Leitura("x", date(2023, 10, 10), "17:00", 1, 1500, 3),   # duvidosa
            Leitura("x", date(2023, 10, 10), "media_diaria", 2, 1000, 1),
        ]
        s = pv.serie_diaria(leit)
        self.assertEqual(s[d], (1232, "17:00"))
        self.assertEqual(s[date(2023, 10, 10)], (1000, "media_consistida"))

    def test_media_consistida_ganha_da_bruta(self):
        d = date(1983, 7, 12)
        s = pv.serie_diaria([Leitura("x", d, "media_diaria", 1, 1300, 1), Leitura("x", d, "media_diaria", 2, 1291, 1)])
        self.assertEqual(s[d], (1291, "media_consistida"))


class Eventos(unittest.TestCase):
    def test_corrida_vira_um_evento_so(self):
        s = {date(2011, 9, 8): (850.0, "17:00"), date(2011, 9, 10): (699.0, "07:00"),
             date(2011, 9, 20): (700.0, "07:00")}
        self.assertEqual(pv.eventos(s, 600), [(date(2011, 9, 8), 850.0, "17:00"), (date(2011, 9, 20), 700.0, "07:00")])


class ContraOBruto(unittest.TestCase):
    """Números que o doc afirma, medidos nos zips — número em doc envelhece calado."""

    @classmethod
    def setUpClass(cls):
        cls.taio = pv.serie_diaria(pv.carregar("83050000"))
        cls.timbo = pv.serie_diaria(pv.carregar("83677000"))

    def test_taio_1983_bate_com_a_maxima_mensal_da_ana(self):
        # Campo Maxima/DiaMaxima de jul/1983, consistido: 1291 no dia 12 (ANA-maximas-mensais-anos-alvo.md).
        self.assertEqual(self.taio[date(1983, 7, 12)], (1291, "media_consistida"))

    def test_taio_2013_a_cheia_foi_em_setembro(self):
        junho = max(v for d, (v, _o) in self.taio.items() if d.year == 2013 and d.month == 6)
        self.assertEqual(junho, 680)
        self.assertEqual(self.taio[date(2013, 9, 23)], (970, "17:00"))

    def test_timbo_sem_leitura_no_dia_da_crista_de_2011(self):
        self.assertEqual(self.timbo[date(2011, 9, 9)][1], "media_consistida")

    def test_zips_vazios_nao_quebram(self):
        self.assertEqual(pv.carregar("83145140"), [])


class Derivado(unittest.TestCase):
    def test_o_json_gravado_e_o_que_o_script_produz(self):
        gravado = json.loads(pv.SAIDA.read_text(encoding="utf-8"))
        self.assertEqual(gravado, json.loads(json.dumps(pv.tudo(), ensure_ascii=False)))

    def test_no_cadastro_estao_so_os_escolhidos(self):
        """Decisões do Jefferson. 24/09/2026: os 5 maiores de Ituporanga, Ibirama, Apiúna e Ilhota
        (83860000). 25/09/2026: em Taió e Timbó, só as cheias da ANA que a série municipal não tem —
        as puladas estão nomeadas aqui. Ilhota-Jusante e Trombudo Central continuam fora."""
        ench = json.loads((pv.RAIZ / "data" / "enchentes.json").read_text(encoding="utf-8"))["eventos"]
        no_cadastro = sorted((e["cidade"], e["data"], e["pico_m"]) for e in ench if "picos_ana_vale" in e["fonte"])
        der = {e["codigo"]: e for e in json.loads(pv.SAIDA.read_text(encoding="utf-8"))["estacoes"]}
        pulados = {("taio", "1983-07-12"), ("taio", "2023-10-09"), ("taio", "2015-10-23"), ("taio", "2011-09-10"),
                   ("taio", "2023-11-04"), ("taio", "2023-11-17"), ("taio", "2013-09-23"), ("taio", "2022-05-05"),
                   ("timbo", "2014-06-09"), ("timbo", "2011-09-08"), ("timbo", "2023-11-03"), ("timbo", "2023-10-12"),
                   ("timbo", "1992-05-29"),  # saiu quando o municipal de 1992 (10,42 m, JMV) entrou
                   ("timbo", "2021-01-21")}  # idem, municipal 7,62 m às 20h (OCP News)
        esperado = [(der[c]["cidade"], ev["data"], round(ev["cm"] / 100, 2))
                    for c in ("83250000", "83440000", "83500000", "83860000") for ev in der[c]["eventos"][:5]]
        esperado += [(der[c]["cidade"], ev["data"], round(ev["cm"] / 100, 2))
                     for c in ("83050000", "83680000", "83677000") for ev in der[c]["eventos"]
                     if (der[c]["cidade"], ev["data"]) not in pulados]
        self.assertEqual(no_cadastro, sorted(esperado))
        self.assertTrue(all(e["confianca"] == "baixa" and "pendencia" in e and "referencia" not in e
                            for e in ench if "picos_ana_vale" in e["fonte"]))

if __name__ == "__main__":
    unittest.main()
