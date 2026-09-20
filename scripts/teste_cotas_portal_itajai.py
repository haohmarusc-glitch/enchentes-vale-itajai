import hashlib
import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


class CotasPortalItajai(unittest.TestCase):
    def test_graficos_preservados_sao_evidencia_nao_substituicao_do_plano(self):
        bruto = (ROOT / "data/brutos/itajai-nivel-rios-2026-09-13.html").read_bytes()
        evidencia = json.loads((ROOT / "data/brutos/itajai-cotas-portal-2026-09-13.json").read_text(encoding="utf-8"))
        self.assertEqual(hashlib.sha256(bruto.replace(b'\r\n', b'\n')).hexdigest(), evidencia["sha256_html"])
        cadastro = json.loads((ROOT / "data/estacoes.json").read_text(encoding="utf-8"))
        texto = bruto.decode("utf-8")
        for est in cadastro["estacoes_tempo_real"]:
            code = est.get("codigo")
            if code not in evidencia["estacoes"]:
                continue
            grafico = evidencia["estacoes"][code]
            inicio = texto.index("document.getElementById('" + grafico["canvas"] + "')")
            fim = texto.find("var canvas_", inicio)
            bloco = texto[inicio:fim if fim >= 0 else len(texto)]
            valores = [float(x) for x in re.findall(r"label:\s*'(?:Atenção|Alerta|Emergência) \(([0-9.]+)m\)'", bloco)]
            self.assertEqual(valores, list(grafico["cotas_m"].values()), code)
            if code in {"DC-01", "DC-07", "DC-08", "DC-09"}:
                conferencia = est["cotas_conferencia_2026_09_13"]
                self.assertEqual(conferencia["portal"], grafico["cotas_m"], code)
                self.assertEqual(est["cotas_m"], conferencia["plano_v17"], code)
                self.assertNotEqual(est["cotas_m"], grafico["cotas_m"], code)
                self.assertEqual(est["fonte_cotas"], conferencia["fonte_plano"], code)
                self.assertIn("Plano de Contingência", est["fonte_cotas"])
                self.assertNotIn("monitoramento/nivel-rios", est["fonte_cotas"])
                self.assertIs(est["alerta_automatico"], False)
            else:
                self.assertEqual(est["cotas_m"], grafico["cotas_m"], code)


if __name__ == "__main__":
    unittest.main()
