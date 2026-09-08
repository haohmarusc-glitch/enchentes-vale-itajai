"""A sonda do histórico de Brusque: o que ela pode e não pode fazer, travado.

O endpoint veio da leitura do formulário pelo Jefferson (08/09/2026), sem
disparar nada. O formato da resposta é desconhecido — e é por isso que ela é
sonda: a série da ANA ensinou no mesmo dia que o formato decide tudo.
"""

from __future__ import annotations

import contextlib
import io
import sys
import unittest
from pathlib import Path

import sonda_brusque_historico as sonda

FONTE = (Path(__file__).resolve().parent / "sonda_brusque_historico.py").read_text(encoding="utf-8")


class _Resposta:
    def __init__(self, status: int, texto: str = ""):
        self.status_code = status
        self.text = texto
        self.content = texto.encode()
        self.headers = {}
        self.history = []


class _Sessao:
    def __init__(self, resposta=None, erro=None):
        self.resposta, self.erro = resposta, erro

    def get(self, url, timeout=None):
        if self.erro:
            raise self.erro
        return self.resposta


class ORobotsEhPorteiro(unittest.TestCase):
    """Foi por robots que o AlertaBlu ficou de fora. Mesma régua aqui."""

    def test_sem_robots_e_liberado(self):
        self.assertTrue(sonda.permitido(_Sessao(_Resposta(404))))

    def test_erro_de_rede_NAO_e_liberado(self):
        """Não saber é motivo para não baixar."""
        import requests
        with contextlib.redirect_stderr(io.StringIO()):
            self.assertFalse(sonda.permitido(_Sessao(erro=requests.ConnectionError("proxy"))))

    def test_robots_que_proibe_o_caminho_barra(self):
        texto = "User-agent: *\nDisallow: /estacao/\n"
        self.assertFalse(sonda.permitido(_Sessao(_Resposta(200, texto))))

    def test_robots_que_libera_passa(self):
        texto = "User-agent: *\nDisallow: /admin/\n"
        self.assertTrue(sonda.permitido(_Sessao(_Resposta(200, texto))))

    def test_http_estranho_nao_e_liberado(self):
        with contextlib.redirect_stderr(io.StringIO()):
            self.assertFalse(sonda.permitido(_Sessao(_Resposta(503))))


class SondarNaoEhVincular(unittest.TestCase):
    def test_o_salseiro_carrega_a_recusa_no_rotulo(self):
        """
        A 31 é a estação que quase entrou como régua de Vidal Ramos. Se a
        saída a listasse sem o aviso, a próxima pessoa refaria o pareamento.
        """
        self.assertIn("RECUSADA", sonda.ESTACOES["31"])
        self.assertIn("0,70 m", sonda.ESTACOES["31"])

    def test_a_ponte_estaiada_diz_que_o_par_foi_provado(self):
        self.assertIn("provado", sonda.ESTACOES["4"].lower())

    def test_os_ids_sao_os_que_o_jefferson_leu(self):
        self.assertEqual(set(sonda.ESTACOES), {"31", "18", "4", "23"})


class NaoEscreveNoProjeto(unittest.TestCase):
    def test_nao_toca_nos_jsons(self):
        for arquivo in ("estacoes.json", "enchentes.json", "transito.json"):
            self.assertNotIn(f'"{arquivo}"', FONTE)

    def test_o_bruto_nao_ganha_extensao_antes_de_ter_formato(self):
        """
        Nomear de .csv o que pode ser HTML de erro é o primeiro passo para
        tratar erro como dado. A extensão fica `.bruto` até alguém abrir.
        """
        self.assertIn('.bruto"', FONTE)
        self.assertNotIn('.csv"', FONTE)


class NaoInsisteAlemDeDoisFormatos(unittest.TestCase):
    def test_tenta_o_nativo_e_o_brasileiro_e_para(self):
        """A telemetria da ANA custou onze chamadas. Aqui o teto é dois."""
        self.assertEqual(sonda.FORMATOS_DE_DATA, ("%Y-%m-%d", "%d/%m/%Y"))
        self.assertIn("NÃO insistir", FONTE)


class OSecoNaoTocaARede(unittest.TestCase):
    def test_seco_imprime_o_plano_e_sai_zero(self):
        argv = sys.argv
        sys.argv = ["sonda", "--seco", "--codest", "4"]
        try:
            with contextlib.redirect_stdout(io.StringIO()) as saida:
                codigo = sonda.main()
        finally:
            sys.argv = argv
        self.assertEqual(codigo, 0)
        texto = saida.getvalue()
        self.assertIn("baixar-historico", texto)
        self.assertIn("robots.txt", texto)
        self.assertIn("PONTE ESTAIADA", texto)


if __name__ == "__main__":
    unittest.main()
