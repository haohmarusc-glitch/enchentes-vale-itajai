#!/usr/bin/env python3
"""
Testes do conferidor de régua × traçado.

O que ele guarda é uma distinção que, confundida, manda consertar a coisa
errada: régua longe do traçado pode ser CURSO FALTANDO no mapa (o caso de
04/09/2026, com os ribeirões de Itajaí) ou coordenada de estação que fica mesmo
longe do talvegue (Blumenau, ~3 km). O script fala do primeiro e não afirma o
segundo — e há teste para ele não passar a afirmar.
"""
import json
import unittest
from pathlib import Path

import conferir_reguas_no_tracado as cf

RAIZ = Path(__file__).resolve().parent.parent


def linha(pontos):
    """Um traçado com UMA polilinha — o formato que `tracados()` devolve."""
    return [[(lon, lat) for lon, lat in pontos]]


class Distancia(unittest.TestCase):
    def test_um_grau_de_latitude_da_cerca_de_111_km(self):
        self.assertAlmostEqual(cf.km((-48.7, -26.9), (-48.7, -27.9)), 111.32, places=1)

    def test_longitude_encolhe_com_a_latitude(self):
        """
        No paralelo 27, um grau de longitude vale ~0,89 de latitude. Sem essa
        correção o mapa entortaria leste-oeste — que é a direção da maior parte
        do Vale — e a régua "mais próxima" sairia errada.
        """
        lon = cf.km((-48.7, -26.9), (-49.7, -26.9))
        lat = cf.km((-48.7, -26.9), (-48.7, -27.9))
        self.assertLess(lon, lat)
        self.assertAlmostEqual(lon / lat, cf.K_LON, places=3)


class DistanciaAoSegmento(unittest.TestCase):
    """
    Mede-se até a LINHA, não até os vértices.

    Achado pelo próprio teste em 04/09/2026: com uma polilinha de dois pontos, a
    régua no meio dela aparecia a ~5 km. Num traçado denso o erro seria de
    metros, mas a resposta ficaria dependendo do espaçamento com que o OSM
    amostrou o trecho — e um trecho reto e longo é justamente o que vem com
    poucos pontos.
    """

    def test_ponto_no_meio_de_um_segmento_longo_esta_EM_CIMA_dele(self):
        a, b = (-48.70, -26.90), (-48.60, -26.90)
        self.assertLess(cf.km_ao_segmento((-48.65, -26.90), a, b), 0.01)
        # E medindo só aos vértices daria quilômetros — o erro que isto corrige.
        self.assertGreater(min(cf.km((-48.65, -26.90), a), cf.km((-48.65, -26.90), b)), 4)

    def test_nao_projeta_fora_do_segmento(self):
        # Além da ponta, a distância é até a PONTA, não à reta infinita.
        a, b = (-48.70, -26.90), (-48.60, -26.90)
        self.assertAlmostEqual(cf.km_ao_segmento((-48.50, -26.90), a, b),
                               cf.km((-48.50, -26.90), b), places=6)

    def test_segmento_degenerado_nao_divide_por_zero(self):
        a = (-48.70, -26.90)
        self.assertAlmostEqual(cf.km_ao_segmento((-48.70, -26.91), a, a),
                               cf.km((-48.70, -26.91), a), places=6)


class Avaliar(unittest.TestCase):
    TR = {"itajai-acu": linha([(-48.70, -26.90), (-48.60, -26.90)])}

    def est(self, **kw):
        base = {"codigo": "DC-X", "titulo": "T", "lat": -26.90, "lon": -48.65,
                "rio": "itajai-acu"}
        return {**base, **kw}

    def test_regua_em_cima_do_tracado_nao_e_acusada(self):
        r = cf.avaliar([self.est()], self.TR)[0]
        self.assertFalse(r["longe"])
        self.assertLess(r["km"], 0.1)

    def test_regua_longe_e_acusada_com_a_distancia(self):
        r = cf.avaliar([self.est(lat=-27.00)], self.TR)[0]  # ~11 km ao sul
        self.assertTrue(r["longe"])
        self.assertGreater(r["km"], 10)

    def test_sem_coordenada_nao_entra_e_pluviometro_tambem_nao(self):
        # Sem coordenada não há o que medir; pluviômetro não mede nível de rio.
        self.assertEqual(cf.avaliar([self.est(lat=None)], self.TR), [])
        self.assertEqual(cf.avaliar([self.est(lon=None)], self.TR), [])
        self.assertEqual(cf.avaliar([self.est(tipo="pluviometro")], self.TR), [])

    def test_o_limite_e_ajustavel_e_muda_o_veredito(self):
        e = [self.est(lat=-26.905)]  # ~0,55 km
        self.assertTrue(cf.avaliar(e, self.TR, limite=0.2)[0]["longe"])
        self.assertFalse(cf.avaliar(e, self.TR, limite=2.0)[0]["longe"])

    def test_ordena_da_mais_longe_para_a_mais_perto(self):
        rs = cf.avaliar(
            [self.est(codigo="perto"), self.est(codigo="longe", lat=-27.2)], self.TR)
        self.assertEqual([r["codigo"] for r in rs], ["longe", "perto"])


class ContraOsDadosReais(unittest.TestCase):
    """
    O estado de 04/09/2026, com o traçado que existe hoje.

    Este teste é um RETRATO que deve envelhecer: quando os ribeirões e o canal
    entrarem em `data/rios/`, ele falha e é para atualizar — a falha é a notícia
    boa de que o mapa ficou completo.
    """

    def setUp(self):
        self.tr = cf.tracados()
        self.est = json.loads(
            (RAIZ / "data/estacoes.json").read_text(encoding="utf-8"))["estacoes_tempo_real"]

    def test_o_tronco_esta_certo_e_a_Volta_de_Cima_tambem(self):
        """
        A dúvida que abriu isto era se o Açu perto da foz estava numa "linha
        reta" em vez do meandro da Volta de Cima. Não estava: a DC-11, que fica
        NA margem desse meandro, cai a poucos metros do traçado — o que só
        acontece se a curva estiver desenhada.
        """
        rs = {r["codigo"]: r for r in cf.avaliar(self.est, self.tr)}
        self.assertLess(rs["DC-11"]["km"], 0.3, "o meandro da Volta de Cima sumiu do traçado")
        for cod in ("DC-01", "DC-02", "DC-04", "DC-05", "DC-06", "DC-10"):
            self.assertLess(rs[cod]["km"], 0.3, f"{cod} saiu de cima do traçado")

    def test_as_quatro_que_faltam_sao_estas(self):
        longe = {r["codigo"] for r in cf.avaliar(self.est, self.tr) if r["longe"]}
        self.assertEqual(
            longe, {"DC-03", "DC-07", "DC-08", "DC-09"},
            "mudou o conjunto de réguas sem curso desenhado — atualize o retrato "
            "e o docs/tracado-ribeiroes.md",
        )

    def test_o_script_NAO_acusa_coordenada_errada(self):
        """
        Distância a traçado não mede erro de coordenada: a régua de Blumenau
        fica ~3 km do talvegue porque a coordenada publicada é a da ESTAÇÃO.
        Se o texto passar a dizer "coordenada errada", manda conferir o dado
        certo pelo motivo errado.
        """
        texto = (RAIZ / "scripts/conferir_reguas_no_tracado.py").read_text(encoding="utf-8")
        self.assertIn("não coordenada errada", texto)


if __name__ == "__main__":
    unittest.main()
