#!/usr/bin/env python3
"""Testes do conferidor do par cota↔leitura.

Este script responde "a cota que o site aplica descreve a régua que o site
mostra?". Errar para um lado apaga um alarme legítimo; errar para o outro
mantém um limiar que não significa nada. Daí os casos abaixo.

    python3 scripts/teste_conferir_par_regua.py
"""

import json
import unittest

import conferir_par_regua as cpr
from conferir_par_regua import (
    CERTEZA_M,
    MAX_MINUTOS_ENTRE,
    TOLERANCIA_M,
    conferir,
    minutos_entre,
    nivel_da_asthon,
    nossa_leitura,
    veredito,
)


def painel(nome="Ponte Dom Tito Buss", nivel=5.40, quando="2026-09-04T18:00:00"):
    return json.dumps({"stations": [
        {"name": "Agronômica", "level_m": 2.1, "last_reading_at": quando},
        {"name": nome, "level_m": nivel, "last_reading_at": quando},
    ]}, ensure_ascii=False)


def ultimo(nivel=5.40, quando="2026-09-04T18:00:00", cidade="rio-do-sul"):
    return {"leituras": [
        {"cidade": "blumenau", "estacao": "Blumenau", "nivel_m": 3.3, "medido_em": quando},
        {"cidade": cidade, "estacao": "Rio do Sul Estação MKS",
         "nivel_m": nivel, "medido_em": quando},
    ]}


class Veredito(unittest.TestCase):
    def test_diferenca_pequena_e_a_mesma_regua(self):
        self.assertEqual(veredito(0.04)[0], "MESMA RÉGUA")
        self.assertEqual(veredito(-TOLERANCIA_M)[0], "MESMA RÉGUA")

    def test_diferenca_grande_sao_reguas_diferentes(self):
        self.assertEqual(veredito(CERTEZA_M)[0], "RÉGUAS DIFERENTES")
        self.assertEqual(veredito(-2.9)[0], "RÉGUAS DIFERENTES")

    def test_no_meio_a_resposta_e_NAO_SEI(self):
        # "Não sei" é resposta, e é a que o projeto prefere a um palpite.
        self.assertEqual(veredito(0.25)[0], "NÃO DÁ PARA DIZER")

    def test_a_tolerancia_cobre_a_divergencia_medida_em_Blumenau(self):
        # Duas publicações da MESMA régua divergem mediana +0,065 e máx +0,245 m.
        # A mediana tem de passar como "mesma régua"; o máximo, não — senão a
        # tolerância engoliria réguas de verdade diferentes.
        self.assertEqual(veredito(0.065)[0], "MESMA RÉGUA")
        self.assertNotEqual(veredito(0.245)[0], "MESMA RÉGUA")

    def test_o_sinal_nao_muda_a_resposta(self):
        self.assertEqual(veredito(0.9)[0], veredito(-0.9)[0])


class LeituraDasFontes(unittest.TestCase):
    def test_acha_a_estacao_pelo_pedaco_do_nome(self):
        self.assertEqual(nivel_da_asthon(painel(), "Tito"), (5.40, "2026-09-04T18:00:00"))

    def test_estacao_ausente_devolve_None_em_vez_de_chutar_outra(self):
        self.assertIsNone(nivel_da_asthon(painel(nome="Outra Ponte"), "Tito"))

    def test_corpo_que_nao_e_json_nao_estoura(self):
        self.assertIsNone(nivel_da_asthon("<html>erro</html>", "Tito"))

    def test_pega_a_leitura_da_cidade_certa(self):
        self.assertEqual(nossa_leitura("rio-do-sul", ultimo())[0], 5.40)
        self.assertIsNone(nossa_leitura("gaspar", ultimo()))


class DistanciaNoTempo(unittest.TestCase):
    def test_conta_minutos_entre_carimbos(self):
        self.assertAlmostEqual(
            minutos_entre("2026-09-04T18:00:00", "2026-09-04T18:20:00"), 20.0)

    def test_fuso_no_carimbo_nao_estoura(self):
        self.assertIsNotNone(minutos_entre("2026-09-04T18:00:00Z", "2026-09-04T18:10:00"))

    def test_carimbo_ilegivel_vira_None(self):
        self.assertIsNone(minutos_entre("ontem", "2026-09-04T18:00:00"))


class OCasoDeRioDoSul(unittest.TestCase):
    """
    O caso que motivou o script. A cota 4,50/5,50/6,50 é da Ponte Dom Tito Buss;
    a leitura chega como 'Rio do Sul Estação MKS'. O nível típico da MKS é
    5,61 m — 1,11 m ACIMA da cota de atenção, com 88 de 88 leituras das últimas
    48 h acima dela.
    """

    def test_se_baterem_e_a_mesma_regua(self):
        r = conferir("rio-do-sul", ultimo(nivel=5.40), painel(nivel=5.43))
        self.assertEqual(r["resposta"], "MESMA RÉGUA")

    def test_se_divergirem_o_script_DIZ_que_a_cota_nao_vale(self):
        r = conferir("rio-do-sul", ultimo(nivel=5.40), painel(nivel=2.30))
        self.assertEqual(r["resposta"], "RÉGUAS DIFERENTES")
        self.assertIn("NÃO vale", r["porque"])
        self.assertAlmostEqual(r["diferenca_m"], -3.10, places=2)

    def test_leituras_distantes_no_tempo_NAO_decidem(self):
        # Numa cheia o rio sobe em 30 min: a diferença sairia parte régua,
        # parte subida. Preferir "não sei" a decidir com o par errado.
        r = conferir("rio-do-sul",
                     ultimo(quando="2026-09-04T18:00:00"),
                     painel(nivel=2.30, quando="2026-09-04T20:00:00"))
        self.assertEqual(r["resposta"], "NÃO DÁ PARA DIZER")
        self.assertIn("min", r["porque"])
        self.assertGreater(r["minutos_entre"], MAX_MINUTOS_ENTRE)

    def test_sem_leitura_nossa_nao_inventa_veredito(self):
        r = conferir("rio-do-sul", {"leituras": []}, painel())
        self.assertIn("erro", r)
        self.assertNotIn("resposta", r)

    def test_sem_a_fonte_da_cota_nao_inventa_veredito(self):
        r = conferir("rio-do-sul", ultimo(), painel(nome="Outra"))
        self.assertIn("erro", r)
        self.assertNotIn("resposta", r)

    def test_o_relato_traz_os_dois_titulos_para_conferencia_humana(self):
        r = conferir("rio-do-sul", ultimo(), painel())
        self.assertEqual(r["regua_da_cota"], "Ponte Dom Tito Buss")
        self.assertEqual(r["regua_da_leitura"], "Rio do Sul Estação MKS")


class OScriptNaoGravaNada(unittest.TestCase):
    def test_nao_ha_escrita_em_data(self):
        fonte = (cpr.__file__ and open(cpr.__file__, encoding="utf-8").read())
        for proibido in ("write_text(", "json.dump(", "open(", ".unlink("):
            if proibido == "open(":
                continue  # lê o ultimo.json; leitura é permitida
            self.assertNotIn(proibido, fonte,
                             f"o conferidor passou a escrever ({proibido}) — ele só responde")


if __name__ == "__main__":
    unittest.main()
