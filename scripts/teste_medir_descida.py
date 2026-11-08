#!/usr/bin/env python3
"""Testes do medidor de descida (`medir_descida.py`).

Cheias SINTÉTICAS com atraso conhecido: cada método tem de devolver o atraso que foi posto, com maré por
cima, com zeros diferentes, com buraco na série. E as travas do contrato: o script nunca escreve em
transito.json, cheia que ainda não passou não vira medida, e a confiança só sobe com eventos e métodos
concordando.

    python3 scripts/teste_medir_descida.py
"""
from __future__ import annotations

import json
import math
import sys
import tempfile
import unittest
from datetime import datetime, timedelta
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))

import medir_descida as md  # noqa: E402

T0 = datetime(2026, 9, 1, 0, 0)
DEZ = timedelta(minutes=10)


def hidrograma(crista: datetime, pico: float, base: float, subida_h: float = 14, descida_h: float = 30,
               dias: int = 8, inicio: datetime = T0) -> list[tuple[datetime, float]]:
    """Onda assimétrica (sobe mais rápido do que desce), como as do Itajaí."""
    out = []
    for k in range(int(dias * 24 * 6)):
        t = inicio + k * DEZ
        h = (t - crista).total_seconds() / 3600
        largura = subida_h if h < 0 else descida_h
        out.append((t, base + (pico - base) * math.exp(-(h / largura) ** 2)))
    return out


def varias_cheias(atraso_h: float, n: int = 6, mare: bool = False, ruido_h: float = 0.0):
    """n cheias espaçadas de 5 dias; embaixo, a mesma forma `atraso_h` depois, outro zero, outra amplitude."""
    cima, baixo = {}, {}
    for e in range(n):
        crista = T0 + timedelta(days=3 + 5 * e, hours=5)
        pico = 6 + e * 0.6
        desvio = timedelta(hours=ruido_h * ((-1) ** e))
        for t, v in hidrograma(crista, pico, 1.0, inicio=T0 + timedelta(days=5 * e), dias=5):
            cima[t] = max(cima.get(t, 0), v)
        for t, v in hidrograma(crista + timedelta(hours=atraso_h) + desvio, 0.4 * pico + 2, 2.5,
                               inicio=T0 + timedelta(days=5 * e), dias=5):
            if mare:
                hh = (t - T0).total_seconds() / 3600
                v += 0.45 * math.sin(2 * math.pi * hh / 12.42) + 0.15 * math.sin(2 * math.pi * hh / 23.93)
            baixo[t] = max(baixo.get(t, -9), v)
    return sorted(cima.items()), sorted(baixo.items())


class TestMetodosRecuperamOAtraso(unittest.TestCase):
    def medir(self, atraso, mare=False, ruido=0.0):
        cima, baixo = varias_cheias(atraso, mare=mare, ruido_h=ruido)
        gu = md.regularizar(cima)
        gd = md.regularizar(baixo)
        if mare:
            gd = md.tirar_mare(gd)
        ev_up = [e for e in md.achar_eventos(gu, 0.5) if not e.aberto]
        ev_dn = md.achar_eventos(gd, 0.2)
        pares = [md.medir_par(gu, gd, e, ev_dn) for e in ev_up]
        return pares, md.resumir(pares)

    def test_cinco_metodos_acham_6_horas(self):
        pares, r = self.medir(6.0)
        self.assertGreaterEqual(r["eventos_pareados"], 5)
        for m in md.METODOS:
            self.assertAlmostEqual(r["metodos"][m]["mediana_h"], 6.0, delta=0.6, msg=m)
        self.assertEqual(r["confianca"], "alta")

    def test_atraso_negativo_tambem_aparece(self):
        """Embaixo cresta ANTES (chuva local): o medidor não pode esconder isso."""
        _, r = self.medir(-3.0)
        self.assertAlmostEqual(r["metodos"]["crista"]["mediana_h"], -3.0, delta=0.4)

    def test_mare_sai_pela_analise_harmonica_sem_deslocar_o_horario(self):
        _, r = self.medir(10.0, mare=True)
        self.assertGreaterEqual(r["eventos_pareados"], 4)
        self.assertAlmostEqual(r["metodos"]["crista"]["mediana_h"], 10.0, delta=1.0)
        self.assertAlmostEqual(r["metodos"]["xcorr"]["mediana_h"], 10.0, delta=1.0)

    def test_eventos_que_discordam_nao_viram_faixa(self):
        _, r = self.medir(6.0, ruido=5.0)  # ±5 h de um evento para o outro
        self.assertEqual(r["confianca"], "insuficiente")
        self.assertIn("eventos discordam", r["por_que_nao"])

    def test_godin_tira_a_mare_pura(self):
        serie = [(T0 + k * DEZ, 3 + 0.5 * math.sin(2 * math.pi * (k / 6) / 12.42)) for k in range(6 * 24 * 6)]
        g = md.godin(md.regularizar(serie))
        meio = [x for x in g.v if x is not None]
        self.assertTrue(meio)
        self.assertLess(max(meio) - min(meio), 0.02)

    def test_rayleigh_escolhe_so_o_que_a_duracao_separa(self):
        curta = md.constituintes_por_rayleigh(16 * 24)
        self.assertIn(12.4206012, curta)               # M2
        self.assertNotIn(24.06589016, curta)           # P1 não se separa de K1 em 16 dias
        longa = md.constituintes_por_rayleigh(400 * 24)
        self.assertEqual(len(longa), len(md.CONSTITUINTES_H))

    def test_analise_harmonica_tira_a_mare_e_deixa_a_cheia(self):
        # 40 dias, como as réguas de Itajaí (meses de série, a cheia no meio): a calmaria separa as constituintes.
        crista = T0 + timedelta(days=20)
        serie = []
        for t, v in hidrograma(crista, 4.0, 1.0, dias=40):
            hh = (t - T0).total_seconds() / 3600
            serie.append((t, v + 0.5 * math.sin(2 * math.pi * hh / 12.4206012) + 0.2 * math.cos(2 * math.pi * hh / 23.93446966)))
        g = md.tirar_mare(md.regularizar(serie))
        limpo = dict(hidrograma(crista, 4.0, 1.0, dias=40))
        erro = max(abs(g.v[i] - limpo[g.t(i)]) for i in range(len(g.v)) if g.v[i] is not None)
        self.assertLess(erro, 0.08)
        ev = md.achar_eventos(g, 0.5)
        self.assertEqual(len(ev), 1)
        self.assertLess(abs((ev[0].crista - crista).total_seconds()), 1800)


