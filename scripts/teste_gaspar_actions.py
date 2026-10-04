#!/usr/bin/env python3
"""
Testes da coleta de Gaspar pelo GitHub Actions (decisão de 04/10/2026).

O que eles travam, em ordem de estrago:

* robots.txt que recusa (ou não responde) → a página NÃO é pedida;
* timeout e erro HTTP → falha registrada (código, motivo, artefato), nunca
  silêncio nem arquivo publicado;
* leitura igual à anterior → nada regravado (sem 96 commits iguais por dia);
* leitura velha → avisada, nunca renovada; a VPS a recusa pela idade;
* a VPS lê o que o Actions publicou com a validação da ponte do PC.

Sem rede: o HTML real é o da captura de 28/09/2026 (1,84 m, 27/09 19h28).
"""

import copy
import hashlib
import json
import os
import sys
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))

import coleta_niveis
import gaspar_actions as ga
from comum import USER_AGENT

# Na CI estas variáveis existem e apontam para o passo de TESTE; o `main` daqui
# escreveria nelas. Cada teste que precisa delas cria as suas.
for _var in ("GITHUB_OUTPUT", "GITHUB_STEP_SUMMARY"):
    os.environ.pop(_var, None)

HTML_REAL = (Path(__file__).resolve().parent.parent / "data" / "brutos"
             / "captura-fontes-2026-09-28" / "gaspar-estacao-21.html").read_bytes()

#: 27/09/2026 20h00 em Brasília: 32 min depois da medição da captura.
AGORA = datetime(2026, 9, 27, 23, 0, tzinfo=timezone.utc)

ROBOTS_LIBERA = b"User-agent: *\nDisallow: /admin\n"
ROBOTS_RECUSA = b"User-agent: *\nDisallow: /estacao/\n"


class Servidor:
    """Finge o portal: registra cada URL pedida e responde do roteiro."""

    def __init__(self, robots=(200, ROBOTS_LIBERA), pagina=(200, HTML_REAL)):
        self.roteiro = {ga.ROBOTS: robots, ga.URL: pagina}
        self.pedidas = []

    def __call__(self, url):
        self.pedidas.append(url)
        resposta = self.roteiro[url]
        if isinstance(resposta, Exception):
            raise resposta
        return resposta


class Robots(unittest.TestCase):
    def test_robots_que_proibe_NAO_baixa_a_pagina(self):
        s = Servidor(robots=(200, ROBOTS_RECUSA))
        with self.assertRaises(ga.Falha) as ctx:
            ga.coletar(None, AGORA, s)
        self.assertEqual(ctx.exception.codigo, "robots")
        self.assertIn("bloqueado por robots.txt", ctx.exception.motivo)
        self.assertEqual(s.pedidas, [ga.ROBOTS], "a página foi pedida apesar do robots.txt")

    def test_robots_fora_do_ar_conta_como_recusa(self):
        """RFC 9309: 5xx ou sem resposta, na dúvida não se pede."""
        for robots in [(503, b""), ga.Falha("timeout", "timeout no robots")]:
            with self.subTest(robots=robots):
                s = Servidor(robots=robots)
                with self.assertRaises(ga.Falha):
                    ga.coletar(None, AGORA, s)
                self.assertEqual(s.pedidas, [ga.ROBOTS])

    def test_robots_inexistente_libera(self):
        s = Servidor(robots=(404, b"nao ha"))
        self.assertEqual(ga.coletar(None, AGORA, s)["estado"], "nova")
        self.assertEqual(s.pedidas, [ga.ROBOTS, ga.URL])


