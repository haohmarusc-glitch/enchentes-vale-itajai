#!/usr/bin/env python3
"""Testes do analisador da tábua de maré.

A página real da Defesa Civil de Itajaí não pôde ser conferida quando este
analisador foi escrito. Estes casos cobrem os três formatos que uma página
dessas costuma ter, e servem de rede para quando alguém ajustar o parser depois
de ver o site no ar.

    python3 scripts/teste_coleta_mares.py
"""

import unittest

from coleta_mares import analisar, texto_da_pagina

TABELA = """
<html><body><h1>Tábua de Marés</h1><h2>Porto de Itajaí — 12/07/2026</h2>
<table><tr><th>Preamar</th><th>Altura</th></tr>
<tr><td>03:12</td><td>1,20 m</td></tr><tr><td>15:44</td><td>1,10 m</td></tr></table>
<table><tr><th>Baixa-mar</th><th>Altura</th></tr>
<tr><td>09:30</td><td>0,30 m</td></tr><tr><td>21:58</td><td>0,25 m</td></tr></table>
</body></html>
"""

LISTA = """
<html><body><p>Marés de 12/07/2026 - Itajaí</p>
<ul><li>PREAMAR 03:12 - 1.20m</li><li>BAIXA-MAR 09:30 - 0.30m</li>
<li>PREAMAR 15:44 - 1.10m</li><li>BAIXA-MAR 21:58 - 0.25m</li></ul></body></html>
"""

SEM_ROTULO = """
<html><body><div>Tabua de mare 12/07/2026</div>
<div>03:12  1,20</div><div>09:30  0,30</div><div>15:44  1,10</div><div>21:58  0,25</div>
<div>Nivel do Rio: 5,65 m</div></body></html>
"""


class TesteAnalisador(unittest.TestCase):
    def analisa(self, html):
        return analisar(texto_da_pagina(html))

    def test_tabela_com_cabecalho(self):
        pre, baixa, dia = self.analisa(TABELA)
        self.assertEqual(dia, "2026-07-12")
        self.assertEqual([e["quando"] for e in pre], ["2026-07-12T03:12", "2026-07-12T15:44"])
        self.assertEqual([e["quando"] for e in baixa], ["2026-07-12T09:30", "2026-07-12T21:58"])

    def test_lista_com_rotulo_na_linha(self):
        pre, baixa, _ = self.analisa(LISTA)
        self.assertEqual(len(pre), 2)
        self.assertEqual(len(baixa), 2)
        self.assertAlmostEqual(pre[0]["altura_m"], 1.20)

    def test_sem_rotulo_separa_pela_altura(self):
        pre, baixa, _ = self.analisa(SEM_ROTULO)
        self.assertEqual([e["quando"] for e in pre], ["2026-07-12T03:12", "2026-07-12T15:44"])
        self.assertEqual([e["quando"] for e in baixa], ["2026-07-12T09:30", "2026-07-12T21:58"])

    def test_nivel_de_rio_nao_vira_mare(self):
        """5,65 m está fora da faixa de maré do porto — não pode entrar na tábua."""
        pre, baixa, _ = self.analisa(SEM_ROTULO)
        alturas = [e["altura_m"] for e in pre + baixa]
        self.assertNotIn(5.65, alturas)

    def test_pagina_sem_data_nao_gera_entrada(self):
        """Sem data não dá para montar o horário: melhor nada que um horário errado."""
        pre, baixa, dia = self.analisa("<html><body><li>PREAMAR 03:12 - 1.20m</li></body></html>")
        self.assertIsNone(dia)
        self.assertEqual(pre, [])
        self.assertEqual(baixa, [])

    def test_pagina_irreconhecivel_devolve_vazio(self):
        pre, baixa, _ = self.analisa("<html><body><p>Serviço indisponível</p></body></html>")
        self.assertEqual(pre, [])
        self.assertEqual(baixa, [])


if __name__ == "__main__":
    unittest.main(verbosity=2)
