#!/usr/bin/env python3
"""
Testes da conferência "o afluente chega no rio?".

Afluente cortado é pior que afluente ausente. Ausente, quem olha sabe que não
sabe. Cortado, o mapa AFIRMA que a água pára ali — e quem mora entre a ponta do
traçado e o rio conclui que o ribeirão não chega perto de casa.
"""
import json
import tempfile
import unittest
from pathlib import Path

import conferir_afluentes_chegam as cf

RAIZ = Path(__file__).resolve().parent.parent


def geojson(linhas):
    return {"type": "Feature", "properties": {},
            "geometry": {"type": "MultiLineString", "coordinates": linhas}}


class Medida(unittest.TestCase):
    """Contra arquivos inventados, para o cálculo não depender do dado real."""

    def monta(self, arquivos: dict) -> Path:
        tmp = Path(tempfile.mkdtemp())
        for nome, linhas in arquivos.items():
            (tmp / f"{nome}.geojson").write_text(
                json.dumps(geojson(linhas)), encoding="utf-8")
        return tmp

    def com(self, arquivos, **kw):
        antigo = cf.RIOS
        cf.RIOS = self.monta(arquivos)
        try:
            return cf.avaliar(**kw)
        finally:
            cf.RIOS = antigo

    def test_afluente_que_encosta_no_tronco_nao_e_cortado(self):
        rs = self.com({
            "itajai-mirim": [[[-48.70, -26.93], [-48.68, -26.93]]],
            "ribeirao-x": [[[-48.69, -26.95], [-48.69, -26.93]]],  # toca a linha
        })
        self.assertEqual(len(rs), 1)
        self.assertFalse(rs[0]["cortado"], rs[0])
        self.assertEqual(rs[0]["chega_em"], "itajai-mirim")

    def test_afluente_que_para_longe_e_cortado(self):
        rs = self.com({
            "itajai-mirim": [[[-48.70, -26.93], [-48.68, -26.93]]],
            "ribeirao-x": [[[-48.69, -26.98], [-48.69, -26.96]]],  # ~3 km antes
        })
        self.assertTrue(rs[0]["cortado"])
        self.assertGreater(rs[0]["metros"], 1000)

    def test_a_PONTA_e_que_conta_nao_a_passagem_perto(self):
        """
        Um afluente pode roçar o tronco no meio do curso e desaguar longe. Medir
        o ponto mais próximo de QUALQUER vértice diria "chega" para um traçado
        que não chega.
        """
        rs = self.com({
            "itajai-mirim": [[[-48.70, -26.93], [-48.60, -26.93]]],
            # Passa colado ao tronco no meio, mas as duas pontas ficam longe.
            "ribeirao-x": [[[-48.65, -26.99], [-48.65, -26.9301], [-48.65, -26.87]]],
        })
        self.assertTrue(rs[0]["cortado"], "passar perto no meio não é desaguar")

    def test_afluente_que_chega_PELO_VIZINHO_nao_e_cortado(self):
        """
        O caso real do Canhanduba: ele não toca o Mirim — deságua no Rio
        Conceição, que deságua no Mirim. É geografia, não defeito, e foi por
        isso que a busca por nome nunca fechou o vão.
        """
        rs = {r["rio"]: r for r in self.com({
            "itajai-mirim": [[[-48.70, -26.93], [-48.60, -26.93]]],
            # O vizinho toca o tronco.
            "rio-conceicao": [[[-48.65, -26.95], [-48.65, -26.9301]]],
            # E o afluente toca o vizinho, longe do tronco.
            "ribeirao-x": [[[-48.65, -26.98], [-48.65, -26.9501]]],
        })}
        self.assertFalse(rs["ribeirao-x"]["cortado"], rs["ribeirao-x"])
        self.assertEqual(rs["ribeirao-x"]["via"], ["rio-conceicao"])
        self.assertEqual(rs["ribeirao-x"]["chega_em"], "itajai-mirim")

    def test_chegar_por_vizinho_que_TAMBEM_esta_cortado_nao_vale(self):
        """
        Encostar num curso que não chega a lugar nenhum não faz a água chegar.
        Sem esta regra, dois afluentes cortados se validariam um ao outro.
        """
        rs = {r["rio"]: r for r in self.com({
            "itajai-mirim": [[[-48.70, -26.93], [-48.60, -26.93]]],
            "solto-a": [[[-48.65, -26.99], [-48.65, -26.97]]],
            "solto-b": [[[-48.65, -26.9701], [-48.65, -26.96]]],
        })}
        self.assertTrue(rs["solto-a"]["cortado"])
        self.assertTrue(rs["solto-b"]["cortado"])

    def test_quem_chega_DIRETO_nao_ganha_via(self):
        rs = {r["rio"]: r for r in self.com({
            "itajai-mirim": [[[-48.70, -26.93], [-48.60, -26.93]]],
            "ribeirao-x": [[[-48.65, -26.95], [-48.65, -26.9301]]],
        })}
        self.assertEqual(rs["ribeirao-x"]["via"], [])

    def test_o_tronco_nao_e_avaliado_como_afluente(self):
        rs = self.com({
            "itajai-acu": [[[-48.70, -26.90], [-48.60, -26.90]]],
            "itajai-mirim": [[[-48.70, -26.93], [-48.60, -26.93]]],
        })
        self.assertEqual(rs, [])


