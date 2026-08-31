#!/usr/bin/env python3
"""
Testes do coletor de chuva da Defesa Civil de SC.

Os dois riscos deste coletor são a conversão de fuso — errar desloca a idade de
toda leitura em três horas, e a idade é o que diz se o número serve — e o mapa
de estação para cidade, onde casar por semelhança de nome erraria calado.

    python3 scripts/teste_coleta_chuva_sc.py
"""

import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from coleta_chuva_sc import (
    CHUVA_MAXIMA_MM, POR_CIDADE, converter, e_numero, hora_local, valor_de,
)


def estacao(codigo="DCSC-00026", nome="SDC-SC Blumenau", h1=1.0, h24=19.06,
            carimbo="2026-08-31T20:39:36.394+00:00"):
    return {
        "codigo": codigo,
        "name": {"prefix": codigo, "general": nome, "local": ""},
        "timestamp": carimbo,
        "position": {"bacia": "SC - Rio Itajaí"},
        "data": {"chuva": {"acumulado": {
            "h001": None if h1 is None else {"value": h1},
            "h024": None if h24 is None else {"value": h24},
        }}},
    }


class TestFuso(unittest.TestCase):
    """UTC do GraphQL -> hora de Brasília sem fuso, que é o formato do projeto."""

    def test_converte_utc_para_brasilia(self):
        self.assertEqual(hora_local("2026-08-31T20:39:36.394+00:00"), "2026-08-31T17:39:36")

    def test_a_diferenca_e_de_tres_horas(self):
        # Se isto quebrar, a idade de toda leitura sai errada em 3 h.
        self.assertEqual(hora_local("2026-08-31T12:00:00+00:00"), "2026-08-31T09:00:00")

    def test_vira_o_dia_para_tras_quando_precisa(self):
        self.assertEqual(hora_local("2026-08-31T01:00:00+00:00"), "2026-08-30T22:00:00")

    def test_aceita_o_z_no_lugar_do_offset(self):
        self.assertEqual(hora_local("2026-08-31T12:00:00Z"), "2026-08-31T09:00:00")

    def test_carimbo_ausente_ou_ilegivel_nao_vira_hora(self):
        self.assertIsNone(hora_local(None))
        self.assertIsNone(hora_local(""))
        self.assertIsNone(hora_local("ontem à tarde"))


class TestValorDe(unittest.TestCase):
    def test_tira_o_value_da_caixa(self):
        self.assertEqual(valor_de({"value": 7.05}), 7.05)

    def test_caixa_ausente_ou_vazia_e_nada(self):
        self.assertIsNone(valor_de(None))
        self.assertIsNone(valor_de({}))
        self.assertIsNone(valor_de({"value": None}))

    def test_booleano_nao_e_milimetro(self):
        self.assertIsNone(valor_de({"value": True}))
        self.assertFalse(e_numero(True))

    def test_zero_e_um_valor_de_verdade(self):
        self.assertEqual(valor_de({"value": 0}), 0.0)


class TestMapa(unittest.TestCase):
    def test_estacao_fora_do_mapa_e_recusada_com_motivo(self):
        leituras, recusadas = converter([estacao(codigo="DCSC-99999", nome="SDC-SC Outra")])
        self.assertEqual(leituras, [])
        self.assertIn("fora do mapa", recusadas[0])

    def test_estacao_mapeada_vira_leitura_da_cidade(self):
        leituras, _ = converter([estacao()])
        self.assertEqual(leituras[0]["cidade"], "blumenau")

    def test_duas_estacoes_da_mesma_cidade_entram_as_duas(self):
        """Botuverá 1 e 2 são pluviômetros distintos; o site mostra o maior."""
        leituras, _ = converter([
            estacao(codigo="DCSC-00018", nome="SDC-SC Botuverá 1", h24=73.4),
            estacao(codigo="DCSC-00027", nome="SDC-SC Botuverá 2", h24=79.7),
        ])
        self.assertEqual([l["cidade"] for l in leituras], ["botuvera", "botuvera"])
        self.assertEqual(len({l["estacao"] for l in leituras}), 2, "nomes têm de ser distintos")

    def test_timbo_fica_de_fora_porque_nao_tem_tela(self):
        """
        Timbó é cidade do projeto, mas mora em `afluentes_monitorados` e não na
        sequência dos rios: nem o site nem o bot a mostram. Coletar a chuva dela
        seria cobertura aparente — número gravado que ninguém vê.
        """
        leituras, recusadas = converter([
            estacao(codigo="DCSC-00023", nome="SDC-SC Timbó 1", h24=90.6)])
        self.assertEqual(leituras, [])
        self.assertIn("fora do mapa", recusadas[0])

    def test_o_codigo_entra_no_nome_da_estacao(self):
        """Sem o código, 'SDC-SC Timbó 1' e 'Timbó 2' viram nomes parecidos demais."""
        leituras, _ = converter([estacao()])
        self.assertTrue(leituras[0]["estacao"].startswith("DCSC-00026 "))

    def test_toda_cidade_do_mapa_pode_ser_MOSTRADA(self):
        """
        Não basta existir no JSON: tem de estar em `comum.cidades()`, que é o
        que o site e o bot enxergam. Foi assim que Timbó apareceu — cidade real,
        sem tela nenhuma, e a chuva dela iria para um arquivo que ninguém lê.
        """
        from comum import cidades
        mostraveis = {c["id"] for c in cidades()}
        for codigo, cidade in POR_CIDADE.items():
            self.assertIn(cidade, mostraveis, f"{codigo} aponta para cidade sem tela")


