#!/usr/bin/env python3
"""Testes do analisador da página de níveis da Defesa Civil de Itajaí.

O HTML abaixo é o do site no ar, conferido em 30/08/2026. O parser anterior
caminhava pelos irmãos do <h2> e lia zero estações, porque o título fica dentro
de um <header> e os valores são irmãos DESSE header. Estes casos existem para
que essa regressão não volte em silêncio — um coletor que devolve lista vazia
numa noite de chuva não avisa ninguém.

    python3 scripts/teste_coleta_niveis.py
"""

import json
import sys
import tempfile
import types
import unittest
from datetime import datetime, timedelta
from pathlib import Path
from unittest import mock

import coleta_niveis

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


class TestChuvaFalhaVersusAusencia(unittest.TestCase):
    """
    `chuva: []` significava duas coisas ao mesmo tempo: "a fonte não publica
    pluviômetro" e "não conseguimos buscar". A tela mostrava as duas igual — e,
    no meio de uma chuva, a segunda aparecendo como a primeira lê-se como "não
    está chovendo". A marca `chuva_ok` separa os dois casos.
    """

    def test_falha_na_coleta_devolve_lista_vazia_e_marca_falso(self):
        with mock.patch.dict(sys.modules, {"coleta_chuva": None}):
            chuva, ok = coleta_niveis.baixar_chuva()
        self.assertEqual(chuva, [])
        self.assertFalse(ok, "falha tem de vir marcada, não apenas vazia")

    def test_coleta_boa_devolve_marca_verdadeira(self):
        falso = types.ModuleType("coleta_chuva")
        falso.URL = "http://exemplo"
        falso.parse = lambda _html: [{"estacao": "P-1", "cidade": "itajai"}]
        with mock.patch.dict(sys.modules, {"coleta_chuva": falso}), \
             mock.patch.object(coleta_niveis, "espera_turno", lambda: None), \
             mock.patch("comum.baixar", lambda *a, **k: "<html></html>"):
            chuva, ok = coleta_niveis.baixar_chuva()
        self.assertEqual(len(chuva), 1)
        self.assertTrue(ok)

    def test_fonte_sem_pluviometro_nenhum_nao_e_falha(self):
        """Lista vazia com a marca verdadeira é 'não há aparelho', e é legítimo."""
        falso = types.ModuleType("coleta_chuva")
        falso.URL = "http://exemplo"
        falso.parse = lambda _html: []
        with mock.patch.dict(sys.modules, {"coleta_chuva": falso}), \
             mock.patch.object(coleta_niveis, "espera_turno", lambda: None), \
             mock.patch("comum.baixar", lambda *a, **k: "<html></html>"):
            chuva, ok = coleta_niveis.baixar_chuva()
        self.assertEqual(chuva, [])
        self.assertTrue(ok, "fonte vazia é resposta, não falha")


class TestPaginaParcial(unittest.TestCase):
    """
    `if not leituras` só pega o caso de ZERO estação. Caindo de catorze para
    duas, a coleta seguia, publicava, e as doze sumiam da tela como se não
    existissem. O vigia detecta, mas roda de hora em hora enquanto a coleta roda
    a cada quinze minutos: três de cada quatro coletas nunca são olhadas.
    """

    def escrever_ultimo(self, titulos):
        coleta_niveis.ULTIMO.parent.mkdir(parents=True, exist_ok=True)
        coleta_niveis.ULTIMO.write_text(json.dumps(
            {"leituras": [{"estacao": t, "nivel_m": 1.0} for t in titulos]}), encoding="utf-8")

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        alvo = Path(self.tmp.name) / "ultimo.json"
        patch = mock.patch.object(coleta_niveis, "ULTIMO", alvo)
        patch.start()
        self.addCleanup(patch.stop)

    def test_estacao_que_sumiu_e_nomeada(self):
        self.escrever_ultimo(["DC-01", "DC-02", "DC-10"])
        agora = coleta_niveis.estacoes_do_ultimo()
        sumidas = sorted(agora - {"DC-01"})
        self.assertEqual(sumidas, ["DC-02", "DC-10"])

    def test_primeira_rodada_nao_acusa_nada(self):
        """Sem arquivo anterior não há base de comparação, e isso não é problema."""
        self.assertEqual(coleta_niveis.estacoes_do_ultimo(), set())

    def test_arquivo_ilegivel_nao_derruba_a_coleta(self):
        coleta_niveis.ULTIMO.write_text("{ isto não é json", encoding="utf-8")
        self.assertEqual(coleta_niveis.estacoes_do_ultimo(), set())

    def test_arquivo_sem_leituras_nao_derruba(self):
        coleta_niveis.ULTIMO.write_text(json.dumps({"coletado_em": "x"}), encoding="utf-8")
        self.assertEqual(coleta_niveis.estacoes_do_ultimo(), set())

    def test_estacao_nova_nao_conta_como_sumida(self):
        self.escrever_ultimo(["DC-01"])
        sumidas = sorted(coleta_niveis.estacoes_do_ultimo() - {"DC-01", "DC-99"})
        self.assertEqual(sumidas, [], "estação a mais é ganho, não perda")


