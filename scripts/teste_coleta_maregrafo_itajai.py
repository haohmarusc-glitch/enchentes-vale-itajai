#!/usr/bin/env python3
"""Testes do coletor do marégrafo de Itajaí (`coleta_maregrafo_itajai.py`).

    python3 scripts/teste_coleta_maregrafo_itajai.py
"""
import html
import json
import sys
import tempfile
import unittest
import unittest.mock
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import coleta_maregrafo_itajai as c

AGORA = datetime(2026, 11, 23, 12, 40, tzinfo=timezone.utc)  # 09:40 em Brasília
BRT = timezone(timedelta(hours=-3))


def leitura(t: datetime, dhn: float, *, orto=2.838, red=0.4455, mexe_ibge=0.0, mexe_dhn=0.0) -> dict:
    ibge = round(dhn - red, 4)
    return {"datahora": t.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z"),
            "nivel_dhn": round(dhn + mexe_dhn, 4), "nivel_ibge": round(ibge + mexe_ibge, 4),
            "nivel_bruto": round(orto - ibge, 4), "altitude_ortometrica": orto, "nivel_reducao": red}


def previsoes(inicio: datetime, horas: int = 30) -> list[dict]:
    """Uma senoide semidiurna de 5 em 5 min, no zero da DHN, com `-03:00` como a fonte."""
    import math
    saida = []
    for i in range(horas * 12):
        t = inicio + timedelta(minutes=5 * i)
        v = 0.7 + 0.45 * math.cos(2 * math.pi * (i * 5) / (12.42 * 60))
        saida.append({"datahora": t.astimezone(BRT).isoformat(), "nivel_dhn": round(v, 4)})
    return saida


def maregrafo(leituras: list[dict], prev: list[dict] | None = None, ident="MRG01") -> dict:
    return {"id": ident, "nome": "Cabeçudas Iate Clube", "leituras": leituras,
            "previsoes": prev if prev is not None else previsoes(AGORA - timedelta(hours=6)),
            "cotas": {"dhn": {"habilitado": False}}}


def pagina(m: dict | None) -> str:
    props = {"secao": "maregrafo", "maregrafo": m} if m is not None else {"secao": "maregrafo"}
    dados = json.dumps({"component": "Monitoramento", "props": props})
    return f'<html><body><div id="app" data-page="{html.escape(dados, quote=True)}"></div></body></html>'


def serie(fim: datetime, n: int = 6, dhn: float = 0.56) -> list[dict]:
    return [leitura(fim - timedelta(minutes=10 * (n - 1 - i)), dhn + i / 100) for i in range(n)]


class Contas(unittest.TestCase):
    def test_leitura_que_fecha_e_coerente(self):
        self.assertTrue(c.leitura_coerente(leitura(AGORA, 0.56)))

    def test_ibge_que_nao_fecha_com_o_sensor_nao_vira_numero(self):
        self.assertFalse(c.leitura_coerente(leitura(AGORA, 0.56, mexe_ibge=0.05)))

    def test_dhn_que_nao_fecha_com_a_reducao_nao_vira_numero(self):
        self.assertFalse(c.leitura_coerente(leitura(AGORA, 0.56, mexe_dhn=0.05)))

    def test_campo_faltando_ou_booleano_nao_vira_numero(self):
        for campo, valor in (("nivel_bruto", None), ("nivel_dhn", True)):
            with self.subTest(campo):
                l = leitura(AGORA, 0.56)
                l[campo] = valor
                self.assertFalse(c.leitura_coerente(l))

    def test_nivel_implausivel_nao_vira_numero(self):
        self.assertFalse(c.leitura_coerente(leitura(AGORA, 9.0)))


class Pagina(unittest.TestCase):
    def test_le_o_mrg01_do_data_page(self):
        m = c.ler_maregrafo(pagina(maregrafo(serie(AGORA))))
        self.assertEqual(m["id"], "MRG01")

    def test_outro_maregrafo_ou_pagina_sem_ele_falha(self):
        with self.assertRaises(c.Falha):
            c.ler_maregrafo(pagina(maregrafo(serie(AGORA), ident="MRG02")))
        with self.assertRaises(c.Falha):
            c.ler_maregrafo(pagina(None))
        with self.assertRaises(c.Falha):
            c.ler_maregrafo("<html>tela de manutenção</html>")


