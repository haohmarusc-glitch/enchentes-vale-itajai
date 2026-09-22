#!/usr/bin/env python3
"""Testes do leitor e dos acumulados da chuva horária do INMET."""
from __future__ import annotations

import gzip
import io
import json
import sys
import tempfile
import unittest
from datetime import date, datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import inmet_chuva as ic  # noqa: E402

FONTE = (Path(__file__).resolve().parent / "inmet_chuva.py").read_text(encoding="utf-8")


def horaria(linhas: list[tuple[str, str, str]]) -> Path:
    """Escreve um CSV horário mínimo (gz) no formato do bruto e devolve o caminho."""
    buf = io.StringIO()
    buf.write("codigo,ts_utc,prec_mm,suspeito\n")
    for cod, ts, mm in linhas:
        buf.write(f"{cod},{ts},{mm},0\n")
    tmp = Path(tempfile.mkdtemp()) / "h.csv.gz"
    with gzip.open(tmp, "wt", encoding="utf-8") as f:
        f.write(buf.getvalue())
    return tmp


class Numero(unittest.TestCase):
    def test_branco_null_e_9999_sao_sem_dado_nunca_chuva(self):
        """INMET (LAI C8): falha vem como 9999, Null ou branco. Nada disso é 9 999 mm."""
        for t in ("", " ", "Null", "null", "9999", "-9999", "9999.0"):
            self.assertIsNone(ic.numero(t), t)

    def test_virgula_decimal_e_aceita(self):
        self.assertEqual(ic.numero("1,8"), 1.8)

    def test_negativo_aborta(self):
        with self.assertRaises(ValueError):
            ic.numero("-0.2")


class Acumulado(unittest.TestCase):
    def setUp(self):
        # 22/11/2008 local (UTC-3) = 03:00Z de 22/11 até 02:59Z de 23/11
        self.serie = {
            datetime(2008, 11, 22, 3): 1.0,    # 00h local de 22/11
            datetime(2008, 11, 22, 4): 2.0,
            datetime(2008, 11, 23, 2): 4.0,    # 23h local de 22/11
            datetime(2008, 11, 23, 3): 100.0,  # 00h local de 23/11 — fora da janela
            datetime(2008, 11, 22, 5): None,
        }

    def test_janela_termina_exclusiva_na_hora_local(self):
        mm, cob = ic.acumulado(self.serie, datetime(2008, 11, 23, 0), 24)
        self.assertEqual(mm, 7.0)
        self.assertEqual(cob, round(3 / 24, 2))

    def test_sem_nenhuma_hora_valida_da_none_e_cobertura_zero(self):
        self.assertEqual(ic.acumulado(self.serie, datetime(2000, 1, 2, 0), 24), (None, 0.0))

    def test_hora_ausente_e_hora_nula_contam_igual_na_cobertura(self):
        serie = {datetime(2020, 1, 1, 3): 5.0, datetime(2020, 1, 1, 4): None}
        mm, cob = ic.acumulado(serie, datetime(2020, 1, 2, 0), 24)
        self.assertEqual((mm, cob), (5.0, round(1 / 24, 2)))


class Diaria(unittest.TestCase):
    def test_dia_local_e_utc_menos_tres_fixo(self):
        """02:59Z ainda é o dia anterior em Brasília; 03:00Z já é o dia."""
        serie = {datetime(2008, 11, 23, 2): 4.0, datetime(2008, 11, 23, 3): 6.0,
                 datetime(2008, 11, 23, 4): None}
        d = ic.diaria(serie)
        self.assertEqual(d[date(2008, 11, 22)], (4.0, 1))
        self.assertEqual(d[date(2008, 11, 23)], (6.0, 1))

    def test_sem_horario_de_verao_no_codigo(self):
        """Os brutos ignoram o horário de verão que SC teve até 2019; o script diz isso e não o aplica."""
        self.assertIn("horário de verão", FONTE)
        self.assertNotIn("zoneinfo", FONTE)
        self.assertNotIn("pytz", FONTE)


class Leitura(unittest.TestCase):
    def test_le_gz_e_converte_vazio_em_none(self):
        p = horaria([("A817", "2008-11-22T03:00Z", "1.0"), ("A817", "2008-11-22T04:00Z", "")])
        s = ic.ler_horaria(p)
        self.assertEqual(s["A817"][datetime(2008, 11, 22, 3)], 1.0)
        self.assertIsNone(s["A817"][datetime(2008, 11, 22, 4)])


