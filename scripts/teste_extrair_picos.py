#!/usr/bin/env python3
"""Testes da extração de picos.

O que estes casos protegem: o script transforma série bruta em registro de
enchente, e registro de enchente é o que a tela mostra. Um pico no horário
errado vira tempo de descida errado, que vira hora de sair de casa errada.

    python3 scripts/teste_extrair_picos.py
"""

import unittest
from datetime import datetime, timedelta

from extrair_picos import (
    INTERVALO_ENTRE_EVENTOS_H,
    MIN_LEITURAS,
    Leitura,
    separar_eventos,
)

INICIO = datetime(2026, 8, 1, 0, 0)


def serie(*valores, passo_h=1, inicio=INICIO):
    """Leituras espaçadas de `passo_h` horas."""
    return [Leitura(inicio + timedelta(hours=i * passo_h), v, "Blumenau")
            for i, v in enumerate(valores)]


class TesteSepararEventos(unittest.TestCase):
    def test_uma_cheia_vira_um_evento_com_o_maior_valor(self):
        eventos = separar_eventos(serie(3.0, 5.0, 7.2, 9.4, 8.1, 6.0, 4.0), limiar=6.0)
        self.assertEqual(len(eventos), 1)
        self.assertAlmostEqual(eventos[0].pico_m, 9.4)
        self.assertEqual(eventos[0].quando, INICIO + timedelta(hours=3))

    def test_o_horario_do_pico_e_o_da_maior_leitura(self):
        eventos = separar_eventos(serie(7.0, 6.5, 9.9, 7.1), limiar=6.0)
        self.assertEqual(eventos[0].quando, INICIO + timedelta(hours=2))

    def test_duas_cheias_separadas_por_dias_sao_dois_eventos(self):
        cheia1 = serie(7.0, 8.0, 7.0)
        depois = INICIO + timedelta(hours=3 + INTERVALO_ENTRE_EVENTOS_H + 5)
        cheia2 = serie(7.5, 9.0, 7.5, inicio=depois)
        eventos = separar_eventos(cheia1 + cheia2, limiar=6.0)
        self.assertEqual(len(eventos), 2)
        self.assertAlmostEqual(eventos[0].pico_m, 8.0)
        self.assertAlmostEqual(eventos[1].pico_m, 9.0)

    def test_rio_baixando_e_subindo_dentro_da_janela_e_um_evento_so(self):
        """A cheia oscila; enquanto ela não fica 18 h abaixo da cota, é a mesma."""
        eventos = separar_eventos(serie(7.0, 5.0, 5.5, 8.0, 7.0), limiar=6.0)
        self.assertEqual(len(eventos), 1)
        self.assertAlmostEqual(eventos[0].pico_m, 8.0)

    def test_leitura_isolada_acima_da_cota_nao_e_evento(self):
        """Um valor solto é mais provavelmente falha de sensor que cheia."""
        self.assertEqual(separar_eventos(serie(3.0, 9.0, 3.0), limiar=6.0), [])
        self.assertEqual(MIN_LEITURAS, 2)

    def test_serie_toda_abaixo_da_cota_nao_gera_evento(self):
        self.assertEqual(separar_eventos(serie(1.0, 2.0, 3.0), limiar=6.0), [])

    def test_serie_vazia(self):
        self.assertEqual(separar_eventos([], limiar=6.0), [])


class TesteSuspeitos(unittest.TestCase):
    def test_salto_grande_e_marcado_mas_nao_removido(self):
        """Blumenau já subiu mais de 4 m em menos de 24 h: descartar o extremo
        seria jogar fora justamente o que interessa."""
        eventos = separar_eventos(serie(7.0, 7.2, 14.0, 7.5), limiar=6.0)
        self.assertEqual(len(eventos), 1)
        self.assertAlmostEqual(eventos[0].pico_m, 14.0, msg="o extremo continua sendo o pico")
        self.assertTrue(eventos[0].suspeitos, "e vem marcado para conferência")

    def test_subida_normal_nao_e_marcada(self):
        eventos = separar_eventos(serie(7.0, 7.5, 8.0, 8.4), limiar=6.0)
        self.assertEqual(eventos[0].suspeitos, [])


if __name__ == "__main__":
    unittest.main(verbosity=2)
