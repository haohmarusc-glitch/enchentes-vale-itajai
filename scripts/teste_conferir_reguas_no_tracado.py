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
    O estado com o traçado que existe hoje.

    Em 04/09/2026 este bloco era um RETRATO das quatro réguas que boiavam fora
    de qualquer rio — DC-03 a 2,32 km, DC-07 a 2,25, DC-08 a 4,41, DC-09 a 0,87
    —, e trazia escrito que a falha dele seria "a notícia boa de que o mapa
    ficou completo". Foi o que aconteceu no mesmo dia: com o Ribeirão da Murta,
    o Rio Canhanduba e o canal retificado do Mirim em `data/rios/`, as ONZE
    réguas passaram a cair a menos de 50 m do curso delas.

    Então o retrato virou REGRA. Em vez de listar quem falta, o teste agora
    cobra que não falte ninguém — afirmação mais forte, que não envelhece e que
    pega o caso perigoso: alguém apagar ou trocar um traçado e um pino voltar a
    flutuar no meio do bairro, sem erro nenhum na tela.
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

    def test_NENHUMA_regua_fica_sem_curso_desenhado(self):
        """
        A regra que substituiu o retrato das quatro que faltavam.

        Pino longe de qualquer rio não dá erro: ele simplesmente aparece no
        lugar errado, e quem mora ali confere a régua do bairro do vizinho
        achando que é a dele.
        """
        longe = {r["codigo"] for r in cf.avaliar(self.est, self.tr) if r["longe"]}
        self.assertEqual(
            longe, set(),
            "régua voltou a ficar sem curso desenhado. Provável causa: um "
            "geojson de data/rios/ foi apagado ou trocado. Ver docs/tracado-ribeiroes.md.",
        )

    def test_os_tres_cursos_de_Itajai_estao_desenhados(self):
        """
        Nomeia os traçados que resolveram as quatro. Sem isto, o teste acima
        também passaria se alguém apagasse os três E as réguas junto.
        """
        for rio_id in ("ribeirao-murta", "ribeirao-canhanduba", "mirim-canal-retificado"):
            self.assertIn(rio_id, self.tr, f"{rio_id} sumiu de data/rios/")

    def test_cada_regua_dos_ribeiroes_casa_com_o_curso_do_cadastro(self):
        """
        Perto de um rio qualquer não basta: perto do rio CERTO.

        Na foz os cursos correm a poucas centenas de metros uns dos outros, e
        uma régua encostada no rio errado diria a cidade errada sobre qual água
        está subindo. Exceção conhecida e aceita: a DC-03, cadastrada como
        `itajai-mirim`, casa com o `mirim-canal-retificado` — é o mesmo rio, na
        obra que o retificou, e o cadastro guarda essa distinção no título.
        """
        esperado = {
            "DC-07": "ribeirao-murta",
            "DC-09": "ribeirao-murta",
            "DC-08": "ribeirao-canhanduba",
            "DC-03": "mirim-canal-retificado",
        }
        rs = {r["codigo"]: r for r in cf.avaliar(self.est, self.tr)}
        for codigo, curso in esperado.items():
            self.assertEqual(rs[codigo]["rio_mais_proximo"], curso,
                             f"{codigo} casou com {rs[codigo]['rio_mais_proximo']}, não com {curso}")
            self.assertLess(rs[codigo]["km"], 0.1, f"{codigo} afastou-se do curso dela")

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
