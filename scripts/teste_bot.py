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

import bot
import notificador
from bot import (IDADE_MAXIMA_PREVISAO_MIN, LIMITE_COTA_RUA_M, LIMITE_LOCALIZACAO_KM, MAX_RUAS,
                 REPETE_AVISO, TIMEOUTS_TOLERADOS, Base, aviso_de_falha, distancia_km,
                 cheias_perto_do_nivel, data_da_cheia, eh_timeout, faixa_da_leitura,
                 faixa_da_regua, linhas_das_cheias, nome_curto, responder,
                 resposta_localizacao, quilometros, resposta_nivel, resposta_rua,
                 saida_para, sem_acento, texto_idade)
from comum import estacao_por_titulo, estacoes_tempo_real, le_json

RAIZ = Path(__file__).resolve().parent.parent

#: As duas réguas de Itajaí cujo par cota↔leitura foi provado (19/09/2026).
DC06 = "DC-06 Rio Itajaí-Mirim (curso antigo) - Itamirim Clube de Campo"
DC10 = "DC-10 Rio Itajaí-Mirim – Bairro Limoeiro"
DC11 = "DC-11 Rio Itajaí-Açú – Santa Regina (Volta de Cima)"

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
    a jusante para o dia ANTERIOR, com cara de previsão.
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
        self.assertIn("Indaial", r)
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
        Trecho curto com leitura de algumas horas: Blumenau→Gaspar é de 2 h, e
        com 2 h 30 de leitura a janela desse trecho já ficou para trás. Dizer
        "por volta de" um horário passado faz a pessoa procurar no relógio uma
        água que, se veio, veio antes.
        """
        b = self.base_com("blumenau", "Blumenau", 5.00, 2.5)
        r = responder("/previsao Blumenau", b, AGORA)
        self.assertIn("janela já passou", r)
        self.assertNotIn("Gaspar</b>: por volta", r)


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
        # 3,76 m e não 4,80 m desde 06/09/2026: a Av. Beira-Rio de 4,80 vinha da
        # lista da imprensa de Brusque, que não declara a referência da régua.
        t = resp("/rua Beira")
        self.assertIn("Brusque", t)
        self.assertIn("3,76 m", t)

    def test_rua_sem_cota_aparece_com_a_nota_e_sem_numero(self):
        """
        Nulo não é zero: a rua aparece, mas sem número e com o porquê.

        O exemplo era uma rua de Gaspar até a importação do mapa da Defesa Civil
        dar número a ela — e o teste quebrou, que é o comportamento certo: ele
        existe para o caso sem número, não para uma rua específica.

        Quebrou DE NOVO em 06/09/2026, e por isso agora usa fixture. Os cinco
        pontos de Brusque que a fonte descreve por faixa ("entre 5,46 m e
        5,80 m") vinham da lista da imprensa de 17/11/2023, que não declara a
        referência da régua — e a partir daquela data cota sem referência
        declarada não entra na busca. O comportamento continua tendo de valer;
        amarrá-lo a uma linha do arquivo real é que era frágil.
        """
        b = Base(ULTIMO, le_json("estacoes.json"), le_json("transito.json"),
                 le_json("enchentes.json"),
                 {"_meta": {}, "cotas": [{"cidade": "brusque", "rio": "itajai-mirim",
                                          "rua": "Túnel do Terminal Urbano",
                                          "bairro": None, "ponto": None, "cota_m": None,
                                          "referencia": "régua",
                                          "nota": "A fonte descreve a faixa: entre 5,46 m e "
                                                  "5,80 m, sem publicar o valor do ponto.",
                                          "fonte": "teste", "data_fonte": "2026-01",
                                          "confianca": "baixa"}]})
        t = resp("/rua Brusque Túnel do Terminal Urbano", b)
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
                                          "referencia": "régua",
                                          "fonte": "teste", "data_fonte": "2026-01",
                                          "confianca": "baixa"}]})
        t = resp("/rua Brusque Sem Nada", b)
        self.assertIn("não publica a cota exata", t)

    def test_hifen_nao_esconde_a_rua(self):
        """
        Quem digita "Beira-Rio" — como está na placa — tem de achar a "Av. Beira
        Rio" do cadastro, que a fonte grafou sem hífen. Antes de 06/09/2026 lia
        "nenhuma rua com esse nome entre as levantadas", para uma rua levantada.
        """
        com = resp("/rua Brusque Beira-Rio")
        sem = resp("/rua Brusque Beira Rio")
        self.assertNotIn("Nenhuma rua", com)
        self.assertIn("Beira Rio", com)
        self.assertEqual(com.count("Alaga a partir de"), sem.count("Alaga a partir de"))

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
        # Ituporanga segue sem cota cadastrada e sem régua com cota. (Taió tinha
        # este papel até 04/09/2026, quando entraram as faixas do Plano de
        # Contingência da COMPDEC — ver test_taio_mostra_o_monitoramento_antes_da_atencao.)
        self.assertIn("ainda não foram levantadas", resp("/cotas Ituporanga"))

    def test_taio_mostra_o_monitoramento_antes_da_atencao(self):
        """
        Taió tem CINCO fases e o nosso esquema tem quatro nomes.

        O piso de monitoramento (5,00 m) é gravado com o nome que o Plano usa, e
        não remapeado para 'atenção' — a tela não pode afirmar um aviso que a
        COMPDEC não deu. Mas ele precisa sair NA POSIÇÃO CERTA: sem entrar em
        ORDEM_COTAS, a resposta listaria "Monitoramento 5,00 m" depois de
        "Emergência 9,00 m", uma escada que sobe e desce.
        """
        t = resp("/cotas Taió")
        self.assertIn("Monitoramento", t)
        for antes, depois in (("Monitoramento", "Atenção"), ("Atenção", "Alerta"),
                              ("Alerta", "Emergência")):
            self.assertLess(t.index(antes), t.index(depois),
                            f"'{antes}' deveria vir antes de '{depois}' na resposta")

    def test_ilhota_tem_cota_de_referencia_mas_segue_sem_regua_propria(self):
        """
        As duas coisas são independentes, e confundi-las foi o bug antigo.

        Ilhota ganhou as faixas do PLANCON 2025/2028 em 04/09/2026 — cota de
        REFERÊNCIA, para a linha do gráfico e para 'minha rua'. Isso NÃO lhe dá
        nível ao vivo: a DC-11 fica na divisa mas é estação de Itajaí, com zero
        próprio (Plano de Contingência, Tabela 11 + Zona 1), e mostrá-la aqui
        seria comparar réguas de cidades diferentes. Ela responde em /cotas Itajaí.
        """
        t = resp("/cotas Ilhota")
        self.assertIn("9,20 m", t)
        self.assertIn("10,50 m", t)
        # A DC-11 pode ser CITADA — a observação existe justamente para dizer
        # por que ela não serve aqui. O que não pode é ser apresentada como a
        # régua de Ilhota. Conferir a linha "Régua:", e não o texto inteiro:
        # proibir a palavra apagaria a explicação junto com o erro.
        linha_regua = next(l for l in t.split("\n") if l.startswith("Régua:"))
        self.assertIn("Cláudio Jeremias Cadorin", linha_regua)
        self.assertNotIn("DC-11", linha_regua)

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

    def test_rios_segue_a_ordem_do_rio_e_nao_a_alfabetica(self):
        """
        Montante -> jusante, o Açu inteiro (até a foz, Itajaí) e depois o Mirim.
        Alfabético punha Brusque antes de Rio do Sul — o rio de baixo antes da
        cabeceira do de cima. A base tem Rio do Sul (Açu, alto), Itajaí (foz do
        Açu) e Brusque (Mirim).
        """
        t = resp("/rios")
        # Marcadores da CIDADE (negrito fechado), para não casar com o cabeçalho
        # do rio "<b>Itajaí-Açu</b>".
        self.assertLess(t.index("<b>Rio do Sul</b>"), t.index("<b>Itajaí</b>"),
                        "a cabeceira do Açu vem antes da foz")
        self.assertLess(t.index("<b>Itajaí</b>"), t.index("<b>Brusque</b>"),
                        "o Açu inteiro vem antes do Mirim")

    def test_rios_mostra_o_rio_inteiro_com_as_lacunas(self):
        """
        Segue o mapa do rio: as cidades SEM leitura agora entram na posição
        delas, marcadas, e não somem — ausência de dado não pode virar buraco
        invisível. A base de teste não tem Ibirama (Açu) nem Botuverá (Mirim).
        """
        t = resp("/rios")
        self.assertIn("sem leitura agora", t)
        self.assertIn("Ibirama", t)
        self.assertIn("Botuverá", t)
        # E o mapa vem rotulado pelos dois rios, cada um do alto para a foz.
        self.assertIn("Itajaí-Açu", t)
        self.assertIn("Itajaí-Mirim", t)
        self.assertLess(t.index("Itajaí-Açu"), t.index("Itajaí-Mirim"))

    def test_nome_curto_tira_a_calha_e_guarda_o_codigo(self):
        """No panorama o que muda entre as linhas é o local, não o nome do rio."""
        self.assertEqual(
            nome_curto({"estacao": "DC-07 Ribeirão da Murta - Portal"}), "DC-07 Portal")
        self.assertEqual(
            nome_curto({"estacao": "DC-10 Rio Itajaí-Mirim – Bairro Limoeiro"}),
            "DC-10 Bairro Limoeiro")

    def test_rios_distribui_as_reguas_de_itajai_por_rio(self):
        """
        Itajaí é foz dos dois: a régua do Açu fecha o Açu, a do Mirim fecha o
        Mirim (junto de Brusque), e os ribeirões — fora dos eixos — saem à parte.
        """
        # Cada rio com DUAS réguas (como na foz real), para vir o bloco com os
        # nomes das réguas, não a linha única de "um número".
        u = {"coletado_em": "2026-08-30T21:25:00+00:00", "leituras": [
            {"estacao": "Brusque", "rio": "itajai-mirim", "cidade": "brusque",
             "nivel_m": 2.0, "medido_em": "2026-08-30T18:15:00"},
            {"estacao": "DC-01 Rio Itajaí-Açu - ICMBio/CEPSUL", "rio": "itajai-acu",
             "cidade": "itajai", "nivel_m": 0.90, "medido_em": "2026-08-30T18:20:00"},
            {"estacao": "DC-02 Rio Itajaí-Açu - Praça Celso Pereira da Silva",
             "rio": "itajai-acu", "cidade": "itajai", "nivel_m": 0.92,
             "medido_em": "2026-08-30T18:20:00"},
            {"estacao": "DC-10 Rio Itajaí-Mirim – Bairro Limoeiro", "rio": "itajai-mirim",
             "cidade": "itajai", "nivel_m": 4.61, "medido_em": "2026-08-30T18:20:00"},
            {"estacao": "DC-03 Rio Itajaí-Mirim - Captação SEMASA", "rio": "itajai-mirim",
             "cidade": "itajai", "nivel_m": 0.59, "medido_em": "2026-08-30T18:20:00"},
            {"estacao": "DC-07 Ribeirão da Murta - Portal", "rio": "ribeirao-murta",
             "cidade": "itajai", "nivel_m": 0.36, "medido_em": "2026-08-30T18:20:00"},
            {"estacao": "DC-08 Ribeirão Canhanduba - Rua Benjamin Dagnoni",
             "rio": "ribeirao-canhanduba", "cidade": "itajai", "nivel_m": 1.1,
             "medido_em": "2026-08-30T18:20:00"},
        ]}
        b = Base(u, le_json("estacoes.json"), le_json("transito.json"),
                 le_json("enchentes.json"), le_json("cotas-ruas.json"))
        t = resp("/rios", b)
        i_acu = t.index("Itajaí-Açu")
        i_mirim = t.index("Itajaí-Mirim")
        # Açu: as réguas do Açu + o Ribeirão da Murta (que deságua no Açu),
        # tudo ANTES do cabeçalho do Mirim.
        self.assertLess(i_acu, t.index("DC-01"))
        self.assertLess(t.index("DC-01"), i_mirim)
        self.assertLess(t.index("Ribeirão da Murta"), i_mirim)
        self.assertLess(t.index("DC-07"), i_mirim)
        # Mirim: as réguas do Mirim (depois de Brusque) + o Ribeirão Canhanduba.
        self.assertLess(t.index("Brusque"), t.index("DC-10"))
        self.assertLess(i_mirim, t.index("DC-10"))
        self.assertLess(i_mirim, t.index("Ribeirão Canhanduba"))
        self.assertLess(i_mirim, t.index("DC-08"))
        # Não há mais bloco solto de ribeirões.
        self.assertNotIn("Ribeirões de Itajaí", t)
        self.assertNotIn("fora dos eixos", t)

    def test_rios_nao_rotula_curso_quando_a_cidade_tem_um_so(self):
        """As duas réguas de Itajaí na base padrão são ambas do Açu: sem subtítulo."""
        t = resp("/rios")
        self.assertIn("2 réguas, com zeros diferentes", t)
        self.assertNotIn("Rio Itajaí-Açu", t)  # só o cabeçalho "Itajaí-Açu", sem "Rio "
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


class TestDistancia(unittest.TestCase):
    def test_mesmo_ponto_da_zero(self):
        self.assertAlmostEqual(distancia_km((-27.1, -48.9), (-27.1, -48.9)), 0, places=6)

    def test_brusque_guabiruba_sao_os_6_km_medidos(self):
        """Par mais próximo da bacia; o número calibrou o raio de 25 km."""
        d = distancia_km((-27.1007, -48.9172), (-27.0847, -48.9789))
        self.assertAlmostEqual(d, 6.2, delta=0.3)

    def test_um_grau_de_latitude_da_111_km(self):
        self.assertAlmostEqual(distancia_km((-27.0, -49.0), (-28.0, -49.0)), 111.2, delta=0.5)


class TestLocalizacao(unittest.TestCase):
    """Duas camadas: a cota do ponto mais perto, onde houver, e a régua da cidade.

    O que estes testes travam é sobretudo o que a resposta NÃO pode dizer. Um pino
    é a pergunta mais direta que o bot recebe — "a água chega em mim?" — e a
    tentação de responder com precisão que o dado não tem é proporcional.
    """

    # Pontos reais: um colado numa cota levantada de Brusque, um em Blumenau
    # (que não tem cota com coordenada) e um fora da bacia.
    BRUSQUE_COM_COTA = (-27.100666, -48.932929)
    BLUMENAU = (-26.9194, -49.0661)
    FLORIPA = (-27.5954, -48.5480)

    def loc(self, ponto, b=None) -> str:
        return "".join(resposta_localizacao(b or base(), ponto[0], ponto[1], AGORA))

    def test_camada_da_rua_sai_quando_ha_cota_perto(self):
        t = self.loc(self.BRUSQUE_COM_COTA)
        self.assertIn("Bartolomeu Pruner", t)
        self.assertIn("Alaga a partir de", t)
        self.assertIn("7,65 m", t)

    def test_diz_a_DISTANCIA_e_nunca_diz_a_sua_rua(self):
        """A cota é de um PONTO. Chamar de "a sua rua" seria afirmar que o ponto
        levantado é a esquina de quem perguntou — e disso o bot não sabe nada."""
        t = self.loc(self.BRUSQUE_COM_COTA)
        self.assertIn("mais perto de você", t)
        self.assertRegex(t, r"a \d+ m daqui")
        self.assertNotIn("sua rua", t.lower())

    def test_a_IDADE_da_cota_sai_junto(self):
        """Uma cota de 2020 e uma de 2023 não podem chegar com a mesma cara."""
        self.assertIn("Cota levantada em 11/2023", self.loc(self.BRUSQUE_COM_COTA))

    def test_camada_da_cidade_sai_SEMPRE(self):
        """É o piso: onde não há cota perto, ela é a resposta inteira."""
        for ponto in (self.BRUSQUE_COM_COTA, self.BLUMENAU):
            t = self.loc(ponto)
            # Brusque e Blumenau não têm coordenada de régua no cadastro: o
            # cabeçalho diz CIDADE. Chamá-lo de "régua" era a afirmação falsa
            # corrigida em 19/09/2026.
            self.assertIn("Cidade mais próxima", t)
            self.assertNotIn("Régua mais próxima", t)
            self.assertIn("nível do rio", t)

    def test_sem_cota_perto_responde_so_a_cidade_sem_linha_em_branco(self):
        t = self.loc(self.BLUMENAU)
        self.assertIn("Blumenau", t)
        self.assertNotIn("Alaga a partir de", t)
        self.assertFalse(t.startswith("\n"), "a resposta não pode abrir com linha em branco")

    # Centro de Brusque: o ponto levantado mais próximo está a 330 m — fora dos
    # 300 m de uso, dentro dos 2 km de aviso. Medido no cadastro em 17/09/2026.
    BRUSQUE_CENTRO = (-27.0977, -48.9177)

    def test_cota_perto_mas_longe_demais_DIZ_que_existe(self):
        """O silêncio mentia por omissão.

        Antes, um pino aqui saía igualzinho ao de uma cidade sem levantamento
        nenhum — e as duas situações pedem decisões diferentes de quem lê. Agora
        a resposta diz que há ponto levantado na região e a que distância, sem
        usar a cota dele.
        """
        t = self.loc(self.BRUSQUE_CENTRO)
        self.assertIn("Nenhum ponto levantado na sua esquina", t)
        self.assertRegex(t, r"fica a \d+ m")
        self.assertNotIn("Alaga a partir de", t, "a cota de 330 m não pode ser usada")
        self.assertNotIn("faltam", t.lower())
        self.assertIn("Cidade mais próxima", t, "a camada da cidade continua saindo")

    def test_sem_levantamento_na_regiao_nao_inventa_o_aviso(self):
        """Em Blumenau a cota com coordenada mais próxima está a dezenas de km.

        Dizer "o mais próximo fica a 23.000 m" seria ruído, não informação.
        """
        self.assertNotIn("Nenhum ponto levantado na sua esquina", self.loc(self.BLUMENAU))

    def test_transversal_sai_como_ESQUINA_e_nao_entre_parenteses(self):
        """"Rua A (Rua B)" se lê como se B fosse outro nome de A. É a esquina.

        São 454 dos 1.615 pontos de Gaspar (medido em 17/09/2026). Quem recebe o
        pino precisa reconhecer o lugar para julgar se aquele ponto é a esquina
        dele — é a única pergunta que a camada de rua responde.
        """
        from bot import nome_do_ponto
        self.assertEqual(
            nome_do_ponto({"rua": "Rua Luiz Franzói", "ponto": "Rua Gertrudes Seberino da Silva"}),
            "Rua Luiz Franzói — esquina com Rua Gertrudes Seberino da Silva")
        self.assertEqual(nome_do_ponto({"rua": "Rua X", "ponto": "Av. Beira Rio"}),
                         "Rua X — esquina com Av. Beira Rio")

    def test_numero_e_referencia_continuam_no_parentese(self):
        """A fonte diz que o campo traz transversal, número da casa OU referência.

        Escrever "nº 47" afirmaria número de casa, e a fonte não garante isso.
        """
        from bot import nome_do_ponto
        self.assertEqual(nome_do_ponto({"rua": "Rua Alvorada", "ponto": "47"}),
                         "Rua Alvorada (47)")
        self.assertEqual(nome_do_ponto({"rua": "Rua São Rafael", "ponto": "final da rua"}),
                         "Rua São Rafael (final da rua)")
        self.assertEqual(nome_do_ponto({"rua": "Rua Y", "ponto": "Esquina - Rua Amazonas"}),
                         "Rua Y (Esquina - Rua Amazonas)")
        self.assertEqual(nome_do_ponto({"rua": "Rua Z", "ponto": None}), "Rua Z")

    def test_fora_do_raio_diz_NAO_SEI_e_nao_oferece_regua_distante(self):
        """A régua de uma cidade a 66 km não diz nada sobre o rio ao lado de quem
        perguntou. Oferecê-la seria pior que o silêncio."""
        t = self.loc(self.FLORIPA)
        self.assertIn("fora da área", t)
        self.assertIn("Defesa Civil do seu município", t)
        self.assertNotIn("Régua mais próxima", t)
        self.assertNotIn("Alaga a partir de", t)

    def test_o_raio_da_cidade_e_o_constante_declarado(self):
        b = base()
        perto = b.cidade_mais_proxima(*self.FLORIPA)
        self.assertGreater(perto[1], LIMITE_LOCALIZACAO_KM)
        perto_br = b.cidade_mais_proxima(*self.BRUSQUE_COM_COTA)
        self.assertLess(perto_br[1], LIMITE_LOCALIZACAO_KM)

    def test_cota_longe_demais_NAO_e_oferecida(self):
        """Ponto a mais de LIMITE_COTA_RUA_M cai para a camada da cidade, que é
        menos específica e continua verdadeira."""
        b = base()
        c = b.cota_mais_proxima(*self.BLUMENAU)
        if c is not None:
            self.assertGreater(c[1], LIMITE_COTA_RUA_M)
        self.assertNotIn("Alaga a partir de", self.loc(self.BLUMENAU))

    def test_coordenada_invalida_nao_estoura(self):
        for lat, lon in ((None, None), ("x", "y"), (999, 999), (True, False)):
            t = "".join(resposta_localizacao(base(), lat, lon, AGORA))
            self.assertIn("Não consegui ler", t)

    def test_toda_resposta_traz_o_rodape_e_o_199(self):
        for ponto in (self.BRUSQUE_COM_COTA, self.BLUMENAU, self.FLORIPA):
            self.assertIn("199", self.loc(ponto))

    #: Coordenada a 31 m de uma cota levantada de Brusque — dentro do limite de
    #: 300 m, então a camada de rua abre. Achada no cadastro real, não chutada.
    BRUSQUE_PERTO_DE_COTA = (-27.10267, -48.917600)

    def _base_brusque(self, leituras, sc=None):
        return Base({"leituras": leituras}, le_json("estacoes.json"),
                    le_json("transito.json"), le_json("enchentes.json"),
                    le_json("cotas-ruas.json"), sc)

    def test_so_o_bruto_estadual_diz_por_que_nao_da_para_comparar(self):
        """ACHADO no teste de campo de 18/09/2026: a fonte municipal de Brusque
        parou, o bot caiu no BRUTO da rede estadual, e a linha "faltam X m"
        sumiu do bloco da rua SEM UMA PALAVRA. A guarda que existia só cobria a
        cidade de várias réguas; com ZERO leituras municipais não disparava."""
        b = self._base_brusque([], {"leituras": [
            {"cidade": "brusque", "rio": "itajai-mirim", "estacao": "SDC-SC Brusque",
             "nivel_bruto_m": 1.31, "medido_em": "2026-08-30T18:20:00"}]})
        t = "".join(resposta_localizacao(b, *self.BRUSQUE_PERTO_DE_COTA, AGORA))
        self.assertIn("Alaga a partir de", t)
        self.assertNotIn("faltam", t)
        self.assertIn("Quanto falta subir não dá para dizer", t)
        self.assertIn("BRUTO da rede estadual", t)
        # E NÃO pode dizer que a cidade some da fonte: o número está na tela.
        self.assertNotIn("não aparece na fonte de tempo real", t)

    def test_o_bruto_nao_e_explicado_duas_vezes_na_mesma_mensagem(self):
        """ENXUGADO em 18/09/2026, depois do teste de campo. Os dois blocos
        diziam a mesma coisa em dez linhas: "zero próprio, não se compara com
        esta cota" na camada de rua e "zero próprio, não comparável com as
        cotas desta cidade" na da régua. Ficou uma vez em cada lugar, sem
        repetir as palavras — 93 caracteres a menos.

        As duas frases CONTINUAM existindo, e é de propósito: o `/rua` sai sem
        o bloco da régua, e o `/nivel` sai sem o da rua. Cada uma tem de se
        bastar sozinha; o que não pode é as duas juntas dizerem o mesmo.
        """
        b = self._base_brusque([], {"leituras": [
            {"cidade": "brusque", "rio": "itajai-mirim", "estacao": "SDC-SC Brusque",
             "nivel_bruto_m": 1.31, "medido_em": "2026-08-30T18:20:00"}]})
        t = "".join(resposta_localizacao(b, *self.BRUSQUE_PERTO_DE_COTA, AGORA))
        self.assertEqual(t.count("zero próprio"), 1)
        # A abertura "Quanto falta subir não dá para dizer" já diz que não se
        # compara; repetir isso no fim da mesma frase era o pleonasmo.
        self.assertNotIn("não se compara com esta cota", t)
        self.assertNotIn("não para dizer quanto falta para uma cota", t)
        # E nenhuma das duas perdeu o que a torna suficiente sozinha.
        self.assertIn("outra régua, com outro zero", t)
        self.assertIn("não comparável", t)

    def test_sem_leitura_nenhuma_e_outro_motivo_que_o_bruto(self):
        """"Não há leitura" e "há leitura, com outro zero" são situações
        diferentes e pedem decisões diferentes de quem lê."""
        b = self._base_brusque([])
        t = "".join(resposta_localizacao(b, *self.BRUSQUE_PERTO_DE_COTA, AGORA))
        self.assertIn("não aparece na fonte de tempo real", t)
        self.assertNotIn("BRUTO da rede estadual", t)

    def test_com_leitura_municipal_a_comparacao_volta(self):
        b = self._base_brusque([{"estacao": "Brusque", "rio": "itajai-mirim",
                                 "cidade": "brusque", "nivel_m": 1.94,
                                 "medido_em": "2026-08-30T18:20:00"}])
        t = "".join(resposta_localizacao(b, *self.BRUSQUE_PERTO_DE_COTA, AGORA))
        self.assertIn("faltam", t)
        self.assertNotIn("Quanto falta subir não dá para dizer", t)

    def test_a_rua_nao_desmente_o_proprio_bot(self):
        """O `/rua` dizia "a cidade não aparece na fonte de tempo real que
        coletamos" enquanto o bot TINHA o número e o exibia no pino, na mesma
        sessão. Frase falsa é pior que silêncio: ensina que o projeto não cobre
        Brusque. Os dois caminhos saem da MESMA função agora."""
        b = self._base_brusque([], {"leituras": [
            {"cidade": "brusque", "rio": "itajai-mirim", "estacao": "SDC-SC Brusque",
             "nivel_bruto_m": 1.31, "medido_em": "2026-08-30T18:20:00"}]})
        brusque = [c for c in b.cidades() if c["id"] == "brusque"][0]
        t = "".join(resposta_rua(b, brusque, "Bepe Rosa", AGORA))
        self.assertNotIn("não aparece na fonte de tempo real", t)
        self.assertIn("BRUTO da rede estadual", t)

    def test_blumenau_nao_publica_distancia_ate_uma_estacao_de_chuva(self):
        """A `coordenadas` de Blumenau é a da DCSC-00026, estação de CHUVA — não
        é a régua. O "a 6,9 km em linha reta" saía medido até ela, e era dito a
        quem está a algumas centenas de metros da régua que deu o número da
        linha seguinte (pino real, 18/09/2026)."""
        t = self.loc(self.BLUMENAU)
        self.assertIn("Cidade mais próxima", t)
        self.assertNotIn("Régua mais próxima", t)
        self.assertNotIn("em linha reta", t)
        # A omissão é DITA. Sumir calado é o defeito que o aviso de cota tinha.
        self.assertIn("A distância não sai", t)

    def test_sem_coordenada_de_regua_a_distancia_fica_mas_diz_ate_onde(self):
        """REESCRITO em 19/09/2026. Antes dizia "ausência do campo mantém a
        distância", e mantinha — só que anunciada como distância até a RÉGUA.
        Ausência de prova nunca foi prova: em Brusque a coordenada é o ponto de
        referência da cidade, e o cadastro não tem a da régua.

        O número não some, porque some informação boa junto. O que some é a
        afirmação falsa: agora a linha diz até ONDE ela mede.
        """
        t = self.loc(self.BRUSQUE_COM_COTA)
        self.assertIn("em linha reta", t)
        self.assertIn("ponto de referência da cidade", t)
        self.assertNotIn("Régua mais próxima", t)
        self.assertNotIn("A distância não sai", t)

    def test_so_blumenau_declara_que_o_pino_nao_e_a_regua(self):
        """Trava de cadastro: cidade nova com o campo `false` cai aqui, e é para
        cair — quem o põe tem de saber que está tirando número da tela."""
        sem = {c["id"] for c in base().cidades()
               if c.get("coordenadas_sao_da_regua") is False}
        self.assertEqual(sem, {"blumenau"})

    def test_fora_da_bacia_ainda_diz_a_distancia(self):
        """Lá o número continua: a 60 km, os ~7 km de erro do pino de Blumenau
        não mudam decisão nenhuma, e a distância é o que dá à pessoa o tamanho
        do "não sei" em vez de só um "não"."""
        t = self.loc(self.FLORIPA)
        self.assertIn("A mais próxima fica a", t)

    def test_fora_da_bacia_tem_rodape_curto_sem_alertablu_nem_sc(self):
        """Achado no teste de campo de 18/09/2026, com o pino a 60,1 km.

        O bot recusava dar número — certo — e logo abaixo mandava seguir o
        AlertaBlu (sistema de Blumenau) e a Defesa Civil de SC (que pode não ser
        nem o estado da pessoa). Fora da bacia as duas viram ruído, e vinham
        DEPOIS de o corpo já ter dito "Procure a Defesa Civil do seu município".
        """
        t = self.loc(self.FLORIPA)
        self.assertIn("fora da área", t)
        self.assertNotIn("AlertaBlu", t)
        self.assertNotIn("Defesa Civil de SC", t)
        # Encurtar não pode virar tirar a ressalva nem o telefone.
        self.assertIn("não é alerta oficial", t)
        self.assertIn("199", t)
        # E a frase do município sai UMA vez, não duas.
        self.assertEqual(t.count("Defesa Civil do seu município"), 1)

    def test_dentro_da_bacia_mantem_o_rodape_inteiro(self):
        """A outra metade: o rodapé curto não pode vazar para quem está dentro,
        que é justamente quem precisa saber do AlertaBlu e da Defesa Civil de SC."""
        for ponto in (self.BRUSQUE_COM_COTA, self.BLUMENAU):
            t = self.loc(ponto)
            self.assertNotIn("fora da área", t)
            self.assertIn("AlertaBlu", t)
            self.assertIn("Defesa Civil de SC", t)

    def test_coordenada_ilegivel_mantem_o_rodape_inteiro(self):
        """Não é o mesmo caso: a pessoa pode estar DENTRO da bacia e o que
        falhou foi a leitura do pino. Sem saber onde ela está, não se pode
        decidir que o AlertaBlu não serve para ela."""
        t = "".join(resposta_localizacao(base(), None, None, AGORA))
        self.assertIn("Não consegui ler", t)
        self.assertIn("AlertaBlu", t)

    def test_nenhuma_resposta_estoura_o_limite_do_telegram(self):
        """Mensagem recusada pelo Telegram é silêncio, que é o pior resultado."""
        for ponto in (self.BRUSQUE_COM_COTA, self.BLUMENAU, self.FLORIPA):
            self.assertLess(len(self.loc(ponto)), 4096)

    def test_cidade_com_VARIAS_reguas_nao_diz_quanto_falta(self):
        """Mesma regra do /rua: com zeros diferentes, nenhuma régua sozinha é "o
        nível da cidade", e "faltam 2,30 m" sairia medido contra a errada."""
        b = base()
        itajai = [c for c in b.cidades() if c["id"] == "itajai"][0]
        self.assertGreater(len(b.leituras_da_cidade("itajai", AGORA)), 1)
        t = "".join(resposta_localizacao(b, *itajai["coordenadas"], AGORA))
        self.assertNotIn("faltam", t)


    def test_o_PINO_do_telegram_chega_a_resposta(self):
        """Até 16/09/2026 o laço exigia `text` e a localização caía fora em
        silêncio: a pessoa mandava onde estava e o bot não respondia nada."""
        msg = {"chat": {"id": 1},
               "location": {"latitude": self.BRUSQUE_COM_COTA[0],
                            "longitude": self.BRUSQUE_COM_COTA[1]}}
        saida = saida_para(msg, base(), AGORA)
        self.assertIsNotNone(saida)
        self.assertIn("Bartolomeu Pruner", saida)

    def test_localizacao_AO_VIVO_tambem_responde(self):
        """O app manda a localização ao vivo como `edited_message`, que o laço já
        lia — o tipo da mensagem é o mesmo, então nada extra é preciso."""
        msg = {"chat": {"id": 1}, "location": {"latitude": self.BLUMENAU[0],
                                               "longitude": self.BLUMENAU[1]}}
        self.assertIn("Blumenau", saida_para(msg, base(), AGORA))

    def test_mensagem_de_texto_continua_indo_para_o_responder(self):
        self.assertIn("Cotas de rua", saida_para({"text": "/rua"}, base(), AGORA))

    def test_mensagem_sem_texto_e_sem_pino_nao_responde(self):
        self.assertIsNone(saida_para({"chat": {"id": 1}}, base(), AGORA))


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


#: Nível BRUTO estadual: Ibirama não tem fonte municipal na base de teste (é
#: lacuna no /rios); Rio do Sul TEM (3,52 no ULTIMO) — o bruto dele não pode
#: aparecer, porque a municipal manda.
NIVEL_SC = {"leituras": [
    {"codigo": "DCSC-00020", "estacao": "SDC-SC Ibirama", "cidade": "ibirama",
     "origem": "estadual", "datum": "bruto_estadual", "offset_datum": None,
     "usar_para_cota": False, "nivel_bruto_m": 2.83, "medido_em": "2026-08-30T18:10:00"},
    {"codigo": "DCSC-00013", "estacao": "SDC-SC Rio do Sul", "cidade": "rio-do-sul",
     "origem": "estadual", "datum": "bruto_estadual", "offset_datum": None,
     "usar_para_cota": False, "nivel_bruto_m": 6.52, "medido_em": "2026-08-30T18:10:00"},
]}


def base_sc() -> Base:
    return Base(ULTIMO, le_json("estacoes.json"), le_json("transito.json"),
                le_json("enchentes.json"), le_json("cotas-ruas.json"), NIVEL_SC)


class TestNivelEstadualBruto(unittest.TestCase):
    """
    O nível bruto estadual preenche as lacunas do /rios (cidades sem fonte
    municipal), mas rotulado e nunca como cota: fica FORA de leituras_da_cidade,
    então /rua e /previsao não o tocam; onde há municipal, a municipal manda.
    """

    def r(self, texto: str) -> str:
        return responder(texto, base_sc(), AGORA)

    def test_rios_preenche_a_lacuna_com_bruto_rotulado(self):
        t = self.r("/rios")
        self.assertIn("2,83 m", t)
        self.assertIn("bruto estadual", t)

    def test_nivel_sem_municipal_mostra_bruto_nao_comparavel(self):
        t = self.r("/nivel Ibirama")
        self.assertIn("2,83 m", t)
        self.assertIn("rede estadual", t)
        self.assertIn("não comparável", t)

    def test_municipal_manda_onde_ela_existe(self):
        t = self.r("/rios")
        self.assertNotIn("6,52", t, "o bruto de Rio do Sul não entra: há municipal")
        n = responder("/nivel Rio do Sul", base_sc(), AGORA)
        self.assertIn("3,52 m", n)
        self.assertNotIn("rede estadual", n)

    def test_bruto_nao_entra_na_previsao(self):
        """Bruto não é cota-comparável: previsão de cidade que só tem bruto recusa."""
        t = self.r("/previsao Ibirama")
        self.assertIn("não há leitura ao vivo", t)

    def test_bruto_nao_vira_faltam_na_rua(self):
        b = base_sc()
        b.cotas_ruas = [{"cidade": "ibirama", "rio": "itajai-acu", "rua": "Rua Teste",
                         "bairro": None, "ponto": None, "cota_m": 5.0, "fonte": "t",
                         "data_fonte": "2026", "confianca": "media", "referencia": "régua"}]
        t = responder("/rua Ibirama Teste", b, AGORA)
        self.assertNotIn("faltam", t)

    def test_sem_arquivo_estadual_nada_muda(self):
        """Base sem nivel_sc: o bruto é vazio e o /rios volta a 'sem leitura agora'."""
        t = resp("/nivel Ibirama")
        self.assertIn("Sem leitura ao vivo", t)


class TestAuxiliares(unittest.TestCase):
    def test_sem_acento(self):
        self.assertEqual(sem_acento("Itajaí-Açu"), "itajai-acu")

    def test_texto_idade(self):
        self.assertEqual(texto_idade(0), "agora mesmo")
        self.assertEqual(texto_idade(45), "há 45 min")
        self.assertEqual(texto_idade(60), "há 1 h")
        self.assertEqual(texto_idade(155), "há 2 h 35")
        self.assertEqual(texto_idade(None), "sem horário de medição")

    def test_acima_de_dois_dias_sai_em_dias(self):
        """ACHADO em 19/09/2026 montando o pino de Indaial: a leitura de 12/09
        saía como "há 163 h 30". Não estava errado — eram 163 horas e 30
        minutos — e ninguém lê isso como "seis dias e meio". A idade existe para
        a pessoa saber se o número serve; escrita assim, não serve para nada."""
        self.assertEqual(texto_idade(9810), "há 6,8 dias")   # o caso real
        self.assertEqual(texto_idade(2880), "há 2 dias")
        self.assertEqual(texto_idade(4320), "há 3 dias")

    def test_ate_48_h_fica_em_horas(self):
        """A hora é a unidade da cheia: numa subida, "há 30 h" diz mais do que
        "há 1,3 dias"."""
        self.assertEqual(texto_idade(1440), "há 24 h")
        self.assertEqual(texto_idade(2879), "há 47 h 59")

    def test_acima_de_dez_dias_a_fracao_deixa_de_importar(self):
        """Quando a resposta já é "isto é de outro mês", a casa decimal é ruído.
        568 dias é o maior intervalo medido no documento de Indaial."""
        self.assertEqual(texto_idade(14400), "há 10 dias")
        self.assertEqual(texto_idade(817920), "há 568 dias")

    def test_nao_sai_virgula_zero(self):
        """"há 2,0 dias" tem cara de número gerado."""
        for m in (2880, 4320, 5760):
            with self.subTest(m=m):
                self.assertNotIn(",0 dias", texto_idade(m))


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

    Em Brusque, a referência histórica de alagamento da Av. Beira-Rio (4,80 m)
    não é a atenção cadastrada (3,00 m). A mensagem precisa conservar essa
    distinção e a ressalva sobre a referência das cotas de rua.
    """

    def test_a_observacao_sai_junto_das_cotas(self):
        r = responder("/cotas Brusque", base(), AGORA)
        self.assertIn("Av. Beira-Rio", r)
        self.assertIn("não é o limiar de atenção vigente no cadastro", r.lower())
        self.assertNotIn("não existe faixa de aviso antes do primeiro alagamento", r.lower())

    def test_os_numeros_continuam_vindo_primeiro(self):
        """A ressalva é depois do número, não no lugar dele."""
        r = responder("/cotas Brusque", base(), AGORA)
        self.assertLess(r.index("Atenção: <b>3,00 m</b>"), r.index("Av. Beira-Rio"))
        self.assertLess(r.index("Emergência: <b>5,00 m</b>"), r.index("Av. Beira-Rio"))

    def test_cidade_sem_observacao_nao_ganha_bloco_vazio(self):
        b = base()
        for c in b.estacoes["rios"]["itajai-mirim"]["cidades"]:
            if c["id"] == "brusque":
                c["observacao"] = ""
        r = responder("/cotas Brusque", b, AGORA)
        self.assertNotIn("<i></i>", r)
        self.assertNotIn("Av. Beira-Rio", r)

    def test_observacao_comprida_e_cortada_com_ponteiro_para_o_site(self):
        b = base()
        for c in b.estacoes["rios"]["itajai-mirim"]["cidades"]:
            if c["id"] == "brusque":
                c["observacao"] = "palavra " * 400
        r = responder("/cotas Brusque", b, AGORA)
        self.assertIn("palavra palavra", r)
        self.assertIn("(o resto no site)", r)
        self.assertLess(len(r), 4096, "a mensagem tem de caber no limite do Telegram")

    def test_nenhuma_cidade_estoura_o_limite_do_telegram(self):
        """Itajaí é o pior caso: onze réguas mais a observação."""
        b = base()
        for cidade in b.cidades():
            r = responder(f"/cotas {cidade['nome']}", b, AGORA) or ""
            self.assertLessEqual(len(r), 4096, cidade["nome"])

    def test_a_ressalva_de_brusque_nao_promove_a_regua_estadual(self):
        """O nome da ponte não autoriza subtrair nível estadual de cota de rua."""
        r = responder("/cotas Brusque", base(), AGORA).lower()
        self.assertIn("não use o nível bruto estadual", r)
        self.assertIn("enquanto esse vínculo não estiver comprovado", r)
        self.assertNotIn("atenção: <b>4,80 m</b>", r)


class NomesDaFonteNoBot(unittest.TestCase):
    """O /cotas escreve o nome que a COMPDEC usa, não o nosso."""

    def test_alerta_maximo_de_blumenau(self):
        from bot import linhas_de_cotas, rotulo_cota
        nomes = {"emergencia": "Alerta Máximo", "monitoramento": "Observação", "_por_que": "x"}
        self.assertEqual(rotulo_cota("emergencia", nomes), "Alerta Máximo")
        self.assertEqual(rotulo_cota("atencao", nomes), "Atenção")
        self.assertEqual(rotulo_cota("emergencia", None), "Emergência")
        self.assertEqual(rotulo_cota("_por_que", nomes), "_por_que")
        linhas = linhas_de_cotas({"monitoramento": 3.0, "atencao": 4.0, "emergencia": 8.0}, nomes)
        self.assertIn("Observação", linhas[0])
        self.assertIn("Alerta Máximo", linhas[-1])
        self.assertNotIn("Emergência", "".join(linhas))


class TestFaixaJuntoDoNivel(unittest.TestCase):
    """A faixa sai junto do número — e SÓ onde o par cota↔leitura foi provado.

    Achado em 18/09/2026 testando o pino de Blumenau: 8,40 m, 40 cm acima do
    Alerta Máximo, e a resposta era o número puro. O caminho do aviso do mesmo
    bot já dizia a faixa; quem perguntava recebia menos que quem esperava.
    """

    def com(self, cidade_id: str, rio: str, estacao: str, nivel: float,
            extra: list[dict] | None = None) -> str:
        leituras = [{"estacao": estacao, "rio": rio, "cidade": cidade_id,
                     "nivel_m": nivel, "medido_em": "2026-08-30T18:20:00"}]
        leituras += extra or []
        b = Base({"leituras": leituras}, le_json("estacoes.json"),
                 le_json("transito.json"), le_json("enchentes.json"))
        cidade = [c for c in b.cidades() if c["id"] == cidade_id and c["rio"] == rio][0]
        return "".join(resposta_nivel(b, cidade, AGORA))

    def test_blumenau_acima_do_alerta_maximo_diz_o_nome_da_fonte(self):
        saida = self.com("blumenau", "itajai-acu", "Blumenau", 8.40)
        self.assertIn("8,40 m", saida)
        # O nome é o da COMPDEC ("Alerta Máximo"), não o nosso ("Emergência").
        self.assertIn("Alerta Máximo", saida)
        self.assertNotIn("Emergência", saida)
        self.assertIn("8,00 m", saida)

    def test_blumenau_abaixo_de_tudo_nomeia_o_primeiro_degrau(self):
        saida = self.com("blumenau", "itajai-acu", "Blumenau", 1.42)
        self.assertIn("Abaixo da primeira cota", saida)
        self.assertIn("3,00 m", saida)
        # Sem bolinha verde: selo de segurança colado num número, não.
        self.assertNotIn("🟢", saida)

    def test_rio_do_sul_nao_ganha_faixa_a_cota_e_de_outra_regua(self):
        """A trava que importa. Cota da Ponte Dom Tito Buss, leitura da Estação
        MKS: 88 de 88 leituras acima da 'atenção' com tempo bom. `cotas_verificado`
        é False, e sem esta guarda o bot soaria alarme permanente."""
        saida = self.com("rio-do-sul", "itajai-acu", "Rio do Sul Estação MKS", 6.90)
        self.assertIn("6,90 m", saida)
        self.assertNotIn("Acima da cota", saida)
        self.assertNotIn("Abaixo da primeira cota", saida)

    def test_duas_reguas_na_cidade_calam_a_faixa(self):
        """`cotas_m` é da CIDADE; com duas réguas não se sabe de qual delas."""
        saida = self.com("blumenau", "itajai-acu", "Blumenau", 8.40, extra=[
            {"estacao": "Blumenau — outra régua", "rio": "itajai-acu",
             "cidade": "blumenau", "nivel_m": 2.10, "medido_em": "2026-08-30T18:20:00"}])
        self.assertNotIn("Acima da cota", saida)

    def test_resgate_do_alertablu_continua_uma_regua_e_ganha_faixa(self):
        """Primária + AlertaBlu são a MESMA régua (`resgate_de`): `por_regua`
        junta as duas, então a faixa sai — o oposto do teste acima."""
        saida = self.com("blumenau", "itajai-acu", "Blumenau", 3.90, extra=[
            {"estacao": "Blumenau (AlertaBlu)", "rio": "itajai-acu", "cidade": "blumenau",
             "nivel_m": 8.40, "medido_em": "2026-08-30T18:28:00",
             "resgate_de": "Blumenau"}])
        self.assertIn("8,40 m", saida)
        self.assertIn("Alerta Máximo", saida)

    def test_nivel_implausivel_nao_vira_abaixo_da_primeira_cota(self):
        """Sensor mudo devolvendo 0,00 m na cheia é a frase mais perigosa que
        este bot poderia escrever. Mesma trava de `alerta_cotas`."""
        saida = self.com("blumenau", "itajai-acu", "Blumenau", 0.0)
        self.assertNotIn("Abaixo da primeira cota", saida)
        self.assertNotIn("Acima da cota", saida)

    def test_so_as_cinco_cidades_com_par_provado(self):
        """Trava de cadastro: se alguém marcar `cotas_verificado: true` sem
        provar o par, este teste cai junto — e é para cair."""
        b = base()
        com_faixa = {c["id"] for c in b.cidades() if c.get("cotas_verificado") is True}
        self.assertEqual(com_faixa,
                         {"ascurra", "indaial", "blumenau", "gaspar", "brusque"})

    def test_o_pino_de_blumenau_carrega_a_faixa(self):
        """Fecha o caminho inteiro: pino -> camada da cidade -> faixa."""
        leituras = [{"estacao": "Blumenau", "rio": "itajai-acu", "cidade": "blumenau",
                     "nivel_m": 8.40, "medido_em": "2026-08-30T18:20:00"}]
        b = Base({"leituras": leituras}, le_json("estacoes.json"),
                 le_json("transito.json"), le_json("enchentes.json"),
                 le_json("cotas-ruas.json"))
        saida = "".join(resposta_localizacao(b, -26.9194, -49.0661, AGORA))
        self.assertIn("Alerta Máximo", saida)
        # Blumenau não tem cota de rua com coordenada: a camada de rua não abre,
        # e o aviso de "nenhum ponto na sua esquina" também não (a mais próxima
        # fica a dezenas de km). A resposta não pode começar em branco.
        self.assertNotIn("Nenhum ponto levantado", saida)
        # Blumenau não tem coordenada de régua: o cabeçalho diz CIDADE.
        self.assertTrue(saida.startswith("📍 Cidade mais próxima"))


class TestFaixaPorRegua(unittest.TestCase):
    """Itajaí tem onze réguas e nenhum "nível da cidade" — mas cada régua tem a
    cota DELA, e comparar uma com a própria não mistura zero nenhum.

    Achado em 19/09/2026, no teste de campo do pino em Itajaí, logo depois de o
    coletor do portal novo devolver as onze: a DC-11 Santa Regina saiu em
    2,39 m, com a primeira cota dela em 3,00 m, e o pino mandou o número pelado.
    Quem mora na Volta de Cima não tinha como saber se faltavam 61 cm.
    """

    def itajai(self, leituras: list[tuple[str, str, float]]) -> str:
        u = {"fonte_itajai_ok": True, "leituras": [
            {"estacao": t, "rio": r, "cidade": "itajai", "nivel_m": n,
             "medido_em": "2026-08-30T18:20:00"} for t, r, n in leituras]}
        b = Base(u, le_json("estacoes.json"), le_json("transito.json"),
                 le_json("enchentes.json"))
        cidade = [c for c in b.cidades() if c["id"] == "itajai"][0]
        return "".join(resposta_nivel(b, cidade, AGORA))

    def test_dc11_abaixo_de_tudo_nomeia_o_primeiro_degrau(self):
        saida = self.itajai([(DC11, "itajai-acu", 2.39)])
        self.assertIn("2,39 m", saida)
        self.assertIn("Abaixo da primeira cota", saida)
        self.assertIn("3,00 m", saida)
        self.assertNotIn("🟢", saida)  # nada de selo de segurança num número

    def test_dc11_acima_da_emergencia(self):
        saida = self.itajai([(DC11, "itajai-acu", 5.20)])
        self.assertIn("Acima da cota", saida)
        self.assertIn("Emergência", saida)
        self.assertIn("5,00 m", saida)

    def test_dc10_usa_a_escada_dela_nao_a_da_dc11(self):
        """8,00 m contra 3,00 m: se a cota viesse da outra régua, 3,93 m sairia
        como 'acima da Emergência' numa régua que está tranquila."""
        saida = self.itajai([(DC10, "itajai-mirim", 3.93)])
        self.assertIn("Abaixo da primeira cota", saida)
        self.assertIn("8,00 m", saida)
        self.assertNotIn("Acima da cota", saida)

    def test_as_nove_de_estuario_continuam_mudas(self):
        """O que sobe nelas é MARÉ: cruzar a cota é rotina de todo dia, e o
        aviso que toca com a maré ensina a ignorar o próximo."""
        estuario = [
            ("DC-01 Rio Itajaí-Açu - ICMBio/CEPSUL", "itajai-acu", 1.40),
            ("DC-07 Ribeirão da Murta - Portal", "ribeirao-murta", 1.70),
            ("DC-08 Ribeirão Canhanduba - Rua Benjamin Dagnoni",
             "ribeirao-canhanduba", 2.95),
        ]
        for titulo, rio, nivel in estuario:
            with self.subTest(titulo):
                saida = self.itajai([(titulo, rio, nivel)])
                self.assertNotIn("Acima da cota", saida)
                self.assertNotIn("Abaixo da primeira cota", saida)

    def test_as_onze_juntas_so_duas_falam(self):
        """Como sai de verdade: o aviso dos zeros diferentes continua, e só as
        duas provadas ganham faixa."""
        saida = self.itajai([
            ("DC-01 Rio Itajaí-Açu - ICMBio/CEPSUL", "itajai-acu", 0.88),
            (DC10, "itajai-mirim", 3.93),
            (DC11, "itajai-acu", 2.39),
        ])
        self.assertEqual(saida.count("Abaixo da primeira cota"), 2)
        self.assertIn("não se comparam entre si", saida)

    def test_nivel_implausivel_nao_vira_abaixo_da_primeira_cota(self):
        saida = self.itajai([(DC11, "itajai-acu", 0.0)])
        self.assertNotIn("Abaixo da primeira cota", saida)
        self.assertNotIn("Acima da cota", saida)

    def test_so_estas_duas_estacoes_tem_o_par_provado(self):
        """Trava de cadastro, igual à das cidades: marcar `cotas_verificado` numa
        estação sem provar o par derruba este teste — e é para derrubar.

        As quatro cujas cotas estão em disputa entre o Plano v17 e o portal novo
        (DC-01, DC-07, DC-08, DC-09) ficam de fora por este campo não existir
        nelas: ali o par cota↔leitura é justamente o que ninguém provou ainda.
        """
        provadas = {e.get("codigo") for e in estacoes_tempo_real()
                    if e.get("cotas_verificado") is True}
        self.assertEqual(provadas, {"DC-10", "DC-11"})

    def test_estuario_calada_mesmo_se_marcarem_como_verificada(self):
        """As duas condições são independentes de propósito: quem um dia marcar
        uma régua de estuário como verificada não abre a torneira sem querer."""
        e = dict(estacao_por_titulo("DC-01 Rio Itajaí-Açu - ICMBio/CEPSUL"),
                 cotas_verificado=True)
        self.assertIs(e["alerta_automatico"], False)
        with unittest.mock.patch("bot.estacao_por_titulo", return_value=e):
            self.assertIsNone(faixa_da_regua(
                {"estacao": "DC-01 Rio Itajaí-Açu - ICMBio/CEPSUL", "nivel_m": 1.40},
                AGORA))

    def test_a_faixa_da_cidade_continua_vencendo(self):
        """Nas cinco cidades que já passavam, a mensagem não muda uma vírgula:
        `faixa_da_regua` só entra onde a da cidade não pôde sair."""
        leituras = [{"estacao": "Blumenau", "rio": "itajai-acu", "cidade": "blumenau",
                     "nivel_m": 8.40, "medido_em": "2026-08-30T18:20:00"}]
        b = Base({"leituras": leituras}, le_json("estacoes.json"),
                 le_json("transito.json"), le_json("enchentes.json"))
        cidade = [c for c in b.cidades() if c["id"] == "blumenau"][0]
        saida = "".join(resposta_nivel(b, cidade, AGORA))
        self.assertIn("Alerta Máximo", saida)
        # E a estação de Blumenau NÃO tem o campo: a faixa veio da cidade.
        # `None`, não a sentinela de idade: a trava do `cotas_verificado` recusa
        # antes, e é essa a ordem — quem nunca teve faixa não a "perde por idade".
        self.assertIsNone(faixa_da_regua({"estacao": "Blumenau", "nivel_m": 8.40}, AGORA))

    def test_o_pino_de_itajai_carrega_a_faixa(self):
        """Fecha o caminho inteiro: pino -> camada da cidade -> faixa da régua.

        O pino sai do Centro de Itajaí, não de cima da DC-11: Santa Regina fica
        na divisa e `cidade_mais_proxima` responde ILHOTA de lá — o risco que o
        `resposta_localizacao` já registra. Ali a recusa é o comportamento certo,
        e a nota da própria DC-11 diz por quê: a leitura é de Itajaí e não pode
        ser lida como o nível de Ilhota.
        """
        u = {"fonte_itajai_ok": True, "leituras": [
            {"estacao": DC11, "rio": "itajai-acu", "cidade": "itajai",
             "nivel_m": 2.39, "medido_em": "2026-08-30T18:20:00"}]}
        b = Base(u, le_json("estacoes.json"), le_json("transito.json"),
                 le_json("enchentes.json"), le_json("cotas-ruas.json"))
        saida = "".join(resposta_localizacao(b, -26.9077, -48.6620, AGORA))
        self.assertIn("Abaixo da primeira cota", saida)
        self.assertIn("3,00 m", saida)


class TestDC10NaoEDeEstuario(unittest.TestCase):
    """A nota da DC-11 dizia "a única das onze réguas acima da maré". Não fecha:
    são nove com `alerta_automatico: false`, e nove mais uma dão dez, não onze.
    A DC-10 é a que faltava — e chamá-la de maré seria calar a régua mais a
    montante do Mirim em Itajaí bem quando ela é a que avisa.
    """

    def test_sao_nove_as_de_estuario(self):
        mudas = {e.get("codigo") for e in estacoes_tempo_real()
                 if e.get("alerta_automatico") is False}
        self.assertEqual(len(mudas), 9)
        self.assertNotIn("DC-10", mudas)
        self.assertNotIn("DC-11", mudas)

    def test_as_cotas_da_dc10_sao_escala_de_rio(self):
        """8/9/10 m. As de estuário ficam entre 1 e 3 m — a maré não sobe oito
        metros em Itajaí."""
        dc10 = estacao_por_titulo(DC10)
        self.assertGreaterEqual(min(dc10["cotas_m"].values()), 5.0)
        for e in estacoes_tempo_real():
            if e.get("alerta_automatico") is False and e.get("cotas_m"):
                self.assertLess(max(e["cotas_m"].values()), 5.0, e["codigo"])

    def test_a_nota_nao_diz_mais_unica(self):
        dc11 = estacao_por_titulo(DC11)
        self.assertNotIn("É a única das onze réguas de Itajaí que fica acima da maré",
                         dc11["nota_cidade"])
        self.assertIn("DUAS", dc11["nota_cidade"])


class TestReguaMaisProxima(unittest.TestCase):
    """A distância tem de ser até uma RÉGUA, e a régua tem de ter nome.

    ACHADO em 19/09/2026, num pino real em Itajaí. O bot respondia
    "Régua mais próxima: Itajaí, a 3,7 km" — e os 3,7 km eram até o PONTO
    MUNICIPAL de Itajaí. A régua mais perto daquele pino era a DC-06, a 813 m:
    quatro vezes e meia mais perto, e com nome. O número estava certo e o
    rótulo, errado.

    O PINO DO JEFFERSON NÃO ENTRA AQUI. A coordenada de quem pergunta é dado
    pessoal e o bot nem a registra; guardá-la em fixture seria inaugurar pelo
    teste o log que o código recusa. Os pontos abaixo são SINTÉTICOS, calculados
    a partir das coordenadas das próprias réguas, e reproduzem a mesma geometria:
    perto de uma DC e longe do ponto municipal.
    """

    def base_itajai(self, leituras=None) -> Base:
        leituras = leituras if leituras is not None else [
            {"estacao": t, "rio": r, "cidade": "itajai", "nivel_m": n,
             "medido_em": "2026-08-30T18:20:00"}
            for t, r, n in [
                ("DC-01 Rio Itajaí-Açu - ICMBio/CEPSUL", "itajai-acu", 0.88),
                (DC06, "itajai-mirim", 0.48),
                (DC11, "itajai-acu", 2.39),
            ]]
        return Base({"fonte_itajai_ok": True, "leituras": leituras},
                    le_json("estacoes.json"), le_json("transito.json"),
                    le_json("enchentes.json"), le_json("cotas-ruas.json"))

    def perto_da(self, titulo: str, metros_norte: float = 300.0) -> tuple[float, float]:
        """Um ponto sintético a ~N metros ao norte da régua."""
        e = estacao_por_titulo(titulo)
        return (e["lat"] + metros_norte / 111_320.0, e["lon"])

    def test_escolhe_a_regua_fisica_e_nao_o_ponto_municipal(self):
        b = self.base_itajai()
        ponto = self.perto_da(DC06)
        est, km = b.regua_mais_proxima(*ponto)
        self.assertEqual(est["codigo"], "DC-06")
        self.assertLess(km, 0.4)
        # E o ponto municipal de Itajaí está MUITO mais longe: é a distância
        # que o bot anunciava como sendo da régua.
        _, km_cidade = b.cidade_mais_proxima(*ponto)
        self.assertGreater(km_cidade, 2.0)

    def test_o_cabecalho_nomeia_a_regua_e_da_a_distancia_dela(self):
        saida = "".join(resposta_localizacao(self.base_itajai(),
                                             *self.perto_da(DC06), AGORA))
        self.assertIn("Régua mais próxima", saida)
        self.assertIn("Itamirim Clube de Campo", saida)
        self.assertIn("300 m", saida)
        self.assertNotIn("3,7 km", saida)

    def test_o_destaque_carrega_o_numero_DELA(self):
        """A distância sai NA LINHA da régua escolhida, ao lado do número dela.
        Se saísse à parte, casar 0,48 m com DC-06 ficaria por conta de quem lê —
        e numa lista de onze, com 0,88 m em cima, casar errado é fácil."""
        saida = "".join(resposta_localizacao(self.base_itajai(),
                                             *self.perto_da(DC06), AGORA))
        linha = [x for x in saida.split("\n") if "Itamirim" in x and "0,48" in x]
        self.assertTrue(linha, saida)
        self.assertIn("daqui", linha[0])
        self.assertNotIn("0,88", linha[0])

    def test_a_ordem_do_cadastro_nao_muda_a_resposta(self):
        """Embaralhar leituras não pode trocar a régua escolhida."""
        leituras = [
            {"estacao": t, "rio": r, "cidade": "itajai", "nivel_m": n,
             "medido_em": "2026-08-30T18:20:00"}
            for t, r, n in [(DC11, "itajai-acu", 2.39), (DC06, "itajai-mirim", 0.48),
                            ("DC-01 Rio Itajaí-Açu - ICMBio/CEPSUL", "itajai-acu", 0.88)]]
        for ordem in (leituras, list(reversed(leituras))):
            with self.subTest(primeira=ordem[0]["estacao"][:6]):
                b = self.base_itajai(ordem)
                self.assertEqual(b.regua_mais_proxima(*self.perto_da(DC06))[0]["codigo"],
                                 "DC-06")

    def test_empate_sai_pelo_codigo_nao_pela_ordem_do_json(self):
        """Duas réguas exatamente à mesma distância: a resposta tem de ser
        estável. Reordenar o JSON não pode trocar o que o morador recebe."""
        b = self.base_itajai()
        gemeas = [
            {"codigo": "DC-99", "titulo": "Z", "rio": "itajai-acu", "cidade": "itajai",
             "lat": -26.9, "lon": -48.7},
            {"codigo": "DC-98", "titulo": "A", "rio": "itajai-acu", "cidade": "itajai",
             "lat": -26.9, "lon": -48.7},
        ]
        for ordem in (gemeas, list(reversed(gemeas))):
            with self.subTest(primeira=ordem[0]["codigo"]):
                b.estacoes = dict(b.estacoes, estacoes_tempo_real=ordem)
                self.assertEqual(b.regua_mais_proxima(-26.9, -48.7)[0]["codigo"], "DC-98")

    def test_pluviometro_nao_concorre_como_regua(self):
        """A DC-00 é a própria Defesa Civil, pluviômetro puro (`rio` nulo).
        Anunciá-la como régua mandaria a pessoa olhar um aparelho que não mede
        rio. Hoje ela nem tem coordenada; a guarda é para quando tiver."""
        b = self.base_itajai()
        dc00 = [dict(e, lat=-26.9, lon=-48.7) for e in estacoes_tempo_real()
                if e.get("codigo") == "DC-00"]
        self.assertTrue(dc00)
        self.assertIsNone(dc00[0].get("rio"))
        b.estacoes = dict(b.estacoes, estacoes_tempo_real=dc00)
        self.assertIsNone(b.regua_mais_proxima(-26.9, -48.7))

    def test_coordenada_invalida_nao_vira_zero(self):
        """`(0, 0)` fica no golfo da Guiné e ganharia de qualquer régua real se
        entrasse como número; `None` não pode estourar."""
        b = self.base_itajai()
        b.estacoes = dict(b.estacoes, estacoes_tempo_real=[
            {"codigo": "DC-97", "titulo": "sem coordenada", "rio": "itajai-acu",
             "cidade": "itajai", "lat": None, "lon": None},
            {"codigo": "DC-96", "titulo": "fora do planeta", "rio": "itajai-acu",
             "cidade": "itajai", "lat": 999.0, "lon": 999.0},
        ])
        self.assertIsNone(b.regua_mais_proxima(-26.9, -48.7))

    def test_regua_muda_continua_sendo_a_mais_proxima(self):
        """Proximidade é geografia. Pular a régua calada para anunciar a segunda
        responderia sobre outro lugar; quem diz que falta leitura é o bloco de
        nível, que já sabe fazer isso."""
        b = self.base_itajai(leituras=[])
        saida = "".join(resposta_localizacao(b, *self.perto_da(DC06), AGORA))
        self.assertIn("Itamirim Clube de Campo", saida)
        self.assertIn("Sem leitura ao vivo", saida)

    def test_regua_dentro_do_limite_salva_o_ponto_municipal_fora(self):
        """A recusa "nenhuma das réguas está a menos de 40 km" era medida contra
        pontos MUNICIPAIS. Quem estivesse perto de uma régua e longe do centro
        da cidade dela ouvia que está fora da bacia."""
        b = self.base_itajai()
        ponto = self.perto_da(DC10)  # Limoeiro, a 20 km do ponto municipal
        _, km_cidade = b.cidade_mais_proxima(*ponto)
        _, km_regua = b.regua_mais_proxima(*ponto)
        self.assertLess(km_regua, 1.0)
        self.assertGreater(km_cidade, km_regua)
        self.assertNotIn("fora da área", "".join(resposta_localizacao(b, *ponto, AGORA)))

    def test_fora_da_bacia_continua_recusando(self):
        """Floripa não passa a entrar porque a conta mudou."""
        saida = "".join(resposta_localizacao(self.base_itajai(), -27.5954, -48.5480, AGORA))
        self.assertIn("fora da área", saida)
        self.assertIn("A mais próxima fica a", saida)

    def test_cota_de_rua_nao_muda_por_causa_da_proximidade(self):
        """Régua perto não autoriza subtrair o nível dela da cota de uma rua:
        Itajaí tem onze zeros diferentes, e a recusa continua."""
        b = self.base_itajai()
        saida = "".join(resposta_localizacao(b, *self.perto_da(DC06), AGORA))
        self.assertNotIn("faltam", saida.lower())
        self.assertIn("não se comparam entre si", saida)


class TestDistanciaEmMetros(unittest.TestCase):
    """Abaixo de 1 km o morador pensa em metros — e a camada de rua, na mesma
    mensagem, já falava em metros enquanto a régua falava em km."""

    def test_abaixo_de_um_km_sai_em_metros(self):
        self.assertEqual(quilometros(0.813), "810 m")
        self.assertEqual(quilometros(0.08), "80 m")

    def test_em_cima_da_regua_nao_diz_zero_nem_finge_precisao(self):
        """"a 0,0 km" lê-se como quebrado (visto em campo em Brusque); "a 10 m"
        prometeria uma precisão que o GPS do celular não tem."""
        self.assertEqual(quilometros(0.0), "menos de 50 m")
        self.assertEqual(quilometros(0.004), "menos de 50 m")

    def test_acima_de_um_km_continua_em_km_com_virgula(self):
        self.assertEqual(quilometros(1.64), "1,6 km")
        self.assertEqual(quilometros(60.1), "60,1 km")

    def test_a_fronteira_nao_produz_mil_metros(self):
        self.assertEqual(quilometros(0.999), "1,0 km")
        self.assertEqual(quilometros(0.994), "990 m")


class TestCheiasAntigas(unittest.TestCase):
    """"E isso é muito?" — a pergunta que vem depois de "quanto está o rio".

    Pedido em 19/09/2026. Um número sozinho só informa quem já tem a escala na
    cabeça; ao lado de "23/09/1880 chegou a 12,56 m aqui", ele ganha tamanho.
    """

    def pino(self, cidade_id: str, estacao: str, rio: str, nivel: float,
             lat: float, lon: float) -> str:
        u = {"fonte_itajai_ok": True, "leituras": [
            {"estacao": estacao, "rio": rio, "cidade": cidade_id, "nivel_m": nivel,
             "medido_em": "2026-08-30T18:20:00"}]}
        b = Base(u, le_json("estacoes.json"), le_json("transito.json"),
                 le_json("enchentes.json"), le_json("cotas-ruas.json"))
        return "".join(resposta_localizacao(b, lat, lon, AGORA))

    def gaspar(self, nivel: float) -> str:
        return self.pino("gaspar", "Gaspar — Ponte Municipal", "itajai-acu",
                         nivel, -26.9316, -48.9586)

    def test_mostra_a_de_cima_e_a_de_baixo_com_data(self):
        """Com o rio a 8,00 m em Gaspar, o que situa é 1957 logo abaixo e 2001
        logo acima — não a lista das 48."""
        t = self.gaspar(8.00)
        self.assertIn("Cheias já registradas nesta régua", t)
        self.assertIn("01/10/2001", t)
        self.assertIn("02/08/1957", t)
        self.assertIn("acima do nível de agora", t)
        self.assertIn("abaixo do nível de agora", t)

    def test_a_maior_de_todas_entra_sempre(self):
        """É a régua mental da cidade: 12,56 m em 1880 diz mais que adjetivo."""
        for nivel in (1.0, 8.0):
            with self.subTest(nivel=nivel):
                self.assertIn("12,56 m", self.gaspar(nivel))

    def test_nao_vira_parede_de_numeros(self):
        """48 registros, no máximo cinco linhas de cheia."""
        linhas = [x for x in self.gaspar(8.00).split("\n")
                  if "do nível de agora" in x]
        self.assertLessEqual(len(linhas), 2 * 2 + 1)

    def test_itajai_diz_que_nao_tem_registro(self):
        """Zero registros de Itajaí em `enchentes.json`. Sumir em silêncio daria
        a mesma tela de uma cidade cuja referência não foi conferida, e são
        coisas diferentes."""
        t = self.pino("itajai", DC06, "itajai-mirim", 0.48, -26.9217, -48.6858)
        self.assertIn("não temos cheia registrada de Itajaí", t)
        self.assertNotIn("Cheias já registradas", t)

    def test_a_falta_do_registro_vem_antes_do_motivo_das_onze_reguas(self):
        """VISTO EM CAMPO no pino de Itajaí (19/09/2026). A cidade cai nos dois
        motivos ao mesmo tempo, e o das réguas saía na frente:

            "Itajaí tem 11 réguas com zeros diferentes, e nenhuma delas sozinha
             é o nível da cidade"

        Verdade, e dá a entender uma coisa falsa: que temos cheias de Itajaí e
        não sabemos a qual régua pertencem. Não temos NENHUMA. O motivo das
        várias réguas é sobre ATRIBUIR o que existe; sem registro não há o que
        atribuir, e a frase manda quem lê procurar um problema que não é o dele.
        """
        u = {"fonte_itajai_ok": True, "leituras": [
            {"estacao": t, "rio": "itajai-mirim", "cidade": "itajai", "nivel_m": n,
             "medido_em": "2026-08-30T18:20:00"}
            for t, n in [(DC06, 0.40), (DC10, 4.06)]]}
        b = Base(u, le_json("estacoes.json"), le_json("transito.json"),
                 le_json("enchentes.json"))
        cidade = [c for c in b.cidades() if c["id"] == "itajai"][0]
        t = "".join(linhas_das_cheias(b, cidade, AGORA))
        self.assertIn("não temos cheia registrada de Itajaí", t)
        self.assertNotIn("réguas com zeros diferentes", t)

    def test_com_registro_o_motivo_das_varias_reguas_volta_a_valer(self):
        """A ordem não engole o outro motivo: onde HÁ cheia registrada e a
        cidade tem várias réguas, o que falta é atribuir — e é isso que sai.

        SUBSTITUI o teste que afirmava a mesma regra usando Itajaí como exemplo.
        Itajaí deixou de servir de exemplo justamente por ser o caso que o
        conserto separou: lá os dois motivos valem, e o que sai agora é o
        primeiro deles.
        """
        u = {"fonte_itajai_ok": True, "leituras": [
            {"estacao": t, "rio": "itajai-mirim", "cidade": "itajai", "nivel_m": n,
             "medido_em": "2026-08-30T18:20:00"}
            for t, n in [(DC06, 0.40), (DC10, 4.06)]]}
        b = Base(u, le_json("estacoes.json"), le_json("transito.json"),
                 {"eventos": [{"cidade": "itajai", "pico_m": 3.0, "data": "2008-11-23",
                               "referencia": "régua", "confianca": "alta"}]})
        cidade = [c for c in b.cidades() if c["id"] == "itajai"][0]
        t = "".join(linhas_das_cheias(b, cidade, AGORA))
        self.assertIn("réguas com zeros diferentes", t)
        self.assertNotIn("não temos cheia registrada", t)

    def test_brusque_cala_pela_referencia_e_diz_por_que(self):
        """REGRA BLOQUEANTE do CLAUDE.md, item 4. As 23 de Brusque estão sem
        referência conferida: ao lado do nível ao vivo dariam diferença de régua
        com cara de diferença de rio."""
        t = self.pino("brusque", "Brusque", "itajai-mirim", 1.94, -27.098, -48.917)
        self.assertIn("sem referência conferida", t)
        self.assertNotIn("Cheias já registradas", t)

    def test_blumenau_mostra_as_de_regua_e_conta_as_que_calou(self):
        """117 registros, 4 em régua e 113 em IBGE ou sem referência. Mostrar
        quatro e calar as outras daria a tela de uma cidade com quatro cheias na
        história — e ela tem a série mais longa da bacia."""
        t = self.pino("blumenau", "Blumenau", "itajai-acu", 7.60, -26.9194, -49.0661)
        self.assertIn("05/05/2022", t)
        self.assertIn("Outras 113 cheias", t)
        self.assertIn("outra referência de régua", t)

    def test_nenhum_pico_do_ibge_entra(self):
        """A trava, medida: nenhum valor devolvido pode vir de registro em IBGE."""
        b = Base({"leituras": []}, le_json("estacoes.json"), le_json("transito.json"),
                 le_json("enchentes.json"))
        for cidade in ("blumenau", "gaspar", "indaial", "brusque", "rio-do-sul"):
            with self.subTest(cidade):
                cheias, _, _ = cheias_perto_do_nivel(b, cidade, 5.0)
                for r in cheias:
                    self.assertEqual(r.get("referencia"), "régua", r.get("data"))

    def test_compilacao_informal_nao_chega_com_cara_de_oficial(self):
        b = Base({"leituras": []}, le_json("estacoes.json"), le_json("transito.json"),
                 {"eventos": [
                     {"cidade": "gaspar", "pico_m": 9.0, "data": "1984-08",
                      "referencia": "régua", "confianca": "baixa"},
                 ]})
        cidade = [c for c in b.cidades() if c["id"] == "gaspar"][0]
        b.ultimo = {"leituras": [{"estacao": "Gaspar — Ponte Municipal",
                                  "rio": "itajai-acu", "cidade": "gaspar",
                                  "nivel_m": 2.0, "medido_em": "2026-08-30T18:20:00"}]}
        t = "".join(linhas_das_cheias(b, cidade, AGORA))
        self.assertIn("08/1984", t)
        self.assertIn("compilação informal", t)


class TestDataDaCheia(unittest.TestCase):
    """O dado guarda o que a fonte sabia. Completar com 01/01 daria precisão que
    a fonte não tem — e numa cheia de 1852 isso seria ficção."""

    def test_dia_mes_ano(self):
        self.assertEqual(data_da_cheia("2008-11-23"), "23/11/2008")

    def test_so_mes_e_ano(self):
        self.assertEqual(data_da_cheia("1984-08"), "08/1984")

    def test_so_ano(self):
        self.assertEqual(data_da_cheia("1852"), "1852")

    def test_vazio_ou_ausente(self):
        for v in (None, "", "   ", 2008):
            with self.subTest(v=v):
                self.assertIsNone(data_da_cheia(v))


class TestContagemDasReferencias(unittest.TestCase):
    """Os números que o bloco de cheias afirma no docstring, medidos no arquivo.

    CORRIGIDO em 19/09/2026 por auditoria externa: eu tinha escrito "98 sem
    referência em Brusque e Rio do Sul". Errado duas vezes — o número é 75, e o
    meu nem fechava a conta (72 + 98 = 170, não 147). E a maioria dos sem
    referência é de BLUMENAU, a mesma cidade dos 72 do IBGE.

    Número escrito em comentário envelhece calado; medido em teste, não.
    """

    def setUp(self):
        self.ev = le_json("enchentes.json")["eventos"]

    def test_a_conta_fecha(self):
        from collections import Counter
        refs = Counter(str(r.get("referencia")) for r in self.ev)
        # 19/09/2026, noite: entraram os quatro de Rio do Sul (1983 ×3 e
        # set/2013) da tabela municipal — 215 → 219, 75 → 79 sem referência.
        # 21/09/2026: entraram os 52 da tabela inteira (decisão do Jefferson,
        # opção a) — 219 → 271, 79 → 131 sem referência. A tabela não nomeia a
        # régua, então os 52 entram com `referencia: null`, como os 13.
        # 22/09/2026: entraram as cinco cheias de Brusque da régua da ANA
        # (83900000, HidroWeb; decisão do Jefferson) — 271 → 276, 131 → 136
        # sem referência: zero da ANA, que coincide com o municipal em
        # 2019–2021 e não se sabe desde quando.
        # 24/09/2026: entraram 14 picos de Taió (tabela do Estudo
        # Socioambiental), Timbó, Rio dos Cedros, Trombudo Central e Botuverá,
        # todos sem régua declarada na fonte — 276 → 290, 136 → 150.
        self.assertEqual(len(self.ev), 290)
        self.assertEqual(refs["régua"], 68)
        self.assertEqual(refs["IBGE (régua + 0,20 m)"], 72)
        self.assertEqual(refs["None"], 150)
        self.assertEqual(refs["IBGE (régua + 0,20 m)"] + refs["None"], 222)

    def test_de_onde_vem_os_sem_referencia(self):
        """Era o segundo erro: eu atribuía os sem referência a Brusque e Rio do
        Sul. Até 21/09/2026 a maioria era de BLUMENAU (41, com 113 calados de
        117 por duas causas ao mesmo tempo). Com os 52 da tabela municipal, Rio
        do Sul passou a ser a maior fatia (65) — e por UMA causa só: a tabela
        não nomeia a régua. Blumenau não mudou."""
        from collections import Counter
        sem = Counter(r["cidade"] for r in self.ev if r.get("referencia") is None)
        self.assertEqual(sem["blumenau"], 41)
        self.assertEqual(sem["brusque"], 28)  # 23 + 5 da régua da ANA (22/09/2026)
        self.assertEqual(sem["rio-do-sul"], 65)
        blu = [r for r in self.ev if r["cidade"] == "blumenau"]
        self.assertEqual(len(blu), 117)
        self.assertEqual(sum(1 for r in blu if r.get("referencia") != "régua"), 113)


class TestLeituraVelhaNaoFalaNoPresente(unittest.TestCase):
    """O pino de Indaial de 19/09/2026, e o que ele mostrou.

    A leitura tinha **6,9 dias** e o pino afirmava, no presente, duas coisas:

        🟠 Acima da cota de Alerta (4,00 m)
        8,70 m — 23/09/1880 (4,60 m acima do nível de agora)

    As duas dizem onde o rio está AGORA a partir de um número de quase uma
    semana. Se ele subiu desde a medição, a segunda promete 4,60 m de folga que
    ninguém mediu — e prometer folga inexistente é o erro que este projeto
    existe para não cometer.

    O bot já sabia a regra: a /previsao recusa a conta com leitura velha, e
    escreve que "o 'agora' é falso". O site também: `compararCheias.ts` descarta
    leitura `velha` e `reguasNoMapa.ts` tira a cor. Faltava aqui.
    """

    INDAIAL = "Indaial — fundos da Celesc (Defesa Civil)"

    def base_indaial(self, minutos_atras: float):
        medido = (AGORA - timedelta(minutes=minutos_atras)).astimezone(
            bot.FUSO).replace(tzinfo=None).isoformat(timespec="seconds")
        leituras = [{"estacao": self.INDAIAL, "rio": "itajai-acu", "cidade": "indaial",
                     "nivel_m": 4.10, "medido_em": medido}]
        b = Base({"leituras": leituras}, le_json("estacoes.json"),
                 le_json("transito.json"), le_json("enchentes.json"))
        cidade = [c for c in b.cidades() if c["id"] == "indaial"][0]
        return b, cidade

    def pino(self, minutos_atras: float) -> str:
        b, cidade = self.base_indaial(minutos_atras)
        return "".join(resposta_nivel(b, cidade, AGORA)
                       + linhas_das_cheias(b, cidade, AGORA))

    def test_com_leitura_fresca_nada_muda(self):
        """A trava não pode custar a resposta boa: com leitura de 30 min, o pino
        segue dizendo a faixa e comparando com as cheias."""
        saida = self.pino(30)
        self.assertIn("Acima da cota de <b>Alerta</b>", saida)
        self.assertIn("acima do nível de agora", saida)
        self.assertIn("8,70 m", saida)

    def test_com_leitura_de_69_dias_a_faixa_sai_e_o_motivo_entra(self):
        saida = self.pino(6.9 * 24 * 60)
        self.assertNotIn("Acima da cota de", saida)
        self.assertIn("velha demais para dizer em que cota o rio está", saida)
        # A idade continua na tela, que é de onde a pessoa julga o número.
        self.assertIn("há 6,9 dias", saida)

    def test_com_leitura_de_69_dias_as_cheias_nao_viram_comparacao(self):
        saida = self.pino(6.9 * 24 * 60)
        self.assertNotIn("acima do nível de agora", saida)
        self.assertNotIn("Cheias já registradas nesta régua", saida)
        self.assertIn("velha demais para dizer onde o rio está agora", saida)

    def test_o_limiar_e_o_mesmo_do_site_e_o_mesmo_da_previsao(self):
        """Um número só. O bot já o aplicava na /previsao e não aqui."""
        self.assertEqual(bot.IDADE_VELHA_MIN, 180)
        self.assertEqual(bot.IDADE_MAXIMA_PREVISAO_MIN, bot.IDADE_VELHA_MIN)
        site = (RAIZ / "web" / "src" / "logica" / "tempoReal.ts").read_text(encoding="utf-8")
        self.assertIn("export const MIN_VELHA = 180", site)

    def test_blumenau_tem_limite_proprio_de_120_minutos(self):
        """A cadência da fonte é que manda. O AlertaBlu publica de hora em hora,
        então 2 h já é a segunda leitura que não chegou; numa fonte de 15 em 15
        min as mesmas 2 h são oito perdidas e as 3 h ainda fazem sentido. O site
        já separava os dois; o bot ficava 1 h mais permissivo justamente na
        cidade de série mais longa da bacia."""
        self.assertEqual(bot.IDADE_VELHA_BLUMENAU_MIN, 120)
        self.assertEqual(bot.limite_de_idade("blumenau"), 120)
        self.assertEqual(bot.limite_de_idade("gaspar"), bot.IDADE_VELHA_MIN)
        self.assertEqual(bot.limite_de_idade(None), bot.IDADE_VELHA_MIN)

    def test_o_mesmo_numero_de_minutos_decide_diferente_nas_duas_cidades(self):
        """150 min: velha em Blumenau, fresca em Indaial. É o ponto da mudança."""
        for cidade, velha_aos_150 in (("blumenau", True), ("indaial", False)):
            leitura = {"cidade": cidade, "nivel_m": 3.06,
                       "medido_em": (AGORA - timedelta(minutes=150)).astimezone(
                           bot.FUSO).replace(tzinfo=None).isoformat(timespec="seconds")}
            self.assertEqual(bot.leitura_velha(leitura, AGORA), velha_aos_150, cidade)

    def test_a_virada_de_blumenau_e_nos_120(self):
        def pino(minutos: float) -> str:
            medido = (AGORA - timedelta(minutes=minutos)).astimezone(
                bot.FUSO).replace(tzinfo=None).isoformat(timespec="seconds")
            leituras = [{"estacao": "Blumenau", "rio": "itajai-acu",
                         "cidade": "blumenau", "nivel_m": 8.40, "medido_em": medido}]
            b = Base({"leituras": leituras}, le_json("estacoes.json"),
                     le_json("transito.json"), le_json("enchentes.json"))
            cidade = [c for c in b.cidades() if c["id"] == "blumenau"][0]
            return "".join(resposta_nivel(b, cidade, AGORA)
                           + linhas_das_cheias(b, cidade, AGORA))

        self.assertIn("Alerta Máximo", pino(120))
        self.assertNotIn("Alerta Máximo", pino(121))
        # E aos 150 min, que antes desta mudança ainda pintaria:
        self.assertIn("velha demais para dizer em que cota o rio está", pino(150))
        self.assertIn("velha demais para dizer onde o rio está agora", pino(150))

    def test_a_virada_e_nos_180_minutos(self):
        self.assertIn("Acima da cota de <b>Alerta</b>", self.pino(180))
        self.assertNotIn("Acima da cota de", self.pino(181))

    def test_sem_carimbo_de_hora_tambem_e_velha(self):
        """"Não sei quando isto foi medido" não pode virar "é o nível de agora"."""
        self.assertTrue(bot.leitura_velha({"nivel_m": 4.10}, AGORA))
        self.assertTrue(bot.leitura_velha({"nivel_m": 4.10, "medido_em": "coisa"}, AGORA))
        self.assertFalse(bot.leitura_velha(
            {"nivel_m": 4.10, "medido_em": "2026-08-30T18:20:00"}, AGORA))

    def test_quem_nunca_teve_faixa_nao_a_perde_por_idade(self):
        """A ordem das travas, e é o ponto mais fácil de errar. Rio do Sul não
        tem `cotas_verificado` — cota da Ponte Dom Tito Buss, leitura da Estação
        MKS. Com leitura velha ela devolve `None`, como sempre devolveu, e NÃO a
        sentinela: anunciar que perdeu a faixa por idade mandaria quem lê
        procurar um problema que não é o dela."""
        velha = {"estacao": "Rio do Sul Estação MKS", "rio": "itajai-acu",
                 "cidade": "rio-do-sul", "nivel_m": 3.52,
                 "medido_em": "2026-08-20T18:20:00"}
        b = Base({"leituras": [velha]}, le_json("estacoes.json"),
                 le_json("transito.json"), le_json("enchentes.json"))
        cidade = [c for c in b.cidades() if c["id"] == "rio-do-sul"][0]
        self.assertIsNone(faixa_da_leitura(cidade, [velha], AGORA))
        self.assertNotIn("velha demais para dizer em que cota",
                         "".join(resposta_nivel(b, cidade, AGORA)))

    def test_a_rua_cala_pelo_mesmo_motivo_e_com_a_mesma_frase(self):
        """Os dois blocos saem de `porque_sem_comparacao` justamente para não
        voltarem a divergir."""
        b, cidade = self.base_indaial(6.9 * 24 * 60)
        motivo = bot.porque_sem_comparacao(b, "indaial", AGORA)
        self.assertIsNotNone(motivo)
        self.assertIn("velha demais para dizer onde o rio está agora", motivo)
        self.assertIn("há 6,9 dias", motivo)


class TestDivergenciaDeBrusque(unittest.TestCase):
    """O portal municipal de Brusque serve DUAS estações com o mesmo nome de
    ponte e cotas diferentes — DCSC 3/5 e ANA 4/7. Relatado por auditoria
    externa em 19/09/2026.

    Aplicar o limite da ANA à leitura da DCSC faria o aviso sair 1 m TARDE
    DEMAIS, num rio de resposta rápida. A trava é o registro das duas.
    """

    def cidade(self) -> dict:
        return [c for c in base().cidades() if c["id"] == "brusque"][0]

    def test_a_cidade_segue_com_as_cotas_da_dcsc(self):
        c = self.cidade()
        self.assertEqual(c["cotas_m"], {"atencao": 3.0, "emergencia": 5.0})
        self.assertEqual(c["regua"], "Ponte Estaiada – DCSC")
        self.assertEqual(c["regua_das_cotas"], "Ponte Estaiada – DCSC")

    def test_o_par_da_ana_esta_registrado_e_nao_adotado(self):
        div = self.cidade()["cotas_divergencia"]
        self.assertEqual(div["adotada"]["atencao"], 3.0)
        self.assertEqual(div["nao_adotada"]["atencao"], 4.0)
        self.assertEqual(div["nao_adotada"]["emergencia"], 7.0)
        self.assertIn("NÃO aplicar", div["nao_adotada"]["_regra"])
        self.assertIn("não conferido por mim", div["_estado"].lower())

    def test_a_terceira_escala_esta_registrada_e_nao_adotada(self):
        """19/09/2026, noite: o portal de ITAJAÍ, com Brusque selecionada,
        publica 3,5/5/6 para a MESMA DCSC-00019. Adotar atrasaria o aviso em
        50 cm num rio de resposta rápida."""
        c = self.cidade()
        terceira = c["cotas_divergencia"]["nao_adotada_portal_itajai"]
        self.assertEqual(terceira["atencao"], 3.5)
        self.assertEqual(terceira["alerta"], 5.0)
        self.assertEqual(terceira["emergencia"], 6.0)
        self.assertIn("NÃO adotar", terceira["_regra"])
        # A cidade não se mexeu: segue com a escala mais baixa das três.
        self.assertEqual(c["cotas_m"], {"atencao": 3.0, "emergencia": 5.0})

    def test_o_boletim_de_2023_segue_discriminando_contra_as_TRES(self):
        """Com uma terceira escala na mesa, a pergunta é se a evidência ainda
        aponta para alguma. Aponta: 3,18 m chamado de 'atenção' é incompatível
        com 3,50 e com 4,00, e só a escala do cadastro (3,00) o explica."""
        div = self.cidade()["cotas_divergencia"]
        nivel = div["evidencia_reunida"]["boletim_2023_10_30"]["nivel_m"]
        self.assertGreater(nivel, div["adotada"]["atencao"])
        for outra in (div["nao_adotada"], div["nao_adotada_portal_itajai"]):
            self.assertLess(nivel, outra["atencao"])

    def test_o_alerta_de_5_m_colide_com_a_emergencia_do_cadastro(self):
        """O detalhe que faz desta divergência mais que um número: 5,00 m é
        ALERTA na escala do portal de Itajaí e EMERGÊNCIA na do cadastro. O
        mesmo número com dois nomes é pior que dois números diferentes."""
        c = self.cidade()
        self.assertEqual(c["cotas_divergencia"]["nao_adotada_portal_itajai"]["alerta"],
                         c["cotas_m"]["emergencia"])
        # E o cadastro afirma que faixa de alerta não existe nesta fonte.
        self.assertNotIn("alerta", c["cotas_m"])
        self.assertIn("Não há faixa de alerta", c["fonte_cotas"])

    def test_a_evidencia_que_discrimina_esta_registrada_e_nao_fecha(self):
        """30/10/2023: 3,18 m chamado de 'atenção'. Entre as duas atenções (3,00
        DCSC · 4,00 ANA), só a DCSC daria esse nome. É evidência a favor do
        cadastro — e o cadastro continua ABERTO, porque um boletim de 2023 não
        prova a regra de 2026 nem nomeia a régua física."""
        div = self.cidade()["cotas_divergencia"]
        b = div["evidencia_reunida"]["boletim_2023_10_30"]
        self.assertEqual(b["nivel_m"], 3.18)
        self.assertEqual(b["estado_declarado"], "atenção")
        self.assertGreater(b["nivel_m"], div["adotada"]["atencao"])
        self.assertLess(b["nivel_m"], div["nao_adotada"]["atencao"])
        self.assertIn("ABERTO", div["_estado"])


class FonteDeRioDoSul:
    """A fonte dos picos de Rio do Sul, identificada em 19/09/2026."""

    FONTE = ("Defesa Civil de Rio do Sul — Histórico de Cheias "
             "(defesacivil.riodosul.sc.gov.br), tabela 'Exportação de Dados'")
    ROTULO_ANTIGO = "Portal GCD — série histórica de Rio do Sul"

    @staticmethod
    def registros() -> list[dict]:
        ev = le_json("enchentes.json")["eventos"]
        return [r for r in ev if r.get("cidade") == "rio-do-sul"]


class TestFonteDeRioDoSul(unittest.TestCase):
    """Os nove registros de Rio do Sul diziam 'Portal GCD' desde 30/08/2026 —
    um rótulo sem URL, sem sigla expandida, que ninguém conseguia reabrir. Em
    19/09/2026 o Jefferson abriu o Histórico de Cheias da Defesa Civil de Rio
    do Sul e conferiu: 9 de 9 níveis iguais, 3 datas diferentes. A fonte é
    essa tabela; o rótulo antigo fica gravado, não apagado.
    """

    def test_nenhum_registro_diz_mais_portal_gcd(self):
        ev = le_json("enchentes.json")["eventos"]
        self.assertEqual([r for r in ev if "GCD" in str(r.get("fonte"))], [])

    def test_os_sessenta_e_cinco_apontam_para_a_tabela_municipal(self):
        # 13 até 21/09/2026; 65 depois da importação dos 52 (opção a). Os 12
        # restantes da tabela ficam na conversão bruta, pendentes de dia.
        rs = FonteDeRioDoSul.registros()
        self.assertEqual(len(rs), 65)
        # 22/09/2026: mai/2018 desceu para `baixa` por decisão do Jefferson — as
        # quatro estações do INMET não sustentam 114,6 mm em 4 dias naquele mês,
        # e o candidato é set/2018. É a ÚNICA exceção; a nota do registro diz
        # "MÊS DUVIDOSO" e a decisão. Ver docs/CHAT-LOCAL.md, L5.
        excecoes = {"2018-05": "baixa"}
        for r in rs:
            self.assertEqual(r["fonte"], FonteDeRioDoSul.FONTE)
            self.assertEqual(r["confianca"], excecoes.get(r["data"], "media"), r["data"])
            if r["data"] in excecoes:
                self.assertIn("MÊS DUVIDOSO", r["nota"])
            # A tabela não nomeia a régua: `null` explícito, não campo ausente
            # (ausente a tela lê como "régua local", que ninguém provou).
            self.assertIn("referencia", r)
            self.assertIsNone(r["referencia"])

    def test_os_nove_antigos_guardam_o_rotulo_que_tinham(self):
        antigos = [r for r in FonteDeRioDoSul.registros() if "fonte_rotulo_anterior" in r]
        self.assertEqual(len(antigos), 9)
        for r in antigos:
            self.assertEqual(r["fonte_rotulo_anterior"], FonteDeRioDoSul.ROTULO_ANTIGO)

    def test_1911_e_outubro_como_na_tabela_e_em_blumenau(self):
        """'Maio' era erro da transcrição à mão de 30/08/2026 — o único dos
        oito anos compartilhados com Blumenau que desalinhava o mês."""
        rs = {r["data"]: r for r in FonteDeRioDoSul.registros()}
        self.assertNotIn("1911-05", rs)
        self.assertEqual(rs["1911-10"]["pico_m"], 12.2)
        self.assertIn("outubro", rs["1911-10"]["nota"].lower())

    def test_out_2023_e_dia_13_tabela_e_dcsc_concordam(self):
        """O 'dia 07' não tinha fonte, e a própria nota dizia que 9,5 m no dia
        7 era leitura de subida. Tabela municipal e crista da DCSC-00013
        (04:30 de 13/10) apontam o 13."""
        rs = {r["data"]: r for r in FonteDeRioDoSul.registros()}
        self.assertNotIn("2023-10-07", rs)
        self.assertEqual(rs["2023-10-13"]["pico_m"], 11.86)

    def test_nov_2023_fica_no_dia_18_com_a_data_da_tabela_guardada(self):
        """Aqui a tabela diz 17/11 e o registro fica em 18/11 — NÃO por teimosia:
        a crista foi na virada da noite (DCSC 13,18 m às 00:20 de 18/11; ANA
        13,06 m subindo às 22:00 de 17/11 e 13,09 m descendo às 02:00 de
        18/11). As duas datas descrevem a mesma cheia; a da fonte fica em
        `data_na_fonte`, e a divergência de valor com a ANA continua."""
        rs = {r["data"]: r for r in FonteDeRioDoSul.registros()}
        self.assertNotIn("2023-11-17", rs)
        r = rs["2023-11-18"]
        self.assertEqual(r["pico_m"], 13.04)
        self.assertEqual(r["data_na_fonte"], "2023-11-17")
        self.assertEqual([d["pico_m"] for d in r["divergencias"]], [13.14])

    def test_a_pendencia_de_1911_saiu_do_meta(self):
        pend = le_json("enchentes.json")["_meta"]["pendencias"]
        self.assertFalse(any("1911" in p for p in pend))


class TestDivergenciasDaTerceiraAuditoria(unittest.TestCase):
    """Pesquisa no Facebook das Defesas Civis (19/09/2026). O que ela achou fica
    REGISTRADO como divergência ou nota; nenhum valor do cadastro muda.

    Os testes travam justamente isso: que a escala não adotada continue não
    adotada, e que a corroborada continue igual.
    """

    def cidade(self, cid: str) -> dict:
        return [c for c in base().cidades() if c["id"] == cid][0]

    def test_taio_segue_com_as_quatro_cotas_do_plancon(self):
        """O Facebook de 13/10/2022 publica 5/7/8/9 — as mesmas do PLANCON de
        2026. Corroboração, não mudança."""
        c = self.cidade("taio")
        self.assertEqual(c["cotas_m"], {"monitoramento": 5.0, "atencao": 7.0,
                                        "alerta": 8.0, "emergencia": 9.0})
        self.assertIn("nova passarela", c["regua_nota"])
        # O campo continua vazio de propósito: "régua do Centro" (PLANCON) e
        # "nova passarela" (post) só se juntam por nome, e nome não é prova.
        self.assertFalse(str(c.get("regua_das_cotas") or "").strip())

    def test_timbo_nao_adota_a_escala_do_facebook(self):
        """2,01 m como atenção faria o aviso soar 3 m antes do que o plano manda."""
        c = self.cidade("timbo")
        self.assertEqual(c["cotas_m"], {"ativacao_plancon": 5.0, "ruas_alerta_citadas": 6.0})
        div = c["cotas_divergencia"]
        self.assertEqual(div["nao_adotada"]["atencao"], 3.0)
        self.assertEqual(div["nao_adotada"]["alto_risco_a_partir_de"], 4.3)
        self.assertIn("NÃO adotar", div["nao_adotada"]["_regra"])
        self.assertIn("não conferido por mim", div["_estado"].lower())

    def test_itajai_continua_sem_registro_de_cheia(self):
        """As oito leituras de 10/09/2011 são de UM horário, não o pico, e a
        identidade com as DC de hoje é por nome. Entram só por decisão do
        Jefferson — este teste cai no dia em que entrarem, e é para cair, para
        a nota do README ser reescrita junto."""
        ev = le_json("enchentes.json")["eventos"]
        self.assertEqual([r for r in ev if r.get("cidade") == "itajai"], [])

    def test_rio_do_sul_tem_1983_e_2013_pela_tabela_municipal(self):
        """Até 19/09/2026 este teste travava a AUSÊNCIA de 1983 e 2013, e caiu
        de propósito no dia em que o Jefferson conferiu a tabela do Histórico
        de Cheias da Defesa Civil de Rio do Sul linha a linha (9 de 9 níveis
        iguais) e decidiu a entrada. Agora trava a PRESENÇA, com os valores da
        tabela: mês sem dia, porque a fonte não dá o dia."""
        rs = {r["data"]: r for r in FonteDeRioDoSul.registros()}
        for data, pico in (("1983-05", 7.35), ("1983-07", 13.58),
                           ("1983-09", 7.60), ("2013-09", 10.39)):
            self.assertIn(data, rs)
            self.assertEqual(rs[data]["pico_m"], pico)
            self.assertEqual(rs[data]["confianca"], "media")
            self.assertIsNone(rs[data]["referencia"])
            self.assertNotIn("fonte_rotulo_anterior", rs[data])
        # Julho de 1983 passa a ser o maior pico de Rio do Sul — acima dos
        # 13,04 m de nov/2023, como em Blumenau (15,34 m em 09/07/1983).
        maior = max(rs.values(), key=lambda r: r["pico_m"])
        self.assertEqual(maior["data"], "1983-07")

    def test_rio_do_sul_2017_segue_com_o_pico_e_nao_com_a_leitura_das_10h(self):
        ev = le_json("enchentes.json")["eventos"]
        jun17 = [r for r in ev if r.get("cidade") == "rio-do-sul"
                 and str(r.get("data", "")).startswith("2017-06")]
        self.assertEqual(len(jun17), 1)
        self.assertEqual(jun17[0]["pico_m"], 10.89)


if __name__ == "__main__":
    unittest.main(verbosity=2)
