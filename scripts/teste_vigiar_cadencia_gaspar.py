#!/usr/bin/env python3
"""Testes do medidor de cadência de Gaspar.

O que não pode falhar: "mudou" tem de sair da MUDANÇA em "Última Medição", não
da consulta; parser que não acha o campo registra erro em vez de gravar vazio
em silêncio; e os intervalos são entre leituras novas.

    python3 scripts/teste_vigiar_cadencia_gaspar.py
"""

import tempfile
import unittest
from datetime import datetime
from pathlib import Path

from vigiar_cadencia_gaspar import extrair, intervalos_entre_mudancas, registrar, ultima_linha, veredito

HTML = """<html><body><h1>Rio Itajaí Açu Gaspar</h1>
<div><span>NÍVEL DO RIO</span> <strong>1,12 m</strong></div>
<div>FONTE: DC. GASPAR</div>
<div>Última Medição: <b>08/09/2026 08:03</b></div>
<script>var x = "Última Medição 01/01/2000 00:00";</script></body></html>"""


class Parser(unittest.TestCase):
    def test_acha_nivel_e_ultima_medicao_e_ignora_script(self):
        d = extrair(HTML)
        self.assertEqual(d["ultima_medicao"], "08/09/2026 08:03")
        self.assertEqual(d["nivel_m"], 1.12)
        self.assertIsNone(d["erro"])

    def test_pagina_sem_os_campos_registra_erro(self):
        d = extrair("<html><body>manutenção</body></html>")
        self.assertIn("parser não achou", d["erro"])


class Registro(unittest.TestCase):
    def test_mudou_vem_da_ultima_medicao_nao_da_consulta(self):
        with tempfile.TemporaryDirectory() as tmp:
            csv_ = Path(tmp) / "c.csv"
            a = registrar({"ultima_medicao": "08/09/2026 08:03", "nivel_m": 1.12}, datetime(2026, 9, 8, 21, 0), csv_)
            b = registrar({"ultima_medicao": "08/09/2026 08:03", "nivel_m": 1.12}, datetime(2026, 9, 8, 22, 0), csv_)
            c = registrar({"ultima_medicao": "09/09/2026 08:01", "nivel_m": 1.10}, datetime(2026, 9, 9, 9, 0), csv_)
            self.assertEqual((a["mudou"], b["mudou"], c["mudou"]), ("sim", "nao", "sim"))
            self.assertEqual(ultima_linha(csv_)["ultima_medicao"], "09/09/2026 08:01")
            linhas = [a, b, c]
            self.assertEqual(intervalos_entre_mudancas(linhas), [23.97])

    def test_erro_de_rede_vira_linha_com_erro(self):
        with tempfile.TemporaryDirectory() as tmp:
            l = registrar({"erro": "rede: timeout"}, datetime(2026, 9, 9, 9, 0), Path(tmp) / "c.csv")
            self.assertEqual(l["mudou"], "")
            self.assertIn("timeout", l["erro"])


PAGINA_REAL = """<html><body><div class="card">
<h5>Rio Itajaí Açu Gaspar</h5>
<p>Estação em situação de NORMALIDADE - Última Medição 08/09/2026 08:03</p>
<p>NIVEL DO RIO: 1,12 M</p>
<p>FONTE: DC. GASPAR</p>
<p>NORMALIDADE (Nível menor que 5,00 m); ATENÇÃO (Nível maior que 5,00 m ou Chuva atual maior que 6,00 mm);
EMERGÊNCIA (Nível maior que 7,00 m)</p>
</div></body></html>"""


class PaginaReal(unittest.TestCase):
    """O texto que o Jefferson leu na página em 08/09/2026, palavra por palavra."""

    def test_parser_le_o_formato_real_inclusive_a_situacao(self):
        d = extrair(PAGINA_REAL)
        self.assertEqual(d["ultima_medicao"], "08/09/2026 08:03")
        self.assertEqual(d["nivel_m"], 1.12)
        self.assertEqual(d["situacao"], "NORMALIDADE")
        self.assertIsNone(d["erro"])

    def test_nivel_com_ponto_nao_vira_112(self):
        d = extrair(PAGINA_REAL.replace("1,12 M", "1.12 M"))
        self.assertEqual(d["nivel_m"], 1.12)


class Veredito(unittest.TestCase):
    def _linhas(self, horas):
        base = datetime(2026, 9, 8, 8, 3)
        out, ant = [], None
        for h in horas:
            m = (base + __import__("datetime").timedelta(hours=h)).strftime("%d/%m/%Y %H:%M")
            out.append({"consultado_em": "", "ultima_medicao": m, "mudou": "sim" if m != ant else "nao"})
            ant = m
        return out

    def test_poucas_leituras_nao_da_veredito(self):
        self.assertIn("ainda não dá", veredito(self._linhas([0, 0, 0])))

    def test_uma_por_turno_nunca_pinta(self):
        v = veredito(self._linhas([0, 12, 24, 36]))
        self.assertIn("nunca pintaria", v)
        self.assertIn("08:03", v)
        self.assertIn("20:03", v)

    def test_leituras_dentro_de_180_min_valem_reapontar(self):
        v = veredito(self._linhas([0, 1, 2, 3, 4]))
        self.assertIn("reapontar", v)
        self.assertIn("mínimo 60 min", v)


if __name__ == "__main__":
    unittest.main()
