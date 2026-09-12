import json
import unittest
from importar_manchas_blumenau import NIVEIS, extrair


class Extracao(unittest.TestCase):
    def fonte(self):
        g = {'type': 'FeatureCollection', 'features': [{'geometry': {'type': 'Polygon',
             'coordinates': [[[-49,-27],[-49.1,-27],[-49.1,-26.9],[-49,-27]]]}}]}
        return 'const CAMADAS = ' + json.dumps({str(n).replace('.', '_'): g for n in NIVEIS}) + '; executarAlgo();'

    def test_extrai_sem_executar_codigo(self):
        self.assertEqual(len(extrair(self.fonte())), 16)
        self.assertIn('8.5', extrair(self.fonte()))

    def test_recusa_coordenadas_e_conjunto_alterados(self):
        for s in [self.fonte().replace('-49.1', '0'), self.fonte().replace('"8_5":', '"7_5":')]:
            with self.assertRaises(ValueError):
                extrair(s)


if __name__ == '__main__':
    unittest.main()
