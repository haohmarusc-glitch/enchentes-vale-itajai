#!/usr/bin/env python3
"""Testes do portão de qualidade: as regras da topologia em árvore têm de ABORTAR.

Documentar a topologia não impediu o JSON de ficar errado por versões seguidas;
o que impediu foi o validador passar a falhar. Estes testes travam esse "falhar":
cada um estraga UM ponto dos dados reais e exige que `valida_estacoes` acuse.
"""

import copy
import json
import unittest

from comum import DADOS
import validar_dados as vd


def _cidade(estacoes, rio, cid):
    return next(c for c in estacoes["rios"][rio]["cidades"] if c["id"] == cid)


def erros_de(estacoes_dict) -> list[str]:
    """Roda só `valida_estacoes` sobre um estacoes.json em memória."""
    vd.erros.clear()
    vd.avisos.clear()
    orig = vd.le_json
    vd.le_json = lambda nome: estacoes_dict if nome == "estacoes.json" else orig(nome)
    try:
        vd.valida_estacoes()
    finally:
        vd.le_json = orig
    return list(vd.erros)


class TopologiaArvore(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.real = json.loads((DADOS / "estacoes.json").read_text(encoding="utf-8"))

    def base(self):
        return copy.deepcopy(self.real)

    def test_dados_reais_passam(self):
        self.assertEqual(erros_de(self.base()), [], "o estacoes.json real deveria passar limpo")

    def test_ordem_global_em_rio_ramificado_aborta(self):
        d = self.base()
        _cidade(d, "itajai-acu", "taio")["ordem"] = 1  # a bacia é árvore: ordem tem de ser null
        self.assertTrue(any("ordem' global" in e for e in erros_de(d)), "ordem global no Açu deveria falhar")

    def test_ramo_ausente_em_rio_ramificado_aborta(self):
        d = self.base()
        del _cidade(d, "itajai-acu", "rio-do-sul")["ramo"]
        self.assertTrue(any("ramo' ausente" in e for e in erros_de(d)))

    def test_ramo_em_rio_em_fila_aborta(self):
        # Mirim é fila: pôr ramo nele mistura árvore e fila.
        d = self.base()
        _cidade(d, "itajai-mirim", "brusque")["ramo"] = "tronco_acu"
        self.assertTrue(any("não se misturam" in e for e in erros_de(d)))

    def test_codigo_dcsc_trocado_aborta(self):
        d = self.base()
        _cidade(d, "itajai-acu", "taio")["codigo_dcsc"] = "DCSC-99999"
        self.assertTrue(any("codigo_dcsc deveria ser" in e for e in erros_de(d)))

    def test_codigo_dcsc_some_com_a_cidade_aborta(self):
        d = self.base()
        cid = d["rios"]["itajai-acu"]["cidades"]
        d["rios"]["itajai-acu"]["cidades"] = [c for c in cid if c["id"] != "ascurra"]
        self.assertTrue(any("sumiu do eixo" in e for e in erros_de(d)))

    def test_tronco_sequencia_fora_de_ordem_aborta(self):
        d = self.base()
        seq = d["rios"]["itajai-acu"]["_topologia"]["tronco_sequencia"]
        seq[1], seq[2] = seq[2], seq[1]  # troca ascurra <-> indaial
        self.assertTrue(any("não bate" in e for e in erros_de(d)))

    def test_ordem_no_ramo_furada_aborta(self):
        d = self.base()
        _cidade(d, "itajai-acu", "indaial")["ordem_no_ramo"] = 9  # buraco no tronco
        self.assertTrue(any("ordem_no_ramo" in e for e in erros_de(d)))

    def test_regua_sem_aviso_precisa_de_motivo(self):
        d = self.base()
        d["estacoes_tempo_real"].append({
            "titulo": "Régua de teste sem motivo",
            "rio": "itajai-acu", "cidade": "itajai",
            "cotas_m": {"atencao": 1.0}, "verificado": True,
            "alerta_automatico": False,
        })
        self.assertTrue(any("motivo_sem_alerta" in e for e in erros_de(d)))


if __name__ == "__main__":
    unittest.main()


def _monotonia(estacoes_dict, transito_dict) -> tuple[list[str], list[str]]:
    """Roda só `valida_monotonia_transito` sobre dados em memória."""
    vd.erros.clear()
    vd.avisos.clear()
    orig = vd.le_json

    def falso(nome):
        if nome == "estacoes.json":
            return estacoes_dict
        if nome == "transito.json":
            return transito_dict
        return orig(nome)

    vd.le_json = falso
    try:
        vd.valida_monotonia_transito()
    finally:
        vd.le_json = orig
    return list(vd.erros), list(vd.avisos)


class MonotoniaDaJanela(unittest.TestCase):
    """
    A janela de chegada contra a ordem do rio.

    A distinção que estes testes travam: SOBREPOSIÇÃO não é CONTRADIÇÃO. Tratar
    as duas igual empurraria alguém a "consertar" o dado trocando valor de fonte
    publicada por interpolação — perder dado achando que ganha precisão.
    """

    @classmethod
    def setUpClass(cls):
        cls.estacoes = json.loads((DADOS / "estacoes.json").read_text(encoding="utf-8"))
        cls.transito = json.loads((DADOS / "transito.json").read_text(encoding="utf-8"))

    def base(self):
        return copy.deepcopy(self.estacoes), copy.deepcopy(self.transito)

    def test_dados_reais_nao_tem_contradicao(self):
        erros, _ = _monotonia(*self.base())
        self.assertEqual(erros, [], "o transito.json real não deveria ter janela impossível")

    def test_a_sobreposicao_conhecida_sai_como_aviso_e_nao_erro(self):
        # Indaial 10-10 h x Blumenau 7-10 h: a de baixo COMEÇA antes, mas
        # 10 <= 10, então existe atribuição consistente. Aviso, nunca erro.
        erros, avisos = _monotonia(*self.base())
        self.assertEqual(erros, [])
        self.assertTrue(
            any("blumenau" in a and "indaial" in a for a in avisos),
            "a sobreposição Blumenau/Indaial deveria aparecer como aviso",
        )

    def test_janela_impossivel_vira_erro(self):
        # Empurra Indaial para depois do MÁXIMO de Blumenau: agora não existe
        # tempo que satisfaça as duas janelas.
        est, tr = self.base()
        for t in tr["trechos"]:
            if t["de"] == "rio-do-sul" and t["para"] == "indaial":
                t["horas_min"] = t["horas_max"] = 11
        erros, _ = _monotonia(est, tr)
        self.assertTrue(
            any("não cabe antes de" in e for e in erros),
            "montante depois do máximo do jusante deveria ser erro",
        )

    def test_empate_no_limite_ainda_passa(self):
        # min_montante == max_jusante é o empate que o hidrograma afirma
        # (Indaial e Blumenau na mesma hora). Não pode virar erro.
        est, tr = self.base()
        for t in tr["trechos"]:
            if t["de"] == "rio-do-sul" and t["para"] == "indaial":
                t["horas_min"] = t["horas_max"] = 10
        erros, _ = _monotonia(est, tr)
        self.assertEqual(erros, [])

    def test_segue_a_mesma_busca_do_site(self):
        # Gaspar não tem trecho direto desde Rio do Sul: a janela sai da cadeia
        # rio-do-sul -> blumenau -> gaspar. Se a busca divergir da do site, o
        # validador aprovaria um percurso que a tela não usa.
        _, tr = self.base()
        self.assertEqual(
            vd._janela_ate(tr["trechos"], "itajai-acu", "rio-do-sul", "gaspar"), (9, 12)
        )
