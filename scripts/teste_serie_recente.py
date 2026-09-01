#!/usr/bin/env python3
"""Testes do recorte `serie-recente.json`, a linha do tempo do site.

O que não pode falhar aqui: entrar chuva onde só deveria haver nível, entrar
leitura velha fora da janela, ou o `medido_em` sair convertido de fuso. Cada um
desses vira um gráfico que mente para quem decide sair de casa.

    python3 scripts/teste_serie_recente.py
"""

import json
import tempfile
import unittest
from datetime import datetime, timedelta
from pathlib import Path

import coleta_niveis
from coleta_niveis import FUSO_BRASILIA


def carimbo(horas_atras: float) -> str:
    """`medido_em` a tantas horas do agora de Brasília, sem fuso — como a fonte."""
    agora = datetime.now(FUSO_BRASILIA).replace(tzinfo=None)
    return (agora - timedelta(hours=horas_atras)).isoformat(timespec="seconds")


class SerieRecente(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.serie = Path(self.tmp.name)
        # Aponta o módulo para o diretório temporário, sem tocar em data/.
        self._serie_orig = coleta_niveis.SERIE
        self._recente_orig = coleta_niveis.SERIE_RECENTE
        coleta_niveis.SERIE = self.serie
        coleta_niveis.SERIE_RECENTE = self.serie / "serie-recente.json"

    def tearDown(self):
        coleta_niveis.SERIE = self._serie_orig
        coleta_niveis.SERIE_RECENTE = self._recente_orig
        self.tmp.cleanup()

    def escrever_mes(self, linhas: list[dict]):
        mes = datetime.now(FUSO_BRASILIA).strftime("%Y-%m")
        (self.serie / f"{mes}.ndjson").write_text(
            "\n".join(json.dumps(l, ensure_ascii=False) for l in linhas) + "\n",
            encoding="utf-8",
        )

    def ler(self) -> dict:
        return json.loads(coleta_niveis.SERIE_RECENTE.read_text(encoding="utf-8"))

    def test_janela_corta_o_que_e_velho(self):
        self.escrever_mes([
            {"estacao": "a", "rio": "itajai-acu", "cidade": "rio-do-sul",
             "medido_em": carimbo(1), "nivel_m": 6.6},
            {"estacao": "a", "rio": "itajai-acu", "cidade": "rio-do-sul",
             "medido_em": carimbo(60), "nivel_m": 2.0},  # fora das 48 h
        ])
        pontos = coleta_niveis.escrever_serie_recente(horas=48)
        serie = self.ler()["series"]["itajai-acu"]["rio-do-sul"]
        self.assertEqual(len(serie), 1)
        self.assertEqual(serie[0]["nivel_m"], 6.6)
        self.assertEqual(pontos, 1)

    def test_so_nivel_nunca_chuva(self):
        self.escrever_mes([
            {"estacao": "a", "rio": "itajai-acu", "cidade": "blumenau",
             "medido_em": carimbo(1), "nivel_m": 5.0},
            {"estacao": "DCSC-00026", "rio": "itajai-acu", "cidade": "blumenau",
             "medido_em": carimbo(1), "mm": 22.0, "coerente": True},  # chuva: fora
        ])
        coleta_niveis.escrever_serie_recente(horas=48)
        blu = self.ler()["series"]["itajai-acu"]["blumenau"]
        self.assertEqual(len(blu), 1)
        self.assertIn("nivel_m", blu[0])
        self.assertNotIn("mm", blu[0])

    def test_ordena_por_tempo_e_agrupa_por_rio_cidade(self):
        self.escrever_mes([
            {"estacao": "a", "rio": "itajai-acu", "cidade": "gaspar",
             "medido_em": carimbo(1), "nivel_m": 6.2},
            {"estacao": "a", "rio": "itajai-acu", "cidade": "gaspar",
             "medido_em": carimbo(3), "nivel_m": 5.9},
            {"estacao": "b", "rio": "itajai-mirim", "cidade": "brusque",
             "medido_em": carimbo(2), "nivel_m": 4.9},
        ])
        coleta_niveis.escrever_serie_recente(horas=48)
        series = self.ler()["series"]
        gaspar = series["itajai-acu"]["gaspar"]
        self.assertEqual([p["nivel_m"] for p in gaspar], [5.9, 6.2])  # do mais antigo
        self.assertIn("brusque", series["itajai-mirim"])

    def test_ignora_linha_sem_cidade_ou_quebrada(self):
        mes = datetime.now(FUSO_BRASILIA).strftime("%Y-%m")
        (self.serie / f"{mes}.ndjson").write_text(
            json.dumps({"estacao": "a", "rio": "itajai-acu",
                        "medido_em": carimbo(1), "nivel_m": 3.0}) + "\n"
            + "{quebrada\n"
            + json.dumps({"estacao": "b", "rio": "itajai-acu", "cidade": "itajai",
                          "medido_em": carimbo(1), "nivel_m": 1.1}) + "\n",
            encoding="utf-8",
        )
        pontos = coleta_niveis.escrever_serie_recente(horas=48)
        self.assertEqual(pontos, 1)  # só a de Itajaí; sem cidade e quebrada saem
        self.assertEqual(list(self.ler()["series"]["itajai-acu"].keys()), ["itajai"])

    def test_meta_e_janela_no_arquivo(self):
        self.escrever_mes([
            {"estacao": "a", "rio": "itajai-acu", "cidade": "itajai",
             "medido_em": carimbo(1), "nivel_m": 1.0},
        ])
        coleta_niveis.escrever_serie_recente(horas=36)
        doc = self.ler()
        self.assertEqual(doc["janela_horas"], 36)
        self.assertIn("Brasília", doc["_meta"]["medido_em"])


if __name__ == "__main__":
    unittest.main()
