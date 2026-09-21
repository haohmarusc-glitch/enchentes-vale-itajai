#!/usr/bin/env python3
"""Testes do conversor e da reconciliação do Histórico de Cheias de Rio do Sul."""
from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import riodosul_historico as rs  # noqa: E402

RAIZ = Path(__file__).resolve().parent.parent
FONTE = (Path(__file__).resolve().parent / "riodosul_historico.py").read_text(encoding="utf-8")
CAPTURA = RAIZ / "data" / "brutos" / "riodosul-historico-cheias-2026-09-21.html"


def pagina(linhas: list[tuple[str, ...]]) -> str:
    """HTML mínimo com as armadilhas da página real: cabeçalho com acento e
    parênteses, células com espaço e &nbsp;, 'm' colado no número."""
    corpo = "".join("<tr>" + "".join(f"<td class='x'> {c} </td>" for c in l) + "</tr>" for l in linhas)
    return ("<html><body><p>Normal 4,34 m</p><table><thead><tr><th>Ano</th><th>Data do Pico</th>"
            "<th>Nível (m)</th><th>Volume (mm)</th><th>Dias de Chuva</th></tr></thead>"
            f"<tbody>{corpo}</tbody></table><table><tr><td>outra tabela</td></tr></table>"
            "</body></html>")


LINHAS = [
    ("2024", "12 de julho", "7,49m", "51,4", "2"),
    ("2024", "Julho", "7,39m", "70,8", "2"),          # só mês, no mesmo mês do de cima
    ("2023", "17 de novembro", "13,04m", "185", "2"),
    ("2023", "Novembro", "8,33m", "83,2", "2"),        # segundo pico do mês
    ("1983", "Julho", "13,58m", "606,7", "20"),
    ("1966", "Fevereiro", "10,00m", "-", "-"),         # '-' é ausência
    ("1911", "Outubro", "12,20m", "-", "-"),
]


class NaoEscreveNoProjeto(unittest.TestCase):
    """Registro entra em enchentes.json só por decisão explícita; o código nem
    tem como gravar lá."""

    def test_nao_grava_nos_jsons_do_projeto(self):
        self.assertNotIn("grava_json", FONTE)
        for ln in FONTE.splitlines():
            if "write_text" in ln and not ln.strip().startswith("#"):
                self.assertIn("destino", ln, f"escrita fora de data/brutos: {ln.strip()}")
        self.assertIn('DIR_BRUTOS / (args.arquivo.stem + ".json")', FONTE)


class Leitura(unittest.TestCase):
    def test_le_a_primeira_tabela_e_ignora_a_segunda(self):
        cab, linhas = rs.ler_tabela(pagina(LINHAS))
        self.assertEqual(len(linhas), len(LINHAS))
        self.assertEqual(linhas[0], ["2024", "12 de julho", "7,49m", "51,4", "2"])

    def test_colunas_diferentes_falham_alto(self):
        html = pagina(LINHAS).replace("Dias de Chuva", "Horas de Chuva")
        with self.assertRaises(ValueError):
            rs.ler_tabela(html)

    def test_pagina_sem_tabela_falha_alto(self):
        with self.assertRaises(ValueError):
            rs.ler_tabela("<html><body>nada</body></html>")


class Conversao(unittest.TestCase):
    def setUp(self):
        _, linhas = rs.ler_tabela(pagina(LINHAS))
        self.regs = rs.converter(linhas)

    def test_dia_e_mes_saem_com_a_precisao_da_fonte(self):
        r = self.regs[0]
        self.assertEqual((r["data"], r["precisao"]), ("2024-07-12", "dia"))
        r = self.regs[1]
        self.assertEqual((r["data"], r["precisao"]), ("2024-07", "mes"))
        self.assertEqual(r["data_na_fonte"], "Julho")

    def test_nivel_com_m_colado_e_virgula(self):
        self.assertEqual(self.regs[0]["nivel_m"], 7.49)
        self.assertEqual(self.regs[5]["nivel_m"], 10.0)

    def test_traco_e_ausencia_e_nao_zero(self):
        self.assertIsNone(self.regs[5]["volume_mm"])
        self.assertIsNone(self.regs[5]["dias_chuva"])
        self.assertEqual(self.regs[0]["dias_chuva"], 2)

    def test_data_ilegivel_e_marcada_e_nao_inventada(self):
        _, linhas = rs.ler_tabela(pagina([("2024", "Setembro ou outubro", "7,00m", "-", "-")]))
        r = rs.converter(linhas)[0]
        self.assertIsNone(r["data"])
        self.assertEqual(r["precisao"], "invalida")
        self.assertIn("data ilegível", rs.validar([r])[0])

    def test_numero_lixo_vira_erro_na_linha(self):
        _, linhas = rs.ler_tabela(pagina([("2024", "Julho", "sete metros", "-", "-")]))
        r = rs.converter(linhas)[0]
        self.assertIn("erro", r)


