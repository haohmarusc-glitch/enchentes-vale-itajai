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


class ReguaComCotaPropria(unittest.TestCase):
    """
    A metade que faltava: cota que mora na RÉGUA, não na cidade.

    Itajaí não tem cota de cidade — as onze réguas da Defesa Civil têm cota
    própria, cada uma com o seu zero. Enquanto a conferência percorria só
    `rios[].cidades[]`, a cidade na foz dos dois rios não aparecia em NENHUMA
    linha: o guarda contra "cor sem alarme" não olhava justamente os onze pinos
    que o Monitor desenha.
    """

    ESTACOES = {
        "rios": {},
        "estacoes_tempo_real": [
            {"codigo": "DC-10", "titulo": "DC-10 Limoeiro", "tipo": None,
             "cotas_m": {"atencao": 8.0, "alerta": 9.0, "emergencia": 10.0}},
            {"codigo": "DC-01", "titulo": "DC-01 CEPSUL", "alerta_automatico": False,
             "motivo_sem_alerta": "régua de estuário: a maré cruza a cota sem enchente",
             "cotas_m": {"atencao": 1.16, "alerta": 1.36, "emergencia": 1.56}},
            {"codigo": "DC-00", "titulo": "DC-00 Pluviômetro", "tipo": "pluviometro",
             "cotas_m": {}},
        ],
    }

    def test_regua_com_cota_propria_ENTRA_na_conferencia(self):
        dados = {"leituras": [leitura("DC-10 Limoeiro", cidade="itajai",
                                      rio="itajai-mirim", nivel=4.6)]}
        linhas = cf.avaliar(dados, self.ESTACOES)
        alvos = [r for r in linhas if r["estacao"] == "DC-10 Limoeiro"]
        self.assertEqual(len(alvos), 1, "a régua com cota própria tem de ser conferida")
        self.assertEqual(alvos[0]["escopo"], "regua")
        self.assertTrue(alvos[0]["vigiada"])
        self.assertFalse(alvos[0]["buraco"])

    def test_regua_de_mare_NAO_e_cobrada_porque_o_mapa_tambem_nao_a_pinta(self):
        """
        Ela é recusada pelo alarme de propósito, e o `reguasNoMapa` a deixa sem
        cor pelo mesmo motivo. Os dois lados concordam: não há discordância a
        apontar, e cobrá-la encheria a saída de falso positivo — que é como um
        guarda para de ser lido.
        """
        dados = {"leituras": [leitura("DC-01 CEPSUL", cidade="itajai",
                                      rio="itajai-acu", nivel=1.24)]}
        linhas = cf.avaliar(dados, self.ESTACOES)
        self.assertEqual([r for r in linhas if r["estacao"] == "DC-01 CEPSUL"], [])

    def test_pluviometro_nao_entra(self):
        dados = {"leituras": [leitura("DC-00 Pluviômetro", cidade="itajai",
                                      rio="itajai-acu", nivel=0.0)]}
        self.assertEqual(cf.avaliar(dados, self.ESTACOES), [])

    def test_regua_que_pinta_e_o_alarme_recusa_por_motivo_NOVO_e_BURACO(self):
        """
        O caso que este arquivo inteiro existe para pegar, agora no nível da
        régua: o pino pinta e o Telegram fica mudo por um motivo que ninguém
        decidiu aceitar.

        Aqui a leitura chega sem rio nem cidade — o alarme recusa com
        "estação sem rio/cidade cadastrados", que NÃO está na lista fechada.
        Antes desta conferência olhar réguas, essa recusa passaria despercebida:
        Itajaí não aparecia em linha nenhuma.
        """
        estacoes = {"rios": {}, "estacoes_tempo_real": [
            {"codigo": "DC-99", "titulo": "Régua inventada para o teste",
             "cotas_m": {"atencao": 2.0}},
        ]}
        dados = {"leituras": [{"estacao": "Régua inventada para o teste",
                               "nivel_m": 2.4, "medido_em": "2026-09-04T03:00:00"}]}
        linhas = cf.avaliar(dados, estacoes)
        alvos = [r for r in linhas if r["escopo"] == "regua"]
        self.assertEqual(len(alvos), 1)
        self.assertFalse(alvos[0]["vigiada"])
        self.assertTrue(alvos[0]["buraco"], f"motivos: {alvos[0]['motivos']}")

    def test_as_reguas_reais_do_cadastro_que_pintam_sao_as_que_o_site_pintaria(self):
        """
        Contra o cadastro de verdade: hoje só DC-10 e DC-11 pintam por cota
        própria — as outras nove estão travadas pela maré. Se alguém destravar
        uma sem passar pelo `medir_mare.py`, esta linha muda e o teste conta.
        """
        reais = json.loads((RAIZ / "data/estacoes.json").read_text(encoding="utf-8"))
        codigos = set()
        por_titulo = {e.get("titulo"): e for e in reais["estacoes_tempo_real"]}
        for titulo in cf.reguas_que_pintam(reais):
            codigos.add(por_titulo[titulo].get("codigo"))
        self.assertEqual(codigos, {"DC-10", "DC-11"})
