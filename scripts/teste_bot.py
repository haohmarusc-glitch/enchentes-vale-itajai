#!/usr/bin/env python3
"""Testes das respostas do bot.

Todas contra uma base montada com os números reais colhidos em 30/08/2026.
`responder` é função pura — recebe os dados e o relógio —, então dá para testar
cada resposta sem rede e sem Telegram nenhum.

O que estes casos protegem: que o bot nunca invente número, que toda leitura
saia com a idade, e que toda resposta lembre que isto não é alerta oficial.

    python3 scripts/teste_bot.py
"""

import unittest
from datetime import datetime, timezone

from bot import Base, responder, sem_acento, texto_idade
from comum import le_json

AGORA = datetime(2026, 8, 30, 21, 30, tzinfo=timezone.utc)  # 18:30 em Brasília

ULTIMO = {
    "coletado_em": "2026-08-30T21:25:00+00:00",
    "leituras": [
        {"estacao": "Rio do Sul Estação MKS", "rio": "itajai-acu", "cidade": "rio-do-sul",
         "nivel_m": 3.52, "medido_em": "2026-08-30T17:55:00"},
        {"estacao": "Brusque", "rio": "itajai-mirim", "cidade": "brusque",
         "nivel_m": 1.94, "medido_em": "2026-08-30T18:15:00"},
        {"estacao": "DC-01 Rio Itajaí-Açu - ICMBio/CEPSUL", "rio": "itajai-acu",
         "cidade": "itajai", "nivel_m": 0.81, "medido_em": "2026-08-30T18:20:00"},
        {"estacao": "DC-02 Rio Itajaí-Açu - Praça Celso Pereira da Silva",
         "rio": "itajai-acu", "cidade": "itajai", "nivel_m": 1.53,
         "medido_em": "2026-08-30T18:20:00"},
    ],
    "chuva": [
        {"estacao": "DC-09 Ribeirão da Murta", "rio": "ribeirao-murta", "cidade": "itajai",
         "mm": {"min10": 0.0, "h1": 1.2, "h12": 40.8, "h24": 40.8, "h48": 42.6},
         "medido_em": "2026-08-30T18:20:00", "coerente": True, "incoerencias": []},
        {"estacao": "DC-06 Itamirim", "rio": "itajai-mirim", "cidade": "itajai",
         "mm": {"min10": 0.0, "h1": 0.4, "h12": 14.6, "h24": 14.6, "h48": 15.4},
         "medido_em": "2026-08-30T18:20:00", "coerente": True, "incoerencias": []},
        {"estacao": "Brusque Estação Guarani", "rio": "itajai-mirim", "cidade": "brusque",
         "mm": {"min10": 0.4, "h1": 0.0, "h12": 0.0, "h24": 0.0, "h48": 0.0},
         "medido_em": "2026-08-30T18:15:00", "coerente": False,
         "incoerencias": ["min10=0.4 mm > h1=0 mm"]},
    ],
}


def base() -> Base:
    # Com as cotas de rua REAIS: é contra elas que /rua responde em produção.
    return Base(ULTIMO, le_json("estacoes.json"), le_json("transito.json"),
                le_json("enchentes.json"), le_json("cotas-ruas.json"))


def resp(texto: str) -> str:
    return responder(texto, base(), AGORA)


class TestNivel(unittest.TestCase):
    def test_nivel_traz_valor_estacao_e_idade(self):
        t = resp("/nivel Rio do Sul")
        self.assertIn("3,52 m", t)
        self.assertIn("Estação MKS", t)
        # 17:55 em Brasília são 20:55 UTC; AGORA é 21:30 UTC.
        self.assertIn("há 35 min", t, "toda leitura sai com a idade")

    def test_cidade_com_varias_reguas_avisa_que_nao_se_comparam(self):
        t = resp("/nivel Itajaí")
        self.assertIn("0,81 m", t)
        self.assertIn("1,53 m", t)
        self.assertIn("não se comparam", t)

    def test_cidade_sem_leitura_diz_que_nao_tem(self):
        t = resp("/nivel Blumenau")
        self.assertIn("Sem leitura ao vivo", t)
        self.assertNotIn(" m\n", t.split("Sem leitura")[0][:200] or " ")

    def test_sem_acento_e_sem_maiuscula_funciona(self):
        self.assertIn("3,52 m", resp("/nivel rio do sul"))
        self.assertIn("1,94 m", resp("/nivel BRUSQUE"))

    def test_cidade_desconhecida_nao_chuta(self):
        t = resp("/nivel Curitiba")
        self.assertIn("Não conheço", t)


