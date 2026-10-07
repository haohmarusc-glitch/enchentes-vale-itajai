#!/usr/bin/env python3
"""Testes do analisador da chuva da Defesa Civil de Itajaí.

Duas páginas: a NOVA (portal `monitoramento.defesacivil.itajai.sc.gov.br`,
captura real de 07/10/2026 em `data/brutos/itajai-portal-2026-10-07/`) e a
ANTIGA, que só serve para reler capturas — o HTML e os NÚMEROS de `PAGINA` são os
do site antigo, colhidos em 30/08/2026 pela `sonda_chuva.py` rodando na VPS. Escrever analisador contra HTML imaginado já
custou caro neste projeto duas vezes — a tábua de maré era montada em
JavaScript, e o título das estações mora dentro de um <header>.

    python3 scripts/teste_coleta_chuva.py
"""

import html as _html
import json
import unittest
from pathlib import Path

from coleta_chuva import (URL, URL_ANTIGA, FonteInvalida, incoerencias, parse,
                          parse_pagina_antiga)

BRUTOS = Path(__file__).resolve().parent.parent / "data" / "brutos" / "itajai-portal-2026-10-07"
PAGINA_NOVA = BRUTOS / "itajai-portal-chuvas-municipio-1.html"
CASCA = BRUTOS / "defesacivil-itajai-casca-spa.html"

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
    """A página ANTIGA, relida por `parse_pagina_antiga`."""

    def setUp(self):
        self.leituras = parse_pagina_antiga(PAGINA)

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


def _pagina_de(dados: dict) -> str:
    return '<div id="app" data-page="' + _html.escape(json.dumps(dados)) + '"></div>'


class TestPortalNovo(unittest.TestCase):
    """A captura real de 07/10/2026 14h49 UTC."""

    def setUp(self):
        self.texto = PAGINA_NOVA.read_text(encoding="utf-8")
        self.leituras = parse(self.texto)

    def test_le_a_pagina_nova_e_nao_a_antiga(self):
        self.assertTrue(URL.startswith("https://monitoramento.defesacivil.itajai.sc.gov.br/"))
        self.assertNotEqual(URL, URL_ANTIGA)

    def test_as_doze_estacoes_com_coordenada_entram(self):
        """A DC-00 ganhou coordenada no cadastro por decisão do Jefferson (07/10/2026)."""
        self.assertEqual(len(self.leituras), 12)
        self.assertEqual(sorted(l["estacao"][:5] for l in self.leituras),
                         [f"DC-{i:02d}" for i in range(0, 12)])

    def test_dc00_entra_pela_coordenada_cadastrada(self):
        dc0 = por_titulo(self.leituras, "DC-00")
        self.assertEqual(dc0["estacao"], "DC-00 Defesa Civil de Itajaí")
        self.assertEqual(dc0["cidade"], "itajai")

    def test_estacao_sem_coordenada_no_cadastro_fica_de_fora(self):
        """Nome igual não prova estação igual: sem coordenada dos dois lados, a estação fica de fora."""
        from unittest import mock
        import coleta_chuva
        cadastro = coleta_chuva._cadastro_por_codigo()
        sem = {**cadastro, "DC-00": {k: v for k, v in cadastro["DC-00"].items() if k not in ("lat", "lon")}}
        with mock.patch.object(coleta_chuva, "_cadastro_por_codigo", return_value=sem):
            leituras = parse(self.texto)
        self.assertFalse(any(l["estacao"].startswith("DC-00") for l in leituras))
        self.assertEqual(len(leituras), 11)

    def test_titulo_igual_ao_das_series_antigas(self):
        """O título vem do cadastro — o mesmo das séries até 19/09 — e a série não quebra."""
        dc11 = por_titulo(self.leituras, "DC-11")
        self.assertEqual(dc11["estacao"], "DC-11 Rio Itajaí-Açú – Santa Regina (Volta de Cima)")
        self.assertEqual(dc11["cidade"], "itajai")

    def test_valores_em_mm_e_janelas(self):
        dc1 = por_titulo(self.leituras, "DC-01")
        self.assertEqual(dc1["mm"], {"min10": 0.0, "h1": 0.0, "h12": 3.6, "h24": 26.6, "h48": 57.6})
        self.assertTrue(dc1["coerente"])

    def test_horario_em_brasilia_sem_fuso(self):
        """14:31:36Z no portal vira 11:31:36, sem offset."""
        self.assertEqual(por_titulo(self.leituras, "DC-01")["medido_em"], "2026-10-07T11:31:36")
        for l in self.leituras:
            self.assertNotIn("+", l["medido_em"])

    def test_a_unidade_e_mm_conferida_pela_serie(self):
        """A soma dos incrementos de 10 min bate com o acumulado de 12 h."""
        from coleta_itajai_portal import carga
        for e in carga(self.texto)["props"]["estacoes"]:
            soma = sum(p["chuva_mm"] or 0 for p in e["serie_12_h"])
            self.assertLessEqual(abs(soma - e["chuva_12_h_mm"]), 0.41, e["codigo"])


