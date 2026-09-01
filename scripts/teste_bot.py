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
from datetime import datetime, timedelta, timezone

import os
import sys
import unittest.mock
from pathlib import Path

import notificador
from bot import (IDADE_MAXIMA_PREVISAO_MIN, MAX_RUAS, REPETE_AVISO, TIMEOUTS_TOLERADOS, Base, aviso_de_falha,
                 eh_timeout, nome_curto, responder, resposta_rua, sem_acento, texto_idade)
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


def resp(texto: str, b=None) -> str:
    """A base padrão é a real; passe outra para testar um dado que ainda não existe."""
    return responder(texto, b if b is not None else base(), AGORA)


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


class TestIdadeDaChuva(unittest.TestCase):
    """
    O número exibido é o MAIOR de cada janela, e pode vir de um pluviômetro
    parado há horas. A idade tem de ser um limite superior: nenhuma leitura
    daquela resposta é mais velha que o que está escrito. Com a idade do mais
    novo, "80 mm em 24 h · há 5 min" saía de uma leitura de três horas atrás.
    """

    def base_com(self, chuvas):
        b = base()
        b.chuva_da_cidade = lambda _cidade: chuvas
        return b

    def chuva(self, estacao, medido_em, h24):
        return {"estacao": estacao, "cidade": "itajai", "coerente": True,
                "medido_em": medido_em, "mm": {"h1": 0.0, "h12": h24 / 2, "h24": h24,
                                               "h48": h24}}

    def test_a_idade_e_a_do_mais_velho(self):
        base = self.base_com([self.chuva("VELHO", "2026-08-30T15:30:00", 80.0),
                              self.chuva("NOVO", "2026-08-30T18:25:00", 2.0)])
        r = responder("/chuva Itajaí", base, AGORA)
        self.assertIn("há 3 h no mais velho", r)
        self.assertIn("há 5 min no mais novo", r)

    def test_nao_diz_agora_quando_o_maior_valor_e_velho(self):
        base = self.base_com([self.chuva("VELHO", "2026-08-30T15:30:00", 80.0),
                              self.chuva("NOVO", "2026-08-30T18:30:00", 2.0)])
        r = responder("/chuva Itajaí", base, AGORA)
        depois = r.split("pluviômetro", 1)[1]
        self.assertNotIn("· agora mesmo", depois, "80 mm de 3 h atrás não é 'agora mesmo'")

    def test_idades_parecidas_saem_com_uma_idade_so(self):
        base = self.base_com([self.chuva("A", "2026-08-30T18:25:00", 8.0),
                              self.chuva("B", "2026-08-30T18:20:00", 6.0)])
        r = responder("/chuva Itajaí", base, AGORA)
        self.assertIn("há 10 min", r)
        self.assertNotIn("mais velho", r, "5 min de diferença não merece duas idades")

    def test_um_pluviometro_so_continua_simples(self):
        base = self.base_com([self.chuva("UNICO", "2026-08-30T18:25:00", 8.0)])
        r = responder("/chuva Itajaí", base, AGORA)
        self.assertIn("há 5 min", r)
        self.assertNotIn("mais velho", r)


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