class TestEventos(unittest.TestCase):
    def test_cheia_na_ponta_da_serie_fica_aberta(self):
        """A série acaba no topo: não é crista — é a cheia em curso."""
        crista = T0 + timedelta(days=3)
        serie = [p for p in hidrograma(crista, 8, 2, dias=5) if p[0] <= crista + timedelta(minutes=30)]
        ev = md.achar_eventos(md.regularizar(serie), 0.5)
        self.assertTrue(ev)
        self.assertTrue(ev[-1].aberto)
        self.assertAlmostEqual(ev[-1].pico, 8, delta=0.01)

    def test_cheia_que_desceu_fecha(self):
        crista = T0 + timedelta(days=3)
        ev = md.achar_eventos(md.regularizar(hidrograma(crista, 8, 2, dias=5)), 0.5)
        self.assertEqual(len(ev), 1)
        self.assertFalse(ev[0].aberto)
        self.assertLess(abs((ev[0].crista - crista).total_seconds()), 3600)

    def test_ondulacao_pequena_nao_e_cheia(self):
        serie = [(T0 + k * DEZ, 2 + 0.1 * math.sin(k / 30)) for k in range(3000)]
        self.assertEqual(md.achar_eventos(md.regularizar(serie), 0.5), [])

    def test_pico_de_sensor_sai(self):
        serie = [(T0 + k * DEZ, 2.0) for k in range(20)]
        serie[10] = (serie[10][0], 9.0)
        self.assertNotIn(9.0, [v for _, v in md.tirar_picos_isolados(serie)])

    def test_lacuna_grande_vira_buraco(self):
        serie = [(T0, 1.0), (T0 + timedelta(hours=2), 2.0)]  # 2 h: buraco; 1 h (AlertaBlu) interpola
        g = md.regularizar(serie)
        self.assertIsNone(g.v[3])
        g2 = md.regularizar([(T0, 1.0), (T0 + timedelta(hours=1), 2.0)])
        self.assertAlmostEqual(g2.v[2], 1 + 2 / 6, places=6)

    def test_metodo_com_um_evento_nao_conta_como_concordancia(self):
        par = lambda c, outros: md.Par(T0, 5, 3, T0 + timedelta(hours=c),  # noqa: E731
                                        {"crista": c, "meia_subida": outros, "centroide": None, "xcorr": None, "dtw": None})
        pares = [par(2.0, None) for _ in range(5)] + [par(2.0, 2.1)]
        r = md.resumir(pares)
        self.assertEqual(r["confianca"], "insuficiente")
        self.assertIn("só um método", r["por_que_nao"])

    def test_sem_correspondente_embaixo_nao_inventa(self):
        cima = hidrograma(T0 + timedelta(days=3), 8, 2, dias=6)
        baixo = [(t, 3.0) for t, _ in cima]
        gu, gd = md.regularizar(cima), md.regularizar(baixo)
        par = md.medir_par(gu, gd, md.achar_eventos(gu, 0.5)[0], md.achar_eventos(gd, 0.2))
        self.assertIsNone(par.crista_jusante)
        self.assertTrue(all(v is None for v in par.lags.values()))


