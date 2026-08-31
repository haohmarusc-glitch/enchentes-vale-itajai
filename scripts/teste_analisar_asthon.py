#!/usr/bin/env python3
"""
Testes da análise da API Asthon.

Esta análise decide o que, de 29 estações novas, pode disparar aviso por
Telegram. Um erro para o lado permissivo aqui não aparece na tela: aparece como
uma mensagem de madrugada dizendo que o rio subiu, com um número que era
altitude, ou a cota de outra cidade, ou o nível de um reservatório.
"""

import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from analisar_asthon import (BRUTO, COTAS_DE_RIO_DO_SUL, REGUA_DE_RIO_DO_SUL,
                             carregar, cotas_da, e_barragem, veredito)

FAIXAS_DE_RIO_DO_SUL = [
    {"band_key": "atencao", "cota_m": 4.5},
    {"band_key": "alerta", "cota_m": 5.5},
    {"band_key": "emergencia", "cota_m": 6.5},
]


def estacao(nome="Régua Qualquer", nivel=3.0, faixas=None) -> dict:
    return {"name": nome, "level_m": nivel, "band_thresholds": faixas}


SEM_BARRAGEM = {"dams": []}


class TestCotasDa(unittest.TestCase):
    def test_le_as_tres_faixas(self):
        self.assertEqual(cotas_da(estacao(faixas=FAIXAS_DE_RIO_DO_SUL)),
                         {"atencao": 4.5, "alerta": 5.5, "emergencia": 6.5})

    def test_sem_faixa_devolve_vazio(self):
        self.assertEqual(cotas_da(estacao()), {})
        self.assertEqual(cotas_da({"name": "X"}), {})

    def test_faixa_sem_numero_nao_entra(self):
        self.assertEqual(cotas_da(estacao(faixas=[{"band_key": "atencao", "cota_m": None}])), {})


class TestVeredito(unittest.TestCase):
    def test_regua_com_cota_propria_pode_avisar(self):
        e = estacao("Itoupava", 0.91, [{"band_key": "atencao", "cota_m": 1.702}])
        self.assertEqual(veredito(e, SEM_BARRAGEM)[0], "aviso")

    def test_leitura_em_centenas_de_metros_fica_fora(self):
        """Mirim Doce 349,08 · Salete 400,4 · Petrolândia 450,74 · Atalanta 454,12."""
        for nivel in (349.08, 400.4, 450.74, 454.12):
            with self.subTest(nivel=nivel):
                decisao, porque = veredito(estacao("Mirim Doce", nivel), SEM_BARRAGEM)
                self.assertEqual(decisao, "fora")
                self.assertIn("fora da faixa", porque)

    def test_nivel_zerado_fica_fora(self):
        """Zero cravado é sensor parado, não rio seco."""
        self.assertEqual(veredito(estacao("Fundo Canoas", 0.0), SEM_BARRAGEM)[0], "fora")

    def test_sem_nivel_fica_fora(self):
        self.assertEqual(veredito(estacao("Serra Canoas", None), SEM_BARRAGEM)[0], "fora")

    def test_barragem_fica_fora_mesmo_com_cota_e_nivel_plausivel(self):
        """
        A de Taió marca 9,79 m com atenção em 11,65 m: número plausível, cota
        própria, e ainda assim responde a pergunta errada — é o reservatório,
        não o rio na cidade.
        """
        e = estacao("Barragem Oeste Taió", 9.79,
                    [{"band_key": "atencao", "cota_m": 11.65}])
        decisao, porque = veredito(e, {"dams": [{"name": "Barragem Oeste Taió"}]})
        self.assertEqual(decisao, "fora")
        self.assertIn("barragem", porque)

    def test_regua_sem_cota_so_aparece(self):
        decisao, porque = veredito(estacao("Vidal Ramos", 2.93), SEM_BARRAGEM)
        self.assertEqual(decisao, "mostrar")
        self.assertIn("nunca para disparar", porque)

    def test_cota_de_rio_do_sul_em_outra_regua_nao_vira_aviso(self):
        """
        Aplicar a cota de uma régua a outra cria alarme onde não há e cala onde
        há. É o erro que o CLAUDE.md proíbe, e a API o comete em quatro réguas.
        """
        e = estacao("Ponte BR 470", 3.63, FAIXAS_DE_RIO_DO_SUL)
        decisao, porque = veredito(e, SEM_BARRAGEM)
        self.assertEqual(decisao, "mostrar")
        self.assertIn("cota de Rio do Sul", porque)

    def test_a_regua_de_rio_do_sul_com_a_cota_dele_vira_aviso(self):
        e = estacao(REGUA_DE_RIO_DO_SUL, 3.67, FAIXAS_DE_RIO_DO_SUL)
        self.assertEqual(veredito(e, SEM_BARRAGEM)[0], "aviso")

    def test_cota_parecida_mas_diferente_nao_e_confundida_com_copia(self):
        faixas = [{"band_key": "atencao", "cota_m": 4.5},
                  {"band_key": "alerta", "cota_m": 5.5},
                  {"band_key": "emergencia", "cota_m": 7.0}]
        self.assertEqual(veredito(estacao("Outra Régua", 3.0, faixas), SEM_BARRAGEM)[0],
                         "aviso")


