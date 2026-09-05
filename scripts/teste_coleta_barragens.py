#!/usr/bin/env python3
"""Testes do coletor das barragens Oeste e Sul.

O que este dado decide é a leitura do nível de Rio do Sul e Taió: comportas
fechadas com o rio subindo significa que a barragem está segurando; abertas com
o rio estável significa que o pico passou. Errar aqui inverte a mensagem.

As quatro armadilhas do corpo têm teste próprio, cada guarda sabotada:
altitude confundida com régua, UTC lido como Brasília, percentual recalculado
por conta, e `vertido` lido como vazão.

    python3 scripts/teste_coleta_barragens.py
"""

import json
import unittest

import coleta_barragens as cb
from coleta_barragens import converter, numero, para_brasilia

#: O corpo REAL, capturado na VPS em 05/09/2026 17:05 UTC.
OESTE = {
    "station_id": "d6e340c8", "name": "Barragem Oeste Taió", "river_name": "Itajaí do Oeste",
    "latitude": -27.09743881225586, "longitude": -50.03879165649414,
    "measured_at": "2026-09-05T17:05:06.43Z",
    "montante_m": 353.6600036621094, "nivel_m": 14.660003662109375, "gauge_zero_m": 339,
    "jusante_m": 5.559999942779541, "percent_use": 31.793886184692383, "vertido": 0,
    "capacidade_atual": 31.78116798400879, "capacidade_maxima": 99.95999908447266,
    "comportas": [{"key": f"comporta_{i}", "nome": f"C{i}", "aberta": True} for i in range(1, 8)],
    "comportas_abertas": 7, "comportas_total": 7,
}
SUL = {
    "station_id": "60c6cf33", "name": "Barragem Sul Ituporanga", "river_name": "Itajaí do Sul",
    "latitude": -27.503854751586914, "longitude": -49.55359649658203,
    "measured_at": "2026-09-05T17:04:55.734Z",
    "montante_m": 392.5799865722656, "nivel_m": 22.579986572265625, "gauge_zero_m": 370,
    "jusante_m": 3.9800000190734863, "percent_use": 35.47340774536133, "vertido": 0,
    "capacidade_atual": 36.843589782714844, "capacidade_maxima": 104.02999877929688,
    "comportas": [{"key": f"comporta_{i}", "nome": f"C{i}", "aberta": True} for i in range(1, 6)],
    "comportas_abertas": 5, "comportas_total": 5,
}


def so(bruto):
    b, _ = converter([bruto])
    return b[0]


class AltitudeNaoERegua(unittest.TestCase):
    """`montante_m` 353,66 é altura acima do MAR. A régua marca 14,66."""

    def test_os_dois_niveis_saem_com_nomes_que_nao_se_confundem(self):
        b = so(OESTE)
        self.assertAlmostEqual(b["altitude_montante_m"], 353.66, places=2)
        self.assertAlmostEqual(b["nivel_na_regua_da_barragem_m"], 14.66, places=2)
        self.assertEqual(b["zero_da_regua_m"], 339)

    def test_a_relacao_regua_igual_altitude_menos_zero_vale_nas_duas(self):
        for bruto in (OESTE, SUL):
            b = so(bruto)
            self.assertAlmostEqual(
                b["altitude_montante_m"] - b["zero_da_regua_m"],
                b["nivel_na_regua_da_barragem_m"], places=3, msg=b["nome"])

    def test_relacao_quebrada_vira_AVISO_e_nao_passa_calada(self):
        # Sabotagem: a fonte muda o significado de `nivel_m`. Sem esta guarda, o
        # resto das contas seguiria valendo em cima de um campo que virou outra
        # coisa.
        estragado = dict(OESTE, nivel_m=99.0)
        _, avisos = converter([estragado])
        self.assertTrue(any("mudou o significado" in a for a in avisos), avisos)

    def test_a_diferenca_de_escala_e_grande_o_bastante_para_matar_uma_comparacao(self):
        # 353 m contra uma régua de rio de ~5 m. Se alguém trocar os campos, o
        # erro não é sutil — e é por isso que os nomes têm que gritar.
        b = so(OESTE)
        self.assertGreater(b["altitude_montante_m"] / b["nivel_na_regua_da_barragem_m"], 20)


