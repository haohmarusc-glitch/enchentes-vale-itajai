#!/usr/bin/env python3
"""Testes do leitor do formato largo do HidroWeb e da conferência do Mirim."""
from __future__ import annotations

import sys
import tempfile
import unittest
from datetime import date, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import hidroweb_csv as hw  # noqa: E402

CABECALHO = (
    "Agência Nacional de Águas - ANA\nSistema de Informações Hidrológicas - Versão WEB\n\n"
    "NivelConsistencia: 1 = Bruto, 2 = Consistido\n\nRestrições da consulta:\nCódigo da Estação:83900000\n\n\n"
)


def cotas_largo(linhas: list[tuple[int, str, int, dict[int, int], dict[int, int] | None]]) -> Path:
    """(nivel, hora ou '' para média, mediadiaria, {dia: cm}, {dia: status})."""
    cols = ["EstacaoCodigo", "NivelConsistencia", "Data", "hora", "MediaDiaria", "TipoMedicaoCotas", "Maxima",
            "Minima", "Media", "DiaMaxima", "DiaMinima", "MaximaStatus", "MinimaStatus", "MediaStatus",
            "MediaAnual", "MediaAnualStatus"] + [f"Cota{d:02d}" for d in range(1, 32)] \
        + [f"Cota{d:02d}Status" for d in range(1, 32)]
    corpo = []
    for nivel, hora, media, vals, sts in linhas:
        p = ["83900000", str(nivel), "01/09/2011", hora, str(media), "1"] + [""] * 10
        p += [str(vals.get(d, "")) for d in range(1, 32)]
        p += [str((sts or {}).get(d, 1 if d in vals else 0)) for d in range(1, 32)]
        corpo.append(";".join(p))
    tmp = Path(tempfile.mkdtemp()) / "83900000_Cotas.csv"
    tmp.write_text(CABECALHO + ";".join(cols) + "\n" + "\n".join(corpo) + "\n", encoding="latin-1")
    return tmp


class Numero(unittest.TestCase):
    def test_aspas_e_virgula(self):
        self.assertEqual(hw.numero('"165,2"'), 165.2)
        self.assertIsNone(hw.numero(""))
        self.assertEqual(hw.numero("890"), 890.0)


class LeituraDoLargo(unittest.TestCase):
    def setUp(self):
        self.p = cotas_largo([
            (1, "07:00", 0, {8: 570, 9: 690}, None),
            (1, "17:00", 0, {8: 630, 9: 890}, None),
            (1, "", 1, {8: 600, 9: 790}, None),
            (2, "", 1, {8: 600, 9: 790}, {9: 2}),
        ])
        self.l = hw.ler_cotas(self.p)

    def test_uma_leitura_por_dia_por_linha_com_dias_do_mes(self):
        self.assertEqual(len(self.l), 4 * 30)  # setembro tem 30 dias; a coluna 31 fica de fora

    def test_hora_e_nivel_e_status(self):
        idx = hw.indice(self.l)
        self.assertEqual(idx[("83900000", date(2011, 9, 9), "17:00", 1)].valor, 890.0)
        self.assertEqual(idx[("83900000", date(2011, 9, 9), "media_diaria", 2)].status, 2)
        self.assertIsNone(idx[("83900000", date(2011, 9, 10), "07:00", 1)].valor)
        self.assertEqual(idx[("83900000", date(2011, 9, 10), "07:00", 1)].status, 0)

    def test_le_de_dentro_do_zip(self):
        import zipfile
        z = self.p.parent / "83900000_csv.zip"
        with zipfile.ZipFile(z, "w") as f:
            f.write(self.p, self.p.name)
        self.assertEqual(len(hw.ler_cotas(z)), 120)
        self.assertEqual(hw.ler_chuvas(z), [])  # zip sem _Chuvas.csv


class Picos(unittest.TestCase):
    def test_corridas_separadas_por_mais_de_cinco_dias(self):
        s = {datetime(2011, 9, 8, 17): 630, datetime(2011, 9, 9, 17): 890, datetime(2011, 9, 10, 7): 480,
             datetime(2011, 9, 16, 7): 460, datetime(2011, 9, 20, 17): 300}
        self.assertEqual(hw.picos(s, 450), [(datetime(2011, 9, 9, 17), 890), (datetime(2011, 9, 16, 7), 460)])

    def test_empate_fica_com_a_mais_cedo(self):
        s = {datetime(2011, 9, 9, 7): 600, datetime(2011, 9, 9, 17): 600}
        self.assertEqual(hw.picos(s, 450), [(datetime(2011, 9, 9, 7), 600)])

    def test_pico_a_montante_nas_72h_anteriores(self):
        s = {datetime(2011, 9, 6, 7): 500, datetime(2011, 9, 9, 7): 453, datetime(2011, 9, 9, 17): 300}
        self.assertEqual(hw.pico_a_montante(s, datetime(2011, 9, 9, 17)), (datetime(2011, 9, 9, 7), 453, 10))

    def test_antecedencia_zero_quando_o_pico_e_a_mesma_leitura(self):
        s = {datetime(2011, 9, 9, 17): 453}
        self.assertEqual(hw.pico_a_montante(s, datetime(2011, 9, 9, 17))[2], 0)


class Implausiveis(unittest.TestCase):
    def test_dedo_do_digitador_e_pego_e_crista_real_nao(self):
        l = [hw.Leitura("83892990", date(2023, 4, 15), "07:00", 1, 1140.0, 1),
             hw.Leitura("83892990", date(2023, 4, 15), "media_diaria", 2, 143.0, 1),
             hw.Leitura("83900000", date(2011, 9, 9), "17:00", 1, 890.0, 1),
             hw.Leitura("83900000", date(2011, 9, 9), "media_diaria", 2, 790.0, 1)]
        self.assertEqual(hw.implausiveis(l), [("83892990", "2023-04-15", "07:00", 1140.0, 143.0)])


