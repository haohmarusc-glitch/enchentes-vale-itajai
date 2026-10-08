#!/usr/bin/env python3
"""
Testes da coleta do Centro de Ituporanga pelo GitHub Actions (08/10/2026).

O que eles travam, em ordem de estrago:
* robots.txt que recusa, ou responde 403 como faz à VPS → a página NÃO é pedida;
* timeout e erro HTTP → falha registrada (código, motivo, artefato), nunca silêncio nem arquivo publicado;
* leitura igual à anterior → nada regravado (duas leituras por dia, não 48 commits);
* leitura velha → avisada, nunca renovada;
* a VPS só aceita o publicado deste coletor, com a página lida há ≤ 3 h e `medido_em` sem fuso;
* `coleta_ituporanga.publicar` cai para o Actions quando a página recusa, e diz isso em `via`.

Sem rede: o HTML é o recorte real de 08/10/2026 07:00 (2,04 m, "Alerta") usado em teste_coleta_ituporanga.py.
"""
import json
import os
import sys
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import coleta_ituporanga as ci
import ituporanga_actions as ia
from teste_coleta_ituporanga import PAGINA

for _var in ("GITHUB_OUTPUT", "GITHUB_STEP_SUMMARY"):
    os.environ.pop(_var, None)

HTML = PAGINA.encode("utf-8")
#: 08/10/2026 09:46 em Brasília = 12:46 UTC: 2 h 46 depois da leitura das 07:00.
AGORA = datetime(2026, 10, 8, 12, 46, tzinfo=timezone.utc)
ROBOTS_LIBERA = b"User-agent: *\nAllow: /\n"
ROBOTS_RECUSA = b"User-agent: *\nDisallow: /nivel-rio\n"


class Servidor:
    """Finge a Prefeitura: registra cada URL pedida e responde do roteiro."""

    def __init__(self, robots=(200, ROBOTS_LIBERA), pagina=(200, HTML)):
        self.roteiro = {ia.ROBOTS: robots, ia.URL: pagina}
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
        with self.assertRaises(ia.Falha) as ctx:
            ia.coletar(None, AGORA, s)
        self.assertEqual(ctx.exception.codigo, "robots")
        self.assertEqual(s.pedidas, [ia.ROBOTS])

    def test_403_no_robots_como_a_vps_recebe_NAO_baixa_a_pagina(self):
        s = Servidor(robots=(403, b"Forbidden"))
        with self.assertRaises(ia.Falha) as ctx:
            ia.coletar(None, AGORA, s)
        self.assertEqual(ctx.exception.codigo, "robots")
        self.assertIn("403", ctx.exception.motivo)
        self.assertEqual(s.pedidas, [ia.ROBOTS])

    def test_sem_robots_404_segue(self):
        r = ia.coletar(None, AGORA, Servidor(robots=(404, b"")))
        self.assertEqual(r["estado"], "nova")


