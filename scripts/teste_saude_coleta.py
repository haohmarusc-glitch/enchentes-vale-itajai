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
    Diagnostico,
    TOLERANCIA_BRUTO_FONTE_MIN,
    TOLERANCIA_COLETA_MIN,
    TOLERANCIA_FONTE_MIN,
    avaliar,
    avaliar_bruto,
    avaliar_versao,
    deve_avisar,
    regua_de,
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


class TestEstacaoParada(unittest.TestCase):
    """
    O vigia olhava `max(medidos)` — "a fonte publicou ALGUMA coisa". Com doze
    réguas congeladas há seis horas e uma publicando, ele dizia "coleta e fonte
    em dia", que é exatamente a hora em que deveria gritar.
    """

    @staticmethod
    def brasilia(minutos_atras):
        """Hora de Brasília, sem fuso — o formato que a fonte publica."""
        return (AGORA - timedelta(minutes=minutos_atras)).astimezone(
            timezone(timedelta(hours=-3))
        ).replace(tzinfo=None).isoformat()

    def coleta_mista(self):
        return {
            "coletado_em": (AGORA - timedelta(minutes=5)).isoformat(),
            "leituras": [
                {"estacao": "Viva", "nivel_m": 3.5, "medido_em": self.brasilia(10)},
                {"estacao": "Congelada", "nivel_m": 6.8, "medido_em": self.brasilia(360)},
            ],
        }

    def test_uma_estacao_viva_nao_mascara_a_congelada(self):
        diag = avaliar(self.coleta_mista(), AGORA)
        self.assertFalse(diag.ok)
        self.assertIn("Congelada", diag.motivo)

    def test_a_estacao_viva_nao_e_acusada(self):
        diag = avaliar(self.coleta_mista(), AGORA)
        self.assertNotIn("Viva", diag.motivo)

    def test_todas_em_dia_continua_ok(self):
        diag = avaliar(coleta(), AGORA)
        self.assertTrue(diag.ok, diag.motivo)


class TestEstacaoQueSumiu(unittest.TestCase):
    """
    A página da Defesa Civil já veio parcial. Sem esta conta, uma régua some do
    arquivo e nada denuncia: a tela para de mostrá-la, o aviso para de vigiá-la,
    e o vigia segue dizendo que está tudo bem.
    """

    def test_estacao_que_veio_antes_e_sumiu_e_denunciada(self):
        # A coleta traz DC-01; a rodada anterior tinha DC-01 e Brusque.
        diag = avaliar(coleta(), AGORA, vistas_antes={"DC-01", "Brusque"})
        self.assertFalse(diag.ok)
        self.assertIn("Brusque", diag.motivo)

    def test_sem_rodada_anterior_nao_acusa_nada(self):
        """Primeira rodada não tem com o que comparar, e não pode inventar falha."""
        self.assertTrue(avaliar(coleta(), AGORA, vistas_antes=None).ok)
        self.assertTrue(avaliar(coleta(), AGORA, vistas_antes=set()).ok)

    def test_estacao_nova_nao_e_problema(self):
        """Régua que apareceu agora e não estava antes é boa notícia, não falha."""
        diag = avaliar(coleta(leituras=2), AGORA, vistas_antes={"DC-01"})
        self.assertTrue(diag.ok, diag.motivo)


class TestArquivoIlegivel(unittest.TestCase):
    """
    O `ultimo.json` corrompido é o ÚNICO caso em que o site fica sem dado
    nenhum — e era o caso em que o vigia se calava: `return 1` antes do
    `--avisar`. Pior: só `JSONDecodeError` era pego; permissão negada ou disco
    com erro estouravam em traceback, que para o cron é o mesmo silêncio.
    """

    def test_ilegivel_vira_diagnostico_de_falha(self):
        diag = Diagnostico(False, "ultimo.json não pôde ser lido: linha 1", [])
        self.assertFalse(diag.ok)
        self.assertIn("não pôde ser lido", str(diag))

    def test_falha_de_leitura_avisa_como_qualquer_outra(self):
        diag = Diagnostico(False, "ultimo.json não pôde ser lido: x", [])
        self.assertTrue(deve_avisar(diag, {}, AGORA), "primeira falha avisa na hora")



