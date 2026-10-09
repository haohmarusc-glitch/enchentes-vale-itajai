#!/usr/bin/env python3
"""Testes do baixador do histórico da rede estadual (DCSC).

O teste que importa mais é o `TesteOConsolidadorLeOQueEsteScriptGrava`: o par
baixador→consolidador só serve se o formato casar, e casar "de vista" não conta.
"""

import json
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import baixar_historico_dcsc as bh  # noqa: E402
import consolidar_historico_dcsc as cons  # noqa: E402

UTC = timezone.utc


def resposta_com(itens):
    return {"data": {"historic": {"items": itens, "totalCount": len(itens)}}}


class TesteJanelas(unittest.TestCase):
    def teste_quebra_sem_buraco_e_sem_sobra(self):
        ini = datetime(2026, 1, 1, tzinfo=UTC)
        fim = ini + timedelta(days=150)
        js = bh.janelas(ini, fim, maximo_dias=60)
        self.assertEqual(len(js), 3)
        self.assertEqual(js[0][0], ini)
        self.assertEqual(js[-1][1], fim)
        for (_, a), (b, _) in zip(js, js[1:]):
            self.assertEqual(a, b, "janela seguinte tem de começar onde a anterior terminou")
        for a, b in js:
            self.assertLessEqual(b - a, timedelta(days=60))

    def teste_periodo_curto_vira_uma_janela(self):
        ini = datetime(2026, 1, 1, tzinfo=UTC)
        self.assertEqual(len(bh.janelas(ini, ini + timedelta(days=3))), 1)

    def teste_periodo_vazio_ou_invertido_nao_gera_janela(self):
        ini = datetime(2026, 1, 1, tzinfo=UTC)
        self.assertEqual(bh.janelas(ini, ini), [])
        self.assertEqual(bh.janelas(ini, ini - timedelta(days=1)), [])


class TesteProfundidade(unittest.TestCase):
    """A API só volta ~89 dias; pedir mais só rende 'Operação bloqueada'."""

    def teste_pedido_fundo_demais_e_puxado_para_o_limite(self):
        agora = datetime(2026, 9, 13, tzinfo=UTC)
        ini, cortou = bh.limitar_profundidade(agora - timedelta(days=365), agora)
        self.assertTrue(cortou)
        self.assertEqual(ini, agora - timedelta(days=bh.PROFUNDIDADE_MAX_DIAS))

    def teste_pedido_dentro_do_limite_passa_intacto(self):
        agora = datetime(2026, 9, 13, tzinfo=UTC)
        pedido = agora - timedelta(days=10)
        ini, cortou = bh.limitar_profundidade(pedido, agora)
        self.assertFalse(cortou)
        self.assertEqual(ini, pedido)


class TesteNomeDaJanela(unittest.TestCase):
    def teste_mesmo_padrao_das_janelas_baixadas_no_pc(self):
        self.assertEqual(
            bh.nome_da_janela(datetime(2023, 11, 1), datetime(2023, 11, 15)),
            "20231101T000000_20231115T000000.json")


