#!/usr/bin/env python3
"""Testes do aviso de cota.

Este é o código que decide se o telefone de alguém toca às três da manhã.
Errar para menos cala o aviso que salvaria; errar para mais ensina a pessoa a
desligar o bot antes da noite em que ele importaria. Daí os casos abaixo.

    python3 scripts/teste_alerta_cotas.py
"""

import unittest

import alerta_cotas
from datetime import datetime, timedelta, timezone

from alerta_cotas import (
    REPETE_H,
    resolver,
    SUBIDA_M,
    decidir,
    faixa_de,
    idade_min,
    subiu,
)

AGORA = datetime(2026, 8, 30, 3, 0, tzinfo=timezone.utc)
COTAS = {"atencao": 4.5, "alerta": 5.5, "inundacao": 6.5}


def payload(nivel, estacao="Rio do Sul Estação MKS", cidade="rio-do-sul",
            rio="itajai-acu", medido="2026-08-30T00:00:00"):
    return {
        "coletado_em": AGORA.isoformat(),
        "leituras": [{
            "estacao": estacao, "rio": rio, "cidade": cidade,
            "nivel_m": nivel, "medido_em": medido,
        }],
    }


class TestFaixa(unittest.TestCase):
    def test_a_faixa_e_a_mais_alta_alcancada(self):
        self.assertEqual(faixa_de(3.0, COTAS), "normal")
        self.assertEqual(faixa_de(4.5, COTAS), "atencao")  # na cota já conta
        self.assertEqual(faixa_de(5.4, COTAS), "atencao")
        self.assertEqual(faixa_de(6.9, COTAS), "inundacao")

    def test_cota_faltando_nao_inventa_faixa(self):
        """Estação com só uma cota cadastrada não vira alerta nem inundação."""
        self.assertEqual(faixa_de(99.0, {"atencao": 4.5}), "atencao")

    def test_ordem_das_faixas(self):
        self.assertTrue(subiu("inundacao", "alerta"))
        self.assertFalse(subiu("alerta", "inundacao"))
        self.assertFalse(subiu("alerta", "alerta"))


