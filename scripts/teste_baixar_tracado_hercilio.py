"""Trava o download do traçado do Rio Hercílio / Itajaí do Norte (scripts/baixar_tracado_hercilio.py)."""
import json
import unittest

import baixar_tracado_hercilio as bh

IBIRAMA = bh.pino_de_ibirama()
ACU = [(-49.47, -27.15), (-49.40, -27.10)]


def way(nome, pontos):
    return {"type": "way", "tags": {"name": nome, "waterway": "river"},
            "geometry": [{"lon": lo, "lat": la} for lo, la in pontos]}


#: Montante (Itajaí do Norte) → Ibirama → chegada ao Açu.
NORTE = way("Rio Itajaí do Norte", [(-49.70, -26.95), (-49.60, -27.00), (-49.55, -27.04)])
HERCILIO = way("Rio Hercílio", [(-49.55, -27.04), (IBIRAMA[0], IBIRAMA[1]), (-49.471, -27.149)])


class Resposta:
    def __init__(self, status, corpo):
        self.status_code, self.text, self.headers = status, corpo, {}


class Conferencia(unittest.TestCase):
    def test_rio_inteiro_passa(self):
        self.assertEqual(bh.conferir(bh.linhas([NORTE, HERCILIO]), ACU, IBIRAMA), [])

    def test_so_um_dos_nomes_e_recusado(self):
        for so in ([NORTE], [HERCILIO]):
            self.assertTrue(any("metade" in p for p in bh.conferir(bh.linhas(so), ACU, IBIRAMA)))

    def test_nao_chega_ao_acu_ou_nao_passa_em_ibirama(self):
        longe = [(-49.0, -27.6)]
        self.assertTrue(any("não chega ao Açu" in p for p in bh.conferir(bh.linhas([NORTE, HERCILIO]), longe, IBIRAMA)))
        self.assertTrue(any("Ibirama" in p for p in bh.conferir(bh.linhas([NORTE, HERCILIO]), ACU, (-50.0, -26.5))))

    def test_outros_rios_e_ways_sem_geometria_ficam_de_fora(self):
        por_nome = bh.linhas([NORTE, way("Rio Itajaí do Oeste", [(-49.9, -27.1), (-49.8, -27.2)]),
                              {"type": "way", "tags": {"name": "Rio Hercílio"}}])
        self.assertEqual(list(por_nome), ["Rio Itajaí do Norte"])

    def test_a_consulta_pede_os_dois_nomes_e_o_pino_e_o_do_cadastro(self):
        q = bh.consulta()
        self.assertIn("Itajaí do Norte", q)
        self.assertIn("Hercílio", q)
        self.assertEqual(IBIRAMA, (-49.52, -27.057))


class Busca(unittest.TestCase):
    def test_espera_na_fila_e_troca_de_espelho_em_corpo_estranho(self):
        respostas = iter([Resposta(504, "fila"), Resposta(200, "<html>limite</html>"),
                          Resposta(200, json.dumps({"elements": [NORTE]}))])
        esperas = []
        dados, espelho = bh.buscar(transporte=lambda *a: next(respostas), dormir=esperas.append, avisar=lambda *a: None)
        self.assertEqual(len(dados["elements"]), 1)
        self.assertEqual(espelho, bh.ESPELHOS[1])
        self.assertEqual(esperas, [bh.BACKOFF_BASE_S])

    def test_timeout_espera_e_tenta_de_novo_sem_derrubar_a_rodada(self):
        def transporte(*a, _r=iter([TimeoutError("lido demais"), Resposta(200, json.dumps({"elements": [NORTE]}))])):
            r = next(_r)
            if isinstance(r, Exception):
                raise r
            return r
        esperas = []
        dados, espelho = bh.buscar(transporte=transporte, dormir=esperas.append, avisar=lambda *a: None)
        self.assertEqual(len(dados["elements"]), 1)
        self.assertEqual(espelho, bh.ESPELHOS[0])
        self.assertEqual(esperas, [bh.BACKOFF_BASE_S])

    def test_o_registro_guarda_espelho_tentativa_e_motivo(self):
        respostas = iter([Resposta(504, "fila"), Resposta(200, json.dumps({"elements": []}))])
        registro = []
        bh.buscar_consulta("q", transporte=lambda *a: next(respostas), dormir=lambda s: None,
                           avisar=lambda *a: None, registro=registro)
        self.assertEqual(registro, [
            {"espelho": bh.ESPELHOS[0], "tentativa": 1, "resultado": "HTTP 504"},
            {"espelho": bh.ESPELHOS[0], "tentativa": 2, "resultado": "ok"},
        ])

    def test_todos_os_espelhos_sem_resposta_vira_systemexit_com_o_motivo(self):
        def transporte(*a):
            raise TimeoutError("lido demais")
        with self.assertRaises(SystemExit) as ctx:
            bh.buscar(transporte=transporte, dormir=lambda s: None, avisar=lambda *a: None)
        self.assertIn("TimeoutError", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
