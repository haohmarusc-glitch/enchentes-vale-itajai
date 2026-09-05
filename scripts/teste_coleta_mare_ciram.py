#!/usr/bin/env python3
"""Testes do coletor de maré da EPAGRI/CIRAM.

Três coisas aqui podem enganar quem lê a tela de Itajaí, e por isso cada uma
tem teste próprio, com a guarda sabotada:

* a unidade é CENTÍMETRO — comparar 61,8 com uma régua em metros erra por duas
  ordens de grandeza;
* o carimbo não traz ano — na virada do ano metade da série é do ano seguinte;
* a série mistura dois dias MEDIDOS com dois dias PREVISTOS — ler previsão como
  medição faria a tela afirmar maré que ainda não aconteceu.

    python3 scripts/teste_coleta_mare_ciram.py
"""

import unittest
from datetime import datetime

import coleta_mare_ciram as c
from coleta_mare_ciram import (
    MAX_CM,
    coletar,
    converter,
    numero,
    quando_para_iso,
)

#: Os números REAIS de Balneário Camboriú em 04/09/2026 22:30, da fonte.
#: observada 61,8 · astronômica 45,0 · residual +16,8 — e 61,8 − 45,0 = 16,8.
LINHA_REAL = {"c": [{"v": "04/09 22:30"}, {"v": "61.80"}, {"v": "45.00"},
                    {"v": "16.80"}, {"v": "44.10"}, {"v": "17.20"}, {"v": "66.40"}]}
#: Linha de previsão: sem maré observada, só astronômica e modelo.
LINHA_PREVISAO = {"c": [{"v": "06/09 10:15"}, {"v": "null"}, {"v": "52.30"},
                        {"v": "null"}, {"v": "55.10"}, {"v": "2.80"}, {"v": "66.40"}]}

AGORA = datetime(2026, 9, 4, 22, 40)


def bruto(*linhas):
    return {"cols": [], "rows": list(linhas)}


class OSinalDoResidual(unittest.TestCase):
    """observada − astronômica. Invertido, diria que o mar está sendo empurrado
    para baixo quando está sendo empurrado para cima — a direção perigosa."""

    def test_o_residual_da_fonte_e_observada_menos_astronomica(self):
        m, _ = converter(bruto(LINHA_REAL), AGORA)
        r = m[0]
        self.assertAlmostEqual(r["observada_cm"] - r["astronomica_cm"], r["residual_cm"], places=2)
        self.assertGreater(r["residual_cm"], 0, "empilhamento por vento é residual POSITIVO")

    def test_o_rotulo_da_coluna_da_fonte_nao_manda_no_sinal(self):
        # A coluna chama-se "(MA-MO)", que sugere astronômica − observada. Se
        # alguém "corrigir" o sinal pelo rótulo, este teste quebra.
        m, _ = converter(bruto(LINHA_REAL), AGORA)
        self.assertNotAlmostEqual(
            m[0]["astronomica_cm"] - m[0]["observada_cm"], m[0]["residual_cm"], places=2)


class AUnidade(unittest.TestCase):
    def test_cada_valor_sai_em_cm_E_em_m(self):
        m, _ = converter(bruto(LINHA_REAL), AGORA)
        self.assertEqual(m[0]["observada_cm"], 61.80)
        self.assertEqual(m[0]["observada_m"], 0.618)
        self.assertEqual(m[0]["nmm_cm"], 66.40)
        self.assertEqual(m[0]["nmm_m"], 0.664)

    def test_metro_e_centimetro_nunca_ficam_incoerentes(self):
        m, _ = converter(bruto(LINHA_REAL), AGORA)
        for nome in ("observada", "astronomica", "residual", "nmm"):
            cm, metros = m[0][f"{nome}_cm"], m[0][f"{nome}_m"]
            self.assertAlmostEqual(cm / 100.0, metros, places=3, msg=nome)

    def test_valor_impossivel_vira_ausencia_e_nao_palpite(self):
        # 9.999 cm são 100 metros de maré. Descartar, nunca "corrigir".
        linha = {"c": [{"v": "04/09 22:30"}, {"v": str(MAX_CM + 1)}, {"v": "45.00"},
                       {"v": "16.80"}, None, None, None]}
        m, p = converter(bruto(linha), AGORA)
        self.assertEqual(m, [], "valor impossível não pode contar como medida")
        self.assertIsNone(p[0]["observada_cm"])
        self.assertIsNone(p[0]["observada_m"])


