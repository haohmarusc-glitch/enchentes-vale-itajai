#!/usr/bin/env python3
"""Testes do coletor do portal NOVO da Defesa Civil de Itajaí.

O que não pode falhar, e por que cada um está travado aqui:

* **Identidade por coordenada.** O cadastro registra que já houve REMANEJAMENTO
  de estação entre edições do Plano de Contingência (a DC-09 era "Ribeirão
  Ariribá" numa edição e "Ribeirão da Murta" na v17). Casar "DC01" com "DC-01"
  só por string aceitaria um código reaproveitado em OUTRO ponto como se fosse
  a mesma régua. Aqui uma régua deslocada é recusada.
* **Título do cadastro.** `estacao` é a chave de identidade do projeto inteiro
  (`regua_de`, memória do vigia, cotas por título, série). Montá-lo a partir do
  portal renomearia onze réguas de uma vez.
* **Fuso.** O portal publica UTC com offset; o repositório grava Brasília sem
  fuso. Confundir os dois já custou uma sessão inteira.
* **`consultadoEm` fora.** É o instante da consulta. Usá-lo rejuvenesceria uma
  leitura velha — a mentira exata que a idade existe para impedir.
* **Cotas do portal fora.** Quatro das onze divergem do Plano de Contingência
  v17 que o cadastro usa, e em duas o portal é MAIS BAIXO. Trocar cota é
  decisão do Jefferson com o documento na mão, não efeito colateral da coleta.

    python3 scripts/teste_coleta_itajai_portal.py
"""

import html as _html
import json
import unittest
from pathlib import Path

from coleta_itajai_portal import (TOLERANCIA_COORD_M, carga, coletar,
                                  distancia_m, para_brasilia, parse)
from comum import classificar_estacao, estacoes_tempo_real

RAIZ = Path(__file__).resolve().parent.parent
PAGINA_REAL = RAIZ / "data" / "brutos" / "itajai-portal-novo-2026-09-19.html"

#: A DC-01 como o portal a publicou em 19/09/2026 13h38 (captura real).
DC01 = {
    "id": 1,
    "codigo": "DC01",
    "nome": "Rio Itajaí-Açu - ICMBio/CEPSUL",
    "municipio_id": 1,
    "latitude": -26.90923,
    "longitude": -48.6516,
    "fonte": "Telemetria Itajaí",
    "medido_em": "2026-09-19T16:31:36.158000+00:00",
    "nivel_rio_m": 0.97,
    "qualidade": {"nivel_rio_m": {"estado": "atual",
                                  "medido_em": "2026-09-19T16:31:36.158000+00:00"}},
    "atencao_m": 1.21, "alerta_m": 1.61, "emergencia_m": 1.75,
}


def pagina_com(estacoes, consultado_em="2026-09-19T16:38:08+00:00"):
    """Um HTML mínimo no formato Inertia que o portal usa."""
    corpo = {"props": {"municipioId": 1, "consultadoEm": consultado_em,
                       "estacoes": estacoes}}
    attr = _html.escape(json.dumps(corpo, ensure_ascii=False), quote=True)
    return f'<html><body><div id="app" data-page="{attr}"></div></body></html>'


class TestCarga(unittest.TestCase):
    def test_le_o_data_page(self):
        d = carga(pagina_com([DC01]))
        self.assertEqual(d["props"]["estacoes"][0]["codigo"], "DC01")

    def test_pagina_sem_app_vira_vazio(self):
        # 404 ou página de manutenção: nenhuma leitura, e o vigia grita.
        self.assertEqual(carga("<html><body>Página não encontrada</body></html>"), {})
        self.assertEqual(parse("<html><body>404</body></html>"), [])

    def test_data_page_quebrado_nao_estoura(self):
        self.assertEqual(carga('<div id="app" data-page="{isso não é json"></div>'), {})


class TestFuso(unittest.TestCase):
    def test_utc_vira_brasilia_sem_fuso(self):
        # 16:31:36 UTC = 13:31:36 em Brasília (UTC-3), sem sufixo e sem microssegundos.
        self.assertEqual(para_brasilia("2026-09-19T16:31:36.158000+00:00"),
                         "2026-09-19T13:31:36")

    def test_sem_offset_vira_none(self):
        """Sem fuso declarado não dá para saber a idade — e assumir é inventar."""
        self.assertIsNone(para_brasilia("2026-09-19T16:31:36"))

    def test_lixo_vira_none(self):
        self.assertIsNone(para_brasilia("ontem de tarde"))
        self.assertIsNone(para_brasilia(None))
        self.assertIsNone(para_brasilia(""))


