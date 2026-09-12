"""Verifica que o complemento de cadeia não desabilita a validação HTTPS."""
import ssl
import unittest
from unittest.mock import MagicMock, patch

import requests

from coleta_alertablu import AdaptadorAlertaBlu, URL, baixar


class TestTLSAlertaBlu(unittest.TestCase):
    def test_exige_cadeia_completa_e_hostname(self):
        adaptador = AdaptadorAlertaBlu()
        self.addCleanup(adaptador.close)
        contexto = adaptador.poolmanager.connection_pool_kw["ssl_context"]
        self.assertEqual(contexto.verify_mode, ssl.CERT_REQUIRED)
        self.assertTrue(contexto.check_hostname)
        self.assertFalse(contexto.verify_flags & ssl.VERIFY_X509_PARTIAL_CHAIN)
        self.assertGreater(contexto.cert_store_stats()["x509_ca"], 1)

    def test_monta_somente_no_host_e_preserva_verificacao(self):
        sessao = MagicMock()
        sessao.get.return_value.json.return_value = {"niveis": []}
        with patch("coleta_alertablu.requests.Session") as fabrica:
            fabrica.return_value.__enter__.return_value = sessao
            self.assertEqual(baixar(), {"niveis": []})
        self.assertEqual(sessao.mount.call_args.args[0], "https://defesacivil.blumenau.sc.gov.br/")
        self.assertIsInstance(sessao.mount.call_args.args[1], AdaptadorAlertaBlu)
        args, kwargs = sessao.get.call_args
        self.assertEqual(args, (URL,))
        self.assertNotEqual(kwargs.get("verify", True), False)
        self.assertEqual(kwargs["timeout"], 30)
        sessao.get.return_value.raise_for_status.assert_called_once()

    def test_erro_tls_nao_dispara_tentativa_sem_validacao(self):
        sessao = MagicMock()
        sessao.get.side_effect = requests.exceptions.SSLError("cadeia inválida")
        with patch("coleta_alertablu.requests.Session") as fabrica:
            fabrica.return_value.__enter__.return_value = sessao
            with self.assertRaises(requests.exceptions.SSLError):
                baixar()
        self.assertEqual(sessao.get.call_count, 1)


if __name__ == "__main__":
    unittest.main()
