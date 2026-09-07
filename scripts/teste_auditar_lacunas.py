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


class PorQueFaltaOElo(unittest.TestCase):
    """
    A auditoria imprimia os dez elos ausentes como lista de tarefas. Um deles
    não é: Indaial -> Blumenau tem as duas pontas na JICA e a diferença é ZERO
    ou NEGATIVA, porque o Benedito entra entre as duas e adianta o pico de
    baixo. Preencher um positivo ali daria a quem está em Blumenau horas que
    não existem — que é a única coisa que este projeto não pode fazer.
    """

    FONTE = {
        "cidades_na_tabela": ["taio", "ibirama", "rio-do-sul", "timbo", "ituporanga",
                              "brusque", "indaial", "blumenau", "gaspar", "ilhota", "itajai"],
        "relogio_proprio": ["timbo", "ibirama", "brusque"],
    }
    TABELA = {
        "indaial":  {"5": 10, "10": 9, "25": 8, "50": 8},
        "blumenau": {"5": 10, "10": 9, "25": 7, "50": 7},
        "gaspar":   {"5": 12, "10": 11, "25": 9, "50": 8},
        "timbo":    {"5": 0, "10": 0, "25": 0, "50": 0},
    }

    def classe(self, de, para):
        return al.por_que_falta_o_elo(de, para, self.FONTE, self.TABELA)[0]

    def motivos(self, de, para):
        return al.por_que_falta_o_elo(de, para, self.FONTE, self.TABELA)[1]

    def test_indaial_blumenau_nao_e_tempo_de_transito(self):
        self.assertEqual(self.classe("indaial", "blumenau"), "nao_positivo")
        texto = " ".join(self.motivos("indaial", "blumenau"))
        self.assertIn("-1 h", texto, "tem de MOSTRAR o número negativo, não só dizer que é")
        self.assertIn("Benedito", texto)

    def test_diferenca_positiva_em_todas_as_colunas_nao_vira_nao_positivo(self):
        """Blumenau -> Gaspar é +2/+2/+2/+1: existe e é um trânsito de verdade."""
        self.assertEqual(self.classe("blumenau", "gaspar"), "sem_tempo_de_fonte")

    def test_cidade_fora_da_tabela_vale_procurar(self):
        self.assertEqual(self.classe("rio-do-sul", "lontras"), "sem_tempo_de_fonte")
        self.assertIn("não lista lontras", " ".join(self.motivos("rio-do-sul", "lontras")))

    def test_relogio_proprio_de_uma_ponta_e_dito(self):
        self.assertIn("relógio próprio", " ".join(self.motivos("timbo", "indaial")))

    def test_guabiruba_brusque_nao_e_classificado_por_relogio_proprio_sozinho(self):
        """
        Erro real da primeira versão: olhava `relogio_proprio` sem checar antes
        se a cidade está na tabela, e classificou Guabiruba -> Brusque como
        relógio próprio. O relógio próprio de Brusque vale em relação ao AÇU;
        Guabiruba é vizinha dela no MIRIM. O que falta ali é a JICA não listar
        Guabiruba, e isso tem de aparecer.
        """
        motivos = " ".join(self.motivos("guabiruba", "brusque"))
        self.assertIn("não lista guabiruba", motivos)

    def test_os_dois_motivos_aparecem_quando_os_dois_valem(self):
        """Rio dos Cedros -> Timbó: a de cima não está na tabela E a de baixo
        tem relógio próprio. Ficar com um só esconde metade do problema."""
        motivos = self.motivos("rio-dos-cedros", "timbo")
        self.assertEqual(len(motivos), 2, motivos)

    def test_bate_com_o_transito_real_do_repositorio(self):
        """A classificação tem de rodar sobre o dado de verdade sem estourar."""
        t = al.le("transito.json")["_meta"]["origem_das_faixas"]
        tabela = t["tabela_7_5_1"]["matriz_horas_por_periodo_de_retorno"]
        classe, motivos = al.por_que_falta_o_elo("indaial", "blumenau", t, tabela)
        self.assertEqual(classe, "nao_positivo")
        self.assertTrue(motivos)


class MinimoDaPrevisao(unittest.TestCase):
    def test_bate_com_o_que_o_claude_md_manda(self):
        """< 5 eventos = 'dados insuficientes', não estimativa."""
        self.assertEqual(al.PARES_MINIMOS, 5)


if __name__ == "__main__":
    unittest.main()
