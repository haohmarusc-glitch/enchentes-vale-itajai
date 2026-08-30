#!/usr/bin/env python3
"""Testes do vigia da coleta.

Se ele errar para menos, a coleta morre em silêncio e o site congela num nível
antigo sem que ninguém perceba. Se errar para mais, avisa toda noite até virar
ruído. Os dois lados estão cobertos aqui.

    python3 scripts/teste_saude_coleta.py
"""

import unittest
from datetime import datetime, timedelta, timezone

from saude_coleta import (
    SILENCIO_H,
    TOLERANCIA_COLETA_MIN,
    TOLERANCIA_FONTE_MIN,
    avaliar,
    deve_avisar,
    texto,
)

AGORA = datetime(2026, 8, 30, 20, 30, tzinfo=timezone.utc)  # 17:30 em Brasília


def coleta(minutos_atras=5, medido_minutos_atras=45, leituras=1):
    """Um ultimo.json com as idades pedidas. `medido_em` é hora de Brasília."""
    quando = AGORA - timedelta(minutes=minutos_atras)
    medido = (AGORA - timedelta(minutes=medido_minutos_atras)).astimezone(
        timezone(timedelta(hours=-3))
    ).replace(tzinfo=None)
    return {
        "coletado_em": quando.isoformat(),
        "leituras": [
            {"estacao": f"DC-{i:02d}", "rio": "itajai-acu", "cidade": "itajai",
             "nivel_m": 1.2, "medido_em": medido.isoformat()}
            for i in range(1, leituras + 1)
        ],
    }


class TestAvaliar(unittest.TestCase):
    def test_coleta_em_dia(self):
        d = avaliar(coleta(), AGORA)
        self.assertTrue(d.ok, d.motivo)

    def test_sem_arquivo_e_falha(self):
        self.assertFalse(avaliar(None, AGORA).ok)

    def test_cron_parado(self):
        d = avaliar(coleta(minutos_atras=TOLERANCIA_COLETA_MIN + 10), AGORA)
        self.assertFalse(d.ok)
        self.assertIn("não roda há", d.motivo)

    def test_o_caso_traicoeiro_arquivo_novo_dado_velho(self):
        """
        O cron correndo perfeitamente sobre uma página que parou de atualizar.
        O arquivo fica novo a cada 15 min; o dado, cada vez mais velho.
        """
        d = avaliar(coleta(minutos_atras=2, medido_minutos_atras=TOLERANCIA_FONTE_MIN + 60), AGORA)
        self.assertFalse(d.ok)
        self.assertIn("não publica leitura nova", d.motivo)

    def test_coleta_que_rodou_e_nao_trouxe_nada(self):
        d = avaliar(coleta(leituras=0), AGORA)
        self.assertFalse(d.ok)
        self.assertIn("nenhuma leitura", d.motivo)

    def test_fonte_lenta_dentro_da_folga_nao_e_falha(self):
        """A estação MKS publica com quase uma hora de atraso, e isso é normal."""
        d = avaliar(coleta(medido_minutos_atras=70), AGORA)
        self.assertTrue(d.ok, d.motivo)

    def test_coletado_em_ilegivel(self):
        dados = coleta()
        dados["coletado_em"] = "faz pouco"
        self.assertFalse(avaliar(dados, AGORA).ok)

    def test_coletado_em_sem_fuso_e_lido_como_utc(self):
        dados = coleta()
        dados["coletado_em"] = (AGORA - timedelta(minutes=5)).replace(tzinfo=None).isoformat()
        self.assertTrue(avaliar(dados, AGORA).ok)


class TestQuandoAvisar(unittest.TestCase):
    def test_primeira_falha_avisa_na_hora(self):
        d = avaliar(None, AGORA)
        self.assertTrue(deve_avisar(d, {}, AGORA))

    def test_falha_que_continua_nao_repete_antes_do_silencio(self):
        d = avaliar(None, AGORA)
        estado = {"falhando": True, "avisado_em": (AGORA - timedelta(hours=1)).isoformat()}
        self.assertFalse(deve_avisar(d, estado, AGORA))

    def test_falha_longa_repete_depois_do_silencio(self):
        d = avaliar(None, AGORA)
        estado = {"falhando": True,
                  "avisado_em": (AGORA - timedelta(hours=SILENCIO_H + 1)).isoformat()}
        self.assertTrue(deve_avisar(d, estado, AGORA))

    def test_recuperacao_avisa_sem_esperar(self):
        d = avaliar(coleta(), AGORA)
        estado = {"falhando": True, "avisado_em": (AGORA - timedelta(minutes=1)).isoformat()}
        self.assertTrue(deve_avisar(d, estado, AGORA))

    def test_tudo_bem_seguido_de_tudo_bem_nao_avisa(self):
        d = avaliar(coleta(), AGORA)
        self.assertFalse(deve_avisar(d, {"falhando": False}, AGORA))


class TestTexto(unittest.TestCase):
    def test_falha_diz_o_que_para_de_funcionar(self):
        t = texto(avaliar(None, AGORA))
        self.assertIn("coleta", t.lower())
        self.assertIn("aviso de cota", t)

    def test_recuperacao_e_curta(self):
        self.assertIn("voltou", texto(avaliar(coleta(), AGORA)))


if __name__ == "__main__":
    unittest.main(verbosity=2)
