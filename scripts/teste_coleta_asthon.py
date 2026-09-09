#!/usr/bin/env python3
"""Testes da coleta Asthon (Vidal Ramos).

O que não pode falhar: entrar barragem ou altitude como se fosse a régua da
cidade, ou o carimbo UTC virar hora local sem converter — três horas de idade
erradas numa cheia. A lista fechada de estação e a conversão de fuso estão
travadas aqui.

    python3 scripts/teste_coleta_asthon.py
"""

import unittest

from coleta_asthon import de_utc_para_brasilia, parse

VIDAL = {
    "station_id": "bd65df3e-a5e3-4760-a879-56df0fb90787",
    "name": "Vidal Ramos",
    "level_m": 2.93,
    "last_reading_at": "2026-08-31T12:21:50.688Z",
}
TITO_BUSS = {
    "station_id": "f6360951-219f-4859-935f-b2e2d13962f1",
    "name": "Ponte Dom Tito Buss",
    "level_m": 4.46,
    "last_reading_at": "2026-09-09T20:00:00.000Z",
}
BARRAGEM = {
    "station_id": "d6e340c8-0000-0000-0000-000000000000",
    "name": "Barragem Oeste Taió",
    "level_m": 15.38,
    "last_reading_at": "2026-08-31T12:20:00.000Z",
}


class TestFuso(unittest.TestCase):
    def test_utc_vira_brasilia_sem_fuso(self):
        # 12:21:50 UTC = 09:21:50 em Brasília (UTC-3), sem sufixo de fuso.
        self.assertEqual(de_utc_para_brasilia("2026-08-31T12:21:50.688Z"),
                         "2026-08-31T09:21:50")

    def test_carimbo_invalido_vira_none(self):
        self.assertIsNone(de_utc_para_brasilia("ontem de tarde"))


class TestParse(unittest.TestCase):
    def test_vidal_ramos_entra_com_fuso_convertido(self):
        leituras = parse({"stations": [VIDAL]})
        self.assertEqual(len(leituras), 1)
        l = leituras[0]
        self.assertEqual(l["cidade"], "vidal-ramos")
        self.assertEqual(l["rio"], "itajai-mirim")
        self.assertEqual(l["nivel_m"], 2.93)
        self.assertEqual(l["medido_em"], "2026-08-31T09:21:50")  # Brasília
        self.assertIn("Asthon", l["estacao"])

    def test_rio_do_sul_entra_pela_regua_de_referencia(self):
        """
        Desde 09/09/2026 a leitura de Rio do Sul é a Ponte Dom Tito Buss da
        Asthon — a régua dona das cotas 4,50/5,50/6,50. O título é a chave com
        estacoes_tempo_real e com o estado do vigia.
        """
        leituras = parse({"stations": [TITO_BUSS]})
        self.assertEqual(len(leituras), 1)
        l = leituras[0]
        self.assertEqual((l["rio"], l["cidade"]), ("itajai-acu", "rio-do-sul"))
        self.assertEqual(l["estacao"], "Rio do Sul, Ponte Dom Tito Buss (Asthon)")
        self.assertEqual(l["nivel_m"], 4.46)
        self.assertEqual(l["medido_em"], "2026-09-09T17:00:00")

    def test_rio_do_sul_tem_uma_regua_so_na_asthon(self):
        """Duas réguas na mesma cidade jogariam a tela em 'várias' e calariam o vigia."""
        from coleta_asthon import POR_ESTACAO
        self.assertEqual(sum(1 for _, c in POR_ESTACAO.values() if c == "rio-do-sul"), 1)

    def test_estacao_fora_da_lista_nao_entra(self):
        # Barragem tem station_id desconhecido: some, mesmo com nível plausível.
        self.assertEqual(parse({"stations": [BARRAGEM]}), [])

    def test_nivel_implausivel_nao_entra(self):
        alto = {**VIDAL, "level_m": 349.08}  # altitude, não nível de rio
        self.assertEqual(parse({"stations": [alto]}), [])

    def test_nivel_zero_nao_entra(self):
        parado = {**VIDAL, "level_m": 0.0}  # sensor parado
        self.assertEqual(parse({"stations": [parado]}), [])

    def test_sem_carimbo_nao_entra(self):
        sem = {k: v for k, v in VIDAL.items() if k != "last_reading_at"}
        self.assertEqual(parse({"stations": [sem]}), [])

    def test_aceita_lista_direta_alem_de_dict(self):
        self.assertEqual(len(parse([VIDAL])), 1)


if __name__ == "__main__":
    unittest.main()
