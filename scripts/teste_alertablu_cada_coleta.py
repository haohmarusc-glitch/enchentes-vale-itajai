"""Não esperar a fonte intermediária envelhecer para consultar Blumenau."""
import unittest
from unittest.mock import patch

from coleta_niveis import baixar_nivel_alertablu


class ConsultaBlumenau(unittest.TestCase):
    def test_consulta_mesmo_com_primaria_recente(self):
        from datetime import datetime
        from zoneinfo import ZoneInfo
        primaria = [{"cidade": "blumenau", "nivel_m": 6.32,
                     "medido_em": datetime.now(ZoneInfo("America/Sao_Paulo")).strftime("%Y-%m-%dT%H:%M:%S")}]
        original = [dict(primaria[0])]
        with patch("coleta_alertablu.baixar", return_value={}) as baixar, \
                patch("coleta_alertablu.parse", return_value=[{"nivel_m": 6.73}]) as parse:
            self.assertEqual(baixar_nivel_alertablu(primaria), [{"nivel_m": 6.73}])
        baixar.assert_called_once()
        parse.assert_called_once_with({})
        self.assertEqual(primaria, original)

    def test_falha_preserva_primaria(self):
        primaria = [{"cidade": "blumenau", "nivel_m": 6.32}]
        with patch("coleta_alertablu.baixar", side_effect=ConnectionError("indisponível")):
            self.assertEqual(baixar_nivel_alertablu(primaria), [])
        self.assertEqual(primaria, [{"cidade": "blumenau", "nivel_m": 6.32}])


if __name__ == "__main__":
    unittest.main()
