"""Trava o download dos afluentes (scripts/baixar_tracados_afluentes.py)."""
import unittest

import baixar_tracados_afluentes as ba

TIMBO = ba.pino("timbo")
ITUPORANGA = ba.pino("ituporanga")
TROMBUDO = ba.pino("trombudo-central")
ACU = [(-49.27, -26.92), (-49.63, -27.21)]


def way(nome, pontos):
    return {"type": "way", "tags": {"name": nome, "waterway": "river"},
            "geometry": [{"lon": lo, "lat": la} for lo, la in pontos]}


BENEDITO = way("Rio Benedito", [(-49.27, -26.75), TIMBO, (-49.271, -26.919)])
SUL = way("Rio Itajaí do Sul", [(-49.40, -27.70), ITUPORANGA, (-49.631, -27.209)])
TROMBUDO_W = way("Rio Trombudo", [(-49.85, -27.40), TROMBUDO, (-49.70, -27.25)])


class Conferencia(unittest.TestCase):
    def test_rio_que_chega_e_passa_pela_regua_e_aceito(self):
        self.assertEqual(ba.conferir("benedito", ba.linhas([BENEDITO], ("Rio Benedito",)), {"itajai-acu": ACU}, TIMBO), [])
        self.assertEqual(ba.conferir("itajai-do-sul", ba.linhas([SUL], ("Rio Itajaí do Sul",)), {"itajai-acu": ACU}, ITUPORANGA), [])

    def test_trombudo_pode_chegar_ao_itajai_do_sul_baixado_na_rodada(self):
        sul = [(-49.70, -27.251)]
        ls = ba.linhas([TROMBUDO_W], ("Rio Trombudo",))
        self.assertEqual(ba.conferir("trombudo", ls, {"itajai-acu": [(-48.9, -26.9)], "itajai-do-sul": sul}, TROMBUDO), [])
        self.assertTrue(any("não chega" in p for p in ba.conferir("trombudo", ls, {"itajai-acu": [(-48.9, -26.9)]}, TROMBUDO)))

    def test_nao_passa_pela_regua_e_recusado(self):
        ls = ba.linhas([BENEDITO], ("Rio Benedito",))
        self.assertTrue(any("régua de timbo" in p for p in ba.conferir("benedito", ls, {"itajai-acu": ACU}, (-49.0, -26.5))))

    def test_nome_parecido_nao_entra(self):
        self.assertEqual(ba.linhas([way("Ribeirão Benedito Novo", [(-49.3, -26.8), (-49.2, -26.9)])], ("Rio Benedito",)), [])
        self.assertTrue(any("nenhum way" in p for p in ba.conferir("benedito", [], {"itajai-acu": ACU}, TIMBO)))

    def test_consulta_pede_o_nome_exato_na_caixa_do_rio(self):
        q = ba.consulta("itajai-do-sul")
        self.assertIn('"^(Rio Itajaí do Sul)$"', q)
        self.assertIn('"^(river)$"', q)
        g = ba.consulta("guabiruba")
        self.assertIn('"^(Rio Guabiruba Norte|Rio Guabiruba)$"', g)
        self.assertIn("(-27.9,-49.8,-27.15,-49.1)", q)