class ContraOsDadosReais(unittest.TestCase):
    """
    A REGRA, não o retrato — e a troca tem história.

    Até 04/09/2026 aqui havia um retrato: "o Canhanduba é o buraco conhecido de
    578 m". O próprio comentário dele prescrevia o que fazer quando o vão
    fechasse — "apague este teste, deixe a regra valer para todos" —, mas o
    conserto (o Rio Conceição, que fecha o vão) entrou e o teste virou
    CONDICIONAL em vez disso:

        if (cf.RIOS / "rio-conceicao.geojson").exists():
            ...assertivas...

    Ou seja: apagar o `rio-conceicao.geojson` fazia a asserção SUMIR EM
    SILÊNCIO, e o conjunto inteiro dos testes continuava verde. Uma sabotagem
    encontrou isso — apagar aquele arquivo não punha um único teste vermelho,
    enquanto apagar o do Ribeirão da Murta punha dois. Guarda que desaparece
    junto com aquilo que ela guarda não é guarda.

    Agora vale a regra: NENHUM afluente desenhado pode ficar cortado. Ela cobre
    os que existem hoje e os que entrarem depois, e não precisa de manutenção
    quando um vão fecha.
    """

    def setUp(self):
        self.rs = {r["rio"]: r for r in cf.avaliar()}

    def test_NENHUM_afluente_desenhado_fica_cortado(self):
        # Afluente cortado AFIRMA que a água pára ali — e o mapa desenha essa
        # afirmação. É a regra inteira, sem lista de exceções.
        cortados = [f"{r} a {d['metros']} m de {d['chega_em']}"
                    for r, d in sorted(self.rs.items()) if d["cortado"]]
        self.assertEqual(
            cortados, [],
            "afluente desenhado sem chegar no rio que o recebe: " + "; ".join(cortados)
            + ". Rebaixe o trecho que falta pelo Overpass "
              "(docs/tracado-ribeiroes.md) — nunca desenhe o vão à mão.",
        )

    def test_cada_afluente_chega_no_tronco_que_o_cadastro_diz(self):
        # Chegar não basta: chegar no rio ERRADO seria traçado trocado.
        esperado = {
            "ribeirao-murta": "itajai-acu",
            "ribeirao-canhanduba": "itajai-mirim",
            "rio-conceicao": "itajai-mirim",
        }
        for rio, tronco in esperado.items():
            with self.subTest(rio=rio):
                self.assertIn(rio, self.rs, f"{rio} sumiu de data/rios/")
                self.assertEqual(self.rs[rio]["chega_em"], tronco)

    def test_o_Canhanduba_chega_PELO_Rio_Conceicao(self):
        """
        O caminho importa, não só o destino.

        O trecho final do Canhanduba não se chama Canhanduba: é o **Rio
        Conceição** (3 vias, ~650 m de canal para 578 m em linha reta —
        sinuosidade 1,12, normal em várzea). Sem ele desenhado, o Canhanduba
        morre a 578 m do Mirim. Cobrar a VIA, e não só o "não cortado", é o que
        faz apagar aquele arquivo virar teste vermelho.
        """
        self.assertEqual(self.rs["ribeirao-canhanduba"]["via"], ["rio-conceicao"])


if __name__ == "__main__":
    unittest.main()
