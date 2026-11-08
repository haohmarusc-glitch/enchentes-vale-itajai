#!/usr/bin/env python3
"""Testes da leitura dos avisos da Defesa Civil de SC pelo GitHub Actions (`avisos_dcsc_actions.py`).

O que não pode falhar: pedir sem ler o robots; publicar avisos de outra forma que a da VPS (os dois caminhos
usam `coleta_avisos_dcsc.converter`); a VPS aceitar leitura velha, de outro coletor ou com fuso no
`publicado_em`; e a leitura parar de ser regravada quando os avisos não mudam (a VPS a recusaria pela idade).

    python3 scripts/teste_avisos_dcsc_actions.py
"""
from __future__ import annotations

import json
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))

import avisos_dcsc_actions as aa  # noqa: E402
import coleta_avisos_dcsc as ca  # noqa: E402

AGORA = datetime(2026, 11, 8, 1, 30, tzinfo=timezone.utc)
POSTS = [
    {"id": 39600, "date_gmt": "2026-11-07T22:10:00", "link": "https://www.defesacivil.sc.gov.br/?p=39600",
     "title": {"rendered": "ALERTA – 07/11 19:10 – CHUVA PERSISTENTE"}, "categories": [7],
     "content": {"rendered": "<p>Chuva persistente no Vale do Itajaí e na Foz do Itajaí.</p>"}},
    {"id": 39590, "date_gmt": "2026-11-07T15:00:00", "link": "https://www.defesacivil.sc.gov.br/?p=39590",
     "title": {"rendered": "AVISO – 07/11 12:00 – TEMPORAIS"}, "categories": [6],
     "content": {"rendered": "<p>Temporais no Oeste.</p>"}},
]


def pedir_que_responde(robots: tuple[int, bytes] = (200, b"User-agent: *\nDisallow: /wp-admin/\n"),
                       api: tuple[int, bytes] | None = None):
    pedidos = []

    def pedir(url):
        pedidos.append(url)
        if url == aa.ROBOTS:
            return robots
        return api or (200, json.dumps(POSTS).encode("utf-8"))

    return pedir, pedidos


class TestRobots(unittest.TestCase):
    def test_robots_antes_de_tudo(self):
        pedir, pedidos = pedir_que_responde()
        aa.coletar(None, AGORA, pedir)
        self.assertEqual(pedidos, [aa.ROBOTS, aa.URL])

    def test_robots_que_recusa_nao_deixa_pedir(self):
        pedir, pedidos = pedir_que_responde(robots=(200, b"User-agent: *\nDisallow: /wp-json/\n"))
        with self.assertRaises(aa.Falha) as c:
            aa.coletar(None, AGORA, pedir)
        self.assertEqual(c.exception.codigo, "robots")
        self.assertEqual(pedidos, [aa.ROBOTS])

    def test_robots_com_erro_e_recusa_e_404_e_sem_regras(self):
        pedir, _ = pedir_que_responde(robots=(503, b""))
        with self.assertRaises(aa.Falha):
            aa.coletar(None, AGORA, pedir)
        pedir, pedidos = pedir_que_responde(robots=(404, b""))
        aa.coletar(None, AGORA, pedir)
        self.assertEqual(pedidos[-1], aa.URL)


class TestColeta(unittest.TestCase):
    def test_mesmos_avisos_da_vps(self):
        pedir, _ = pedir_que_responde()
        r = aa.coletar(None, AGORA, pedir)
        self.assertEqual(r["estado"], "nova")
        self.assertEqual(r["corpo"]["avisos"], ca.converter(POSTS))
        self.assertEqual(r["corpo"]["pagina_lida_em"], "2026-11-08T01:30:00+00:00")
        self.assertEqual(r["corpo"]["coletor"], "github-actions")

    def test_sem_mudanca_nao_regrava_mas_refresca_antes_do_teto(self):
        pedir, _ = pedir_que_responde()
        primeiro = aa.coletar(None, AGORA, pedir)["corpo"]
        r = aa.coletar(primeiro, AGORA + timedelta(minutes=30), pedir)
        self.assertFalse(r["mudou"])
        r = aa.coletar(primeiro, AGORA + timedelta(hours=aa.REFRESCAR_H, minutes=1), pedir)
        self.assertTrue(r["mudou"])
        self.assertEqual(r["estado"], "refresco")
        self.assertLess(aa.REFRESCAR_H + 0.5, aa.TETO_PAGINA_LIDA_H, "o refresco tem de vir antes do teto da VPS")

    def test_aviso_novo_regrava_na_hora(self):
        pedir, _ = pedir_que_responde()
        primeiro = aa.coletar(None, AGORA, pedir)["corpo"]
        outro = POSTS + [{**POSTS[0], "id": 39601, "title": {"rendered": "ALERTA – NOVO"}}]
        pedir2, _ = pedir_que_responde(api=(200, json.dumps(outro).encode("utf-8")))
        r = aa.coletar(primeiro, AGORA + timedelta(minutes=30), pedir2)
        self.assertEqual(r["estado"], "nova")

    def test_resposta_que_nao_e_lista_falha_com_o_bruto(self):
        pedir, _ = pedir_que_responde(api=(200, b'{"code":"rest_no_route"}'))
        with self.assertRaises(aa.Falha) as c:
            aa.coletar(None, AGORA, pedir)
        self.assertEqual(c.exception.codigo, "formato")
        self.assertTrue(c.exception.bruto)

    def test_http_de_erro_falha(self):
        pedir, _ = pedir_que_responde(api=(503, b"<html>"))
        with self.assertRaises(aa.Falha) as c:
            aa.coletar(None, AGORA, pedir)
        self.assertEqual(c.exception.codigo, "http")


