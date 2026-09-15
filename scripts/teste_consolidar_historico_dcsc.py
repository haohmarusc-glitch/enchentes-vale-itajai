"""O histórico da DCSC: fuso passa como está (é Brasília), sentinelas e picos de sensor não viram crista."""

from __future__ import annotations

import csv
import json
import tempfile
import unittest
from datetime import datetime
from pathlib import Path

from consolidar_historico_dcsc import (COLUNAS, cortadas_na_quebra, cristas, gravar_csv, isolada,
                                       ler_pasta, nivel, resumo_da_estacao, serie_de)


def item(ts: str, rio: float | None, codigo: str = "DCSC-00099", **extra) -> dict:
    d = {"ts": ts, "codigo": codigo, "timestamp": ts, "bateria_v": 12.5}
    if rio is not None:
        d["rio_nivel"] = rio
    d.update(extra)
    return d


def janela(inicio_utc: str, fim_utc: str, itens: list[dict], coletado="2026-09-10T02:00:00.000Z") -> dict:
    return {"variables": {"stationCode": "DCSC-00099", "startDate": inicio_utc, "endDate": fim_utc},
            "coletado_em_utc": coletado,
            "resposta": {"data": {"historic": {"items": itens, "totalCount": len(itens)}}}}


class Nivel(unittest.TestCase):
    def test_sentinela_e_implausivel_viram_none(self):
        self.assertIsNone(nivel({"rio_nivel": -35}))
        self.assertIsNone(nivel({"rio_nivel": 21474836.47}))
        self.assertIsNone(nivel({"rio_nivel": 581.0}))
        self.assertEqual(nivel({"rio_nivel": 13.18}), 13.18)
        self.assertEqual(nivel({"rio_nivel": "7.07"}), 7.07)
        self.assertIsNone(nivel({}))
        self.assertIsNone(nivel({"rio_nivel": ""}))


class Fuso(unittest.TestCase):
    def test_ts_passa_sem_conversao_porque_ja_e_brasilia(self):
        # janela pedida em UTC (01/09 00:00Z) devolve o primeiro item às 21:10 de 31/08: o ts É local.
        j = janela("2026-09-01T00:00:00.000Z", "2026-09-10T02:07:00.000Z",
                   [item("2026-08-31T21:10:00.000", 3.0), item("2026-08-31T21:20:00.000", 3.1)])
        with tempfile.TemporaryDirectory() as d:
            Path(d, "x.json").write_text(json.dumps(j), encoding="utf-8")
            por = ler_pasta(Path(d))
        serie = serie_de(por["DCSC-00099"]["itens"])
        self.assertEqual(serie[0][0], datetime(2026, 8, 31, 21, 10))
        with tempfile.TemporaryDirectory() as d:
            destino = Path(d, "s.csv")
            gravar_csv(destino, por["DCSC-00099"]["itens"])
            linhas = list(csv.DictReader(destino.open(encoding="utf-8")))
        self.assertEqual(list(linhas[0].keys()), COLUNAS)
        self.assertEqual(linhas[0]["medido_em"], "2026-08-31T21:10:00")   # sem .000, sem fuso, sem deslocar