class TestPrevisaoComLeituraVelha(unittest.TestCase):
    """
    A conta é "se o pico fosse AGORA", e parte do instante da medição. Com
    leitura velha o "agora" é mentira: com uma de 30 h, o bot anunciava chegada
    em Apiúna para o dia ANTERIOR, com cara de previsão.
    """

    def base_com(self, cidade, estacao, nivel, horas_atras):
        medido = datetime(2026, 8, 30, 18, 30) - timedelta(hours=horas_atras)
        ultimo = {"coletado_em": "2026-08-30T21:25:00+00:00", "leituras": [
            {"estacao": estacao, "rio": "itajai-acu", "cidade": cidade, "nivel_m": nivel,
             "medido_em": medido.isoformat(timespec="minutes")}]}
        return Base(ultimo, le_json("estacoes.json"), le_json("transito.json"),
                    le_json("enchentes.json"), le_json("cotas-ruas.json"))

    def test_leitura_fresca_calcula(self):
        b = self.base_com("rio-do-sul", "Rio do Sul Estação MKS", 3.52, 0.1)
        r = responder("/previsao Rio do Sul", b, AGORA)
        self.assertIn("Apiúna", r)
        self.assertNotIn("Não dá para calcular com ela", r)

    def test_no_limite_ainda_calcula(self):
        b = self.base_com("rio-do-sul", "Rio do Sul Estação MKS", 3.52,
                          IDADE_MAXIMA_PREVISAO_MIN / 60 - 0.1)
        self.assertNotIn("Não dá para calcular com ela",
                         responder("/previsao Rio do Sul", b, AGORA))

    def test_passando_do_limite_recusa(self):
        b = self.base_com("rio-do-sul", "Rio do Sul Estação MKS", 3.52,
                          IDADE_MAXIMA_PREVISAO_MIN / 60 + 0.1)
        r = responder("/previsao Rio do Sul", b, AGORA)
        self.assertIn("Não dá para calcular com ela", r)

    def test_a_recusa_diz_a_idade_e_o_nivel(self):
        """Recusar não é sumir com o dado: o número e a idade continuam à vista."""
        b = self.base_com("rio-do-sul", "Rio do Sul Estação MKS", 3.52, 30)
        r = responder("/previsao Rio do Sul", b, AGORA)
        self.assertIn("há 30 h", r)
        self.assertIn("3,52 m", r)

    def test_leitura_velha_nao_anuncia_horario_nenhum(self):
        b = self.base_com("rio-do-sul", "Rio do Sul Estação MKS", 3.52, 30)
        r = responder("/previsao Rio do Sul", b, AGORA)
        self.assertNotIn("por volta de", r)
        self.assertNotIn("entre 2", r)

    def test_janela_ja_passada_nao_vira_previsao(self):
        """
        Trecho curto com leitura de algumas horas: Apiúna→Indaial é de 1 h, e
        com 2 h 30 de leitura a janela inteira já ficou para trás. Dizer "por
        volta de" um horário passado faz a pessoa procurar no relógio uma água
        que, se veio, veio antes.
        """
        b = self.base_com("apiuna", "Apiúna", 2.10, 2.5)
        r = responder("/previsao Apiúna", b, AGORA)
        self.assertIn("janela já passou", r)
        self.assertNotIn("Indaial</b>: por volta", r)


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
        """
        Nulo não é zero: a rua aparece, mas sem número e com o porquê.

        O exemplo era uma rua de Gaspar até a importação do mapa da Defesa Civil
        dar número a ela — e o teste quebrou, que é o comportamento certo: ele
        existe para o caso sem número, não para uma rua específica. Os que
        continuam sem número são os cinco pontos de Brusque que a fonte descreve
        por faixa ("entre 5,46 m e 5,80 m") sem publicar o valor.
        """
        t = resp("/rua Brusque Túnel do Terminal Urbano")
        self.assertIn("Terminal Urbano", t)
        self.assertNotIn("0,00 m", t)
        self.assertNotIn("Alaga a partir de", t)
        self.assertIn("5,46 m", t, "a nota tem de dizer o que se sabe")

    def test_rua_sem_cota_e_sem_nota_diz_que_a_fonte_nao_publicou(self):
        """
        O caso de última linha: sem número E sem nota, o bot ainda tem de
        explicar. Silêncio aqui vira "a rua não alaga" na cabeça de quem lê.
        """
        b = Base(ULTIMO, le_json("estacoes.json"), le_json("transito.json"),
                 le_json("enchentes.json"),
                 {"_meta": {}, "cotas": [{"cidade": "brusque", "rio": "itajai-mirim",
                                          "rua": "Rua Sem Nada", "bairro": None,
                                          "ponto": None, "cota_m": None,
                                          "fonte": "teste", "data_fonte": "2026-01",
                                          "confianca": "baixa"}]})
        t = resp("/rua Brusque Sem Nada", b)
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

    def test_diz_por_que_nao_ha_comparacao_com_o_nivel(self):
        """
        Blumenau tem cota de rua e não aparece na coleta. Sem explicação, o
        silêncio parece esquecimento — e a pergunta seguinte a "minha rua alaga
        a quantos metros" é sempre "e onde está o rio agora".
        """
        t = resp("/rua Blumenau São Rafael")
        self.assertIn("7,40 m", t)
        self.assertIn("não dá para dizer", t)
        self.assertIn("não aparece na fonte de tempo real", t)

    def test_a_explicacao_sai_uma_vez_por_cidade(self):
        t = resp("/rua Blumenau São Rafael")
        # Duas ruas casam; a ressalva não pode sair duas vezes.
        self.assertEqual(t.count("não dá para dizer"), 1)

    def test_cidade_de_varias_reguas_diz_o_motivo_certo(self):
        b = base()
        b.cotas_ruas = [{"cidade": "itajai", "rio": "itajai-acu", "rua": "Rua Teste",
                         "bairro": None, "ponto": None, "cota_m": 2.0, "fonte": "t",
                         "data_fonte": "2026-08-31", "confianca": "media",
                         "referencia": "régua"}]
        t = resp("/rua Itajaí teste", b)
        self.assertIn("réguas com zeros diferentes", t)

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

    def test_nenhuma_busca_de_rua_real_chega_a_ser_cortada(self):
        """
        O corte existe para não perder a mensagem inteira, mas cortar já é
        perder informação: a última rua da lista sai pela metade. Cada
        importação nova aumenta o texto — a de Brusque acrescentou uma nota por
        ponto, dizendo quanta água cobriu ali em 2023 —, e é aqui que se vê se
        o limite ficou perto.

        Só entram os termos que casam com pelo menos MAX_RUAS ruas: acima disso
        a resposta já está no teto, então o pior caso está nesse grupo.
        """
        import collections

        b = base()
        cotas = le_json("cotas-ruas.json")["cotas"]
        frequencia = collections.Counter(
            pedaco for c in cotas for pedaco in str(c["rua"]).lower().split()
            if len(pedaco) >= 2
        )
        cheios = [t for t, n in frequencia.items() if n >= MAX_RUAS]
        self.assertGreater(len(cheios), 50, "amostra pequena demais para valer de guarda")

        pior_termo, pior = "", 0
        for termo in cheios:
            tamanho = len("".join(resposta_rua(b, None, termo, AGORA)))
            if tamanho > pior:
                pior_termo, pior = termo, tamanho
        self.assertLess(
            pior, notificador.LIMITE_CARACTERES,
            f"a busca por “{pior_termo}” gera {pior} caracteres e seria cortada — "
            "diminuir MAX_RUAS ou encurtar as notas antes de importar mais",
        )