class TestDecidir(unittest.TestCase):
    def test_primeira_travessia_avisa(self):
        avisos, estado, _ = decidir(payload(4.6), {}, AGORA)
        self.assertEqual(len(avisos), 1)
        self.assertEqual(avisos[0]["faixa"], "atencao")
        self.assertEqual(estado["Rio do Sul Estação MKS"]["faixa"], "atencao")

    def test_rio_baixo_nao_avisa_nada(self):
        """Ninguém precisa saber que o rio está normal — nem uma vez."""
        avisos, estado, _ = decidir(payload(2.0), {}, AGORA)
        self.assertEqual(avisos, [])
        self.assertEqual(estado["Rio do Sul Estação MKS"]["faixa"], "normal")

    def test_mesma_faixa_sem_subida_nao_repete(self):
        antes = {"Rio do Sul Estação MKS": {
            "faixa": "atencao", "nivel_m": 4.6,
            "avisado_em": (AGORA - timedelta(hours=REPETE_H + 1)).isoformat()}}
        avisos, _, _ = decidir(payload(4.7), antes, AGORA)
        self.assertEqual(avisos, [], "subiu 10 cm em 4 h — isso não é notícia")

    def test_mesma_faixa_com_subida_repete_depois_da_espera(self):
        antes = {"Rio do Sul Estação MKS": {
            "faixa": "atencao", "nivel_m": 4.6,
            "avisado_em": (AGORA - timedelta(hours=REPETE_H + 1)).isoformat()}}
        avisos, _, _ = decidir(payload(4.6 + SUBIDA_M), antes, AGORA)
        self.assertEqual(len(avisos), 1)

    def test_subida_de_exatamente_30_cm_avisa(self):
        """
        A borda, e o caso mais provável: 4,60 -> 4,90. Em ponto flutuante a
        diferença dá 0,2999..., e sem arredondar ao centímetro o aviso sumia.
        """
        antes = {"Rio do Sul Estação MKS": {
            "faixa": "atencao", "nivel_m": 4.60,
            "avisado_em": (AGORA - timedelta(hours=REPETE_H + 1)).isoformat()}}
        avisos, _, _ = decidir(payload(4.90), antes, AGORA)
        self.assertEqual(len(avisos), 1)

    def test_subida_grande_mas_cedo_demais_espera(self):
        antes = {"Rio do Sul Estação MKS": {
            "faixa": "atencao", "nivel_m": 4.6,
            "avisado_em": (AGORA - timedelta(minutes=20)).isoformat()}}
        avisos, _, _ = decidir(payload(5.4), antes, AGORA)
        self.assertEqual(avisos, [], "ainda em atenção e o último aviso foi há 20 min")

    def test_escalada_de_faixa_fura_qualquer_espera(self):
        """Atenção -> alerta é informação nova. Não espera cronômetro nenhum."""
        antes = {"Rio do Sul Estação MKS": {
            "faixa": "atencao", "nivel_m": 4.6,
            "avisado_em": (AGORA - timedelta(minutes=5)).isoformat()}}
        avisos, _, _ = decidir(payload(5.6), antes, AGORA)
        self.assertEqual(len(avisos), 1)
        self.assertEqual(avisos[0]["faixa"], "alerta")

    def test_volta_ao_normal_avisa_uma_vez_so(self):
        antes = {"Rio do Sul Estação MKS": {
            "faixa": "alerta", "nivel_m": 5.6, "avisado_em": AGORA.isoformat()}}
        avisos, estado, _ = decidir(payload(3.0), antes, AGORA)
        self.assertEqual(len(avisos), 1)
        self.assertEqual(avisos[0]["faixa"], "normal")
        de_novo, _, _ = decidir(payload(3.0), estado, AGORA)
        self.assertEqual(de_novo, [])

    def test_nao_ha_horario_de_silencio(self):
        """Três da manhã é exatamente quando o aviso importa."""
        for hora in (3, 4, 23, 12):
            quando = AGORA.replace(hour=hora)
            avisos, _, _ = decidir(payload(6.6), {}, quando)
            self.assertEqual(len(avisos), 1, f"calou às {hora}h")
            self.assertEqual(avisos[0]["faixa"], "inundacao")

    def test_cidade_com_varias_reguas_nao_usa_a_cota_da_cidade(self):
        """
        Itajaí tem onze réguas com zeros diferentes. Aplicar a cota da cidade a
        todas criaria alarme onde não há — foi o erro que já custou caro aqui.

        Os títulos abaixo são inventados de propósito: as onze DC reais ganharam
        cota própria do Plano de Contingência e não passam mais por este
        caminho. A invariante continua valendo para a próxima estação que
        aparecer na fonte antes de ser cadastrada — que é justamente quando ela
        protege.
        """
        dados = {"coletado_em": AGORA.isoformat(), "leituras": [
            {"estacao": "DC-99 Régua nova ainda não cadastrada", "rio": "itajai-mirim",
             "cidade": "itajai", "nivel_m": 9.9, "medido_em": "2026-08-30T00:00:00"},
            {"estacao": "DC-98 Outra régua nova", "rio": "itajai-mirim",
             "cidade": "itajai", "nivel_m": 0.5, "medido_em": "2026-08-30T00:00:00"},
        ]}
        avisos, _, recusas = decidir(dados, {}, AGORA)
        self.assertEqual(avisos, [])
        self.assertEqual(len(recusas), 2)
        self.assertTrue(all("mais de uma régua" in r for r in recusas), recusas)

    def test_regua_de_estuario_mostra_cota_mas_nao_dispara(self):
        """
        As nove réguas de estuário de Itajaí têm cota oficial do Plano de
        Contingência, e mesmo assim não disparam sozinhas: a maré cruza a cota
        sem enchente. A DC-01 marcou 1,24 m às 17:21 de 30/08/2026, acima da sua
        cota de 1,16, e 0,70 m três horas depois.
        """
        dados = {"coletado_em": AGORA.isoformat(), "leituras": [
            {"estacao": "DC-01 Rio Itajaí-Açu - ICMBio/CEPSUL", "rio": "itajai-acu",
             "cidade": "itajai", "nivel_m": 9.9, "medido_em": "2026-08-30T00:00:00"},
        ]}
        avisos, _, recusas = decidir(dados, {}, AGORA)
        self.assertEqual(avisos, [], "9,9 m acima de qualquer cota, e ainda assim não dispara")
        self.assertEqual(len(recusas), 1)
        self.assertIn("maré", recusas[0])

    def test_regua_fora_do_estuario_dispara_com_a_cota_do_plano(self):
        """A DC-11, em Ilhota, não é de maré: com o Plano ela passou a avisar."""
        dados = {"coletado_em": AGORA.isoformat(), "leituras": [
            {"estacao": "DC-11 Rio Itajaí-Açú – Santa Regina (Volta de Cima)",
             "rio": "itajai-acu", "cidade": "ilhota", "nivel_m": 5.5,
             "medido_em": "2026-08-30T00:00:00"},
        ]}
        avisos, _, _ = decidir(dados, {}, AGORA)
        self.assertEqual(len(avisos), 1)
        self.assertEqual(avisos[0]["faixa"], "emergencia")
        self.assertIn("Emergência", avisos[0]["texto"])

    def test_leitura_sem_numero_e_ignorada(self):
        dados = payload(4.6)
        dados["leituras"][0]["nivel_m"] = None
        avisos, _, _ = decidir(dados, {}, AGORA)
        self.assertEqual(avisos, [])


