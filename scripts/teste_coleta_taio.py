#!/usr/bin/env python3
"""
Testes do coletor de Taió — e da armadilha que ele existe para evitar.

O teste mais importante daqui não é o do caminho feliz: é o que trava que o
`montante` (reservatório, ~17 m) NUNCA vire nível de cidade. A régua de
plausibilidade do projeto não pega esse erro, porque 17,2 m cabe na faixa
0–25 m que ela aceita — e a cota de emergência de Taió é 9,00 m. Um coletor que
lesse o campo errado pintaria emergência todo dia.
"""
import json
import unittest
from pathlib import Path

import coleta_taio as ct

RAIZ = Path(__file__).resolve().parent.parent
FIXTURE = RAIZ / "data" / "brutos" / "taio-cards-2026-09-03.json"


def cards() -> dict:
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


class ArmadilhaDasDuasReguas(unittest.TestCase):
    def test_o_montante_nunca_vira_leitura_de_cidade(self):
        d = ct.parse(cards())
        for l in d["leituras"]:
            self.assertNotEqual(l["nivel_m"], 17.2, "o reservatório virou nível de cidade")
            self.assertLess(l["nivel_m"], 10.0, "nível de cidade em escala de barragem")
        # E continua disponível, no lugar certo.
        self.assertEqual(d["barragem"]["montante_m"], 17.2)

    def test_a_regua_de_plausibilidade_NAO_pega_esse_erro(self):
        """
        É por isso que a separação tem de ser estrutural.

        Se um dia alguém trocar o campo, `nivel_plausivel` não vai avisar: 17,2
        passa. Este teste existe para que a razão fique escrita junto do código.
        """
        from comum import nivel_plausivel
        self.assertTrue(nivel_plausivel(17.2))

    def test_o_campo_lido_e_o_da_cidade(self):
        self.assertEqual(ct.CAMPO_NIVEL_CIDADE, "nivelCentro")
        self.assertEqual(ct.CAMPO_NIVEL_BARRAGEM, "montante")


class Comportas(unittest.TestCase):
    def test_le_o_estado_do_texto_da_fonte(self):
        c = ct.comportas("7 de 7")
        self.assertEqual((c["abertas"], c["total"]), (7, 7))
        self.assertTrue(c["todas_abertas"])
        self.assertEqual(c["regime"], "vertendo")

    def test_zero_aberta_e_dado_bom_e_significa_retendo(self):
        # Zero aqui NÃO é ausência — é a barragem segurando, que é justamente a
        # informação que muda a leitura do rio a jusante.
        c = ct.comportas("0 de 7")
        self.assertEqual(c["abertas"], 0)
        self.assertEqual(c["regime"], "retendo")
        self.assertFalse(c["todas_abertas"])

    def test_qualquer_comporta_aberta_ja_e_vertendo(self):
        self.assertEqual(ct.comportas("1 de 7")["regime"], "vertendo")

    def test_texto_impossivel_e_recusado(self):
        # "8 de 7" é erro da fonte, não estado de barragem.
        self.assertIsNone(ct.comportas("8 de 7"))
        self.assertIsNone(ct.comportas("aberta"))
        self.assertIsNone(ct.comportas(None))

    def test_o_total_vem_do_texto_e_nao_do_codigo(self):
        # A JICA diz 7 condutos com comporta na Oeste, e a API diz "de 7". Se a
        # fonte mudar, é ela que manda — o coletor não fixa o total.
        self.assertEqual(ct.comportas("3 de 5")["total"], 5)


class Carimbo(unittest.TestCase):
    def test_nao_converte_fuso(self):
        """
        `dataUltimaAtualizacao` já é horário de Brasília, o mesmo contrato de
        `medido_em`. Converter "para garantir" jogaria a idade 3 h fora — e a
        idade é o que diz se o número serve.
        """
        self.assertEqual(ct.quando("03/09/2026 20:41:58"), "2026-09-03T20:41:58")

    def test_sem_carimbo_nao_ha_leitura(self):
        d = ct.parse({**cards(), "dataUltimaAtualizacao": None})
        self.assertEqual(d["leituras"], [], "sem idade o número não serve")
        # A barragem continua sendo reportada: comporta sem carimbo ainda diz
        # o regime, e é melhor que silêncio.
        self.assertIsNotNone(d["barragem"]["comportas"])

    def test_data_fora_do_formato_nao_vira_agora(self):
        self.assertIsNone(ct.quando("2026-09-03T20:41:58"))
        self.assertIsNone(ct.quando("ontem"))


class CamposVazios(unittest.TestCase):
    def test_o_traco_e_o_vazio_da_API_viram_none(self):
        # A API usa "", "–" e null para "não tem" — os três.
        for v in ("", "–", "-", None, "  "):
            self.assertIsNone(ct.numero(v), f"{v!r} deveria virar None")

    def test_as_cotas_da_API_sao_ignoradas_porque_vem_sempre_null(self):
        d = ct.parse(cards())
        texto = json.dumps(d, ensure_ascii=False)
        self.assertNotIn("cotasAlagamento", texto)
        self.assertNotIn("cotaEmergencia", texto)

    def test_json_inesperado_nao_quebra(self):
        for entrada in ({}, [], None, "erro"):
            d = ct.parse(entrada)
            self.assertEqual(d["leituras"], [])