class TestChuvaDeSCEntraNaLista(unittest.TestCase):
    """
    O coletor de SC existia gravando um arquivo que ninguém lia — chuva colhida
    e nunca mostrada. Estes casos travam a ligação: ela tem de entrar na mesma
    lista que o site e o bot leem.
    """

    def test_as_duas_fontes_convivem_na_mesma_lista(self):
        falso = types.ModuleType("coleta_chuva_sc")
        falso.baixar_estacoes = lambda: []
        falso.converter = lambda _e: ([{"estacao": "DCSC-00026 SDC-SC Blumenau",
                                        "cidade": "blumenau", "mm": {"h24": 19.4}}], [])
        with mock.patch.dict(sys.modules, {"coleta_chuva_sc": falso}):
            de_sc = coleta_niveis.baixar_chuva_sc()
        self.assertEqual(len(de_sc), 1)
        self.assertEqual(de_sc[0]["cidade"], "blumenau")

    def test_falha_em_sc_nao_derruba_a_coleta(self):
        with mock.patch.dict(sys.modules, {"coleta_chuva_sc": None}):
            self.assertEqual(coleta_niveis.baixar_chuva_sc(), [])

    def test_o_codigo_dcsc_evita_colisao_de_nome(self):
        """
        Sem o código na frente, "SDC-SC Brusque" e a "Brusque Estação Guarani"
        da outra fonte poderiam se confundir na tela, que agrupa por cidade.
        """
        falso = types.ModuleType("coleta_chuva_sc")
        falso.baixar_estacoes = lambda: []
        falso.converter = lambda _e: ([{"estacao": "DCSC-00019 SDC-SC Brusque",
                                        "cidade": "brusque", "mm": {"h24": 60.4}}], [])
        with mock.patch.dict(sys.modules, {"coleta_chuva_sc": falso}):
            de_sc = coleta_niveis.baixar_chuva_sc()
        outra = {"estacao": "Brusque Estação Guarani", "cidade": "brusque"}
        nomes = {l["estacao"] for l in de_sc} | {outra["estacao"]}
        self.assertEqual(len(nomes), 2, "as duas estações de Brusque têm de ser distintas")


class TestZeroDeSensorParado(unittest.TestCase):
    """Pluviômetro preso em zero numa cidade que chove vira suspeito, sem sumir."""

    def _mm(self, **kw):
        base = {"min10": None, "h1": None, "h12": None, "h24": None, "h48": None}
        base.update(kw)
        return base

    def test_zero_com_outra_estacao_chovendo_vira_suspeito(self):
        chuva = [
            {"cidade": "brusque", "estacao": "Guarani", "mm": self._mm(h1=0.0, h24=0.0), "coerente": True},
            {"cidade": "brusque", "estacao": "DCSC Brusque", "mm": self._mm(h1=1.0, h24=8.2), "coerente": True},
        ]
        self.assertEqual(coleta_niveis.marcar_zero_suspeito(chuva), 1)
        self.assertFalse(chuva[0]["coerente"])
        self.assertTrue(any("sensor parado" in p for p in chuva[0]["incoerencias"]))
        self.assertTrue(chuva[1]["coerente"], "a estação que mede chuva fica intacta")

    def test_cidade_seca_de_verdade_nao_e_marcada(self):
        chuva = [
            {"cidade": "taio", "estacao": "A", "mm": self._mm(h1=0.0, h24=0.0), "coerente": True},
            {"cidade": "taio", "estacao": "B", "mm": self._mm(h24=0.0), "coerente": True},
        ]
        self.assertEqual(coleta_niveis.marcar_zero_suspeito(chuva), 0)
        self.assertTrue(all(l["coerente"] for l in chuva))

    def test_estacao_com_chuva_nunca_e_marcada(self):
        chuva = [{"cidade": "x", "estacao": "A", "mm": self._mm(h24=5.0), "coerente": True}]
        self.assertEqual(coleta_niveis.marcar_zero_suspeito(chuva), 0)


