#!/usr/bin/env python3
"""Testes do analisador da página de chuvas da Defesa Civil de Itajaí.

O HTML e os NÚMEROS abaixo são os do site no ar, colhidos em 30/08/2026 pela
`sonda_chuva.py` rodando na VPS. Escrever analisador contra HTML imaginado já
custou caro neste projeto duas vezes — a tábua de maré era montada em
JavaScript, e o título das estações mora dentro de um <header>.

    python3 scripts/teste_coleta_chuva.py
"""

import unittest

from coleta_chuva import incoerencias, parse

# Recorte fiel: mesma aninhagem da página de níveis, rótulos e valores reais.
PAGINA = """
<html><body>
<h1>Chuvas</h1>
<ul class="cards">
<li class="card point">
    <header>
        <h2>DC-09 Ribeirão da Murta - Ponte da Rua Lidia Puel Peixer</h2>
    </header>
    <div class="content">
        <ul class="current-telemetria">
            <li><span class="label">Chuva nos últimos 10 minutos: </span> 0,00 mm</li>
            <li>
                <span class="label">Data e hora da medição: </span>
                30/08/2026 18:10                                  </li>
            <li><span class="label">Chuva acumulada 1h: </span> 0,40 mm</li>
            <li><span class="label">Chuva acumulada 12h: </span> 39,60 mm</li>
            <li><span class="label">Chuva acumulada 24h: </span> 39,60 mm</li>
            <li><span class="label">Chuva acumulada 48h: </span> 41,40 mm</li>
        </ul>
        <div class="chart-telemetria"><canvas id="chart-9-tel"></canvas></div>
    </div>
</li>
<li class="card point">
    <header><h2>Brusque Estação Guarani</h2></header>
    <div class="content"><ul class="current-telemetria">
        <li><span class="label">Chuva nos últimos 10 minutos: </span> 0,20 mm</li>
        <li><span class="label">Data e hora da medição: </span> 30/08/2026 18:15</li>
        <li><span class="label">Chuva acumulada 1h: </span> 0,00 mm</li>
        <li><span class="label">Chuva acumulada 12h: </span> 0,00 mm</li>
        <li><span class="label">Chuva acumulada 24h: </span> 0,00 mm</li>
        <li><span class="label">Chuva acumulada 48h: </span> 0,00 mm</li>
    </ul></div>
</li>
<li class="card point">
    <header><h2>Blumenau</h2></header>
    <div class="content"><ul class="current-telemetria"></ul></div>
</li>
<li class="card point">
    <header><h2>Rio do Sul Estação MKS</h2></header>
    <div class="content"><ul class="current-telemetria">
        <li><span class="label">Chuva nos últimos 10 minutos: </span> 0,00 mm</li>
        <li><span class="label">Data e hora da medição: </span> 30/08/2026 17:55</li>
        <li><span class="label">Chuva acumulada 1h: </span> 0,00 mm</li>
        <li><span class="label">Chuva acumulada 12h: </span> 0,00 mm</li>
        <li><span class="label">Chuva acumulada 24h: </span> 0,00 mm</li>
        <li><span class="label">Chuva acumulada 48h: </span> 0,00 mm</li>
    </ul></div>
</li>
</ul>
</body></html>
"""


def por_titulo(leituras, prefixo):
    return next(l for l in leituras if l["estacao"].startswith(prefixo))


class TestParse(unittest.TestCase):
    def setUp(self):
        self.leituras = parse(PAGINA)

    def test_le_as_estacoes_com_dado(self):
        """Blumenau aparece na página mas vem vazia — não vira leitura falsa."""
        titulos = [l["estacao"] for l in self.leituras]
        self.assertNotIn("Blumenau", titulos)
        self.assertEqual(len(self.leituras), 3)

    def test_valores_e_janelas_da_fonte(self):
        dc9 = por_titulo(self.leituras, "DC-09")
        self.assertEqual(dc9["mm"], {
            "min10": 0.0, "h1": 0.4, "h12": 39.6, "h24": 39.6, "h48": 41.4,
        })

    def test_nao_ha_janela_de_6h(self):
        """A fonte não publica 6 h, e estimar suporia chuva constante."""
        for l in self.leituras:
            self.assertNotIn("h6", l["mm"])

    def test_horario_da_medicao(self):
        self.assertEqual(por_titulo(self.leituras, "DC-09")["medido_em"],
                         "2026-08-30T18:10:00")

    def test_liga_a_estacao_a_cidade(self):
        self.assertEqual(por_titulo(self.leituras, "Rio do Sul")["cidade"], "rio-do-sul")
        self.assertEqual(por_titulo(self.leituras, "Brusque")["cidade"], "brusque")

    def test_nome_diferente_do_da_pagina_de_niveis(self):
        """
        Na página de chuva a estação de Brusque se chama "Brusque Estação
        Guarani"; na de níveis, só "Brusque". Se o casamento fosse por título
        exato, a chuva de Brusque ficaria órfã.
        """
        self.assertEqual(por_titulo(self.leituras, "Brusque")["rio"], "itajai-mirim")


class TestCoerencia(unittest.TestCase):
    def test_leitura_encaixada_e_coerente(self):
        dc9 = por_titulo(parse(PAGINA), "DC-09")
        self.assertTrue(dc9["coerente"], dc9["incoerencias"])

    def test_o_caso_real_da_estacao_guarani(self):
        """
        0,20 mm nos últimos 10 min e 0,00 mm em 1 h é impossível: os 10 minutos
        estão DENTRO da hora. Zero ali significa "sem dado", e mostrar 0 mm ao
        lado de uma vizinha com 39 mm manda a pessoa para o lado errado.
        """
        guarani = por_titulo(parse(PAGINA), "Brusque")
        self.assertFalse(guarani["coerente"])
        self.assertIn("min10=0.2 mm > h1=0 mm", guarani["incoerencias"])

    def test_zeros_coerentes_passam(self):
        """Não chover de verdade não é inconsistência."""
        rds = por_titulo(parse(PAGINA), "Rio do Sul")
        self.assertTrue(rds["coerente"], rds["incoerencias"])

    def test_janela_ausente_nao_conta_como_zero(self):
        self.assertEqual(incoerencias({"min10": 5.0, "h1": None, "h12": 30.0}), [])

    def test_arredondamento_da_fonte_nao_vira_alarme(self):
        """0,05 mm de diferença é passo do balde, não contradição."""
        self.assertEqual(incoerencias({"h1": 10.02, "h12": 10.0}), [])
        self.assertEqual(len(incoerencias({"h1": 10.5, "h12": 10.0})), 1)

    def test_queda_entre_janelas_longas_e_apontada(self):
        problemas = incoerencias({"h1": 1.0, "h12": 40.0, "h24": 12.0, "h48": 50.0})
        self.assertEqual(problemas, ["h12=40 mm > h24=12 mm"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
