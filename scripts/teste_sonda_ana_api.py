"""A sonda da API da ANA olha; não grava dado do projeto.

Ela existe porque em 08/09/2026 a `HidroSerieCotas` mostrou que o FORMATO da
resposta é o que decide tudo — a série de rótulo melhor apagava uma cheia de
4 m. Escrever coletor contra formato suposto repetiria o erro. Estes testes
travam o que a sonda pode e não pode fazer, já que o alvo dela é a rede e
ninguém consegue rodá-la no CI.
"""

from __future__ import annotations

import unittest
from pathlib import Path

import sonda_ana_api as sonda

FONTE = (Path(__file__).resolve().parent / "sonda_ana_api.py").read_text(encoding="utf-8")


class NaoEscreveNoProjeto(unittest.TestCase):
    def test_nao_toca_nos_jsons_de_verdade(self):
        """
        Sonda que grava em estacoes.json ou enchentes.json deixa de ser sonda.
        A decisão de gravar dado neste projeto é humana — mesma divisão do
        ana_hidroweb.py e do ana_inventario.py.
        """
        for arquivo in ("estacoes.json", "enchentes.json", "transito.json"):
            self.assertNotIn(f'"{arquivo}"', FONTE, f"a sonda menciona {arquivo} em código")

    def test_o_unico_write_e_em_brutos(self):
        for linha in FONTE.splitlines():
            if "write_text" in linha and not linha.strip().startswith("#"):
                self.assertIn("destino", linha, f"escrita fora de data/brutos: {linha.strip()}")


class ChamaAsRotasQueASpecDeclara(unittest.TestCase):
    """Os caminhos vieram de /api-docs em 08/09/2026, não de suposição."""

    def test_rotas(self):
        self.assertEqual(sonda.ROTA_INVENTARIO,
                         "/EstacoesTelemetricas/HidroInventarioEstacoes/v1")
        self.assertEqual(sonda.ROTA_TELEMETRIA,
                         "/EstacoesTelemetricas/HidroinfoanaSerieTelemetricaAdotada/v1")

    def test_o_range_pedido_esta_no_enum_da_spec(self):
        """`Range Intervalo de busca` é obrigatório e é enum. HORA_24 existe."""
        self.assertIn('"HORA_24"', FONTE)

    def test_respeita_o_turno_entre_chamadas(self):
        """Rate limit é regra do projeto para toda fonte externa."""
        self.assertIn("espera_turno()", FONTE)

    def test_identifica_o_user_agent(self):
        self.assertIn("USER_AGENT", FONTE)


class ResumoNaoMenteQuandoDaErrado(unittest.TestCase):
    def test_http_errado_vira_texto_visivel(self):
        linha, itens = sonda._resumo({"_erro": "HTTP 401", "_corpo": "sem token"})
        self.assertIn("401", linha)
        self.assertEqual(itens, [])

    def test_resposta_sem_items_diz_quais_chaves_vieram(self):
        linha, itens = sonda._resumo({"status": "OK", "outra_coisa": 1})
        self.assertIn("sem lista", linha)
        self.assertIn("outra_coisa", linha)
        self.assertEqual(itens, [])

    def test_lista_vazia_nao_e_confundida_com_sucesso(self):
        linha, itens = sonda._resumo({"message": "Não houve retorno de registros. Verifique!",
                                      "items": []})
        self.assertIn("0 item", linha)
        self.assertEqual(itens, [])

    def test_lista_com_itens_conta_certo(self):
        linha, itens = sonda._resumo({"message": "Sucesso", "items": [{"a": 1}, {"a": 2}]})
        self.assertIn("2 item", linha)
        self.assertEqual(len(itens), 2)


class AsCandidatasSaoDaBacia(unittest.TestCase):
    def test_todas_estao_no_cadastro_de_estacoes_conhecidas(self):
        """
        Sondar um código que o projeto não conhece daria um resultado sem dono.
        E o cadastro é onde está escrito por que cada uma NÃO é régua de cidade.
        """
        import validar_dados as vd
        for codigo in sonda.CANDIDATAS:
            with self.subTest(codigo=codigo):
                self.assertIn(codigo.lstrip("0"), vd.ESTACOES_ANA_CONHECIDAS)

    def test_sondar_nao_e_vincular(self):
        """
        A sonda olha nível ao vivo; NÃO afirma que a estação é a régua daquela
        cidade. Quatro dessas candidatas são recusas escritas em
        `codigo_ana_nao_e`, e é assim que o Salseiro quase entrou em Vidal
        Ramos. O aviso tem de estar no próprio arquivo.
        """
        self.assertIn("conferência de régua", FONTE)


