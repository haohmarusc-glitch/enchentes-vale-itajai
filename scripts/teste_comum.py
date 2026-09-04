#!/usr/bin/env python3
"""
Testes das utilidades compartilhadas.

O teste que importa aqui é o do `USER_AGENT` em ASCII. Ele não guarda um gosto
de estilo: guarda um bug que derrubou uma coleta inteira e levou uma sessão
para ser achado, porque a falha aparecia como problema da fonte.
"""
import re
import unittest
from pathlib import Path

from comum import USER_AGENT

RAIZ = Path(__file__).resolve().parent


class CabecalhoHTTP(unittest.TestCase):
    """
    Cabeçalho HTTP é ASCII. O que acontece quando não é (provado em 04/09/2026):

    `requests` codifica valor de cabeçalho em **latin-1**, então "ó" sai como o
    byte solto 0xF3 — sequência inválida em UTF-8. Servidor cuja borda valida
    UTF-8 no cabeçalho recusa antes de a aplicação ver: HTTP 400, corpo vazio,
    sem Content-Type. Nada na mensagem aponta para o cabeçalho, e o erro parece
    da fonte.

    O teste que separou as três formas do mesmo caractere, contra a API de Taió:

        "...\\xc3\\xb3..."  (ó em UTF-8, dois bytes)  -> 200
        "...\\xf3..."       (ó em latin-1, um byte)   -> 400
        só ASCII                                     -> 200

    curl não reproduzia porque o shell UTF-8 manda os dois bytes; só o
    `requests` mandava o byte solto. Por isso a linha de comando "provava" que
    estava tudo bem enquanto o coletor falhava.
    """

    def test_o_user_agent_e_ascii_puro(self):
        self.assertTrue(
            USER_AGENT.isascii(),
            "caractere fora do ASCII no User-Agent: "
            + repr([c for c in USER_AGENT if not c.isascii()]),
        )

    def test_o_que_o_requests_manda_na_rede_e_utf8_valido(self):
        """
        A checagem no nível do byte, que é onde o servidor decide.

        `USER_AGENT.encode("latin-1")` é literalmente o que sai no socket. Se
        esses bytes não decodificarem como UTF-8, é 400 na borda estrita.
        """
        na_rede = USER_AGENT.encode("latin-1")
        na_rede.decode("utf-8")  # levanta UnicodeDecodeError se voltar o acento

    def test_continua_identificando_o_projeto(self):
        # Tirar o acento não pode virar desculpa para tirar a identificação: o
        # CLAUDE.md exige que todo request diga quem é.
        self.assertIn("enchentes-vale-itajai", USER_AGENT)
        self.assertIn("GitHub", USER_AGENT)

    def test_nenhum_script_define_agente_proprio_com_acento(self):
        """
        O conserto vale para os onze scripts que importam de `comum`. Este teste
        cobre o caso seguinte: alguém escrever um agente local em outro arquivo
        e reintroduzir o byte inválido lá.
        """
        padrao = re.compile(r"^\s*\w*USER_AGENT\w*\s*=.*", re.M)
        culpados = []
        for arquivo in sorted(RAIZ.glob("*.py")):
            texto = arquivo.read_text(encoding="utf-8")
            for linha in padrao.findall(texto):
                if not linha.isascii():
                    culpados.append(f"{arquivo.name}: {linha.strip()}")
        self.assertEqual(culpados, [], "User-Agent com caractere fora do ASCII")


class Plausibilidade(unittest.TestCase):
    def test_a_faixa_recusa_o_que_nao_e_nivel_de_rio(self):
        from comum import nivel_plausivel

        self.assertTrue(nivel_plausivel(5.25))
        self.assertFalse(nivel_plausivel(0))
        self.assertFalse(nivel_plausivel(-1))
        self.assertFalse(nivel_plausivel(30))


if __name__ == "__main__":
    unittest.main()