class OCarimboVemEmUTC(unittest.TestCase):
    def test_UTC_com_Z_vira_Brasilia_sem_fuso(self):
        # 17:05 UTC é 14:05 em Brasília. Gravar o UTC como se fosse local
        # envelheceria a leitura em 3 h na tela do morador.
        self.assertEqual(para_brasilia("2026-09-05T17:05:06.43Z"), "2026-09-05T14:05:06")

    def test_as_duas_barragens_convertem(self):
        self.assertEqual(so(OESTE)["medido_em"], "2026-09-05T14:05:06")
        self.assertEqual(so(SUL)["medido_em"], "2026-09-05T14:04:55")

    def test_carimbo_ilegivel_vira_None_e_nao_a_hora_de_agora(self):
        self.assertIsNone(para_brasilia("ontem"))
        self.assertIsNone(para_brasilia(None))
        self.assertIsNone(so(dict(OESTE, measured_at=None))["medido_em"])


class OPercentualNaoERecalculado(unittest.TestCase):
    def test_vale_o_publicado_mesmo_quando_diverge(self):
        # Na Sul o publicado (35,47%) diverge 0,06 pp da razão das capacidades.
        # Recalcular inventaria um número que a fonte não afirma.
        b = so(SUL)
        self.assertAlmostEqual(b["percent_use"], 35.4734, places=3)
        self.assertNotAlmostEqual(b["percent_use"], 35.4163, places=3)

    def test_a_divergencia_fica_registrada_em_vez_de_escondida(self):
        self.assertAlmostEqual(so(SUL)["percent_use_divergencia_pp"], 0.0571, places=3)
        self.assertAlmostEqual(so(OESTE)["percent_use_divergencia_pp"], 0.0, places=3)

    def test_divergencia_grande_vira_aviso(self):
        _, avisos = converter([dict(SUL, percent_use=90.0)])
        self.assertTrue(any("percent_use" in a for a in avisos), avisos)


class AsComportas(unittest.TestCase):
    def test_conta_pela_LISTA_e_nao_pelo_campo_derivado(self):
        # Sabotagem: a fonte diz 7 abertas, mas a lista tem uma fechada. O que
        # vale é a lista, e a discordância vira aviso.
        lista = [dict(c) for c in OESTE["comportas"]]
        lista[3]["aberta"] = False
        b, avisos = converter([dict(OESTE, comportas=lista)])
        self.assertEqual(b[0]["comportas_abertas"], 6, "seguiu o campo derivado, não a lista")
        self.assertTrue(any("comportas_abertas=7" in a for a in avisos), avisos)

    def test_a_fechada_e_nomeada_para_a_tela_poder_dizer_qual(self):
        lista = [dict(c) for c in OESTE["comportas"]]
        lista[3]["aberta"] = False
        b = converter([dict(OESTE, comportas=lista)])[0][0]
        fechadas = [c["nome"] for c in b["comportas"] if not c["aberta"]]
        self.assertEqual(fechadas, ["C4"])

    def test_aberta_ausente_conta_como_FECHADA_e_nao_como_aberta(self):
        # Campo faltando é "não sei". Contar como aberta diria "esvaziando"
        # quando pode estar segurando — a direção que engana.
        lista = [{"nome": "C1"}, {"nome": "C2", "aberta": True}]
        b = converter([dict(OESTE, comportas=lista, comportas_abertas=1, comportas_total=2)])[0][0]
        self.assertEqual(b["comportas_abertas"], 1)
        self.assertFalse(b["comportas"][0]["aberta"])

    def test_os_totais_reais_das_duas_barragens(self):
        self.assertEqual((so(OESTE)["comportas_abertas"], so(OESTE)["comportas_total"]), (7, 7))
        self.assertEqual((so(SUL)["comportas_abertas"], so(SUL)["comportas_total"]), (5, 5))


class VertidoNaoEVazao(unittest.TestCase):
    def test_e_gravado_cru_com_o_nome_dizendo_que_e_bruto(self):
        b = so(OESTE)
        self.assertEqual(b["vertido_bruto"], 0)
        self.assertNotIn("vazao", json.dumps(b))

    def test_o_meta_avisa_que_o_significado_e_desconhecido(self):
        doc = cb.coletar(buscador=lambda _c: [OESTE, SUL], city_ids=(1,))
        self.assertIn("DESCONHECIDO", doc["_meta"]["vertido"])
        self.assertIn("NÃO é a vazão de saída", doc["_meta"]["vertido"])


