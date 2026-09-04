#!/usr/bin/env python3
"""Testes da medição de maré.

Este script decide, por dado, quais réguas podem disparar aviso sozinhas. Se
ele errar para um lado, o telefone toca com a maré e a pessoa aprende a ignorar
o aviso; se errar para o outro, a régua fica muda numa cheia de verdade.

    python3 scripts/teste_medir_mare.py
"""

import math
import unittest
from datetime import datetime, timedelta

import json
import tempfile
from pathlib import Path

import medir_mare
from medir_mare import (CORRELACAO_DE_MARE, amostrar, correlacao, destendenciar,
                        duracao_das_travessias, leituras_da_serie, medir,
                        travessias, veredito)

INICIO = datetime(2026, 9, 1, 0, 0)


def serie(dias: int, base: float, amplitude: float, passo_min: int = 15,
          tendencia: float = 0.0) -> list[tuple[datetime, float]]:
    """Série senoidal de período 12,4 h — a maré semidiurna."""
    pontos = []
    n = int(dias * 24 * 60 / passo_min)
    for i in range(n):
        t = INICIO + timedelta(minutes=passo_min * i)
        h = i * passo_min / 60
        nivel = base + amplitude / 2 * math.sin(2 * math.pi * h / 12.4) + tendencia * h / 24
        pontos.append((t, round(nivel, 2)))
    return pontos


class TestTravessias(unittest.TestCase):
    def test_conta_so_as_subidas(self):
        pontos = [(INICIO + timedelta(minutes=15 * i), n)
                  for i, n in enumerate([1.0, 1.2, 1.4, 1.2, 1.0, 1.3])]
        # Cruza 1.3 para cima duas vezes; a descida não conta.
        self.assertEqual(travessias(pontos, 1.3), (2, 1))

    def test_serie_sempre_abaixo_nao_cruza(self):
        self.assertEqual(travessias(serie(3, 0.7, 0.4), 5.0), (0, 0))


class TestVeredito(unittest.TestCase):
    def medida(self, **kw):
        base = {"dias": 10, "menor_cota_m": 1.16, "folga_ate_a_cota_m": 0.4,
                "amplitude_diaria_mediana_m": 0.2, "travessias": 0,
                "dias_com_travessia": 0}
        base.update(kw)
        return base

    def test_serie_curta_nao_opina(self):
        """Um dia de dados não separa maré de cheia."""
        s, _ = veredito(self.medida(dias=1))
        self.assertEqual(s, "sem opinião")

    def test_oscila_mais_que_a_folga_nao_dispara(self):
        # O caso da DC-01: oscila mais do que a distância até a cota, então
        # cruza sozinha, sem enchente.
        s, porque = veredito(self.medida(amplitude_diaria_mediana_m=0.9,
                                         folga_ate_a_cota_m=0.4))
        self.assertEqual(s, "NÃO disparar sozinha")
        self.assertIn("cruza sozinha", porque)

    def test_cruza_em_muitos_dias_nao_dispara(self):
        s, _ = veredito(self.medida(dias=9, dias_com_travessia=4, travessias=8))
        self.assertEqual(s, "NÃO disparar sozinha")

    def test_regua_de_rio_com_folga_pode_disparar(self):
        s, _ = veredito(self.medida(amplitude_diaria_mediana_m=0.15,
                                    folga_ate_a_cota_m=1.4))
        self.assertEqual(s, "pode disparar")

    def test_sem_cota_nao_opina(self):
        s, _ = veredito(self.medida(menor_cota_m=None))
        self.assertEqual(s, "sem opinião")


class TestMedir(unittest.TestCase):
    def test_serie_de_mare_tem_amplitude_diaria_alta(self):
        m = medir("Régua fictícia", serie(5, base=0.9, amplitude=0.8))
        self.assertGreater(m["amplitude_diaria_mediana_m"], 0.7)
        self.assertEqual(m["dias"], 5)

    def test_serie_calma_tem_amplitude_baixa(self):
        m = medir("Régua fictícia", serie(5, base=3.5, amplitude=0.05))
        self.assertLess(m["amplitude_diaria_mediana_m"], 0.1)

    def test_serie_curta_demais_devolve_none(self):
        self.assertIsNone(medir("x", [(INICIO, 1.0)]))

    def test_estacao_real_traz_cota_e_estado_do_cadastro(self):
        """
        Contra o cadastro de verdade: a DC-01 está marcada para não disparar, e
        a medição precisa enxergar isso para poder discordar.
        """
        m = medir("DC-01 Rio Itajaí-Açu - ICMBio/CEPSUL", serie(4, 0.9, 0.8))
        self.assertEqual(m["codigo"], "DC-01")
        self.assertEqual(m["menor_cota_m"], 1.16)
        self.assertFalse(m["alerta_automatico_hoje"])

    def test_estacao_de_rio_dispara_no_cadastro(self):
        m = medir("Rio do Sul Estação MKS", serie(4, 3.5, 0.1))
        self.assertTrue(m["alerta_automatico_hoje"])
        self.assertEqual(m["menor_cota_m"], 4.5)


