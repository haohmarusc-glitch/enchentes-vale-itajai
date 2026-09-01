#!/usr/bin/env python3
"""
Testes do leitor da tabela da Defesa Civil de Gaspar.

Gaspar é a cidade com mais cotas de rua e nenhuma cota de régua. O que este
script propuser como cota vira, um dia, o limiar que dispara o aviso lá — e um
limiar errado não aparece na tela: o site continua bonito, o bot continua
respondendo, e o telefone toca na hora errada, ou não toca.

Por isso quase todos os testes aqui são sobre o que ele **recusa** a chamar de
nível e de cota.
"""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from coleta_gaspar import (MARGEM_DO_NIVEL_M, analisar, e_barragem,
                           faixas_da_linha, ler_linha, permitido)

TABELA = """
<table>
  <tr><th>Estação</th><th>Nível</th><th>Atualizado</th></tr>
  <tr><td>Rio Itajaí Açu Gaspar</td><td>3,25 m</td><td>01/09/2026 01:00</td></tr>
  <tr><td>Barragem Oeste</td><td>ocupação 85,4 %</td><td>9,79 m</td></tr>
</table>
"""


class TestLerLinha(unittest.TestCase):
    def test_cada_grandeza_sai_da_propria_celula(self):
        """
        O defeito que motivou a reescrita: juntando a linha inteira e pegando o
        primeiro decimal, a ocupação de 85,4 % da barragem virava o nível dela.
        """
        item = ler_linha(["Barragem Oeste", "ocupação 85,4 %", "9,79 m"])
        self.assertEqual(item["ocupacao_pct"], 85.4)
        self.assertEqual(item["nivel_m"], 9.79)

    def test_a_unidade_e_obrigatoria_para_virar_nivel(self):
        """Sem o "m", 85,4 é ocupação e 01/09/2026 é data — nenhum é nível."""
        item = ler_linha(["X", "85,4 %", "01/09/2026 01:00"])
        self.assertIsNone(item["nivel_m"])

    def test_nivel_fora_da_faixa_do_rio_e_marcado(self):
        """
        349 m é o caso das estações que leem altitude. O número aparece, mas
        marcado — nunca some calado nem passa por nível.
        """
        item = ler_linha(["Mirim Doce", "349,08 m"])
        self.assertEqual(item["nivel_m"], 349.08)
        self.assertFalse(item["nivel_plausivel"])

    def test_nivel_plausivel_e_marcado_como_tal(self):
        self.assertTrue(ler_linha(["Gaspar", "3,25 m"])["nivel_plausivel"])

    def test_linha_sem_numero_nenhum_nao_vira_leitura(self):
        self.assertIsNone(ler_linha(["Estação", "Nível", "Atualizado"]))

    def test_linha_vazia_ou_curta_demais_nao_vira_leitura(self):
        for cels in ([], [""], ["só o rótulo"]):
            with self.subTest(cels=cels):
                self.assertIsNone(ler_linha(cels))

    def test_a_linha_bruta_fica_para_o_ajuste_do_parser(self):
        item = ler_linha(["Gaspar", "3,25 m", "01/09/2026 01:00"])
        self.assertIn("3,25 m", item["linha_bruta"])


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
        self.assertEqual([b["rotulo"] for b in lido["barragens"]], ["Barragem Oeste"])

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
        self.assertEqual(lido["estacoes"][0]["nivel_m"], 3.25)
        Path(caminho).unlink()

    def test_html_com_byte_estranho_nao_quebra_a_leitura(self):
        """Página salva do navegador pode vir em outra codificação."""
        lido = analisar(TABELA.replace("Açu", "A\ufffdu"))
        self.assertEqual(len(lido["estacoes"]), 1)


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