class Validacao(unittest.TestCase):
    def test_duplicata_exata_e_avisada_e_segundo_pico_nao(self):
        _, linhas = rs.ler_tabela(pagina(LINHAS + [LINHAS[3]]))
        avisos = rs.validar(rs.converter(linhas))
        self.assertTrue(any("duplicata exata" in a for a in avisos), avisos)
        # 13,04 e 8,33 no mesmo mês NÃO são duplicata: são dois picos
        self.assertEqual(sum("duplicata" in a for a in avisos), 1)

    def test_empate_de_nivel_no_mesmo_ano_e_avisado(self):
        _, linhas = rs.ler_tabela(pagina([("1957", "Agosto", "9,65m", "-", "-"),
                                          ("1957", "Julho", "9,65m", "-", "-")]))
        avisos = rs.validar(rs.converter(linhas))
        self.assertTrue(any("empate" in a for a in avisos), avisos)

    def test_nivel_e_ano_fora_do_plausivel(self):
        _, linhas = rs.ler_tabela(pagina([("1800", "Julho", "40,00m", "-", "-")]))
        avisos = rs.validar(rs.converter(linhas))
        self.assertTrue(any("fora de" in a and " m" in a for a in avisos), avisos)
        self.assertTrue(any("ano 1800" in a for a in avisos), avisos)


class Reconciliacao(unittest.TestCase):
    CADASTRADOS = [
        {"data": "2023-11-18", "pico_m": 13.04, "data_na_fonte": "2023-11-17"},
        {"data": "1983-07", "pico_m": 13.58},
        {"data": "1911-10", "pico_m": 12.2},
        {"data": "1954-10", "pico_m": 10.7},          # não está na tabela sintética
    ]

    def setUp(self):
        _, linhas = rs.ler_tabela(pagina(LINHAS))
        self.rec = rs.reconciliar(rs.converter(linhas), self.CADASTRADOS)

    def test_resumo(self):
        self.assertEqual(self.rec["resumo"], {
            "linhas_validas": 7, "ja_cadastradas": 3, "candidatas_a_inclusao": 3,
            "segundo_pico_no_mesmo_mes": 1, "com_dia_diferente_ou_novo": 0,
            "cadastrados_sem_linha_na_tabela": 1})

    def test_o_dia_da_fonte_casa_pelo_data_na_fonte(self):
        """Nov/2023: a tabela diz 17, o cadastro 18 com data_na_fonte 17. É a
        mesma linha, sem observação de divergência."""
        nov = next(r for r in self.rec["ja_cadastradas"] if r["data"] == "2023-11-17")
        self.assertNotIn("nota", nov)

    def test_segundo_pico_do_mes_nao_vira_alteracao(self):
        seg = self.rec["segundo_pico_no_mesmo_mes"]
        self.assertEqual([(r["data"], r["nivel_m"]) for r in seg], [("2023-11", 8.33)])

    def test_cadastrado_sem_linha_aparece(self):
        self.assertEqual(self.rec["cadastrados_sem_linha_na_tabela"][0]["data"], "1954-10")

    def test_dia_novo_e_anotado(self):
        rec = rs.reconciliar(rs.converter(rs.ler_tabela(pagina(
            [("2023", "13 de outubro", "11,86m", "393,2", "9")]))[1]),
            [{"data": "2023-10", "pico_m": 11.86}])
        self.assertIn("a tabela dá o dia", rec["ja_cadastradas"][0]["nota"])

    def test_cadastrados_nao_sao_alterados(self):
        antes = json.dumps(self.CADASTRADOS)
        rs.reconciliar(rs.converter(rs.ler_tabela(pagina(LINHAS))[1]), self.CADASTRADOS)
        self.assertEqual(json.dumps(self.CADASTRADOS), antes)


