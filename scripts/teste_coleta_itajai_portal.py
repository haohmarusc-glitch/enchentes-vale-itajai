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
from datetime import datetime, timedelta, timezone
from pathlib import Path

from coleta_itajai_portal import (MIN_PARES, MUNICIPIO_BLUMENAU, MUNICIPIO_ITAJAI,
                                  REGUA_BLUMENAU, TITULO_BLUMENAU, TOLERANCIA_COORD_M,
                                  URL_BLUMENAU, carga, coletar, conferir_com_alertablu,
                                  conferir_municipio, municipio_da_carga,
                                  distancia_m, para_brasilia, parse, parse_blumenau)
from comum import classificar_estacao, estacoes_tempo_real

RAIZ = Path(__file__).resolve().parent.parent
PAGINA_REAL = RAIZ / "data" / "brutos" / "itajai-portal-novo-2026-09-19.html"
PAGINA_BRUSQUE = RAIZ / "data" / "brutos" / "itajai-portal-rios-municipio-2-brusque-2026-09-21.html"
#: Os três municípios que o portal serve além de Itajaí, capturados pelo
#: Jefferson em 21/09/2026: (arquivo, municipioId, nome, código, fonte, cotas).
OUTROS_MUNICIPIOS = [
    ("itajai-portal-rios-municipio-2-brusque-2026-09-21.html", 2, "Brusque",
     "DCSC-00019", "Brusque", (3.5, 5, 6)),
    ("itajai-portal-rios-municipio-3-blumenau-2026-09-21.html", 3, "Blumenau",
     "PADKND", "AlertaBlu PADKND — Nível do rio", (4, 6, 8)),
    ("itajai-portal-rios-municipio-4-rio-do-sul-2026-09-21.html", 4, "Rio do Sul",
     "DCSC-00013", "Rio do Sul", (5, 6, 7)),
]

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