class Resumo(unittest.TestCase):
    def resumo(self, leituras, prev=None, agora=AGORA):
        return c.resumo_publicavel(maregrafo(leituras, prev), agora, AGORA.isoformat())

    def test_medindo_leva_nivel_previsto_e_diferenca_da_mesma_estacao(self):
        r = self.resumo(serie(AGORA - timedelta(minutes=10)))
        u = r["ultima_medicao"]
        self.assertEqual(r["situacao"], "medindo")
        self.assertEqual(u["medido_em"], "2026-11-23T09:30:00", "UTC com Z vira Brasília sem fuso")
        self.assertAlmostEqual(u["observada_m"], 0.61)
        self.assertIsNotNone(u["astronomica_m"])
        self.assertAlmostEqual(u["diferenca_observado_astronomica_m"], round(u["observada_m"] - u["astronomica_m"], 3))

    def test_referencia_vertical_e_a_escrita_na_fonte(self):
        r = self.resumo(serie(AGORA))
        ref = r["referencia_vertical"]
        self.assertEqual(ref["status"], "confirmada")
        self.assertIn("DHN", ref["descricao"])
        self.assertIn("nivel_dhn", ref["fonte"])
        self.assertEqual(r["unidade"], "m")

    def test_leitura_antiga_ou_do_futuro_nao_leva_numero(self):
        for nome, fim in (("antiga", AGORA - timedelta(minutes=61)), ("futuro", AGORA + timedelta(minutes=20))):
            with self.subTest(nome):
                r = self.resumo(serie(fim))
                self.assertEqual(r["situacao"], "sem_medicao_recente")
                self.assertNotIn("observada_m", r["ultima_medicao"])

    def test_ultima_incoerente_sai_e_vale_a_anterior(self):
        ls = serie(AGORA - timedelta(minutes=10))
        ls[-1]["nivel_ibge"] += 0.3
        r = self.resumo(ls)
        self.assertEqual(r["ultima_medicao"]["medido_em"], "2026-11-23T09:20:00")
        self.assertEqual(r["leituras_coerentes"], 5)
        self.assertEqual(r["leituras_na_fonte"], 6)

    def test_sem_previsao_no_mesmo_horario_nao_ha_diferenca(self):
        longe = previsoes(AGORA + timedelta(hours=5))  # começa depois da leitura
        r = self.resumo(serie(AGORA), longe)
        self.assertIsNone(r["ultima_medicao"]["astronomica_m"])
        self.assertIsNone(r["ultima_medicao"]["diferenca_observado_astronomica_m"])

    def test_sem_leitura_nenhuma(self):
        r = self.resumo([])
        self.assertEqual(r["situacao"], "sem_medicao")
        self.assertIsNone(r["ultima_medicao"])

    def test_extremos_previstos_tem_altura_dhn_horario_de_brasilia_e_so_futuros(self):
        r = self.resumo(serie(AGORA))
        ext = r["previsao"]["extremos"]
        self.assertEqual(len(ext), c.N_EXTREMOS)
        self.assertTrue(all(e["quando"] >= "2026-11-23T09:40" for e in ext))
        self.assertEqual({e["tipo"] for e in ext}, {"preamar", "baixamar"})
        self.assertTrue(all(0.2 <= e["altura_m"] <= 1.2 for e in ext))
        self.assertIn("DHN", r["previsao"]["referencia"])

    def test_texto_nunca_chama_a_diferenca_de_mare_meteorologica(self):
        texto = json.dumps(self.resumo(serie(AGORA)), ensure_ascii=False).lower()
        self.assertNotIn("maré meteorológica", texto)
        self.assertNotIn("mare meteorologica", texto)


class Publicar(unittest.TestCase):
    def setUp(self):
        self.dir = Path(tempfile.mkdtemp())
        (self.dir / "tempo-real").mkdir()
        self.destino = self.dir / c.ARQUIVO_PUBLICAVEL
        import comum
        self.p1 = unittest.mock.patch.object(comum, "DADOS", self.dir)
        self.p1.start()
        self.addCleanup(self.p1.stop)

    def test_grava_o_arquivo(self):
        with unittest.mock.patch("sys.stdout"):
            rc = c.publicar(AGORA, baixador=lambda: pagina(maregrafo(serie(AGORA))))
        self.assertEqual(rc, 0)
        d = json.loads(self.destino.read_text(encoding="utf-8"))
        self.assertEqual(d["versao"], 1)
        self.assertEqual(d["estacao"]["id"], "itajai-cabecudas")

    def test_falha_apaga_o_anterior(self):
        self.destino.write_text('{"versao": 1}', encoding="utf-8")

        def cai():
            raise TimeoutError("sem resposta")
        with unittest.mock.patch("sys.stderr"):
            rc = c.publicar(AGORA, baixador=cai)
        self.assertEqual(rc, 1)
        self.assertFalse(self.destino.exists())


class Publicador(unittest.TestCase):
    def test_o_publicador_roda_e_leva_o_arquivo_com_portao(self):
        sh = (Path(__file__).parent / "publicar_tempo_real.sh").read_text(encoding="utf-8")
        self.assertIn("python3 scripts/coleta_maregrafo_itajai.py --publicar", sh)
        self.assertIn("ultimo_maregrafo_itajai.json", sh)


if __name__ == "__main__":
    unittest.main(verbosity=2)