class TestRecusaMesmoComStatus200(unittest.TestCase):
    """O furo de set–out/2026: casca vazia com 200 virava 'sem pluviômetro'."""

    def setUp(self):
        from coleta_itajai_portal import carga
        self.dados = carga(PAGINA_NOVA.read_text(encoding="utf-8"))

    def test_casca_spa_do_endereco_antigo_e_falha(self):
        with self.assertRaises(FonteInvalida):
            parse(CASCA.read_text(encoding="utf-8"))

    def test_resposta_vazia_e_falha(self):
        for corpo in ("", "   ", "<html></html>"):
            with self.subTest(corpo=corpo), self.assertRaises(FonteInvalida):
                parse(corpo)

    def test_json_solto_nao_e_a_pagina(self):
        with self.assertRaises(FonteInvalida):
            parse(json.dumps({"estacoes": []}))

    def test_outro_municipio_e_falha(self):
        self.dados["props"]["municipioId"] = 2
        with self.assertRaises(FonteInvalida):
            parse(_pagina_de(self.dados))

    def test_lista_de_estacoes_vazia_e_falha(self):
        self.dados["props"]["estacoes"] = []
        with self.assertRaises(FonteInvalida):
            parse(_pagina_de(self.dados))

    def test_esquema_sem_as_janelas_e_falha(self):
        for e in self.dados["props"]["estacoes"]:
            del e["chuva_12_h_mm"]
        with self.assertRaises(FonteInvalida):
            parse(_pagina_de(self.dados))

    def test_valor_que_nao_e_chuva_recusa_a_estacao(self):
        e = next(x for x in self.dados["props"]["estacoes"] if x["codigo"] == "DC01")
        e["chuva_1_h_mm"] = "0,0"
        leituras = parse(_pagina_de(self.dados))
        self.assertFalse(any(l["estacao"].startswith("DC-01") for l in leituras))
        self.assertEqual(len(leituras), 11)

    def test_sem_dados_vira_ausente_nunca_zero(self):
        e = next(x for x in self.dados["props"]["estacoes"] if x["codigo"] == "DC02")
        e["qualidade"]["chuva_48_h_mm"]["estado"] = "sem_dados"
        dc2 = por_titulo(parse(_pagina_de(self.dados)), "DC-02")
        self.assertIsNone(dc2["mm"]["h48"])

    def test_estacao_deslocada_e_recusada(self):
        e = next(x for x in self.dados["props"]["estacoes"] if x["codigo"] == "DC03")
        e["latitude"] += 0.01  # ~1,1 km
        leituras = parse(_pagina_de(self.dados))
        self.assertFalse(any(l["estacao"].startswith("DC-03") for l in leituras))

    def test_carimbos_diferentes_valem_pelo_mais_antigo(self):
        e = next(x for x in self.dados["props"]["estacoes"] if x["codigo"] == "DC04")
        e["qualidade"]["chuva_48_h_mm"]["medido_em"] = "2026-10-07T09:00:00+00:00"
        self.assertEqual(por_titulo(parse(_pagina_de(self.dados)), "DC-04")["medido_em"],
                         "2026-10-07T06:00:00")

    def test_coleta_niveis_publica_o_endereco_novo(self):
        import coleta_niveis
        self.assertEqual(coleta_niveis.URL_CHUVA_ITAJAI, URL)

    def test_falha_do_parse_vira_chuva_ok_falso(self):
        import sys
        from unittest import mock
        import coleta_niveis
        with mock.patch.object(coleta_niveis, "espera_turno", lambda: None), \
             mock.patch("comum.baixar", lambda *a, **k: CASCA.read_text(encoding="utf-8")):
            chuva, ok = coleta_niveis.baixar_chuva()
        self.assertEqual(chuva, [])
        self.assertFalse(ok, "casca vazia com 200 é falha da fonte, não ausência de pluviômetro")


