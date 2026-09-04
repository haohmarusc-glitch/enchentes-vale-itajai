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


class CadaPontoDizDeQueReguaVeio(unittest.TestCase):
    """
    O ponto tem de dizer de QUE RÉGUA veio, senão a série da cidade mistura
    zeros diferentes.

    O defeito, medido na série publicada de 04/09/2026: `itajai-acu/itajai`
    trazia DC-01, DC-02 e DC-11 intercaladas — 2,70 → 1,20 → 0,56 → 2,71 → ... —
    com salto MEDIANO de 1,70 m entre pontos vizinhos. Simulando a `tendencia()`
    do site em cada instante da janela, `itajai-mirim/itajai` daria |cm/h| > 100
    em 707 dos 949 instantes, com pico de +2448 cm/h: o site dizendo a quem mora
    na foz que o rio sobe 24 metros por hora.
    """

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.serie = Path(self.tmp.name)
        self._serie_orig = coleta_niveis.SERIE
        self._recente_orig = coleta_niveis.SERIE_RECENTE
        coleta_niveis.SERIE = self.serie
        coleta_niveis.SERIE_RECENTE = self.serie / "serie-recente.json"

    def tearDown(self):
        coleta_niveis.SERIE = self._serie_orig
        coleta_niveis.SERIE_RECENTE = self._recente_orig
        self.tmp.cleanup()

    def escrever_mes(self, linhas):
        mes = datetime.now(FUSO_BRASILIA).strftime("%Y-%m")
        (self.serie / f"{mes}.ndjson").write_text(
            "\n".join(json.dumps(l, ensure_ascii=False) for l in linhas) + "\n",
            encoding="utf-8",
        )

    def ler(self):
        return json.loads(coleta_niveis.SERIE_RECENTE.read_text(encoding="utf-8"))

    #: As três réguas do Açu em Itajaí, com os níveis reais de 04/09 às 11:31.
    TRES = [
        ("DC-01 Rio Itajaí-Açu - ICMBio/CEPSUL", 0.56),
        ("DC-02 Rio Itajaí-Açu - Praça Celso Pereira da Silva", 1.20),
        ("DC-11 Rio Itajaí-Açú – Santa Regina (Volta de Cima)", 2.70),
    ]

    def tres_reguas(self):
        self.escrever_mes([
            {"estacao": titulo, "rio": "itajai-acu", "cidade": "itajai",
             "medido_em": carimbo(h), "nivel_m": nivel}
            for h in (2, 1)
            for titulo, nivel in self.TRES
        ])
        coleta_niveis.escrever_serie_recente(horas=48)
        return self.ler()

    def test_a_legenda_traz_as_reguas_da_cidade(self):
        doc = self.tres_reguas()
        self.assertEqual(
            doc["reguas"]["itajai-acu"]["itajai"],
            sorted(t for t, _ in self.TRES),
            "sem a legenda não há como separar réguas de zeros diferentes",
        )

    def test_o_indice_r_separa_as_tres_em_series_coerentes(self):
        doc = self.tres_reguas()
        legenda = doc["reguas"]["itajai-acu"]["itajai"]
        pontos = doc["series"]["itajai-acu"]["itajai"]
        self.assertEqual(len(pontos), 6)

        por_regua = {}
        for p in pontos:
            self.assertIn("r", p, "ponto sem régua: a série volta a ser inseparável")
            por_regua.setdefault(legenda[p["r"]], []).append(p["nivel_m"])

        esperado = {t: [n, n] for t, n in self.TRES}
        self.assertEqual(por_regua, esperado)
        # E o que o defeito produzia: separadas, cada régua fica PLANA; juntas,
        # o salto entre pontos vizinhos passa de 1 m.
        for niveis in por_regua.values():
            self.assertEqual(max(niveis) - min(niveis), 0.0)
        juntos = [p["nivel_m"] for p in pontos]
        self.assertGreater(
            max(abs(b - a) for a, b in zip(juntos, juntos[1:])), 1.0,
            "o fixture parou de reproduzir o serrilhado — o teste virou vazio",
        )

    def test_cidade_de_uma_regua_so_tambem_leva_o_indice(self):
        # Não é caso especial: uma régua hoje pode virar duas amanhã, e a série
        # não pode mudar de forma no meio de uma cheia.
        self.escrever_mes([
            {"estacao": "Rio do Sul - Ponte Dom Tito Buss", "rio": "itajai-acu",
             "cidade": "rio-do-sul", "medido_em": carimbo(1), "nivel_m": 5.3},
        ])
        coleta_niveis.escrever_serie_recente(horas=48)
        doc = self.ler()
        self.assertEqual(doc["reguas"]["itajai-acu"]["rio-do-sul"],
                         ["Rio do Sul - Ponte Dom Tito Buss"])
        self.assertEqual(doc["series"]["itajai-acu"]["rio-do-sul"][0]["r"], 0)

    def test_ponto_sem_estacao_fica_SEM_r_em_vez_de_chutar_zero(self):
        # Chutar 0 diria "é a primeira régua da legenda", que é uma afirmação
        # sobre o zero da medição. Ausente é a resposta honesta.
        self.escrever_mes([
            {"rio": "itajai-acu", "cidade": "itajai",
             "medido_em": carimbo(1), "nivel_m": 1.1},
            {"estacao": "DC-02 Rio Itajaí-Açu - Praça Celso Pereira da Silva",
             "rio": "itajai-acu", "cidade": "itajai",
             "medido_em": carimbo(2), "nivel_m": 1.2},
        ])
        coleta_niveis.escrever_serie_recente(horas=48)
        doc = self.ler()
        pontos = doc["series"]["itajai-acu"]["itajai"]
        sem = [p for p in pontos if "r" not in p]
        self.assertEqual(len(sem), 1)
        self.assertEqual(sem[0]["nivel_m"], 1.1)
        # A legenda só lista a que existe — não inventa entrada para a anônima.
        self.assertEqual(len(doc["reguas"]["itajai-acu"]["itajai"]), 1)

    def test_a_lista_de_pontos_continua_LISTA_para_o_site_antigo(self):
        # Retrocompatibilidade não é detalhe: o publicador roda em cron e o site
        # é implantado à parte. Mudar a forma derrubaria a linha do tempo de
        # todas as cidades até o deploy — possivelmente no meio de uma cheia.
        doc = self.tres_reguas()
        pontos = doc["series"]["itajai-acu"]["itajai"]
        self.assertIsInstance(pontos, list)
        for p in pontos:
            self.assertIn("medido_em", p)
            self.assertIn("nivel_m", p)

    def test_o_meta_explica_o_r(self):
        doc = self.tres_reguas()
        self.assertIn("r", doc["_meta"])
        self.assertIn("ZEROS DIFERENTES", doc["_meta"]["r"])


if __name__ == "__main__":
    unittest.main()