class TestResolver(unittest.TestCase):
    """O panorama e o aviso têm de concordar sobre quem está sendo vigiado."""

    def test_diz_quem_vigia_e_quem_nao(self):
        dados = {"coletado_em": AGORA.isoformat(), "leituras": [
            {"estacao": "Rio do Sul Estação MKS", "rio": "itajai-acu",
             "cidade": "rio-do-sul", "nivel_m": 3.6, "medido_em": "2026-08-30T00:00:00"},
            {"estacao": "DC-01 Rio Itajaí-Açu - ICMBio/CEPSUL", "rio": "itajai-acu",
             "cidade": "itajai", "nivel_m": 1.2, "medido_em": "2026-08-30T00:00:00"},
            {"estacao": "DC-02 Rio Itajaí-Açu - Praça Celso Pereira da Silva",
             "rio": "itajai-acu", "cidade": "itajai", "nivel_m": 1.5,
             "medido_em": "2026-08-30T00:00:00"},
        ]}
        vigiadas, recusas = resolver(dados)
        self.assertEqual([v["leitura"]["cidade"] for v in vigiadas], ["rio-do-sul"])
        self.assertEqual(len(recusas), 2)

    def test_o_panorama_nao_diverge_do_aviso(self):
        """
        Se o relatório dissesse que uma estação está vigiada enquanto o aviso a
        ignora, a pessoa confiaria num alcance que não existe.
        """
        dados = {"coletado_em": AGORA.isoformat(), "leituras": [
            {"estacao": "Rio do Sul Estação MKS", "rio": "itajai-acu",
             "cidade": "rio-do-sul", "nivel_m": 6.6, "medido_em": "2026-08-30T00:00:00"},
            {"estacao": "DC-01 Rio Itajaí-Açu - ICMBio/CEPSUL", "rio": "itajai-acu",
             "cidade": "itajai", "nivel_m": 9.9, "medido_em": "2026-08-30T00:00:00"},
            {"estacao": "DC-02 Rio Itajaí-Açu - Praça Celso Pereira da Silva",
             "rio": "itajai-acu", "cidade": "itajai", "nivel_m": 9.9,
             "medido_em": "2026-08-30T00:00:00"},
        ]}
        vigiadas, _ = resolver(dados)
        avisos, _, _ = decidir(dados, {}, AGORA)
        self.assertEqual(
            {v["leitura"]["estacao"] for v in vigiadas},
            {"Rio do Sul Estação MKS"})
        self.assertTrue({a["estacao"] for a in avisos} <= {v["leitura"]["estacao"] for v in vigiadas})

    def test_leitura_sem_numero_aparece_como_recusa_nao_some(self):
        dados = payload(4.6)
        dados["leituras"][0]["nivel_m"] = None
        vigiadas, recusas = resolver(dados)
        self.assertEqual(vigiadas, [])
        self.assertIn("não trouxe número", recusas[0])


