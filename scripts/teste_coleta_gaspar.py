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

import json
import sys
from datetime import datetime
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import coleta_gaspar as cg
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


#: Cabeçalho com as janelas curtas, que o INDICES enxuto acima não tem.
INDICES_CHUVA = {"estacao": 0, "fonte": 1, "coleta": 2, "nivel": 3,
                 "chuva_atual": 4, "chuva_1h": 5, "chuva_6h": 6, "chuva_24h": 7}


class TestCoerenciaDaChuva(unittest.TestCase):
    """
    Janela curta não pode ter mais chuva que a longa que a contém.

    É a mesma regra do coletor de Itajaí, reusada — e não recopiada — porque
    regra duplicada é regra que diverge, e é sempre a cópia esquecida que passa
    a aceitar lixo.

    O que está em jogo: a atenção de Gaspar dispara com chuva acima de 6 mm.
    Um campo que marca 108 mm com a última hora em zero acionaria isso todo dia.
    Alarme falso ensina a pessoa a desligar o aviso — justamente antes da noite
    em que ele importaria.
    """

    def test_leitura_coerente_passa_sem_marca(self):
        item = ler_linha(["PLU - ARRAIAL D' OURO", "CEMADEN", "31/08 23:29", "-",
                          "0,00", "0,39", "28,30", "91,77"], INDICES_CHUVA)
        self.assertTrue(item["chuva_coerente"])
        self.assertIsNone(item["chuva_incoerencias"])

    def test_chuva_atual_maior_que_a_ultima_hora_e_marcada(self):
        # Se 42 mm tivessem caído agora, a última hora não poderia marcar zero.
        item = ler_linha(["PLU LOC. - SERTÃO VERDE", "DC. GASPAR", "31/08 17:12", "-",
                          "42,00", "0,00", "0,00", "104,00"], INDICES_CHUVA)
        self.assertFalse(item["chuva_coerente"])
        self.assertIn("chuva_atual=42 mm > chuva_1h=0 mm", item["chuva_incoerencias"])

    def test_o_dado_incoerente_nao_e_apagado(self):
        # Marcar não é censurar: quem lê a tabela crua continua vendo o que a
        # fonte publicou, e quem for USAR a chuva é que decide o que fazer.
        item = ler_linha(["PLU. - ALTO GASPARINHO", "DC. GASPAR", "31/08 13:50", "-",
                          "108,00", "0,00", "0,00", "108,00"], INDICES_CHUVA)
        self.assertEqual(item["chuva_mm"]["chuva_atual"], 108.0)
        self.assertFalse(item["chuva_coerente"])

    def test_janela_ausente_nao_conta_como_zero(self):
        # Ausência de dado não é chuva zero: comparar contra um buraco
        # inventaria incoerência onde só falta medição.
        item = ler_linha(["PLU", "Cemaden", "31/08 23:29", "-",
                          "0,00", "-", "-", "82,29"], INDICES_CHUVA)
        self.assertTrue(item["chuva_coerente"])

    def test_linha_so_de_nivel_nao_opina_sobre_chuva(self):
        item = ler_linha(["Rio Itajaí Açu Gaspar", "DC. Gaspar", "31/08 22:59", "3,85",
                          "70,00"], INDICES)
        self.assertEqual(item["nivel_m"], 3.85)
        # Tem chuva_24h, então opina; o que não pode é inventar veredito sem
        # nenhuma janela.
        self.assertIsNotNone(item["chuva_coerente"])

    def test_a_pagina_real_marca_exatamente_as_tres_conhecidas(self):
        """
        Trava o achado contra a página salva: três pluviômetros da DC. GASPAR
        publicam `chuva atual` de 42, 100 e 108 mm com a última hora em zero.
        Se a fonte se corrigir, este teste cai e a descoberta é revisitada — que
        é o ponto de travar num arquivo real e não num exemplo inventado.
        """
        if not PAGINA_REAL.exists():
            self.skipTest("página real de Gaspar não está neste checkout")
        d = analisar(PAGINA_REAL.read_text(encoding="utf-8", errors="replace"))
        ruins = sorted(e["rotulo"] for e in d["estacoes"] if e["chuva_coerente"] is False)
        self.assertEqual(len(ruins), 3, f"esperava 3 incoerentes, achei {ruins}")
        # A régua oficial do rio — a que a legenda do /estacao/ver/21 descreve —
        # tem de estar entre as COERENTES: é nela que um gatilho por chuva se
        # apoiaria.
        regua = next(e for e in d["estacoes"] if e["rotulo"] == "Rio Itajaí Açu Gaspar")
        self.assertTrue(regua["chuva_coerente"])