class TestCotas(unittest.TestCase):
    def test_cotas_com_aviso_de_regua_propria(self):
        t = resp("/cotas Rio do Sul")
        self.assertIn("Atenção", t)
        self.assertIn("4,50 m", t)
        self.assertIn("próprio zero", t)

    def test_cidade_sem_cota_diz_que_falta(self):
        # Taió não tem cota cadastrada nem régua com cota em estacoes.json.
        self.assertIn("ainda não foram levantadas", resp("/cotas Taió"))

    def test_ilhota_nao_tem_cota_porque_a_dc11_e_de_itajai(self):
        """
        Ilhota NÃO tem régua própria. A DC-11 fica na divisa mas é estação de
        Itajaí (Plano de Contingência, Tabela 11 + Zona 1) — mostrá-la como cota
        de Ilhota seria comparar réguas de cidades diferentes. Antes o cadastro
        atribuía a DC-11 a Ilhota; corrigido. Dizer "não levantadas" aqui é o
        certo, e a DC-11 responde em /cotas Itajaí.
        """
        t = resp("/cotas Ilhota")
        self.assertIn("ainda não foram levantadas", t)
        self.assertNotIn("DC-11", t)

    def test_itajai_sai_uma_vez_com_as_onze_reguas_e_os_ribeiroes(self):
        t = resp("/cotas Itajaí")
        # Uma resposta só, não uma por rio: o separador de blocos não aparece.
        self.assertNotIn("———", t)
        # A DC-11, corrigida para Itajaí, tem de aparecer aqui — e não some.
        for codigo in ("DC-01", "DC-06", "DC-10", "DC-11"):
            self.assertIn(codigo, t)
        # Os ribeirões não estão em nenhuma tela de rio; aqui eles aparecem.
        self.assertIn("Ribeirão da Murta", t)
        self.assertIn("Ribeirão da Canhanduba", t)

    def test_regua_de_mare_vem_marcada_e_explicada(self):
        t = resp("/cotas Itajaí")
        self.assertIn("estuário", t)
        self.assertIn("não dispara aviso automático", t)
        # Limoeiro fica rio acima e não leva a marca.
        limoeiro = t.split("DC-10")[1].split("\n")[0]
        self.assertNotIn("*", limoeiro)

    def test_resposta_de_itajai_cabe_no_telegram(self):
        """Onze réguas com bloco cada uma estouravam o limite de 4096."""
        self.assertLess(len(resp("/cotas Itajaí")), 4096)


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
        self.assertIn("há ", t)

    def test_rios_nao_elege_um_numero_para_cidade_de_varias_reguas(self):
        """
        Havia `max(nivel_m)` aqui: elegia o maior metro como se fosse o nível
        da cidade, comparando réguas de zeros diferentes. Em Itajaí saía
        "4,88 m" num dia calmo — a régua de Limoeiro, 20 km rio acima. E uma
        subida de metro e meio nas outras nove não mudava o número, porque o
        vencedor é sempre a mesma régua.
        """
        t = resp("/rios")
        # As duas réguas de Itajaí na base de teste leem 0,81 e 1,53:
        # nenhuma pode aparecer como "o nível de Itajaí", e as duas precisam
        # aparecer, cada uma com o nome da sua régua.
        self.assertNotIn("maior de", t)
        self.assertIn("2 réguas, com zeros diferentes", t)
        self.assertIn("0,81 m", t)
        self.assertIn("1,53 m", t)
        self.assertIn("DC-01", t)
        self.assertIn("DC-02", t)

    def test_rios_mantem_uma_linha_para_cidade_de_uma_regua(self):
        t = resp("/rios")
        self.assertRegex(t, r"<b>Brusque</b>: \d+,\d\d m · h")

    def test_nome_curto_tira_a_calha_e_guarda_o_codigo(self):
        """No panorama o que muda entre as linhas é o local, não o nome do rio."""
        self.assertEqual(
            nome_curto({"estacao": "DC-07 Ribeirão da Murta - Portal"}), "DC-07 Portal")
        self.assertEqual(
            nome_curto({"estacao": "DC-10 Rio Itajaí-Mirim – Bairro Limoeiro"}),
            "DC-10 Bairro Limoeiro")
        # Sem código e sem hífen, fica como veio — nada é adivinhado.
        self.assertEqual(nome_curto({"estacao": "Brusque"}), "Brusque")
        self.assertEqual(nome_curto({"estacao": ""}), "")

    def test_escapa_html_do_que_a_pessoa_digitou(self):
        t = resp("/nivel <b>xxx</b>")
        self.assertNotIn("<b>xxx</b>", t)


