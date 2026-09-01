#!/usr/bin/env python3
"""
Testes do coletor de NÍVEL BRUTO da rede estadual (Defesa Civil de SC).

A chamada de rede não roda aqui (o host não é alcançável do container); o que se
testa é o `converter`, onde moram os riscos: o fuso (errar desloca a idade em
três horas), a separação em baldes (leitura / sem_leitura / suspeita) e a regra
de fundo — nível BRUTO, `usar_para_cota` SEMPRE False, nunca comparado com cota
municipal sem offset calibrado.

    python3 scripts/teste_coleta_nivel_sc.py
"""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from coleta_nivel_sc import converter, e_numero, hora_local


def estacao(codigo="DCSC-00006", nome="SDC-SC Indaial", local="",
            bacia="SC - Rio Itajaí-Açu", nivel=6.86, chuva24=13.5,
            carimbo="2026-09-01T23:42:54+00:00"):
    return {
        "codigo": codigo,
        "name": {"general": nome, "local": local},
        "timestamp": carimbo,
        "position": {"bacia": bacia, "latitude": -26.9, "longitude": -49.2},
        "data": {
            "rio": {"rio_nivel": {"value": nivel}},
            "chuva": {"acumulado": {"h024": None if chuva24 is None else {"value": chuva24}}},
        },
    }


class TestFuso(unittest.TestCase):
    """UTC do GraphQL -> hora de Brasília sem fuso, o formato do projeto (CLAUDE.md)."""

    def test_converte_utc_para_brasilia(self):
        self.assertEqual(hora_local("2026-09-01T23:42:54+00:00"), "2026-09-01T20:42:54")

    def test_a_diferenca_e_de_tres_horas(self):
        # Se isto quebrar, a idade de toda leitura sai errada em 3 h.
        self.assertEqual(hora_local("2026-08-31T12:00:00+00:00"), "2026-08-31T09:00:00")

    def test_vira_o_dia_para_tras(self):
        self.assertEqual(hora_local("2026-08-31T01:00:00+00:00"), "2026-08-30T22:00:00")

    def test_a_leitura_sai_em_horario_de_brasilia(self):
        leituras, _, _ = converter([estacao()])
        self.assertEqual(leituras[0]["medido_em"], "2026-09-01T20:42:54",
                         "medido_em é Brasília sem fuso, não o UTC cru do GraphQL")

    def test_carimbo_ilegivel_nao_vira_hora(self):
        self.assertIsNone(hora_local(None))
        self.assertIsNone(hora_local("ontem"))


class TestBaldes(unittest.TestCase):
    def test_indaial_vira_leitura(self):
        leituras, sem, susp = converter([estacao()])
        self.assertEqual(len(leituras), 1)
        self.assertEqual((sem, susp), ([], []))
        l = leituras[0]
        self.assertEqual(l["cidade"], "indaial")
        self.assertEqual(l["nivel_bruto_m"], 6.86)

    def test_value_null_vai_para_sem_leitura(self):
        """Gaspar tem sensor e às vezes vem null: é 'sem leitura agora', não some."""
        leituras, sem, susp = converter([estacao(codigo="DCSC-00005", nome="SDC-SC Gaspar", nivel=None)])
        self.assertEqual(leituras, [])
        self.assertEqual(len(sem), 1)
        self.assertEqual(sem[0]["cidade"], "gaspar")

    def test_estacao_H_e_descartada(self):
        """'(H)' reporta altitude, não rio: não entra em balde nenhum."""
        leituras, sem, susp = converter([estacao(nome="SDC-SC Salete (H)", nivel=399.0)])
        self.assertEqual((leituras, sem, susp), ([], [], []))

    def test_guabiruba_e_suspeita(self):
        leituras, sem, susp = converter([estacao(codigo="DCSC-00029", nome="SDC-SC Guabiruba", nivel=24.91)])
        self.assertEqual(leituras, [])
        self.assertEqual(len(susp), 1)
        self.assertEqual(susp[0]["cidade"], "guabiruba")

    def test_barragem_tem_datum_reservatorio(self):
        leituras, _, _ = converter([estacao(codigo="DCSC-00040", nome="SDC-SC Barragem Oeste", nivel=12.0)])
        self.assertEqual(leituras[0]["datum"], "reservatorio")

    def test_bacia_null_nao_quebra_e_estacao_de_fora_fica_de_fora(self):
        """position.bacia null não estoura; e sem 'Itaja' a estação não entra."""
        leituras, sem, susp = converter([estacao(bacia=None)])
        self.assertEqual((leituras, sem, susp), ([], [], []))

    def test_valor_absurdo_vai_para_suspeita(self):
        leituras, sem, susp = converter([estacao(nivel=50.0)])
        self.assertEqual(leituras, [])
        self.assertEqual(len(susp), 1)

    def test_booleano_nao_e_metro(self):
        """rio_nivel.value booleano (armadilha 1) não vira 1,00 m — vai para sem_leitura."""
        leituras, sem, susp = converter([estacao(nivel=True)])
        self.assertEqual(leituras, [])
        self.assertEqual(len(sem), 1)


class TestRegraDeFundo(unittest.TestCase):
    def test_toda_leitura_e_bruta_e_nao_serve_para_cota(self):
        leituras, _, _ = converter([estacao(), estacao(codigo="DCSC-00040", nome="SDC-SC Barragem", nivel=9.0)])
        self.assertTrue(leituras)
        for l in leituras:
            self.assertFalse(l["usar_para_cota"], "nível estadual nunca vira cota sem offset calibrado")
            self.assertEqual(l["origem"], "estadual")
            self.assertIsNone(l["offset_datum"])
            self.assertIn(l["datum"], ("bruto_estadual", "reservatorio"))


class TestCadeia(unittest.TestCase):
    def test_estacao_fora_da_cadeia_entra_sem_cidade(self):
        leituras, _, _ = converter([estacao(codigo="DCSC-99999", nome="SDC-SC Outra")])
        self.assertEqual(len(leituras), 1)
        self.assertIsNone(leituras[0]["cidade"])

    def test_so_cadeia_recusa_estacao_fora_do_mapa(self):
        leituras, _, _ = converter([estacao(codigo="DCSC-99999", nome="SDC-SC Outra")], so_cadeia=True)
        self.assertEqual(leituras, [])


class TestENumero(unittest.TestCase):
    def test_booleano_nao_e_numero(self):
        self.assertFalse(e_numero(True))
        self.assertTrue(e_numero(0))
        self.assertTrue(e_numero(6.86))
        self.assertFalse(e_numero(None))
        self.assertFalse(e_numero("6.86"))


if __name__ == "__main__":
    unittest.main(verbosity=2)