class AsTresReguasDoAcuEmItajaiSaoSEPARADAS(unittest.TestCase):
    """
    O ndjson mestre SEMPRE guardou `estacao`, e `medir_mare` chaveia por ela —
    então a DC-11 nunca esteve bloqueada por "série misturada".

    A confusão vinha do recorte publicado (`serie-recente.json`), que agrupava
    só por (rio, cidade) e jogava a estação fora: ali, sim, DC-01, DC-02 e
    DC-11 saíam intercaladas. Mas não é esse arquivo que este script lê.
    O bloqueio real da DC-11 é outro: o ndjson mora na VPS.

    Este teste existe para que a afirmação não precise ser acreditada — ele
    monta um ndjson com as TRÊS réguas do Açu em Itajaí, com os níveis reais de
    04/09/2026, e cobra que saiam três medidas distintas.
    """

    DC01 = "DC-01 Rio Itajaí-Açu - ICMBio/CEPSUL"
    DC02 = "DC-02 Rio Itajaí-Açu - Praça Celso Pereira da Silva"
    DC11 = "DC-11 Rio Itajaí-Açú – Santa Regina (Volta de Cima)"

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self._orig = medir_mare.SERIE
        medir_mare.SERIE = Path(self.tmp.name)

    def tearDown(self):
        medir_mare.SERIE = self._orig
        self.tmp.cleanup()

    def escrever(self, linhas):
        (medir_mare.SERIE / "2026-09.ndjson").write_text(
            "\n".join(json.dumps(l, ensure_ascii=False) for l in linhas) + "\n",
            encoding="utf-8",
        )

    def tres_reguas(self):
        # Níveis reais de 04/09: DC-01 0,56 · DC-02 1,20 · DC-11 2,70.
        # Cada uma com uma oscilação própria, para não saírem idênticas.
        linhas = []
        for i in range(4 * 24 * 4):  # 4 dias, de 15 em 15 min
            t = (INICIO + timedelta(minutes=15 * i)).isoformat(timespec="seconds")
            h = i / 4
            for titulo, base, amp in (
                (self.DC01, 0.56, 0.9),
                (self.DC02, 1.20, 0.7),
                (self.DC11, 2.70, 0.2),
            ):
                nivel = base + amp / 2 * math.sin(2 * math.pi * h / 12.4)
                linhas.append({
                    "estacao": titulo, "rio": "itajai-acu", "cidade": "itajai",
                    "medido_em": t, "nivel_m": round(nivel, 2),
                })
        self.escrever(linhas)

    def test_a_serie_sai_separada_por_estacao(self):
        self.tres_reguas()
        serie = leituras_da_serie("2026-09")
        self.assertEqual(sorted(serie), sorted([self.DC01, self.DC02, self.DC11]))
        # E cada uma em torno do SEU nível — não da média das três.
        for titulo, base in ((self.DC01, 0.56), (self.DC02, 1.20), (self.DC11, 2.70)):
            niveis = [n for _, n in serie[titulo]]
            self.assertAlmostEqual(sum(niveis) / len(niveis), base, delta=0.05)

    def test_a_DC11_ganha_medida_propria_com_a_cota_DELA(self):
        self.tres_reguas()
        serie = leituras_da_serie("2026-09")
        m = medir(self.DC11, serie[self.DC11], reguas_na_cidade=3)
        self.assertIsNotNone(m)
        self.assertEqual(m["codigo"], "DC-11")
        # A cota vem da PRÓPRIA estação (3,00 / 4,00 / 5,00), não emprestada da
        # cidade — Itajaí tem onze réguas, e emprestar mediria contra o zero
        # errado.
        self.assertEqual(m["menor_cota_m"], 3.00)
        self.assertAlmostEqual(m["nivel_tipico_m"], 2.70, delta=0.05)

    def test_juntar_as_tres_daria_uma_amplitude_que_NAO_e_mare(self):
        # A prova de que separar importa: a mistura das três oscila muito mais
        # que qualquer uma delas, e a diferença é entre ZEROS, não maré.
        self.tres_reguas()
        serie = leituras_da_serie("2026-09")
        separadas = [
            medir(t, serie[t], 3)["amplitude_diaria_mediana_m"]
            for t in (self.DC01, self.DC02, self.DC11)
        ]
        juntas = sorted(p for t in serie for p in serie[t])
        misturada = medir("mistura", juntas, 3)["amplitude_diaria_mediana_m"]
        self.assertGreater(
            misturada, max(separadas) * 1.5,
            "o fixture parou de reproduzir a diferença — o teste virou vazio",
        )