class Coleta(unittest.TestCase):
    def test_leitura_nova_vira_corpo_com_dados_e_hora_da_pagina(self):
        s = Servidor()
        r = ia.coletar(None, AGORA, s)
        self.assertEqual(s.pedidas, [ia.ROBOTS, ia.URL])
        self.assertTrue(r["mudou"])
        c = r["corpo"]
        self.assertEqual(c["coletor"], "github-actions")
        self.assertEqual(c["dados"]["nivel_m"], 2.04)
        self.assertEqual(c["dados"]["medido_em"], "2026-10-08T07:00:00")
        self.assertEqual(c["dados"]["criticidade_na_fonte"], "Alerta")
        self.assertEqual(c["pagina_lida_em"], "2026-10-08T12:46:00+00:00")
        self.assertEqual(c["bruto"]["bytes"], len(HTML))
        self.assertEqual(r["avisos"], [])

    def test_mesma_leitura_nao_regrava(self):
        anterior = ia.coletar(None, AGORA, Servidor())["corpo"]
        r = ia.coletar(anterior, AGORA, Servidor())
        self.assertEqual(r["estado"], "sem_mudanca")
        self.assertFalse(r["mudou"])
        self.assertIsNone(r["corpo"])

    def test_http_fora_de_200_e_falha_com_bruto(self):
        with self.assertRaises(ia.Falha) as ctx:
            ia.coletar(None, AGORA, Servidor(pagina=(503, b"manutencao")))
        self.assertEqual(ctx.exception.codigo, "http")
        self.assertEqual(ctx.exception.bruto, b"manutencao")

    def test_pagina_sem_leitura_e_falha(self):
        with self.assertRaises(ia.Falha) as ctx:
            ia.coletar(None, AGORA, Servidor(pagina=(200, b"<html>em manutencao</html>")))
        self.assertEqual(ctx.exception.codigo, "sem_leitura")

    def test_leitura_velha_avisa_e_nao_e_falha(self):
        depois = datetime(2026, 10, 9, 5, 0, tzinfo=timezone.utc)   # 19 h depois da leitura
        r = ia.coletar(None, depois, Servidor())
        self.assertTrue(r["mudou"])
        self.assertTrue(any("leitura velha" in a for a in r["avisos"]))

    def test_medicao_no_futuro_e_falha(self):
        antes = datetime(2026, 10, 8, 9, 0, tzinfo=timezone.utc)   # 06:00 em Brasília, 1 h antes da leitura
        with self.assertRaises(ia.Falha) as ctx:
            ia.coletar(None, antes, Servidor())
        self.assertEqual(ctx.exception.codigo, "futuro")


class LinhaDeComando(unittest.TestCase):
    def test_grava_json_e_bruto_e_escreve_as_saidas_do_passo(self):
        with tempfile.TemporaryDirectory() as tmp:
            saida = Path(tmp) / "saida"
            out = Path(tmp) / "out.txt"
            os.environ["GITHUB_OUTPUT"] = str(out)
            try:
                self.assertEqual(ia.main(["--saida", str(saida)], AGORA, Servidor()), 0)
            finally:
                os.environ.pop("GITHUB_OUTPUT", None)
            corpo = json.loads((saida / ia.ARQUIVO_LEITURA).read_text(encoding="utf-8"))
            self.assertEqual(corpo["dados"]["nivel_m"], 2.04)
            self.assertEqual((saida / ia.ARQUIVO_BRUTO).read_bytes(), HTML)
            self.assertIn("mudou=true", out.read_text(encoding="utf-8"))
            # Segunda rodada com o anterior igual: nada regravado.
            saida2 = Path(tmp) / "saida2"
            self.assertEqual(ia.main(["--anterior", str(saida / ia.ARQUIVO_LEITURA), "--saida", str(saida2)],
                                     AGORA, Servidor()), 0)
            self.assertFalse((saida2 / ia.ARQUIVO_LEITURA).exists())

    def test_falha_grava_diagnostico_e_sai_1(self):
        with tempfile.TemporaryDirectory() as tmp:
            saida = Path(tmp) / "saida"
            self.assertEqual(ia.main(["--saida", str(saida)], AGORA, Servidor(robots=(403, b""))), 1)
            falha = json.loads((saida / "falha.json").read_text(encoding="utf-8"))
            self.assertEqual(falha["codigo"], "robots")
            self.assertFalse((saida / ia.ARQUIVO_LEITURA).exists())


