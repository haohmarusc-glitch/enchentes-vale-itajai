"""Trânsito medido na telemetria: sentinela fora, crista por proeminência, lag recuperado.

O teste-âncora é o `RecuperaOLagConhecido`: séries sintéticas com lag e ganho
que EU escolhi, para o script provar que devolve o que foi plantado. Sem isso,
"o número saiu" e "o número está certo" viram a mesma coisa.
"""

from __future__ import annotations

import csv
import math
import tempfile
import unittest
from datetime import datetime, timedelta
from pathlib import Path

from calibrar_transito_telemetria import (COLUNAS_MINIMAS, MIN_LAG_RESOLVIVEL_H,
                                          MIN_PROEMINENCIA_M, aviso_do_cadastro, classificar,
                                          concentracao, cristas, grade, lag_estavel,
                                          lag_por_correlacao, ler_serie, medir_trecho,
                                          parear_cristas, percentil, recusa_do_cadastro)

INICIO = datetime(2026, 6, 1, 0, 0)


def escrever(pasta: Path, codigo: str, valores: list[float | None], passo_min: int = 60) -> None:
    caminho = pasta / f"{codigo}.csv"
    with caminho.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(COLUNAS_MINIMAS)
        for i, v in enumerate(valores):
            quando = INICIO + timedelta(minutes=passo_min * i)
            w.writerow([quando.isoformat(timespec="seconds"), "" if v is None else v])


def onda(t: float, inicio: float, amp: float, dur: float) -> float:
    """Hidrograma tosco: sobe rápido, desce devagar."""
    if t < inicio or t > inicio + dur:
        return 0.0
    x = (t - inicio) / dur
    return amp * (x ** 0.7) * math.exp(1 - x ** 0.7) * (1 - x) ** 0.3


def serie_sintetica(horas: int, lag: int, ganho: float, base: float,
                    eventos: list[tuple[int, float, int]]) -> list[float]:
    return [
        round(base + sum(ganho * onda(h - lag, i, a, d) for i, a, d in eventos), 3)
        for h in range(horas)
    ]


class LeituraDaSerie(unittest.TestCase):
    def test_sentinela_e_implausivel_saem(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp)
            escrever(p, "DCSC-00001", [2.0, -35.0, 2.1, 99.0, 2.2, None, 2.3])
            serie = ler_serie("DCSC-00001", p)
        self.assertEqual([v for _, v in serie], [2.0, 2.1, 2.2, 2.3])

    def test_estacao_sem_arquivo_devolve_vazio(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(ler_serie("DCSC-99999", Path(tmp)), [])

    def test_carimbo_passa_como_esta(self):
        """medido_em é Brasília (CLAUDE.md) e não pode ser convertido aqui."""
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp)
            escrever(p, "DCSC-00001", [2.0, 2.1])
            serie = ler_serie("DCSC-00001", p)
        self.assertEqual(serie[0][0], INICIO)


class Grade(unittest.TestCase):
    def test_buraco_curto_interpola_e_longo_fica_none(self):
        serie = [(INICIO + timedelta(hours=h), float(h)) for h in (0, 1, 2)]
        serie += [(INICIO + timedelta(hours=h), float(h)) for h in (4, 10, 11)]
        carimbos, valores = grade(serie)
        self.assertEqual(len(carimbos), 12)
        self.assertAlmostEqual(valores[3], 3.0, places=6)   # buraco de 1 h: interpola
        self.assertIsNone(valores[6])                        # buraco de 5 h: fica None


class Cristas(unittest.TestCase):
    def test_ombro_de_rampa_nao_vira_crista(self):
        """Uma cheia lenta sobe 0,3 m a cada 12 h sem ser vários eventos."""
        valores = serie_sintetica(400, 0, 1.0, 2.0, [(100, 2.0, 60)])
        carimbos, vs = grade([(INICIO + timedelta(hours=h), v) for h, v in enumerate(valores)])
        self.assertEqual(len(cristas(carimbos, vs)), 1)

    def test_encontra_todos_os_eventos(self):
        """Com o limiar solto, o detector acha os três — é a mecânica, não a régua."""
        eventos = [(40, 1.5, 30), (150, 2.4, 45), (280, 1.0, 25)]
        valores = serie_sintetica(400, 0, 1.0, 2.0, eventos)
        carimbos, vs = grade([(INICIO + timedelta(hours=h), v) for h, v in enumerate(valores)])
        self.assertEqual(len(cristas(carimbos, vs, min_proeminencia=0.3)), len(eventos))

    def test_limiar_de_producao_descarta_a_subida_pequena(self):
        """Os mesmos três eventos com MIN_PROEMINENCIA_M: o de 0,73 m sai.

        É o conserto de 15/09/2026. A 0,30 m o método achava 41 "cristas" por
        ano em Indaial — ondulação, não cheia —, e parear ondulação com
        ondulação dava lag de 15 a 48 h em um quarto dos pares.
        """
        eventos = [(40, 1.5, 30), (150, 2.4, 45), (280, 1.0, 25)]
        valores = serie_sintetica(400, 0, 1.0, 2.0, eventos)
        carimbos, vs = grade([(INICIO + timedelta(hours=h), v) for h, v in enumerate(valores)])
        achadas = cristas(carimbos, vs)   # usa MIN_PROEMINENCIA_M
        self.assertEqual(len(achadas), 2)
        self.assertTrue(all(prom >= MIN_PROEMINENCIA_M for _, _, prom in achadas))