class SepararMareDeCheia(unittest.TestCase):
    """
    O defeito do próprio script, achado em 04/09/2026.

    Ele media amplitude e travessias e chamava as duas coisas de "oscila" —
    mas amplitude NÃO distingue maré de cheia. Na janela de 6 dias em que
    rodou, a bacia inteira descia de um evento real (Blumenau −1,15 m, DC-10
    −1,00 m, Brusque −0,52 m), e ele recomendou travar a DC-11. Num evento
    assim, ele recomendaria travar régua que estava alarmando CERTO — o erro na
    direção que cala.

    O separador: recessão de cheia é LENTA (dias), maré é RÁPIDA (12,4 h).
    Tirando a média móvel de 13 h, a recessão sai e a maré fica.
    """

    def reta_descendo(self, dias=6, base=5.0, queda=0.5):
        """Rio em recessão pura: desce devagar, sem maré."""
        n = int(dias * 24 * 60 / 15)
        return [(INICIO + timedelta(minutes=15 * i), base - queda * (i / 96) / 24)
                for i in range(n)]

    def test_destendenciar_apaga_a_recessao_e_deixa_a_mare(self):
        so_mare = serie(6, 1.0, 0.9)
        com_recessao = [(t, v - 0.5 * i / 96 / 24)
                        for i, (t, v) in enumerate(so_mare)]
        r = destendenciar(com_recessao)
        # A maré sobrevive: o resíduo ainda tem a amplitude dela.
        self.assertGreater(max(r) - min(r), 0.5)
        # E a recessão some: o resíduo não tem tendência.
        self.assertAlmostEqual(sum(r[:50]) / 50, sum(r[-50:]) / 50, delta=0.15)

    def test_regua_de_MARE_correlaciona_com_a_referencia(self):
        ref = serie(6, 1.0, 0.9)
        alvo = [(t, v + 1.8 - 0.5 * i / 96 / 24)
                for i, (t, v) in enumerate(serie(6, 0.0, 0.7))]
        r = correlacao(destendenciar(alvo), destendenciar(ref))
        self.assertIsNotNone(r)
        self.assertGreaterEqual(r, CORRELACAO_DE_MARE)

    def test_regua_de_RIO_nao_correlaciona_com_a_referencia(self):
        """
        O caso REAL, e o único que prova que a destendência faz falta.

        Numa semana com cheia, a régua de estuário TAMBÉM está em recessão —
        as duas descem juntas. A correlação CRUA fica alta por causa da queda
        compartilhada, e é isso que fazia o script confundir cheia com maré.
        Medido no dado real de 04/09: DC-11 × Blumenau dava +0,77 CRU e cai
        para +0,09 destendenciado.

        Uma reta descendo contra uma maré pura não serve de teste: ela já
        correlaciona mal sem destendenciar nada, e o teste passaria mesmo com a
        destendência removida. A falsificação flagrou exatamente isso.
        """
        # Proporções do dado REAL de 04/09: a recessão domina a maré. Blumenau
        # caiu 1,15 m em 48 h enquanto a oscilação rápida da DC-11 era 0,33 m
        # de pico a pico. `tendencia` é queda por dia.
        ref = serie(6, 1.0, 0.33, tendencia=-0.5)
        # Rio em recessão na MESMA taxa, com um bolinho lento de 7 h que não é
        # maré — sem ele o resíduo fica degenerado e a correlação vira None.
        rio = [(t, v + 0.02 * math.sin(2 * math.pi * (i / 4) / 7))
               for i, (t, v) in enumerate(serie(6, 5.0, 0.0, tendencia=-0.5))]

        cru = correlacao([v for _, v in rio], [v for _, v in ref])
        self.assertIsNotNone(cru)
        self.assertGreater(
            cru, CORRELACAO_DE_MARE,
            "o fixture parou de reproduzir o defeito: sem destendenciar, as duas "
            "têm de parecer parecidas por causa da queda compartilhada",
        )

        limpo = correlacao(destendenciar(rio), destendenciar(ref))
        self.assertIsNotNone(limpo)
        self.assertLess(
            limpo, CORRELACAO_DE_MARE,
            "destendenciada, a régua de rio não pode passar por maré — é o que "
            "impede o script de recomendar trava para quem estava alarmando certo",
        )

    def test_correlacao_com_poucos_pontos_devolve_None_em_vez_de_numero(self):
        self.assertIsNone(correlacao([1.0, 2.0], [1.0, 2.0]))

    def test_correlacao_de_serie_constante_nao_divide_por_zero(self):
        self.assertIsNone(correlacao([1.0] * 30, list(range(30))))

    def test_amostrar_interpola_na_grade_da_outra_regua(self):
        pontos = [(INICIO, 1.0), (INICIO + timedelta(hours=2), 3.0)]
        meio = amostrar(pontos, [INICIO + timedelta(hours=1)])
        self.assertAlmostEqual(meio[0], 2.0)

    def test_amostrar_fora_do_intervalo_vira_None_e_nao_extrapola(self):
        pontos = [(INICIO, 1.0), (INICIO + timedelta(hours=2), 3.0)]
        fora = amostrar(pontos, [INICIO - timedelta(hours=5)])
        self.assertIsNone(fora[0])