class SerieInstantanea(unittest.TestCase):
    def test_exclui_duvidosa_e_nivel_dois(self):
        l = [hw.Leitura("83900000", date(2013, 1, 11), "07:00", 1, 102.0, 3),
             hw.Leitura("83900000", date(2013, 1, 12), "07:00", 1, 110.0, 1),
             hw.Leitura("83900000", date(2013, 1, 12), "media_diaria", 2, 110.0, 1)]
        self.assertEqual(hw.serie_instantanea(l, "83900000"), {datetime(2013, 1, 12, 7): 110.0})


class BrutoReal(unittest.TestCase):
    """Contra os zips versionados. Trava os números da documentação."""

    @classmethod
    def setUpClass(cls):
        if not hw.DIR.exists():
            raise unittest.SkipTest("brutos do HidroWeb ausentes")
        cls.cotas, cls.chuvas = hw.carregar_tudo()

    def test_derivado_de_cotas_se_reproduz(self):
        r = hw.conferir_cotas(self.cotas)
        self.assertEqual(r["diferentes"], 0, r["exemplos"])
        self.assertGreater(r["iguais"], 160000)

    def test_derivado_de_chuva_se_reproduz(self):
        r = hw.conferir_chuvas(self.chuvas)
        self.assertEqual(r["diferentes"], 0, r["exemplos"])
        self.assertGreater(r["iguais"], 60000)

    def test_json_de_picos_32_de_34(self):
        """Dois eventos (jan/1997 e out/2015) são sub-picos que a corrida de 5 dias funde ao maior."""
        r = hw.conferir_picos(self.cotas)
        self.assertEqual(r["iguais"], 32, r["exemplos"])
        self.assertEqual([d[1] for d in r["exemplos"]], ["1997-01-27T07:00", "2015-10-16T17:00"])
        self.assertEqual(r["so_no_reproduzido"], [])

    def test_os_erros_de_digitacao_do_salseiro(self):
        """03/10/2020 e 15/04/2023 conferidos na série de 15 min da DC de Brusque: 1,49 m nos dois.
        25/03/2024 (167165) não tem média consistida para comparar e fica fora desta regra."""
        achados = hw.implausiveis(self.cotas)
        self.assertEqual([(a[1], a[3]) for a in achados if a[0] == "83892990"],
                         [("2009-12-24", 3145.0), ("2020-10-03", 434.0), ("2023-04-15", 1140.0)])

    def test_os_recordes_de_brusque_sao_erros_de_digitacao(self):
        """1444 (1944), 1347 (1958), 1204 (1978), 1047 (1941): média consistida do dia entre 1,2 e 1,5 m."""
        achados = {(a[1], a[3]) for a in hw.implausiveis(self.cotas) if a[0] == "83900000"}
        for par in (("1944-02-04", 1444.0), ("1958-04-11", 1347.0), ("1978-02-20", 1204.0), ("1941-11-19", 1047.0)):
            self.assertIn(par, achados)
        self.assertNotIn(("2011-09-09", 890.0), achados)
        self.assertNotIn(("1984-08-06", 758.0), achados)

    def test_nenhum_pico_do_json_usa_leitura_implausivel(self):
        import json
        from datetime import datetime as dtm
        flag = {(a[0], a[1], a[2]) for a in hw.implausiveis(self.cotas)}
        for e in json.loads(hw.PICOS_JSON.read_text())["eventos"]:
            tb = dtm.fromisoformat(e["pico_brusque"]).replace(tzinfo=None)
            self.assertNotIn(("83900000", tb.date().isoformat(), f"{tb.hour:02d}:00"), flag)
            for k, cod in (("salseiro", "83892990"), ("botuvera_mont", "83892998")):
                t = dtm.fromisoformat(e[k]["pico"]).replace(tzinfo=None)
                self.assertNotIn((cod, t.date().isoformat(), f"{t.hour:02d}:00"), flag)

    def test_brusque_ana_bate_com_a_regua_municipal_em_2019_e_2021(self):
        b = hw.serie_instantanea(self.cotas, "83900000")
        self.assertEqual(b[datetime(2019, 5, 31, 17)], 590.0)   # cadastro: 5,90 m
        self.assertEqual(b[datetime(2021, 10, 12, 17)], 568.0)  # cadastro: 5,68 m

    def test_brusque_ana_termina_em_marco_de_2022(self):
        ultimo = max(x.data for x in self.cotas if x.codigo == "83900000" and x.valor is not None)
        self.assertEqual(ultimo, date(2022, 3, 31))

    def test_nov_2008_no_mirim(self):
        def soma(cod, d0, d1):
            idx, m2 = hw.indice(self.chuvas), hw.meses_consistidos(self.chuvas)
            tot = 0.0
            d = d0
            while d <= d1:
                x = hw._derivado_esperado(idx, m2, cod, d, "diaria")
                tot += x.valor or 0.0
                d = date.fromordinal(d.toordinal() + 1)
            return round(tot, 1)
        self.assertEqual(soma("2749045", date(2008, 11, 21), date(2008, 11, 24)), 334.1)
        self.assertEqual(soma("2748000", date(2008, 11, 21), date(2008, 11, 24)), 287.0)
        self.assertEqual(soma("2749033", date(2008, 11, 21), date(2008, 11, 24)), 53.8)


if __name__ == "__main__":
    unittest.main()