class TestSerieDeChuva(unittest.TestCase):
    """
    A chuva vivia só no ultimo.json, sobrescrito a cada rodada: quinze minutos
    depois, o dado tinha sumido. Com o nível de montante explicando pouco o de
    jusante (r² = 0,21), a chuva é a candidata mais forte a preditor — e
    preditor se constrói com série, que só existe se for guardada desde já.
    """

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        p = mock.patch.object(coleta_niveis, "SERIE", Path(self.tmp.name))
        p.start()
        self.addCleanup(p.stop)

    def chuva(self, estacao="P-1", medido="2026-08-31T17:49:23", h24=19.4, coerente=True):
        return {"estacao": estacao, "rio": None, "cidade": "blumenau", "medido_em": medido,
                "mm": {"min10": None, "h1": 1.0, "h12": None, "h24": h24, "h48": None},
                "coerente": coerente}

    def nivel(self, estacao="Brusque", medido="2026-08-31T18:05:00", m=3.29):
        return {"estacao": estacao, "rio": "itajai-mirim", "cidade": "brusque",
                "medido_em": medido, "nivel_m": m}

    def arquivos(self):
        return sorted(p.name for p in Path(self.tmp.name).iterdir())

    def test_chuva_e_nivel_vao_para_arquivos_SEPARADOS(self):
        """Grandezas diferentes, campos diferentes: juntar obrigaria a adivinhar."""
        coleta_niveis.acumular([self.nivel()])
        coleta_niveis.acumular([self.chuva()], prefixo="chuva-")
        self.assertEqual(self.arquivos(), ["2026-08.ndjson", "chuva-2026-08.ndjson"])

    def test_a_linha_de_chuva_guarda_as_janelas(self):
        coleta_niveis.acumular([self.chuva()], prefixo="chuva-")
        linha = json.loads((Path(self.tmp.name) / "chuva-2026-08.ndjson").read_text().strip())
        self.assertEqual(linha["mm"]["h24"], 19.4)
        self.assertNotIn("nivel_m", linha, "chuva não tem nível")

    def test_a_linha_de_nivel_nao_ganha_campo_de_chuva(self):
        coleta_niveis.acumular([self.nivel()])
        linha = json.loads((Path(self.tmp.name) / "2026-08.ndjson").read_text().strip())
        self.assertEqual(linha["nivel_m"], 3.29)
        self.assertNotIn("mm", linha)

    def test_leitura_incoerente_e_guardada_MARCADA(self):
        """
        Descartar calado viraria "não choveu" para quem ler a série meses
        depois. É o mesmo critério da tela.
        """
        coleta_niveis.acumular([self.chuva(h24=0.0, coerente=False)], prefixo="chuva-")
        linha = json.loads((Path(self.tmp.name) / "chuva-2026-08.ndjson").read_text().strip())
        self.assertFalse(linha["coerente"])

    def test_a_mesma_medicao_nao_entra_duas_vezes(self):
        self.assertEqual(coleta_niveis.acumular([self.chuva()], prefixo="chuva-"), (1, 0))
        self.assertEqual(coleta_niveis.acumular([self.chuva()], prefixo="chuva-"), (0, 1))

    def test_sem_carimbo_nao_vira_linha(self):
        c = self.chuva(); c["medido_em"] = None
        self.assertEqual(coleta_niveis.acumular([c], prefixo="chuva-"), (0, 0))
        self.assertEqual(self.arquivos(), [])

    def test_a_chuva_nao_polui_a_serie_de_nivel(self):
        """Sem prefixo elas cairiam no mesmo arquivo e o leitor teria de adivinhar."""
        coleta_niveis.acumular([self.nivel()])
        coleta_niveis.acumular([self.chuva(medido="2026-08-31T18:05:00")], prefixo="chuva-")
        do_nivel = (Path(self.tmp.name) / "2026-08.ndjson").read_text().strip().splitlines()
        self.assertEqual(len(do_nivel), 1)
        self.assertIn("nivel_m", do_nivel[0])


class TestCompactarComPrefixo(unittest.TestCase):
    """
    O mês vem do FIM do nome. Com a série de chuva o stem virou `chuva-2026-08`,
    e comparar isso com `2026-08` como texto dá sempre "maior" — "c" vem depois
    de "2" —, então nenhum arquivo de chuva jamais seria compactado, em silêncio.
    """

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.dir = Path(self.tmp.name)
        p = mock.patch.object(coleta_niveis, "SERIE", self.dir)
        p.start()
        self.addCleanup(p.stop)
        hoje = datetime.now()
        self.atual = hoje.strftime("%Y-%m")
        self.passado = (hoje.replace(day=1) - timedelta(days=1)).strftime("%Y-%m")

    def criar(self, *nomes):
        for n in nomes:
            (self.dir / n).write_text('{"estacao":"x","medido_em":"2020-01-01T00:00:00"}\n')

    def test_compacta_as_duas_series_do_mes_fechado(self):
        self.criar(f"{self.passado}.ndjson", f"chuva-{self.passado}.ndjson")
        self.assertEqual(coleta_niveis.compactar(), 2)
        sobrou = sorted(p.name for p in self.dir.iterdir())
        self.assertEqual(sobrou, [f"{self.passado}.ndjson.gz", f"chuva-{self.passado}.ndjson.gz"])

    def test_o_mes_corrente_fica_intocado_nas_duas(self):
        self.criar(f"{self.atual}.ndjson", f"chuva-{self.atual}.ndjson")
        self.assertEqual(coleta_niveis.compactar(), 0)

    def test_nome_sem_mes_no_fim_e_ignorado(self):
        """Arquivo estranho na pasta não vira lixo compactado."""
        self.criar("qualquer-coisa.ndjson")
        self.assertEqual(coleta_niveis.compactar(), 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