class Cristas(unittest.TestCase):
    def _serie(self):
        base = datetime(2023, 11, 17, 0, 0)
        from datetime import timedelta
        s = []
        for i in range(6 * 24 * 6):          # seis dias a 10 min
            t = base + timedelta(minutes=10 * i)
            v = 2.0
            if 100 <= i <= 140:              # cheia de 17/11: sobe até 8,63 e desce
                v = 2.0 + 6.63 * (1 - abs(i - 120) / 20)
            if 650 <= i <= 670:              # segunda cheia menor, > 3 dias depois
                v = 2.0 + 4.0 * (1 - abs(i - 660) / 10)
            s.append((t, round(v, 2)))
        s[300] = (s[300][0], 12.38)          # pico de sensor: 12,38 entre vizinhas de 2,0
        return s

    def test_pico_solto_e_descartado_e_marcado(self):
        s = self._serie()
        self.assertTrue(isolada(s, s[300][0], 12.38))
        self.assertFalse(isolada(s, s[120][0], 8.63))
        c = cristas(s, n=6)
        isoladas = [x for x in c if x["isolada"]]
        validas = [x for x in c if not x["isolada"]]
        self.assertEqual([x["maximo_m"] for x in isoladas], [12.38])
        self.assertEqual(validas[0]["maximo_m"], 8.63)
        self.assertEqual(validas[0]["quando"], "2023-11-17T20:00")
        self.assertEqual(validas[1]["maximo_m"], 6.0)          # a segunda cheia, > 3 dias depois

    def test_mesmo_evento_nao_conta_duas_vezes(self):
        s = self._serie()
        validas = [x for x in cristas(s, n=6) if not x["isolada"]]
        datas = [x["quando"][:10] for x in validas]
        self.assertEqual(len(datas), len(set(datas)))


class Resumo(unittest.TestCase):
    def test_conta_sentinelas_implausiveis_e_buracos(self):
        from datetime import timedelta
        base = datetime(2023, 3, 1, 0, 0)
        itens = {}
        for i in range(200):
            t = base + timedelta(minutes=10 * i)
            if 50 <= i < 100:
                continue                      # buraco de 500 min (> 6 h)
            v = -35 if i % 40 == 0 else (581.0 if i == 7 else 1.0 + i / 100)
            it = item(t.isoformat(timespec="seconds") + ".000", v)
            itens[it["ts"]] = it
        e = {"itens": itens, "janelas": 3, "coletas": ["2026-09-10T01:00:00Z"], "fim_janelas": "2023-03-15T00:00:00.000Z"}
        r = resumo_da_estacao("DCSC-00099", e)
        self.assertEqual(r["sentinelas_rio_nivel"], 4)
        self.assertEqual(r["implausiveis_acima_30m"], 1)
        self.assertEqual(r["buracos_maiores_que_6h"], 1)
        self.assertGreaterEqual(r["maior_buraco_h"], 8)
        self.assertEqual(r["leituras"], 150)
        self.assertEqual(r["leituras_com_nivel"], 145)
        self.assertIsNone(r["cidade"])                       # 00099 não está na CADEIA
        self.assertLess(r["nivel_max_m"], 30)