class LeituraDeCidade(unittest.TestCase):
    """
    Qual linha da tabela vira o NÍVEL DE GASPAR — e por que não pode ser por
    semelhança de nome.

    A mesma tabela publica três coisas que uma busca frouxa por "gaspar"
    pegaria, e uma delas não seria recusada por nada no sistema:

        PLU. - ALTO GASPARINHO      pluviômetro, nome contém "gaspar"
        RIBEIRÃO BELCHIOR CENTRAL   1,68 m — nível PLAUSÍVEL, outro curso
        Barragem Oeste Taió         cota de reservatório

    A do meio é a perigosa: passa na régua de plausibilidade, então Gaspar
    apareceria "normal" com 1,68 m enquanto o Açu estivesse em 6 m. Silêncio no
    lugar de alarme é o pior desfecho deste projeto.
    """

    def analise(self, estacoes):
        return {"estacoes": estacoes, "barragens": [], "faixas_propostas": {}}

    def estacao(self, rotulo, nivel=3.85, iso="2026-08-31T22:59:00", plaus=True):
        return {"rotulo": rotulo, "nivel_m": nivel, "nivel_plausivel": plaus,
                "medido_em_iso": iso}

    def test_pega_a_regua_do_acu_e_so_ela(self):
        d = self.analise([
            self.estacao("PLU. - ALTO GASPARINHO", nivel=None, plaus=False),
            self.estacao("RIBEIRÃO BELCHIOR CENTRAL", nivel=1.68),
            self.estacao("Rio Itajaí Açu Gaspar", nivel=3.85),
        ])
        l = cg.leitura_da_cidade(d)
        self.assertIsNotNone(l)
        self.assertEqual(l["nivel_m"], 3.85, "pegou a régua errada")
        self.assertEqual(l["cidade"], "gaspar")
        self.assertEqual(l["rio"], "itajai-acu")

    def test_o_BELCHIOR_sozinho_NAO_vira_nivel_de_gaspar(self):
        # O caso que o silêncio esconderia: só o ribeirão na tabela.
        d = self.analise([self.estacao("RIBEIRÃO BELCHIOR CENTRAL", nivel=1.68)])
        self.assertIsNone(cg.leitura_da_cidade(d))

    def test_gasparinho_nao_e_gaspar(self):
        d = self.analise([self.estacao("PLU. - ALTO GASPARINHO", nivel=2.0)])
        self.assertIsNone(cg.leitura_da_cidade(d))

    def test_sem_carimbo_ou_implausivel_nao_ha_leitura(self):
        # Sem idade o número não diz nada sobre agora.
        d = self.analise([self.estacao("Rio Itajaí Açu Gaspar", iso=None)])
        self.assertIsNone(cg.leitura_da_cidade(d))
        d = self.analise([self.estacao("Rio Itajaí Açu Gaspar", plaus=False)])
        self.assertIsNone(cg.leitura_da_cidade(d))
        d = self.analise([self.estacao("Rio Itajaí Açu Gaspar", nivel=None)])
        self.assertIsNone(cg.leitura_da_cidade(d))

    def test_acento_e_caixa_nao_atrapalham_a_igualdade(self):
        for r in ("RIO ITAJAI ACU GASPAR", "rio itajaí açu gaspar", " Rio Itajaí Açu Gaspar "):
            self.assertTrue(cg.e_a_regua_do_acu(r), r)
        for r in ("Rio Itajaí Açu Ilhota", "Ribeirão Belchior Central", ""):
            self.assertFalse(cg.e_a_regua_do_acu(r), r)

    def test_a_leitura_REAL_de_31_08_cai_na_faixa_certa(self):
        """
        Conferência cruzada com as cotas do Plano (5 / 6 / 7 m): 3,85 m é
        NORMALIDADE, abaixo da atenção. Se a régua lida fosse outra, este
        número não teria por que cair onde cai.
        """
        d = json.loads((RAIZ / "data/tempo-real/ultimo_gaspar.json").read_text(encoding="utf-8"))
        l = cg.leitura_da_cidade(d)
        self.assertIsNotNone(l, "a captura real deixou de produzir leitura de cidade")
        self.assertEqual(l["nivel_m"], 3.85)
        est = json.loads((RAIZ / "data/estacoes.json").read_text(encoding="utf-8"))
        gaspar = next(c for c in est["rios"]["itajai-acu"]["cidades"] if c["id"] == "gaspar")
        self.assertLess(l["nivel_m"], gaspar["cotas_m"]["atencao"])

    def test_sai_marcada_para_virar_faixa(self):
        # Cota municipal + régua municipal do mesmo rio: PODE pintar cor, ao
        # contrário do bruto estadual. A ressalva (o Plano não publica o zero)
        # está escrita no `leitura_da_cidade`.
        d = self.analise([self.estacao("Rio Itajaí Açu Gaspar")])
        self.assertIs(cg.leitura_da_cidade(d)["usar_para_cota"], True)


if __name__ == "__main__":
    unittest.main(verbosity=2)