class Leitura(unittest.TestCase):
    def test_le_a_captura_real_e_guarda_o_bruto_com_sha256(self):
        r = ga.coletar(None, AGORA, Servidor())
        self.assertTrue(r["mudou"])
        l = r["corpo"]["leitura"]
        self.assertEqual((l["nivel_m"], l["medido_em"]), (1.84, "2026-09-27T19:28:00"))
        self.assertEqual(l["cidade"], "gaspar")
        self.assertEqual(r["bruto"], HTML_REAL)
        self.assertEqual(r["corpo"]["bruto"]["sha256"], hashlib.sha256(HTML_REAL).hexdigest())
        self.assertEqual(r["corpo"]["user_agent"], USER_AGENT)

    def test_fusos_medido_em_brasilia_sem_fuso_e_coletado_em_utc(self):
        corpo = ga.coletar(None, AGORA, Servidor())["corpo"]
        self.assertEqual(corpo["coletado_em"], "2026-09-27T23:00:00+00:00")
        self.assertIsNone(datetime.fromisoformat(corpo["leitura"]["medido_em"]).tzinfo)

    def test_pagina_sem_a_regua_do_acu_e_falha_com_bruto(self):
        outra = HTML_REAL.replace("Rio Itajaí Açu Gaspar".encode(), b"RIBEIRAO BELCHIOR CENTRAL")
        with self.assertRaises(ga.Falha) as ctx:
            ga.coletar(None, AGORA, Servidor(pagina=(200, outra)))
        self.assertEqual(ctx.exception.codigo, "sem_leitura")
        self.assertEqual(ctx.exception.bruto, outra)

    def test_medicao_no_futuro_e_falha(self):
        antes = datetime(2026, 9, 27, 21, 0, tzinfo=timezone.utc)  # 18h00 em Brasília
        with self.assertRaises(ga.Falha) as ctx:
            ga.coletar(None, antes, Servidor())
        self.assertEqual(ctx.exception.codigo, "futuro")


