#!/usr/bin/env python3
"""
Testes do leitor da tabela da Defesa Civil de Gaspar.

Gaspar é a cidade com mais cotas de rua, e agora tem cota de régua — 5,00 / 6,00
/ 7,00 m, do Plano de Contingência. Ou seja: o aviso de Gaspar já está armado e
espera só um número. O que este script propuser como cota entraria em cima de uma
faixa oficial, e um limiar errado não aparece na tela: o site continua bonito, o
bot continua respondendo, e o telefone toca na hora errada, ou não toca.

Por isso quase todos os testes aqui são sobre o que ele **recusa** a chamar de
nível e de cota.
"""

import sys
from datetime import datetime
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from coleta_gaspar import (MARGEM_DO_NIVEL_M, analisar, e_barragem,
                           faixas_da_linha, indices_do_cabecalho, ler_linha,
                           numero, permitido, quando_de)

RAIZ = Path(__file__).resolve().parent.parent
PAGINA_REAL = RAIZ / "data" / "brutos" / "gaspar-monitoramento-2026-08-31.html"

TABELA = """
<table>
  <tr><td>Estação</td><td>Fonte</td><td>Coleta</td><td>Nível</td><td>24 horas</td></tr>
  <tr><td>Rio Itajaí Açu Gaspar</td><td>DC. Gaspar</td><td>31/08 22:59</td>
      <td>3,85</td><td>70,00</td></tr>
  <tr><td>Barragem Oeste Taió</td><td>DCSC</td><td>31/08 23:29</td>
      <td>351,81</td><td>0,00</td></tr>
</table>
"""

CABECALHO = ["Estação", "Fonte", "Coleta", "Nível", "24 horas"]
INDICES = {"estacao": 0, "fonte": 1, "coleta": 2, "nivel": 3, "chuva_24h": 4}


class TestNumero(unittest.TestCase):
    """
    A tabela real escreve `<td>3,85</td>` — sem unidade. A primeira versão
    exigia o "m" para um número virar nível, e por isso leu ZERO estações na
    página de verdade. A unidade não é o que separa nível de chuva: a coluna é.
    """

    def test_le_numero_sem_unidade(self):
        self.assertEqual(numero("3,85"), 3.85)
        self.assertEqual(numero("265,90"), 265.9)
        self.assertEqual(numero("0,00"), 0.0)

    def test_traco_e_vazio_viram_none(self):
        for texto in ("-", "", "   ", None):
            with self.subTest(texto=texto):
                self.assertIsNone(numero(texto))

    def test_texto_com_numero_dentro_nao_vira_numero(self):
        self.assertIsNone(numero("Coleta 31/08 22:59"))
        self.assertIsNone(numero("Rio Itajaí Açu Gaspar"))


class TestCabecalho(unittest.TestCase):
    def test_acha_as_colunas_pelo_nome(self):
        self.assertEqual(indices_do_cabecalho(CABECALHO), INDICES)

    def test_cota_e_nivel_sao_a_mesma_coluna(self):
        """O rodapé desta tabela diz "Cota" onde o topo diz "Nível"."""
        self.assertEqual(indices_do_cabecalho(["Estação", "Cota"])["nivel"], 1)

    def test_linha_de_dados_nao_e_confundida_com_cabecalho(self):
        self.assertNotIn("nivel", indices_do_cabecalho(
            ["Rio Itajaí Açu Gaspar", "DC. Gaspar", "31/08 22:59", "3,85"]))


class TestQuando(unittest.TestCase):
    def test_le_a_data_sem_ano_da_pagina(self):
        agora = datetime(2026, 9, 1, 2, 0)
        texto, iso = quando_de("31/08 22:59", agora)
        self.assertEqual(texto, "31/08 22:59")
        self.assertEqual(iso, "2026-08-31T22:59:00")

    def test_data_que_cairia_no_futuro_usa_o_ano_anterior(self):
        """Em 1º de janeiro, "31/12 23:00" é do ano passado, não do que vem."""
        _, iso = quando_de("31/12 23:00", datetime(2026, 1, 1, 3, 0))
        self.assertEqual(iso, "2025-12-31T23:00:00")

    def test_ano_explicito_e_respeitado(self):
        _, iso = quando_de("09/09/2011 14:00", datetime(2026, 9, 1))
        self.assertEqual(iso, "2011-09-09T14:00:00")

    def test_texto_sem_data_nao_inventa_nada(self):
        self.assertEqual(quando_de("sem data"), (None, None))