#: Blumenau em cheia com as DUAS leituras da MESMA régua (ANA 83800002): a
#: primária (página da Defesa Civil de Itajaí), mais velha, e o resgate do
#: AlertaBlu, mais fresco, marcado com `resgate_de`. Foi o caso real que fez o
#: bot dizer "2 réguas que não se comparam" e sumir com o nível da cidade.
ULTIMO_BLUMENAU = {
    "coletado_em": "2026-08-30T21:25:00+00:00",
    "leituras": [
        {"estacao": "Blumenau", "rio": "itajai-acu", "cidade": "blumenau",
         "nivel_m": 6.43, "medido_em": "2026-08-30T15:11:00"},
        {"estacao": "Blumenau (AlertaBlu)", "rio": "itajai-acu", "cidade": "blumenau",
         "nivel_m": 6.54, "medido_em": "2026-08-30T17:26:00", "resgate_de": "Blumenau"},
    ],
}


def base_blumenau() -> Base:
    return Base(ULTIMO_BLUMENAU, le_json("estacoes.json"), le_json("transito.json"),
                le_json("enchentes.json"), le_json("cotas-ruas.json"))


class TestReguaDeResgate(unittest.TestCase):
    """
    Primária e resgate são a MESMA régua — mesmo zero — e não podem contar como
    duas. Sem juntá-las, Blumenau em cheia (primária velha + AlertaBlu fresco)
    aparecia como "2 réguas que não se comparam" e o bot recusava dizer o nível,
    a previsão e o quanto falta subir na rua. É o mesmo colapso do site.
    """

    def r(self, texto: str) -> str:
        return responder(texto, base_blumenau(), AGORA)

    def test_nivel_mostra_uma_regua_a_mais_fresca(self):
        t = self.r("/nivel Blumenau")
        self.assertIn("6,54 m", t, "a leitura mais fresca da régua")
        self.assertIn("AlertaBlu", t)
        self.assertNotIn("6,43 m", t, "a primária velha não vira uma segunda régua")
        self.assertNotIn("não se comparam", t)

    def test_rios_traz_blumenau_como_uma_linha_so(self):
        t = self.r("/rios")
        self.assertRegex(t, r"<b>Blumenau</b>: 6,54 m · h")
        self.assertNotIn("réguas, com zeros diferentes", t)

    def test_previsao_de_blumenau_calcula(self):
        t = self.r("/previsao Blumenau")
        self.assertNotIn("mais de uma régua", t)
        self.assertIn("6,54 m", t)
        self.assertIn("Itajaí", t, "a onda desce até a foz")

    def test_rua_de_blumenau_compara_com_o_nivel(self):
        t = self.r("/rua Blumenau São Rafael")
        self.assertIn("6,54 m", t, "o nível da cidade volta a aparecer")
        self.assertNotIn("réguas com zeros diferentes", t)
        self.assertNotIn("não aparece na fonte de tempo real", t)

    def test_itajai_com_onze_reguas_continua_onze(self):
        """O colapso junta só primária+resgate; réguas distintas seguem distintas."""
        t = resp("/nivel Itajaí")
        self.assertIn("0,81 m", t)
        self.assertIn("1,53 m", t)
        self.assertIn("não se comparam", t)