class TestResgateNaoContaDuasVezes(unittest.TestCase):
    """
    Bug A: a mesma régua vinda de duas fontes (primária + resgate) era contada
    como duas estações, e o vigia gritava com a leitura velha ao lado da nova.
    A régua é UMA; está viva se qualquer das duas está fresca.
    """

    def _local(self, minutos_atras):
        return (AGORA - timedelta(minutes=minutos_atras)).astimezone(
            timezone(timedelta(hours=-3))).replace(tzinfo=None).isoformat()

    def coleta_com_resgate(self, primaria_min, resgate_min):
        return {
            "coletado_em": (AGORA - timedelta(minutes=3)).isoformat(),
            "leituras": [
                {"estacao": "Blumenau", "rio": "itajai-acu", "cidade": "blumenau",
                 "nivel_m": 7.5, "medido_em": self._local(primaria_min)},
                {"estacao": "Blumenau (AlertaBlu)", "resgate_de": "Blumenau",
                 "rio": "itajai-acu", "cidade": "blumenau",
                 "nivel_m": 7.5, "medido_em": self._local(resgate_min)},
            ],
        }

    def test_primaria_velha_mas_resgate_fresco_nao_e_falha(self):
        # Primária há 6h, resgate há 40 min: a régua está viva.
        d = avaliar(self.coleta_com_resgate(360, 40), AGORA)
        self.assertTrue(d.ok, d.motivo)
        self.assertNotIn("Blumenau", d.motivo)

    def test_as_duas_velhas_e_falha_uma_vez_so(self):
        # Ambas paradas: falha, mas Blumenau aparece UMA vez, não duas.
        d = avaliar(self.coleta_com_resgate(360, 200), AGORA)
        self.assertFalse(d.ok)
        self.assertEqual(d.motivo.count("Blumenau"), 1, d.motivo)

    def test_regua_de_usa_o_resgate_de(self):
        self.assertEqual(regua_de({"estacao": "Blumenau (AlertaBlu)",
                                    "resgate_de": "Blumenau"}), "Blumenau")
        self.assertEqual(regua_de({"estacao": "DC-02"}), "DC-02")


class TestItajaiNaoMascara(unittest.TestCase):
    """
    A régua-a-régua não pode voltar a mascarar: Itajaí tem onze réguas de
    títulos distintos, e uma fresca não cobre as outras dez.
    """

    def test_uma_viva_nao_esconde_dez_congeladas(self):
        agora = AGORA
        def local(min):
            return (agora - timedelta(minutes=min)).astimezone(
                timezone(timedelta(hours=-3))).replace(tzinfo=None).isoformat()
        leituras = [{"estacao": "DC-01", "cidade": "itajai", "rio": "itajai-acu",
                     "nivel_m": 1.2, "medido_em": local(30)}]
        leituras += [{"estacao": f"DC-{i:02d}", "cidade": "itajai", "rio": "itajai-acu",
                      "nivel_m": 1.2, "medido_em": local(400)} for i in range(2, 12)]
        d = avaliar({"coletado_em": (agora - timedelta(minutes=3)).isoformat(),
                     "leituras": leituras}, agora)
        self.assertFalse(d.ok)
        self.assertIn("10 de 11", d.motivo)

def bruto(minutos_atras=5, medido_minutos_atras=30, com_silenciosas=True):
    """
    Um ultimo_nivel_sc.json com as idades pedidas. Espelha o real: uma estação
    fresca e várias silenciosas (medido_em None), que NÃO podem virar falha.
    """
    quando = AGORA - timedelta(minutes=minutos_atras)
    medido = (AGORA - timedelta(minutes=medido_minutos_atras)).astimezone(
        timezone(timedelta(hours=-3))).replace(tzinfo=None)
    leituras = [{"estacao": "SDC-SC Taió", "cidade": "taio", "nivel_bruto_m": 5.3,
                 "medido_em": medido.isoformat()}]
    if com_silenciosas:
        leituras += [{"estacao": f"SDC-SC Muda {i}", "cidade": None,
                      "nivel_bruto_m": None, "medido_em": None} for i in range(18)]
    return {"coletado_em": quando.isoformat(), "leituras": leituras}