class TestCadastro(unittest.TestCase):
    """
    Estações que só existem na página de chuvas.

    A página de níveis tem 13 estações; a de chuvas tem 14. A extra é a DC-00,
    um pluviômetro puro na sede da Defesa Civil. Antes de ser cadastrada, ela
    era coletada e descartada em silêncio — 28 mm em 24 h que não contavam
    para cidade nenhuma.
    """

    def test_dc00_e_de_itajai_e_nao_tem_rio(self):
        from comum import classificar_estacao
        rio, cidade = classificar_estacao("DC-00 Defesa Civil de Itajaí")
        self.assertEqual(cidade, "itajai")
        self.assertIsNone(rio, "DC-00 não tem régua, só pluviômetro")

    def test_guarani_e_a_mesma_brusque_da_pagina_de_niveis(self):
        from comum import classificar_estacao
        self.assertEqual(classificar_estacao("Brusque Estação Guarani"),
                         classificar_estacao("Brusque"))

    def test_a_chuva_da_mks_continua_sendo_de_rio_do_sul(self):
        """
        09/09/2026: o NÍVEL da MKS deixou de ser coletado (é outra régua, zero
        ~0,17 m acima da Tito Buss da Asthon, dona das cotas), mas a CHUVA dela
        continua sendo chuva de Rio do Sul — chuva não tem zero de régua. O
        mapeamento fica; o corte é em coleta_itajai.REGUAS_NAO_COLETADAS.
        """
        from coleta_itajai import REGUAS_NAO_COLETADAS
        from comum import classificar_estacao
        self.assertEqual(classificar_estacao("Rio do Sul Estação MKS"), ("itajai-acu", "rio-do-sul"))
        self.assertIn("Rio do Sul Estação MKS", REGUAS_NAO_COLETADAS)
        self.assertEqual(classificar_estacao("Rio do Sul, Ponte Dom Tito Buss (Asthon)"),
                         ("itajai-acu", "rio-do-sul"))

    def test_pluviometro_nao_conta_como_regua(self):
        """
        A Guarani está no mesmo (rio, cidade) da régua de Brusque. Se contasse
        como régua, a cidade passaria a "ter duas" e a regra que recusa a cota
        da cidade onde há várias calaria o aviso no Itajaí-Mirim inteiro.
        """
        import json
        from comum import DADOS
        registro = json.loads((DADOS / "estacoes.json").read_text(encoding="utf-8"))
        reguas = [
            e for e in registro["estacoes_tempo_real"]
            if e.get("tipo") != "pluviometro"
            and (e.get("rio"), e.get("cidade")) == ("itajai-mirim", "brusque")
        ]
        self.assertEqual(len(reguas), 1, [e["titulo"] for e in reguas])


class TestCoerencia(unittest.TestCase):
    def test_leitura_encaixada_e_coerente(self):
        dc9 = por_titulo(parse_pagina_antiga(PAGINA), "DC-09")
        self.assertTrue(dc9["coerente"], dc9["incoerencias"])

    def test_o_caso_real_da_estacao_guarani(self):
        """
        0,20 mm nos últimos 10 min e 0,00 mm em 1 h é impossível: os 10 minutos
        estão DENTRO da hora. Zero ali significa "sem dado", e mostrar 0 mm ao
        lado de uma vizinha com 39 mm manda a pessoa para o lado errado.
        """
        guarani = por_titulo(parse_pagina_antiga(PAGINA), "Brusque")
        self.assertFalse(guarani["coerente"])
        self.assertIn("min10=0.2 mm > h1=0 mm", guarani["incoerencias"])

    def test_zeros_coerentes_passam(self):
        """Não chover de verdade não é inconsistência."""
        rds = por_titulo(parse_pagina_antiga(PAGINA), "Rio do Sul")
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