class PlanoDeInclusao(unittest.TestCase):
    """A decisão de 21/09/2026 em código: o maior de cada mês entra, o resto
    fica preservado e pendente, com motivo."""

    LINHAS = [
        ("2014", "Junho", "9,42m", "152,6", "6"),
        ("2014", "Junho", "7,76m", "147,5", "4"),      # colisão: fica pendente
        ("2024", "18 de maio", "8,97m", "175,4", "3"),
        ("2024", "Maio", "7,34m", "46,8", "2"),        # colisão: fica pendente
        ("1931", "Maio", "10,18m", "-", "-"),
        ("2023", "Novembro", "8,33m", "83,2", "2"),    # segundo pico: fica pendente
        ("2023", "17 de novembro", "13,04m", "185", "2"),  # já cadastrado
    ]
    CADASTRADOS = [{"data": "2023-11-18", "pico_m": 13.04, "data_na_fonte": "2023-11-17"}]

    def setUp(self):
        _, linhas = rs.ler_tabela(pagina(self.LINHAS))
        self.plano = rs.plano_de_inclusao(rs.reconciliar(rs.converter(linhas), self.CADASTRADOS))

    def test_entra_o_maior_de_cada_mes_e_o_menor_fica_pendente(self):
        self.assertEqual([(e["data"], e["pico_m"]) for e in self.plano["entram"]],
                         [("1931-05", 10.18), ("2014-06", 9.42), ("2024-05-18", 8.97)])
        pend = {(p["data"], p["nivel_m"]): p["motivo"] for p in self.plano["pendentes"]}
        self.assertIn("colisão de mês", pend[("2014-06", 7.76)])
        self.assertIn("colisão de mês", pend[("2024-05", 7.34)])
        self.assertIn("segundo pico", pend[("2023-11", 8.33)])
        self.assertEqual(self.plano["resumo"], {"entram": 3, "pendentes": 3})

    def test_o_registro_novo_tem_a_forma_dos_treze(self):
        e = next(e for e in self.plano["entram"] if e["data"] == "2014-06")
        self.assertEqual((e["rio"], e["cidade"], e["confianca"], e["referencia"]),
                         ("itajai-acu", "rio-do-sul", "media", None))
        self.assertEqual(e["fonte"], rs.FONTE)
        self.assertEqual((e["chuva_mm"], e["dias_de_chuva"]), (152.6, 6))
        self.assertIn("linha 2", e["nota"])
        self.assertIn("7.76 m", e["nota"])          # a colisão está dita na nota
        self.assertNotIn("divergencias", e)          # crista diferente não é divergência

    def test_sem_chuva_nao_inventa_zero(self):
        e = next(e for e in self.plano["entram"] if e["data"] == "1931-05")
        self.assertNotIn("chuva_mm", e)
        self.assertNotIn("dias_de_chuva", e)

    def test_nenhuma_data_e_inventada(self):
        for e in self.plano["entram"]:
            self.assertIn(len(e["data"]), (7, 10))
        for p in self.plano["pendentes"]:
            self.assertEqual(p["precisao"], "mes")


@unittest.skipUnless(CAPTURA.exists(), "captura de 21/09/2026 ausente")
class CapturaReal(unittest.TestCase):
    """Contra o HTML que o Jefferson salvou em 21/09/2026."""

    @classmethod
    def setUpClass(cls):
        _, linhas = rs.ler_tabela(CAPTURA.read_text(encoding="utf-8", errors="replace"))
        cls.regs = rs.converter(linhas)
        cls.avisos = rs.validar(cls.regs)

    def test_sao_77_linhas_todas_validas_e_sem_aviso(self):
        self.assertEqual(len(self.regs), 77)
        self.assertFalse([r for r in self.regs if "erro" in r])
        self.assertEqual(self.avisos, [])

    def test_a_maior_e_julho_de_1983(self):
        maior = max(self.regs, key=lambda r: r["nivel_m"])
        self.assertEqual((maior["data"], maior["nivel_m"]), ("1983-07", 13.58))

    def test_so_quatro_linhas_tem_dia(self):
        com_dia = sorted(r["data"] for r in self.regs if r["precisao"] == "dia")
        self.assertEqual(com_dia, ["2023-10-13", "2023-11-17", "2024-05-18", "2024-07-12"])

    def test_os_treze_cadastrados_estao_na_tabela(self):
        from comum import le_json
        cad = [e for e in le_json("enchentes.json")["eventos"] if e["cidade"] == "rio-do-sul"]
        rec = rs.reconciliar(self.regs, cad)
        self.assertEqual(rec["resumo"]["ja_cadastradas"], len(cad))
        self.assertEqual(rec["resumo"]["cadastrados_sem_linha_na_tabela"], 0)
        self.assertEqual(rec["resumo"]["candidatas_a_inclusao"]
                         + rec["resumo"]["segundo_pico_no_mesmo_mes"], 77 - len(cad))

    def test_o_plano_da_decisao_e_52_entram_e_12_pendentes(self):
        """13 cadastrados + 57 candidatos + 7 segundos picos = 77. Dos 57, cinco
        colisões de mês: 52 entram, 5 + 7 = 12 ficam pendentes. Depois da
        importação os 52 já estão cadastrados e o plano fica vazio de
        entradas — o teste aceita as duas situações e trava a soma."""
        from comum import le_json
        cad = [e for e in le_json("enchentes.json")["eventos"] if e["cidade"] == "rio-do-sul"]
        plano = rs.plano_de_inclusao(rs.reconciliar(self.regs, cad))
        self.assertIn(len(cad), (13, 65))
        self.assertEqual(plano["resumo"]["entram"], 65 - len(cad))
        self.assertEqual(len(cad) + plano["resumo"]["entram"] + plano["resumo"]["pendentes"], 77)
        self.assertEqual(plano["resumo"]["pendentes"], 12)


if __name__ == "__main__":
    unittest.main()