class TestLerLinha(unittest.TestCase):
    def test_le_o_nivel_pela_coluna(self):
        item = ler_linha(["Rio Itajaí Açu Gaspar", "DC. Gaspar", "31/08 22:59", "3,85",
                          "70,00"], INDICES, datetime(2026, 9, 1, 2, 0))
        self.assertEqual(item["nivel_m"], 3.85)
        self.assertTrue(item["nivel_plausivel"])
        self.assertEqual(item["chuva_mm"]["chuva_24h"], 70.0)
        self.assertEqual(item["fonte_da_leitura"], "DC. Gaspar")

    def test_chuva_nao_vira_nivel(self):
        """
        A coluna de 24 h desta linha traz 70,00 — um número perfeitamente
        plausível como nível. Quem impede a confusão é a coluna.
        """
        item = ler_linha(["PLUVIÔMETRO", "Cemaden", "31/08 23:29", "-", "82,29"],
                         INDICES)
        self.assertIsNone(item["nivel_m"])
        self.assertEqual(item["chuva_mm"]["chuva_24h"], 82.29)

    def test_barragem_em_centenas_de_metros_e_marcada(self):
        """265 a 392 m é cota de reservatório acima do mar, não nível de rio."""
        item = ler_linha(["Barragem Sul Ituporanga", "DCSC", "31/08 23:29", "392,62",
                          "0,00"], INDICES)
        self.assertEqual(item["nivel_m"], 392.62)
        self.assertFalse(item["nivel_plausivel"])

    def test_sem_coluna_de_nivel_nao_le_a_linha(self):
        """Melhor não ler do que ler pela posição chutada."""
        self.assertIsNone(ler_linha(["X", "Y"], {"estacao": 0}))

    def test_linha_sem_rotulo_nao_vira_leitura(self):
        self.assertIsNone(ler_linha(["", "", "", "3,85"], INDICES))

    def test_a_linha_bruta_fica_para_o_ajuste_do_parser(self):
        item = ler_linha(["Gaspar", "DC", "31/08 22:59", "3,85", "0,00"], INDICES)
        self.assertIn("3,85", item["linha_bruta"])


class TestFaixas(unittest.TestCase):
    def test_faixa_rotulada_em_celula_propria_entra(self):
        self.assertEqual(faixas_da_linha(["Gaspar", "Atenção", "6,00 m"], None),
                         {"atencao": 6.0})

    def test_texto_corrido_nao_vira_faixa(self):
        """
        "ATENÇÃO — nível 3,25 m" numa página de monitoramento quer dizer que o
        rio ESTÁ em 3,25 m. A versão anterior capturava isso como a cota de
        atenção e o mandava para estacoes.json.
        """
        self.assertEqual(faixas_da_linha(["ATENÇÃO — nível 3,25 m", "01/09/2026"], None), {})

    def test_candidata_igual_ao_nivel_atual_e_recusada(self):
        """O rótulo ecoando o nível é a armadilha; a margem existe só para ela."""
        self.assertEqual(faixas_da_linha(["Situação", "Atenção", "3,25 m"], 3.25), {})
        self.assertEqual(faixas_da_linha(["Situação", "Atenção", "6,00 m"], 3.25),
                         {"atencao": 6.0})

    def test_a_margem_e_estreita_o_bastante_para_nao_comer_faixa_de_verdade(self):
        self.assertLessEqual(MARGEM_DO_NIVEL_M, 0.05)
        self.assertEqual(faixas_da_linha(["x", "Alerta", "3,30 m"], 3.25), {"alerta": 3.3})

    def test_faixa_fora_da_faixa_de_rio_nao_entra(self):
        self.assertEqual(faixas_da_linha(["x", "Emergência", "349,00 m"], None), {})

    def test_rotulo_sem_numero_ao_lado_nao_inventa_faixa(self):
        self.assertEqual(faixas_da_linha(["x", "Atenção", "sem dado"], None), {})


class TestBarragem(unittest.TestCase):
    def test_reconhece_barragem_com_e_sem_acento(self):
        for rotulo in ("Barragem Oeste", "BARRAGEM SUL", "Represa do Norte"):
            with self.subTest(rotulo=rotulo):
                self.assertTrue(e_barragem(rotulo))

    def test_estacao_de_rio_nao_e_barragem(self):
        self.assertFalse(e_barragem("Rio Itajaí Açu Gaspar"))


class TestAnalisar(unittest.TestCase):
    def test_separa_estacao_de_barragem(self):
        lido = analisar(TABELA)
        self.assertEqual([e["rotulo"] for e in lido["estacoes"]], ["Rio Itajaí Açu Gaspar"])
        self.assertEqual([b["rotulo"] for b in lido["barragens"]], ["Barragem Oeste Taió"])

    def test_a_tabela_de_exemplo_nao_produz_faixa_nenhuma(self):
        """
        Ela só publica o nível atual — que é o cenário mais provável. Nesse caso
        a resposta certa é "não há faixa aqui", e não uma faixa deduzida.
        """
        self.assertEqual(analisar(TABELA)["faixas_propostas"], {})

    def test_html_sem_tabela_nao_quebra(self):
        lido = analisar("<html><body><p>fora do ar</p></body></html>")
        self.assertEqual((lido["estacoes"], lido["barragens"]), ([], []))