class TestePedir(unittest.TestCase):
    def teste_errors_da_api_vira_Bloqueado_e_nao_insiste_para_sempre(self):
        chamadas = []

        def transporte(payload):
            chamadas.append(payload)
            return {"errors": [{"message": "Operação bloqueada."}]}

        with self.assertRaises(bh.Bloqueado) as ctx:
            bh.pedir("DCSC-00006", datetime(2020, 1, 1, tzinfo=UTC),
                     datetime(2020, 2, 1, tzinfo=UTC), "HOUR_1",
                     transporte=transporte, dormir=lambda _s: None)
        self.assertIn("Operação bloqueada.", str(ctx.exception))
        self.assertEqual(len(chamadas), 2, "duas tentativas, não quatro")

    def teste_erro_de_rede_e_tentado_de_novo(self):
        chamadas = []

        def transporte(payload):
            chamadas.append(payload)
            if len(chamadas) == 1:
                raise OSError("conexão caiu")
            return resposta_com([{"ts": "2026-09-01T00:00:00.000", "rio_nivel": 1.0}])

        _, resp = bh.pedir("DCSC-00006", datetime(2026, 9, 1, tzinfo=UTC),
                           datetime(2026, 9, 2, tzinfo=UTC), "HOUR_1",
                           transporte=transporte, dormir=lambda _s: None)
        self.assertEqual(len(chamadas), 2)
        self.assertEqual(bh.quantos_itens(resp), 1)

    def teste_manda_o_operationName_e_o_client_que_a_api_exige(self):
        vistos = {}

        def transporte(payload):
            vistos.update(payload)
            return resposta_com([])

        bh.pedir("DCSC-00013", datetime(2026, 9, 1, tzinfo=UTC),
                 datetime(2026, 9, 2, tzinfo=UTC), "MIN_10",
                 transporte=transporte, dormir=lambda _s: None)
        self.assertEqual(vistos["operationName"], "Historic")
        self.assertIn('client: "secretaria-de-defesa-civil"', vistos["query"])
        self.assertTrue(vistos["variables"]["startDate"].endswith("Z"),
                        "startDate vai em UTC com Z; o ts que volta é de Brasília")