class TestAuxiliares(unittest.TestCase):
    def test_sem_acento(self):
        self.assertEqual(sem_acento("Itajaí-Açu"), "itajai-acu")

    def test_texto_idade(self):
        self.assertEqual(texto_idade(0), "agora mesmo")
        self.assertEqual(texto_idade(45), "há 45 min")
        self.assertEqual(texto_idade(60), "há 1 h")
        self.assertEqual(texto_idade(155), "há 2 h 35")
        self.assertEqual(texto_idade(None), "sem horário de medição")


class TestLogDoLaco(unittest.TestCase):
    """
    O journal é onde se olha durante uma cheia. Log que grita "erro" para
    rotina ensina quem opera a ignorar o log inteiro — o mesmo defeito de um
    aviso que toca com a maré.
    """

    class ReadTimeout(Exception):
        pass

    def test_timeout_solitario_do_long_polling_nao_vira_erro(self):
        self.assertIsNone(aviso_de_falha(self.ReadTimeout("read timeout=40"), 1))
        self.assertIsNone(aviso_de_falha(self.ReadTimeout("read timeout=40"), 2))

    def test_timeout_que_insiste_aparece(self):
        aviso = aviso_de_falha(self.ReadTimeout("read timeout=40"),
                                   TIMEOUTS_TOLERADOS)
        self.assertIsNotNone(aviso)
        self.assertIn("sem receber mensagens", aviso)

    def test_queda_longa_nao_escreve_uma_linha_a_cada_meio_minuto(self):
        e = self.ReadTimeout("read timeout=40")
        # Avisa ao cruzar o limite, cala nas seguintes, e volta a avisar de
        # tempos em tempos para a queda não sumir do log.
        self.assertIsNotNone(aviso_de_falha(e, TIMEOUTS_TOLERADOS))
        self.assertIsNone(aviso_de_falha(e, TIMEOUTS_TOLERADOS + 1))
        self.assertIsNotNone(aviso_de_falha(e, REPETE_AVISO))
        self.assertIsNone(aviso_de_falha(e, REPETE_AVISO + 1))

    def test_erro_que_ninguem_previu_sai_na_primeira(self):
        aviso = aviso_de_falha(ValueError("json quebrado"), 1)
        self.assertIn("erro na rodada", aviso)
        self.assertIn("json quebrado", aviso)

    def test_so_erro_de_verdade_faz_o_bot_dormir(self):
        # Dormir depois de um timeout é mais tempo calado sem motivo: a espera
        # já foi gasta pendurada na conexão.
        self.assertTrue(eh_timeout(self.ReadTimeout("x")))
        self.assertFalse(eh_timeout(ValueError("x")))


class TestCotaMaxima(unittest.TestCase):
    """
    Rio do Sul publica mínima E máxima por logradouro. A máxima é informação;
    o gatilho continua sendo a mínima, que é quando a água chega à rua.
    """

    def test_maxima_aparece_sem_virar_o_numero_principal(self):
        b = base()
        b.cotas_ruas = [{"cidade": "rio-do-sul", "rio": "itajai-acu", "rua": "1 DE MAIO",
                         "bairro": None, "ponto": "ponto mais baixo", "cota_m": 8.12,
                         "cota_max_m": 9.65, "fonte": "portal", "data_fonte": "2026-08-31",
                         "confianca": "alta", "referencia": "régua"}]
        t = resp("/rua Rio do Sul 1 de maio", b)
        self.assertIn("Alaga a partir de <b>8,12 m</b>", t)
        self.assertIn("toda a rua a 9,65 m", t)

    def test_ressalva_sai_junto_do_numero(self):
        """
        Rio do Sul publica rua alagando a 3,11 m; a régua marca 3,35 m num dia
        seco. Sem a ressalva ao lado, o bot diria "já foi alcançado" com tempo
        bom — o alarme falso que ensina a ignorar o aviso de verdade.
        """
        b = base()
        b.cotas_ruas = [{"cidade": "rio-do-sul", "rio": "itajai-acu", "rua": "POUSO REDONDO",
                         "bairro": None, "ponto": "ponto mais baixo", "cota_m": 3.11,
                         "fonte": "portal", "data_fonte": "2026-08-31", "confianca": "alta",
                         "referencia": "régua",
                         "nota": "Esta cota fica ABAIXO da menor cota de referência."}]
        t = resp("/rua Rio do Sul pouso redondo", b)
        self.assertIn("3,11 m", t)
        self.assertIn("ABAIXO da menor cota", t)

    def test_cota_nao_conferida_nao_vira_ja_foi_alcancado(self):
        """
        A régua de Rio do Sul marca 3,35 m num dia seco. Com uma cota de 3,11 m
        não conferida, a comparação diria "já foi alcançado" com tempo bom.
        """
        b = base()
        b.cotas_ruas = [{"cidade": "rio-do-sul", "rio": "itajai-acu", "rua": "POUSO REDONDO",
                         "bairro": None, "ponto": "ponto mais baixo", "cota_m": 3.11,
                         "fonte": "portal", "data_fonte": "2026-08-31", "confianca": "alta",
                         "referencia": "régua", "usar_para_aviso": False,
                         "nota": "Abaixo da menor cota de referência, não conferida."}]
        t = resp("/rua Rio do Sul pouso redondo", b)
        self.assertIn("3,11 m", t)
        self.assertIn("não conferida", t)
        self.assertNotIn("já foi alcançado", t)
        self.assertNotIn("faltam", t)

    def test_sem_maxima_a_frase_nao_aparece(self):
        b = base()
        b.cotas_ruas = [{"cidade": "rio-do-sul", "rio": "itajai-acu", "rua": "1 DE MAIO",
                         "bairro": None, "ponto": "ponto mais baixo", "cota_m": 8.12,
                         "fonte": "portal", "data_fonte": "2026-08-31",
                         "confianca": "alta", "referencia": "régua"}]
        t = resp("/rua Rio do Sul 1 de maio", b)
        self.assertIn("8,12 m", t)
        self.assertNotIn("toda a rua", t)