class TestChuva(unittest.TestCase):
    def test_chuva_mostra_as_janelas_da_fonte(self):
        t = resp("/chuva Itajaí")
        self.assertIn("24 h", t)
        self.assertIn("40,8 mm", t)
        self.assertIn("14,6", t, "quando os pontos discordam, mostra a faixa")
        self.assertNotIn("6 h:", t, "a fonte não publica 6 h")

    def test_pluviometro_inconsistente_nao_vira_zero(self):
        """
        O caso real da Guarani. Dizer "0,0 mm" ali seria dizer que não choveu em
        Brusque — a pior resposta possível numa noite de chuva.
        """
        t = resp("/chuva Brusque")
        self.assertIn("inconsistente", t)
        self.assertNotIn("0,0 mm", t)

    def test_cidade_sem_pluviometro(self):
        self.assertIn("Não há pluviômetro", resp("/chuva Botuverá"))


class TestPrevisao(unittest.TestCase):
    def test_previsao_encadeia_ate_a_foz(self):
        t = resp("/previsao Rio do Sul")
        self.assertIn("Blumenau", t)
        self.assertIn("Itajaí", t)
        self.assertIn("conta condicional", t)

    def test_janela_ancorada_na_medicao_e_nao_em_agora(self):
        """
        A leitura de Rio do Sul é das 17:55; a chegada em Blumenau (7-10 h) tem
        de ser contada a partir dali, não das 18:30. Ancorar em "agora"
        empurraria toda a janela 35 min para frente.
        """
        t = resp("/previsao Rio do Sul")
        self.assertIn("00:55", t, "17:55 + 7 h")
        self.assertIn("03:55", t, "17:55 + 10 h")

    def test_cidade_com_varias_reguas_recusa(self):
        t = resp("/previsao Itajaí")
        self.assertIn("mais de uma régua", t)

    def test_cidade_sem_leitura_recusa(self):
        self.assertIn("não há leitura ao vivo", resp("/previsao Blumenau"))

    def test_foz_nao_tem_para_onde_mandar(self):
        t = resp("/previsao Brusque")
        self.assertIn("Itajaí", t)


    def test_cidade_dos_dois_rios_nao_responde_duplicado(self):
        """
        Itajaí existe no Açu e no Mirim. Chuva e nível são por cidade: a mesma
        resposta saindo duas vezes fazia a mensagem parecer defeito.
        """
        t = resp("/chuva Itajaí")
        self.assertEqual(t.count("chuva acumulada"), 1)
        self.assertEqual(resp("/nivel Itajaí").count("nível do rio"), 1)

    def test_ordem_impossivel_e_denunciada(self):
        """
        Os tempos de descida vêm de fontes diferentes e não concordam: no eixo
        do Açu, Blumenau pode aparecer recebendo a água antes de Apiúna, que
        fica acima. Esconder isso seria apresentar como sequência algo que a
        fonte não sustenta.
        """
        t = resp("/previsao Rio do Sul")
        self.assertIn("não estão em ordem de rio abaixo", t)

    def test_previsao_sem_desordem_nao_avisa_a_toa(self):
        b = base()
        b.transito = [
            {"rio": "itajai-mirim", "de": "brusque", "para": "itajai",
             "horas_min": 6, "horas_max": 6, "confianca": "baixa", "fonte": "F"},
        ]
        t = responder("/previsao Brusque", b, AGORA)
        self.assertNotIn("não estão em ordem", t)


class TestRua(unittest.TestCase):
    """
    /rua — a pergunta que a pessoa realmente faz.

    Tudo o mais que o bot responde está em metros de régua, que é a linguagem de
    quem opera o rio. Aqui é leitura de tabela: nenhuma previsão no meio.
    """

    def test_acha_rua_com_cidade(self):
        t = resp("/rua Blumenau São Rafael")
        self.assertIn("7,40 m", t)
        self.assertIn("7,75 m", t)
        self.assertLess(t.index("7,40"), t.index("7,75"), "a cota mais baixa vem primeiro")

    def test_o_ponto_faz_parte_do_nome(self):
        """
        A São Rafael alaga a 7,40 m no final e a 7,75 m perto do nº 169.
        Sem o ponto, as duas linhas pareceriam a mesma rua duplicada.
        """
        t = resp("/rua Blumenau São Rafael")
        self.assertIn("final da rua", t)
        self.assertIn("169", t)

    def test_sem_acento_e_sem_maiuscula(self):
        self.assertIn("7,40 m", resp("/rua blumenau sao rafael"))
        self.assertIn("7,40 m", resp("/rua BLUMENAU SAO RAFAEL"))

    def test_nome_de_cidade_dentro_de_nome_de_rua(self):
        """
        "Rua Rio do Sul", em Gaspar, é rua — e "Rio do Sul" é cidade. Casar o
        prefixo mais curto mandaria a busca para a cidade errada.
        """
        t = resp("/rua Gaspar Rio do Sul")
        self.assertIn("Gaspar", t)
        self.assertNotIn("Nenhuma rua", t)

    def test_sem_cidade_busca_em_todas_e_avisa(self):
        t = resp("/rua Beira")
        self.assertIn("Brusque", t)
        self.assertIn("4,80 m", t)

    def test_rua_sem_cota_aparece_com_a_nota_e_sem_numero(self):
        """Nulo não é zero: a rua aparece, mas sem número e com o porquê."""
        t = resp("/rua Gaspar Alfazema")
        self.assertIn("Alfazema", t)
        self.assertNotIn("0,00 m", t)
        self.assertIn("não publica a cota exata", t)

    def test_rua_desconhecida_nao_diz_que_nao_alaga(self):
        """A diferença entre as duas frases é alguém sair de casa ou não."""
        t = resp("/rua Blumenau Avenida Brasil")
        self.assertIn("não quer dizer que a sua rua não alaga", t)

    def test_compara_com_o_nivel_de_agora_quando_a_cidade_tem_uma_regua(self):
        t = resp("/rua Brusque Beira-Rio")
        self.assertIn("faltam", t)
        self.assertIn("1,94 m", t)

    def test_nao_compara_com_o_nivel_onde_a_cidade_tem_varias_reguas(self):
        """
        Itajaí tem onze réguas com zeros diferentes. "Faltam 2,30 m" sairia
        medido contra a régua errada.
        """
        b = base()
        b.cotas_ruas = [{"cidade": "itajai", "rio": "itajai-acu", "rua": "Rua Teste",
                         "bairro": None, "ponto": None, "cota_m": 3.0,
                         "fonte": "F", "data_fonte": "2026", "confianca": "media"}]
        t = responder("/rua Itajaí Teste", b, AGORA)
        self.assertIn("3,00 m", t)
        self.assertNotIn("faltam", t)

    def test_sem_argumento_lista_as_cidades(self):
        t = resp("/rua")
        self.assertIn("Blumenau", t)
        self.assertIn("/rua Blumenau", t)

    def test_traz_as_ressalvas_obrigatorias(self):
        t = resp("/rua Blumenau São Rafael")
        self.assertIn("não previsão", t.replace("não é previsão", "não previsão"))
        self.assertIn("199", t)


