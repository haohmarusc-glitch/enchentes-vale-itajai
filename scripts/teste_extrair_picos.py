#!/usr/bin/env python3
"""Testes da extração de picos.

O que estes casos protegem: o script transforma série bruta em registro de
enchente, e registro de enchente é o que a tela mostra. Um pico no horário
errado vira tempo de descida errado, que vira hora de sair de casa errada.

    python3 scripts/teste_extrair_picos.py
"""

import unittest
from datetime import datetime, timedelta

import json
import tempfile
import unittest.mock
from pathlib import Path

from extrair_picos import (
    INTERVALO_ENTRE_EVENTOS_H,
    MIN_LEITURAS,
    Leitura,
    ler_serie,
    limiar_da_estacao,
    separar_eventos,
)

INICIO = datetime(2026, 8, 1, 0, 0)


def serie(*valores, passo_h=1, inicio=INICIO):
    """Leituras espaçadas de `passo_h` horas."""
    return [Leitura(inicio + timedelta(hours=i * passo_h), v, "Blumenau")
            for i, v in enumerate(valores)]


class TesteSepararEventos(unittest.TestCase):
    def test_uma_cheia_vira_um_evento_com_o_maior_valor(self):
        eventos = separar_eventos(serie(3.0, 5.0, 7.2, 9.4, 8.1, 6.0, 4.0), limiar=6.0)
        self.assertEqual(len(eventos), 1)
        self.assertAlmostEqual(eventos[0].pico_m, 9.4)
        self.assertEqual(eventos[0].quando, INICIO + timedelta(hours=3))

    def test_o_horario_do_pico_e_o_da_maior_leitura(self):
        eventos = separar_eventos(serie(7.0, 6.5, 9.9, 7.1), limiar=6.0)
        self.assertEqual(eventos[0].quando, INICIO + timedelta(hours=2))

    def test_duas_cheias_separadas_por_dias_sao_dois_eventos(self):
        cheia1 = serie(7.0, 8.0, 7.0)
        depois = INICIO + timedelta(hours=3 + INTERVALO_ENTRE_EVENTOS_H + 5)
        cheia2 = serie(7.5, 9.0, 7.5, inicio=depois)
        eventos = separar_eventos(cheia1 + cheia2, limiar=6.0)
        self.assertEqual(len(eventos), 2)
        self.assertAlmostEqual(eventos[0].pico_m, 8.0)
        self.assertAlmostEqual(eventos[1].pico_m, 9.0)

    def test_rio_baixando_e_subindo_dentro_da_janela_e_um_evento_so(self):
        """A cheia oscila; enquanto ela não fica 18 h abaixo da cota, é a mesma."""
        eventos = separar_eventos(serie(7.0, 5.0, 5.5, 8.0, 7.0), limiar=6.0)
        self.assertEqual(len(eventos), 1)
        self.assertAlmostEqual(eventos[0].pico_m, 8.0)

    def test_leitura_isolada_acima_da_cota_nao_e_evento(self):
        """Um valor solto é mais provavelmente falha de sensor que cheia."""
        self.assertEqual(separar_eventos(serie(3.0, 9.0, 3.0), limiar=6.0), [])
        self.assertEqual(MIN_LEITURAS, 2)

    def test_serie_toda_abaixo_da_cota_nao_gera_evento(self):
        self.assertEqual(separar_eventos(serie(1.0, 2.0, 3.0), limiar=6.0), [])

    def test_serie_vazia(self):
        self.assertEqual(separar_eventos([], limiar=6.0), [])


class TesteSuspeitos(unittest.TestCase):
    def test_salto_grande_e_marcado_mas_nao_removido(self):
        """Blumenau já subiu mais de 4 m em menos de 24 h: descartar o extremo
        seria jogar fora justamente o que interessa."""
        eventos = separar_eventos(serie(7.0, 7.2, 14.0, 7.5), limiar=6.0)
        self.assertEqual(len(eventos), 1)
        self.assertAlmostEqual(eventos[0].pico_m, 14.0, msg="o extremo continua sendo o pico")
        self.assertTrue(eventos[0].suspeitos, "e vem marcado para conferência")

    def test_subida_normal_nao_e_marcada(self):
        eventos = separar_eventos(serie(7.0, 7.5, 8.0, 8.4), limiar=6.0)
        self.assertEqual(eventos[0].suspeitos, [])


