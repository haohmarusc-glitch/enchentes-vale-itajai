#!/usr/bin/env python3
"""O cadastro da rede estadual: um fato, dois leitores.

O que precisa ficar travado aqui é a razão de o módulo existir. As listas moravam dentro do
coletor de tempo real e o lado do histórico não as via — o resultado foi o resumo commitado
listar 28,70 m como crista candidata de Guabiruba enquanto o coletor já mandava a mesma estação
para `suspeitas`. Os testes abaixo cobrem as duas metades disso: que o coletor continua lendo as
MESMAS listas (e não uma cópia que envelhece sozinha) e que a quebra de série corta onde deve.
"""

from __future__ import annotations

import unittest
from datetime import datetime

import cadastro_dcsc
import coleta_nivel_sc
import consolidar_historico_dcsc
from cadastro_dcsc import (CADEIA, NAO_MEDE_NIVEL, QUEBRAS_DE_SERIE, RESERVATORIOS, SUSPEITAS,
                           apos_a_quebra, mede_nivel, quebra_de)


class UmCadastroDoisLeitores(unittest.TestCase):
    def teste_o_coletor_ao_vivo_le_o_MESMO_objeto_nao_uma_copia(self):
        """`is`, não `==`: cópia igual hoje é cópia diferente depois da próxima descoberta."""
        self.assertIs(coleta_nivel_sc.SUSPEITAS, SUSPEITAS)
        self.assertIs(coleta_nivel_sc.NAO_MEDE_NIVEL, NAO_MEDE_NIVEL)
        self.assertIs(coleta_nivel_sc.RESERVATORIOS, RESERVATORIOS)
        self.assertIs(coleta_nivel_sc.CADEIA, CADEIA)

    def teste_o_consolidador_do_historico_le_o_mesmo_objeto(self):
        self.assertIs(consolidar_historico_dcsc.CADEIA, CADEIA)
        self.assertIs(consolidar_historico_dcsc.NAO_MEDE_NIVEL, NAO_MEDE_NIVEL)

    def teste_o_cadastro_nao_arrasta_requests(self):
        """Sem dependência de rede: o import do histórico pode ser direto, não num try/except
        que some calado quando `requests` falta."""
        import sys
        fonte = (__import__("pathlib").Path(cadastro_dcsc.__file__)).read_text(encoding="utf-8")
        self.assertNotIn("import requests", fonte)
        self.assertIn("cadastro_dcsc", sys.modules)


class QuemEQuem(unittest.TestCase):
    def teste_estacao_que_nao_mede_nivel(self):
        self.assertFalse(mede_nivel("DCSC-00005"))      # Gaspar
        self.assertFalse(mede_nivel("DCSC-00026"))      # Blumenau, type=Meteo
        self.assertTrue(mede_nivel("DCSC-00013"))       # Rio do Sul

    def teste_estacao_desconhecida_mede_ate_prova_em_contrario(self):
        """Ausência de cadastro não é acusação: estação nova não nasce descartada."""
        self.assertTrue(mede_nivel("DCSC-99999"))
        self.assertIsNone(quebra_de("DCSC-99999"))

    def teste_toda_estacao_das_listas_esta_na_cadeia(self):
        """Lista que aponta para código fora da CADEIA é lista com erro de digitação."""
        for cod in set(SUSPEITAS) | set(NAO_MEDE_NIVEL) | set(RESERVATORIOS) | set(QUEBRAS_DE_SERIE):
            self.assertIn(cod, CADEIA, f"{cod} não está na CADEIA")

    def teste_reservatorio_nao_e_regua_urbana(self):
        self.assertEqual(RESERVATORIOS, {"DCSC-00040", "DCSC-00038"})


class Quebra(unittest.TestCase):
    """Guabiruba, 01/04/2026 17:40 — de régua do ribeirão para altitude, num passo de 10 min."""

    def teste_antes_da_quebra_a_leitura_vale(self):
        self.assertFalse(apos_a_quebra("DCSC-00029", datetime(2026, 4, 1, 17, 30)))

    def teste_o_instante_da_quebra_JA_e_a_grandeza_nova(self):
        """Inclusivo: às 17:40 a leitura já era 16,21 m — o passo de 0,51 para 16,21."""
        self.assertTrue(apos_a_quebra("DCSC-00029", datetime(2026, 4, 1, 17, 40)))

    def teste_depois_da_quebra_a_leitura_nao_vale(self):
        self.assertTrue(apos_a_quebra("DCSC-00029", datetime(2026, 9, 9, 23, 10)))

    def teste_estacao_sem_quebra_nunca_corta(self):
        self.assertFalse(apos_a_quebra("DCSC-00013", datetime(2026, 9, 9, 23, 10)))

    def teste_sem_carimbo_nao_corta(self):
        """"Não sei quando foi" nunca pode virar "descarta" — seria apagar série por ignorância."""
        self.assertFalse(apos_a_quebra("DCSC-00029", None))

    def teste_a_quebra_diz_as_duas_grandezas_e_a_fonte(self):
        """Quebra sem o que era antes e o que é depois não permite reconciliar o datum depois."""
        q = quebra_de("DCSC-00029")
        self.assertIsNotNone(q)
        for campo in ("desde", "grandeza_antes", "grandeza_depois", "motivo", "fonte"):
            self.assertTrue(q.get(campo), f"quebra sem {campo}")
        datetime.fromisoformat(q["desde"])              # carimbo válido, hora de Brasília

    def teste_a_estacao_da_quebra_tambem_esta_em_suspeitas(self):
        """As duas listas contam a mesma história de Guabiruba; divergir seria o bug de novo."""
        self.assertIn("DCSC-00029", SUSPEITAS)
        self.assertIn("04/2026", SUSPEITAS["DCSC-00029"])


if __name__ == "__main__":
    unittest.main()