class TestPaginaDeOutroMunicipio(unittest.TestCase):
    """O corpo de `?municipio_id=2`, capturado pelo Jefferson em 21/09/2026.

    O portal é de Itajaí e serve quatro cidades com a MESMA moldura; a página
    de Brusque traz o cabeçalho "Situação atual em Itajaí". Cidade nunca se
    infere pelo domínio: vem do `props.municipioId`, e as estações e a fonte
    têm que concordar com ele."""

    @classmethod
    def setUpClass(cls):
        cls.html = PAGINA_BRUSQUE.read_text(encoding="utf-8")
        cls.dados = carga(cls.html)

    def test_a_pagina_diz_que_e_brusque(self):
        self.assertEqual(municipio_da_carga(self.dados), {"id": 2, "nome": "Brusque"})

    def test_a_moldura_diz_itajai_e_o_corpo_diz_brusque(self):
        """A armadilha, preservada: o cabeçalho é de outra cidade e de três
        dias antes."""
        self.assertIn("Situação atual em Itajaí", self.html)
        self.assertIn("18/09/2026, 17:35", self.html)
        est = self.dados["props"]["estacoes"][0]
        self.assertEqual(est["medido_em"], "2026-09-21T11:00:00+00:00")

    def test_pedido_e_resposta_conferem_para_brusque_e_nao_para_itajai(self):
        self.assertIsNone(conferir_municipio(self.dados, 2))
        motivo = conferir_municipio(self.dados, MUNICIPIO_ITAJAI)
        self.assertIsNotNone(motivo)
        self.assertIn("respondeu 2", motivo)

    def test_a_unica_estacao_vem_sem_coordenada(self):
        """É o motivo medido de Brusque continuar desligada: a identidade aqui
        é provada por coordenada, e o portal não a publica."""
        est = self.dados["props"]["estacoes"]
        self.assertEqual(len(est), 1)
        self.assertEqual(est[0]["codigo"], "DCSC-00019")
        self.assertEqual(est[0]["fonte"], "Brusque")
        self.assertIsNone(est[0]["latitude"])
        self.assertIsNone(est[0]["longitude"])

    def test_parse_recusa_a_pagina_inteira(self):
        """Nada de Brusque vira leitura de Itajaí, nem por engano de código."""
        self.assertEqual(parse(self.html), [])

    def test_a_terceira_escala_esta_no_corpo(self):
        est = self.dados["props"]["estacoes"][0]
        self.assertEqual((est["atencao_m"], est["alerta_m"], est["emergencia_m"]), (3.5, 5, 6))

    def test_pagina_sem_municipio_nao_vira_itajai(self):
        dados = {"props": {"estacoes": []}}
        self.assertIsNone(municipio_da_carga(dados))
        self.assertIn("não diz", conferir_municipio(dados, MUNICIPIO_ITAJAI))

    def test_os_tres_outros_municipios_seguem_o_mesmo_padrao(self):
        """Blumenau (3) e Rio do Sul (4) chegaram em 21/09/2026 e confirmam o
        que Brusque mostrou: UMA estação por município, SEM coordenada, com a
        moldura de Itajaí por cima. Nenhum vira leitura de Itajaí; Blumenau
        tem leitor próprio, com prova por medição (`TestBlumenauDe5Minutos`)."""
        for arquivo, mid, nome, codigo, fonte, cotas in OUTROS_MUNICIPIOS:
            with self.subTest(municipio=nome):
                html = (RAIZ / "data" / "brutos" / arquivo).read_text(encoding="utf-8")
                dados = carga(html)
                self.assertEqual(municipio_da_carga(dados), {"id": mid, "nome": nome})
                est = dados["props"]["estacoes"]
                self.assertEqual(len(est), 1)
                self.assertEqual(est[0]["codigo"], codigo)
                self.assertEqual(est[0]["fonte"], fonte)
                self.assertEqual(est[0]["municipio_id"], mid)
                self.assertIsNone(est[0]["latitude"])
                self.assertIsNone(est[0]["longitude"])
                self.assertEqual((est[0]["atencao_m"], est[0]["alerta_m"], est[0]["emergencia_m"]), cotas)
                self.assertIn("Situação atual em Itajaí", html)
                self.assertIsNone(conferir_municipio(dados, mid))
                self.assertIsNotNone(conferir_municipio(dados, MUNICIPIO_ITAJAI))
                self.assertEqual(parse(html), [])

    def test_a_tendencia_do_portal_nao_e_de_confianca(self):
        """Rio do Sul, 21/09/2026: o portal diz `tendencia: "estavel"` com a
        própria série dele caindo 69 cm em 12 h (5,08 → 4,39). O campo não
        descreve a série; este coletor nunca o lê, e o teste trava o motivo."""
        html = (RAIZ / "data" / "brutos" / OUTROS_MUNICIPIOS[2][0]).read_text(encoding="utf-8")
        est = carga(html)["props"]["estacoes"][0]
        serie = est["serie_12_h"]
        self.assertEqual(est["tendencia"], "estavel")
        self.assertLess(serie[-1]["nivel_rio_m"] - serie[0]["nivel_rio_m"], -0.6)

    def test_estacao_de_outro_municipio_e_apanhada_e_a_fonte_nao_decide(self):
        """`municipio_id` da estação decide; `fonte` NÃO. A primeira versão
        exigia que a fonte citasse a cidade e a captura de Blumenau derrubou
        isso: a fonte lá é "AlertaBlu PADKND — Nível do rio", o provedor."""
        base = {"props": {"municipioId": 1, "municipios": [{"id": 1, "nome": "Itajaí"}]}}
        d = {**base, "props": {**base["props"], "estacoes": [{"codigo": "DC01", "municipio_id": 2}]}}
        self.assertIn("município 2", conferir_municipio(d, 1))
        d = {**base, "props": {**base["props"], "estacoes": [{"codigo": "DC01", "municipio_id": 1,
                                                              "fonte": "AlertaBlu PADKND — Nível do rio"}]}}
        self.assertIsNone(conferir_municipio(d, 1))
        d = {**base, "props": {**base["props"], "estacoes": [{"codigo": "DC01", "municipio_id": 1,
                                                              "fonte": "Telemetria Itajaí"}]}}
        self.assertIsNone(conferir_municipio(d, 1))


#: A captura de 27/09/2026 21h04Z, feita pelo fluxo
#: .github/workflows/capturar-portal-itajai.yml (run 36350320996) e remontada
#: com o sha256 conferido — ver data/brutos/itajai-portal-captura-2026-09-27.json.
PAGINA_27_09 = RAIZ / "data" / "brutos" / "itajai-portal-rios-municipio-1-itajai-2026-09-27.html"
OUTROS_27_09 = [
    ("itajai-portal-rios-municipio-2-brusque-2026-09-27.html", 2, "Brusque",
     "DCSC-00019", "Brusque", (3.5, 5, 6)),
    ("itajai-portal-rios-municipio-3-blumenau-2026-09-27.html", 3, "Blumenau",
     "PADKND", "AlertaBlu PADKND — Nível do rio", (4, 6, 8)),
    ("itajai-portal-rios-municipio-4-rio-do-sul-2026-09-27.html", 4, "Rio do Sul",
     "DCSC-00013", "Rio do Sul", (5, 6, 7)),
]


