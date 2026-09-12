"""Extrai CAMADAS como JSON, sem executar JavaScript da fonte."""
import argparse
import hashlib
import json
import math
import re
from pathlib import Path

FONTE = 'https://defesacivil.blumenau.sc.gov.br/static/mapas/inundacao/camadas_get_nivel.js'
NIVEIS = [8, 8.5, 9, 9.5, 10, 10.5, 11, 11.5, 12, 12.5, 13, 14, 15, 16, 17, 18]


def extrair(texto):
    inicio = re.search(r'\bconst\s+CAMADAS\s*=\s*', texto)
    if not inicio:
        raise ValueError('Declaração CAMADAS ausente')
    camadas, _ = json.JSONDecoder().raw_decode(texto[inicio.end():])
    camadas = {k.replace('_', '.'): v for k, v in camadas.items()}
    if sorted(map(float, camadas)) != NIVEIS:
        raise ValueError('Conjunto de cotas inesperado: revisar fonte')
    for geo in camadas.values():
        if geo.get('type') != 'FeatureCollection' or not geo.get('features'):
            raise ValueError('Camada vazia ou inválida')
        for f in geo['features']:
            g = f['geometry']
            if g['type'] not in ('Polygon', 'MultiPolygon'):
                raise ValueError('Geometria não poligonal')
            polys = g['coordinates'] if g['type'] == 'MultiPolygon' else [g['coordinates']]
            for pol in polys:
                for anel in pol:
                    if len(anel) < 4 or anel[0] != anel[-1]:
                        raise ValueError('Anel aberto')
                    for lon, lat in anel:
                        if not (math.isfinite(lon) and math.isfinite(lat) and -49.4 < lon < -48.8 and -27.2 < lat < -26.6):
                            raise ValueError('Coordenada fora de Blumenau')
    return camadas


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('arquivo', type=Path)
    args = ap.parse_args()
    bruto = args.arquivo.read_bytes()
    camadas = extrair(bruto.decode('utf-8-sig'))
    destino = Path(__file__).resolve().parent.parent / 'data/manchas/blumenau'
    destino.mkdir(parents=True, exist_ok=True)
    indice = {'fonte': FONTE, 'pagina': 'https://defesacivil.blumenau.sc.gov.br/m/inundacao',
              'sha256_js': hashlib.sha256(bruto).hexdigest(), 'ano_cartografia': 2025,
              'tipo': 'simulação por cota; não é evento histórico nem alagamento observado', 'camadas': []}
    for n in NIVEIS:
        geo = camadas[str(n)]
        arquivo = f'cota-{n:.2f}.geojson'
        (destino / arquivo).write_text(json.dumps(geo, ensure_ascii=False, separators=(',', ':')) + '\n', encoding='utf-8')
        indice['camadas'].append({'nivel_m': n, 'arquivo': arquivo, 'feicoes': len(geo['features'])})
    (destino / 'index.json').write_text(json.dumps(indice, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(f'{len(camadas)} camadas extraídas; coordenadas preservadas')


if __name__ == '__main__':
    main()
