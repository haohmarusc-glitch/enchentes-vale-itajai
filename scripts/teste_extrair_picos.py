#!/usr/bin/env python3
"""Testes da extração de picos.

O que estes casos protegem: o script transforma série bruta em registro de
enchente, e registro de enchente é o que a tela mostra. Um pico no horário
errado vira tempo de descida errado, que vira hora de sair de casa errada.

    python3 scripts/teste_extrair_picos.py
"""

import unittest
from datetime import datetime, timedelta

import json
import tempfile
import unittest.mock
from pathlib import Path

import extrair_picos as ep
from extrair_picos import (
    INTERVALO_ENTRE_EVENTOS_H,
    MIN_LEITURAS,
    Leitura,
    ler_serie,
    limiar_da_estacao,
    separar_eventos,
)

INICIO = datetime(2026, 8, 1, 0, 0)


def serie(*valores, passo_h=1, inicio=INICIO):
    """Leituras espaçadas de `passo_h` horas."""
    return [Leitura(inicio + timedelta(hours=i * passo_h), v, "Blumenau")
            for i, v in enumerate(valores)]


class TesteSepararEventos(unittest.TestCase):
    def test_uma_cheia_vira_um_evento_com_o_maior_valor(self):
        eventos = separar_eventos(serie(3.0, 5.0, 7.2, 9.4, 8.1, 6.0, 4.0), limiar=6.0)
        self.assertEqual(len(eventos), 1)
        self.assertAlmostEqual(eventos[0].pico_m, 9.4)
        self.assertEqual(eventos[0].quando, INICIO + timedelta(hours=3))

    def test_o_horario_do_pico_e_o_da_maior_leitura(self):
        eventos = separar_eventos(serie(7.0, 6.5, 9.9, 7.1), limiar=6.0)
        self.assertEqual(eventos[0].quando, INICIO + timedelta(hours=2))

    def test_duas_cheias_separadas_por_dias_sao_dois_eventos(self):
        cheia1 = serie(7.0, 8.0, 7.0)
        depois = INICIO + timedelta(hours=3 + INTERVALO_ENTRE_EVENTOS_H + 5)
        cheia2 = serie(7.5, 9.0, 7.5, inicio=depois)
        eventos = separar_eventos(cheia1 + cheia2, limiar=6.0)
        self.assertEqual(len(eventos), 2)
        self.assertAlmostEqual(eventos[0].pico_m, 8.0)
        self.assertAlmostEqual(eventos[1].pico_m, 9.0)

    def test_rio_baixando_e_subindo_dentro_da_janela_e_um_evento_so(self):
        """A cheia oscila; enquanto ela não fica 18 h abaixo da cota, é a mesma."""
        eventos = separar_eventos(serie(7.0, 5.0, 5.5, 8.0, 7.0), limiar=6.0)
        self.assertEqual(len(eventos), 1)
        self.assertAlmostEqual(eventos[0].pico_m, 8.0)

    def test_leitura_isolada_acima_da_cota_nao_e_evento(self):
        """Um valor solto é mais provavelmente falha de sensor que cheia."""
        self.assertEqual(separar_eventos(serie(3.0, 9.0, 3.0), limiar=6.0), [])
        self.assertEqual(MIN_LEITURAS, 2)

    def test_serie_toda_abaixo_da_cota_nao_gera_evento(self):
        self.assertEqual(separar_eventos(serie(1.0, 2.0, 3.0), limiar=6.0), [])

    def test_serie_vazia(self):
        self.assertEqual(separar_eventos([], limiar=6.0), [])


class TesteSuspeitos(unittest.TestCase):
    def test_salto_grande_e_marcado_mas_nao_removido(self):
        """Blumenau já subiu mais de 4 m em menos de 24 h: descartar o extremo
        seria jogar fora justamente o que interessa."""
        eventos = separar_eventos(serie(7.0, 7.2, 14.0, 7.5), limiar=6.0)
        self.assertEqual(len(eventos), 1)
        self.assertAlmostEqual(eventos[0].pico_m, 14.0, msg="o extremo continua sendo o pico")
        self.assertTrue(eventos[0].suspeitos, "e vem marcado para conferência")

    def test_subida_normal_nao_e_marcada(self):
        eventos = separar_eventos(serie(7.0, 7.5, 8.0, 8.4), limiar=6.0)
        self.assertEqual(eventos[0].suspeitos, [])