class TesteBaixarEstacao(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.destino = Path(self.tmp.name)
        self.addCleanup(self.tmp.cleanup)
        self.ini = datetime(2026, 9, 1, tzinfo=UTC)
        self.fim = datetime(2026, 9, 10, tzinfo=UTC)

    def teste_grava_uma_janela_e_nao_rebaixa_na_segunda_vez(self):
        chamadas = []

        def transporte(payload):
            chamadas.append(payload)
            return resposta_com([{"ts": "2026-09-01T00:00:00.000", "codigo": "DCSC-00006",
                                  "rio_nivel": 2.5}])

        r1 = bh.baixar_estacao("DCSC-00006", self.ini, self.fim, "MIN_10", self.destino,
                               transporte=transporte, dormir=lambda _s: None)
        self.assertEqual(r1["janelas"], 1)
        self.assertEqual(r1["itens"], 1)

        r2 = bh.baixar_estacao("DCSC-00006", self.ini, self.fim, "MIN_10", self.destino,
                               transporte=transporte, dormir=lambda _s: None)
        self.assertEqual(r2["janelas"], 0)
        self.assertEqual(r2["puladas"], 1)
        self.assertEqual(len(chamadas), 1, "a segunda execução não pode repetir a chamada")

    def teste_janela_que_falhou_nao_vira_arquivo(self):
        """Arquivo de janela falhada seria um buraco silencioso: a próxima execução pularia."""
        def transporte(_payload):
            return {"errors": [{"message": "Operação bloqueada."}]}

        r = bh.baixar_estacao("DCSC-00006", self.ini, self.fim, "MIN_10", self.destino,
                              transporte=transporte, dormir=lambda _s: None)
        self.assertEqual(r["janelas"], 0)
        self.assertEqual(len(r["falhas"]), 1)
        self.assertEqual(list((self.destino / "DCSC-00006").glob("*.json")), [])


class TesteOConsolidadorLeOQueEsteScriptGrava(unittest.TestCase):
    """O par só serve se o formato casar. Aqui o consolidador lê a saída real do baixador."""

    def teste_ida_e_volta(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        destino = Path(tmp.name)
        itens = [{"ts": f"2026-09-01T0{h}:00:00.000", "codigo": "DCSC-00013",
                  "rio_nivel": 2.0 + h / 10, "chuva_mm": 0.0} for h in range(5)]

        bh.baixar_estacao("DCSC-00013", datetime(2026, 9, 1, tzinfo=UTC),
                          datetime(2026, 9, 5, tzinfo=UTC), "HOUR_1", destino,
                          transporte=lambda _p: resposta_com(itens),
                          dormir=lambda _s: None)

        lido = cons.ler_pasta(destino)
        self.assertIn("DCSC-00013", lido)
        self.assertEqual(len(lido["DCSC-00013"]["itens"]), 5)
        self.assertEqual(lido["DCSC-00013"]["janelas"], 1)
        self.assertTrue(lido["DCSC-00013"]["coletas"], "o coletado_em_utc tem de chegar")
        self.assertAlmostEqual(
            max(i["rio_nivel"] for i in lido["DCSC-00013"]["itens"].values()), 2.4)

    def teste_o_ts_vai_para_o_csv_sem_conversao_de_fuso(self):
        """`ts` é hora de Brasília (provado no consolidador). Converter aqui deslocaria 3 h."""
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        destino = Path(tmp.name)
        bh.baixar_estacao("DCSC-00013", datetime(2026, 9, 1, tzinfo=UTC),
                          datetime(2026, 9, 2, tzinfo=UTC), "HOUR_1", destino,
                          transporte=lambda _p: resposta_com(
                              [{"ts": "2026-09-01T05:20:00.000", "codigo": "DCSC-00013",
                                "rio_nivel": 7.07}]),
                          dormir=lambda _s: None)
        lido = cons.ler_pasta(destino)
        self.assertIn("2026-09-01T05:20:00.000", lido["DCSC-00013"]["itens"])


class TesteSemanasFechadas(unittest.TestCase):
    """O modo do cron: semanas fixas no calendário, para o nome do arquivo não mudar entre execuções."""

    def teste_segunda_a_segunda_dentro_do_alcance_e_terminadas(self):
        agora = datetime(2026, 10, 9, 21, 0, tzinfo=UTC)  # sexta
        s = bh.semanas_fechadas(agora)
        self.assertTrue(s)
        for ini, fim in s:
            self.assertEqual(ini.weekday(), 0)
            self.assertEqual((ini.hour, ini.minute), (0, 0))
            self.assertEqual(fim - ini, timedelta(days=7))
        self.assertGreaterEqual(s[0][0], agora - timedelta(days=bh.PROFUNDIDADE_MAX_DIAS))
        self.assertEqual(s[-1][1], datetime(2026, 10, 5, tzinfo=UTC), "a semana corrente não fecha")
        for (_, f), (i, _) in zip(s, s[1:]):
            self.assertEqual(f, i, "semanas contíguas, sem buraco")

    def teste_folga_de_um_dia_depois_do_fim_da_semana(self):
        # Segunda 12:00: a semana que terminou à 00:00 ainda pode receber dado atrasado.
        s = bh.semanas_fechadas(datetime(2026, 10, 5, 12, 0, tzinfo=UTC))
        self.assertEqual(s[-1][1], datetime(2026, 9, 28, tzinfo=UTC))
        s = bh.semanas_fechadas(datetime(2026, 10, 6, 0, 0, tzinfo=UTC))
        self.assertEqual(s[-1][1], datetime(2026, 10, 5, tzinfo=UTC))

    def teste_o_nome_e_o_mesmo_em_execucoes_diferentes(self):
        a = bh.semanas_fechadas(datetime(2026, 10, 9, 3, 0, tzinfo=UTC))
        b = bh.semanas_fechadas(datetime(2026, 10, 10, 23, 0, tzinfo=UTC))
        comuns = set(a) & set(b)
        self.assertGreater(len(comuns), 10)
        ini, fim = sorted(comuns)[0]
        self.assertEqual(bh.nome_acumulado("DCSC-00013", ini, fim),
                         f"DCSC-00013/{ini:%Y%m%dT%H%M%S}_{fim:%Y%m%dT%H%M%S}.json.gz")


class TesteAcumularEstacao(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.destino = Path(self.tmp.name)
        self.addCleanup(self.tmp.cleanup)
        self.semanas = [(datetime(2026, 9, 21, tzinfo=UTC), datetime(2026, 9, 28, tzinfo=UTC)),
                        (datetime(2026, 9, 28, tzinfo=UTC), datetime(2026, 10, 5, tzinfo=UTC))]

    def acumular(self, transporte, ja=frozenset()):
        return bh.acumular_estacao("DCSC-00013", self.semanas, "MIN_10", self.destino, set(ja),
                                   transporte=transporte, dormir=lambda _s: None)

    def teste_pula_o_que_o_acervo_tem_e_grava_gz_que_o_consolidador_le(self):
        chamadas = []

        def transporte(payload):
            chamadas.append(payload["variables"]["startDate"])
            return resposta_com([{"ts": "2026-09-28T05:20:00.000", "codigo": "DCSC-00013", "rio_nivel": 7.07}])

        ja = {bh.nome_acumulado("DCSC-00013", *self.semanas[0])}
        r = self.acumular(transporte, ja)
        self.assertEqual(r["ja_no_acervo"], 1)
        self.assertEqual(len(chamadas), 1, "a semana do acervo não pode ser pedida de novo")
        self.assertEqual(r["novas"], [bh.nome_acumulado("DCSC-00013", *self.semanas[1])])
        self.assertTrue((self.destino / r["novas"][0]).exists())
        lido = cons.ler_pasta(self.destino)
        self.assertIn("2026-09-28T05:20:00.000", lido["DCSC-00013"]["itens"], "ts como veio, sem fuso")

    def teste_o_consolidador_junta_o_pc_e_o_acervo_sem_duplicar(self):
        item = {"ts": "2026-09-28T05:20:00.000", "codigo": "DCSC-00013", "rio_nivel": 7.07}
        self.acumular(lambda _p: resposta_com([item]))
        pc = Path(self.tmp.name) / "pc"
        bh.baixar_estacao("DCSC-00013", datetime(2026, 9, 27, tzinfo=UTC), datetime(2026, 9, 29, tzinfo=UTC),
                          "MIN_10", pc, transporte=lambda _p: resposta_com(
                              [item, {**item, "ts": "2026-09-27T05:20:00.000"}]), dormir=lambda _s: None)
        junto = cons.juntar([cons.ler_pasta(pc), cons.ler_pasta(self.destino / "DCSC-00013")])
        self.assertEqual(sorted(junto["DCSC-00013"]["itens"]),
                         ["2026-09-27T05:20:00.000", "2026-09-28T05:20:00.000"])

    def teste_semana_vazia_nao_vira_arquivo(self):
        r = self.acumular(lambda _p: resposta_com([]))
        self.assertEqual((r["vazias"], r["novas"], r["falhas"]), (2, [], []))
        self.assertEqual(list(self.destino.rglob("*.gz")), [])

    def teste_item_de_outra_estacao_reprova_a_semana(self):
        r = self.acumular(lambda _p: resposta_com([{"ts": "2026-09-28T05:20:00.000", "codigo": "DCSC-00019"}]))
        self.assertEqual(r["novas"], [])
        self.assertEqual(len(r["falhas"]), 2)
        self.assertEqual(list(self.destino.rglob("*.gz")), [])

    def teste_recusa_da_api_vira_falha_sem_arquivo(self):
        r = self.acumular(lambda _p: {"errors": [{"message": "Operação bloqueada."}]})
        self.assertEqual(len(r["falhas"]), 2)
        self.assertEqual(list(self.destino.rglob("*.gz")), [])


class TesteCodigosDaCadeia(unittest.TestCase):
    def teste_le_os_codigos_dcsc_do_estacoes_json(self):
        codigos = bh.codigos_da_cadeia()
        self.assertTrue(codigos, "estacoes.json tem codigo_dcsc")
        self.assertTrue(all(c.startswith("DCSC-") for c in codigos))
        self.assertEqual(len(codigos), len(set(codigos)), "sem repetidos")


if __name__ == "__main__":
    unittest.main()