class TestFontes(unittest.TestCase):
    def test_juntar_fontes_preenche_buraco_com_deslocamento(self):
        a = [(T0 + timedelta(hours=h), 5.0 + h * 0.01) for h in range(0, 24) if not 10 <= h <= 14]
        b = [(T0 + timedelta(hours=h), 5.0 + h * 0.01 - 0.06) for h in range(0, 24)]
        junto = dict(md.juntar_fontes([a, b]))
        self.assertAlmostEqual(junto[T0 + timedelta(hours=12)], 5.12, places=6)  # 6 cm devolvidos
        self.assertEqual(len(junto), 24)

    def test_serie_recente_usa_o_indice_da_regua(self):
        corpo = {"reguas": {"itajai-acu": {"blumenau": ["Blumenau (AlertaBlu)", "Blumenau (PADKND)"]}},
                 "series": {"itajai-acu": {"blumenau": [
                     {"medido_em": "2026-11-07T20:50:00", "nivel_m": 8.05, "r": 1},
                     {"medido_em": "2026-11-07T20:00:00", "nivel_m": 7.97, "r": 0},
                     {"medido_em": "2026-11-07T20:10:00", "nivel_m": 99.0},  # sem r: régua desconhecida
                 ]}}}
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "serie-recente.json"
            p.write_text(json.dumps(corpo), encoding="utf-8")
            s = md.ler_recente(p)
        self.assertEqual(s["Blumenau (PADKND)"], [(datetime(2026, 11, 7, 20, 50), 8.05)])
        self.assertEqual(s["Blumenau (AlertaBlu)"], [(datetime(2026, 11, 7, 20, 0), 7.97)])

    def test_carimbo_com_fuso_fica_de_fora(self):
        self.assertIsNone(md._quando("2026-11-07T20:50:00+00:00"))
        self.assertEqual(md._quando("2026-11-07T20:50:00"), datetime(2026, 11, 7, 20, 50))

    def test_repasse_atrasado_de_blumenau_nao_e_fonte(self):
        """O título 'Blumenau' (repasse antigo, 3 h atrasado) não entra no ponto de Blumenau."""
        self.assertNotIn("Blumenau", md.PONTOS["blumenau"].fonte[1])


class TestEstatistica(unittest.TestCase):
    def test_bootstrap_reprodutivel(self):
        xs = [5.0, 6.0, 6.5, 7.0, 9.0]
        self.assertEqual(md.bootstrap_mediana(xs), md.bootstrap_mediana(xs))
        a, b = md.bootstrap_mediana(xs)
        self.assertLessEqual(a, 6.5)
        self.assertGreaterEqual(b, 6.5)

    def test_theil_sen_resiste_a_um_ponto_fora(self):
        xs = [1, 2, 3, 4, 5, 6]
        ys = [17, 16, 15, 14, 13, 40]
        self.assertAlmostEqual(md.theil_sen(xs, ys), -1.0)

    def test_referencia_jica_por_coluna(self):
        self.assertEqual(md.referencia_jica("blumenau", "itajai-dc11"), (12, 17))
        self.assertEqual(md.referencia_jica("blumenau", "ilhota"), (5, 7))
        self.assertIsNone(md.referencia_jica("vidal-ramos", "botuvera"))


class TestContrato(unittest.TestCase):
    def test_gravar_nunca_toca_o_transito(self):
        cima, baixo = varias_cheias(6.0)
        with tempfile.TemporaryDirectory() as d:
            raiz = Path(d)
            (raiz / "data").mkdir()
            (raiz / "docs").mkdir()
            transito = raiz / "data" / "transito.json"
            transito.write_text("{}", encoding="utf-8")
            serie = raiz / "serie"
            serie.mkdir()
            with (serie / "2026-09.ndjson").open("w", encoding="utf-8") as f:
                for titulo, s in (("Blumenau (PADKND)", cima),
                                  ("DC-11 Rio Itajaí-Açú – Santa Regina (Volta de Cima)", baixo)):
                    for t, v in s:
                        f.write(json.dumps({"estacao": titulo, "medido_em": t.isoformat(), "nivel_m": v}) + "\n")
            with mock.patch.object(md, "DADOS", raiz / "data"), mock.patch.object(md, "RAIZ", raiz), \
                    mock.patch("sys.stdout"):
                self.assertEqual(md.main(["--serie", str(serie), "--gravar"]), 0)
            self.assertEqual(transito.read_text(encoding="utf-8"), "{}")
            saida = json.loads((raiz / "data" / "descida-medida.json").read_text(encoding="utf-8"))
            self.assertIn("Nunca entra em transito.json", saida["_meta"]["o_que_e"])
            trecho = next(t for t in saida["trechos"] if t["de"] == "blumenau" and t["para"] == "itajai-dc11")
            self.assertGreaterEqual(trecho["resumo"]["eventos_pareados"], 4)
            self.assertTrue((raiz / "docs" / "DESCIDA-MEDIDA.md").read_text(encoding="utf-8").startswith("# Descida"))

    def test_todo_trecho_usa_pontos_cadastrados(self):
        for t in md.TRECHOS:
            self.assertIn(t.de, md.PONTOS)
            self.assertIn(t.para, md.PONTOS)


if __name__ == "__main__":
    unittest.main()