class QuantoTempoFicaAcimaDaCota(unittest.TestCase):
    """
    O número que falta para calibrar uma regra de persistência — "só avisar
    depois de N horas acima". Maré cruza e VOLTA em horas; cheia cruza e FICA.
    Sem esta medição, o N seria chute.
    """

    def test_mede_cada_travessia_separadamente(self):
        # Sobe, desce, sobe de novo: duas travessias.
        p = [(INICIO + timedelta(hours=h), n) for h, n in
             ((0, 1.0), (1, 3.0), (2, 3.0), (3, 1.0), (4, 3.0), (5, 1.0))]
        self.assertEqual(duracao_das_travessias(p, 2.0), [2.0, 1.0])

    def test_serie_que_termina_ACIMA_conta_ate_o_fim(self):
        # Não descartar: uma cheia em curso é exatamente esse caso.
        p = [(INICIO + timedelta(hours=h), n) for h, n in ((0, 1.0), (1, 3.0), (4, 3.0))]
        self.assertEqual(duracao_das_travessias(p, 2.0), [3.0])

    def test_serie_sempre_abaixo_nao_tem_travessia(self):
        p = [(INICIO + timedelta(hours=h), 1.0) for h in range(5)]
        self.assertEqual(duracao_das_travessias(p, 2.0), [])

    def test_mare_fica_POUCO_tempo_acima_e_cheia_fica_MUITO(self):
        # A diferença que sustenta a ideia de persistência.
        de_mare = duracao_das_travessias(serie(6, 2.8, 0.7), 3.0)
        cheia = [(INICIO + timedelta(hours=h), 3.5) for h in range(48)]
        de_cheia = duracao_das_travessias(cheia, 3.0)
        self.assertTrue(de_mare, "o fixture de maré parou de cruzar a cota")
        self.assertLess(max(de_mare), 12.0)
        self.assertGreater(de_cheia[0], 40.0)


class OVereditoUsaAAssinaturaAntesDaAmplitude(unittest.TestCase):
    def test_sem_assinatura_de_mare_a_amplitude_vira_evidencia_de_CHEIA(self):
        # A correção do defeito: oscilar muito SEM assinatura de maré é o rio
        # subindo, e recomendar trava aí calaria um aviso verdadeiro.
        m = {"dias": 6, "menor_cota_m": 3.0, "folga_ate_a_cota_m": 0.2,
             "amplitude_diaria_mediana_m": 0.85, "travessias": 7,
             "dias_com_travessia": 3, "mare_correlacao": 0.09,
             "mare_referencia": "Blumenau"}
        self.assertEqual(veredito(m)[0], "pode disparar")

    def test_com_assinatura_de_mare_continua_recomendando_a_trava(self):
        m = {"dias": 6, "menor_cota_m": 3.0, "folga_ate_a_cota_m": 0.2,
             "amplitude_diaria_mediana_m": 0.85, "travessias": 7,
             "dias_com_travessia": 3, "mare_correlacao": 0.92,
             "mare_referencia": "DC-09", "horas_acima_mediana": 2.5,
             "horas_acima_maxima": 4.0}
        sugestao, porque = veredito(m)
        self.assertEqual(sugestao, "NÃO disparar sozinha")
        self.assertIn("É de maré", porque)
        self.assertIn("2.5 h", porque)

    def test_sem_assinatura_calculada_o_comportamento_antigo_vale(self):
        # Régua sem referência de maré na série: não inventa veredito novo.
        m = {"dias": 6, "menor_cota_m": 3.0, "folga_ate_a_cota_m": 0.2,
             "amplitude_diaria_mediana_m": 0.85, "travessias": 7,
             "dias_com_travessia": 3, "mare_correlacao": None}
        self.assertEqual(veredito(m)[0], "NÃO disparar sozinha")


if __name__ == "__main__":
    unittest.main(verbosity=2)