class TestCapturaDe27DeSetembro(unittest.TestCase):
    """Oito dias depois da primeira captura, o portal mudou a FORMA, não o
    conteúdo que o projeto usa. Este bloco trava as duas metades: o que tem
    que continuar igual, e o que mudou sem poder vazar para a leitura."""

    @classmethod
    def setUpClass(cls):
        cls.html = PAGINA_27_09.read_text(encoding="utf-8")
        cls.dados = carga(cls.html)
        cls.leituras = parse(cls.html)
        cls.antes = carga(PAGINA_REAL.read_text(encoding="utf-8"))

    def test_as_onze_reguas_saem_sem_ajuste_no_coletor(self):
        self.assertEqual(len(self.leituras), 11)
        self.assertEqual({l["cidade"] for l in self.leituras}, {"itajai"})

    def test_os_mesmos_onze_codigos_de_19_09(self):
        cod = lambda d: sorted(e["codigo"] for e in d["props"]["estacoes"])
        self.assertEqual(cod(self.dados), cod(self.antes))

    def test_as_onze_seguem_a_zero_metro_do_cadastro(self):
        """Nenhuma régua saiu do lugar entre 19/09 e 27/09."""
        cadastro = {e["codigo"]: e for e in estacoes_tempo_real()
                    if str(e.get("codigo", "")).startswith("DC-")}
        for e in self.dados["props"]["estacoes"]:
            nossa = cadastro[f"DC-{e['codigo'][2:]}"]
            self.assertLessEqual(
                distancia_m((nossa["lat"], nossa["lon"]),
                            (e["latitude"], e["longitude"])), 1.0, e["codigo"])

    def test_carimbos_em_brasilia(self):
        """O portal publicou 20h50–20h51 UTC; o repositório grava 17h50–17h51."""
        for l in self.leituras:
            self.assertNotIn("+", l["medido_em"])
            self.assertTrue(l["medido_em"].startswith("2026-09-27T17:5"), l["medido_em"])

    def test_campo_novo_historico_existe_e_nao_vaza(self):
        """`historico_monitoramento` apareceu em 27/09: vinte registros por
        estação, com nível, variação, tendência e SEIS janelas de chuva, em
        UTC. É o que dobrou o tamanho da página (87 KB → 180 KB). O coletor
        não o lê — a leitura continua com as mesmas chaves de antes."""
        for e in self.dados["props"]["estacoes"]:
            h = e["historico_monitoramento"]
            self.assertEqual(len(h), 20, e["codigo"])
            self.assertIn("chuva_24_h_mm", h[0])
            self.assertIn("+00:00", h[0]["medido_em"])
        for l in self.leituras:
            self.assertEqual(set(l), {"estacao", "rio", "cidade", "nivel_m", "medido_em"})

    def test_cotas_do_portal_iguais_as_de_19_09_e_o_cadastro_no_plano(self):
        """As quatro divergências com o Plano de Contingência v17 (DC-01, DC-07,
        DC-08, DC-09) persistem idênticas oito dias depois. O cadastro segue no
        v17: trocar cota continua sendo decisão do Jefferson."""
        trinca = lambda e: (e["atencao_m"], e["alerta_m"], e["emergencia_m"])
        antes = {e["codigo"]: trinca(e) for e in self.antes["props"]["estacoes"]}
        agora = {e["codigo"]: trinca(e) for e in self.dados["props"]["estacoes"]}
        self.assertEqual(agora, antes)
        cadastro = {e["codigo"]: e["cotas_m"] for e in estacoes_tempo_real()
                    if str(e.get("codigo", "")).startswith("DC-")}
        divergem = sorted(
            f"DC-{c[2:]}" for c, t in agora.items()
            if t != tuple(cadastro[f"DC-{c[2:]}"][k] for k in ("atencao", "alerta", "emergencia")))
        self.assertEqual(divergem, ["DC-01", "DC-07", "DC-08", "DC-09"])

    def test_os_outros_tres_seguem_sem_coordenada_e_sem_moldura(self):
        """Brusque, Blumenau e Rio do Sul: mesma estação, mesma fonte, mesmas
        cotas, e ainda SEM coordenada — fora de `parse()`. O que mudou: a moldura
        "Situação atual em Itajaí" não vem mais no HTML servido (páginas de
        ~44 KB para ~15 KB). A armadilha passou para o navegador; a regra de
        conferir `props.municipioId` continua valendo igual."""
        for arquivo, mid, nome, codigo, fonte, cotas in OUTROS_27_09:
            with self.subTest(municipio=nome):
                html = (RAIZ / "data" / "brutos" / arquivo).read_text(encoding="utf-8")
                dados = carga(html)
                self.assertEqual(municipio_da_carga(dados), {"id": mid, "nome": nome})
                est = dados["props"]["estacoes"]
                self.assertEqual(len(est), 1)
                self.assertEqual((est[0]["codigo"], est[0]["fonte"]), (codigo, fonte))
                self.assertIsNone(est[0]["latitude"])
                self.assertIsNone(est[0]["longitude"])
                self.assertEqual((est[0]["atencao_m"], est[0]["alerta_m"], est[0]["emergencia_m"]), cotas)
                self.assertNotIn("Situação atual em Itajaí", html)
                self.assertIsNotNone(conferir_municipio(dados, MUNICIPIO_ITAJAI))
                self.assertEqual(parse(html), [])


