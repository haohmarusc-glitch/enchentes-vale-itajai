#!/usr/bin/env python3
"""Testes do importador da tábua de maré da UNIVALI/CTTMAR.

O ponto mais delicado testado aqui: `formatar()` NUNCA emite `altura_m` — a
planilha vem em datum IBGE, e nada garante que bate com o datum que a Defesa
Civil/DHN publicam (mesmo problema que já é REGRA BLOQUEANTE para Blumenau).
Um teste trava isso: se `altura_m` vazar para o JSON, quebra.

    python3 scripts/teste_importar_mare_univali.py
"""

import unittest
from datetime import date, datetime, time

from importar_mare_univali import (
    classificar_extremos,
    extrair_eventos,
    formatar,
    montar,
)


def linha(d1=None, h1=None, v1=None, d2=None, h2=None, v2=None, d3=None, h3=None, v3=None):
    """Uma linha da planilha nos 3 blocos (Data, Hora, Nível | ... | ...)."""
    d1 = datetime.combine(d1, time()) if d1 else None
    d2 = datetime.combine(d2, time()) if d2 else None
    d3 = datetime.combine(d3, time()) if d3 else None
    return (d1, h1, v1, None, d2, h2, v2, None, d3, h3, v3)


class TesteExtrairEventos(unittest.TestCase):
    def test_data_repete_para_baixo_dentro_do_mesmo_dia(self):
        # Só a primeira linha de cada dia tem a data; as seguintes vêm None.
        linhas = [
            linha(d1=date(2026, 9, 1), h1=time(4, 28), v1=1.2),
            linha(h1=time(9, 49), v1=0.5),  # mesmo dia 1, sem data na célula
            linha(d1=date(2026, 9, 2), h1=time(5, 10), v1=1.1),
        ]
        eventos = extrair_eventos(linhas)
        self.assertEqual(len(eventos), 3)
        self.assertEqual(eventos[0][0], datetime(2026, 9, 1, 4, 28))
        self.assertEqual(eventos[1][0], datetime(2026, 9, 1, 9, 49))
        self.assertEqual(eventos[2][0], datetime(2026, 9, 2, 5, 10))

    def test_tres_blocos_lado_a_lado_juntam_e_ordenam(self):
        # Bloco 1 = dias 1-2; bloco 2 = dias 10-11 (datas mais tarde, mas a
        # planilha real tem os blocos por faixa de dias, não por ordem).
        linhas = [
            linha(
                d1=date(2026, 9, 1), h1=time(4, 0), v1=1.0,
                d2=date(2026, 9, 10), h2=time(1, 0), v2=1.3,
            ),
            linha(h1=time(10, 0), v1=0.3),
        ]
        eventos = extrair_eventos(linhas)
        # Ordenado no tempo, mesmo vindo de blocos "fora de ordem" na planilha.
        self.assertEqual([e[0] for e in eventos], sorted(e[0] for e in eventos))
        self.assertEqual(len(eventos), 3)

    def test_linha_sem_data_nenhuma_ainda_e_ignorada(self):
        linhas = [linha(h1=time(9, 0), v1=0.5)]  # nunca veio data pra esse bloco
        eventos = extrair_eventos(linhas)
        self.assertEqual(eventos, [])


class TesteClassificarExtremos(unittest.TestCase):
    def test_alterna_alta_baixa_alta_baixa(self):
        base = datetime(2026, 9, 1)
        eventos = [
            (base.replace(hour=4), 1.29),
            (base.replace(hour=9), 0.50),
            (base.replace(hour=16), 1.18),
            (base.replace(hour=20), 0.45),
        ]
        preamares, baixamares = classificar_extremos(eventos)
        self.assertEqual([q.hour for q, _ in preamares], [4, 16])
        self.assertEqual([q.hour for q, _ in baixamares], [9, 20])

    def test_ponta_da_serie_classifica_pelo_unico_vizinho(self):
        base = datetime(2026, 9, 1)
        eventos = [(base.replace(hour=0), 1.0), (base.replace(hour=6), 0.2)]
        preamares, baixamares = classificar_extremos(eventos)
        self.assertEqual(len(preamares), 1)
        self.assertEqual(len(baixamares), 1)

    def test_plo_total_nao_classifica_nada(self):
        # Três valores iguais: nenhum é claramente pico nem vale — os três
        # empatam com seus vizinhos dos dois lados. Preferir não classificar a
        # adivinhar qual é o extremo.
        base = datetime(2026, 9, 1)
        eventos = [
            (base.replace(hour=0), 1.0),
            (base.replace(hour=1), 1.0),
            (base.replace(hour=2), 1.0),
        ]
        preamares, baixamares = classificar_extremos(eventos)
        self.assertEqual(len(preamares) + len(baixamares), 0)


class TesteFormatarNuncaEmiteAltura(unittest.TestCase):
    def test_formatar_so_tem_a_chave_quando(self):
        pontos = [(datetime(2026, 9, 1, 4, 28), 1.2895471327770707)]
        saida = formatar(pontos)
        self.assertEqual(saida, [{"quando": "2026-09-01T04:28"}])
        self.assertNotIn("altura_m", saida[0])

    def test_montar_nao_vaza_altura_em_nenhum_registro(self):
        pontos = [(datetime(2026, 9, 1, 4, 28), 1.29)]
        dados = montar(pontos, pontos)
        texto = str(dados)
        self.assertNotIn("altura_m", texto)
        self.assertNotIn("1.29", texto)

    def test_meta_avisa_datum_ibge_e_carater_interino(self):
        dados = montar([], [])
        aviso = dados["_meta"]["aviso"]
        self.assertIn("IBGE", aviso)
        self.assertIn("INTERINO", aviso)
        self.assertEqual(dados["porto"], "Itajaí")


if __name__ == "__main__":
    unittest.main()