class TestArquivoSalvo(unittest.TestCase):
    """
    O host de Gaspar dá timeout de conexão de fora da região — três tentativas,
    duas datas, com DNS resolvendo. O navegador de quem mora lá alcança, então
    o caminho é salvar o HTML e passar o arquivo. Ler arquivo que alguém salvou
    não é rastejar site: não há requisição, e por isso não há robots a consultar.
    """

    def test_le_a_mesma_tabela_de_um_arquivo(self):
        import tempfile
        with tempfile.NamedTemporaryFile("w", suffix=".html", encoding="utf-8",
                                         delete=False) as arquivo:
            arquivo.write(TABELA)
            caminho = arquivo.name
        lido = analisar(Path(caminho).read_text(encoding="utf-8"))
        self.assertEqual([e["rotulo"] for e in lido["estacoes"]], ["Rio Itajaí Açu Gaspar"])
        self.assertEqual(lido["estacoes"][0]["nivel_m"], 3.85)
        Path(caminho).unlink()

    def test_html_com_byte_estranho_nao_quebra_a_leitura(self):
        """Página salva do navegador pode vir em outra codificação."""
        lido = analisar(TABELA.replace("Açu", "A\ufffdu"))
        self.assertEqual(len(lido["estacoes"]), 1)


class TestPaginaReal(unittest.TestCase):
    """
    Contra a página que a Defesa Civil de Gaspar publicou em 31/08/2026, salva
    do navegador. Exemplo inventado passa enquanto a fonte muda embaixo dele —
    e foi exatamente o que aconteceu: a primeira versão passava nos testes e
    lia zero estações da página de verdade.
    """

    @classmethod
    def setUpClass(cls):
        cls.lido = analisar(PAGINA_REAL.read_text(encoding="utf-8"))

    def test_le_o_nivel_do_itajai_acu_em_gaspar(self):
        gaspar = next(e for e in self.lido["estacoes"]
                      if "Rio Itajaí Açu Gaspar" in e["rotulo"])
        self.assertEqual(gaspar["nivel_m"], 3.85)
        self.assertTrue(gaspar["nivel_plausivel"])
        self.assertEqual(gaspar["medido_em"], "31/08 22:59")

    def test_le_o_ribeirao_belchior(self):
        belchior = next(e for e in self.lido["estacoes"] if "BELCHIOR" in e["rotulo"])
        self.assertEqual(belchior["nivel_m"], 1.68)

    def test_as_tres_barragens_ficam_fora_da_faixa_de_rio(self):
        self.assertEqual(len(self.lido["barragens"]), 3)
        for b in self.lido["barragens"]:
            with self.subTest(rotulo=b["rotulo"]):
                self.assertFalse(b["nivel_plausivel"])
                self.assertGreater(b["nivel_m"], 200)

    def test_os_pluviometros_nao_ganham_nivel(self):
        pluvio = [e for e in self.lido["estacoes"] if "PLU" in e["rotulo"].upper()]
        self.assertEqual(len(pluvio), 6)
        for p in pluvio:
            with self.subTest(rotulo=p["rotulo"]):
                self.assertIsNone(p["nivel_m"])
                self.assertIsNotNone(p["chuva_mm"]["chuva_24h"])

    def test_a_pagina_nao_publica_faixa_de_cota(self):
        """
        A resposta que o levantamento buscava: a tabela traz leitura, não
        limiar. As cotas de régua de Gaspar têm de vir por outro caminho.
        """
        self.assertEqual(self.lido["faixas_propostas"], {})


class TestRobots(unittest.TestCase):
    def test_disallow_da_pagina_barra(self):
        self.assertFalse(permitido(buscar=lambda u: "User-agent: *\nDisallow: /monitoramento"))

    def test_disallow_vazio_libera(self):
        self.assertTrue(permitido(buscar=lambda u: "User-agent: *\nDisallow:"))

    def test_sem_robots_txt_e_permissao_por_omissao(self):
        def falha(url):
            raise RuntimeError("404 Client Error: Not Found for url: " + url)
        self.assertTrue(permitido(buscar=falha))

    def test_erro_de_rede_nao_vira_permissao(self):
        def falha(url):
            raise RuntimeError("Connection reset by peer")
        self.assertFalse(permitido(buscar=falha))


if __name__ == "__main__":
    unittest.main(verbosity=2)
