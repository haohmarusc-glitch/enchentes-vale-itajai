#!/usr/bin/env python3
"""Testes do coletor dos alertas da IDAP (`coleta_alertas_idap.py`).

O que não pode falhar: pedir o feed sem ler o robots; deixar entrar alerta de outro estado; trocar o fuso
(`enviado_em` é Brasília SEM fuso); chamar de "SC inteiro" o que o feed declara por município (ou o contrário);
casar cidade por proximidade em vez de nome; perder um alerta ainda vigente só porque saiu do feed de ~12 h; e a
publicação levar um arquivo velho.

    python3 scripts/teste_coleta_alertas_idap.py
"""
from __future__ import annotations

import io
import json
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))

import coleta_alertas_idap as ci  # noqa: E402

AGORA = datetime(2026, 11, 8, 2, 15, tzinfo=timezone.utc)
CIDADES = {"blumenau": "blumenau", "gaspar": "gaspar", "itajai": "itajai", "rio do sul": "rio-do-sul"}


def entrada(ident: str, area: str, ibge: list[str], *, sent="2026-11-07T18:57:13-03:00",
            expires="2026-11-08T07:00:00-03:00", headline="Defesa Civil:ATENCAO - INUNDACAO GRADUAL",
            description="ATENÇÃO - INUNDAÇÃO GRADUAL nas próximas horas. Ocorrências ligue 199 ou 193.",
            sender_name="Defesa Civil Estadual de Santa Catarina", msg_type="Alert", references="") -> str:
    geos = "".join(f"<geocode><valueName>IBGE</valueName><value>{c}</value></geocode>" for c in ibge)
    refs = f"<references>{references}</references>" if references else ""
    return f"""<entry><title>INUNDAÇÕES</title><id>{ident}</id><updated>2026-11-07T21:57:13Z</updated>
<content type="text/xml"><alert xmlns="urn:oasis:names:tc:emergency:cap:1.2">
<identifier>{ident}</identifier><sender>CENAD-SEDEC</sender><sent>{sent}</sent><status>Actual</status>
<msgType>{msg_type}</msgType>{refs}<source>Defesa Civil</source><scope>Public</scope>
<info><language>pt-BR</language><category>Geo</category><event>INUNDAÇÕES</event><urgency>Expected</urgency>
<severity>Severe</severity><certainty>Likely</certainty><expires>{expires}</expires>
<senderName>{sender_name}</senderName><headline>{headline}</headline><description>{description}</description>
<instruction>Siga as orientações da defesa civil local.</instruction>
<parameter><valueName>CHANNEL-LIST</valueName><value>Google</value></parameter>
<area><areaDesc>{area}</areaDesc><polygon>-26.9,-49.0 -26.9,-49.1 -27.0,-49.1 -26.9,-49.0</polygon>{geos}</area>
</info></alert></content></entry>"""


def feed(*entradas: str) -> bytes:
    return (f"""<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom"><title>Rss Idap</title><id>http://idapapi.mi.gov.br/api/rss/cap</id>
<updated>2026-11-08T02:09:54Z</updated>{''.join(entradas)}</feed>""").encode("utf-8")


GASPAR = entrada("197200/2026", "Gaspar/SC", ["4205902"])
BLUMENAU = entrada("197241/2026", "Blumenau/SC", ["4202404"], sent="2026-11-07T21:23:20-03:00",
                   expires="2026-11-08T01:00:00-03:00", sender_name="Defesa Civil de Blumenau (SC)",
                   description="ALERTABLU INFORMA - previsão 8,20 m à 01h do dia 08/11/26, sendo este o pico estimado.")
ESTADO = entrada("196995/2026", "SANTA CATARINA/SC", [], sent="2026-11-07T11:48:59-03:00",
                 expires="2026-11-07T13:45:00-03:00",
                 description="ATENÇÃO - TEMPORAIS para os municípios de Abdon Batista, Campos Novos …")
DOIS = entrada("197081/2026", "Trombudo Central/SC, Agronômica/SC", ["4218608", "4200309"])
PARANA = entrada("197300/2026", "Curitiba/PR", ["4106902"])
GOIAS_COM_NOME_IGUAL = entrada("197301/2026", "Gaspar/GO", ["5200000"])


def ler(conteudo: bytes):
    return ci.ler_feed(io.BytesIO(conteudo), CIDADES)