class TestLimiteDoTelegram(unittest.TestCase):
    def test_mensagem_longa_e_cortada_com_marca(self):
        """
        Acima de 4096 caracteres o Telegram recusa, e recusa é silêncio — o pior
        resultado possível num aviso de cheia.
        """
        import notificador
        curta = "a" * 100
        self.assertEqual(notificador.encurtar(curta), curta)
        longa = notificador.encurtar("b" * 9000)
        self.assertLessEqual(len(longa), notificador.LIMITE_CARACTERES)
        self.assertIn("cortada", longa)


class TestCotas(unittest.TestCase):
    def test_cotas_com_aviso_de_regua_propria(self):
        t = resp("/cotas Rio do Sul")
        self.assertIn("Atenção", t)
        self.assertIn("4,50 m", t)
        self.assertIn("própria régua", t)

    def test_cidade_sem_cota_diz_que_falta(self):
        self.assertIn("ainda não foram levantadas", resp("/cotas Ilhota"))


class TestGerais(unittest.TestCase):
    def test_toda_resposta_lembra_que_nao_e_alerta_oficial(self):
        for cmd in ("/ajuda", "/rios", "/emergencia", "/nivel Brusque",
                    "/chuva Itajaí", "/previsao Rio do Sul", "/cotas Blumenau"):
            with self.subTest(cmd=cmd):
                t = resp(cmd)
                self.assertIn("199", t, f"{cmd} não traz o telefone de emergência")

    def test_texto_que_nao_e_comando_e_ignorado(self):
        self.assertIsNone(resp("bom dia"))
        self.assertIsNone(resp(""))

    def test_comando_desconhecido_fica_em_silencio(self):
        """Em grupo, responder a comando de outro bot é ruído."""
        self.assertIsNone(resp("/piada"))

    def test_comando_com_arroba_do_grupo(self):
        self.assertIn("3,52 m", resp("/nivel@cheias_bot Rio do Sul"))

    def test_comando_sem_cidade_lista_as_cidades(self):
        t = resp("/nivel")
        self.assertIn("Blumenau", t)
        self.assertIn("/nivel Blumenau", t)

    def test_rios_mostra_tudo_com_idade(self):
        t = resp("/rios")
        self.assertIn("Rio do Sul", t)
        self.assertIn("Brusque", t)
        self.assertIn("maior de 2 réguas", t)

    def test_escapa_html_do_que_a_pessoa_digitou(self):
        t = resp("/nivel <b>xxx</b>")
        self.assertNotIn("<b>xxx</b>", t)


class TestAuxiliares(unittest.TestCase):
    def test_sem_acento(self):
        self.assertEqual(sem_acento("Itajaí-Açu"), "itajai-acu")

    def test_texto_idade(self):
        self.assertEqual(texto_idade(0), "agora mesmo")
        self.assertEqual(texto_idade(45), "há 45 min")
        self.assertEqual(texto_idade(60), "há 1 h")
        self.assertEqual(texto_idade(155), "há 2 h 35")
        self.assertEqual(texto_idade(None), "sem horário de medição")


if __name__ == "__main__":
    unittest.main(verbosity=2)
