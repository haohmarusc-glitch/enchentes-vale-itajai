#!/usr/bin/env python3
"""Testes do resumo das cheias captadas (`eventos_captados.py`).

O que protegem: o chat responde "qual foi a última cheia?" a partir deste arquivo. Uma régua de
estuário contada como cheia, uma troca de fonte lida como duas réguas ao mesmo tempo, ou o
relógio atrasado do repasse de Blumenau virando "hora do pico" seriam respostas erradas ditas
com voz de dado.

    python3 scripts/teste_eventos_captados.py
"""

import json
import tempfile
import unittest
from datetime import datetime, timedelta
from pathlib import Path

import extrair_picos as ep
from eventos_captados import faixa_alcancada, maior_lacuna_min, registro_em_enchentes, resumir

INICIO = datetime(2026, 9, 10, 0, 0)
ESTACOES = {
    "rios": {
        "itajai-acu": {
            "cidades": [
                {"id": "blumenau", "nome": "Blumenau", "cotas_m": {"monitoramento": 3.0, "atencao": 4.0, "alerta": 6.0, "emergencia": 8.0}},
                {"id": "rio-do-sul", "nome": "Rio do Sul", "cotas_m": {"atencao": 4.5, "alerta": 5.5, "inundacao": 6.5}},
                {"id": "ascurra", "nome": "Ascurra", "cotas_m": {"atencao": 8.5}},
                {"id": "gaspar", "nome": "Gaspar", "cotas_m": {"atencao": 5.0, "emergencia": 7.0}},
                {"id": "itajai", "nome": "Itajaí", "cotas_m": {}},
            ]
        }
    },
    "estacoes_tempo_real": [
        {"titulo": "Blumenau", "cidade": "blumenau", "rio": "itajai-acu", "cotas_m": {}},
        {"titulo": "Rio do Sul, Ponte Dom Tito Buss (Asthon)", "cidade": "rio-do-sul", "rio": "itajai-acu", "cotas_m": {}},
        {"titulo": "DC-01 Rio Itajaí-Açu - ICMBio/CEPSUL", "codigo": "DC-01", "cidade": "itajai", "rio": "itajai-acu",
         "cotas_m": {"atencao": 1.16, "alerta": 1.36}, "alerta_automatico": False, "motivo_sem_alerta": "régua de estuário"},
        {"titulo": "DC-11 Rio Itajaí-Açú – Santa Regina (Volta de Cima)", "codigo": "DC-11", "cidade": "itajai", "rio": "itajai-acu",
         "cotas_m": {"atencao": 3.0, "alerta": 4.0, "emergencia": 5.0}},
    ],
}


def leituras(estacao, valores, passo_min=60, inicio=INICIO):
    return [ep.Leitura(inicio + timedelta(minutes=i * passo_min), v, estacao) for i, v in enumerate(valores)]


def grupo(rio, cidade, *listas):
    todas = sorted((l for lista in listas for l in lista), key=lambda l: l.quando)
    return {"rio": rio, "cidade": cidade, "leituras": todas}


