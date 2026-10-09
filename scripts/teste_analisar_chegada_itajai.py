#!/usr/bin/env python3
"""Testes da análise Blumenau × maré × Itajaí.

O que trava: cada régua sai com o SEU atraso e o SEU fator de maré (a DC-01 não
reage como a DC-11, e a DC-10 nem sente a maré); tirar a maré não inventa uma
crista; e a publicação "Blumenau" da página de Itajaí, 3 h atrasada, é corrigida
antes de entrar na conta.

    python3 scripts/teste_analisar_chegada_itajai.py
"""

import json
import math
import tempfile
import unittest
from datetime import datetime, timedelta
from pathlib import Path

from analisar_chegada_itajai import (
    ajuste_mare,
    analisar,
    crista,
    curva_mare,
    eventos,
    plato,
    sem_mare,
)

T0 = datetime(2026, 9, 1)
N = 24 * 20


def mare_sintetica(n=N):
    # Semidiurna (12,4 h) com modulação lenta, como a de Itajaí.
    return [0.8 + 0.5 * math.cos(2 * math.pi * i / 12.42) * (1 + 0.3 * math.cos(2 * math.pi * i / 354))
            for i in range(n)]


class AjusteDeMare(unittest.TestCase):
    def test_cada_regua_sai_com_o_seu_atraso_e_o_seu_fator(self):
        mare = mare_sintetica()
        dc01 = [1.0 + 0.9 * m for m in mare]  # sente a maré inteira, sem atraso
        dc11 = [2.0 + 0.7 * mare[i - 1] if i else None for i in range(N)]  # 1 h depois, mais fraca
        a01, a11 = ajuste_mare(dc01, mare), ajuste_mare(dc11, mare)
        self.assertEqual(a01["atraso_h"], 0)
        self.assertAlmostEqual(a01["fator"], 0.9, places=2)
        self.assertEqual(a11["atraso_h"], 1)
        self.assertAlmostEqual(a11["fator"], 0.7, places=2)

    def test_regua_que_nao_sente_a_mare_sai_com_fator_perto_de_zero(self):
        mare = mare_sintetica()
        dc10 = [3.0 + 0.4 * math.sin(2 * math.pi * i / 97) for i in range(N)]  # só rio, ondas lentas
        self.assertLess(abs(ajuste_mare(dc10, mare)["fator"]), 0.05)

    def test_tirar_a_mare_devolve_o_rio(self):
        mare = mare_sintetica()
        rio = [2.0 + (1.5 if 200 <= i <= 230 else 0.0) for i in range(N)]
        regua = [r + 0.8 * (m - sum(mare) / N) for r, m in zip(rio, mare)]
        limpo = sem_mare(regua, mare, ajuste_mare(regua, mare))
        miolo = [abs(a - b) for a, b in zip(limpo[20:-20], rio[20:-20]) if a is not None and abs(a - b) < 1]
        self.assertLess(max(miolo[:150]), 0.05)


class Eventos(unittest.TestCase):
    def test_pico_e_plato(self):
        blu = [2.0] * 60 + [3.0, 4.0, 5.0, 6.0, 6.97, 7.0, 6.98, 6.96, 6.5, 6.0] + [5.0] * 60
        (i,) = eventos(blu, [T0 + timedelta(hours=k) for k in range(len(blu))])
        self.assertEqual(blu[i], 7.0)
        self.assertEqual(plato(blu, i), (64, 67))

    def test_subida_pequena_nao_e_evento(self):
        blu = [2.0] * 60 + [2.5, 2.8, 2.5] + [2.0] * 60
        self.assertEqual(eventos(blu, [T0] * len(blu)), [])

    def test_crista_na_ponta_da_janela_nao_vale_como_crista(self):
        self.assertEqual(crista([1, 2, 3, 4, 5], 0, 4), (4, True, False))
        self.assertEqual(crista([1, 3, 2, 1, 1], 0, 4), (1, False, False))
        self.assertIsNone(crista([1, None, None, None, 2], 0, 4))

    def test_crista_nunca_cai_em_hora_sem_leitura_bruta(self):
        # 12/09/2026, DC-11: a média móvel deu o máximo às 07h, hora sem leitura.
        suave = [4.0, 4.2, 4.3, 4.35, 4.2, 4.1, 4.0, 3.9, 3.8, 3.7]
        bruta = [4.0, 4.2, 4.3, None, 4.2, 4.1, 4.0, 3.9, 3.8, 3.7]
        k, _, lacuna = crista(suave, 0, 9, bruta)
        self.assertEqual(k, 2)
        self.assertFalse(lacuna, "uma hora só faltando não é lacuna")

    def test_lacuna_de_duas_horas_deixa_o_horario_indeterminado(self):
        suave = [4.0, 4.2, 4.3, 4.2, 4.1, 4.1, 4.0, 3.9, 3.8, 3.7]
        bruta = [4.0, 4.2, 4.3, 4.2, None, None, 4.0, 3.9, 3.8, 3.7]
        self.assertTrue(crista(suave, 0, 9, bruta)[2])