class TestJanelas(unittest.TestCase):
    def test_so_h1_e_h24_vem_preenchidas(self):
        """A fonte publica duas janelas. As outras ficam None, não zero."""
        leituras, _ = converter([estacao(h1=7.05, h24=79.36)])
        mm = leituras[0]["mm"]
        self.assertEqual(mm["h1"], 7.05)
        self.assertEqual(mm["h24"], 79.36)
        for ausente in ("min10", "h12", "h48"):
            self.assertIsNone(mm[ausente], f"{ausente} não é publicado e não vira zero")

    def test_estacao_sem_janela_nenhuma_e_recusada(self):
        leituras, recusadas = converter([estacao(h1=None, h24=None)])
        self.assertEqual(leituras, [])
        self.assertIn("sem nenhuma janela", recusadas[0])

    def test_chuva_absurda_nao_entra(self):
        leituras, recusadas = converter([estacao(h24=CHUVA_MAXIMA_MM + 1)])
        self.assertEqual(leituras, [])
        self.assertIn("fora da faixa", recusadas[0])

    def test_chuva_negativa_nao_entra(self):
        leituras, recusadas = converter([estacao(h24=-1)])
        self.assertEqual(leituras, [])

    def test_chuva_forte_de_verdade_entra(self):
        """100,5 mm em 24 h é o que Trombudo Central 1 marcava em 31/08/2026."""
        leituras, _ = converter([estacao(codigo="DCSC-00041", nome="SDC-SC Taió",
                                         h1=5.0, h24=100.47)])
        self.assertEqual(len(leituras), 1)
        self.assertEqual(leituras[0]["cidade"], "taio")


class TestCoerencia(unittest.TestCase):
    def test_acumulado_que_diminui_e_marcado(self):
        """1 h não pode ser maior que 24 h: as janelas são encaixadas."""
        leituras, _ = converter([estacao(h1=50.0, h24=10.0)])
        self.assertFalse(leituras[0]["coerente"])
        self.assertTrue(leituras[0]["incoerencias"])

    def test_serie_coerente_passa_limpa(self):
        leituras, _ = converter([estacao(h1=7.05, h24=79.36)])
        self.assertTrue(leituras[0]["coerente"])
        self.assertEqual(leituras[0]["incoerencias"], [])

    def test_incoerente_ainda_entra_para_a_tela_poder_dizer(self):
        """Descartar calado viraria 'não choveu'. Vai marcado, como na outra fonte."""
        leituras, _ = converter([estacao(h1=50.0, h24=10.0)])
        self.assertEqual(len(leituras), 1)


class TestNuncaNivel(unittest.TestCase):
    """
    A trava que importa. A mesma resposta traz `rio_nivel`, e ele NÃO pode
    entrar: Ilhota vinha 10,34 m enquanto a nossa régua da mesma cidade marcava
    3,25 m, e as estações `(H)` trazem valores na casa das centenas. Sem cota
    por estação, nada disso pode virar aviso.
    """

    def test_a_leitura_nao_carrega_nivel(self):
        com_nivel = estacao()
        com_nivel["data"]["rio"] = {"rio_nivel": {"value": 10.34}}
        leituras, _ = converter([com_nivel])
        texto = json.dumps(leituras[0], ensure_ascii=False)
        self.assertNotIn("10.34", texto)
        self.assertNotIn("nivel", texto.lower())

    def test_a_consulta_nao_pede_nivel(self):
        from coleta_chuva_sc import CONSULTA
        self.assertNotIn("rio_nivel", CONSULTA, "nem pedir o nível, para não tentar usar")

    def test_o_rio_fica_nulo_porque_a_fonte_da_bacia_e_nao_a_calha(self):
        leituras, _ = converter([estacao()])
        self.assertIsNone(leituras[0]["rio"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