class OResultadoNegativoDaTelemetriaEstaEscrito(unittest.TestCase):
    """
    Onze chamadas em 08/09/2026, todas vazias, contra um inventário da MESMA
    API que afirma a estação telemétrica e operando. Resultado negativo não
    guardado vira a mesma busca daqui a um mês — e esta custou uma rodada
    inteira de variações de parâmetro.
    """

    def test_a_sonda_avisa_que_ja_foi_respondido(self):
        self.assertIn("RESPONDIDO EM 08/09/2026, E É NÃO", FONTE)

    def test_diz_quantas_tentativas_foram(self):
        self.assertIn("Onze chamadas", FONTE)

    def test_nomeia_a_contradicao_com_o_inventario(self):
        """
        É o ponto que impede alguém de concluir "a estação não transmite": o
        cadastro da própria ANA diz que transmite desde 1996.
        """
        self.assertIn("83900000", FONTE)
        self.assertIn("05/1996", FONTE)

    def test_manda_parar_de_chutar_parametro(self):
        self.assertIn("chutando parâmetro", FONTE)


class OResultadoPositivoDe0909TambemEstaEscrito(unittest.TestCase):
    """
    A EPAGRI explicou o vazio de 08/09 (estações desativadas) e a janela
    histórica nas quatro ativas devolveu 672 leituras cada. Quem ler só o
    "É NÃO" de 08/09 desistiria de uma série que existe.
    """

    def test_a_sonda_diz_que_a_serie_existe_para_as_ativas(self):
        self.assertIn("REVISTO EM 09/09/2026, E É SIM", FONTE)
        for codigo in ("83029900", "83050000", "83250000", "83892990"):
            self.assertIn(codigo, FONTE)

    def test_avisa_que_a_janela_termina_na_data_pedida(self):
        """É o detalhe que fez a Saltinho parecer ter pico de 10,32 m."""
        self.assertIn("TERMINANDO na data pedida", FONTE)


class ResumoDeCotasNaoInventaPico(unittest.TestCase):
    """`Cota_Adotada` vem em CENTÍMETROS, como string, e com muitos `null`."""

    ITENS = [
        {"Data_Hora_Medicao": "2023-11-11 00:00:00.0", "Cota_Adotada": "634.00"},
        {"Data_Hora_Medicao": "2023-11-11 00:15:00.0", "Cota_Adotada": None},
        {"Data_Hora_Medicao": "2023-11-14 12:00:00.0", "Cota_Adotada": "920.00"},
        {"Data_Hora_Medicao": "2023-11-17 23:45:00.0", "Cota_Adotada": "1032.00"},
    ]

    def test_converte_centimetros_para_metros_e_conta_nulls(self):
        r = sonda.resumo_cotas(self.ITENS)
        self.assertEqual((r["n"], r["n_cota"]), (4, 3))
        self.assertEqual(r["primeira"], ("2023-11-11 00:00:00.0", 6.34))
        self.assertEqual(r["ultima"], ("2023-11-17 23:45:00.0", 10.32))
        self.assertEqual(r["minima"][1], 6.34)

    def test_maximo_na_ultima_leitura_e_piso_e_nao_pico(self):
        """
        Saltinho, 17/11/2023 23:45: 10,32 m era a última leitura E a maior.
        O rio ainda subia; a janela acabou antes do pico. Citar 10,32 m como
        pico faria o morador achar a cheia menor do que foi.
        """
        r = sonda.resumo_cotas(self.ITENS)
        self.assertTrue(r["pico_pode_estar_depois"])

    def test_pico_dentro_da_janela_nao_dispara_o_aviso(self):
        itens = self.ITENS + [{"Data_Hora_Medicao": "2023-11-18 00:00:00.0",
                               "Cota_Adotada": "1000.00"}]
        r = sonda.resumo_cotas(itens)
        self.assertEqual(r["maxima"], ("2023-11-17 23:45:00.0", 10.32))
        self.assertFalse(r["pico_pode_estar_depois"])

    def test_serie_toda_nula_nao_vira_zero(self):
        """Ituporanga (83250000) veio `null` nas pontas; null não é 0,00 m."""
        r = sonda.resumo_cotas([{"Data_Hora_Medicao": "x", "Cota_Adotada": None}] * 3)
        self.assertEqual(r["n_cota"], 0)
        self.assertIsNone(r["maxima"])
        self.assertFalse(r["pico_pode_estar_depois"])

    def test_lista_vazia(self):
        self.assertEqual(sonda.resumo_cotas([])["n"], 0)

    def test_string_que_nao_e_numero_vira_ausente(self):
        self.assertIsNone(sonda._cota_m({"Cota_Adotada": "n/d"}))


class AGravacaoDaSerieEOptativaEVaiParaBrutos(unittest.TestCase):
    def test_flags(self):
        self.assertIn('"--gravar"', FONTE)
        self.assertIn('"--sem-inventario"', FONTE)

    def test_nome_do_bruto_da_serie_carrega_estacao_data_e_intervalo(self):
        """Sem os três no nome, duas janelas da mesma estação se sobrescrevem."""
        self.assertIn('f"ana-telemetria-{codigo}-{data or date.today().isoformat()}-{intervalo}.json"',
                      FONTE)


if __name__ == "__main__":
    unittest.main()