class TestLeitura(unittest.TestCase):
    def test_so_entra_sc(self):
        _, alertas, total = ler(feed(GASPAR, PARANA, GOIAS_COM_NOME_IGUAL))
        self.assertEqual(total, 3)
        self.assertEqual([a["identificador"] for a in alertas], ["197200/2026"])

    def test_fuso_de_brasilia_sem_offset_e_original_guardado(self):
        _, (a,), _ = ler(feed(GASPAR))
        self.assertEqual(a["enviado_em"], "2026-11-07T18:57:13")
        self.assertEqual(a["enviado_em_original"], "2026-11-07T18:57:13-03:00")
        self.assertEqual(a["expira_em"], "2026-11-08T07:00:00")

    def test_carimbo_em_utc_vira_brasilia(self):
        _, (a,), _ = ler(feed(entrada("1/2026", "Gaspar/SC", ["4205902"], sent="2026-11-07T21:57:13Z")))
        self.assertEqual(a["enviado_em"], "2026-11-07T18:57:13")

    def test_carimbo_sem_fuso_nao_entra(self):
        _, alertas, _ = ler(feed(entrada("1/2026", "Gaspar/SC", ["4205902"], sent="2026-11-07T18:57:13")))
        self.assertEqual(alertas, [])

    def test_municipios_com_ibge_na_ordem_e_cidade_do_projeto_pelo_nome(self):
        _, (a,), _ = ler(feed(GASPAR))
        self.assertEqual(a["municipios"], [{"nome": "Gaspar", "uf": "SC", "ibge": "4205902"}])
        self.assertEqual(a["cidades_do_projeto"], ["gaspar"])
        self.assertEqual(a["area_declarada"], "municipios")

    def test_dois_municipios_so_um_do_projeto(self):
        _, (a,), _ = ci.ler_feed(io.BytesIO(feed(DOIS)), {"trombudo central": "trombudo-central"})
        self.assertEqual([m["nome"] for m in a["municipios"]], ["Trombudo Central", "Agronômica"])
        self.assertEqual(a["cidades_do_projeto"], ["trombudo-central"])

    def test_contagem_que_nao_bate_nao_adivinha_o_ibge(self):
        _, (a,), _ = ler(feed(entrada("1/2026", "Gaspar/SC, Ilhota/SC", ["4205902"])))
        self.assertEqual([m["ibge"] for m in a["municipios"]], [None, None])

    def test_area_do_estado_nao_vira_municipio_e_nao_casa_cidade(self):
        _, (a,), _ = ler(feed(ESTADO))
        self.assertEqual(a["area_declarada"], "estado")
        self.assertEqual(a["municipios"], [])
        self.assertEqual(a["cidades_do_projeto"], [])

    def test_titulo_sem_prefixo_e_texto_cortado(self):
        longo = "x" * (ci.TEXTO_MAX + 50)
        _, (a,), _ = ler(feed(entrada("1/2026", "Gaspar/SC", ["4205902"], description=longo)))
        self.assertEqual(a["titulo"], "ATENCAO - INUNDACAO GRADUAL")
        self.assertTrue(a["descricao"].endswith("…"))
        self.assertEqual(len(a["descricao"]), ci.TEXTO_MAX + 1)

    def test_feed_vazio_ou_outra_coisa_falha(self):
        with self.assertRaises(ci.Falha):
            ler(feed())
        with self.assertRaises(Exception):
            ler(b"<html>login</html>")

    def test_cidades_do_projeto_vem_de_estacoes_json(self):
        nomes = ci.nomes_das_cidades()
        self.assertEqual(nomes.get("itajai"), "itajai")
        self.assertEqual(nomes.get("blumenau"), "blumenau")


class TestJuntar(unittest.TestCase):
    def test_alerta_que_saiu_do_feed_fica_enquanto_vale(self):
        _, antes, _ = ler(feed(GASPAR, BLUMENAU))
        anterior = {"alertas": ci.juntar(antes, None, AGORA)}
        _, agora, _ = ler(feed(GASPAR))
        r = ci.juntar(agora, anterior, AGORA + timedelta(hours=3))
        por_id = {a["identificador"]: a for a in r}
        self.assertTrue(por_id["197200/2026"]["no_feed"])
        self.assertFalse(por_id["197241/2026"]["no_feed"])  # expirou 01:00 BRT, ainda dentro das 6 h
        expirou = datetime(2026, 11, 8, 4, 0, tzinfo=timezone.utc)  # 01:00 de Brasília
        r = ci.juntar(agora, anterior, expirou + timedelta(hours=ci.GUARDA_APOS_EXPIRAR_H, minutes=1))
        self.assertNotIn("197241/2026", {a["identificador"] for a in r})

    def test_visto_primeiro_em_nao_muda(self):
        _, a1, _ = ler(feed(GASPAR))
        primeiro = ci.juntar(a1, None, AGORA)
        depois = ci.juntar(a1, {"alertas": primeiro}, AGORA + timedelta(minutes=15))
        self.assertEqual(depois[0]["visto_primeiro_em"], "2026-11-08T02:15:00+00:00")

    def test_cancelamento_marca_o_alerta(self):
        cancela = entrada("2/2026", "Gaspar/SC", ["4205902"], msg_type="Cancel", sent="2026-11-07T20:00:00-03:00",
                          references="CENAD-SEDEC,197200/2026,2026-11-07T18:57:13-03:00")
        _, a, _ = ler(feed(GASPAR, cancela))
        r = {x["identificador"]: x for x in ci.juntar(a, None, AGORA)}
        self.assertTrue(r["197200/2026"]["cancelado"])

    def test_mais_novo_primeiro(self):
        _, a, _ = ler(feed(GASPAR, BLUMENAU, ESTADO))
        self.assertEqual([x["identificador"] for x in ci.juntar(a, None, AGORA)],
                         ["197241/2026", "197200/2026", "196995/2026"])


