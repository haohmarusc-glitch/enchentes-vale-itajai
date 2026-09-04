#!/usr/bin/env python3
"""
Testes do encadeamento por conectividade.

O que ele resolve: o trecho final do Canhanduba tem outro nome no OSM, ou
nenhum, então casar por NOME não o alcança. Casar por conectividade alcança —
desde que "conectado" seja definido com cuidado. Estes testes fixam essa
definição, sem rede.
"""
import unittest

import baixar_vao_canhanduba as bv


def via(id_, pontos, nome=None, tipo="stream"):
    return {"type": "way", "id": id_,
            "geometry": [{"lon": p[0], "lat": p[1]} for p in pontos],
            "tags": {"waterway": tipo, **({"name": nome} if nome else {})}}


# ~0,001 grau de longitude ≈ 99 m nesta latitude, e CHEGOU_M é 100 — pontos
# vizinhos a 99 m fariam a PRIMEIRA via já contar como "chegou", e o teste de
# encadeamento passaria sem encadear. Por isso o passo aqui é 0,005 ≈ 500 m.
A = (-48.700, -26.940)
B = (-48.695, -26.940)
C = (-48.690, -26.940)
D = (-48.685, -26.940)


class Encadear(unittest.TestCase):
    def test_uma_via_que_toca_a_origem_e_chega_no_alvo(self):
        r = bv.encadear([via(1, [A, B])], A, [B])
        self.assertEqual([v["id"] for v in r], [1])

    def test_encadeia_DUAS_vias_anonimas_ate_o_alvo(self):
        """O caso real: o vão é feito de trechos sem nome, um depois do outro."""
        r = bv.encadear([via(1, [A, B]), via(2, [B, C])], A, [C])
        self.assertEqual([v["id"] for v in r], [1, 2])

    def test_via_invertida_tambem_liga(self):
        """O OSM não orienta as vias; a ponta que toca pode ser qualquer uma."""
        r = bv.encadear([via(1, [B, A])], A, [B])
        self.assertEqual([v["id"] for v in r], [1])

    def test_via_solta_NAO_entra_na_cadeia(self):
        longe = (-48.60, -26.80)
        r = bv.encadear([via(9, [longe, (-48.601, -26.80)]), via(1, [A, B])], A, [B])
        self.assertEqual([v["id"] for v in r], [1])

    def test_sem_caminho_devolve_VAZIO_e_nao_inventa(self):
        """
        A regra que mais importa: sem cadeia, nada. Uma reta entre a ponta e o
        rio seria geografia inventada num mapa de enchente.
        """
        self.assertEqual(bv.encadear([via(1, [C, D])], A, [D]), [])

    def test_prefere_a_MENOR_cadeia(self):
        elementos = [via(1, [A, D]), via(2, [A, B]), via(3, [B, C]), via(4, [C, D])]
        r = bv.encadear(elementos, A, [D])
        self.assertEqual(len(r), 1, "menos elos, menos incerteza")

    def test_a_ponta_do_Canhanduba_e_a_que_olha_para_o_Mirim(self):
        try:
            p = bv.ponta_do_canhanduba()
        except SystemExit:
            self.skipTest("traçados ausentes neste checkout")
        mirim = [q for l in bv.vias_do_geojson("itajai-mirim") for q in l]
        self.assertLess(min(bv.m(p, q) for q in mirim), 700,
                        "a ponta escolhida não é a que encara o Mirim")


class Limites(unittest.TestCase):
    def test_TOCA_e_folga_de_digitalizacao_nao_de_geografia(self):
        self.assertLessEqual(bv.TOCA_M, 50, "acima disso, 'toca' vira palpite")

    def test_CHEGOU_bate_com_o_conferidor_de_afluentes(self):
        import conferir_afluentes_chegam as ca
        self.assertEqual(bv.CHEGOU_M, ca.LIMITE_M,
                         "os dois têm de concordar sobre o que é 'chegou no rio'")



