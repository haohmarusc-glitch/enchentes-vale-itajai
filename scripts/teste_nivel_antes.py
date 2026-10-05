"""Trava a conta "nível das outras réguas N horas antes" (scripts/nivel_antes.py, 05/10/2026)."""
import math
import unittest
from datetime import datetime, timedelta

from nivel_antes import RAIZ, Serie, bloco_rua, cadastro, carregar, cristas, linhas_antes, montante, nivel_em, primeira_passagem, relatorio

T0 = datetime(2026, 9, 10)
RELATORIO = RAIZ / "docs" / "NIVEL-ANTES.md"


def serie(sid, cidade, rio, valores, passo_min=10, familia="brasilia"):
    s = Serie(sid, cidade, rio, "teste", familia)
    s.pontos = [(T0 + timedelta(minutes=passo_min * k), v) for k, v in enumerate(valores)]
    return s


def onda(n, pico_em, altura, base=1.0, largura=60):
    return [round(base + altura * math.exp(-((k - pico_em) / largura) ** 2), 3) for k in range(n)]


class Leitura(unittest.TestCase):
    def test_hora_exata_perto_interpolada_e_vao(self):
        s = serie("X", "blumenau", "itajai-acu", [1.0, 2.0, 3.0])
        self.assertEqual(nivel_em(s, T0 + timedelta(minutes=10)), (2.0, T0 + timedelta(minutes=10)))
        self.assertEqual(nivel_em(s, T0 + timedelta(minutes=14))[1], T0 + timedelta(minutes=10))  # até 10 min: a leitura
        s.pontos = [(T0, 1.0), (T0 + timedelta(minutes=40), 3.0)]
        self.assertEqual(nivel_em(s, T0 + timedelta(minutes=20))[0], 2.0)  # vão de 40 min: interpola
        s.pontos = [(T0, 1.0), (T0 + timedelta(minutes=90), 3.0)]
        self.assertIsNone(nivel_em(s, T0 + timedelta(minutes=45)))  # vão de 90 min: sem leitura, nunca estima
        self.assertIsNone(nivel_em(s, T0 - timedelta(hours=1)))  # fora da série

    def test_primeira_passagem(self):
        s = serie("X", "blumenau", "itajai-acu", [1.0, 1.4, 1.6, 1.2, 1.7])
        self.assertEqual(primeira_passagem(s, 1.5, T0), T0 + timedelta(minutes=20))
        self.assertEqual(primeira_passagem(s, 1.5, T0 + timedelta(minutes=25)), T0 + timedelta(minutes=40))
        self.assertIsNone(primeira_passagem(s, 2.0, T0))


class Cristas(unittest.TestCase):
    def test_uma_onda_uma_crista_e_marola_nao_conta(self):
        s = serie("X", "blumenau", "itajai-acu", onda(1000, 500, 4.0))
        cs = cristas(s)
        self.assertEqual(len(cs), 1)
        self.assertEqual(cs[0].quando, T0 + timedelta(minutes=5000))
        self.assertFalse(cs[0].borda)
        baixa = serie("Y", "blumenau", "itajai-acu", onda(1000, 500, 0.3))
        self.assertEqual(cristas(baixa), [])  # subiu menos de 0,5 m

    def test_regua_com_mare_crista_da_media_nao_da_preamar(self):
        # Onda de cheia + maré de 12,42 h com 0,6 m de amplitude: a crista é a da cheia, não a preamar.
        n, pico = 1200, 600
        vals = [round(v + 0.6 * math.sin(2 * math.pi * k * 10 / (12.42 * 60)), 3) for k, v in enumerate(onda(n, pico, 2.0, largura=150))]
        s = serie("DC-04 teste", "itajai", "itajai-mirim", vals)
        self.assertTrue(s.mare)
        cs = cristas(s)
        self.assertEqual(len(cs), 1)
        self.assertLess(abs((cs[0].quando - (T0 + timedelta(minutes=10 * pico))).total_seconds()), 3 * 3600)


