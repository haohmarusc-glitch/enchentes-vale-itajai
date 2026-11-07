#!/usr/bin/env python3
"""Testes do coletor de avisos da Defesa Civil de SC (`coleta_avisos_dcsc.py`). Sem rede: o que se testa é a
leitura do JSON do WordPress, as regiões citadas, o fuso e o `--publicar` que apaga o arquivo quando falha."""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))

import coleta_avisos_dcsc as ca  # noqa: E402


def post(id_, titulo, corpo, cats=(7,), date_gmt="2026-11-04T12:41:00"):
    return {"id": id_, "date": "2026-11-04T09:41:00", "date_gmt": date_gmt,
            "link": f"https://www.defesacivil.sc.gov.br/?p={id_}",
            "title": {"rendered": titulo}, "content": {"rendered": corpo}, "categories": list(cats)}


POSTS = [
    post(39521, "ATEN&#199;&#195;O &#8211; 04/11 09:34 &#8211; TEMPORAIS",
         "<p>Para as pr&oacute;ximas 4 horas: pancadas de chuva com <strong>temporais</strong> no Extremo Oeste, "
         "Oeste e Meio-Oeste. Risco de alagamentos.</p>", cats=(7,)),
    post(39500, "AVISO – 03/11 – CHUVA PERSISTENTE",
         "<p>Chuva volumosa no Vale do Itajaí, Litoral Norte e Grande Florianópolis até quarta.</p>", cats=(6, 1),
         date_gmt="2026-11-03T18:00:00"),
    post(39400, "Monitoramento Meteorológico DC/SC 03/11 10:00", "<p>Vale do Itajaí: tempo firme.</p>", cats=(23,)),
    post(39300, "ALERTA – 01/11 – VENDAVAL", "<p>Ventos fortes em todo o Estado.</p>", cats=(7,),
         date_gmt="2026-11-01T22:30:00"),
]


class Texto(unittest.TestCase):
    def test_tags_e_entidades(self):
        self.assertEqual(ca.texto_de("<p>Para as pr&oacute;ximas  4 horas:<br/> <b>temporais</b></p>"),
                         "Para as próximas 4 horas: temporais")
        self.assertEqual(ca.texto_de(None), "")


class Regioes(unittest.TestCase):
    def test_na_ordem_da_mencao_e_sem_casar_dentro_de_outra(self):
        regioes, estado = ca.regioes_citadas("temporais no Extremo Oeste, Oeste e Meio-Oeste; nada no Litoral Norte")
        self.assertEqual(regioes, ["Extremo Oeste", "Oeste", "Meio-Oeste", "Litoral Norte"])
        self.assertFalse(estado)

    def test_oeste_sozinho_nao_vem_de_extremo_oeste(self):
        regioes, _ = ca.regioes_citadas("chuva no Extremo Oeste e no Planalto Norte")
        self.assertEqual(regioes, ["Extremo Oeste", "Planalto Norte"])

    def test_bacia_e_estado_inteiro(self):
        regioes, estado = ca.regioes_citadas("Ventos fortes em todo o Estado")
        self.assertEqual((regioes, estado), ([], True))
        regioes, _ = ca.regioes_citadas("Foz do Rio Itajaí e Alto Vale em atenção")
        self.assertEqual(regioes, ["Foz do Itajaí", "Alto Vale"])

    def test_sem_acento_e_caixa(self):
        self.assertEqual(ca.regioes_citadas("VALE DO ITAJAI e Meio Oeste")[0], ["Vale do Itajaí", "Meio-Oeste"])


