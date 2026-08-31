#!/usr/bin/env python3
"""
Testes do importador das cotas de Rio do Sul.

O que se testa aqui é o que decide se alguém sai de casa: se o número que entra
no arquivo é o que a fonte publicou, se o que não é número de rio fica de fora,
e se importar duas vezes não estraga o que já estava lá.
"""

import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from importar_cotas_rio_do_sul import (
    TETO_DA_FONTE, como_registro, cota_de_inundacao_da_cidade, extrair, mesclar,
    robots_permite,
)


class TestExtrair(unittest.TestCase):
    def test_le_as_tres_formas_que_o_minificador_gera(self):
        js = ("[{name:`1 DE MAIO`,min:8.12,max:9.65},"
              '{"name":"10 DE OUTUBRO","min":8.25,"max":10.01},'
              "{min:11.59,max:12.52,name:'7 DE SETEMBRO'}]")
        ruas, _ = extrair(js)
        self.assertEqual([r["rua"] for r in ruas],
                         ["1 DE MAIO", "10 DE OUTUBRO", "7 DE SETEMBRO"])
        self.assertEqual(ruas[0]["min"], 8.12)
        self.assertEqual(ruas[2]["max"], 12.52)

    def test_objeto_sem_min_nao_e_rua(self):
        """Item de menu tem `name` e não tem cota. Não vira rua em silêncio."""
        js = "[{name:`Painel Principal`,path:`/painel`},{name:`RUA X`,min:9.1}]"
        ruas, _ = extrair(js)
        self.assertEqual([r["rua"] for r in ruas], ["RUA X"])

    def test_min_nulo_nao_vira_zero(self):
        js = "[{name:`RUA SEM COTA`,min:null,max:null}]"
        ruas, _ = extrair(js)
        self.assertEqual(ruas, [])

    def test_valor_fora_da_faixa_de_rio_e_recusado_com_motivo(self):
        js = "[{name:`ALTITUDE`,min:340.5},{name:`NEGATIVA`,min:-2},{name:`OK`,min:9.0}]"
        ruas, recusas = extrair(js)
        self.assertEqual([r["rua"] for r in ruas], ["OK"])
        self.assertEqual(len(recusas), 2)
        self.assertTrue(any("340.5" in m for m in recusas))

    def test_maxima_menor_que_minima_perde_so_a_maxima(self):
        """A rua não some por causa de um campo torto: perde o campo torto."""
        js = "[{name:`INVERTIDA`,min:9.0,max:7.0}]"
        ruas, recusas = extrair(js)
        self.assertEqual(len(ruas), 1)
        self.assertEqual(ruas[0]["min"], 9.0)
        self.assertIsNone(ruas[0]["max"])
        self.assertTrue(any("abaixo da mínima" in m for m in recusas))

    def test_repetido_mantem_o_primeiro_e_avisa(self):
        js = "[{name:`RUA X`,min:9.0},{name:`rua x`,min:11.0}]"
        ruas, recusas = extrair(js)
        self.assertEqual(len(ruas), 1)
        self.assertEqual(ruas[0]["min"], 9.0)
        self.assertTrue(any("repetido" in m for m in recusas))


