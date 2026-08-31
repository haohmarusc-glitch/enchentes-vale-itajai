#!/usr/bin/env python3
"""
Testes do importador das cotas de Brusque (camada de 2023).

O que se testa aqui não é formato de JSON: é a evidência. Esta importação grava
`confianca: alta` — o grau mais forte do projeto — apoiada numa única conta,
`cota + lâmina = 8,96 m`. Se essa conta deixar de valer e a importação seguir
mesmo assim, o site passa a dizer a 350 pontos de Brusque um número cujo
significado ninguém conhece. Os testes abaixo existem para que isso quebre alto.
"""

import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from importar_cotas_brusque import (
    BRUTO, FRACAO_MINIMA_CONFERIDA, PICO_2023_M, TOLERANCIA_M, autorizado,
    chave, como_registro, fecha_a_conta, mesclar, normalizar, numero, verificar,
)

RAIZ = Path(__file__).resolve().parent.parent


def ponto(cota, lamina=None, rua="Rua Teste", bairro="Centro", esquina=None) -> dict:
    return {"cota_rotulo": cota, "nivel_registrado_no_local": lamina,
            "rua": rua, "bairro": bairro, "esquina": esquina}


class TestNumero(unittest.TestCase):
    """
    A fonte escreve o mesmo número de quatro jeitos. O primeiro corte deste
    importador lia só dois, e 160 dos 344 pontos com lâmina saíam da conferência
    calados — a prova ficava apoiada em metade da amostra sem que nada avisasse.
    """

    def test_le_virgula_ponto_e_unidade(self):
        for texto in ("7,65", "7.65", "7,65 m", "7,65 m.", " 7,65 M ", "7,65m"):
            with self.subTest(texto=texto):
                self.assertEqual(numero(texto), 7.65)

    def test_o_que_nao_e_numero_vira_none(self):
        for texto in (None, "", "sem cota", "abc", "m"):
            with self.subTest(texto=texto):
                self.assertIsNone(numero(texto))

    def test_nao_inventa_numero_a_partir_de_texto_com_numero_dentro(self):
        self.assertIsNone(numero("cota 7,65 na parede"))


class TestFechaAConta(unittest.TestCase):
    def test_fecha_quando_a_soma_da_o_pico(self):
        self.assertTrue(fecha_a_conta(ponto("7,65", "1,31")))

    def test_nao_fecha_quando_a_soma_erra(self):
        self.assertFalse(fecha_a_conta(ponto("6,48", "1,10")))

    def test_sem_lamina_nao_ha_o_que_conferir(self):
        self.assertIsNone(fecha_a_conta(ponto("9,64", None)))

    def test_a_tolerancia_e_do_tamanho_do_arredondamento_da_fonte(self):
        """Um centímetro passa; dois já são divergência de verdade."""
        self.assertTrue(fecha_a_conta(ponto(f"{PICO_2023_M - 1.30 + 0.01:.2f}", "1,30")))
        self.assertFalse(fecha_a_conta(ponto(f"{PICO_2023_M - 1.30 + 0.03:.2f}", "1,30")))
        self.assertLess(TOLERANCIA_M, 0.02)


class TestAutorizado(unittest.TestCase):
    """
    O portão da importação. É a linha entre gravar cota de régua e gravar
    número de significado desconhecido.
    """

    def test_recusa_quando_a_conta_para_de_fechar(self):
        self.assertFalse(autorizado(conferidos=50, com_lamina=100))

    def test_recusa_quando_nao_ha_o_que_conferir(self):
        self.assertFalse(autorizado(conferidos=0, com_lamina=0),
                         "camada sem nenhuma lâmina não prova nada e não pode passar")

    def test_autoriza_a_camada_real(self):
        self.assertTrue(autorizado(conferidos=338, com_lamina=344))

    def test_a_fracao_exigida_e_quase_a_totalidade(self):
        self.assertGreaterEqual(FRACAO_MINIMA_CONFERIDA, 0.95)