class Resposta:
    """Uma resposta fingida, com o mínimo que `buscar` olha."""

    def __init__(self, status, texto, cabecalhos=None):
        self.status_code = status
        self.text = texto
        self.headers = cabecalhos or {}


class Insistencia(unittest.TestCase):
    """
    O 504 real de 04/09/2026 tinha de ser resolvido pelo script, não por alguém
    repetindo o comando na mão. A caixa aqui tem 1,7 x 1,3 km — não é peso de
    consulta, é fila do servidor, e fila passa.
    """

    def buscar(self, respostas, **kw):
        self.chamadas = []
        self.esperas = []

        def transporte(url, dados, cabecalhos, timeout):
            self.chamadas.append(url)
            return respostas.pop(0)

        return bv.buscar(bv.CAIXA, transporte=transporte,
                         dormir=self.esperas.append, avisar=lambda *_: None, **kw)

    def test_200_de_primeira_nao_espera_nada(self):
        r = self.buscar([Resposta(200, '{"elements": [{"id": 1}]}')])
        self.assertEqual(r, [{"id": 1}])
        self.assertEqual(self.esperas, [])

    def test_504_espera_e_tenta_de_novo_NO_MESMO_espelho(self):
        r = self.buscar([Resposta(504, "<html>fila</html>"),
                         Resposta(200, '{"elements": []}')])
        self.assertEqual(r, [])
        self.assertEqual(len(self.esperas), 1)
        self.assertEqual(self.chamadas[0], self.chamadas[1])

    def test_backoff_CRESCE(self):
        self.buscar([Resposta(504, "x"), Resposta(504, "x"),
                     Resposta(200, '{"elements": []}')])
        self.assertGreater(self.esperas[1], self.esperas[0])

    def test_Retry_After_do_servidor_vence_o_backoff_quando_e_maior(self):
        """Ignorar o pedido de calma é o caminho para levar bloqueio."""
        self.buscar([Resposta(429, "x", {"Retry-After": "60"}),
                     Resposta(200, '{"elements": []}')])
        self.assertGreaterEqual(self.esperas[0], 60)

    def test_esgotado_um_espelho_TROCA_de_espelho(self):
        respostas = [Resposta(504, "x")] * bv.TENTATIVAS_POR_ESPELHO
        respostas.append(Resposta(200, '{"elements": [{"id": 7}]}'))
        r = self.buscar(respostas)
        self.assertEqual(r, [{"id": 7}])
        self.assertNotEqual(self.chamadas[0], self.chamadas[-1])

    def test_404_NAO_espera_nem_insiste_no_mesmo_espelho(self):
        """4xx que não é 429 não melhora sozinho; insistir só castiga a fonte."""
        with self.assertRaises(SystemExit):
            self.buscar([Resposta(404, "sumiu")] * 9)
        self.assertEqual(self.esperas, [])
        self.assertEqual(len(self.chamadas), len(bv.ESPELHOS))

    def test_200_com_corpo_NAO_JSON_nao_e_repetido_no_mesmo_espelho(self):
        """Foi o caso do `curl`: 200 com HTML. Repetir não muda o corpo."""
        with self.assertRaises(SystemExit) as e:
            self.buscar([Resposta(200, "<html>não é json</html>")] * 9)
        self.assertIn("não é JSON", str(e.exception).replace("NÃO é JSON", "não é JSON"))
        self.assertEqual(len(self.chamadas), len(bv.ESPELHOS))

    def test_a_mensagem_final_mostra_o_que_veio(self):
        """Sem isso, o erro não ajuda a diagnosticar — foi o defeito do curl."""
        with self.assertRaises(SystemExit) as e:
            self.buscar([Resposta(504, "PAGINA-DE-FILA")] * 30)
        self.assertIn("PAGINA-DE-FILA", str(e.exception))

if __name__ == "__main__":
    unittest.main()
