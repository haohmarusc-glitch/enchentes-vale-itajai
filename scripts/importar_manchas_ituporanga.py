"""Extrai polígonos das camadas KML, sem interpolar ou alterar coordenadas."""
import argparse
import hashlib
import json
import math
import re
from pathlib import Path
import xml.etree.ElementTree as ET
from shapely.geometry import Polygon, MultiPolygon, mapping
from shapely import union_all

NS = {'k': 'http://www.opengis.net/kml/2.2'}
FONTE = 'https://www.google.com/maps/d/viewer?mid=19tpP2Tfsl58ue6GtY5ihBfK3MLkiUrA'


def anel(elemento, interno=False):
    pontos = []
    for item in (elemento.text or '').split():
        lon, lat, *_ = map(float, item.split(','))
        if not (math.isfinite(lon) and math.isfinite(lat) and -180 <= lon <= 180 and -90 <= lat <= 90):
            raise ValueError('Coordenada inválida')
        pontos.append([lon, lat])
    if len(pontos) < 4 or pontos[0] != pontos[-1]:
        raise ValueError('Anel incompleto ou aberto')
    # Orientação GeoJSON: exterior anti-horário, furos horários. Não move vértices.
    area = sum(a[0] * b[1] - b[0] * a[1] for a, b in zip(pontos, pontos[1:]))
    if (area < 0 and not interno) or (area > 0 and interno):
        pontos.reverse()
    return pontos


def converter(conteudo):
    camadas = []
    for pasta in ET.fromstring(conteudo).findall('.//k:Folder', NS):
        nome = pasta.findtext('k:name', '', NS)
        m = re.fullmatch(r'COTA\s*-?\s*(\d+,\d+)', nome.strip())
        if not m:
            continue
        nivel = float(m[1].replace(',', '.'))
        poligonos = []
        for pol in pasta.findall('.//k:Polygon', NS):
            externo = pol.find('k:outerBoundaryIs/k:LinearRing/k:coordinates', NS)
            if externo is None:
                raise ValueError('Polígono sem contorno externo')
            poligonos.append([anel(externo)] + [anel(a, interno=True) for a in pol.findall('k:innerBoundaryIs/k:LinearRing/k:coordinates', NS)])
        if not poligonos:
            raise ValueError(f'Camada vazia: {nome}')
        geometrias = [Polygon(p[0], p[1:]) for p in poligonos]
        if any(not g.is_valid for g in geometrias):
            raise ValueError(f'Polígono inválido: {nome}')
        # Dissolve limites internos das faixas contíguas, sem buffer ou simplificação.
        # Faixas subpixel isoladas somem ao projetar em pixels no navegador.
        uniao = union_all(geometrias)
        if uniao.geom_type == 'Polygon':
            uniao = MultiPolygon([uniao])
        if uniao.geom_type != 'MultiPolygon' or not uniao.is_valid:
            raise ValueError(f'União inválida: {nome}')
        geo = {'type': 'FeatureCollection', 'features': [{'type': 'Feature',
               'properties': {'camada': nome, 'nivel_fonte_m': nivel, 'poligonos_fonte': len(poligonos)},
               'geometry': mapping(uniao)}]}
        camadas.append((nivel, nome, geo, len(pasta.findall('.//k:LineString', NS))))
    if len({c[0] for c in camadas}) != len(camadas):
        raise ValueError('Níveis duplicados')
    return sorted(camadas)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('kml', type=Path)
    ap.add_argument('--saida', type=Path, required=True)
    args = ap.parse_args()
    bruto = args.kml.read_bytes()
    camadas = converter(bruto)
    if [c[0] for c in camadas] != [3 + i / 2 for i in range(8)]:
        raise ValueError('Esperadas oito camadas entre 3,00 e 6,50 m')
    args.saida.mkdir(parents=True, exist_ok=True)
    indice = {'fonte': FONTE, 'sha256_kml': hashlib.sha256(bruto).hexdigest(),
              'referencia_regua': None, 'comparar_com_tempo_real': False, 'camadas': []}
    for nivel, nome, geo, linhas in camadas:
        arquivo = f'cota-{nivel:.2f}.geojson'
        (args.saida / arquivo).write_text(json.dumps(geo, separators=(',', ':')), encoding='utf-8')
        indice['camadas'].append({'nivel_m': nivel, 'nome': nome, 'arquivo': arquivo,
                                  'poligonos': geo['features'][0]['properties']['poligonos_fonte'],
                                  'poligonos_apos_uniao': len(geo['features'][0]['geometry']['coordinates']),
                                  'linhas_nao_preenchidas': linhas})
    (args.saida / 'index.json').write_text(json.dumps(indice, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


if __name__ == '__main__':
    main()
