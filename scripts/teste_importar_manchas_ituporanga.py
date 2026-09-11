import unittest
import xml.etree.ElementTree as ET
from importar_manchas_ituporanga import anel, converter

class Importacao(unittest.TestCase):
    def test_preserva_poligono_e_furo(self):
        kml = b'''<kml xmlns="http://www.opengis.net/kml/2.2"><Document><Folder><name>COTA - 3,00</name><Placemark><Polygon><outerBoundaryIs><LinearRing><coordinates>0,0,0 2,0,0 2,2,0 0,2,0 0,0,0</coordinates></LinearRing></outerBoundaryIs><innerBoundaryIs><LinearRing><coordinates>0.5,0.5,0 1,0.5,0 1,1,0 0.5,1,0 0.5,0.5,0</coordinates></LinearRing></innerBoundaryIs></Polygon><LineString><coordinates>0,0 2,2</coordinates></LineString></Placemark></Folder></Document></kml>'''
        nivel, nome, geo, linhas = converter(kml)[0]
        self.assertEqual(nivel, 3)
        self.assertEqual(linhas, 1)
        rings = geo['features'][0]['geometry']['coordinates'][0]
        self.assertEqual(len(rings), 2)
        area = lambda ps: sum(a[0]*b[1]-b[0]*a[1] for a,b in zip(ps,ps[1:]))
        self.assertLess(area(rings[0]) * area(rings[1]), 0)
        self.assertEqual(set(map(tuple,rings[1])), {(0.5,0.5),(1,0.5),(1,1),(0.5,1)})

    def test_uniao_preserva_area_sem_fresta_entre_fragmentos(self):
        from shapely.geometry import shape
        poligonos = ''.join('<Polygon><outerBoundaryIs><LinearRing><coordinates>'+c+
            '</coordinates></LinearRing></outerBoundaryIs></Polygon>' for c in
            ['0,0 1,0 1,1 0,1 0,0', '1,0 2,0 2,1 1,1 1,0'])
        kml = '<kml xmlns="http://www.opengis.net/kml/2.2"><Folder><name>COTA 3,00</name>'+poligonos+'</Folder></kml>'
        geo = converter(kml)[0][2]
        geometria = shape(geo['features'][0]['geometry'])
        self.assertEqual(geometria.area, 2)
        self.assertEqual(len(geometria.geoms), 1)
        self.assertEqual(geo['features'][0]['properties']['poligonos_fonte'], 2)

    def test_recusa_anel_aberto_e_coordenada_invalida(self):
        for coords in ['0,0 1,0 1,1 0,1', 'nan,0 1,0 1,1 nan,0']:
            with self.subTest(coords=coords), self.assertRaises(ValueError):
                anel(ET.fromstring('<coordinates>'+coords+'</coordinates>'))

if __name__ == '__main__':
    unittest.main()
