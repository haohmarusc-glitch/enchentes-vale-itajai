#!/usr/bin/env python3
"""Testes da captura bruta das fontes municipais (`capturar_fontes.py`).

O que não pode falhar:

* **robots.txt manda.** Caminho recusado não é pedido — nem uma vez.
* **Uma fonte fora do ar não derruba as outras.** A falha vira linha no
  manifesto, com o motivo, e a captura segue.
* **O caminho de volta só grava o que confere.** Fatia faltando ou sha256
  diferente não viram arquivo em data/brutos/.
* **Os alvos são os dos coletores.** A lista não pode divergir, em silêncio,
  do que os coletores de fato leem.
* **TLS nunca é desligado.**

    python3 scripts/teste_capturar_fontes.py
"""

import tempfile
import unittest
from pathlib import Path

import capturar_fontes as cf
from capturar_fontes import ALVOS, Alvo, capturar, fatias, remontar


class Servidor:
    """Um servidor de mentira: {url: (status, corpo)}; registra o que foi pedido."""

    def __init__(self, respostas):
        self.respostas = respostas
        self.pedidos = []

    def __call__(self, url, _ca):
        self.pedidos.append(url)
        status, corpo = self.respostas.get(url, (404, b"nao existe"))
        return status, corpo, "text/plain"


class TestRobots(unittest.TestCase):
    def test_caminho_recusado_nao_e_pedido(self):
        srv = Servidor({"https://x.test/robots.txt": (200, b"User-agent: *\nDisallow: /privado\n")})
        alvos = [Alvo("a.html", "x", "https://x.test/privado/pagina")]
        with tempfile.TemporaryDirectory() as d:
            linhas = capturar(alvos, Path(d), pedir=srv)
        self.assertEqual(linhas[0]["estado"], "recusado_robots")
        self.assertNotIn("https://x.test/privado/pagina", srv.pedidos)

    def test_robots_ausente_nao_proibe(self):
        """404 no robots.txt é "sem regras" pela norma."""
        srv = Servidor({"https://x.test/pagina": (200, b"ok")})
        with tempfile.TemporaryDirectory() as d:
            linhas = capturar([Alvo("a.html", "x", "https://x.test/pagina")], Path(d), pedir=srv)
            self.assertEqual(linhas[0]["estado"], "ok")
            self.assertEqual((Path(d) / "a.html").read_bytes(), b"ok")

    def test_robots_pedido_uma_vez_por_host(self):
        srv = Servidor({"https://x.test/a": (200, b"1"), "https://x.test/b": (200, b"2")})
        alvos = [Alvo("a", "x", "https://x.test/a"), Alvo("b", "x", "https://x.test/b")]
        with tempfile.TemporaryDirectory() as d:
            capturar(alvos, Path(d), pedir=srv)
        self.assertEqual(srv.pedidos.count("https://x.test/robots.txt"), 1)

    def test_a_consulta_entra_na_regra(self):
        """`?municipio_id=2` é parte do caminho que o robots.txt pode recusar."""
        self.assertEqual(cf.caminho_com_consulta("https://h/rios?municipio_id=2"), "/rios?municipio_id=2")
        self.assertEqual(cf.caminho_com_consulta("https://h"), "/")


class TestFalhaNaoDerrubaAsOutras(unittest.TestCase):
    def test_transporte_quebrado_vira_linha_e_segue(self):
        def pedir(url, _ca):
            if url == "https://fora.test/p":
                return 0, b"ConnectTimeout: 45 s", ""
            return (200, b"corpo", "text/html") if url.endswith("/q") else (404, b"", "")
        alvos = [Alvo("p", "a", "https://fora.test/p"), Alvo("q", "b", "https://ok.test/q")]
        with tempfile.TemporaryDirectory() as d:
            linhas = capturar(alvos, Path(d), pedir=pedir)
        self.assertEqual([l["estado"] for l in linhas], ["falha_transporte", "ok"])
        self.assertIn("ConnectTimeout", linhas[0]["motivo"])
        self.assertIsNone(linhas[0]["sha256"])

    def test_http_de_erro_e_guardado_e_marcado(self):
        """Um 403 é evidência também: o corpo guarda o motivo que o servidor deu."""
        srv = Servidor({"https://x.test/p": (403, b"bloqueado")})
        with tempfile.TemporaryDirectory() as d:
            linhas = capturar([Alvo("p", "x", "https://x.test/p")], Path(d), pedir=srv)
        self.assertEqual((linhas[0]["estado"], linhas[0]["http"]), ("http_nao_200", 403))


