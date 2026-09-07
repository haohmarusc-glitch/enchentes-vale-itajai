#!/usr/bin/env python3
"""
Testes da auditoria de lacunas.

O relatório existe para ORDENAR a busca. Errar a topologia inverte o pedido —
mandar ofício a Ascurra por um elo que na verdade falta em Indaial —, e errar a
contagem de cotas apaga um buraco real da lista. Os dois casos estão travados
aqui.
"""
import unittest

import auditar_lacunas as al


def cidade(id_, **campos):
    base = {"id": id_, "nome": id_.title(), "cotas_m": {}, "coordenadas": [-27.0, -49.0]}
    base.update(campos)
    return base


class ProximaAJusante(unittest.TestCase):
    """O Açu é ÁRVORE, não fila: a posição vem de ramo + ordem_no_ramo."""

    def setUp(self):
        self.est = {
            "rios": {
                "itajai-acu": {
                    "_topologia": {
                        "tronco_sequencia": ["rio-do-sul", "indaial", "itajai"],
                        "cabeceiras_paralelas": ["taio", "ituporanga"],
                        "confluencia_cabeceiras": {"nasce": "rio-do-sul"},
                        "afluentes_laterais": [
                            {"id": "timbo", "entra_perto_de": "indaial"}
                        ],
                    },
                    "cidades": [
                        cidade("taio", ramo="oeste", ordem_no_ramo=1),
                        cidade("ituporanga", ramo="sul", ordem_no_ramo=1),
                        cidade("rio-do-sul", ramo="tronco_acu", ordem_no_ramo=1),
                        cidade("indaial", ramo="tronco_acu", ordem_no_ramo=2),
                        cidade("itajai", ramo="tronco_acu", ordem_no_ramo=3),
                        cidade("timbo", ramo="benedito", ordem_no_ramo=1),
                        cidade("solta"),
                    ],
                },
                "itajai-mirim": {
                    "cidades": [
                        cidade("brusque", ordem=1),
                        cidade("itajai", ordem=2),
                    ]
                },
            }
        }

    def jusante(self, rio, id_):
        c = next(x for x in self.est["rios"][rio]["cidades"] if x["id"] == id_)
        return al.proxima_a_jusante(self.est, rio, c)

    def test_tronco_segue_a_sequencia(self):
        self.assertEqual(self.jusante("itajai-acu", "rio-do-sul"), "indaial")

    def test_foz_nao_tem_jusante(self):
        self.assertIsNone(self.jusante("itajai-acu", "itajai"))

    def test_cabeceiras_paralelas_caem_na_confluencia(self):
        """Taió e Ituporanga são PARALELAS: nenhuma é jusante da outra."""
        self.assertEqual(self.jusante("itajai-acu", "taio"), "rio-do-sul")
        self.assertEqual(self.jusante("itajai-acu", "ituporanga"), "rio-do-sul")

    def test_afluente_lateral_entra_onde_a_fonte_declara(self):
        self.assertEqual(self.jusante("itajai-acu", "timbo"), "indaial")

    def test_cidade_sem_posicao_nao_ganha_jusante_inventado(self):
        """Trombudo Central é o caso real: a fonte diz o rio, não a confluência."""
        self.assertIsNone(self.jusante("itajai-acu", "solta"))

    def test_rio_em_fila_usa_ordem(self):
        self.assertEqual(self.jusante("itajai-mirim", "brusque"), "itajai")


class ContagemDeCotas(unittest.TestCase):
    """Cota incompleta não é o mesmo buraco que cota ausente."""

    def test_faixas_essenciais_sao_atencao_e_alerta(self):
        self.assertEqual(al.FAIXAS_ESSENCIAIS, ("atencao", "alerta"))

    def test_cota_so_de_atencao_nao_conta_como_completa(self):
        """Brusque é o caso real: tem atenção e inundação, falta alerta."""
        cotas = {"atencao": 3.0, "inundacao": 5.0}
        self.assertFalse(all(f in cotas for f in al.FAIXAS_ESSENCIAIS))
        self.assertTrue(bool(cotas))


class MinimoDaPrevisao(unittest.TestCase):
    def test_bate_com_o_que_o_claude_md_manda(self):
        """< 5 eventos = 'dados insuficientes', não estimativa."""
        self.assertEqual(al.PARES_MINIMOS, 5)


if __name__ == "__main__":
    unittest.main()
