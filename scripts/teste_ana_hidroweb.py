"""A série da ANA tem uma armadilha de 4 metros, e ela tem nome.

Medido em 08/09/2026, estação 83800002 (Blumenau), setembro de 2011: a série
CONSISTIDA de médias diárias mostra o rio descendo suavemente a partir do dia 8
(885 cm) enquanto a leitura das 07h do dia 9 marca 1248 cm. A cheia que a base
registra em 12,80 m simplesmente não está na série consistida.

Quem importasse a consistida como histórico gravaria o pico de set/2011 em
8,85 m — quatro metros a menos, na direção de fazer alguém se sentir mais
seguro do que estava, e com o rótulo de maior qualidade em cima.

Os dados destes testes são os valores REAIS transcritos daquela execução.
"""

from __future__ import annotations

import unittest

from ana_hidroweb import cota_em_metros, pico_do_mes


def _linha(hora: str, mediadiaria: str, consistencia: str, dias: dict[int, str]) -> dict:
    linha = {
        "Data_Hora_Dado": f"2011-09-01 {hora}.0",
        "Mediadiaria": mediadiaria,
        "nivelconsistencia": consistencia,
    }
    for d in range(1, 32):
        linha[f"Cota_{d:02d}"] = dias.get(d)
    return linha


# Valores reais de setembro de 2011 na 83800002, dias 5 a 12.
MEDIA_CONSISTIDA = _linha("00:00:00", "1", "2",
                          {5: "310.0", 6: "392.0", 7: "538.0", 8: "885.0",
                           9: "847.0", 10: "809.0", 11: "771.0", 12: "733.0"})
LEITURA_07H = _linha("07:00:00", "0", "1",
                     {5: "320.0", 6: "353.0", 7: "487.0", 8: "730.0", 9: "1248.0"})
LEITURA_17H = _linha("17:00:00", "0", "1",
                     {5: "300.0", 6: "432.0", 7: "588.0", 8: "1040.0"})


class ACotaVemEmCentimetros(unittest.TestCase):
    def test_converte(self):
        self.assertEqual(cota_em_metros("1519.0"), 15.19)
        self.assertEqual(cota_em_metros("885.0"), 8.85)

    def test_ausente_e_none_nao_zero(self):
        """Zero seria um nível de rio. Ausente não é nível nenhum."""
        self.assertIsNone(cota_em_metros(None))
        self.assertIsNone(cota_em_metros(""))


class OPicoNaoSaiDaMediaDiaria(unittest.TestCase):
    def test_o_caso_real_de_setembro_de_2011(self):
        r = pico_do_mes({"items": [MEDIA_CONSISTIDA, LEITURA_07H, LEITURA_17H]})
        self.assertEqual(r["cota_m"], 12.48, "pegou a média diária em vez da leitura")
        self.assertEqual(r["dia"], 9)
        self.assertIn("07:00:00", r["de"])

    def test_a_consistida_sozinha_e_RECUSADA(self):
        """
        É a linha que qualquer um escolheria: nivelconsistencia 2. Devolver
        8,85 m daqui seria o erro de 4 m com cara de dado de qualidade.
        """
        r = pico_do_mes({"items": [MEDIA_CONSISTIDA]})
        self.assertIsNone(r["cota_m"])
        self.assertIn("média diária", r["recusa"])
        self.assertIn("4 m", r["recusa"])

    def test_1983_e_1984_caem_na_recusa(self):
        """
        Os dois eventos que a REGRA_REFERENCIA_BLUMENAU nomeia só têm média
        diária na API. Se algum dia este teste passar a achar leitura, a regra
        ganhou o teste que falta — e este texto tem de mudar junto.
        """
        so_media = _linha("00:00:00", "1", "2", {9: "1519.0"})
        r = pico_do_mes({"items": [so_media]})
        self.assertIsNone(r["cota_m"], "apareceu leitura para 1983: reveja a regra")

    def test_resposta_vazia_nao_explode(self):
        for vazia in ({"items": []}, {}, {"items": None}):
            r = pico_do_mes(vazia)
            self.assertIsNone(r["cota_m"])
            self.assertTrue(r["recusa"])

    def test_a_maior_leitura_atravessa_as_duas_horas(self):
        """O pico pode estar na leitura das 17h de um dia e nas 07h de outro."""
        r = pico_do_mes({"items": [LEITURA_17H]})
        self.assertEqual(r["cota_m"], 10.40)
        self.assertEqual(r["dia"], 8)
        self.assertIn("17:00:00", r["de"])

    def test_leitura_sem_valor_nenhum_recusa(self):
        r = pico_do_mes({"items": [_linha("07:00:00", "0", "1", {})]})
        self.assertIsNone(r["cota_m"])
        self.assertIn("sem valor", r["recusa"])


if __name__ == "__main__":
    unittest.main()