class Pareamento(unittest.TestCase):
    def test_crista_de_jusante_pequena_demais_nao_pareia(self):
        cm = [(INICIO, 5.0, 2.0)]
        cj = [(INICIO + timedelta(hours=5), 3.0, 0.2)]   # 10 % da proeminência
        self.assertEqual(parear_cristas(cm, cj), [])

    def test_ambiguidade_nao_e_medida(self):
        cm = [(INICIO, 5.0, 2.0)]
        cj = [(INICIO + timedelta(hours=4), 3.0, 1.8),
              (INICIO + timedelta(hours=9), 3.2, 1.9)]
        self.assertEqual(parear_cristas(cm, cj), [])

    def test_agua_nao_sobe_o_rio(self):
        cm = [(INICIO + timedelta(hours=10), 5.0, 2.0)]
        cj = [(INICIO, 3.0, 1.9)]
        self.assertEqual(parear_cristas(cm, cj), [])


class RecuperaOLagConhecido(unittest.TestCase):
    """O teste que vale: lag plantado tem de voltar pelos dois métodos."""

    EVENTOS = [(120, 1.8, 40), (400, 2.6, 55), (700, 1.4, 36), (1000, 2.1, 48),
               (1300, 1.6, 30)]
    HORAS = 1500

    def monta(self, tmp: Path, lag: int, ganho: float) -> None:
        escrever(tmp, "DCSC-MONT",
                 serie_sintetica(self.HORAS, 0, 1.0, 2.0, self.EVENTOS))
        escrever(tmp, "DCSC-JUS",
                 serie_sintetica(self.HORAS, lag, ganho, 1.5, self.EVENTOS))

    def test_lag_de_7h_volta_pelos_dois_metodos(self):
        with tempfile.TemporaryDirectory() as t:
            tmp = Path(t)
            self.monta(tmp, lag=7, ganho=1.3)
            m = medir_trecho("DCSC-MONT", "DCSC-JUS", tmp)
        self.assertIsNotNone(m)
        self.assertEqual(m["lag_correlacao_h"], 7)
        self.assertEqual(len(m["lags_cristas_h"]), len(self.EVENTOS))
        self.assertAlmostEqual(percentil(m["lags_cristas_h"], 0.5), 7.0, delta=1.0)

    def test_faixa_publicada_cobre_o_lag_real(self):
        with tempfile.TemporaryDirectory() as t:
            tmp = Path(t)
            self.monta(tmp, lag=14, ganho=0.9)
            m = medir_trecho("DCSC-MONT", "DCSC-JUS", tmp)
        lags = m["lags_cristas_h"]
        self.assertLessEqual(percentil(lags, 0.25), 14.0)
        self.assertGreaterEqual(percentil(lags, 0.75), 14.0)

    def test_series_sem_nada_em_comum_nao_medem(self):
        with tempfile.TemporaryDirectory() as t:
            tmp = Path(t)
            escrever(tmp, "DCSC-MONT", [2.0] * 200)
            escrever(tmp, "DCSC-JUS", [1.5] * 200)
            m = medir_trecho("DCSC-MONT", "DCSC-JUS", tmp)
        self.assertEqual(m["lags_cristas_h"], [])

    def test_correlacao_ignora_o_zero_da_regua(self):
        """Réguas com zeros diferentes (uma em cota absoluta) dão o mesmo lag."""
        with tempfile.TemporaryDirectory() as t:
            tmp = Path(t)
            escrever(tmp, "DCSC-MONT", serie_sintetica(self.HORAS, 0, 1.0, 2.0, self.EVENTOS))
            escrever(tmp, "DCSC-JUS", serie_sintetica(self.HORAS, 6, 1.1, 24.0, self.EVENTOS))
            m = medir_trecho("DCSC-MONT", "DCSC-JUS", tmp)
        self.assertEqual(m["lag_correlacao_h"], 6)