CAPTURA_28_09 = RAIZ / "data" / "brutos" / "captura-fontes-2026-09-28"
PADKND_28_09 = CAPTURA_28_09 / "itajai-portal-rios-municipio-3-blumenau.html"
PADKND_27_09 = RAIZ / "data" / "brutos" / "itajai-portal-rios-municipio-3-blumenau-2026-09-27.html"
ALERTABLU_28_09 = CAPTURA_28_09 / "blumenau-alertablu-nivel-oficial.json"


class TestBlumenauDe5Minutos(unittest.TestCase):
    """A PADKND (municipio_id=3) entra como publicação da régua de Blumenau só
    quando bate com o AlertaBlu nas horas cheias em comum. Sem coordenada, é a
    medição que prova a régua — e o relógio, que no repasse antigo vinha 3 h
    atrasado."""

    AGORA_28 = datetime(2026, 9, 28, 3, 32, 32, tzinfo=timezone.utc)

    def setUp(self):
        self.pagina = PADKND_28_09.read_text(encoding="utf-8")
        self.alertablu = json.loads(ALERTABLU_28_09.read_text(encoding="utf-8"))

    def _alertablu_mexido(self, horas=0, soma_m=0.0, so_ate=None):
        a = json.loads(json.dumps(self.alertablu))
        niveis = []
        for n in a["niveis"]:
            t = datetime.fromisoformat(n["horaLeitura"].replace("Z", "+00:00")) + timedelta(hours=horas)
            if so_ate and t > so_ate:
                continue
            niveis.append({"nivel": round(n["nivel"] + soma_m, 2),
                           "horaLeitura": t.strftime("%Y-%m-%dT%H:%M:%SZ")})
        a["niveis"] = niveis
        return a

    def test_captura_de_28_09_entra_com_titulo_proprio(self):
        r = parse_blumenau(self.pagina, self.alertablu, self.AGORA_28)
        self.assertEqual(r, [{
            "estacao": "Blumenau (PADKND)", "rio": "itajai-acu", "cidade": "blumenau",
            "nivel_m": 3.2, "medido_em": "2026-09-28T00:05:00", "resgate_de": "Blumenau",
        }])

    def test_captura_de_27_09_tambem_bate(self):
        pagina = PADKND_27_09.read_text(encoding="utf-8")
        r = parse_blumenau(pagina, self.alertablu, datetime(2026, 9, 27, 21, 4, tzinfo=timezone.utc))
        self.assertEqual([(l["nivel_m"], l["medido_em"]) for l in r], [(3.3, "2026-09-27T17:50:00")])

    def test_as_horas_cheias_batem_ao_centimetro(self):
        """O que sustenta a ligação, medido: 12 de 12 horas iguais."""
        est = carga(self.pagina)["props"]["estacoes"][0]
        padknd = {p["medido_em"]: p["nivel_rio_m"] for p in est["serie_12_h"]}
        pares = [(padknd[n["horaLeitura"].replace("Z", "+00:00")], n["nivel"])
                 for n in self.alertablu["niveis"]
                 if n["horaLeitura"].replace("Z", "+00:00") in padknd]
        self.assertEqual(len(pares), 12)
        self.assertTrue(all(a == b for a, b in pares))

    def test_nunca_usa_o_titulo_do_repasse_atrasado(self):
        """'Blumenau' é o repasse antigo da página de Itajaí, 3 h atrasado:
        extrair_picos, nivel_antes e o site o tratam assim."""
        self.assertNotEqual(TITULO_BLUMENAU, "Blumenau")
        from extrair_picos import RELOGIO_DEFASADO
        self.assertNotIn(TITULO_BLUMENAU, RELOGIO_DEFASADO)

    def test_a_regua_coberta_esta_no_cadastro(self):
        titulos = {e.get("titulo") for e in estacoes_tempo_real()}
        self.assertIn(REGUA_BLUMENAU, titulos)
        self.assertNotIn(TITULO_BLUMENAU, titulos)

    def test_relogio_deslocado_em_3_h_e_recusado(self):
        self.assertEqual(parse_blumenau(self.pagina, self._alertablu_mexido(horas=3), self.AGORA_28), [])

    def test_valor_diferente_e_recusado(self):
        """Outra régua com o mesmo código daria número diferente no mesmo instante."""
        self.assertEqual(parse_blumenau(self.pagina, self._alertablu_mexido(soma_m=0.05), self.AGORA_28), [])

    def test_um_centimetro_de_arredondamento_passa(self):
        self.assertEqual(len(parse_blumenau(self.pagina, self._alertablu_mexido(soma_m=0.01), self.AGORA_28)), 1)

    def test_sem_alertablu_nao_entra(self):
        for a in (None, {}, {"niveis": []}):
            with self.subTest(alertablu=a):
                self.assertEqual(parse_blumenau(self.pagina, a, self.AGORA_28), [])

    def test_poucos_pares_nao_provam(self):
        """A série da PADKND começa às 15:05Z; cortar o AlertaBlu às 16:00Z deixa
        uma hora cheia em comum — coincidência num rio parado, não prova."""
        motivo = conferir_com_alertablu(
            carga(self.pagina)["props"]["estacoes"][0]["serie_12_h"],
            self._alertablu_mexido(so_ate=datetime(2026, 9, 27, 16, 0, tzinfo=timezone.utc))["niveis"],
            datetime(2026, 9, 28, 3, 5, tzinfo=timezone.utc))
        self.assertIn("mínimo", motivo)
        self.assertEqual(MIN_PARES, 3)

    def test_prova_velha_nao_vale(self):
        """Três pares que batem (16:00, 17:00 e 18:00Z), mas a 9 h da leitura de
        03:05Z: a régua pode ter sido trocada depois."""
        motivo = conferir_com_alertablu(
            carga(self.pagina)["props"]["estacoes"][0]["serie_12_h"],
            self._alertablu_mexido(so_ate=datetime(2026, 9, 27, 18, 0, tzinfo=timezone.utc))["niveis"],
            datetime(2026, 9, 28, 3, 5, tzinfo=timezone.utc))
        self.assertIn("prova velha", motivo)

    def test_carimbo_no_futuro_e_recusado(self):
        self.assertEqual(parse_blumenau(self.pagina, self.alertablu,
                                        datetime(2026, 9, 28, 2, 0, tzinfo=timezone.utc)), [])

    def test_pagina_de_outro_municipio_e_recusada(self):
        brusque = PAGINA_BRUSQUE.read_text(encoding="utf-8")
        self.assertEqual(parse_blumenau(brusque, self.alertablu, self.AGORA_28), [])
        itajai = (CAPTURA_28_09 / "itajai-portal-rios-municipio-1-itajai.html").read_text(encoding="utf-8")
        self.assertEqual(parse_blumenau(itajai, self.alertablu, self.AGORA_28), [])

    def test_nivel_implausivel_e_recusado(self):
        dados = carga(self.pagina)
        dados["props"]["estacoes"][0]["nivel_rio_m"] = 0
        pagina = '<div id="app" data-page="' + _html.escape(json.dumps(dados)) + '"></div>'
        self.assertEqual(parse_blumenau(pagina, self.alertablu, self.AGORA_28), [])

    def test_endereco_e_o_do_municipio_3(self):
        self.assertTrue(URL_BLUMENAU.endswith("?municipio_id=3"))
        self.assertEqual(MUNICIPIO_BLUMENAU, 3)

    def test_parse_de_itajai_continua_sem_blumenau(self):
        self.assertEqual(parse(self.pagina), [])


if __name__ == "__main__":
    unittest.main(verbosity=2)