class TestCaminhoDeVolta(unittest.TestCase):
    CORPO = ("<html>" + "nível 1,42 m · " * 900 + "</html>").encode("utf-8")

    def test_ida_e_volta_confere(self):
        log = "\n".join(["ruído", *fatias("a.html", self.CORPO, largura=200), "fim"])
        with tempfile.TemporaryDirectory() as d:
            self.assertEqual(remontar(log, Path(d)), {"a.html": "confere"})
            self.assertEqual((Path(d) / "a.html").read_bytes(), self.CORPO)

    def test_fatia_faltando_nao_grava(self):
        linhas = fatias("a.html", self.CORPO, largura=50)
        self.assertGreater(len(linhas), 2)
        with tempfile.TemporaryDirectory() as d:
            r = remontar("\n".join(linhas[:1] + linhas[2:]), Path(d))
            self.assertIn("faltam fatias [2]", r["a.html"])
            self.assertFalse((Path(d) / "a.html").exists())

    def test_sha_diferente_nao_grava(self):
        adulterado = [l.replace(l.split()[2], "0" * 64) for l in fatias("a.html", self.CORPO)]
        with tempfile.TemporaryDirectory() as d:
            self.assertEqual(remontar("\n".join(adulterado), Path(d)), {"a.html": "sha256 não confere"})
            self.assertFalse((Path(d) / "a.html").exists())

    def test_fatia_nao_passa_da_largura(self):
        for l in fatias("a.html", self.CORPO):
            self.assertLessEqual(len(l.split(" ", 4)[4]), cf.LARGURA_FATIA)


class TestAlvos(unittest.TestCase):
    def test_todo_alvo_tem_origem(self):
        """Cada alvo é URL de coletor OU fonte que o cadastro declara para a
        MESMA cidade em `fontes_tempo_real`. Nada entra por palpite."""
        import json
        import re
        cadastro = json.loads((Path(cf.__file__).resolve().parent.parent
                               / "data" / "estacoes.json").read_text(encoding="utf-8"))
        declaradas = set()
        for rio in cadastro["rios"].values():
            for c in rio["cidades"]:
                for f in c.get("fontes_tempo_real") or []:
                    m = re.search(r"https?://\S+", f if isinstance(f, str) else json.dumps(f))
                    if m:
                        declaradas.add((c["id"], m.group(0)))
        sem_coletor = {(a.cidade, a.url) for a in ALVOS} - {
            (a.cidade, a.url) for a in ALVOS if a.url.split("?municipio_id=")[0] in self._dos_coletores()}
        self.assertEqual(sem_coletor - declaradas, set())
        self.assertEqual(sem_coletor, {("ituporanga", "https://www.ituporanga.sc.gov.br/nivel-rio")})

    @staticmethod
    def _dos_coletores():
        import coleta_alertablu
        import coleta_asthon
        import coleta_barragens
        import coleta_gaspar
        import coleta_indaial
        import coleta_itajai_portal
        import coleta_taio
        return {
            coleta_itajai_portal.URL,
            coleta_taio.URL_CARDS, coleta_taio.URL_HISTORICO,
            coleta_asthon.URL_PAINEL, coleta_barragens.URL,
            coleta_gaspar.URL, coleta_gaspar.URL_ESTACAO,
            coleta_alertablu.URL, coleta_indaial.URL,
        }

    def test_toda_url_de_coletor_esta_na_captura(self):
        """E o caminho inverso: nenhum coletor municipal fica de fora. Se um
        coletor mudar de endereço, a captura tem que mudar junto."""
        urls = {a.url.split("?municipio_id=")[0] for a in ALVOS}
        self.assertEqual(self._dos_coletores() - urls, set())

    def test_nomes_de_arquivo_unicos(self):
        nomes = [a.arquivo for a in ALVOS]
        self.assertEqual(len(nomes), len(set(nomes)))

    def test_os_quatro_municipios_do_portal(self):
        portal = [a for a in ALVOS if a.url.startswith(cf.PORTAL_ITAJAI)]
        self.assertEqual(len(portal), 4)

    def test_intermediario_do_alertablu_existe(self):
        a = next(a for a in ALVOS if "blumenau.sc.gov.br" in a.url)
        self.assertTrue(a.ca_extra and a.ca_extra.exists())


CAPTURA_28_09 = Path(cf.__file__).resolve().parent.parent / "data" / "brutos" / "captura-fontes-2026-09-28"


