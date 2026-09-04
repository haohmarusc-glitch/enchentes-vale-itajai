#!/usr/bin/env python3
"""
Testes do conversor de traçado — e das GRAFIAS que o OSM realmente usa.

Escrever as chaves de busca é adivinhar como o mapeador nomeou o curso. Adivinhar
errado não quebra nada barulhento: o conversor pula com aviso, o geojson não
nasce, e o rio simplesmente continua faltando no mapa — que é o estado de antes,
e por isso passa despercebido.

Os nomes abaixo NÃO são chute. Vieram da consulta real ao Overpass rodada na VPS
em 04/09/2026, que devolveu exatamente:

    Rio Canhanduba                       11 ways
    Ribeirão da Murta                     5
    Canal Retificado Rio Itajaí Mirim     2
    Canal Retificado Rio Itajaí-Mirim     1

As duas grafias do canal (com e sem hífen) são o MESMO canal partido em ways
diferentes, e por isso caem no mesmo arquivo — o que o teste também trava.
"""
import unittest

import converter_tracado_rios as ct

#: O que o Overpass devolveu de verdade, com a contagem de ways.
NOMES_REAIS_DO_OSM = {
    "Rio Canhanduba": 11,
    "Ribeirão da Murta": 5,
    "Canal Retificado Rio Itajaí Mirim": 2,
    "Canal Retificado Rio Itajaí-Mirim": 1,
}


def way(nome, n=3):
    """Um way com `n` pontos — geometria fake, o que importa aqui é o nome."""
    return {
        "type": "way",
        "tags": {"name": nome, "waterway": "stream"},
        "geometry": [{"lon": -48.7 + i * 0.001, "lat": -26.9 - i * 0.001} for i in range(n)],
    }


class GrafiasReaisDoOSM(unittest.TestCase):
    def test_cada_nome_real_cai_no_rio_certo(self):
        elementos = [way(n) for n, c in NOMES_REAIS_DO_OSM.items() for _ in range(c)]
        achados = {
            rio: ct.linhas_por_substring(elementos, chaves)
            for rio, chaves in ct.RIOS_AFLUENTES.items()
        }
        self.assertEqual(len(achados["ribeirao-canhanduba"]), 11, "Rio Canhanduba não casou")
        self.assertEqual(len(achados["ribeirao-murta"]), 5, "Ribeirão da Murta não casou")
        # As DUAS grafias do canal, juntas: é o mesmo canal partido em ways.
        self.assertEqual(len(achados["mirim-canal-retificado"]), 3,
                         "as duas grafias do canal deviam cair no mesmo arquivo")

    def test_nenhum_nome_real_cai_em_DOIS_rios(self):
        """
        Chave frouxa demais faria o mesmo way virar dois rios, e o mapa
        desenharia o Canhanduba por cima do canal. Cada nome tem um dono só.
        """
        for nome in NOMES_REAIS_DO_OSM:
            donos = [rio for rio, chaves in ct.RIOS_AFLUENTES.items()
                     if ct.linhas_por_substring([way(nome)], chaves)]
            self.assertEqual(len(donos), 1, f"{nome!r} casou com {donos}")

    def test_o_tronco_nao_e_arrastado_pelas_chaves_dos_afluentes(self):
        # "Rio Itajaí-Mirim" contém "itajaí-mirim"; se a chave do canal fosse só
        # isso, o tronco inteiro viraria canal — e o Mirim apareceria duplicado.
        for nome in ("Rio Itajaí-Mirim", "Rio Itajaí-Açu", "Rio Itajaí do Oeste"):
            donos = [rio for rio, chaves in ct.RIOS_AFLUENTES.items()
                     if ct.linhas_por_substring([way(nome)], chaves)]
            self.assertEqual(donos, [], f"{nome!r} foi capturado por {donos}")


class SemBruto(unittest.TestCase):
    def test_way_curto_demais_nao_vira_linha(self):
        # Um ponto só não é traçado; desenhar viraria um risco de nada.
        self.assertEqual(ct.linhas_por_substring([way("Rio Canhanduba", n=1)],
                                                 ["rio canhanduba"]), [])

    def test_way_sem_nome_e_ignorado(self):
        anonimo = {"type": "way", "tags": {"waterway": "stream"},
                   "geometry": [{"lon": -48.7, "lat": -26.9}, {"lon": -48.6, "lat": -26.9}]}
        self.assertEqual(ct.linhas_por_substring([anonimo], ["rio canhanduba"]), [])

    def test_a_geometria_sai_em_lon_lat_ordem_do_geojson(self):
        # O OSM devolve lat/lon; o GeoJSON quer [lon, lat]. Trocar inverteria o
        # mapa inteiro — e o rio apareceria na África.
        linha = ct.linhas_por_substring([way("Rio Canhanduba")], ["rio canhanduba"])[0]
        lon, lat = linha[0]
        self.assertLess(lon, -40, "longitude e latitude trocadas")
        self.assertGreater(lat, -30)
        self.assertLess(lat, -20)


if __name__ == "__main__":
    unittest.main()