class TestComoRegistro(unittest.TestCase):
    def test_ponto_cuja_conta_nao_fecha_nao_entra(self):
        """
        Francisco Sassi, da camada real: 6,48 + 1,10 = 7,58, e não 8,96. Um dos
        dois números está errado e não dá para saber qual. Gravar 6,48 seria
        avisar essa rua 1,38 m antes da hora — ou, se o errado for o outro,
        nunca. A rua já tem cota na lista oficial de out/2023; esta some.
        """
        self.assertIsNone(como_registro(ponto("6,48", "1,10", rua="Francisco Sassi")))

    def test_ponto_sem_rua_nao_entra(self):
        self.assertIsNone(como_registro(ponto("7,65", "1,31", rua="  ")))

    def test_ponto_sem_cota_numerica_nao_entra(self):
        self.assertIsNone(como_registro(ponto("sem cota", "1,31")))

    def test_registro_bom_sai_como_regua_e_confianca_alta(self):
        r = como_registro(ponto("7,65", "1,31"))
        self.assertEqual(r["cota_m"], 7.65)
        self.assertEqual(r["referencia"], "régua")
        self.assertEqual(r["confianca"], "alta")
        self.assertEqual(r["cidade"], "brusque")
        self.assertEqual(r["rio"], "itajai-mirim")

    def test_a_lamina_medida_fica_guardada_na_nota(self):
        """Guardar a lâmina deixa a conta refazível sem voltar ao bruto."""
        self.assertIn("1,31", como_registro(ponto("7,65", "1,31"))["nota"].replace(".", ","))

    def test_ponto_sem_lamina_diz_que_nao_pode_ser_conferido(self):
        nota = como_registro(ponto("9,64", None))["nota"]
        self.assertIn("não publica a lâmina", nota)

    def test_cota_acima_do_recorde_entra_com_ressalva(self):
        nota = como_registro(ponto("11,01", None))["nota"]
        self.assertIn("maior pico já registrado", nota)

    def test_cota_abaixo_do_piso_da_cidade_nao_move_aviso(self):
        """
        3,76 m é o ponto mais baixo da camada e fica 1,04 m ABAIXO da cota de
        atenção de Brusque (4,80 m). O número é oficial e aparece na tela; o que
        ele não pode fazer é baixar sozinho o limiar do aviso, que passaria a
        tocar com o rio em nível quase normal. Fechar essa lacuna é assunto de
        ofício à Defesa Civil, não de limiar inventado por este script.
        """
        r = como_registro(ponto("3,76", "5,20"), piso=4.80)
        self.assertEqual(r["cota_m"], 3.76, "o número continua na tela")
        self.assertIs(r["usar_para_aviso"], False)
        self.assertIn("não use como aviso sozinha", r["nota"])

    def test_sem_piso_conhecido_nenhum_registro_e_silenciado(self):
        r = como_registro(ponto("3,76", "5,20"), piso=None)
        self.assertNotIn("usar_para_aviso", r)


class TestIdentidade(unittest.TestCase):
    def test_mesma_rua_sem_esquina_com_cotas_diferentes_sao_pontos_diferentes(self):
        """
        "General Osório" aparece 17 vezes na camada, quase sempre sem esquina.
        Sem a cota na identidade, dezesseis desses pontos sumiriam calados.
        """
        a = {"cidade": "brusque", "rua": "General Osório", "ponto": None, "cota_m": 8.06}
        b = {"cidade": "brusque", "rua": "General Osório", "ponto": None, "cota_m": 8.31}
        self.assertNotEqual(chave(a), chave(b))

    def test_acento_e_caixa_nao_criam_registro_novo(self):
        a = {"cidade": "brusque", "rua": "General Osório", "ponto": "Poste", "cota_m": 8.06}
        b = {"cidade": "brusque", "rua": "GENERAL OSORIO", "ponto": "poste", "cota_m": 8.06}
        self.assertEqual(chave(a), chave(b))

    def test_normalizar_junta_espaco_dobrado(self):
        self.assertEqual(normalizar("Rio  Branco"), "RIO BRANCO")


class TestMesclar(unittest.TestCase):
    def novos(self) -> list[dict]:
        return [
            {"cidade": "brusque", "rua": "General Osório", "ponto": None, "cota_m": 8.06},
            {"cidade": "brusque", "rua": "General Osório", "ponto": None, "cota_m": 8.31},
        ]

    def test_nao_apaga_o_que_ja_estava(self):
        antigos = [{"cidade": "brusque", "rua": "Rua Coelho Neto", "ponto": None,
                    "cota_m": 5.64, "confianca": "media"}]
        saida, n, repetidos = mesclar(antigos, self.novos())
        self.assertEqual(n, 2)
        self.assertEqual(saida[0], antigos[0], "o registro anterior sai intacto e no lugar")

    def test_importar_duas_vezes_nao_duplica(self):
        saida, n, _ = mesclar([], self.novos())
        self.assertEqual(n, 2)
        de_novo, n2, repetidos = mesclar(saida, self.novos())
        self.assertEqual((n2, repetidos), (0, 2))
        self.assertEqual(len(de_novo), 2)

    def test_registro_antigo_sem_cota_nao_derruba_a_mesclagem(self):
        """Brusque tem cinco registros com `cota_m: null` na lista oficial."""
        antigos = [{"cidade": "brusque", "rua": "Túnel do Terminal Urbano",
                    "ponto": "Túnel do Terminal Urbano", "cota_m": None}]
        saida, n, _ = mesclar(antigos, self.novos())
        self.assertEqual(len(saida), 3)