class Converter(unittest.TestCase):
    def test_so_aviso_e_alerta_do_mais_novo_ao_mais_antigo(self):
        avisos = ca.converter(POSTS)
        self.assertEqual([a["id"] for a in avisos], [39521, 39500, 39300], "Monitoramento (23) fica de fora")
        self.assertEqual([a["categoria"] for a in avisos], ["Alerta", "Aviso", "Alerta"])

    def test_campos_do_aviso(self):
        a = ca.converter(POSTS)[0]
        self.assertEqual(a["titulo"], "ATENÇÃO – 04/11 09:34 – TEMPORAIS")
        self.assertEqual(a["publicado_em"], "2026-11-04T09:41:00", "date_gmt em Brasília, sem fuso (CLAUDE.md)")
        self.assertEqual(a["publicado_em_utc"], "2026-11-04T12:41:00")
        self.assertEqual(a["regioes"], ["Extremo Oeste", "Oeste", "Meio-Oeste"])
        self.assertFalse(a["inclui_bacia"])
        self.assertIn("temporais", a["trecho"])
        self.assertNotIn("<", a["trecho"])

    def test_inclui_bacia(self):
        por_id = {a["id"]: a for a in ca.converter(POSTS)}
        self.assertTrue(por_id[39500]["inclui_bacia"], "Vale do Itajaí e Litoral Norte")
        self.assertTrue(por_id[39300]["inclui_bacia"], "todo o Estado inclui a bacia")
        self.assertTrue(por_id[39300]["estado_inteiro"])

    def test_lixo_nao_quebra(self):
        self.assertEqual(ca.converter([None, {"id": 1}, {"id": 2, "categories": [7], "title": "x", "content": None}])[0]["titulo"], "x")


class Publicar(unittest.TestCase):
    def test_grava_e_apaga_na_falha(self):
        with tempfile.TemporaryDirectory() as d:
            with mock.patch.object(ca, "DADOS", Path(d)), mock.patch("comum.DADOS", Path(d)), mock.patch("sys.stdout"):
                (Path(d) / "tempo-real").mkdir()
                self.assertEqual(ca.publicar(buscador=lambda: POSTS), 0)
                saida = json.loads((Path(d) / ca.ARQUIVO_PUBLICAVEL).read_text(encoding="utf-8"))
                self.assertEqual(saida["versao"], 1)
                self.assertEqual(len(saida["avisos"]), 3)
                self.assertTrue(saida["gerado_em"].endswith("+00:00"), "gerado_em em UTC, como o publicador exige")
                self.assertIn("Defesa Civil de Santa Catarina", saida["fonte"])

                def explode():
                    raise RuntimeError("503")
                with mock.patch("sys.stderr"):
                    self.assertEqual(ca.publicar(buscador=explode), 1)
                self.assertFalse((Path(d) / ca.ARQUIVO_PUBLICAVEL).exists(), "arquivo de outra coleta não passa por atual")

    def test_url_pede_so_as_categorias_de_aviso(self):
        self.assertIn("categories=7,6", ca.URL)
        self.assertIn("_fields=id,date,date_gmt,link,title,content,categories", ca.URL)
        self.assertTrue(ca.URL.startswith("https://www.defesacivil.sc.gov.br/wp-json/wp/v2/posts"))

    def test_cabe_no_corte_de_60_s_da_publicacao(self):
        """publicar_tempo_real.sh mata o coletor em 60 s: tentativas × espera tem de caber, com folga."""
        corte = 60
        sh = (Path(__file__).parent / "publicar_tempo_real.sh").read_text(encoding="utf-8")
        self.assertIn(f"timeout {corte} python3 scripts/coleta_avisos_dcsc.py", sh)
        self.assertLessEqual(ca.TENTATIVAS * ca.TIMEOUT_S, corte - 5)

    def test_buscar_usa_uma_tentativa_e_o_timeout_proprio(self):
        pedidos = []

        def falso(url, *, tentativas, timeout):
            pedidos.append((tentativas, timeout))
            return "[]"

        with mock.patch.object(ca, "baixar", falso):
            self.assertEqual(ca.buscar(), [])
        self.assertEqual(pedidos, [(ca.TENTATIVAS, ca.TIMEOUT_S)])


if __name__ == "__main__":
    unittest.main()
