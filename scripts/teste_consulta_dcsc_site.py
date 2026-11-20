#!/usr/bin/env python3
"""Testes da consulta do site da DCSC (`consulta_dcsc_site.py`) — a única `Tags_data` aceita desde ~17/11/2026.

    python3 scripts/teste_consulta_dcsc_site.py
"""
import hashlib
import re
import sys
import unittest
import unittest.mock
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import consulta_dcsc_site as c

FECHADA = [{"message": "Consulta não permitida. Use exatamente o texto das consultas do guia da API "
                       "(docs/guia-da-api.md).", "extensions": {"code": "QUERY_NOT_ALLOWED"}}]
OK = {"data": {"tags_data": {"qualle_meteorologia": [{"codigo": "DCSC-00019"}]}}}


class TextoDoSite(unittest.TestCase):
    def test_o_texto_e_o_copiado_do_site_sem_mudanca(self):
        """Montar à mão já deu 400 uma vez (armadilha 9). Trocar o texto exige copiar de novo do site."""
        self.assertEqual(hashlib.sha256(c.ARQUIVO.read_bytes()).hexdigest(),
                         "e123cda79a4e3f228c42dc9f16dc302b62c123a96170d370805cedae0b999cec")

    def test_traz_o_que_os_coletores_leem(self):
        plano = re.sub(r"\s+", " ", c.TAGS_DATA_DO_SITE)
        for campo in ("codigo", "name { prefix general local }", "timestamp", "type",
                      "rio_nivel { value", "rio_nivel_tendencia { value", "rio_nome { value }",
                      "rio_area_drenagem { value }", "h024 { value", "h168 { value", "h001 { value",
                      "h012 { value", "tem_nivel_do_rio", "bacia latitude longitude"):
            self.assertIn(campo, plano)
        self.assertIn('clients: ["secretaria-de-defesa-civil"]', plano)

    def test_nao_traz_rio_alarmes(self):
        """Enquanto só ela passa, a faixa estadual sai `indisponivel` — nunca inventada."""
        self.assertNotIn("rio_alarmes", c.TAGS_DATA_DO_SITE)


class Escada(unittest.TestCase):
    def test_usa_a_propria_quando_aceita(self):
        pedir = unittest.mock.Mock(return_value=OK)
        est, consulta = c.tags_data(pedir, "query curta")
        self.assertEqual(est, [{"codigo": "DCSC-00019"}])
        self.assertEqual(consulta, {"degrau": "propria", "motivo": None})
        pedir.assert_called_once_with("query curta")

    def test_lista_fechada_cai_para_o_texto_do_site_e_guarda_a_recusa(self):
        pedir = unittest.mock.Mock(side_effect=[{"errors": FECHADA}, OK])
        est, consulta = c.tags_data(pedir, "query curta")
        self.assertEqual(est, [{"codigo": "DCSC-00019"}])
        self.assertEqual(pedir.call_args_list[1].args[0], c.TAGS_DATA_DO_SITE)
        self.assertEqual(consulta["degrau"], "site")
        self.assertIn("Consulta não permitida", consulta["motivo"])

    def test_as_duas_recusadas_levanta_com_as_duas_mensagens(self):
        pedir = unittest.mock.Mock(side_effect=[{"errors": FECHADA}, RuntimeError("timeout")])
        with self.assertRaises(RuntimeError) as ctx:
            c.tags_data(pedir, "query curta")
        self.assertIn("Consulta não permitida", str(ctx.exception))
        self.assertIn("timeout", str(ctx.exception))


class Corpo(unittest.TestCase):
    def test_400_com_errors_devolve_o_corpo(self):
        r = unittest.mock.Mock(status_code=400)
        r.json.return_value = {"errors": FECHADA}
        self.assertEqual(c.corpo(r), {"errors": FECHADA})
        r.raise_for_status.assert_not_called()

    def test_400_sem_json_levanta_o_erro_http(self):
        r = unittest.mock.Mock(status_code=400)
        r.json.side_effect = ValueError("não é JSON")
        r.raise_for_status.side_effect = RuntimeError("400 Client Error")
        with self.assertRaises(RuntimeError):
            c.corpo(r)

    def test_500_levanta(self):
        r = unittest.mock.Mock(status_code=500)
        r.raise_for_status.side_effect = RuntimeError("500 Server Error")
        with self.assertRaises(RuntimeError):
            c.corpo(r)


if __name__ == "__main__":
    unittest.main(verbosity=2)
