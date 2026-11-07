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


COD_TITO = "f6360951-219f-4859-935f-b2e2d13962f1"
COD_VIDAL = "bd65df3e-a5e3-4760-a879-56df0fb90787"


def historico(codigo, pontos, datum="gauge_zero"):
    return {"station_id": codigo, "level_datum": datum,
            "level": [{"timestamp": t, "value": v} for t, v in pontos]}


class TestHistorico(unittest.TestCase):
    """O nível vem do station-history (07/11/2026): o painel mentiu a idade por três dias."""

    def test_usa_o_ponto_mais_recente_com_a_hora_da_medicao(self):
        from coleta_asthon import ultimo_do_historico
        corpo = historico(COD_TITO, [
            ("2026-11-07T15:37:43.317454Z", 7.552136695421368),
            ("2026-11-07T15:16:27.317575Z", 7.49905109489051),
        ])
        self.assertEqual(ultimo_do_historico(corpo, COD_TITO),
                         {"nivel_m": 7.55, "medido_em": "2026-11-07T12:37:43"})

    def test_valor_parado_do_painel_nao_vira_leitura_de_agora(self):
        """
        O caso de 05/11/2026: o painel dizia 3,27 m "agora", mas o último ponto
        do histórico era de 04/11 08:26. A leitura sai com a hora verdadeira, e
        a tela a julga velha.
        """
        from coleta_asthon import ultimo_do_historico
        corpo = historico(COD_TITO, [("2026-11-04T11:26:25.808061Z", 3.269444798978941)])
        self.assertEqual(ultimo_do_historico(corpo, COD_TITO)["medido_em"], "2026-11-04T08:26:25")

    def test_outra_estacao_outro_datum_ou_vazio_nao_entram(self):
        from coleta_asthon import ultimo_do_historico
        ponto = [("2026-11-07T15:30:00Z", 7.81)]
        self.assertIsNone(ultimo_do_historico(historico("d2f60af1-53e3-497f-81d6-c6498d28f5a2", ponto), COD_TITO))
        self.assertIsNone(ultimo_do_historico(historico(COD_TITO, ponto, datum="absolute"), COD_TITO))
        self.assertIsNone(ultimo_do_historico(historico(COD_TITO, []), COD_TITO))
        self.assertIsNone(ultimo_do_historico([], COD_TITO))

    def test_ultimo_ponto_implausivel_nao_cai_no_anterior(self):
        from coleta_asthon import ultimo_do_historico
        corpo = historico(COD_TITO, [("2026-11-07T15:00:00Z", 7.4), ("2026-11-07T15:10:00Z", 0.0)])
        self.assertIsNone(ultimo_do_historico(corpo, COD_TITO))

    def test_coletar_segue_com_uma_regua_quando_a_outra_falha(self):
        from coleta_asthon import coletar

        def falso(codigo):
            if codigo == COD_VIDAL:
                raise ConnectionError("timeout")
            return historico(codigo, [("2026-11-07T15:30:00Z", 7.5)])

        leituras = coletar(baixar_hist=falso)
        self.assertEqual([(l["cidade"], l["nivel_m"], l["medido_em"]) for l in leituras],
                         [("rio-do-sul", 7.5, "2026-11-07T12:30:00")])
        self.assertEqual(leituras[0]["estacao"], "Rio do Sul, Ponte Dom Tito Buss (Asthon)")

    def test_espelho_estadual_nunca_entra_na_lista(self):
        """d2f60af1 (owner DCSC) ocupou o lugar no painel em 07/11; é outra régua."""
        from coleta_asthon import POR_ESTACAO
        self.assertNotIn("d2f60af1-53e3-497f-81d6-c6498d28f5a2", POR_ESTACAO)


if __name__ == "__main__":
    unittest.main()