class TestRegistro(unittest.TestCase):
    def test_cota_m_recebe_a_minima_que_e_a_que_avisa(self):
        r = como_registro({"rua": "1 DE MAIO", "min": 8.12, "max": 9.65}, "fonte", "2026-08-31")
        self.assertEqual(r["cota_m"], 8.12)
        self.assertEqual(r["cota_max_m"], 9.65)
        self.assertEqual(r["referencia"], "régua")
        self.assertEqual(r["cidade"], "rio-do-sul")

    def test_teto_da_escala_nao_vira_cota(self):
        """
        A fonte usa 20 m como "acima disto não foi medido". Gravar 20 como a
        cota em que a rua alaga inteira seria inventar precisão que não existe.
        """
        r = como_registro({"rua": "ALTA", "min": 18.92, "max": TETO_DA_FONTE},
                          "fonte", "2026-08-31")
        self.assertNotIn("cota_max_m", r)
        self.assertIn("teto da escala", r["nota"])

    def test_cota_abaixo_do_piso_da_cidade_entra_com_ressalva(self):
        """
        A fonte publica rua alagando a 3,11 m e a menor cota de Rio do Sul é
        4,50 m — a régua marca mais que isso num dia seco. O dado entra, porque
        é oficial e publicado, mas entra dizendo que precisa de conferência:
        sem a nota, "este nível já foi alcançado" apareceria com tempo bom.
        """
        r = como_registro({"rua": "POUSO REDONDO", "min": 3.11, "max": 7.0},
                          "fonte", "2026-08-31", piso_da_cidade=4.5)
        self.assertEqual(r["cota_m"], 3.11)
        self.assertIn("ABAIXO", r["nota"])
        self.assertIn("não foi conferida", r["nota"])
        # Não move aviso: sem isto, o validador exigiria baixar a cota de
        # atenção da cidade por causa de um número que ninguém conferiu.
        self.assertIs(r["usar_para_aviso"], False)

    def test_cota_acima_do_piso_nao_ganha_ressalva(self):
        r = como_registro({"rua": "1 DE MAIO", "min": 8.12, "max": 9.65},
                          "fonte", "2026-08-31", piso_da_cidade=4.5)
        self.assertNotIn("nota", r)
        self.assertNotIn("usar_para_aviso", r)

    def test_as_duas_ressalvas_cabem_no_mesmo_registro(self):
        r = como_registro({"rua": "ESTRANHA", "min": 3.0, "max": TETO_DA_FONTE},
                          "fonte", "2026-08-31", piso_da_cidade=4.5)
        self.assertIn("teto da escala", r["nota"])
        self.assertIn("ABAIXO", r["nota"])
        self.assertNotIn("cota_max_m", r)

    def test_sem_piso_conhecido_nada_e_inventado(self):
        r = como_registro({"rua": "X", "min": 3.0, "max": None},
                          "fonte", "2026-08-31", piso_da_cidade=None)
        self.assertNotIn("nota", r)

    def test_o_piso_vem_do_arquivo_e_nao_de_numero_cravado(self):
        """Se a cota de Rio do Sul mudar em estacoes.json, a ressalva acompanha."""
        piso = cota_de_inundacao_da_cidade()
        self.assertIsNotNone(piso)
        self.assertGreater(piso, 0)

    def test_todo_registro_leva_fonte_e_confianca(self):
        r = como_registro({"rua": "X", "min": 9.0, "max": None}, "portal", "2026-08-31")
        self.assertEqual(r["fonte"], "portal")
        self.assertEqual(r["confianca"], "alta")
        self.assertEqual(r["data_fonte"], "2026-08-31")


class TestMesclar(unittest.TestCase):
    def base(self) -> list[dict]:
        return [
            {"cidade": "blumenau", "rua": "Rua São Rafael", "ponto": "final da rua", "cota_m": 7.4},
            {"cidade": "brusque", "rua": "Rua Coelho Neto", "ponto": None, "cota_m": 5.64},
        ]

    def test_nao_toca_em_registro_de_outra_cidade(self):
        novos = [{"cidade": "rio-do-sul", "rua": "1 DE MAIO", "ponto": "p", "cota_m": 8.12}]
        saida, n, a = mesclar(self.base(), novos)
        self.assertEqual(len(saida), 3)
        self.assertEqual((n, a), (1, 0))
        self.assertEqual(saida[0]["cidade"], "blumenau")

    def test_importar_duas_vezes_da_o_mesmo_arquivo(self):
        novos = [{"cidade": "rio-do-sul", "rua": "1 DE MAIO", "ponto": "p", "cota_m": 8.12}]
        uma, _, _ = mesclar(self.base(), novos)
        duas, n, a = mesclar(uma, novos)
        self.assertEqual(uma, duas)
        self.assertEqual((n, a), (0, 1))

    def test_cota_corrigida_na_fonte_atualiza_no_lugar(self):
        antes = self.base() + [{"cidade": "rio-do-sul", "rua": "1 DE MAIO",
                                "ponto": "p", "cota_m": 8.12}]
        novos = [{"cidade": "rio-do-sul", "rua": "1 DE MAIO", "ponto": "p", "cota_m": 8.40}]
        saida, n, a = mesclar(antes, novos)
        self.assertEqual(len(saida), 3)
        self.assertEqual((n, a), (0, 1))
        self.assertEqual(saida[2]["cota_m"], 8.40)