class TestCamadaReal(unittest.TestCase):
    """
    Contra o arquivo bruto de verdade. Um teste que só usa exemplo inventado
    passa enquanto a fonte muda embaixo dele.
    """

    @classmethod
    def setUpClass(cls):
        cls.pontos = json.loads(
            (RAIZ / "data" / BRUTO).read_text(encoding="utf-8"))["pontos"]

    def test_a_conta_ainda_fecha_na_camada_inteira(self):
        conferidos, com_lamina, _ = verificar(self.pontos)
        self.assertTrue(autorizado(conferidos, com_lamina),
                        f"só {conferidos} de {com_lamina} fecham em {PICO_2023_M} m — "
                        "a fonte mudou de significado e a importação precisa parar")

    def test_a_conferencia_cobre_quase_todos_os_pontos_com_lamina(self):
        """
        Guarda contra a regressão de parsing: se a leitura de unidade quebrar, o
        denominador cai pela metade e a fração continua alta — a prova encolhe
        sem que nada falhe.
        """
        _, com_lamina, _ = verificar(self.pontos)
        com_texto = sum(1 for p in self.pontos if p.get("nivel_registrado_no_local"))
        self.assertEqual(com_lamina, com_texto,
                         "toda lâmina publicada precisa entrar na conferência")
        self.assertGreater(com_lamina, 300)

    def test_nenhum_registro_importado_contradiz_a_propria_conta(self):
        for p in self.pontos:
            r = como_registro(p)
            if r is not None:
                self.assertIsNot(fecha_a_conta(p), False, r["rua"])

    def test_toda_cota_importada_cabe_na_faixa_de_nivel_do_rio(self):
        for p in self.pontos:
            r = como_registro(p)
            if r is not None:
                with self.subTest(rua=r["rua"]):
                    self.assertTrue(0 < r["cota_m"] < 15.0)

    def test_todo_registro_tem_referencia_fonte_e_confianca(self):
        for p in self.pontos:
            r = como_registro(p)
            if r is not None:
                self.assertEqual(r["referencia"], "régua")
                self.assertTrue(r["fonte"])
                self.assertEqual(r["confianca"], "alta")


class TestNoArquivoGravado(unittest.TestCase):
    """Depois de importado: o que está em `cotas-ruas.json` continua de pé."""

    @classmethod
    def setUpClass(cls):
        cotas = json.loads(
            (RAIZ / "data" / "cotas-ruas.json").read_text(encoding="utf-8"))["cotas"]
        cls.de_2023 = [c for c in cotas
                       if c["cidade"] == "brusque" and c.get("data_fonte") == "2023-11"]
        cls.antigos = [c for c in cotas
                       if c["cidade"] == "brusque" and c.get("data_fonte") != "2023-11"]

    def test_a_lista_oficial_de_out_2023_continua_no_arquivo(self):
        self.assertEqual(len(self.antigos), 27,
                         "os 27 registros anteriores de Brusque não podem sumir")

    def test_a_camada_de_2023_entrou(self):
        self.assertGreater(len(self.de_2023), 300)

    def test_o_unico_ponto_abaixo_do_piso_esta_marcado(self):
        piso = 4.80
        for c in self.de_2023:
            if c["cota_m"] < piso:
                with self.subTest(rua=c["rua"]):
                    self.assertIs(c.get("usar_para_aviso"), False)

    def test_nenhuma_cota_de_2023_chega_perto_do_teto_da_camada_de_2011(self):
        """
        A camada de 2011 tem ponto de 29,53 m. Se algum dia ela vazar para
        dentro desta importação, é aqui que aparece.
        """
        for c in self.de_2023:
            self.assertLess(c["cota_m"], 12.0, c["rua"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
