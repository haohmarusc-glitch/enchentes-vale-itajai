"""A sonda da API da ANA olha; não grava dado do projeto.

Ela existe porque em 08/09/2026 a `HidroSerieCotas` mostrou que o FORMATO da
resposta é o que decide tudo — a série de rótulo melhor apagava uma cheia de
4 m. Escrever coletor contra formato suposto repetiria o erro. Estes testes
travam o que a sonda pode e não pode fazer, já que o alvo dela é a rede e
ninguém consegue rodá-la no CI.
"""

from __future__ import annotations

import unittest
from pathlib import Path

import sonda_ana_api as sonda

FONTE = (Path(__file__).resolve().parent / "sonda_ana_api.py").read_text(encoding="utf-8")


class NaoEscreveNoProjeto(unittest.TestCase):
    def test_nao_toca_nos_jsons_de_verdade(self):
        """
        Sonda que grava em estacoes.json ou enchentes.json deixa de ser sonda.
        A decisão de gravar dado neste projeto é humana — mesma divisão do
        ana_hidroweb.py e do ana_inventario.py.
        """
        for arquivo in ("estacoes.json", "enchentes.json", "transito.json"):
            self.assertNotIn(f'"{arquivo}"', FONTE, f"a sonda menciona {arquivo} em código")

    def test_o_unico_write_e_em_brutos(self):
        for linha in FONTE.splitlines():
            if "write_text" in linha and not linha.strip().startswith("#"):
                self.assertIn("destino", linha, f"escrita fora de data/brutos: {linha.strip()}")


class ChamaAsRotasQueASpecDeclara(unittest.TestCase):
    """Os caminhos vieram de /api-docs em 08/09/2026, não de suposição."""

    def test_rotas(self):
        self.assertEqual(sonda.ROTA_INVENTARIO,
                         "/EstacoesTelemetricas/HidroInventarioEstacoes/v1")
        self.assertEqual(sonda.ROTA_TELEMETRIA,
                         "/EstacoesTelemetricas/HidroinfoanaSerieTelemetricaAdotada/v1")

    def test_o_range_pedido_esta_no_enum_da_spec(self):
        """`Range Intervalo de busca` é obrigatório e é enum. HORA_24 existe."""
        self.assertIn('"HORA_24"', FONTE)

    def test_respeita_o_turno_entre_chamadas(self):
        """Rate limit é regra do projeto para toda fonte externa."""
        self.assertIn("espera_turno()", FONTE)

    def test_identifica_o_user_agent(self):
        self.assertIn("USER_AGENT", FONTE)


class ResumoNaoMenteQuandoDaErrado(unittest.TestCase):
    def test_http_errado_vira_texto_visivel(self):
        linha, itens = sonda._resumo({"_erro": "HTTP 401", "_corpo": "sem token"})
        self.assertIn("401", linha)
        self.assertEqual(itens, [])

    def test_resposta_sem_items_diz_quais_chaves_vieram(self):
        linha, itens = sonda._resumo({"status": "OK", "outra_coisa": 1})
        self.assertIn("sem lista", linha)
        self.assertIn("outra_coisa", linha)
        self.assertEqual(itens, [])

    def test_lista_vazia_nao_e_confundida_com_sucesso(self):
        linha, itens = sonda._resumo({"message": "Não houve retorno de registros. Verifique!",
                                      "items": []})
        self.assertIn("0 item", linha)
        self.assertEqual(itens, [])

    def test_lista_com_itens_conta_certo(self):
        linha, itens = sonda._resumo({"message": "Sucesso", "items": [{"a": 1}, {"a": 2}]})
        self.assertIn("2 item", linha)
        self.assertEqual(len(itens), 2)


class AsCandidatasSaoDaBacia(unittest.TestCase):
    def test_todas_estao_no_cadastro_de_estacoes_conhecidas(self):
        """
        Sondar um código que o projeto não conhece daria um resultado sem dono.
        E o cadastro é onde está escrito por que cada uma NÃO é régua de cidade.
        """
        import validar_dados as vd
        for codigo in sonda.CANDIDATAS:
            with self.subTest(codigo=codigo):
                self.assertIn(codigo.lstrip("0"), vd.ESTACOES_ANA_CONHECIDAS)

    def test_sondar_nao_e_vincular(self):
        """
        A sonda olha nível ao vivo; NÃO afirma que a estação é a régua daquela
        cidade. Quatro dessas candidatas são recusas escritas em
        `codigo_ana_nao_e`, e é assim que o Salseiro quase entrou em Vidal
        Ramos. O aviso tem de estar no próprio arquivo.
        """
        self.assertIn("conferência de régua", FONTE)


if __name__ == "__main__":
    unittest.main()