class TestTexto(unittest.TestCase):
    def test_mensagem_traz_o_essencial(self):
        avisos, _, _ = decidir(payload(6.6), {}, AGORA)
        t = avisos[0]["texto"]
        self.assertIn("Rio Do Sul", t)
        self.assertIn("6,60 m", t)
        self.assertIn("Inundação", t)
        self.assertIn("199", t)
        self.assertIn("não é alerta oficial", t)
        self.assertIn("própria régua", t)

    def test_leitura_velha_entra_com_ressalva_mas_entra(self):
        """Leitura antiga mostrando inundação continua sendo o melhor que há."""
        dados = payload(6.6, medido="2026-08-29T20:00:00")
        avisos, _, _ = decidir(dados, {}, AGORA)
        self.assertEqual(len(avisos), 1)
        self.assertIn("⚠️", avisos[0]["texto"])
        self.assertIn("a fonte não atualiza", avisos[0]["texto"])

    def test_escapa_html_do_nome_da_estacao(self):
        """Um & cru no nome faz o Telegram devolver 400 e o aviso não sai."""
        dados = payload(6.6, estacao="Rio do Sul <b>MKS</b> & cia")
        avisos, _, _ = decidir(dados, {}, AGORA)
        self.assertIn("&amp; cia", avisos[0]["texto"])
        self.assertNotIn("<b>MKS</b>", avisos[0]["texto"])


class TestIdade(unittest.TestCase):
    def test_medido_em_e_hora_de_brasilia(self):
        """00:00 em Brasília são 03:00 UTC — a idade tem de dar zero."""
        self.assertAlmostEqual(idade_min("2026-08-30T00:00:00", AGORA), 0.0, places=6)

    def test_sem_horario_devolve_none(self):
        self.assertIsNone(idade_min(None, AGORA))
        self.assertIsNone(idade_min("ontem de tarde", AGORA))


class TestNivelImplausivel(unittest.TestCase):
    """
    O caminho do aviso é o único que fala sozinho, de madrugada. O site recusa
    nível fora de 0–25 m desde sempre; aqui a trava faltava. Não há registro da
    fonte publicando 0,00 m — a página omite a estação sem leitura — mas a
    assimetria era uma trava a menos onde ela custa mais.
    """

    def resolver(self, nivel):
        dados = {"leituras": [{
            "estacao": "Rio do Sul Estação MKS", "rio": "itajai-acu",
            "cidade": "rio-do-sul", "nivel_m": nivel,
            "medido_em": "2026-08-30T22:00",
        }]}
        return alerta_cotas.resolver(dados)

    def test_zero_nao_vira_faixa_normal(self):
        vigiadas, recusas = self.resolver(0.0)
        self.assertEqual(vigiadas, [])
        self.assertTrue(any("não é nível de rio" in m for m in recusas), recusas)

    def test_valor_absurdo_nao_vira_inundacao(self):
        vigiadas, recusas = self.resolver(139.0)
        self.assertEqual(vigiadas, [])
        self.assertTrue(any("139.00 m" in m or "139,00" in m for m in recusas), recusas)

    def test_negativo_recusado(self):
        vigiadas, _ = self.resolver(-1.5)
        self.assertEqual(vigiadas, [])

    def test_nivel_normal_continua_passando(self):
        vigiadas, recusas = self.resolver(6.80)
        self.assertEqual(len(vigiadas), 1, recusas)
        self.assertEqual(vigiadas[0]["faixa"], "inundacao")

    def test_a_recusa_diz_a_faixa_para_quem_le_o_seco(self):
        _, recusas = self.resolver(0.0)
        self.assertTrue(any("0–25 m" in m for m in recusas), recusas)


if __name__ == "__main__":
    unittest.main(verbosity=2)