class Suspeitos(unittest.TestCase):
    """Pluviômetro parado publica zero, não falha. O bruto marca `suspeito` nos zeros de
    sequências que se estendem por ≥ 20 dias; a diária e o JSON os descartam."""

    def _serie(self, horas_zero: int, quebra_em: int | None = None, furo_em: int | None = None) -> dict:
        s = {}
        for i in range(horas_zero):
            s[datetime(2014, 5, 1) + timedelta(hours=i)] = 0.0
        if quebra_em is not None:
            s[datetime(2014, 5, 1) + timedelta(hours=quebra_em)] = 0.2
        if furo_em is not None:
            s[datetime(2014, 5, 1) + timedelta(hours=furo_em)] = None
        return s

    def test_vinte_dias_de_zero_sao_marcados(self):
        s = self._serie(480)
        self.assertEqual(ic.zeros_travados(s), set(s))

    def test_menos_de_vinte_dias_nao(self):
        self.assertEqual(ic.zeros_travados(self._serie(479)), set())

    def test_uma_chuva_no_meio_quebra_a_sequencia(self):
        self.assertEqual(ic.zeros_travados(self._serie(600, quebra_em=300)), set())

    def test_hora_sem_dado_no_meio_nao_quebra(self):
        s = self._serie(600, furo_em=300)
        marcas = ic.zeros_travados(s)
        self.assertEqual(len(marcas), 599)
        self.assertNotIn(datetime(2014, 5, 1) + timedelta(hours=300), marcas)

    def test_ler_horaria_honra_a_marca_por_padrao(self):
        buf = "codigo,ts_utc,prec_mm,suspeito\nA817,2014-05-01T03:00Z,0.0,1\nA817,2014-05-01T04:00Z,0.0,0\n"
        tmp = Path(tempfile.mkdtemp()) / "h.csv.gz"
        with gzip.open(tmp, "wt", encoding="utf-8") as f:
            f.write(buf)
        com = ic.ler_horaria(tmp)["A817"]
        sem = ic.ler_horaria(tmp, honrar_suspeito=False)["A817"]
        self.assertIsNone(com[datetime(2014, 5, 1, 3)])
        self.assertEqual(com[datetime(2014, 5, 1, 4)], 0.0)
        self.assertEqual(sem[datetime(2014, 5, 1, 3)], 0.0)


class Conferencia(unittest.TestCase):
    def test_conferir_eventos_reproduz_e_acusa_diferenca(self):
        series = {"A817": {datetime(2008, 11, 22, 3): 1.0, datetime(2008, 11, 22, 4): 2.0}}
        ev = {"eventos": {"x-2008-11": {
            "janela_termina": "2008-11-23T00:00-03:00",
            "estacoes": {"A817": {"24h": {"mm": 3.0}, "72h": {"mm": 3.0},
                                  "7d": {"mm": 9.9}, "30d": {"mm": None}}}}}}
        tmp = Path(tempfile.mkdtemp()) / "ev.json"
        tmp.write_text(json.dumps(ev), encoding="utf-8")
        r = ic.conferir_eventos(series, tmp)
        self.assertEqual((r["iguais"], r["diferentes"]), (2, 2))  # 7d errado; 30d null mas há dado
        self.assertEqual(r["exemplos"][0][:3], ("x-2008-11", "A817", "7d"))


class Estacoes(unittest.TestCase):
    def test_sao_as_quatro_da_lai_c8_e_indaial_esta_em_pane(self):
        self.assertEqual(sorted(ic.ESTACOES), ["A817", "A861", "A863", "A868"])
        self.assertEqual(ic.ESTACOES["A817"]["situacao_2026_09"], "Pane")


class BrutoReal(unittest.TestCase):
    """Roda contra o bruto versionado. Trava os números que a documentação cita."""

    @classmethod
    def setUpClass(cls):
        if not ic.HORARIA.exists():
            raise unittest.SkipTest("bruto do INMET ausente")
        cls.series = ic.ler_horaria()

    def test_indaial_nov_2008(self):
        s = self.series["A817"]
        self.assertEqual(ic.acumulado(s, datetime(2008, 11, 25), 96), (246.6, 1.0))   # 21–24/11
        self.assertEqual(ic.acumulado(s, datetime(2008, 11, 24), 24), (145.2, 1.0))   # 23/11
        self.assertEqual(ic.acumulado(s, datetime(2008, 12, 1), 720), (567.4, 1.0))   # mês

    def test_ituporanga_nov_2008_ficou_seca(self):
        s = self.series["A863"]
        self.assertEqual(ic.acumulado(s, datetime(2008, 11, 25), 96), (46.4, 1.0))

    def test_rio_do_campo_nao_tem_nov_2008(self):
        mm, cob = ic.acumulado(self.series["A861"], datetime(2008, 12, 1), 720)
        self.assertLess(mm or 0, 1.0)

    def test_indaial_calou_em_maio_de_2025(self):
        self.assertEqual(ic.ultimo_valido(self.series["A817"]), datetime(2025, 5, 31, 23))

    def test_o_json_de_eventos_se_reproduz_da_horaria(self):
        r = ic.conferir_eventos(self.series)
        self.assertEqual(r["diferentes"], 0, r["exemplos"])
        self.assertGreater(r["iguais"], 1000)

    def test_a_diaria_se_reproduz_da_horaria(self):
        r = ic.conferir_diaria(self.series)
        self.assertEqual(r["diferentes"], 0, r["exemplos"])
        self.assertGreater(r["iguais"], 26000)

    def test_a_marca_suspeito_e_a_regra_dos_vinte_dias(self):
        """Só zeros, e exatamente os das sequências de ≥ 20 dias."""
        crua = ic.ler_horaria(honrar_suspeito=False)
        marcas = ic.ler_suspeitos()
        for cod, serie in crua.items():
            self.assertTrue(all(serie[t] == 0.0 for t in marcas.get(cod, ())), cod)
            self.assertEqual(ic.zeros_travados(serie), marcas.get(cod, set()), cod)


if __name__ == "__main__":
    unittest.main()
