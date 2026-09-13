import hashlib
import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


class CotasPortalItajai(unittest.TestCase):
    def test_cadastro_corresponde_aos_graficos_preservados(self):
        bruto = (ROOT / "data/brutos/itajai-nivel-rios-2026-09-13.html").read_bytes()
        evidencia = json.loads((ROOT / "data/brutos/itajai-cotas-portal-2026-09-13.json").read_text(encoding="utf-8"))
        self.assertEqual(hashlib.sha256(bruto).hexdigest(), evidencia["sha256_html"])
        cadastro = json.loads((ROOT / "data/estacoes.json").read_text(encoding="utf-8"))
        texto = bruto.decode("utf-8")
        for est in cadastro["estacoes_tempo_real"]:
            code = est.get("codigo")
            if code not in evidencia["estacoes"]:
                continue
            grafico = evidencia["estacoes"][code]
            self.assertEqual(est["cotas_m"], grafico["cotas_m"], code)
            inicio = texto.index("document.getElementById('" + grafico["canvas"] + "')")
            fim = texto.find("var canvas_", inicio)
            bloco = texto[inicio:fim if fim >= 0 else len(texto)]
            valores = [float(x) for x in re.findall(r"label:\s*'(?:Atenção|Alerta|Emergência) \(([0-9.]+)m\)'", bloco)]
            self.assertEqual(valores, list(est["cotas_m"].values()), code)
            if code in {"DC-01", "DC-07", "DC-08", "DC-09"}:
                self.assertIs(est["alerta_automatico"], False)
                self.assertIn("plano_v17", est["cotas_conferencia_2026_09_13"])


if __name__ == "__main__":
    unittest.main()