class Confianca(unittest.TestCase):
    def base(self, n_cristas: int, corr: int, mediana: float) -> dict:
        return {"lag_correlacao_h": corr, "r": 0.9,
                "lags_cristas_h": [mediana] * n_cristas, "horas_comuns": 2000}

    def test_poucos_eventos_nao_publica(self):
        self.assertIsNone(classificar(self.base(1, 6, 6.0), False)[0])

    def test_metodos_discordantes_nao_publicam(self):
        self.assertIsNone(classificar(self.base(5, 6, 20.0), False)[0])

    def test_concordancia_com_eventos_da_alta(self):
        self.assertEqual(classificar(self.base(4, 6, 6.5), False)[0], "alta")

    def test_barragem_segura_no_media(self):
        self.assertEqual(classificar(self.base(4, 6, 6.5), True)[0], "media")

    def test_sem_crista_nenhuma_nao_publica(self):
        self.assertIsNone(classificar(self.base(0, 6, 6.0), False)[0])


class LagEstavel(unittest.TestCase):
    """Partir a série ao meio é o que separa trânsito de artefato da janela."""

    def test_lag_consistente_nas_duas_metades_e_estavel(self):
        eventos = [(120, 1.8, 40), (400, 2.6, 55), (700, 1.4, 36), (1000, 2.1, 48)]
        m = serie_sintetica(1400, 0, 1.0, 2.0, eventos)
        j = serie_sintetica(1400, 6, 1.2, 1.5, eventos)
        estavel, a, b = lag_estavel(m, j)
        self.assertTrue(estavel)
        self.assertEqual((a, b), (6, 6))

    def test_serie_sem_evento_nenhum_nao_e_estavel(self):
        """Ruído puro: cada metade encontra um 'melhor lag' diferente."""
        import random
        random.seed(11)
        m = [2.0 + random.gauss(0, 0.05) for _ in range(1200)]
        j = [1.5 + random.gauss(0, 0.05) for _ in range(1200)]
        estavel, a, b = lag_estavel(m, j)
        self.assertFalse(estavel, f"ruído deu {a} h e {b} h — deveria discordar")


class Concentracao(unittest.TestCase):
    def test_uma_populacao_so_e_concentrada(self):
        self.assertEqual(concentracao([5.0, 6.0, 6.0, 7.0, 7.0, 8.0]), 1.0)

    def test_duas_populacoes_derrubam_a_concentracao(self):
        """O caso real: ascurra -> indaial tinha 23 % dos pares entre 15 e 48 h."""
        lags = [2.0] * 8 + [30.0, 40.0]
        self.assertAlmostEqual(concentracao(lags), 0.8)

    def test_lista_vazia_nao_explode(self):
        self.assertEqual(concentracao([]), 0.0)


class GuardasNaClassificacao(unittest.TestCase):
    def base(self, **extra) -> dict:
        d = {"lag_correlacao_h": 6, "r": 0.9, "lags_cristas_h": [6.0] * 5,
             "concentracao": 1.0, "lag_estavel": True, "lag_metades_h": [6, 6],
             "horas_comuns": 2000}
        d.update(extra)
        return d

    def test_lag_instavel_nao_publica(self):
        conf, porque = classificar(self.base(lag_estavel=False, lag_metades_h=[4, 8]), False)
        self.assertIsNone(conf)
        self.assertIn("instável", porque)

    def test_pares_espalhados_nao_publicam(self):
        conf, porque = classificar(self.base(concentracao=0.5), False)
        self.assertIsNone(conf)
        self.assertIn("população", porque)

    def test_tudo_em_ordem_ainda_publica(self):
        """As guardas novas não podem reprovar o trecho que sempre foi bom."""
        self.assertEqual(classificar(self.base(), False)[0], "alta")


class ToleranciaRelativa(unittest.TestCase):
    """Duas horas de diferença significam coisas diferentes em 20 h e em 3 h."""

    def base(self, lags: list[float], corr: int) -> dict:
        return {"lag_correlacao_h": corr, "r": 0.9, "lags_cristas_h": lags,
                "concentracao": 1.0, "lag_estavel": True, "lag_metades_h": [corr, corr],
                "horas_comuns": 2000}

    def test_duas_horas_de_erro_em_vinte_ainda_e_alta(self):
        self.assertEqual(classificar(self.base([20.0] * 5, 18), False)[0], "alta")

    def test_duas_horas_de_erro_em_quatro_nao_e_mais_alta(self):
        """Antes passava: 2 h fixas em cima de um lag de 4 h é 50 % de erro."""
        conf, _ = classificar(self.base([4.0] * 5, 6), False)
        self.assertNotEqual(conf, "alta")

    def test_o_piso_absoluto_protege_o_lag_pequeno(self):
        """25 % de 4 h é 1 h, mas a tolerância nunca cai abaixo de 1 h."""
        self.assertEqual(classificar(self.base([4.0] * 5, 5), False)[0], "alta")