class Leitura(unittest.TestCase):
    def test_curva_de_mare_passa_pelos_extremos(self):
        f = curva_mare([(T0, 1.4), (T0 + timedelta(hours=6), 0.2)])
        self.assertAlmostEqual(f(T0), 1.4)
        self.assertAlmostEqual(f(T0 + timedelta(hours=3)), 0.8)
        self.assertIsNone(f(T0 + timedelta(hours=7)))

    def test_publicacao_do_portal_de_itajai_e_atrasada_em_3_h(self):
        with tempfile.TemporaryDirectory() as d:
            pasta = Path(d)
            mare = [(T0 + timedelta(hours=6.21 * k), 1.3 if k % 2 == 0 else 0.3) for k in range(80)]
            (pasta / "mare.json").write_text(json.dumps({
                "preamares": [{"quando": t.isoformat(), "altura_m": h} for t, h in mare if h > 1],
                "baixamares": [{"quando": t.isoformat(), "altura_m": h} for t, h in mare if h < 1],
            }))
            linhas = []
            for k in range(24 * 15):
                t = T0 + timedelta(hours=k)
                nivel = 7.0 - abs(k - 200) * 0.1 if abs(k - 200) < 40 else 3.0
                # Só a publicação do portal, carimbada 3 h antes da hora certa.
                linhas.append({"estacao": "Blumenau", "cidade": "blumenau", "rio": "itajai-acu",
                               "medido_em": (t - timedelta(hours=3)).isoformat(), "nivel_m": round(nivel, 2)})
                linhas.append({"estacao": "DC-11 Rio Itajaí-Açú", "cidade": "itajai", "rio": "itajai-acu",
                               "medido_em": t.isoformat(), "nivel_m": 2.0})
            (pasta / "2026-09.ndjson").write_text("\n".join(json.dumps(x) for x in linhas))
            r = analisar(pasta, pasta / "mare.json")
            self.assertEqual([e["pico"] for e in r["eventos"]], [T0 + timedelta(hours=200)])


class TesteRecorteVersionado(unittest.TestCase):
    """O recorte em data/brutos/serie-2026-itajai/ reproduz as tabelas do documento.

    Auditoria do PR #449 (03/10/2026, item A2): as tabelas só rodavam com um
    pacote que não estava no repositório. Este teste trava os números.
    """

    @classmethod
    def setUpClass(cls):
        from comum import DADOS
        cls.r = analisar(DADOS / "brutos" / "serie-2026-itajai", DADOS / "mare-itajai-chm.json")

    def test_fatores_de_mare(self):
        reg = self.r["reguas"]
        self.assertEqual((reg["DC-01"]["atraso_h"], round(reg["DC-01"]["fator"], 2)), (0, 0.90))
        self.assertEqual((reg["DC-11"]["atraso_h"], round(reg["DC-11"]["fator"], 2)), (1, 0.70))
        self.assertEqual((reg["ilhota"]["atraso_h"], round(reg["ilhota"]["fator"], 2)), (1, 0.57))
        self.assertLess(reg["DC-02"]["fator"], 0.1)

    def test_12_09_dc11_tem_lacuna_e_ilhota_mais_3_5_h(self):
        (e,) = [e for e in self.r["eventos"] if e["pico"] == datetime(2026, 9, 12, 5)]
        self.assertEqual(e["nivel_m"], 7.86)
        self.assertTrue(e["cristas"]["DC-11"]["lacuna"])
        self.assertEqual(e["cristas"]["DC-11"]["horas"], 0.5)
        self.assertFalse(e["cristas"]["ilhota"]["lacuna"])
        self.assertEqual(e["cristas"]["ilhota"]["horas"], 3.5)


if __name__ == "__main__":
    unittest.main()
