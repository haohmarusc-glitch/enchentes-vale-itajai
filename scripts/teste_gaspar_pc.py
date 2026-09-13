"""Regressões da ponte municipal: identidade, validade e integração."""
import copy
import json
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

import coleta_niveis
import gaspar_pc


class Ponte(unittest.TestCase):
    def setUp(self):
        self.agora = datetime(2026, 9, 13, 0, 20, tzinfo=timezone.utc)
        self.corpo = {'fonte': gaspar_pc.FONTE, 'coletado_em': '2026-09-13T00:19:00+00:00',
                      'leitura': {'cidade': 'gaspar', 'rio': 'itajai-acu',
                                  'estacao': gaspar_pc.ESTACAO, 'nivel_m': 4.09,
                                  'medido_em': '2026-09-12T21:00:00'}}

    def test_preserva_medicao(self):
        l = gaspar_pc.validar(self.corpo, self.agora)
        self.assertEqual(l['medido_em'], '2026-09-12T21:00:00')
        self.assertEqual(l['nivel_m'], 4.09)

    def test_recusa_outro_instrumento_e_valores_invalidos(self):
        for chave, valor in [('cidade', 'blumenau'), ('estacao', 'Belchior'),
                             ('rio', 'outro'), ('nivel_m', True), ('nivel_m', float('nan')),
                             ('nivel_m', 0), ('nivel_m', 30), ('medido_em', '2026-09-12T23:00:00'),
                             ('medido_em', '2026-09-12T17:00:00'), ('medido_em', None)]:
            with self.subTest(chave=chave, valor=valor):
                c = copy.deepcopy(self.corpo)
                c['leitura'][chave] = valor
                self.assertIsNone(gaspar_pc.validar(c, self.agora))
        for coleta in ['2026-09-12T23:00:00+00:00', '2026-09-13T01:00:00+00:00', '2026-09-13T00:19:00']:
            self.assertIsNone(gaspar_pc.validar({**self.corpo, 'coletado_em': coleta}, self.agora))
        self.assertIsNone(gaspar_pc.validar({**self.corpo, 'fonte': 'outra'}, self.agora))

    def test_arquivo_ausente_corrompido_e_valido(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / 'ponte.json'
            self.assertIsNone(gaspar_pc.ler(p, self.agora))
            p.write_text('{', encoding='utf-8')
            self.assertIsNone(gaspar_pc.ler(p, self.agora))
            p.write_text(json.dumps(self.corpo), encoding='utf-8')
            self.assertEqual(gaspar_pc.ler(p, self.agora)['nivel_m'], 4.09)

    def test_coleta_usa_ponte_sem_tentar_rede_bloqueada(self):
        l = gaspar_pc.validar(self.corpo, self.agora)
        with patch('gaspar_pc.ler', return_value=l), patch('coleta_gaspar.permitido') as rede:
            self.assertEqual(coleta_niveis.baixar_nivel_gaspar(False), [l])
            rede.assert_not_called()


if __name__ == '__main__':
    unittest.main()
