#!/usr/bin/env python3
"""Testes do núcleo HTTP da coleta.

Um ciclo perdido é histórico perdido para sempre — e numa cheia o ciclo perdido
pode ser justamente o do pico. Estes casos garantem que a coleta insiste quando
insistir adianta, e só nesses casos: insistir em 404 atrasa o resto, e insistir
num 429 sem respeitar o Retry-After é o caminho para levar bloqueio de uma fonte
pública que usamos de graça.

Sem rede e sem espera de verdade: o transporte e o `dormir` entram por parâmetro.

    python3 scripts/teste_http.py
"""

import unittest

import requests

from comum import HTTP_BACKOFF_BASE_S, baixar


class Resposta:
    def __init__(self, status=200, texto="ok", cabecalhos=None):
        self.status_code = status
        self.text = texto
        self.headers = cabecalhos or {}

    def raise_for_status(self):
        if self.status_code >= 400:
            erro = requests.HTTPError(f"HTTP {self.status_code}")
            erro.response = self
            raise erro


class Servidor:
    """Devolve as respostas na ordem; exceção na lista é levantada."""

    def __init__(self, *respostas):
        self.respostas = list(respostas)
        self.chamadas = 0

    def __call__(self, url, cabecalhos, timeout):
        self.chamadas += 1
        r = self.respostas[min(self.chamadas - 1, len(self.respostas) - 1)]
        if isinstance(r, Exception):
            raise r
        return r


class Relogio:
    def __init__(self):
        self.esperas = []

    def __call__(self, s):
        self.esperas.append(s)


class TestSucesso(unittest.TestCase):
    def test_devolve_o_texto(self):
        s = Servidor(Resposta(200, "<html>nível</html>"))
        self.assertEqual(baixar("http://x", transporte=s, dormir=Relogio()), "<html>nível</html>")
        self.assertEqual(s.chamadas, 1, "não repete o que deu certo")

    def test_manda_user_agent_identificavel(self):
        vistos = {}

        def transporte(url, cabecalhos, timeout):
            vistos.update(cabecalhos)
            return Resposta()

        baixar("http://x", transporte=transporte, dormir=Relogio())
        self.assertIn("enchentes-vale-itajai", vistos.get("User-Agent", ""))


class TestInsiste(unittest.TestCase):
    def test_erro_passageiro_de_servidor_e_retentado(self):
        """500 num servidor municipal é quase sempre soluço, não fim."""
        s = Servidor(Resposta(500), Resposta(500), Resposta(200, "veio"))
        relogio = Relogio()
        self.assertEqual(baixar("http://x", transporte=s, dormir=relogio), "veio")
        self.assertEqual(s.chamadas, 3)
        self.assertEqual(relogio.esperas, [HTTP_BACKOFF_BASE_S, HTTP_BACKOFF_BASE_S**2],
                         "a espera cresce entre tentativas")

    def test_timeout_e_retentado(self):
        s = Servidor(requests.Timeout("estourou"), Resposta(200, "veio"))
        self.assertEqual(baixar("http://x", transporte=s, dormir=Relogio()), "veio")

    def test_desiste_depois_das_tentativas_e_conta_o_porque(self):
        s = Servidor(Resposta(500))
        with self.assertRaises(requests.RequestException) as ctx:
            baixar("http://x", transporte=s, dormir=Relogio())
        self.assertEqual(s.chamadas, 3)
        self.assertIn("http://x", str(ctx.exception))


class TestNaoInsiste(unittest.TestCase):
    def test_404_nao_e_retentado(self):
        """Página que mudou de endereço não volta na segunda tentativa."""
        s = Servidor(Resposta(404))
        with self.assertRaises(requests.RequestException):
            baixar("http://x", transporte=s, dormir=Relogio())
        self.assertEqual(s.chamadas, 1)

    def test_403_nao_e_retentado(self):
        s = Servidor(Resposta(403))
        with self.assertRaises(requests.RequestException):
            baixar("http://x", transporte=s, dormir=Relogio())
        self.assertEqual(s.chamadas, 1)

    def test_rede_fora_desiste_rapido(self):
        """
        DNS quebrado ou rota inexistente não melhora esperando. Insistir aqui
        empata a execução enquanto o resto da coleta espera.
        """
        s = Servidor(requests.ConnectionError("network is unreachable"))
        with self.assertRaises(requests.RequestException):
            baixar("http://x", transporte=s, dormir=Relogio())
        self.assertEqual(s.chamadas, 2)


class Test429(unittest.TestCase):
    def test_respeita_o_retry_after_do_servidor(self):
        s = Servidor(Resposta(429, cabecalhos={"Retry-After": "45"}), Resposta(200, "veio"))
        relogio = Relogio()
        self.assertEqual(baixar("http://x", transporte=s, dormir=relogio), "veio")
        self.assertEqual(relogio.esperas, [45.0],
                         "o servidor pediu calma e disse por quanto tempo")

    def test_429_sem_cabecalho_usa_o_backoff(self):
        s = Servidor(Resposta(429), Resposta(200, "veio"))
        relogio = Relogio()
        baixar("http://x", transporte=s, dormir=relogio)
        self.assertEqual(relogio.esperas, [HTTP_BACKOFF_BASE_S])

    def test_retry_after_ilegivel_nao_quebra_a_coleta(self):
        s = Servidor(Resposta(429, cabecalhos={"Retry-After": "Wed, 21 Oct 2026 07:28:00 GMT"}),
                     Resposta(200, "veio"))
        relogio = Relogio()
        self.assertEqual(baixar("http://x", transporte=s, dormir=relogio), "veio")
        self.assertEqual(relogio.esperas, [HTTP_BACKOFF_BASE_S])


if __name__ == "__main__":
    unittest.main(verbosity=2)