class LagNaResolucaoDaGrade(unittest.TestCase):
    """O caso ascurra → indaial: cinco pares idênticos em 1,0 h não é precisão."""

    def base(self, lags: list[float], corr: int) -> dict:
        return {"lag_correlacao_h": corr, "r": 0.9, "lags_cristas_h": lags,
                "concentracao": 1.0, "lag_estavel": True, "lag_metades_h": [corr, corr],
                "horas_comuns": 2000}

    def test_lag_no_piso_da_grade_nao_publica(self):
        conf, porque = classificar(self.base([1.0] * 5, 2), False)
        self.assertIsNone(conf)
        self.assertIn("quantização", porque)

    def test_lag_acima_do_piso_publica(self):
        self.assertIsNotNone(classificar(self.base([6.0] * 5, 6), False)[0])

    def test_o_piso_acompanha_o_passo_da_grade(self):
        """Se um dia a grade ficar mais fina, o piso desce junto — não é número solto."""
        from calibrar_transito_telemetria import PASSO_H
        self.assertEqual(MIN_LAG_RESOLVIVEL_H, 2 * PASSO_H)


class Percentil(unittest.TestCase):
    def test_interpola_entre_amostras(self):
        self.assertAlmostEqual(percentil([1.0, 2.0, 3.0, 4.0], 0.25), 1.75)
        self.assertAlmostEqual(percentil([5.0], 0.5), 5.0)


class Correlacao(unittest.TestCase):
    def test_serie_curta_demais_nao_devolve_lag(self):
        self.assertIsNone(lag_por_correlacao([1.0] * 10, [1.0] * 10))


class Cadastro(unittest.TestCase):
    """O que o cadastro da rede recusa aqui — e, tão importante quanto, o que ele NÃO recusa."""

    BLUMENAU, GASPAR = "DCSC-00026", "DCSC-00005"
    GUABIRUBA, BOTUVERA = "DCSC-00029", "DCSC-00018"
    RIO_DO_SUL, INDAIAL = "DCSC-00013", "DCSC-00006"

    def teste_par_normal_passa(self):
        self.assertIsNone(recusa_do_cadastro(self.RIO_DO_SUL, self.INDAIAL))
        self.assertIsNone(aviso_do_cadastro(self.RIO_DO_SUL, self.INDAIAL))

    def teste_estacao_que_nao_mede_rio_recusa_dos_dois_lados(self):
        """`blumenau -> gaspar` tem as duas pontas em `estacoes.json` e nenhum rio medido."""
        self.assertIn("não mede nível de rio", recusa_do_cadastro(self.BLUMENAU, self.GASPAR))
        self.assertIn("montante", recusa_do_cadastro(self.BLUMENAU, self.INDAIAL))
        self.assertIn("jusante", recusa_do_cadastro(self.INDAIAL, self.BLUMENAU))

    def teste_datum_nao_calibrado_NAO_impede_medir_o_lag(self):
        """Trânsito é diferença entre horários, e a correlação é da VARIAÇÃO: o zero da régua não
        entra na conta. Recusar Guabiruba por datum seria recusar por motivo que não se aplica."""
        self.assertIsNone(recusa_do_cadastro(self.BOTUVERA, self.GUABIRUBA))

    def teste_mas_o_datum_e_a_quebra_saem_como_aviso(self):
        aviso = aviso_do_cadastro(self.BOTUVERA, self.GUABIRUBA)
        self.assertIn("SUSPEITAS", aviso)
        self.assertIn("2026-04-01T17:40", aviso)

    def teste_leitura_depois_da_quebra_nao_entra_na_serie(self):
        """Defesa em profundidade: CSV antigo ainda traz altitude misturada na mesma coluna."""
        with tempfile.TemporaryDirectory() as d:
            pasta = Path(d)
            caminho = pasta / f"{self.GUABIRUBA}.csv"
            with caminho.open("w", newline="", encoding="utf-8") as f:
                w = csv.writer(f)
                w.writerow(COLUNAS_MINIMAS)
                w.writerow(["2026-04-01T17:30:00", 0.51])
                w.writerow(["2026-04-01T17:40:00", 16.21])
                w.writerow(["2026-04-01T17:50:00", 24.68])
            serie = ler_serie(self.GUABIRUBA, pasta)
        self.assertEqual([v for _, v in serie], [0.51])

    def teste_a_quebra_so_vale_para_a_estacao_dela(self):
        with tempfile.TemporaryDirectory() as d:
            pasta = Path(d)
            escrever(pasta, self.RIO_DO_SUL, [1.0, 2.0, 3.0])
            self.assertEqual(len(ler_serie(self.RIO_DO_SUL, pasta)), 3)


if __name__ == "__main__":
    unittest.main()
