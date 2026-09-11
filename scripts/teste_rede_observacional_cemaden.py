"""Contrato do cadastro e sua separação das medições ao vivo."""
import json
import unittest
import tempfile
from pathlib import Path
from unittest.mock import patch
from xml.sax.saxutils import escape
from zipfile import ZipFile

from coleta_chuva_cemaden import REDE_OBSERVACIONAL, carregar_rede_observacional, converter
from importar_rede_cemaden import importar


class Importacao(unittest.TestCase):
    def arquivo(self, path, rows):
        header = ["Codigo PCD", "Tipo rede", "UF", "Município", "lat", "long", "status"]
        cells = []
        for i, row in enumerate([header] + rows, 1):
            values = ''.join(f'<c r="{col}{i}" t="inlineStr"><is><t>{escape(str(v))}</t></is></c>'
                             for col, v in zip("ABCDEFG", row))
            cells.append(f'<row r="{i}">{values}</row>')
        with ZipFile(path, "w") as z:
            z.writestr("xl/workbook.xml", '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><sheets><sheet name="Rede Cemaden SC" r:id="rId1"/></sheets></workbook>')
            z.writestr("xl/_rels/workbook.xml.rels", '<Relationships><Relationship Id="rId1" Target="worksheets/sheet1.xml"/></Relationships>')
            z.writestr("xl/worksheets/sheet1.xml", '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><sheetData>' + ''.join(cells) + '</sheetData></worksheet>')

    def test_importa_texto_coordenadas_e_ignora_vazias(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "rede.xlsx"
            self.arquivo(path, [["421320321H", "Hidrológica", "SC", "Pomerode", -26.7259, -49.172, "Operacional"], []])
            result = importar(path)
            self.assertEqual(len(result["estacoes"]), 1)
            self.assertEqual(result["estacoes"][0]["lat"], -26.7259)
            self.assertEqual(result["estacoes"][0]["linha_origem"], 2)
            self.assertIsNone(result["_meta"]["data_referencia_status"])
            self.assertEqual(len(result["_meta"]["sha256"]), 64)

    def test_recusa_duplicatas_campos_ausentes_e_coordenadas_invalidas(self):
        row = ["421320321H", "Hidrológica", "SC", "Pomerode", -26.7259, -49.172, "Operacional"]
        for rows in [[row, row], [row[:-1]], [row[:4] + ["nan"] + row[5:]]]:
            with self.subTest(rows=rows), tempfile.TemporaryDirectory() as tmp:
                path = Path(tmp) / "rede.xlsx"
                self.arquivo(path, rows)
                with self.assertRaises(ValueError):
                    importar(path)


class RedeObservacional(unittest.TestCase):
    def setUp(self):
        self.cadastro = carregar_rede_observacional()

    def reg(self, codigo="420590202A", municipio="GASPAR-SC", icon="flag_verde", lbl=0):
        return dict(estacao_cod=codigo, estacao_munic=municipio, icon=icon, lbl=lbl)

    def test_codigos_unicos_e_campos_completos(self):
        rows = json.loads(REDE_OBSERVACIONAL.read_text(encoding="utf-8"))["estacoes"]
        self.assertEqual(len(rows), len(self.cadastro))
        self.assertEqual(len(rows), 415)
        for r in rows:
            self.assertTrue(all(v is not None for v in r.values()))
            self.assertIn(r["status_cadastro"], {"Operacional", "Inativa"})

    def test_zero_real_com_coordenadas(self):
        leituras, _, _ = converter([self.reg()], cadastro=self.cadastro)
        self.assertEqual(leituras[0]["mm"]["h24"], 0)
        self.assertEqual(leituras[0]["cadastro_observacional"]["lat"], -27)

    def test_cadastro_operacional_nao_cria_leitura(self):
        self.assertEqual(converter([], cadastro=self.cadastro)[0], [])
        for reg in [self.reg(lbl=""), self.reg(icon="flag_cinza")]:
            self.assertEqual(converter([reg], cadastro=self.cadastro)[0], [])

    def test_status_antigo_nao_bloqueia_feed_e_expoe_divergencia(self):
        leituras, _, _ = converter([self.reg(codigo="420590205A", lbl=12)], cadastro=self.cadastro)
        self.assertEqual(leituras[0]["mm"]["h24"], 12)
        self.assertTrue(leituras[0]["cadastro_observacional"]["divergencia_status"])

    def test_codigo_desconhecido_preserva_coleta(self):
        leituras, _, _ = converter([self.reg(codigo="nova-A")], cadastro=self.cadastro)
        self.assertEqual(len(leituras), 1)
        self.assertNotIn("cadastro_observacional", leituras[0])

    def test_municipio_divergente_nao_recebe_coordenadas(self):
        leituras, _, _ = converter([self.reg(municipio="BRUSQUE-SC")], cadastro=self.cadastro)
        self.assertNotIn("cadastro_observacional", leituras[0])

    def test_hidrologica_nao_vira_chuva_mesmo_com_numero(self):
        for cadastro in [self.cadastro, {}]:
            leituras, recusadas, _ = converter(
                [self.reg(codigo="420290901H", municipio="BRUSQUE-SC", lbl=2.5)], cadastro=cadastro)
            self.assertEqual(leituras, [])
            self.assertEqual(len(recusadas), 1)

    def test_arquivo_ausente_nao_interrompe_coleta(self):
        with patch("pathlib.Path.read_text", side_effect=FileNotFoundError):
            self.assertEqual(len(converter([self.reg()])[0]), 1)


if __name__ == "__main__":
    unittest.main()