class SemMudanca(unittest.TestCase):
    def test_mesma_leitura_nao_regrava(self):
        anterior = ga.coletar(None, AGORA, Servidor())["corpo"]
        depois = datetime(2026, 9, 27, 23, 15, tzinfo=timezone.utc)
        r = ga.coletar(anterior, depois, Servidor())
        self.assertEqual(r["estado"], "sem_mudanca")
        self.assertFalse(r["mudou"])
        self.assertIsNone(r["corpo"])

    def test_nivel_ou_horario_novo_regrava(self):
        anterior = copy.deepcopy(ga.coletar(None, AGORA, Servidor())["corpo"])
        anterior["leitura"]["medido_em"] = "2026-09-27T18:28:00"
        self.assertTrue(ga.coletar(anterior, AGORA, Servidor())["mudou"])

    def test_main_sem_mudanca_nao_escreve_arquivo_e_avisa_o_fluxo(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            anterior = tmp / "anterior.json"
            anterior.write_text(json.dumps(ga.coletar(None, AGORA, Servidor())["corpo"]))
            saida, saidas = tmp / "saida", tmp / "github_output"
            with mock.patch.dict(os.environ, {"GITHUB_OUTPUT": str(saidas)}):
                codigo = ga.main(["--anterior", str(anterior), "--saida", str(saida)],
                                 AGORA, Servidor())
            self.assertEqual(codigo, 0)
            self.assertEqual(list(saida.iterdir()), [], "regravou o que não mudou")
            self.assertIn("mudou=false", saidas.read_text())

    def test_main_leitura_nova_escreve_json_e_bruto(self):
        with tempfile.TemporaryDirectory() as tmp:
            saida = Path(tmp) / "saida"
            codigo = ga.main(["--anterior", str(Path(tmp) / "nao-existe.json"),
                              "--saida", str(saida)], AGORA, Servidor())
            self.assertEqual(codigo, 0)
            self.assertEqual((saida / ga.ARQUIVO_BRUTO).read_bytes(), HTML_REAL)
            corpo = json.loads((saida / ga.ARQUIVO_LEITURA).read_text(encoding="utf-8"))
            self.assertEqual(corpo["leitura"]["nivel_m"], 1.84)

    def test_anterior_corrompido_conta_como_sem_anterior(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "a.json"
            p.write_text("{")
            self.assertIsNone(ga.ler_anterior(p))


class LeituraVelha(unittest.TestCase):
    TARDE = datetime(2026, 9, 28, 3, 32, tzinfo=timezone.utc)  # a hora real da captura

    def test_velha_e_avisada_sem_falhar_e_sem_renovar(self):
        r = ga.coletar(None, self.TARDE, Servidor())
        self.assertTrue(r["avisos"])
        self.assertIn("leitura velha", r["avisos"][0])
        self.assertIn("parou de atualizar, não a coleta", r["avisos"][0])
        self.assertEqual(r["corpo"]["leitura"]["medido_em"], "2026-09-27T19:28:00")

    def test_main_marca_o_estado_e_sai_zero(self):
        with tempfile.TemporaryDirectory() as tmp:
            saidas = Path(tmp) / "out"
            with mock.patch.dict(os.environ, {"GITHUB_OUTPUT": str(saidas)}):
                codigo = ga.main(["--saida", str(Path(tmp) / "s")], self.TARDE, Servidor())
            self.assertEqual(codigo, 0)
            self.assertIn("estado=leitura_velha", saidas.read_text())

    def test_a_VPS_recusa_a_velha(self):
        corpo = ga.coletar(None, self.TARDE, Servidor())["corpo"]
        self.assertIsNone(ga.validar(corpo, self.TARDE))


class Falhas(unittest.TestCase):
    def test_timeout_vira_falha_registrada(self):
        import requests

        with mock.patch("requests.get", side_effect=requests.ConnectTimeout("estourou")), \
                mock.patch.object(ga, "espera_turno"):
            with self.assertRaises(ga.Falha) as ctx:
                ga.pedir_http(ga.URL)
        self.assertEqual(ctx.exception.codigo, "timeout")

    def test_main_com_timeout_sai_1_e_deixa_diagnostico(self):
        s = Servidor(pagina=ga.Falha("timeout", "timeout ao pedir a estação 21"))
        with tempfile.TemporaryDirectory() as tmp:
            saida, saidas = Path(tmp) / "saida", Path(tmp) / "out"
            with mock.patch.dict(os.environ, {"GITHUB_OUTPUT": str(saidas)}):
                codigo = ga.main(["--saida", str(saida)], AGORA, s)
            self.assertEqual(codigo, 1, "timeout tem de reprovar o job")
            falha = json.loads((saida / "falha.json").read_text(encoding="utf-8"))
            self.assertEqual(falha["codigo"], "timeout")
            self.assertFalse((saida / ga.ARQUIVO_LEITURA).exists(), "publicou sem leitura")
            texto = saidas.read_text()
            self.assertIn("estado=timeout", texto)
            self.assertIn("mudou=false", texto)

    def test_http_500_guarda_o_corpo_para_o_artefato(self):
        with tempfile.TemporaryDirectory() as tmp:
            saida = Path(tmp)
            codigo = ga.main(["--saida", str(saida)], AGORA,
                             Servidor(pagina=(500, b"erro interno")))
            self.assertEqual(codigo, 1)
            self.assertEqual((saida / f"falha-{ga.ARQUIVO_BRUTO}").read_bytes(), b"erro interno")

    def test_pedido_leva_o_user_agent_do_projeto_e_timeout(self):
        resposta = mock.Mock(status_code=200, content=b"ok")
        with mock.patch("requests.get", return_value=resposta) as get, \
                mock.patch.object(ga, "espera_turno") as turno:
            self.assertEqual(ga.pedir_http(ga.URL), (200, b"ok"))
        self.assertEqual(get.call_args.kwargs["headers"]["User-Agent"], USER_AGENT)
        self.assertEqual(get.call_args.kwargs["timeout"], ga.TIMEOUT_S)
        turno.assert_called_once()


class NaVPS(unittest.TestCase):
    def corpo(self):
        return ga.coletar(None, AGORA, Servidor())["corpo"]

    def test_aceita_o_publicado_mesmo_com_consulta_antiga(self):
        """O arquivo não é regravado sem mudança: a consulta envelhece, a medição decide."""
        tarde = datetime(2026, 9, 27, 23, 50, tzinfo=timezone.utc)  # 2h22 depois da medição
        self.assertEqual(ga.validar(self.corpo(), tarde)["nivel_m"], 1.84)

    def test_recusa_corpo_que_nao_veio_do_actions(self):
        c = self.corpo()
        del c["coletor"]
        self.assertIsNone(ga.validar(c, AGORA))
        self.assertIsNone(ga.validar("lixo", AGORA))

    def test_ler_publicado_nunca_derruba_a_coleta(self):
        def explode(_url):
            raise RuntimeError("404 branch inexistente")

        self.assertIsNone(ga.ler_publicado(explode, AGORA))
        self.assertIsNone(ga.ler_publicado(lambda _u: "{", AGORA))
        self.assertEqual(ga.ler_publicado(lambda _u: json.dumps(self.corpo()), AGORA)["nivel_m"], 1.84)

    def test_coleta_niveis_fica_com_a_medicao_mais_recente(self):
        do_actions = ga.validar(self.corpo(), AGORA)
        do_pc = {**do_actions, "nivel_m": 1.80, "medido_em": "2026-09-27T18:00:00"}
        with mock.patch("gaspar_pc.ler", return_value=do_pc), \
                mock.patch("gaspar_actions.ler_publicado", return_value=do_actions), \
                mock.patch("coleta_gaspar.permitido") as rede:
            self.assertEqual(coleta_niveis.baixar_nivel_gaspar(False), [do_actions])
            rede.assert_not_called()


if __name__ == "__main__":
    unittest.main(verbosity=2)