class NovosDaInspecao(unittest.TestCase):
    """Rio dos Cedros chega ao Benedito; Guabiruba ao Mirim (06/10/2026)."""

    def test_rio_dos_cedros_chega_ao_benedito_baixado_na_rodada(self):
        rc = ba.pino("rio-dos-cedros")
        ls = ba.linhas([way("Rio dos Cedros", [(-49.30, -26.60), rc, (-49.27, -26.80)])], ("Rio dos Cedros",))
        self.assertEqual(ba.conferir("rio-dos-cedros", ls, {"benedito": [(-49.27, -26.801)]}, rc), [])
        self.assertTrue(ba.conferir("rio-dos-cedros", ls, {}, rc))

    def test_guabiruba_e_o_norte_da_estacao_ligado_ao_guabiruba_que_chega_ao_mirim(self):
        g = ba.pino("guabiruba")
        juncao = (-48.96326, -27.0958)
        norte = way("Rio Guabiruba Norte", [(-48.99211, -27.08118), g, juncao])
        baixo = way("Rio Guabiruba", [juncao, (-48.92983, -27.09784)])
        mirim = {"itajai-mirim": [(-48.92983, -27.09784)]}
        nomes = ba.RIOS["guabiruba"]["nomes"]
        self.assertEqual(ba.conferir("guabiruba", ba.linhas([norte, baixo], nomes), mirim, g), [])
        # O Sul entra no mesmo nó, mas não é o curso da estação: o nome não entra.
        self.assertEqual(ba.linhas([way("Rio Guabiruba Sul", [(-49.05, -27.13), juncao])], nomes), [])

    def test_pedaco_solto_perto_do_rio_de_baixo_nao_conta_como_chegada(self):
        g = ba.pino("guabiruba")
        norte = way("Rio Guabiruba Norte", [(-48.99211, -27.08118), g, (-48.96326, -27.0958)])
        solto = way("Rio Guabiruba", [(-48.95, -27.0959), (-48.92983, -27.09784)])   # não toca o Norte
        ls = ba.linhas([norte, solto], ba.RIOS["guabiruba"]["nomes"])
        problemas = ba.conferir("guabiruba", ls, {"itajai-mirim": [(-48.92983, -27.09784)]}, g)
        self.assertTrue(any("não chega" in p for p in problemas))

    def test_a_ordem_baixa_quem_recebe_antes(self):
        self.assertLess(ba.ORDEM.index("benedito"), ba.ORDEM.index("rio-dos-cedros"))
        self.assertLess(ba.ORDEM.index("itajai-do-sul"), ba.ORDEM.index("trombudo"))


class RodadaComOverpassFalhando(unittest.TestCase):
    """06/10/2026: um rio sem resposta não derruba a rodada; os outros seguem, e o relatório diz o porquê."""

    def test_rio_sem_resposta_nao_para_os_outros_e_mantem_o_ultimo_arquivo(self):
        import json as _json
        bruto = _json.loads((ba.BRUTOS / "tracado-benedito-osm.json").read_text(encoding="utf-8"))

        def buscar(texto, registro):
            if "Rio dos Cedros" in texto:
                registro.append({"espelho": "https://espelho/", "tentativa": 3, "resultado": "ReadTimeout: lido demais"})
                raise SystemExit("Nenhum espelho do Overpass respondeu com JSON.")
            registro.append({"espelho": "https://espelho/", "tentativa": 1, "resultado": "ok"})
            return bruto, "https://espelho/"

        rodada = ba.rodar(["rio-dos-cedros", "benedito"], buscar=buscar)
        self.assertEqual(rodada["rio-dos-cedros"]["situacao"], "sem_resposta")
        self.assertEqual(rodada["rio-dos-cedros"]["arquivo"], "mantido")
        self.assertIn("ReadTimeout", rodada["rio-dos-cedros"]["tentativas"][0]["resultado"])
        self.assertEqual(rodada["benedito"]["situacao"], "baixado")
        self.assertEqual(rodada["benedito"]["espelho"], "https://espelho/")
        aviso = ba.aviso_da_rodada(rodada)
        self.assertTrue(aviso.startswith("Coleta parcial: 1 de 2 rios baixados."))
        self.assertIn("rio-dos-cedros (último arquivo válido mantido)", aviso)

    def test_nenhum_rio_respondeu_avisa_e_nao_toca_arquivos(self):
        def buscar(texto, registro):
            raise SystemExit("fora do ar")
        rodada = ba.rodar(["benedito"], buscar=buscar)
        self.assertEqual(rodada["benedito"]["arquivo"], "mantido")
        self.assertTrue(ba.aviso_da_rodada(rodada).startswith("Coleta não realizada"))

    def test_rodada_completa_nao_avisa(self):
        self.assertIsNone(ba.aviso_da_rodada({"benedito": {"situacao": "baixado", "arquivo": "novo"}}))


if __name__ == "__main__":
    unittest.main()