class OAnoQueAFonteNaoManda(unittest.TestCase):
    def test_dia_e_mes_viram_ISO_no_ano_certo(self):
        self.assertEqual(quando_para_iso("04/09 22:30", AGORA), "2026-09-04T22:30:00")

    def test_na_virada_do_ano_o_ano_vem_da_distancia_ate_agora(self):
        # 31/12 às 23h45: a série cobre dois dias para a frente, então 01/01 é
        # do ANO SEGUINTE. Usar `agora.year` poria a linha 364 dias no passado.
        reveillon = datetime(2026, 12, 31, 23, 45)
        self.assertEqual(quando_para_iso("01/01 02:00", reveillon), "2027-01-01T02:00:00")
        self.assertEqual(quando_para_iso("31/12 22:00", reveillon), "2026-12-31T22:00:00")

    def test_e_simetrico_na_outra_ponta(self):
        ano_novo = datetime(2027, 1, 1, 0, 30)
        self.assertEqual(quando_para_iso("30/12 18:00", ano_novo), "2026-12-30T18:00:00")

    def test_29_de_fevereiro_em_ano_nao_bissexto_nao_explode(self):
        self.assertEqual(quando_para_iso("29/02 12:00", datetime(2027, 3, 1, 0, 0)),
                         "2028-02-29T12:00:00")

    def test_carimbo_ilegivel_descarta_a_linha_em_vez_de_inventar_data(self):
        self.assertIsNone(quando_para_iso("", AGORA))
        self.assertIsNone(quando_para_iso("ontem à noite", AGORA))
        m, p = converter(bruto({"c": [{"v": "sem hora"}, {"v": "61.8"}]}), AGORA)
        self.assertEqual((m, p), ([], []))


class MedidoNaoSeMisturaComPrevisto(unittest.TestCase):
    def test_linha_com_observada_e_medida_sem_observada_e_previsao(self):
        m, p = converter(bruto(LINHA_REAL, LINHA_PREVISAO), AGORA)
        self.assertEqual(len(m), 1)
        self.assertEqual(len(p), 1)
        self.assertTrue(m[0]["medido"])
        self.assertFalse(p[0]["medido"])

    def test_a_previsao_guarda_a_astronomica_mas_nao_finge_observada(self):
        _, p = converter(bruto(LINHA_PREVISAO), AGORA)
        self.assertEqual(p[0]["astronomica_cm"], 52.30)
        self.assertIsNone(p[0]["observada_cm"])
        self.assertIsNone(p[0]["observada_m"])

    def test_itajai_sem_observada_nenhuma_nao_vira_ultima_medida(self):
        # O caso real: a estação de Itajaí devolve 384 linhas e ZERO com maré
        # observada. Se `ultima_medida` pegasse a última linha qualquer, a tela
        # mostraria previsão MOHID como se fosse medição.
        saida = coletar(AGORA, buscador=lambda n, i: bruto(LINHA_PREVISAO, LINHA_PREVISAO))
        for chave, est in saida["estacoes"].items():
            self.assertIsNone(est["ultima_medida"], chave)
            self.assertEqual(est["n_medidas"], 0, chave)
            self.assertEqual(est["n_previsoes"], 2, chave)


