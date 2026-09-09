"""A crista da telemetria da ANA só vale depois de juntar as janelas.

Em 09/09/2026 a cheia de novembro de 2023 em Taió (83050000) cruzou a fronteira
entre duas janelas de DIAS_7: 10,32 m às 21:00 de 17/11 numa, 10,31 m às 00:00
de 18/11 na outra. Uma janela só diria "pico" com o rio na borda. E null é
leitura ausente, não zero.
"""

from __future__ import annotations

import contextlib
import io
import json
import tempfile
import unittest
from datetime import datetime, timedelta
from pathlib import Path

from analisar_telemetria_ana import (
    buracos,
    carregar,
    cota_m,
    crista,
    juntar,
    main,
    relatorio,
    serie_do_bruto,
)

T0 = datetime(2023, 11, 17, 20, 0)


def item(t: datetime, cm: str | None, codigo="83050000") -> dict:
    return {"codigoestacao": codigo, "Data_Hora_Medicao": t.strftime("%Y-%m-%d %H:%M:%S.0"),
            "Cota_Adotada": cm}


def serie(valores, inicio=T0):
    return [(inicio + i * timedelta(minutes=15), v) for i, v in enumerate(valores)]


class Unidades(unittest.TestCase):
    def test_centimetros_em_string_viram_metros(self):
        self.assertEqual(cota_m({"Cota_Adotada": "1032.00"}), 10.32)

    def test_null_nao_vira_zero(self):
        self.assertIsNone(cota_m({"Cota_Adotada": None}))
        self.assertIsNone(cota_m({}))

    def test_lixo_vira_ausente(self):
        self.assertIsNone(cota_m({"Cota_Adotada": "n/d"}))


class JuntarJanelas(unittest.TestCase):
    def test_carimbo_repetido_igual_nao_duplica(self):
        a = serie([10.30, 10.32, 10.32])
        b = serie([10.32, 10.31, 10.20], inicio=T0 + timedelta(minutes=30))
        s, conflitos = juntar([a, b])
        self.assertEqual(len(s), 5)
        self.assertEqual(conflitos, 0)

    def test_carimbo_repetido_diferente_e_contado_nao_escondido(self):
        a = serie([10.30, 10.32])
        b = serie([10.30, 9.00])
        _, conflitos = juntar([a, b])
        self.assertEqual(conflitos, 1)

    def test_null_numa_janela_e_valor_na_outra_fica_com_o_valor(self):
        a = serie([None])
        b = serie([2.99])
        s, conflitos = juntar([a, b])
        self.assertEqual(s[0][1], 2.99)
        self.assertEqual(conflitos, 0)


class Crista(unittest.TestCase):
    def test_crista_na_borda_da_janela_e_piso(self):
        """A primeira janela de Taió: máximo na última leitura."""
        c = crista(serie([6.34, 8.00, 10.32]))
        self.assertEqual(c["maximo_m"], 10.32)
        self.assertTrue(c["na_borda"])

    def test_juntando_a_janela_seguinte_a_crista_sai_da_borda(self):
        a = serie([6.34, 8.00, 10.32, 10.32])
        b = serie([10.31, 9.50, 8.00], inicio=T0 + timedelta(hours=1))
        s, _ = juntar([a, b])
        c = crista(s)
        self.assertFalse(c["na_borda"])
        self.assertEqual(c["quando"], T0 + timedelta(minutes=30))
        # platô: 10,32 / 10,32 / 10,31 dentro de ±0,02 m
        self.assertEqual(c["plato_leituras"], 3)
        self.assertEqual(c["plato_fim"], T0 + timedelta(hours=1))

    def test_serie_toda_nula_nao_tem_crista(self):
        """Ituporanga (83250000): 0 de 672 com cota, nas duas janelas."""
        self.assertIsNone(crista(serie([None, None, None])))

    def test_null_no_meio_nao_vira_zero_nem_minimo(self):
        c = crista(serie([2.00, None, 2.99, None]))
        self.assertEqual(c["maximo_m"], 2.99)
        self.assertEqual(c["n_cota"], 2)


class Buracos(unittest.TestCase):
    def test_sequencia_de_null_vira_buraco_com_duracao(self):
        s = serie([1.0] + [None] * 8 + [1.1])  # 8 × 15 min = 2 h
        b = buracos(s)
        self.assertEqual(len(b), 1)
        self.assertEqual(b[0][0], T0 + timedelta(minutes=15))
        self.assertEqual(b[0][1], T0 + timedelta(minutes=15 * 8))

    def test_buraco_curto_nao_e_listado(self):
        self.assertEqual(buracos(serie([1.0, None, None, 1.1])), [])

    def test_mudez_ate_o_fim_conta(self):
        """Barragem Taió Montante: muda de 17/11 02:15 até o fim da janela."""
        s = serie([2.9] + [None] * 5)
        b = buracos(s, minimo=timedelta(hours=1))
        self.assertEqual(len(b), 1)
        self.assertEqual(b[0][1], s[-1][0])

    def test_carimbo_faltando_tambem_e_buraco(self):
        s = [(T0, 1.0), (T0 + timedelta(hours=3), 1.2)]
        b = buracos(s)
        self.assertEqual(len(b), 1)


class LeituraDoBruto(unittest.TestCase):
    def test_agrupa_por_estacao(self):
        corpo = {"items": [item(T0, "100.00"), item(T0, "50.00", codigo="83892990")]}
        s = serie_do_bruto(corpo)
        self.assertEqual(set(s), {"83050000", "83892990"})

    def test_relatorio_de_ponta_a_ponta_e_nao_grava_nada(self):
        with tempfile.TemporaryDirectory() as d:
            p1 = Path(d) / "ana-telemetria-83050000-2023-11-17-DIAS_7.json"
            p2 = Path(d) / "ana-telemetria-83050000-2023-11-24-DIAS_7.json"
            p1.write_text(json.dumps({"items": [item(T0, "634.00"), item(T0 + timedelta(minutes=15), "1032.00")]}))
            p2.write_text(json.dumps({"items": [item(T0 + timedelta(minutes=30), "1031.00"),
                                                item(T0 + timedelta(minutes=45), "900.00")]}))
            saida = io.StringIO()
            with contextlib.redirect_stdout(saida):
                relatorio(carregar([p1, p2]), curva=False)
            texto = saida.getvalue()
            self.assertIn("CRISTA:   10.32 m", texto)
            self.assertNotIn("NA BORDA", texto)
            self.assertEqual(sorted(x.name for x in Path(d).iterdir()), [p1.name, p2.name])

    def test_arquivo_ausente_e_erro_visivel(self):
        import sys
        argv = sys.argv
        sys.argv = ["x", "/nao/existe.json"]
        try:
            with contextlib.redirect_stderr(io.StringIO()):
                self.assertEqual(main(), 2)
        finally:
            sys.argv = argv


if __name__ == "__main__":
    unittest.main()