class Fixture(unittest.TestCase):
    def test_a_leitura_real_de_03_09(self):
        d = ct.parse(cards())
        self.assertEqual(len(d["leituras"]), 1)
        l = d["leituras"][0]
        self.assertEqual(l["nivel_m"], 5.25)
        self.assertEqual(l["cidade"], "taio")
        self.assertEqual(l["medido_em"], "2026-09-03T20:41:58")
        # Esta régua É a que as cotas do Plano descrevem, então pode virar
        # faixa — ao contrário do nível bruto da rede estadual.
        self.assertTrue(l["usar_para_cota"])
        self.assertEqual(d["barragem"]["comportas"]["regime"], "vertendo")

    def test_a_leitura_cai_na_faixa_de_monitoramento_do_plano(self):
        """
        Conferência cruzada: 5,25 m com as cotas de Taió (monitoramento 5,00,
        atenção 7,00) tem de cair em monitoramento — e a home da Defesa Civil
        pintava o card de amarelo naquele instante. Se o coletor lesse o campo
        errado, 17,2 m cairia em emergência.
        """
        d = json.loads((RAIZ / "data" / "estacoes.json").read_text(encoding="utf-8"))
        taio = next(c for c in d["rios"]["itajai-acu"]["cidades"] if c["id"] == "taio")
        cotas = taio["cotas_m"]
        nivel = ct.parse(cards())["leituras"][0]["nivel_m"]
        self.assertGreaterEqual(nivel, cotas["monitoramento"])
        self.assertLess(nivel, cotas["atencao"])


class Historico(unittest.TestCase):
    def test_le_nivel_e_comportas_por_hora(self):
        pontos = [{
            "dataUltimaAtualizacao": "03/09/2026 20:00:34",
            "dataHora": "03/09 20:00", "nivel": "5.17", "chuva": "0.0",
            "montante": "17.2", "jusante": "", "comportaAberta": "7",
            "comportaFechada": "0",
        }]
        s = ct.parse_historico(pontos)
        self.assertEqual(len(s), 1)
        self.assertEqual(s[0]["nivel_m"], 5.17)
        self.assertEqual(s[0]["comportas_abertas"], 7)

    def test_ponto_sem_nivel_ou_sem_carimbo_e_descartado(self):
        self.assertEqual(ct.parse_historico([{"nivel": "5.1"}]), [])
        self.assertEqual(ct.parse_historico([{"dataUltimaAtualizacao": "03/09/2026 20:00:34"}]), [])
        self.assertEqual(ct.parse_historico(None), [])


class DiagnosticoDeTransporte(unittest.TestCase):
    """
    Quando a API recusa, a mensagem tem de dizer O QUE o servidor falou.

    Em 04/09/2026 a primeira execução contra a VPS devolveu só "400 Client
    Error: Bad Request". Verdadeiro e inútil: não dá para saber se falta um
    cabeçalho, se o parâmetro mudou ou se o IP está bloqueado. O corpo da
    resposta quase sempre nomeia a causa, e agora vem junto.
    """

    def _falso_requests(self, status, corpo, tipo="application/json"):
        import types

        class Resposta:
            ok = 200 <= status < 300
            status_code = status
            text = corpo
            headers = {"Content-Type": tipo}

            def json(self):
                import json as _j
                return _j.loads(corpo)

        mod = types.ModuleType("requests")
        mod.get = lambda url, headers=None, timeout=None: Resposta()
        mod._cabecalhos = {}
        return mod

    def test_o_erro_carrega_o_corpo_da_resposta(self):
        import sys
        sys.modules["requests"] = self._falso_requests(
            400, '{"error":"missing required header"}')
        try:
            with self.assertRaises(ct.RespostaRuim) as caso:
                ct.baixar_json(ct.URL_CARDS)
        finally:
            sys.modules.pop("requests", None)
        msg = str(caso.exception)
        self.assertIn("HTTP 400", msg)
        self.assertIn("missing required header", msg)
        self.assertIn("application/json", msg)

    def test_corpo_vazio_nao_vira_mensagem_muda(self):
        import sys
        sys.modules["requests"] = self._falso_requests(503, "   ", "text/html")
        try:
            with self.assertRaises(ct.RespostaRuim) as caso:
                ct.baixar_json(ct.URL_CARDS)
        finally:
            sys.modules.pop("requests", None)
        self.assertIn("(corpo vazio)", str(caso.exception))

    def test_continua_identificando_o_projeto_no_User_Agent(self):
        # O Accept foi acrescentado para o caso de servidor que recusa
        # requisicao sem ele. Nao e disfarce: a identificacao do projeto
        # permanece, como o CLAUDE.md exige de todo script.
        import sys, types
        vistos = {}

        class Resposta:
            ok = True
            status_code = 200
            text = "{}"
            headers = {"Content-Type": "application/json"}

            def json(self):
                return {}

        mod = types.ModuleType("requests")

        def get(url, headers=None, timeout=None):
            vistos.update(headers or {})
            return Resposta()

        mod.get = get
        sys.modules["requests"] = mod
        try:
            ct.baixar_json(ct.URL_CARDS)
        finally:
            sys.modules.pop("requests", None)
        self.assertIn("enchentes-vale-itajai", vistos.get("User-Agent", ""))
        self.assertEqual(vistos.get("Accept"), "application/json")


if __name__ == "__main__":
    unittest.main()
