import unittest
from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import patch

from coleta_niveis import coletar_fonte_itajai
from bot import resposta_nivel, _linha_cidade


class FalhaItajai(unittest.TestCase):
    def test_html_sem_reguas_nao_e_sucesso(self):
        with patch('coleta_niveis.baixar_niveis', return_value=[]):
            self.assertEqual(coletar_fonte_itajai(), ([], False))

    def test_erro_de_rede_vira_estado_de_falha(self):
        with patch('coleta_niveis.baixar_niveis', side_effect=ConnectionError('offline')):
            self.assertEqual(coletar_fonte_itajai(), ([], False))

    def test_recuperacao_da_fonte(self):
        leituras = [{'cidade': 'itajai', 'medido_em': '2026-09-12T07:00:00', 'nivel_m': 1.5}]
        with patch('coleta_niveis.baixar_niveis', return_value=leituras):
            self.assertEqual(coletar_fonte_itajai(), (leituras, True))

    def test_bot_informa_falha_em_ambos_comandos(self):
        base = SimpleNamespace(ultimo={'fonte_itajai_ok': False})
        cidade = {'id': 'itajai', 'nome': 'Itajaí'}
        agora = datetime.now(timezone.utc)
        self.assertIn('Fonte de Itajaí indisponível', '\n'.join(resposta_nivel(base, cidade, agora)))
        self.assertIn('fonte municipal indisponível', '\n'.join(_linha_cidade(base, cidade, {}, agora, 'itajai-acu')))


if __name__ == '__main__':
    unittest.main()