class TesteAgrupamentoPorRegua(unittest.TestCase):
    """
    Leituras reais da Defesa Civil de Itajaí, colhidas em 30/08/2026 às 16h.

    Cinco réguas do Itajaí-Mirim dentro de Itajaí, no MESMO instante, marcando
    de 0,92 m a 4,82 m. Se o agrupamento fosse por cidade, 4,82 m viraria o
    "pico de Itajaí" — comparando réguas com zeros diferentes, que é o erro que
    o projeto avisa em toda tela para não cometer.
    """

    LEITURAS = [
        ("DC-03 Rio Itajaí-Mirim (canal retificado) - Captação SEMASA", 0.92),
        ("DC-04 Rio Itajaí-Mirim (canal retificado e curso antigo) - Vitalmar Pescados", 1.14),
        ("DC-05 Rio Itajaí-Mirim (curso antigo) - Propriedade privada", 1.07),
        ("DC-06 Rio Itajaí-Mirim (curso antigo) - Itamirim Clube de Campo", 0.97),
        ("DC-10 Rio Itajaí-Mirim – Bairro Limoeiro", 4.82),
    ]

    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        caminho = Path(self.dir.name) / "2026-08.ndjson"
        with open(caminho, "w", encoding="utf-8") as f:
            for hora in ("16:00", "16:15"):
                for estacao, nivel in self.LEITURAS:
                    f.write(json.dumps({
                        "estacao": estacao, "rio": "itajai-mirim", "cidade": "itajai",
                        "medido_em": f"2026-08-30T{hora}:00", "nivel_m": nivel,
                    }, ensure_ascii=False) + "\n")
        self.patch = unittest.mock.patch("extrair_picos.SERIE", Path(self.dir.name))
        self.patch.start()

    def tearDown(self):
        self.patch.stop()
        self.dir.cleanup()

    def test_cada_regua_fica_no_seu_grupo(self):
        grupos = ler_serie(None)
        self.assertEqual(len(grupos), 5, "cinco réguas, cinco séries")
        for estacao, nivel in self.LEITURAS:
            self.assertEqual([l.nivel_m for l in grupos[estacao]["leituras"]], [nivel, nivel])

    def test_nenhum_grupo_mistura_reguas(self):
        for estacao, grupo in ler_serie(None).items():
            alturas = {l.nivel_m for l in grupo["leituras"]}
            self.assertEqual(len(alturas), 1, f"{estacao} juntou leituras de réguas diferentes")

    def test_cidade_com_varias_reguas_recusa_a_cota_da_cidade(self):
        """A cota de estacoes.json é por cidade; com cinco réguas não dá para
        saber a qual delas ela se refere. Recusar é melhor que escolher.

        A estação é inventada: as onze DC reais ganharam cota própria do Plano
        de Contingência e não caem mais aqui. A invariante segue valendo para a
        próxima régua que a fonte publicar antes de ser cadastrada.
        """
        limiar, motivo = limiar_da_estacao("DC-99 régua nova", "itajai-mirim", "itajai",
                                           quantas_na_cidade=5)
        self.assertIsNone(limiar)
        self.assertEqual(motivo, "varias-reguas")

    def test_estacao_com_cota_propria_e_analisada_mesmo_com_varias_reguas(self):
        """
        O ganho do Plano de Contingência: a DC-10 tem régua de 8 a 10 m e cota
        própria, então a extração de picos passa a analisá-la — antes ela era
        recusada junto com as outras dez de Itajaí.
        """
        limiar, nome = limiar_da_estacao("DC-10 Rio Itajaí-Mirim – Bairro Limoeiro",
                                         "itajai-mirim", "itajai", quantas_na_cidade=5)
        self.assertAlmostEqual(limiar, 8.0)
        self.assertIn("própria estação", nome)

    def test_cidade_com_uma_regua_usa_a_cota_dela(self):
        limiar, nome = limiar_da_estacao("Blumenau", "itajai-acu", "blumenau", quantas_na_cidade=1)
        # Atenção real de Blumenau em estacoes.json: 4,00 m desde 09/09/2026
        # (escala oficial do AlertaBlu; antes o cadastro trazia 6,00 sem fonte).
        self.assertAlmostEqual(limiar, 4.0)
        self.assertEqual(nome, "atencao")

    def test_cota_propria_da_estacao_destrava_a_analise(self):
        """
        É esta a saída para Itajaí: cota por régua em estacoes.json. Com ela, a
        estação passa a ser analisada mesmo numa cidade com cinco réguas.
        """
        titulo = "DC-10 Rio Itajaí-Mirim – Bairro Limoeiro"
        with unittest.mock.patch(
            "comum.le_json",
            side_effect=lambda nome: {
                "estacoes_tempo_real": [
                    {"codigo": "DC-10", "titulo": titulo, "rio": "itajai-mirim",
                     "cidade": "itajai", "cotas_m": {"atencao": 5.5}, "verificado": True}
                ],
                "rios": {},
            } if nome == "estacoes.json" else {},
        ):
            limiar, nome = limiar_da_estacao(titulo, "itajai-mirim", "itajai", quantas_na_cidade=5)
        self.assertAlmostEqual(limiar, 5.5)
        self.assertIn("própria estação", nome)