class Topologia(unittest.TestCase):
    def test_montante_no_mesmo_rio_sem_afluente_lateral(self):
        cad = cadastro()
        alvo = serie("A", "blumenau", "itajai-acu", [1])
        self.assertTrue(montante(alvo, serie("B", "indaial", "itajai-acu", [1]), cad))
        self.assertTrue(montante(alvo, serie("C", "taio", "itajai-acu", [1]), cad))  # cabeceira
        self.assertFalse(montante(alvo, serie("D", "timbo", "itajai-acu", [1]), cad))  # afluente lateral
        self.assertFalse(montante(alvo, serie("E", "gaspar", "itajai-acu", [1]), cad))  # a jusante
        self.assertFalse(montante(alvo, serie("F", "brusque", "itajai-mirim", [1]), cad))  # outro rio
        itajai = serie("G", "itajai", "itajai-mirim", [1])
        self.assertTrue(montante(itajai, serie("H", "brusque", "itajai-mirim", [1]), cad))
        self.assertFalse(montante(itajai, serie("I", "itajai", "itajai-mirim", [1]), cad))  # outra régua da mesma cidade

    def test_familias_nao_se_cruzam(self):
        alvo = serie("A", "blumenau", "itajai-acu", onda(600, 300, 3.0), familia="ana")
        outra = serie("B", "indaial", "itajai-acu", onda(600, 250, 3.0))
        linhas = linhas_antes(alvo, T0 + timedelta(hours=50), {"A": alvo, "B": outra}, (3, 6), True)
        self.assertEqual(linhas, [])


class DadosDoRepositorio(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.series = carregar()

    def test_fontes_e_exclusao_da_blumenau_atrasada(self):
        self.assertNotIn("Blumenau", self.series)  # publicação antiga de Itajaí, 3 h atrasada
        for sid in ("Blumenau (AlertaBlu)", "DCSC-00003 SDC-SC Ascurra", "Asthon Vidal Ramos", "ANA 83800002 Blumenau"):
            self.assertIn(sid, self.series)
        self.assertEqual(self.series["ANA 83800002 Blumenau"].familia, "ana")
        self.assertEqual(self.series["DCSC-00003 SDC-SC Ascurra"].rio, "itajai-acu")

    def test_cheia_de_setembro_em_blumenau(self):
        c = [c for c in cristas(self.series["Blumenau (AlertaBlu)"]) if c.quando.date().isoformat() == "2026-09-12"]
        self.assertEqual([(c[0].quando.hour, c[0].nivel)], [(5, 7.86)])
        linhas = "\n".join(linhas_antes(self.series["Blumenau (AlertaBlu)"], c[0].quando, self.series, (3, 6), True))
        self.assertIn("DCSC-00003 SDC-SC Ascurra** (a montante)", linhas)
        self.assertNotIn("Timbó", linhas)  # afluente lateral
        self.assertNotIn("Ilhota", linhas)  # a jusante

    def test_rua_de_blumenau_hora_em_que_a_regua_passou_da_cota(self):
        texto = bloco_rua("Rua São Rafael", self.series, (3,))
        # Final da rua, cota 7,40 m: o AlertaBlu é de hora em hora, então a passagem é um intervalo.
        self.assertIn("cota 7,40 m", texto)
        self.assertIn("passou de 7,40 m entre 12/set 00:00", texto)
        self.assertIn("não é observação na rua", texto)
        self.assertIn("DCSC-00006 SDC-SC Indaial** (a montante): 3 h antes:", texto)

    def test_rua_sem_regua_ligada_nao_inventa_hora(self):
        # Gaspar tem cotas de rua, mas a régua delas ainda não foi ligada a uma série com hora.
        texto = bloco_rua("Rua Lino", self.series, (3,))
        self.assertIn("(gaspar)", texto)
        self.assertIn("ainda não está ligada", texto)
        self.assertNotIn("passou de", texto)

    def test_relatorio_salvo_e_o_recalculado(self):
        # Entrou série nova em data/brutos/? Rodar `python3 scripts/nivel_antes.py --relatorio docs/NIVEL-ANTES.md`.
        self.assertEqual(RELATORIO.read_text(encoding="utf-8"), relatorio(self.series, (3, 6, 12)))


if __name__ == "__main__":
    unittest.main()