class TesteResumo(unittest.TestCase):
    def setUp(self):
        import eventos_captados
        import comum
        # O cadastro de teste no lugar do estacoes.json real, nas duas pontas que o leem.
        self._le_json = comum.le_json
        comum.le_json = lambda nome: ESTACOES if nome == "estacoes.json" else self._le_json(nome)
        eventos_captados.estacao_por_titulo = lambda t: next((e for e in ESTACOES["estacoes_tempo_real"] if e["titulo"] == t), None)
        ep.cota_da_estacao = lambda t: next(
            ((float(e["cotas_m"][k]), k) for e in ESTACOES["estacoes_tempo_real"] if e["titulo"] == t
             for k in ("atencao", "alerta", "emergencia", "inundacao") if k in e["cotas_m"]), (None, None))
        ep.cota_de_referencia = lambda rio, cidade: next(
            ((float(c["cotas_m"][k]), k) for c in ESTACOES["rios"][rio]["cidades"] if c["id"] == cidade
             for k in ("atencao", "alerta", "emergencia", "inundacao") if k in c["cotas_m"]), (None, None))

    def tearDown(self):
        import comum
        comum.le_json = self._le_json

    def test_blumenau_relogio_do_repasse_cede_a_hora_ao_alertablu(self):
        # Repasse (Blumenau) de 10 em 10 min com a crista 7,87 às 02:15; AlertaBlu horário com a crista 7,86 às 05:00.
        repasse = leituras("Blumenau", [3.0, 5.0, 7.87, 7.5, 6.0, 4.0, 3.0], passo_min=60, inicio=INICIO)
        alertablu = leituras("Blumenau (AlertaBlu)", [2.9, 3.0, 5.0, 6.9, 7.6, 7.86, 7.4, 6.0, 4.0, 3.0], passo_min=60, inicio=INICIO)
        r = resumir({"Blumenau": grupo("itajai-acu", "blumenau", repasse, alertablu)}, ESTACOES, enchentes=[])
        ev = [e for e in r["episodios"] if e["cidade"] == "blumenau"]
        self.assertEqual(len(ev), 1)
        self.assertEqual(ev[0]["maior_leitura_m"], 7.87, "o valor é o maior, de qualquer publicação")
        self.assertEqual(ev[0]["horario_de"], "Blumenau (AlertaBlu)", "o horário vem do relógio confiável")
        self.assertEqual(ev[0]["quando"], (INICIO + timedelta(hours=5)).strftime("%Y-%m-%dT%H:%M:%S"))
        self.assertFalse(ev[0]["relogio_defasado"])
        self.assertEqual(ev[0]["faixa_alcancada"], "alerta")

    def test_regua_de_estuario_nao_gera_episodio_mas_fica_na_cobertura(self):
        dc01 = leituras("DC-01 Rio Itajaí-Açu - ICMBio/CEPSUL", [1.0, 1.5, 1.6, 1.0, 1.5, 1.6, 1.0])
        dc11 = leituras("DC-11 Rio Itajaí-Açú – Santa Regina (Volta de Cima)", [2.0, 3.5, 4.2, 3.0, 2.0])
        r = resumir({dc01[0].estacao: grupo("itajai-acu", "itajai", dc01), dc11[0].estacao: grupo("itajai-acu", "itajai", dc11)}, ESTACOES, [])
        self.assertEqual([e["regua"] for e in r["episodios"]], ["DC-11 Rio Itajaí-Açú – Santa Regina (Volta de Cima)"])
        cob = {c["regua"]: c for c in r["cobertura"]}
        self.assertEqual(cob["DC-01 Rio Itajaí-Açu - ICMBio/CEPSUL"]["sem_faixa"], "régua de estuário")
        self.assertIsNone(cob["DC-01 Rio Itajaí-Açu - ICMBio/CEPSUL"]["maior_leitura"]["faixa"])
        self.assertTrue(cob["DC-11 Rio Itajaí-Açú – Santa Regina (Volta de Cima)"]["varias_ao_mesmo_tempo"])
        self.assertEqual(r["episodios"][0]["faixa_alcancada"], "alerta", "cota da própria estação: 4,20 m ≥ alerta 4,00")

    def test_troca_de_fonte_e_uma_publicacao_por_vez_cada_uma_com_a_cota_da_cidade(self):
        antiga = leituras("Rio do Sul Estação MKS", [4.0, 6.0, 7.06, 5.0, 4.0], inicio=INICIO)
        nova = leituras("Rio do Sul, Ponte Dom Tito Buss (Asthon)", [4.0, 5.0, 5.89, 5.0, 4.0], inicio=INICIO + timedelta(days=3))
        r = resumir({"Rio do Sul Estação MKS": grupo("itajai-acu", "rio-do-sul", antiga),
                     "Rio do Sul, Ponte Dom Tito Buss (Asthon)": grupo("itajai-acu", "rio-do-sul", nova)}, ESTACOES, [])
        ev = sorted(r["episodios"], key=lambda e: e["inicio"])
        self.assertEqual([e["maior_leitura_m"] for e in ev], [7.06, 5.89])
        self.assertEqual([e["faixa_alcancada"] for e in ev], ["inundacao", "alerta"])
        self.assertEqual([e["no_cadastro"] for e in ev], [False, True], "a publicação antiga fica marcada como fora do cadastro")
        self.assertTrue(all(e["id"].startswith("2026-09-1") and "-rio-do-sul-" in e["id"] for e in ev), "ids distinguem a publicação")
        for c in r["cobertura"]:
            self.assertFalse(c["varias_ao_mesmo_tempo"], "não coexistem no tempo, então não são 'várias réguas'")

    def test_ascurra_e_gaspar_nao_ganham_faixa_das_cotas(self):
        asc = leituras("Ascurra — Ponte do Beber (DCSC-00003)", [7.0, 9.0, 9.42, 8.0, 7.0])
        r = resumir({asc[0].estacao: grupo("itajai-acu", "ascurra", asc)}, ESTACOES, [])
        self.assertEqual(len(r["episodios"]), 1)
        self.assertIsNone(r["episodios"][0]["faixa_alcancada"])
        self.assertIn("C18", r["cobertura"][0]["sem_faixa"])
        self.assertIsNone(faixa_alcancada("gaspar", 5.0, {"atencao": 5.0}), "5 m exatos não estão definidos em Gaspar")
        self.assertEqual(faixa_alcancada("gaspar", 5.01, {}), "atencao")
        self.assertEqual(faixa_alcancada("gaspar", 7.5, {}), "emergencia")

    def test_registro_em_enchentes_casa_por_cidade_e_data_proxima(self):
        enchentes = [{"rio": "itajai-acu", "cidade": "blumenau", "data": "2026-09-12", "hora": "05:15", "pico_m": 7.87, "referencia": "régua", "confianca": "alta"}]
        self.assertIsNotNone(registro_em_enchentes(enchentes, "itajai-acu", "blumenau", datetime(2026, 9, 11, 23, 0)))
        self.assertIsNone(registro_em_enchentes(enchentes, "itajai-acu", "blumenau", datetime(2026, 9, 20, 0, 0)))
        self.assertIsNone(registro_em_enchentes(enchentes, "itajai-acu", "gaspar", datetime(2026, 9, 12, 5, 0)))

    def test_lacuna_e_a_maior_distancia_entre_leituras(self):
        ls = leituras("Blumenau", [4.0, 4.5, 5.0], passo_min=15)
        ls.append(ep.Leitura(ls[-1].quando + timedelta(hours=6), 5.2, "Blumenau"))
        self.assertEqual(maior_lacuna_min(ls), 360)
        self.assertEqual(maior_lacuna_min(ls[:1]), 0)

    def test_arquivo_gravado_e_json_valido_sem_tocar_enchentes(self):
        with tempfile.TemporaryDirectory() as temp:
            r = resumir({"Blumenau": grupo("itajai-acu", "blumenau", leituras("Blumenau", [3.0, 5.0, 6.5, 4.0, 3.0]))}, ESTACOES, [])
            caminho = Path(temp) / "eventos-captados.json"
            caminho.write_text(json.dumps(r, ensure_ascii=False), encoding="utf-8")
            lido = json.loads(caminho.read_text(encoding="utf-8"))
            self.assertIn("Nunca entra em enchentes.json", lido["_meta"]["o_que_e"])
            self.assertEqual(lido["episodios"][0]["registro_em_enchentes"], None)


if __name__ == "__main__":
    unittest.main()