class TestDumpReal(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.dump = carregar()
        cls.estacoes = cls.dump["panel"]["stations"]

    def test_o_dump_tem_as_29_estacoes(self):
        self.assertEqual(len(self.estacoes), 29)

    def test_taio_e_ituporanga_so_aparecem_como_barragem(self):
        """
        A pendência dizia que a API cobre Taió e Ituporanga. Cobre as BARRAGENS
        delas, que é outra coisa — e é por isso que esta checagem existe.
        """
        for cidade in ("Taió", "Ituporanga"):
            reguas = [s for s in self.dump["stations_list"]
                      if s.get("spatial_city_name") == cidade]
            self.assertTrue(reguas, cidade)
            for r in reguas:
                self.assertIn("Barragem", r["name"], f"{cidade}: {r['name']}")

    def test_vidal_ramos_tem_regua_de_rio_e_nao_tem_cota(self):
        e = next(s for s in self.estacoes if s["name"] == "Vidal Ramos")
        self.assertEqual(veredito(e, self.dump)[0], "mostrar")
        self.assertEqual(cotas_da(e), {})

    def test_a_cota_de_rio_do_sul_da_api_bate_com_a_nossa(self):
        """
        A confirmação que dá crédito ao resto: as faixas de Dom Tito Buss aqui
        são as mesmas que já estão em `estacoes.json`, vindas por outro caminho.
        """
        import comum
        e = next(s for s in self.estacoes if s["name"] == REGUA_DE_RIO_DO_SUL)
        da_api = cotas_da(e)
        nosso = {}
        for rio in comum.le_json("estacoes.json")["rios"].values():
            for c in rio["cidades"]:
                if c["id"] == "rio-do-sul":
                    nosso = c.get("cotas_m") or {}
        # A API chama a terceira faixa de "emergencia" e nós de "inundacao" —
        # nome diferente, mesmo número. É a comparação dos VALORES que importa.
        self.assertEqual(
            tuple(da_api[f] for f in ("atencao", "alerta", "emergencia")),
            tuple(nosso[f] for f in ("atencao", "alerta", "inundacao")))
        self.assertEqual(tuple(da_api[f] for f in ("atencao", "alerta", "emergencia")),
                         COTAS_DE_RIO_DO_SUL)

    def test_nenhuma_barragem_entra_como_aviso(self):
        nomes = {b["name"] for b in self.dump["dams"]}
        for e in self.estacoes:
            if e["name"] in nomes:
                self.assertNotEqual(veredito(e, self.dump)[0], "aviso", e["name"])

    def test_toda_estacao_recebe_um_veredito_conhecido(self):
        for e in self.estacoes:
            decisao, porque = veredito(e, self.dump)
            with self.subTest(estacao=e["name"]):
                self.assertIn(decisao, ("aviso", "mostrar", "fora"))
                self.assertTrue(porque, "decisão sem motivo escrito não serve")

    def test_o_bruto_esta_no_repositorio(self):
        self.assertTrue((Path(__file__).resolve().parent.parent / "data" / BRUTO).exists())


if __name__ == "__main__":
    unittest.main(verbosity=2)
