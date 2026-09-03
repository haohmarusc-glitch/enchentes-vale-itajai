#!/usr/bin/env python3
"""Testes do coletor de maré.

O formato testado aqui é o que o `mares.js` do site consome — inclusive a
chave `astronimical_tides`, escrita com erro de digitação na própria API, e o
`tidelevel` em centímetros. Um erro de unidade aqui viraria maré de 120 m.

    python3 scripts/teste_coleta_mares.py
"""

import unittest
from datetime import datetime

from coleta_mares import (
    JANELA_PICO_H,
    extremos,
    instante,
    montar,
    serie_astronomica,
    serie_observada,
)


def curva(inicio: datetime, alturas, passo_min=30):
    """Resposta no formato da API, a partir de uma lista de alturas."""
    from datetime import timedelta
    return [
        {
            "datetime": (inicio + timedelta(minutes=i * passo_min)).strftime("%Y-%m-%d %H:%M:%S"),
            "date_formated": "irrelevante",
            "level": str(a),
        }
        for i, a in enumerate(alturas)
    ]


INICIO = datetime(2026, 8, 30, 0, 0)
# Meia maré semidiurna: sobe até 1,4 m, desce até 0,2 m, sobe de novo.
SEMIDIURNA = [0.4, 0.7, 1.0, 1.25, 1.4, 1.3, 1.05, 0.75, 0.45, 0.25, 0.2,
              0.3, 0.6, 0.95, 1.2, 1.35, 1.25, 1.0, 0.7, 0.4]


class TesteFormato(unittest.TestCase):
    def test_instante_aceita_os_formatos_plausiveis(self):
        for texto in ("2026-08-30T14:30:00", "2026-08-30 14:30:00", "30/08/2026 14:30"):
            self.assertEqual(instante(texto), datetime(2026, 8, 30, 14, 30), texto)

    def test_instante_recusa_lixo_em_vez_de_adivinhar(self):
        self.assertIsNone(instante("ontem à tarde"))
        self.assertIsNone(instante(""))

    def test_tidelevel_vem_em_centimetros(self):
        """O site divide por 100 para plotar. Errar isso vira maré de 120 metros."""
        obs = serie_observada({"tides": [
            {"datetime": "2026-08-30 10:00:00", "date_formated": "x", "tidelevel": "120"},
        ]})
        self.assertEqual(len(obs), 1)
        self.assertAlmostEqual(obs[0]["altura_m"], 1.20)

    def test_level_astronomico_ja_vem_em_metros(self):
        ast = serie_astronomica({"astronimical_tides": curva(INICIO, [1.2])})
        self.assertAlmostEqual(ast[0]["altura_m"], 1.2)

    def test_altura_implausivel_e_descartada(self):
        ast = serie_astronomica({"astronimical_tides": [
            {"datetime": "2026-08-30 10:00:00", "level": "97.5"},
            {"datetime": "2026-08-30 11:00:00", "level": "1.1"},
        ]})
        self.assertEqual([p["altura_m"] for p in ast], [1.1])

    def test_resposta_vazia_nao_quebra(self):
        self.assertEqual(serie_astronomica({"tides": [], "astronimical_tides": []}), [])
        self.assertEqual(serie_observada({"tides": [], "astronimical_tides": []}), [])
        self.assertEqual(serie_astronomica({}), [])


class TestePreamares(unittest.TestCase):
    def setUp(self):
        self.serie = serie_astronomica({"astronimical_tides": curva(INICIO, SEMIDIURNA)})

    def test_acha_as_duas_preamares_da_curva(self):
        picos = extremos(self.serie, maximos=True)
        self.assertEqual([p["altura_m"] for p in picos], [1.4, 1.35])

    def test_acha_a_baixa_mar_entre_elas(self):
        vales = extremos(self.serie, maximos=False)
        self.assertEqual([p["altura_m"] for p in vales], [0.2])

    def test_o_horario_da_preamar_e_o_do_ponto_mais_alto(self):
        picos = extremos(self.serie, maximos=True)
        self.assertEqual(picos[0]["quando"], datetime(2026, 8, 30, 2, 0))

    def test_curva_plana_nao_tem_preamar(self):
        plana = serie_astronomica({"astronimical_tides": curva(INICIO, [1.0] * 10)})
        self.assertEqual(extremos(plana, maximos=True), [])

    def test_serie_curta_demais_nao_gera_preamar(self):
        curta = serie_astronomica({"astronimical_tides": curva(INICIO, [0.5, 1.0])})
        self.assertEqual(extremos(curta, maximos=True), [])

    def test_duas_leituras_da_mesma_mare_viram_uma_preamar(self):
        """Pontos empatados dentro da janela são a mesma maré alta."""
        from datetime import timedelta
        assert JANELA_PICO_H >= 1
        serie = serie_astronomica({"astronimical_tides": curva(
            INICIO, [0.4, 0.9, 1.30, 1.30, 0.9, 0.4], passo_min=20)})
        picos = extremos(serie, maximos=True)
        self.assertEqual(len(picos), 1)


class TesteMontagem(unittest.TestCase):
    def test_arquivo_sai_no_formato_que_o_site_le(self):
        d = montar(
            serie_astronomica({"astronimical_tides": curva(INICIO, SEMIDIURNA)}),
            serie_observada({"tides": []}),
        )
        self.assertEqual(d["porto"], "Itajaí")
        self.assertEqual(len(d["preamares"]), 2)
        self.assertRegex(d["preamares"][0]["quando"], r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}$")
        self.assertIn("fonte", d["_meta"])

    def test_meta_credita_a_defesa_civil_para_a_tela(self):
        # A tela (PainelMare.tsx) lê _meta.fonte_curta para creditar a fonte —
        # sem isto ela cairia num fallback genérico em vez do link real.
        d = montar([], [])
        self.assertEqual(d["_meta"]["fonte_curta"], "Defesa Civil de Itajaí")
        self.assertIn("fonte_url", d["_meta"])

    def test_fonte_vazia_produz_listas_vazias(self):
        d = montar([], [])
        self.assertEqual(d["preamares"], [])
        self.assertEqual(d["pontos_astronomicos"], 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