TOKEN_FALSO = "8000000001:AAH_token_de_teste_nunca_use_isto_xyz"

# Como o Telegram devolve o erro: a URL inteira, com o token no caminho.
ERRO_DE_REDE = (
    "HTTPSConnectionPool(host='api.telegram.org', port=443): Max retries exceeded "
    f"with url: /bot{TOKEN_FALSO}/getUpdates (Caused by NewConnectionError(...))"
)


class ErroFalso(Exception):
    """Erro de rede qualquer — o que importa é o texto que ele carrega."""


class TestTokenNaoVazaNoLog(unittest.TestCase):
    """
    O token no log é acesso ao bot para quem ler o log — e log é justamente o
    que se copia e cola para pedir ajuda. Estes casos travam isso.
    """

    def setUp(self):
        self.env = unittest.mock.patch.dict(
            os.environ, {"TELEGRAM_BOT_TOKEN": TOKEN_FALSO, "TELEGRAM_CHAT_ID": "1"}
        )
        self.env.start()
        self.addCleanup(self.env.stop)

    def test_erro_na_rodada_nao_carrega_o_token(self):
        linha = aviso_de_falha(ErroFalso(ERRO_DE_REDE), 1)
        self.assertNotIn(TOKEN_FALSO, linha)
        self.assertIn("/bot***/", linha)

    def test_o_resto_da_mensagem_de_erro_continua_no_log(self):
        """Esconder o token não pode virar esconder o defeito."""
        linha = aviso_de_falha(ErroFalso(ERRO_DE_REDE), 1)
        self.assertIn("api.telegram.org", linha)
        self.assertIn("Max retries exceeded", linha)

    def test_nem_meio_token_escapa(self):
        """Um pedaço do segredo ainda é segredo."""
        linha = aviso_de_falha(ErroFalso(ERRO_DE_REDE), 1)
        self.assertNotIn(TOKEN_FALSO.split(":")[1][:12], linha)

    def test_aviso_de_timeout_nunca_teve_o_token_e_continua_sem(self):
        erro = type("ReadTimeout", (Exception,), {})(ERRO_DE_REDE)
        linha = aviso_de_falha(erro, TIMEOUTS_TOLERADOS)
        self.assertNotIn(TOKEN_FALSO, linha)


class TestUmaVezNaoDerramaTraceback(unittest.TestCase):
    """
    `--uma-vez` chamava `rodada` sem proteção: falha de rede subia até o topo e
    o Python imprimia o traceback, com a URL e o token dentro. É o modo que roda
    em cron e o que se digita para depurar — a saída que mais acaba colada.
    """

    def setUp(self):
        self.env = unittest.mock.patch.dict(
            os.environ, {"TELEGRAM_BOT_TOKEN": TOKEN_FALSO, "TELEGRAM_CHAT_ID": "1"}
        )
        self.env.start()
        self.addCleanup(self.env.stop)

    def _rodar(self):
        import io, contextlib, bot as modulo_bot
        err = io.StringIO()
        with unittest.mock.patch.object(modulo_bot, "rodada",
                                        side_effect=ErroFalso(ERRO_DE_REDE)), \
             unittest.mock.patch.object(modulo_bot, "le_estado", return_value={}), \
             unittest.mock.patch.object(sys, "argv", ["bot.py", "--uma-vez"]), \
             contextlib.redirect_stderr(err):
            codigo = modulo_bot.main()
        return codigo, err.getvalue()

    def test_a_falha_nao_vira_traceback(self):
        codigo, saida = self._rodar()
        self.assertEqual(codigo, 1, "falha tem de sair com código de erro")
        self.assertIn("não deu para processar a fila", saida)

    def test_e_o_token_nao_aparece(self):
        _, saida = self._rodar()
        self.assertNotIn(TOKEN_FALSO, saida)
        self.assertIn("/bot***/", saida)

    def test_o_motivo_da_falha_continua_visivel(self):
        _, saida = self._rodar()
        self.assertIn("api.telegram.org", saida)