class TesteAgrupamentoPorRegua(unittest.TestCase):
    """
    Leituras reais da Defesa Civil de Itajaí, colhidas em 30/08/2026 às 16h.

    Cinco réguas do Itajaí-Mirim dentro de Itajaí, no MESMO instante, marcando
    de 0,92 m a 4,82 m. Se o agrupamento fosse por cidade, 4,82 m viraria o
    "pico de Itajaí" — comparando réguas com zeros diferentes, que é o erro que
    o projeto avisa em toda tela para não cometer.
    """

    LEITURAS = [
        ("DC-03 Rio Itajaí-Mirim (canal retificado) - Captação SEMASA", 0.92),
        ("DC-04 Rio Itajaí-Mirim (canal retificado e curso antigo) - Vitalmar Pescados", 1.14),
        ("DC-05 Rio Itajaí-Mirim (curso antigo) - Propriedade privada", 1.07),
        ("DC-06 Rio Itajaí-Mirim (curso antigo) - Itamirim Clube de Campo", 0.97),
        ("DC-10 Rio Itajaí-Mirim – Bairro Limoeiro", 4.82),
    ]

    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        caminho = Path(self.dir.name) / "2026-08.ndjson"
        with open(caminho, "w", encoding="utf-8") as f:
            for hora in ("16:00", "16:15"):
                for estacao, nivel in self.LEITURAS:
                    f.write(json.dumps({
                        "estacao": estacao, "rio": "itajai-mirim", "cidade": "itajai",
                        "medido_em": f"2026-08-30T{hora}:00", "nivel_m": nivel,
                    }, ensure_ascii=False) + "\n")
        self.patch = unittest.mock.patch("extrair_picos.SERIE", Path(self.dir.name))
        self.patch.start()

    def tearDown(self):
        self.patch.stop()
        self.dir.cleanup()

    def test_cada_regua_fica_no_seu_grupo(self):
        grupos = ler_serie(None)
        self.assertEqual(len(grupos), 5, "cinco réguas, cinco séries")
        for estacao, nivel in self.LEITURAS:
            self.assertEqual([l.nivel_m for l in grupos[estacao]["leituras"]], [nivel, nivel])

    def test_nenhum_grupo_mistura_reguas(self):
        for estacao, grupo in ler_serie(None).items():
            alturas = {l.nivel_m for l in grupo["leituras"]}
            self.assertEqual(len(alturas), 1, f"{estacao} juntou leituras de réguas diferentes")

    def test_cidade_com_varias_reguas_recusa_a_cota_da_cidade(self):
        """A cota de estacoes.json é por cidade; com cinco réguas não dá para
        saber a qual delas ela se refere. Recusar é melhor que escolher."""
        limiar, motivo = limiar_da_estacao("DC-10", "itajai-mirim", "itajai", quantas_na_cidade=5)
        self.assertIsNone(limiar)
        self.assertEqual(motivo, "varias-reguas")

    def test_cidade_com_uma_regua_usa_a_cota_dela(self):
        limiar, nome = limiar_da_estacao("Blumenau", "itajai-acu", "blumenau", quantas_na_cidade=1)
        self.assertAlmostEqual(limiar, 6.0)
        self.assertEqual(nome, "atencao")

    def test_cota_propria_da_estacao_destrava_a_analise(self):
        """
        É esta a saída para Itajaí: cota por régua em estacoes.json. Com ela, a
        estação passa a ser analisada mesmo numa cidade com cinco réguas.
        """
        titulo = "DC-10 Rio Itajaí-Mirim – Bairro Limoeiro"
        with unittest.mock.patch(
            "comum.le_json",
            side_effect=lambda nome: {
                "estacoes_tempo_real": [
                    {"codigo": "DC-10", "titulo": titulo, "rio": "itajai-mirim",
                     "cidade": "itajai", "cotas_m": {"atencao": 5.5}, "verificado": True}
                ],
                "rios": {},
            } if nome == "estacoes.json" else {},
        ):
            limiar, nome = limiar_da_estacao(titulo, "itajai-mirim", "itajai", quantas_na_cidade=5)
        self.assertAlmostEqual(limiar, 5.5)
        self.assertIn("própria estação", nome)


if __name__ == "__main__":
    unittest.main(verbosity=2)