class TestRobots(unittest.TestCase):
    """
    O AlertaBlu foi recusado por robots.txt. A mesma régua vale para todo mundo,
    inclusive para a fonte que nos interessa.
    """

    def test_proibicao_do_caminho_bloqueia(self):
        robots = "User-agent: *\nDisallow: /index.php\n"
        self.assertFalse(robots_permite(robots, "/index.php"))

    def test_proibicao_de_outro_caminho_nao_bloqueia(self):
        robots = "User-agent: *\nDisallow: /admin\n"
        self.assertTrue(robots_permite(robots, "/index.php"))

    def test_disallow_vazio_e_permissao(self):
        self.assertTrue(robots_permite("User-agent: *\nDisallow:\n", "/qualquer"))

    def test_regra_de_outro_agente_nao_vale_para_nos(self):
        robots = "User-agent: GPTBot\nDisallow: /\n\nUser-agent: *\nDisallow: /admin\n"
        self.assertTrue(robots_permite(robots, "/index.php"))

    def test_comentario_e_ignorado(self):
        robots = "User-agent: *\n# Disallow: /index.php\nDisallow: /admin\n"
        self.assertTrue(robots_permite(robots, "/index.php"))

    def test_robots_vazio_permite(self):
        self.assertTrue(robots_permite("", "/index.php"))


class TestFormatoDoArquivo(unittest.TestCase):
    def test_registro_gerado_tem_os_campos_que_o_validador_exige(self):
        r = como_registro({"rua": "X", "min": 9.0, "max": 10.0}, "f", "2026-08-31")
        for campo in ("cidade", "rio", "rua", "cota_m", "fonte", "confianca", "referencia"):
            self.assertIn(campo, r, f"falta {campo}")

    def test_o_arquivo_real_continua_valido_depois_de_mesclar(self):
        """
        Com uma rua que ainda NÃO está no arquivo — as 554 de Rio do Sul já
        estão, e usar uma delas testaria atualização, não inclusão.
        """
        arquivo = Path(__file__).resolve().parent.parent / "data" / "cotas-ruas.json"
        base = json.loads(arquivo.read_text(encoding="utf-8"))
        novos = [como_registro({"rua": "RUA QUE NAO EXISTE NO ARQUIVO", "min": 8.12,
                                "max": 9.65}, "portal", "2026-08-31")]
        saida, n, _ = mesclar(base["cotas"], novos)
        self.assertEqual(n, 1)
        self.assertEqual(len(saida), len(base["cotas"]) + 1)
        # Nenhum registro anterior mudou.
        self.assertEqual(saida[: len(base["cotas"])], base["cotas"])

    def test_reimportar_o_arquivo_real_nao_duplica_nada(self):
        """As 554 já estão gravadas: mesclar de novo atualiza, não acrescenta."""
        arquivo = Path(__file__).resolve().parent.parent / "data" / "cotas-ruas.json"
        base = json.loads(arquivo.read_text(encoding="utf-8"))
        de_rio_do_sul = [r for r in base["cotas"] if r["cidade"] == "rio-do-sul"]
        self.assertGreater(len(de_rio_do_sul), 500)
        saida, n, a = mesclar(base["cotas"], de_rio_do_sul)
        self.assertEqual(n, 0)
        self.assertEqual(a, len(de_rio_do_sul))
        self.assertEqual(saida, base["cotas"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
