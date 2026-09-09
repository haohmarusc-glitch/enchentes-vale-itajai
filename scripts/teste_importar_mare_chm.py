#!/usr/bin/env python3
"""Testes do importador da tábua CHM.

O que não pode falhar: o ano vem do cabeçalho (sem ele, nada); as colunas
intercaladas (01, 17, 02, 18) acabam em ordem cronológica; altura negativa é
lida; um estofo (dois mínimos seguidos) é descartado, não adivinhado; e o
cruzamento com a tábua anterior mede minutos, não escolhe fonte.

    python3 scripts/teste_importar_mare_chm.py
"""

import importlib.util
import unittest
from datetime import datetime

from importar_mare_chm import BRUTO, cruzar, extrair_texto, parse
from importar_mare_univali import classificar_extremos

TEXTO = """166
PORTO DE ITAJAÍ (ESTADO DE SANTA CATARINA) - 2026
CHM 78 Componentes Nível Médio 0.6 m Carta 1841
Janeiro
HORA  ALT(m) HORA  ALT(m)
01
QUI
0044    1.08
0808    0.35
1227    0.83
2002    0.10
17
SÁB
0127    1.06
0906    0.46
02
SEX
0129    1.13
0902    0.36
2134   -0.02
06
TER
1604    1.02
2159    0.25
2346    0.19
"""


class Parse(unittest.TestCase):
    def test_ordem_cronologica_apesar_das_colunas_intercaladas(self):
        pontos, relato = parse(TEXTO)
        self.assertEqual(relato["ano"], 2026)
        datas = [p[0] for p in pontos]
        self.assertEqual(datas, sorted(datas))
        self.assertEqual(datas[0], datetime(2026, 1, 1, 0, 44))
        self.assertEqual(datas[-1], datetime(2026, 1, 17, 9, 6))
        self.assertEqual(relato["dias"], 4)

    def test_altura_negativa_e_lida(self):
        pontos, _ = parse(TEXTO)
        self.assertIn((datetime(2026, 1, 2, 21, 34), -0.02), pontos)

    def test_sem_ano_no_cabecalho_aborta(self):
        with self.assertRaises(ValueError):
            parse(TEXTO.replace("- 2026", ""))

    def test_estofo_e_descartado_nao_adivinhado(self):
        pontos, _ = parse(TEXTO)
        pre, bai = classificar_extremos(pontos)
        instantes = {q for q, _ in pre} | {q for q, _ in bai}
        # 06/01: 1604 1.02 (pico), 2159 0.25 (nem pico nem vale), 2346 0.19 (vale)
        self.assertNotIn(datetime(2026, 1, 6, 21, 59), instantes)
        self.assertIn(datetime(2026, 1, 6, 23, 46), {q for q, _ in bai})


class Cruzamento(unittest.TestCase):
    def test_mede_minutos_entre_fontes(self):
        novos = [{"quando": "2026-09-01T04:30"}, {"quando": "2026-09-01T16:50"}, {"quando": "2026-12-01T00:00"}]
        # A tábua antiga vai até 02/09: o ponto de dezembro fica fora e não pareia.
        antigos = [{"quando": "2026-09-01T04:28"}, {"quando": "2026-09-01T16:45"}, {"quando": "2026-09-02T05:00"}]
        c = cruzar(novos, antigos)
        self.assertEqual(c["pareados"], 2)
        self.assertEqual(c["mediana_min"], 3.5)
        self.assertEqual(c["maximo_min"], 5.0)
        self.assertIsNone(cruzar(novos, []))


# O CI instala só beautifulsoup4, requests e ruff; o pypdf é dependência do
# importador, não do projeto. Sem ele, o único teste que abre o PDF é pulado
# com o motivo à vista — os testes com a fixture de texto continuam rodando.
@unittest.skipUnless(importlib.util.find_spec("pypdf"), "pypdf não instalado (pip install pypdf)")
class BrutoReal(unittest.TestCase):
    def test_o_pdf_de_2026_cobre_o_ano_inteiro(self):
        if not BRUTO.exists():
            self.skipTest("bruto ausente")
        pontos, relato = parse(extrair_texto(BRUTO))
        self.assertEqual((relato["ano"], relato["meses"], relato["dias"]), (2026, 12, 365))
        self.assertEqual(pontos[0][0].date().isoformat(), "2026-01-01")
        self.assertEqual(pontos[-1][0].date().isoformat(), "2026-12-31")
        pre, bai = classificar_extremos(pontos)
        self.assertGreater(len(pre), 600)
        self.assertGreater(len(bai), 600)


if __name__ == "__main__":
    unittest.main()