class TestAvaliarBruto(unittest.TestCase):
    def test_bruto_em_dia(self):
        d = avaliar_bruto(bruto(), AGORA)
        self.assertTrue(d.ok, d.motivo)

    def test_silenciosas_nao_derrubam(self):
        # 18 sem leitura + 1 fresca = em dia (é o normal do bruto estadual).
        d = avaliar_bruto(bruto(com_silenciosas=True), AGORA)
        self.assertTrue(d.ok, d.motivo)

    def test_coletor_parado_e_falha(self):
        # O caso real: o cron do coletor estadual sumiu; coletado_em congelou.
        d = avaliar_bruto(bruto(minutos_atras=13 * 60), AGORA)
        self.assertFalse(d.ok)
        self.assertIn("não roda", d.motivo)

    def test_fonte_estadual_travada_dentro_da_folga(self):
        d = avaliar_bruto(bruto(medido_minutos_atras=TOLERANCIA_BRUTO_FONTE_MIN - 10), AGORA)
        self.assertTrue(d.ok, d.motivo)

    def test_fonte_estadual_travada_alem_da_folga(self):
        d = avaliar_bruto(bruto(medido_minutos_atras=TOLERANCIA_BRUTO_FONTE_MIN + 30), AGORA)
        self.assertFalse(d.ok)
        self.assertIn("leitura nova", d.motivo)

    def test_sem_arquivo_e_falha(self):
        d = avaliar_bruto(None, AGORA)
        self.assertFalse(d.ok)
        self.assertIn("cabeceiras", d.motivo)


class CodigoAtrasado(unittest.TestCase):
    """
    O vigia precisa ver o DEPLOY que não desembarcou.

    A VPS tem dois checkouts: o cron da coleta roda de `/opt`, o trabalho manual
    acontece em `/root`. Um `git pull` no segundo não muda nada no primeiro, e o
    teste feito à mão passa — dando a impressão de que o conserto está no ar.

    O resto do vigia é cego para isso por desenho: compara cada coleta com a
    ANTERIOR, então vê régua que sumiu e não vê régua que nunca chegou. Um
    deploy que não desembarcou não perde nada, logo não acusa nada.
    """

    def _git(self, respostas):
        """Um git de mentira: mapeia o primeiro argumento para (código, saída)."""
        return lambda args: respostas.get(args[0], (0, ""))

    def test_em_dia_nao_reclama(self):
        d = avaliar_versao(self._git({"rev-list": (0, "0")}))
        self.assertTrue(d.ok)
        self.assertTrue(any("em dia" in x for x in d.detalhes))

    def test_atrasado_e_FALHA_e_diz_quantos_commits(self):
        d = avaliar_versao(self._git({"rev-list": (0, "3")}))
        self.assertFalse(d.ok)
        self.assertIn("3 commits atrás", d.motivo)
        self.assertIn("versão antiga", d.motivo)

    def test_um_commit_nao_vira_plural(self):
        d = avaliar_versao(self._git({"rev-list": (0, "1")}))
        self.assertIn("1 commit atrás", d.motivo)
        self.assertNotIn("commits", d.motivo)

    def test_sem_rede_NAO_vira_alarme(self):
        """
        Falhar em conferir não é o mesmo que estar atrasado.

        Uma VPS com rede ruim gritaria "código atrasado" por engano, e alarme
        falso de deploy ensina a ignorar o alarme verdadeiro de cheia.
        """
        d = avaliar_versao(self._git({"fetch": (128, "")}))
        self.assertTrue(d.ok, "git fetch falhando não pode virar falha do vigia")
        self.assertTrue(any("não deu para conferir" in x for x in d.detalhes))

    def test_sem_git_ou_fora_de_checkout_NAO_vira_alarme(self):
        d = avaliar_versao(self._git({"rev-parse": (127, "")}))
        self.assertTrue(d.ok)
        self.assertTrue(any("não é um checkout git" in x for x in d.detalhes))

    def test_saida_estranha_do_git_NAO_vira_alarme(self):
        for saida in ("", "abc", "-1"):
            d = avaliar_versao(self._git({"rev-list": (0, saida)}))
            self.assertTrue(d.ok, f"saída {saida!r} não podia virar falha")

    def test_a_MANCHETE_do_aviso_nao_mente_sobre_a_coleta(self):
        """
        Com a coleta viva e só o código atrasado, dizer "a coleta parou" manda
        procurar defeito onde não há — e ensina a duvidar do próximo aviso, que
        pode ser o da cheia.
        """
        d = Diagnostico(False, "o código em /opt está 3 commits atrás", [])
        so_versao = texto(d, so_versao=True)
        self.assertIn("código no ar está atrasado", so_versao)
        self.assertNotIn("coleta de nível parou", so_versao)
        self.assertIn("git pull", so_versao, "o aviso tem de trazer o conserto")

        parou = texto(d, so_versao=False)
        self.assertIn("coleta de nível parou", parou)


if __name__ == "__main__":
    unittest.main(verbosity=2)
