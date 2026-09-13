import unittest
from datetime import datetime
from zoneinfo import ZoneInfo
from unittest.mock import patch
from coleta_indaial import interpretar, coletar


class Indaial(unittest.TestCase):
    agora = datetime(2026, 9, 13, 12, tzinfo=ZoneInfo('America/Sao_Paulo'))

    def ler(self, texto):
        return interpretar('Régua instalada fundos Celesc\n' + texto, self.agora)

    def test_mais_recente_independe_da_ordem_e_preserva_idade(self):
        l = self.ler('1209/2026\n22h - 4,10m\n21h - 4,14m\n11/09/2026\n23h - 5,15m')
        self.assertEqual(l['medido_em'], '2026-09-12T22:00:00')
        self.assertEqual(l['nivel_m'], 4.10)

    def test_nao_aceita_milimetros_ou_data_ambigua(self):
        with self.assertRaises(ValueError):
            self.ler('12/09/2026\n09h - 5,00mm\n13/2026\n10h - 5,01m')

    def test_futuro(self):
        with self.assertRaises(ValueError):
            self.ler('14/09/2026\n10h - 4,10m')

    def test_conflito(self):
        with self.assertRaises(ValueError):
            self.ler('12/09/2026\n22h - 4,10m\n22h - 4,11m')

    def test_referencia_obrigatoria(self):
        with self.assertRaises(ValueError):
            interpretar('12/09/2026\n22h - 4,10m', self.agora)

    def test_falha_isolada(self):
        with patch('coleta_indaial.baixar', side_effect=ValueError('indisponível')):
            self.assertEqual(coletar(), [])


if __name__ == '__main__':
    unittest.main()
