#!/usr/bin/env python3
"""
Testes da conferência mapa × alarme.

O que ela guarda é uma classe de falha que nenhum teste unitário pega: os dois
caminhos, cada um sozinho, coerentes — e discordando entre si. Blumenau ficou
sem aviso automático assim, com o mapa pintando a cor certa o tempo todo.
"""
import json
import unittest
from pathlib import Path

import conferir_mapa_e_alarme as cf

RAIZ = Path(__file__).resolve().parent.parent


def leitura(estacao, cidade="blumenau", rio="itajai-acu", nivel=3.4,
            medido="2026-09-04T03:00:00", **extra):
    return {"estacao": estacao, "rio": rio, "cidade": cidade, "nivel_m": nivel,
            "medido_em": medido, **extra}


class VocabularioSincronizado(unittest.TestCase):
    def test_as_chaves_que_pintam_sao_AS_MESMAS_do_site(self):
        """
        A lista está escrita nos dois lados. Divergindo, este script deixa de
        cobrir o que promete — passaria a ignorar justamente a cidade cuja cota
        o mapa pinta e ele não conhece.
        """
        ts = (RAIZ / "web/src/logica/tempoReal.ts").read_text(encoding="utf-8")
        i = ts.index("const CHAVES_QUE_PINTAM")
        trecho = ts[i:ts.index("])", i)]
        do_site = {c.strip().strip("',\"") for c in trecho.split("[", 1)[1].split(",")}
        do_site = {c for c in do_site if c}
        self.assertEqual(do_site, cf.CHAVES_QUE_PINTAM,
                         "o vocabulário do site e o deste script divergiram")


class Buraco(unittest.TestCase):
    ESTACOES = {"rios": {"itajai-acu": {"cidades": [
        {"id": "blumenau", "cotas_m": {"atencao": 6.0, "alerta": 6.5, "inundacao": 7.4}},
    ]}}}

    def test_primaria_mais_resgate_NAO_e_buraco_quando_o_alarme_conta_reguas(self):
        dados = {"leituras": [
            leitura("Blumenau", medido="2026-09-04T00:15:00"),
            leitura("Blumenau (AlertaBlu)", resgate_de="Blumenau"),
        ]}
        r = cf.avaliar(dados, self.ESTACOES)
        self.assertEqual(len(r), 1)
        self.assertEqual(r[0]["reguas"], 1, "resgate tem de contar como a MESMA régua")
        self.assertTrue(r[0]["vigiada"])
        self.assertFalse(r[0]["buraco"])

    def test_cidade_sem_leitura_nao_entra(self):
        # Sem leitura, o mapa também não pinta: não há discordância a apontar.
        self.assertEqual(cf.avaliar({"leituras": []}, self.ESTACOES), [])

    def test_leitura_que_NAO_pode_virar_cota_nao_entra(self):
        # O bruto estadual mostra número e nunca pinta — cobrar alarme dele
        # seria pedir aviso sobre uma régua com zero próprio.
        dados = {"leituras": [leitura("SDC-SC Blumenau", usar_para_cota=False)]}
        self.assertEqual(cf.avaliar(dados, self.ESTACOES), [])

    def test_cidade_sem_cota_de_acionamento_nao_entra(self):
        est = {"rios": {"itajai-acu": {"cidades": [
            {"id": "blumenau", "cotas_m": {"inundacao_historica": 8.5}},
        ]}}}
        self.assertEqual(cf.avaliar({"leituras": [leitura("Blumenau")]}, est), [])

    def test_a_lista_de_recusas_aceitas_e_FECHADA(self):
        """
        Motivo novo tem de aparecer como falha até alguém decidir que é
        aceitável. Lista de exceções que cresce sozinha para de proteger.
        """
        self.assertNotIn("mais de uma régua", " ".join(cf.RECUSAS_ACEITAS),
                         "aceitar este motivo às cegas reabriria o buraco do Blumenau")


class ContraOsDadosReais(unittest.TestCase):
    def test_o_cadastro_e_o_alarme_concordam_hoje(self):
        """
        Roda contra o `ultimo_gaspar`... não: contra o que houver em
        `data/tempo-real/ultimo.json`. Sem arquivo, o teste não inventa um —
        pula, e a conferência de verdade acontece na VPS e na CI.
        """
        if not cf.ULTIMO.exists():
            self.skipTest("sem ultimo.json neste ambiente")
        dados = json.loads(cf.ULTIMO.read_text(encoding="utf-8"))
        est = json.loads(cf.ESTACOES.read_text(encoding="utf-8"))
        buracos = [r for r in cf.avaliar(dados, est) if r["buraco"]]
        self.assertEqual(buracos, [], f"cor sem alarme: {[b['cidade'] for b in buracos]}")


if __name__ == "__main__":
    unittest.main()