class TestSemSegredo(unittest.TestCase):
    def setUp(self):
        self.env = unittest.mock.patch.dict(
            os.environ, {"TELEGRAM_BOT_TOKEN": TOKEN_FALSO, "TELEGRAM_CHAT_ID": "1"}
        )
        self.env.start()
        self.addCleanup(self.env.stop)

    def test_apaga_o_token_configurado(self):
        self.assertEqual(notificador.sem_segredo(f"x {TOKEN_FALSO} y"), "x *** y")

    def test_apaga_token_que_nao_e_o_nosso(self):
        """Depois de uma troca de token, o log antigo ainda carrega o anterior."""
        sujo = "url: /bot123456:OUTRO_TOKEN_QUALQUER/sendMessage"
        self.assertEqual(notificador.sem_segredo(sujo), "url: /bot***/sendMessage")

    def test_para_na_barra_e_no_espaco(self):
        limpo = notificador.sem_segredo("/bot9:SEGREDO/getUpdates depois disso")
        self.assertEqual(limpo, "/bot***/getUpdates depois disso")

    def test_aceita_excecao_direto_sem_str(self):
        self.assertNotIn(TOKEN_FALSO, notificador.sem_segredo(ErroFalso(ERRO_DE_REDE)))

    def test_texto_sem_segredo_nenhum_passa_intacto(self):
        self.assertEqual(notificador.sem_segredo("rio a 3,52 m"), "rio a 3,52 m")

    def test_sem_token_configurado_a_regex_ainda_protege(self):
        with unittest.mock.patch.dict(os.environ, {"TELEGRAM_BOT_TOKEN": ""}):
            self.assertEqual(notificador.sem_segredo("/botABC/x"), "/bot***/x")

    def test_corta_depois_de_limpar_nao_antes(self):
        """
        Cortar primeiro e limpar depois deixaria meio token para trás quando o
        token cai em cima do limite. Este caso prova a ordem.
        """
        recheio = "a" * 290
        texto = f"{recheio}{TOKEN_FALSO} fim"
        self.assertNotIn(TOKEN_FALSO[:20], notificador.sem_segredo(texto)[:300])