class Cadastro(unittest.TestCase):
    """As duas coisas que a régua de plausibilidade por valor absoluto NÃO pega.

    Guabiruba passou de régua para cota referenciada ao nível do mar em 01/04/2026 às 17:40 e o
    valor novo (24 m) passa por baixo do limite de 30 m: o resumo commitado listava 28,70 m como
    a maior CRISTA CANDIDATA da estação. Gaspar não mede nível de rio nesta rede e ainda assim o
    endpoint devolve uma coluna `rio_nivel` — cinco "cristas" de 0,84 m e zero.
    """

    GUABIRUBA = "DCSC-00029"
    GASPAR = "DCSC-00005"

    def serie_com_quebra(self) -> dict:
        """Três dias de régua (0,5 m), depois o degrau para altitude (24 m), como na série real."""
        from datetime import timedelta
        base = datetime(2026, 3, 29, 17, 40)
        itens = {}
        for i in range(600):
            t = base + timedelta(minutes=10 * i)
            v = 0.51 if t < datetime(2026, 4, 1, 17, 40) else 24.68
            it = item(t.isoformat(timespec="seconds") + ".000", v, codigo=self.GUABIRUBA)
            itens[it["ts"]] = it
        return itens

    def test_nivel_sem_codigo_nao_corta_nada(self):
        """Quem chama sem estação (teste de unidade da régua) continua vendo o valor cru."""
        it = item("2026-09-01T10:00:00.000", 24.68, codigo=self.GUABIRUBA)
        self.assertEqual(nivel(it), 24.68)

    def test_nivel_com_codigo_corta_depois_da_quebra(self):
        antes = item("2026-04-01T17:30:00.000", 0.51, codigo=self.GUABIRUBA)
        depois = item("2026-04-01T17:40:00.000", 16.21, codigo=self.GUABIRUBA)
        self.assertEqual(nivel(antes, self.GUABIRUBA), 0.51)
        self.assertIsNone(nivel(depois, self.GUABIRUBA))

    def test_a_crista_de_24_m_nao_sobrevive_a_quebra(self):
        itens = self.serie_com_quebra()
        e = {"itens": itens, "janelas": 1, "coletas": [], "fim_janelas": ""}
        r = resumo_da_estacao(self.GUABIRUBA, e)
        for c in r["cristas_candidatas"] + r["descartadas_isoladas"]:
            self.assertLess(c["maximo_m"], 10, "altitude virou crista candidata de novo")
        self.assertLess(r["nivel_max_m"], 10)

    def test_o_resumo_DIZ_o_que_cortou(self):
        """Corte silencioso é como uma série some sem ninguém ver."""
        itens = self.serie_com_quebra()
        e = {"itens": itens, "janelas": 1, "coletas": [], "fim_janelas": ""}
        r = resumo_da_estacao(self.GUABIRUBA, e)
        q = r["quebra_de_serie"]
        self.assertEqual(q["desde"], "2026-04-01T17:40")
        self.assertEqual(q["leituras_de_nivel_cortadas"], cortadas_na_quebra(self.GUABIRUBA, itens))
        self.assertGreater(q["leituras_de_nivel_cortadas"], 0)
        self.assertIn("NÍVEL DO MAR", q["grandeza_depois"])

    def test_a_linha_continua_no_csv_sem_o_nivel(self):
        """O pluviômetro não mudou de datum: só a coluna de nível é cortada."""
        itens = self.serie_com_quebra()
        with tempfile.TemporaryDirectory() as d:
            destino = Path(d) / "x.csv"
            n = gravar_csv(destino, itens, self.GUABIRUBA)
            linhas = list(csv.DictReader(destino.open(encoding="utf-8")))
        self.assertEqual(n, len(itens))                      # nenhuma LINHA sumiu
        depois = [l for l in linhas if l["medido_em"] >= "2026-04-01T17:40"]
        self.assertTrue(depois)
        self.assertTrue(all(l["rio_nivel"] == "" for l in depois))
        self.assertTrue(all(l["bateria_v"] == "12.5" for l in depois))

    def test_estacao_que_nao_mede_nivel_nao_publica_crista(self):
        from datetime import timedelta
        base = datetime(2023, 3, 16, 0, 0)
        itens = {}
        for i in range(300):
            t = base + timedelta(minutes=10 * i)
            v = 0.84 if i == 99 else 0.0
            it = item(t.isoformat(timespec="seconds") + ".000", v, codigo=self.GASPAR)
            itens[it["ts"]] = it
        e = {"itens": itens, "janelas": 1, "coletas": [], "fim_janelas": ""}
        r = resumo_da_estacao(self.GASPAR, e)
        self.assertEqual(r["cristas_candidatas"], [])
        self.assertEqual(r["descartadas_isoladas"], [])
        self.assertIn("tem_nivel_do_rio=false", r["nao_mede_nivel"])
        # as contagens ficam: descrevem o que a fonte devolveu, e sumir com elas seria outra mentira
        self.assertEqual(r["leituras_com_nivel"], 300)
        self.assertEqual(r["nivel_max_m"], 0.84)

    def test_estacao_comum_nao_ganha_campo_nenhum(self):
        """Campo novo tem que ser None nas outras 10 estações, senão o conferir_resumo_dcsc.py
        acusa divergência em todas elas e vira alarme que ninguém lê."""
        itens = {i["ts"]: i for i in [item("2023-03-16T00:00:00.000", 1.0)]}
        r = resumo_da_estacao("DCSC-00013", {"itens": itens, "janelas": 1, "coletas": [], "fim_janelas": ""})
        self.assertIsNone(r["nao_mede_nivel"])
        self.assertIsNone(r["quebra_de_serie"])


if __name__ == "__main__":
    unittest.main()