class TestIdentidadePelaCoordenada(unittest.TestCase):
    def test_dc01_entra_com_o_titulo_do_cadastro(self):
        leituras = parse(pagina_com([DC01]))
        self.assertEqual(len(leituras), 1)
        l = leituras[0]
        # O título é o do cadastro, não "DC01 Rio Itajaí-Açu - ICMBio/CEPSUL"
        # montado aqui: o cadastro usa hífen no código.
        self.assertEqual(l["estacao"], "DC-01 Rio Itajaí-Açu - ICMBio/CEPSUL")
        self.assertEqual(l["cidade"], "itajai")
        self.assertEqual(l["nivel_m"], 0.97)
        self.assertEqual(l["medido_em"], "2026-09-19T13:31:36")

    def test_rio_e_cidade_batem_com_o_mapeamento_antigo(self):
        """
        O coletor novo lê rio e cidade do cadastro; o antigo passava o título
        por `classificar_estacao`. Se os dois discordassem, a troca de portal
        mudaria de cidade uma régua sem ninguém notar — a DC-11, por exemplo,
        tem regra de fallback que diz "ilhota" e cadastro que diz "itajai".
        """
        for l in parse(PAGINA_REAL.read_text(encoding="utf-8")):
            self.assertEqual((l["rio"], l["cidade"]),
                             classificar_estacao(l["estacao"]), l["estacao"])

    def test_titulo_existe_no_cadastro(self):
        """A chave de identidade tem que casar com `estacoes.json`, string a string."""
        titulos = {e["titulo"] for e in estacoes_tempo_real()}
        for l in parse(PAGINA_REAL.read_text(encoding="utf-8")):
            self.assertIn(l["estacao"], titulos)

    def test_regua_deslocada_e_recusada(self):
        """
        Mesmo código, outro lugar: é o remanejamento que o cadastro registra.
        Entrar como se fosse a mesma régua daria nível certo com cota errada.
        """
        mudada = dict(DC01, latitude=-26.95, longitude=-48.70)  # ~7 km
        self.assertGreater(distancia_m((-26.90923, -48.6516), (-26.95, -48.70)),
                           TOLERANCIA_COORD_M)
        self.assertEqual(parse(pagina_com([mudada])), [])

    def test_deslocamento_de_publicacao_passa(self):
        """Arredondamento de coordenada não pode derrubar a régua."""
        # ~11 m: quinta casa decimal.
        vizinha = dict(DC01, latitude=-26.90933)
        self.assertEqual(len(parse(pagina_com([vizinha]))), 1)

    def test_sem_coordenada_e_recusada(self):
        self.assertEqual(parse(pagina_com([dict(DC01, latitude=None)])), [])

    def test_codigo_fora_do_cadastro_e_recusado(self):
        """Uma DC-12 nova entraria sem rio, sem cidade e sem cota."""
        self.assertEqual(parse(pagina_com([dict(DC01, codigo="DC12")])), [])

    def test_codigo_ilegivel_e_recusado(self):
        self.assertEqual(parse(pagina_com([dict(DC01, codigo="Régua do centro")])), [])


class TestQualidadeDoNumero(unittest.TestCase):
    def test_nivel_implausivel_e_recusado(self):
        """"9999,00" viraria alerta de inundação em toda a cidade."""
        self.assertEqual(parse(pagina_com([dict(DC01, nivel_rio_m=9999.0)])), [])

    def test_nivel_ausente_e_recusado(self):
        self.assertEqual(parse(pagina_com([dict(DC01, nivel_rio_m=None)])), [])

    def test_sem_horario_a_leitura_nao_entra(self):
        """Sem idade não dá para dizer ao morador de quando é o número."""
        orfa = dict(DC01, medido_em=None, qualidade={})
        self.assertEqual(parse(pagina_com([orfa])), [])

    def test_carimbo_da_grandeza_vence_o_da_estacao(self):
        """
        `qualidade.nivel_rio_m.medido_em` é o carimbo do NÍVEL e pode ser mais
        velho que o da estação (que a chuva, por exemplo, renova). Usar o da
        estação rejuvenesceria a leitura.
        """
        atrasada = dict(DC01)
        atrasada["qualidade"] = {"nivel_rio_m": {
            "estado": "atrasado", "medido_em": "2026-09-19T10:00:00+00:00"}}
        self.assertEqual(parse(pagina_com([atrasada]))[0]["medido_em"],
                         "2026-09-19T07:00:00")


