#!/usr/bin/env python3
"""Testes do analisador da página de níveis da Defesa Civil de Itajaí.

O HTML abaixo é o do site no ar, conferido em 30/08/2026. O parser anterior
caminhava pelos irmãos do <h2> e lia zero estações, porque o título fica dentro
de um <header> e os valores são irmãos DESSE header. Estes casos existem para
que essa regressão não volte em silêncio — um coletor que devolve lista vazia
numa noite de chuva não avisa ninguém.

    python3 scripts/teste_coleta_niveis.py
"""

import unittest

from coleta_itajai import parse

# Recorte fiel da página, com a aninhagem real.
PAGINA = """
<html><body>
<h1>Nível dos Rios</h1>
<ul class="cards">
<li class="card point point-city-1" style="display: block;">
    <header>
        <h2>DC-01 Rio Itajaí-Açu - ICMBio/CEPSUL</h2>
    </header>
    <div class="content">
        <ul class="current-telemetria">
            <li>
                <span class="label">Nível do Rio: </span>
                1,39 m
            </li>
            <li>
                <span class="label">Data e hora da medição: </span>
                30/08/2026 15:51                                        </li>
        </ul>
        <div class="chart-telemetria"><canvas id="chart-2-tel"></canvas></div>
    </div>
</li>
<li class="card point point-city-1" style="display: block;">
    <header><h2>Blumenau</h2></header>
    <div class="content">
        <ul class="current-telemetria">
            <li><span class="label">Nível do Rio: </span> 5,65 m</li>
            <li><span class="label">Data e hora da medição: </span> 30/08/2026 15:00</li>
        </ul>
    </div>
</li>
<li class="card point">
    <header><h2>DC-09 Ribeirão da Murta - Ponte da Rua Lidia Puel Peixer</h2></header>
    <div class="content"><p>Estação sem leitura no momento.</p></div>
</li>
</ul>
</body></html>
"""


class TesteParse(unittest.TestCase):
    def setUp(self):
        self.leituras = parse(PAGINA)
        self.por_estacao = {l["estacao"]: l for l in self.leituras}

    def test_le_as_estacoes_com_leitura(self):
        self.assertEqual(len(self.leituras), 2)

    def test_o_nivel_sai_em_metros_com_virgula_decimal(self):
        self.assertAlmostEqual(self.por_estacao["Blumenau"]["nivel_m"], 5.65)
        dc01 = self.por_estacao["DC-01 Rio Itajaí-Açu - ICMBio/CEPSUL"]
        self.assertAlmostEqual(dc01["nivel_m"], 1.39)

    def test_pega_o_horario_da_medicao(self):
        self.assertEqual(self.por_estacao["Blumenau"]["medido_em"], "2026-08-30T15:00:00")

    def test_liga_a_estacao_a_cidade_do_projeto(self):
        self.assertEqual(self.por_estacao["Blumenau"]["cidade"], "blumenau")
        dc01 = self.por_estacao["DC-01 Rio Itajaí-Açu - ICMBio/CEPSUL"]
        self.assertEqual((dc01["rio"], dc01["cidade"]), ("itajai-acu", "itajai"))

    def test_estacao_sem_leitura_nao_vira_linha(self):
        self.assertNotIn("DC-09 Ribeirão da Murta - Ponte da Rua Lidia Puel Peixer",
                         self.por_estacao)

    def test_o_titulo_da_pagina_nao_vira_estacao(self):
        self.assertNotIn("Níveis dos Rios", self.por_estacao)

    def test_pagina_sem_estacoes_devolve_vazio(self):
        self.assertEqual(parse("<html><body><p>Indisponível</p></body></html>"), [])