class TestLeituraNaVps(unittest.TestCase):
    def corpo(self, **mudar):
        pedir, _ = pedir_que_responde()
        c = aa.coletar(None, AGORA, pedir)["corpo"]
        c.update(mudar)
        return c

    def test_aceita_o_que_o_runner_publicou(self):
        v = aa.validar(self.corpo(), AGORA + timedelta(minutes=40))
        self.assertEqual(v["pagina_lida_em"], "2026-11-08T01:30:00+00:00")
        self.assertEqual(len(v["avisos"]), 2)

    def test_recusa_velho_futuro_e_de_outro_coletor(self):
        self.assertIsNone(aa.validar(self.corpo(), AGORA + timedelta(hours=aa.TETO_PAGINA_LIDA_H, minutes=1)))
        self.assertIsNone(aa.validar(self.corpo(), AGORA - timedelta(hours=1)))
        self.assertIsNone(aa.validar(self.corpo(coletor="vps"), AGORA))
        self.assertIsNone(aa.validar(self.corpo(pagina_lida_em="2026-11-08T01:30:00"), AGORA))  # sem fuso

    def test_recusa_aviso_com_fuso_ou_sem_campo(self):
        c = self.corpo()
        c["avisos"][0]["publicado_em"] += "+00:00"
        self.assertIsNone(aa.validar(c, AGORA))
        c = self.corpo()
        del c["avisos"][0]["inclui_bacia"]
        self.assertIsNone(aa.validar(c, AGORA))

    def test_ler_publicado_engole_falha_de_rede(self):
        def cai(url):
            raise ConnectionError("404 branch inexistente")
        with mock.patch("sys.stderr"):
            self.assertIsNone(aa.ler_publicado(buscar=cai, agora=AGORA))

    def test_url_publicado_e_do_branch_proprio(self):
        self.assertTrue(aa.URL_PUBLICADO.endswith(f"/{aa.BRANCH}/{aa.ARQUIVO}"))
        self.assertTrue(aa.URL_PUBLICADO.startswith("https://raw.githubusercontent.com/"))


class TestLinhaDeComando(unittest.TestCase):
    def test_grava_quando_muda_e_nao_grava_quando_nao(self):
        pedir, _ = pedir_que_responde()
        with tempfile.TemporaryDirectory() as d, mock.patch("sys.stdout"):
            saida = Path(d) / "saida"
            self.assertEqual(aa.main(["--saida", str(saida)], AGORA, pedir), 0)
            publicado = saida / aa.ARQUIVO
            self.assertTrue(publicado.exists())
            self.assertTrue((saida / aa.ARQUIVO_BRUTO).exists())
            saida2 = Path(d) / "saida2"
            self.assertEqual(aa.main(["--anterior", str(publicado), "--saida", str(saida2)],
                                     AGORA + timedelta(minutes=30), pedir), 0)
            self.assertFalse((saida2 / aa.ARQUIVO).exists())

    def test_falha_deixa_diagnostico_e_sai_1(self):
        pedir, _ = pedir_que_responde(robots=(403, b""))
        with tempfile.TemporaryDirectory() as d, mock.patch("sys.stdout"):
            self.assertEqual(aa.main(["--saida", d], AGORA, pedir), 1)
            falha = json.loads((Path(d) / "falha.json").read_text(encoding="utf-8"))
        self.assertEqual(falha["codigo"], "robots")


if __name__ == "__main__":
    unittest.main()