class TestConsultadoEmNaoEntra(unittest.TestCase):
    def test_consultado_em_nao_renova_a_idade(self):
        """
        O corpo declara a consulta às 16h38 UTC e a medição às 16h31. Se o
        `consultadoEm` vazasse para `medido_em`, uma leitura de ontem apareceria
        como de agora — e o vigia nunca mais gritaria por régua parada.
        """
        velha = dict(DC01)
        velha["medido_em"] = "2026-09-18T12:00:00+00:00"
        velha["qualidade"] = {"nivel_rio_m": {"estado": "atrasado",
                                              "medido_em": "2026-09-18T12:00:00+00:00"}}
        l = parse(pagina_com([velha], consultado_em="2026-09-19T16:38:08+00:00"))[0]
        self.assertEqual(l["medido_em"], "2026-09-18T09:00:00")


class TestCotasNaoSaoAdotadas(unittest.TestCase):
    def test_leitura_nao_carrega_cota_do_portal(self):
        """
        Quatro das onze divergem do Plano de Contingência v17 (DC-01, DC-07,
        DC-08, DC-09) e em DC-07 e DC-08 o portal é MAIS BAIXO. A coleta não
        decide cota: o campo simplesmente não existe na leitura.
        """
        l = parse(pagina_com([DC01]))[0]
        for campo in ("atencao_m", "alerta_m", "emergencia_m", "cotas_m"):
            self.assertNotIn(campo, l)

    def test_cotas_do_cadastro_seguem_as_do_plano(self):
        """A DC-01 do cadastro continua com 1,16/1,36/1,56 — o v17, não o portal."""
        dc01 = next(e for e in estacoes_tempo_real() if e.get("codigo") == "DC-01")
        self.assertNotEqual(dc01["cotas_m"].get("atencao"), 1.21)


class TestPaginaReal(unittest.TestCase):
    """Contra os 87.637 bytes capturados em 19/09/2026 — a evidência preservada."""

    def setUp(self):
        self.leituras = parse(PAGINA_REAL.read_text(encoding="utf-8"))

    def test_as_onze_reguas_saem(self):
        self.assertEqual(len(self.leituras), 11)

    def test_todas_batem_com_o_cadastro_na_coordenada(self):
        """Em 19/09/2026 as onze bateram a 0,0 m. Se uma sair do lugar, cai aqui."""
        por_titulo = {e["titulo"]: e for e in estacoes_tempo_real()}
        d = carga(PAGINA_REAL.read_text(encoding="utf-8"))
        for e in d["props"]["estacoes"]:
            codigo = f"DC-{e['codigo'][2:]}"
            nossa = next(x for x in por_titulo.values() if x.get("codigo") == codigo)
            self.assertLessEqual(
                distancia_m((nossa["lat"], nossa["lon"]),
                            (e["latitude"], e["longitude"])), 1.0, codigo)

    def test_dc00_nao_vira_leitura(self):
        """A DC-00 é a própria Defesa Civil (sem rio nem coordenada), não uma régua."""
        self.assertNotIn("DC-00", " ".join(l["estacao"] for l in self.leituras))

    def test_todas_em_itajai(self):
        """Esta resposta é do município 1. Brusque, Blumenau e Rio do Sul não vêm nela."""
        self.assertEqual({l["cidade"] for l in self.leituras}, {"itajai"})

    def test_carimbos_sao_de_brasilia(self):
        """13h e não 16h: o portal publica UTC, o repositório grava Brasília."""
        for l in self.leituras:
            self.assertNotIn("+", l["medido_em"])
            self.assertTrue(l["medido_em"].startswith("2026-09-19T13:"), l["medido_em"])

    def test_coletar_de_arquivo_nao_usa_rede(self):
        d = coletar(PAGINA_REAL.read_text(encoding="utf-8"))
        self.assertEqual(d["fonte"].startswith("https://monitoramento.defesacivil"), True)
        self.assertEqual(len(d["leituras"]), 11)


if __name__ == "__main__":
    unittest.main(verbosity=2)