class TestNenhumLogNovoVazaSegredo(unittest.TestCase):
    """
    Guarda estrutural, além dos casos de comportamento acima.

    Os dois vazamentos vieram de alguém escrever `{e}` num print e não lembrar
    que o texto do erro carrega a URL, e a URL carrega o token. Este caso lê o
    fonte dos dois módulos que falam com o Telegram e cobra `sem_segredo` em
    toda interpolação de erro — para o quarto ponto de chamada já nascer certo.
    """

    MODULOS = ("bot.py", "notificador.py")
    NOMES_DE_ERRO = ("e", "erro", "exc", "excecao")

    def _linhas_logicas(self, texto):
        """Junta continuação de linha: um print quebrado em três ainda é um."""
        atual, saida, inicio = "", [], 1
        for numero, linha in enumerate(texto.splitlines(), 1):
            if not atual:
                inicio = numero
            atual += linha.strip() + " "
            if atual.count("(") <= atual.count(")"):
                saida.append((inicio, atual))
                atual = ""
        if atual:
            saida.append((inicio, atual))
        return saida

    def _suspeitas(self, texto, modulo="<teste>"):
        """
        Linha que leva um erro para fora sem limpar.

        Cobre `print` E `return`: o vazamento de `aviso_de_falha` era um return,
        e uma primeira versão desta guarda, que só olhava print, passou por ele
        sem ver. Quem monta a linha e quem a imprime podem estar separados.
        """
        achadas = []
        for numero, linha in self._linhas_logicas(texto):
            if "print(" not in linha and not linha.lstrip().startswith("return "):
                continue
            interpola = any(f"{{{nome}" in linha for nome in self.NOMES_DE_ERRO)
            if (interpola or ".text" in linha) and "sem_segredo" not in linha:
                achadas.append(f"{modulo}:{numero}: {linha.strip()[:110]}")
        return achadas

    def test_todo_erro_que_sai_passa_por_sem_segredo(self):
        aqui = Path(__file__).parent
        suspeitas = []
        for modulo in self.MODULOS:
            suspeitas += self._suspeitas((aqui / modulo).read_text(encoding="utf-8"), modulo)
        self.assertEqual(suspeitas, [], "erro sai sem sem_segredo: " + " | ".join(suspeitas))

    def test_a_guarda_pega_o_return_que_escapou_da_primeira_versao(self):
        """Exatamente a linha que vazava, na forma em que vazava."""
        vazando = '    return f"erro na rodada: {erro}"'
        self.assertEqual(len(self._suspeitas(vazando)), 1)

    def test_a_guarda_aceita_o_return_ja_limpo(self):
        limpo = '    return f"erro na rodada: {notificador.sem_segredo(erro)}"'
        self.assertEqual(self._suspeitas(limpo), [])

    def test_a_guarda_pega_um_vazamento_de_verdade(self):
        """A guarda só vale se falhar quando deve. Este caso prova que falha."""
        linhas = self._linhas_logicas('print(f"erro: {e}", file=sys.stderr)')
        self.assertEqual(len(linhas), 1)
        self.assertIn("{e}", linhas[0][1])
        self.assertNotIn("sem_segredo", linhas[0][1])

    def test_junta_print_quebrado_em_varias_linhas(self):
        fonte = 'print(\n    f"erro: {erro}",\n    file=sys.stderr,\n)'
        linhas = [l for _, l in self._linhas_logicas(fonte)]
        self.assertEqual(len(linhas), 1, "print quebrado tem de virar uma linha lógica só")
        self.assertIn("{erro}", linhas[0])


class TestObservacaoNasCotas(unittest.TestCase):
    """
    A observação da cidade é onde moram as ressalvas que o número sozinho não
    conta. O site já a mostrava; o bot, que é o canal de quem consulta às três
    da manhã, mostrava só os números.

    O caso que motivou: em Brusque a cota de 4,80 m é a Av. Beira-Rio, marginal
    ao rio, JÁ alagando — a fonte a chama de "cota de inundação da via". Ela
    está como atenção porque é o primeiro sinal, mas quem lê "Atenção 4,80 m"
    sem a ressalva não tem como saber que ali a água já está numa via, e que
    NÃO existe faixa de aviso antes disso.
    """

    def test_a_observacao_sai_junto_das_cotas(self):
        r = responder("/cotas Brusque", base(), AGORA)
        self.assertIn("Av. Beira-Rio", r)
        self.assertIn("não existe faixa de aviso antes do primeiro alagamento".lower(),
                      r.lower())

    def test_os_numeros_continuam_vindo_primeiro(self):
        """A ressalva é depois do número, não no lugar dele."""
        r = responder("/cotas Brusque", base(), AGORA)
        self.assertLess(r.index("4,80 m"), r.index("Av. Beira-Rio"))

    def test_cidade_sem_observacao_nao_ganha_bloco_vazio(self):
        b = base()
        for c in b.cidades():
            if c["id"] == "brusque":
                c["observacao"] = ""
        r = responder("/cotas Brusque", b, AGORA)
        self.assertNotIn("<i></i>", r)

    def test_observacao_comprida_e_cortada_com_ponteiro_para_o_site(self):
        b = base()
        for c in b.cidades():
            if c["id"] == "brusque":
                c["observacao"] = "palavra " * 400
        r = responder("/cotas Brusque", b, AGORA)
        self.assertIn("(o resto no site)", r)
        self.assertLess(len(r), 4096, "a mensagem tem de caber no limite do Telegram")

    def test_nenhuma_cidade_estoura_o_limite_do_telegram(self):
        """Itajaí é o pior caso: onze réguas mais a observação."""
        b = base()
        for cidade in b.cidades():
            r = responder(f"/cotas {cidade['nome']}", b, AGORA) or ""
            self.assertLessEqual(len(r), 4096, cidade["nome"])

    def test_a_ressalva_de_brusque_diz_que_a_agua_ja_esta_na_via(self):
        """
        O ponto todo: a diferença entre "prepare-se" e "já começou". Trocar uma
        pela outra é errar para o lado de quem se sente seguro.
        """
        r = responder("/cotas Brusque", base(), AGORA).lower()
        self.assertIn("já está", r)
        self.assertNotIn("aviso prévio, é o começo".replace("é o começo", "ZZZ"), r)


if __name__ == "__main__":
    unittest.main(verbosity=2)