class UmaEstacaoForaNaoDerrubaAsOutras(unittest.TestCase):
    def test_estacao_que_falha_some_do_resultado_sem_parar_o_resto(self):
        def buscador(n, ident):
            if n == 12:
                raise RuntimeError("500")
            return bruto(LINHA_REAL)
        saida = coletar(AGORA, buscador=buscador)
        self.assertNotIn("itajai", saida["estacoes"])
        self.assertIn(c.PRINCIPAL, saida["estacoes"])
        self.assertEqual(saida["estacoes"][c.PRINCIPAL]["n_medidas"], 1)

    def test_a_principal_e_a_mais_perto_de_itajai_COM_mare_observada(self):
        # Itajaí está a 0 km e não publica observada; a principal tem que ser a
        # próxima mais perta, não a de menor distância no cadastro.
        self.assertEqual(c.PRINCIPAL, "balneario-camboriu")
        self.assertEqual(c.ESTACOES[c.PRINCIPAL][3], 13)
        self.assertLess(c.ESTACOES[c.PRINCIPAL][3], c.ESTACOES["imbituba"][3])


class OQueOArquivoPromete(unittest.TestCase):
    def test_o_meta_avisa_da_unidade_e_do_misturado(self):
        saida = coletar(AGORA, buscador=lambda n, i: bruto(LINHA_REAL))
        meta = saida["_meta"]
        self.assertIn("CENTÍMETROS", meta["unidade"])
        self.assertIn("observada − astronômica", meta["residual"])
        self.assertIn("Brasília", meta["fuso"])
        self.assertIn("UTC", meta["fuso"])

    def test_numero_aceita_virgula_decimal(self):
        self.assertEqual(numero({"v": "61,80"}), 61.8)
        self.assertIsNone(numero({"v": "null"}))
        self.assertIsNone(numero(None))



class LeituraVelhaNaoELeituraAtual(unittest.TestCase):
    """Estação fora do ar devolve o último valor antigo sem avisar, e ele
    parece atual. Com cadência de 15 min, uma hora sem leitura nova é parada."""

    def _saida(self, minutos_atras):
        quando = AGORA - __import__("datetime").timedelta(minutes=minutos_atras)
        linha = {"c": [{"v": quando.strftime("%d/%m %H:%M")}, {"v": "61.80"},
                       {"v": "45.00"}, {"v": "16.80"}, None, None, None]}
        return coletar(AGORA, buscador=lambda n, i: bruto(linha))["estacoes"][c.PRINCIPAL]

    def test_leitura_de_agora_e_fresca(self):
        est = self._saida(10)
        self.assertTrue(est["fresca"])
        self.assertLessEqual(est["idade_min"], 15)

    def test_leitura_de_tres_horas_NAO_e_fresca(self):
        est = self._saida(180)
        self.assertFalse(est["fresca"], "3 h de atraso passou por leitura atual")
        self.assertGreater(est["idade_min"], c.FRESCA_MIN)

    def test_sem_medida_nenhuma_fresca_e_False_e_nao_None(self):
        # Estação muda e estação fora do ar têm que dar a mesma resposta: não.
        est = coletar(AGORA, buscador=lambda n, i: bruto(LINHA_PREVISAO))["estacoes"][c.PRINCIPAL]
        self.assertIs(est["fresca"], False)
        self.assertIsNone(est["idade_min"])

    def test_a_idade_e_medida_em_BRASILIA_nos_dois_lados(self):
        # Converter um dos lados para UTC daria 180 min de erro — e é o engano
        # que o CLAUDE.md registra como tendo custado uma sessão.
        est = self._saida(30)
        self.assertAlmostEqual(est["idade_min"], 30, delta=1,
                               msg="a idade saiu com deslocamento de fuso")

    def test_carimbo_ilegivel_nao_vira_idade_zero(self):
        # Zero afirmaria leitura recém-chegada. Ausência diz "não sei".
        self.assertIsNone(c.idade_min(None, AGORA))
        self.assertIsNone(c.idade_min("ontem", AGORA))

if __name__ == "__main__":
    unittest.main()