class TestCapturaDe28DeSetembro(unittest.TestCase):
    """A primeira captura das fontes das cidades (run 36374094642, 03h32 UTC).
    Cada corpo passa pelo coletor DELE: se a fonte mudar de formato, o teste
    aponta qual coletor deixou de ler o que o servidor entrega."""

    @staticmethod
    def ler(nome):
        return (CAPTURA_28_09 / nome).read_text(encoding="utf-8")

    def test_manifesto_bate_com_os_arquivos(self):
        import hashlib
        import json
        man = json.loads(self.ler("manifesto.json"))
        ok = [a for a in man["alvos"] if a["estado"] == "ok"]
        self.assertEqual(len(ok), 12)
        for a in ok:
            corpo = (CAPTURA_28_09 / a["arquivo"]).read_bytes()
            self.assertEqual(hashlib.sha256(corpo).hexdigest(), a["sha256"], a["arquivo"])

    def test_indaial_foi_recusado_pelo_robots_e_nao_pedido(self):
        import json
        man = json.loads(self.ler("manifesto.json"))
        indaial = [a for a in man["alvos"] if a["cidade"] == "indaial"]
        self.assertEqual([a["estado"] for a in indaial], ["recusado_robots"])
        self.assertFalse(any("indaial" in p.name for p in CAPTURA_28_09.iterdir()))

    def test_taio_le_o_centro_e_a_barragem(self):
        import json
        import coleta_taio
        r = coleta_taio.parse(json.loads(self.ler("taio-uniparking-cards.json")))
        self.assertEqual([(l["nivel_m"], l["medido_em"]) for l in r["leituras"]],
                         [(5.24, "2026-09-28T00:31:04")])
        self.assertEqual(r["barragem"]["comportas"]["abertas"], 7)
        self.assertEqual(len(coleta_taio.parse_historico(
            json.loads(self.ler("taio-uniparking-historico.json")))), 24)

    def test_rio_do_sul_le_a_ponte_dom_tito_buss(self):
        import json
        import coleta_asthon
        r = coleta_asthon.parse(json.loads(self.ler("rio-do-sul-asthon-panel.json")))
        self.assertEqual([(l["cidade"], l["nivel_m"]) for l in r], [("rio-do-sul", 5.19)])

    def test_alertablu_le_blumenau(self):
        import json
        import coleta_alertablu
        r = coleta_alertablu.parse(json.loads(self.ler("blumenau-alertablu-nivel-oficial.json")))
        self.assertEqual([(l["cidade"], l["nivel_m"], l["medido_em"]) for l in r],
                         [("blumenau", 3.2, "2026-09-28T00:00:00")])

    def test_gaspar_responde_fora_da_vps_e_o_coletor_le(self):
        """O host de Gaspar dá timeout na VPS desde 31/08; do runner do
        GitHub respondeu 200 às duas páginas, com robots.txt permitindo."""
        import coleta_gaspar
        estacao = coleta_gaspar.analisar_estacao(self.ler("gaspar-estacao-21.html"))
        self.assertEqual([(e["rotulo"], e["nivel_m"], e["medido_em_iso"]) for e in estacao["estacoes"]],
                         [("Rio Itajaí Açu Gaspar", 1.84, "2026-09-27T19:28:00")])
        tabela = coleta_gaspar.analisar(self.ler("gaspar-monitoramento-tabela.html"))
        rio = [e for e in tabela["estacoes"] if e["rotulo"] == "Rio Itajaí Açu Gaspar"]
        self.assertEqual([(e["nivel_m"], e["medido_em_iso"]) for e in rio], [(1.84, "2026-09-27T19:28:00")])

    def test_portal_de_itajai_segue_com_as_onze(self):
        from coleta_itajai_portal import parse
        self.assertEqual(len(parse(self.ler("itajai-portal-rios-municipio-1-itajai.html"))), 11)


class TestSemAtalhos(unittest.TestCase):
    def test_tls_nunca_desligado(self):
        fonte = Path(cf.__file__).read_text(encoding="utf-8")
        self.assertNotIn("verify=False", fonte.replace("Nunca `verify=False`", ""))

    def test_user_agent_do_projeto(self):
        fonte = Path(cf.__file__).read_text(encoding="utf-8")
        self.assertIn('headers={"User-Agent": USER_AGENT}', fonte)
        self.assertNotIn("Mozilla", fonte)


if __name__ == "__main__":
    unittest.main(verbosity=2)