class TestValidarEGravar(unittest.TestCase):
    def corpo(self, gerado=AGORA):
        _, a, total = ler(feed(GASPAR))
        return ci.montar(ci.juntar(a, None, gerado), gerado.isoformat(timespec="seconds"), "2026-11-08T02:09:54Z",
                         total)

    def test_publicacao_aceita_ate_45_min(self):
        self.assertTrue(ci.validar(self.corpo(), AGORA + timedelta(minutes=44)))
        self.assertFalse(ci.validar(self.corpo(), AGORA + timedelta(minutes=46)))
        self.assertFalse(ci.validar(self.corpo(), AGORA - timedelta(minutes=1)))

    def test_recusa_enviado_em_com_fuso(self):
        c = self.corpo()
        c["alertas"][0]["enviado_em"] += "-03:00"
        self.assertFalse(ci.validar(c, AGORA))

    def test_aviso_fala_do_199_e_de_que_nao_e_faixa(self):
        texto = self.corpo()["aviso"]
        self.assertIn("199", texto)
        self.assertIn("não são faixa", texto.lower())

    def test_gravar_e_falha_que_nao_apaga_o_anterior(self):
        with tempfile.TemporaryDirectory() as d, mock.patch.object(ci, "DADOS", Path(d)), \
                mock.patch("coleta_alertas_idap.grava_json",
                           lambda nome, c: (Path(d) / nome).write_text(json.dumps(c), encoding="utf-8")), \
                mock.patch("sys.stdout"), mock.patch("sys.stderr"), \
                mock.patch.object(ci, "nomes_das_cidades", lambda: CIDADES):
            (Path(d) / "tempo-real").mkdir()
            self.assertEqual(ci.gravar(lambda: feed(GASPAR), AGORA), 0)
            destino = Path(d) / ci.ARQUIVO_PUBLICAVEL
            self.assertEqual(json.loads(destino.read_text())["alertas"][0]["cidades_do_projeto"], ["gaspar"])

            def cai():
                raise ci.Falha("timeout")
            self.assertEqual(ci.gravar(cai, AGORA), 1)
            self.assertTrue(destino.exists())


class Resposta:
    def __init__(self, status: int, corpo: bytes = b""):
        self.status_code, self.content = status, corpo
        self.text = corpo.decode("utf-8")


class TestRobots(unittest.TestCase):
    def pedir(self, robots: Resposta):
        pedidos = []

        def pedir(url):
            pedidos.append(url)
            return robots if url == ci.ROBOTS else Resposta(200, feed(GASPAR))
        return pedir, pedidos

    def test_robots_antes_e_404_e_sem_regras(self):
        pedir, pedidos = self.pedir(Resposta(404))
        ci.baixar_feed(pedir)
        self.assertEqual(pedidos, [ci.ROBOTS, ci.URL])

    def test_robots_que_recusa_nao_deixa_pedir(self):
        pedir, pedidos = self.pedir(Resposta(200, b"User-agent: *\nDisallow: /idap/\n"))
        with self.assertRaises(ci.Falha):
            ci.baixar_feed(pedir)
        self.assertEqual(pedidos, [ci.ROBOTS])

    def test_robots_com_erro_e_recusa(self):
        pedir, pedidos = self.pedir(Resposta(503))
        with self.assertRaises(ci.Falha):
            ci.baixar_feed(pedir)
        self.assertEqual(pedidos, [ci.ROBOTS])


class TestPublicacao(unittest.TestCase):
    def test_publicar_usa_a_mesma_idade_maxima(self):
        script = (Path(__file__).resolve().parent / "publicar_tempo_real.sh").read_text(encoding="utf-8")
        self.assertIn("ultimo_alertas_idap.json", script)
        self.assertIn(f"idade <= {ci.IDADE_MAX_PUBLICACAO_S}", script)
        self.assertNotIn("python3 scripts/coleta_alertas_idap.py", script,
                         "o feed leva ~85 s: não cabe no corte de 60 s")


if __name__ == "__main__":
    unittest.main()