class SobreOCorpoInteiro(unittest.TestCase):
    def test_as_duas_barragens_saem_sem_aviso_nenhum(self):
        barragens, avisos = converter([OESTE, SUL])
        self.assertEqual(len(barragens), 2)
        self.assertEqual(avisos, [], "o corpo real de 05/09 não deveria gerar aviso")

    def test_o_meta_avisa_da_altitude_e_do_fuso(self):
        doc = cb.coletar(buscador=lambda _c: [OESTE, SUL], city_ids=(1,))
        self.assertIn("NÍVEL DO MAR", doc["_meta"]["ALTITUDE_NAO_E_REGUA"])
        self.assertIn("Brasília", doc["_meta"]["fuso"])
        self.assertIn("UTC", doc["_meta"]["fuso"])

    def test_corpo_vazio_nao_inventa_barragem(self):
        self.assertEqual(converter([]), ([], []))
        self.assertEqual(converter({"erro": "x"}), ([], []))

    def test_numero_recusa_booleano(self):
        # `isinstance(True, int)` é True em Python, e True não é metro.
        self.assertIsNone(numero(True))
        self.assertEqual(numero(3), 3.0)




class VariasCidadesDeInteresse(unittest.TestCase):
    """
    O coletor aceita N cidades e deduplica. A hipótese original ("a Norte vem por
    uma cidade a jusante dela") foi REFUTADA em 05/09/2026: Ibirama e Blumenau
    devolvem `[]`; `city_id` é cadastro do município cliente, não hidrologia. O
    mecanismo fica, porque um município cliente pode um dia devolver a Norte.
    """

    def test_a_mesma_barragem_por_duas_cidades_entra_UMA_vez(self):
        # Rio do Sul e Ibirama devolvem as duas do Alto Vale; sem dedupe o site
        # mostraria "4 barragens" e contaria as comportas em dobro.
        doc = cb.coletar(buscador=lambda _c: [OESTE, SUL], city_ids=(4214805, 4207106))
        self.assertEqual(len(doc["barragens"]), 2)

    def test_barragem_que_so_uma_cidade_traz_entra_tambem(self):
        norte = dict(SUL, station_id="norte-x", name="Barragem Norte José Boiteux",
                     river_name="Itajaí do Norte")
        def buscador(cid):
            return [OESTE, SUL] if cid == 4214805 else [OESTE, SUL, norte]
        doc = cb.coletar(buscador=buscador, city_ids=(4214805, 4207106))
        nomes = sorted(b["nome"] for b in doc["barragens"])
        self.assertEqual(nomes, ["Barragem Norte José Boiteux", "Barragem Oeste Taió",
                                 "Barragem Sul Ituporanga"])

    def test_cidade_que_falha_vira_aviso_e_as_outras_seguem(self):
        def buscador(cid):
            if cid == 4207106:
                raise RuntimeError("404")
            return [OESTE, SUL]
        doc = cb.coletar(buscador=buscador, city_ids=(4214805, 4207106))
        self.assertEqual(len(doc["barragens"]), 2)
        self.assertTrue(any("4207106" in a for a in doc["_meta"]["avisos_da_fonte"]))

    def test_cidade_que_devolve_lista_vazia_vira_aviso_nao_silencio(self):
        # 05/09/2026: `dams?city_id=4207106` (Ibirama) devolveu `[]`. Sem aviso,
        # código errado e cidade sem barragem pareceriam coleta saudável.
        def buscador(cid):
            return [] if cid == 4207106 else [OESTE, SUL]
        doc = cb.coletar(buscador=buscador, city_ids=(4214805, 4207106))
        self.assertEqual(len(doc["barragens"]), 2)
        avisos = doc["_meta"]["avisos_da_fonte"]
        self.assertTrue(any("4207106" in a and "vazia" in a for a in avisos), avisos)

    def test_a_lista_de_cidades_tem_rio_do_sul_e_nenhuma_que_devolve_vazio(self):
        self.assertIn(4214805, cb.CITY_IDS)
        # Ibirama saiu porque devolve `[]`; voltar com ela seria pedido vazio a
        # cada coleta e aviso permanente no log. Só volta cidade que TRAGA a Norte.
        self.assertNotIn(4207106, cb.CITY_IDS)

    def test_meta_declara_que_a_norte_nao_esta(self):
        # Quem lê "12 de 12 comportas abertas" precisa saber que são DUAS das TRÊS
        # barragens da bacia. A ausência da Norte é dado, não omissão.
        doc = cb.coletar(buscador=lambda _c: [OESTE, SUL])
        cobertura = doc["_meta"]["cobertura"].upper()
        self.assertIn("NORTE", cobertura)
        self.assertIn("NÃO", cobertura)


if __name__ == "__main__":
    unittest.main()