class TestSemRede(unittest.TestCase):
    """
    Analisar HTML não pode exigir biblioteca de rede.

    Isto já era verdade por acidente — a CI não instalava `requests`, então
    qualquer import solto quebrava o teste. Agora a CI instala (o núcleo HTTP
    precisa dela), e a propriedade viraria invisível. Aqui ela é afirmada:
    quem só quer entender um HTML salvo não deveria precisar de rede nenhuma,
    e um import no topo do módulo transformaria falta de dependência em coleta
    silenciosamente morta.
    """

    def test_parse_funciona_com_requests_indisponivel(self):
        import subprocess
        import sys
        from pathlib import Path

        codigo = (
            "import sys; sys.modules['requests'] = None\n"
            "import coleta_itajai, coleta_chuva\n"
            "assert len(coleta_itajai.parse(open('/dev/stdin').read())) >= 1\n"
            "print('ok')\n"
        )
        r = subprocess.run(
            [sys.executable, "-c", codigo],
            input=PAGINA, capture_output=True, text=True,
            cwd=str(Path(__file__).resolve().parent),
        )
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("ok", r.stdout)


class TesteBlocoContaminado(unittest.TestCase):
    """
    O pior defeito que a auditoria achou nesta coleta.

    `bloco_da_estacao` sobe do <h2> até o <li> da estação. Quando a página não
    tem <li> nem <article>, ela cai para o avô — que pode ser o contêiner de
    TODAS as estações. Aí o texto do bloco tem várias leituras, o `search` acha
    a primeira e a copia para cada título.

    Medido antes do conserto: o DC-10 (Limoeiro), que estava em 5,21 m, saía
    com 1,39 m — o nível de uma régua de estuário. O aviso compararia esse
    1,39 com a cota de atenção de 8,00 m do Limoeiro e concluiria que está
    tudo normal, no meio da cheia.
    """

    PAGINA_SEM_LI = """<html><body><h1>Nível dos Rios</h1><div class="cards">
      <div class="card"><h2>DC-01 Rio Itajaí-Açu - ICMBio/CEPSUL</h2></div>
      <div class="card"><span class="label">Nível do Rio: </span> 1,39 m
         <span class="label">Data e hora da medição: </span> 30/08/2026 15:51</div>
      <div class="card"><h2>DC-10 Rio Itajaí-Mirim - Limoeiro</h2></div>
      <div class="card"><span class="label">Nível do Rio: </span> 5,21 m
         <span class="label">Data e hora da medição: </span> 30/08/2026 15:50</div>
    </div></body></html>"""

    def test_bloco_com_varias_leituras_nao_vira_leitura_nenhuma(self):
        leituras = parse(self.PAGINA_SEM_LI)
        self.assertEqual(leituras, [], "número errado com cara de certo é pior que nenhum")

    def test_nao_copia_o_nivel_de_uma_estacao_para_outra(self):
        por_estacao = {l["estacao"]: l["nivel_m"] for l in parse(self.PAGINA_SEM_LI)}
        self.assertNotIn(1.39, por_estacao.values())

    def test_a_pagina_normal_continua_sendo_lida(self):
        """A trava não pode custar a coleta que funciona."""
        leituras = parse(PAGINA)
        self.assertGreaterEqual(len(leituras), 2)
        por = {l["estacao"]: l["nivel_m"] for l in leituras}
        self.assertEqual(por["Blumenau"], 5.65)


class TesteFaixaPlausivel(unittest.TestCase):
    def uma(self, texto_nivel):
        html = ("<html><body><ul><li><h2>DC-10 Limoeiro</h2>"
                f'<span class="label">Nível do Rio: </span> {texto_nivel} '
                '<span class="label">Data e hora da medição: </span> 30/08/2026 15:50'
                "</li></ul></body></html>")
        return parse(html)

    def test_valor_absurdo_nao_entra(self):
        """9999,00 viraria alerta de inundação em todas as cidades."""
        self.assertEqual(self.uma("9999,00 m"), [])

    def test_zero_nao_entra(self):
        self.assertEqual(self.uma("0,00 m"), [])

    def test_nivel_normal_entra(self):
        leituras = self.uma("5,21 m")
        self.assertEqual(len(leituras), 1)
        self.assertEqual(leituras[0]["nivel_m"], 5.21)


if __name__ == "__main__":
    unittest.main(verbosity=2)