class SerieEstadualSoParaHorario(unittest.TestCase):
    """
    A rede estadual destrava os elos de trânsito do Itajaí-Mirim — só o horário.

    Os três elos (`vidal-ramos → botuvera → guabiruba → brusque`) são a lógica
    que a Defesa Civil de Brusque usa de fato, e nenhum podia ser medido:
    Botuverá e Guabiruba não têm régua municipal, então nenhuma cheia futura
    produziria o par de horários. A rede estadual publica Botuverá e Vidal
    Ramos, e a coleta já vinha acumulando esses números sem que nada os lesse.

    O que destrava é simples: **tempo de trânsito se mede entre horários, e
    horário não depende do zero da régua.** O que o zero desconhecido impede é
    dizer quantos METROS o pico teve — e é isso que estes testes travam.
    """

    #: Cheia sintética: Vidal Ramos (montante) pica às 10:00 com 4,80 m e
    #: Botuverá às 12:00 com 4,60 m — 2 h de vão. É exatamente o par de
    #: horários que o elo `vidal-ramos → botuvera` precisa, e note que os
    #: VALORES não são comparáveis entre as duas (zeros diferentes): só o vão é.
    HORAS = ["08:00", "09:00", "10:00", "11:00", "12:00", "13:00", "14:00"]
    VIDAL = [2.0, 3.5, 4.8, 3.9, 2.8, 2.1, 1.9]
    BOTUVERA = [2.1, 2.4, 3.2, 4.0, 4.6, 3.5, 2.4]

    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        caminho = Path(self.dir.name) / "nivel-sc-2026-09.ndjson"
        with open(caminho, "w", encoding="utf-8") as f:
            for hora, vr, bo in zip(self.HORAS, self.VIDAL, self.BOTUVERA):
                for codigo, estacao, nivel in (
                    ("DCSC-00024", "SDC-SC Vidal Ramos", vr),
                    ("DCSC-00018", "SDC-SC Botuverá 1", bo),
                ):
                    f.write(json.dumps({
                        "codigo": codigo, "estacao": estacao, "cidade": None,
                        "datum": "bruto_estadual", "nivel_bruto_m": nivel,
                        "medido_em": f"2026-09-05T{hora}:00",
                    }, ensure_ascii=False) + "\n")
        # Uma linha de reservatório, que NÃO pode entrar: datum próprio.
        with open(caminho, "a", encoding="utf-8") as f:
            f.write(json.dumps({
                "codigo": "DCSC-00024", "estacao": "Barragem Oeste",
                "datum": "reservatorio", "nivel_bruto_m": 350.42,
                "medido_em": "2026-09-05T10:00:00",
            }, ensure_ascii=False) + "\n")
        self.patch = unittest.mock.patch("extrair_picos.SERIE", Path(self.dir.name))
        self.patch.start()

    def tearDown(self):
        self.patch.stop()
        self.dir.cleanup()

    def test_a_cidade_sai_do_codigo_dcsc(self):
        grupos = ep.ler_serie_estadual(None)
        self.assertEqual(grupos["SDC-SC Vidal Ramos"]["cidade"], "vidal-ramos")
        self.assertEqual(grupos["SDC-SC Vidal Ramos"]["rio"], "itajai-mirim")
        self.assertEqual(grupos["SDC-SC Botuverá 1"]["cidade"], "botuvera")

    def test_reservatorio_fica_de_fora(self):
        """Cota absoluta de reservatório não é nível de régua de rio."""
        grupos = ep.ler_serie_estadual(None)
        self.assertNotIn(350.42, [l.nivel_m for l in grupos["Barragem Oeste"]["leituras"]]
                         if "Barragem Oeste" in grupos else [])
        self.assertNotIn("Barragem Oeste", grupos)

    def test_toda_leitura_estadual_nasce_marcada(self):
        for grupo in ep.ler_serie_estadual(None).values():
            for l in grupo["leituras"]:
                self.assertTrue(l.so_horario, "leitura estadual sem a marca de datum")

    def test_o_horario_do_pico_e_o_que_o_transito_precisa(self):
        grupos = ep.ler_serie_estadual(None)
        picos = {}
        for nome, grupo in grupos.items():
            eventos = ep.separar_eventos(grupo["leituras"], 3.0)
            self.assertEqual(len(eventos), 1, f"{nome} deveria ter um evento")
            picos[grupo["cidade"]] = eventos[0].quando
        vao = (picos["botuvera"] - picos["vidal-ramos"]).total_seconds() / 3600
        self.assertEqual(vao, 2.0, "o vão entre os picos é o tempo de trânsito")

    def test_o_evento_inteiro_herda_a_marca(self):
        grupo = ep.ler_serie_estadual(None)["SDC-SC Vidal Ramos"]
        self.assertTrue(ep.separar_eventos(grupo["leituras"], 3.0)[0].so_horario)

    def test_a_serie_estadual_nao_entra_no_glob_municipal(self):
        """
        `*.ndjson` pegava o arquivo estadual e o de chuva. O leitor municipal
        cuspia um aviso por linha — ruído que ensina a ignorar avisos.
        """
        self.assertEqual(ep.arquivos_da_serie(None), [])
        self.assertEqual(ler_serie(None), {})


class SerieEstadualNaoGrava(unittest.TestCase):
    """
    Gravar `pico_m` em datum estadual poria no enchentes.json um número que
    parece régua municipal e não é. As duas travas ficam em código.
    """

    def roda(self, *args) -> tuple[int, str]:
        import io as _io
        import contextlib
        err = _io.StringIO()
        with unittest.mock.patch("sys.argv", ["extrair_picos.py", *args]), \
             contextlib.redirect_stderr(err), contextlib.redirect_stdout(_io.StringIO()):
            codigo = ep.main()
        return codigo, err.getvalue()

    def test_sem_limiar_recusa_e_explica(self):
        codigo, err = self.roda("--serie-estadual")
        self.assertEqual(codigo, 2)
        self.assertIn("exige --limiar", err)
        self.assertIn("5,98", err, "o exemplo de Indaial precisa estar no erro")

    def test_com_escrever_recusa_e_explica(self):
        codigo, err = self.roda("--serie-estadual", "--limiar", "3", "--escrever")
        self.assertEqual(codigo, 2)
        self.assertIn("não grava", err)


if __name__ == "__main__":
    unittest.main(verbosity=2)
