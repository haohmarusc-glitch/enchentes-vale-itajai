import copy
import json
import unittest
from calibrar_chegada_itajai import BASE, atraso, avaliar


def evento(i=1):
    return {
        "id": str(i), "evento": f"cheia-{i}", "natureza": "par_de_picos_observados",
        "status": "verificado", "serie_original_conferida": True,
        "efeito_mare_conferido": True, "estacao_montante": "A", "estacao_jusante": "B",
        "fonte": "Fonte de teste", "url": "https://example.org/serie",
        "pico_montante": f"2023-{i + 1:02d}-01T10:00:00-03:00",
        "pico_jusante": f"2023-{i + 1:02d}-02T02:00:00-03:00",
    }


class Calibracao(unittest.TestCase):
    def test_base_real_nao_calibra(self):
        r = avaliar(json.loads(BASE.read_text(encoding="utf8")))
        self.assertEqual(r["pares"], [])
        self.assertFalse(r["previsao_validada"])

    def test_nao_promove_relato_nem_ignora_mare(self):
        for campo, valor in [("status", "pendente"), ("natureza", "observacao_relatada_em_estudo"),
                             ("serie_original_conferida", False), ("efeito_mare_conferido", False),
                             ("pico_jusante", None), ("pico_jusante", "2023-10-02T02:00"),
                             ("pico_jusante", "2023-09-30T02:00:00-03:00")]:
            e = evento()
            e[campo] = valor
            self.assertIsNone(atraso(e), campo)

    def test_usa_instantes_com_offset(self):
        e = evento()
        e["pico_jusante"] = "2023-02-02T05:00:00+00:00"
        self.assertEqual(atraso(e), 16)

    def test_cinco_eventos_no_mesmo_par_para_estatisticas(self):
        base = {"eventos": [evento(i) for i in range(5)]}
        self.assertEqual(avaliar(base)["pares"][0]["estatisticas_descritivas"]["media_h"], 16)
        base["eventos"].pop()
        self.assertIsNone(avaliar(base)["pares"][0]["estatisticas_descritivas"])

    def test_nao_mistura_estacoes_nem_conta_mesmo_evento_duas_vezes(self):
        base = {"eventos": [evento(i) for i in range(5)]}
        base["eventos"][-1]["estacao_jusante"] = "C"
        self.assertTrue(all(p["estatisticas_descritivas"] is None for p in avaliar(base)["pares"]))
        base = {"eventos": [evento(i) for i in range(5)]}
        repetido = copy.deepcopy(base["eventos"][0])
        repetido["id"] = "outra-fonte-mesma-cheia"
        base["eventos"].append(repetido)
        self.assertEqual(avaliar(base)["pares"][0]["eventos_validos"], 4)
        self.assertIsNone(avaliar(base)["pares"][0]["estatisticas_descritivas"])

    def test_id_duplicado_nao_entra(self):
        base = {"eventos": [evento(i) for i in range(5)]}
        base["eventos"].append(evento(0))
        self.assertEqual(avaliar(base)["pares"][0]["eventos_validos"], 4)

    def test_mesmos_horarios_com_nomes_diferentes_nao_sao_nova_cheia(self):
        base = {"eventos": [evento(i) for i in range(5)]}
        base["eventos"][4]["pico_montante"] = base["eventos"][0]["pico_montante"]
        base["eventos"][4]["pico_jusante"] = base["eventos"][0]["pico_jusante"]
        r = avaliar(base)["pares"][0]
        self.assertEqual(r["eventos_validos"], 3)
        self.assertIsNone(r["estatisticas_descritivas"])


if __name__ == "__main__":
    unittest.main()