class LeituraNaVps(unittest.TestCase):
    def corpo(self, **mudancas):
        c = ia.coletar(None, AGORA, Servidor())["corpo"]
        c.update(mudancas)
        return c

    def test_aceita_o_publicado_deste_coletor_lido_ha_pouco(self):
        v = ia.validar(self.corpo(), AGORA)
        self.assertEqual(v["dados"]["nivel_m"], 2.04)
        self.assertEqual(v["pagina_lida_em"], "2026-10-08T12:46:00+00:00")

    def test_recusa_outro_coletor_pagina_velha_e_medido_em_com_fuso(self):
        self.assertIsNone(ia.validar(self.corpo(coletor="vps"), AGORA))
        self.assertIsNone(ia.validar(self.corpo(), datetime(2026, 10, 8, 16, 0, tzinfo=timezone.utc)),
                          "página lida há mais de 3 h não serve")
        c = self.corpo()
        c["dados"]["medido_em"] = "2026-10-08T07:00:00-03:00"
        self.assertIsNone(ia.validar(c, AGORA), "medido_em com fuso quebra o contrato")
        c = self.corpo()
        c["dados"]["nivel_m"] = 204.0
        self.assertIsNone(ia.validar(c, AGORA), "204 m não é nível de rio")
        self.assertIsNone(ia.validar("não é dict", AGORA))

    def test_ler_publicado_devolve_none_em_qualquer_falha(self):
        def cai(url):
            raise OSError("sem rede")
        self.assertIsNone(ia.ler_publicado(buscar=cai, agora=AGORA))
        self.assertIsNone(ia.ler_publicado(buscar=lambda url: "não é json", agora=AGORA))
        bom = json.dumps(self.corpo())
        self.assertEqual(ia.ler_publicado(buscar=lambda url: bom, agora=AGORA)["dados"]["nivel_m"], 2.04)


class PublicarNaVps(unittest.TestCase):
    """`coleta_ituporanga.publicar`: página primeiro; recusada, o publicado pelo Actions; nada, apaga."""

    AGORA_BRASILIA = datetime(2026, 10, 8, 9, 46)

    def test_pagina_recusada_cai_para_o_actions_e_diz_isso_em_via(self):
        publicado = ia.validar(ia.coletar(None, AGORA, Servidor())["corpo"], AGORA)

        def recusa():
            raise RuntimeError("403 Client Error: Forbidden for url: .../robots.txt")

        with tempfile.TemporaryDirectory() as tmp:
            raiz = Path(tmp)
            self.assertEqual(ci.publicar(self.AGORA_BRASILIA, buscador=recusa, raiz=raiz, publicado=lambda: publicado), 0)
            d = json.loads((raiz / ci.ARQUIVO_PUBLICAVEL).read_text(encoding="utf-8"))
            self.assertEqual(d["ultima_leitura"]["nivel_m"], 2.04)
            self.assertEqual(d["ultima_leitura"]["medido_em"], "2026-10-08T07:00:00")
            self.assertEqual(d["via"], {"coletor": "github-actions", "pagina_lida_em": "2026-10-08T12:46:00+00:00"})
            self.assertTrue(d["gerado_em"].endswith("+00:00"))
            self.assertEqual(d["situacao"], "fresca")

    def test_pagina_direta_vence_e_via_e_vps(self):
        with tempfile.TemporaryDirectory() as tmp:
            raiz = Path(tmp)
            chamou = []
            self.assertEqual(ci.publicar(self.AGORA_BRASILIA, buscador=lambda: PAGINA, raiz=raiz,
                                         publicado=lambda: chamou.append(1)), 0)
            d = json.loads((raiz / ci.ARQUIVO_PUBLICAVEL).read_text(encoding="utf-8"))
            self.assertEqual(d["via"]["coletor"], "vps")
            self.assertEqual(chamou, [], "com a página aberta, o Actions não é consultado")

    def test_sem_pagina_e_sem_actions_apaga_o_anterior(self):
        def recusa():
            raise RuntimeError("403")

        with tempfile.TemporaryDirectory() as tmp:
            raiz = Path(tmp)
            self.assertEqual(ci.publicar(self.AGORA_BRASILIA, buscador=lambda: PAGINA, raiz=raiz, publicado=lambda: None), 0)
            self.assertEqual(ci.publicar(self.AGORA_BRASILIA, buscador=recusa, raiz=raiz, publicado=lambda: None), 1)
            self.assertFalse((raiz / ci.ARQUIVO_PUBLICAVEL).exists())


if __name__ == "__main__":
    unittest.main()
