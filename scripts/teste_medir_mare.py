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
from medir_mare import leituras_da_serie, medir, travessias, veredito

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


if __name__ == "__main__":
    unittest.main(verbosity=2)
