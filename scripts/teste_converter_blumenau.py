#!/usr/bin/env python3
"""
Testes da proposta de conversão de Blumenau para a régua de hoje.

O erro que mais importa aqui é somar o deslocamento errado sem avisar: 0,20 m
num registro que já estava na régua nova faz a cheia parecer 20 cm maior do que
foi, e isso vira "faltam X m" errado na tela. Por isso os testes travam sobretudo
o que NÃO pode ser convertido em silêncio: a janela da troca de régua, a fonte
sem régua declarada e o trecho em que a Tabela 4 e a planilha da FURB discordam.
"""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import validar_dados as vd
from converter_blumenau import ROTULO_IBGE, SOMA, aplicar, classificar, converter_registro, proposta


def ev(data, pico, **extra):
    return {"cidade": "blumenau", "rio": "itajai-acu", "data": data, "pico_m": pico,
            "fonte": "teste", "confianca": "alta", **extra}


class TesteClassificar(unittest.TestCase):
    def test_deslocamentos_sao_os_da_furb(self):
        # IBGE = régua antiga + 0,20; régua de hoje (GPS) = régua antiga + 0,40.
        self.assertEqual(SOMA, {"IBGE": 0.20, "régua antiga": 0.40, "régua de hoje": 0.0})

    def test_rotulo_ibge_soma_020(self):
        c = classificar(ev("1983-07-09", 15.34, referencia=ROTULO_IBGE), {})
        self.assertEqual((c["referencia_publicada"], c["certeza"]), ("IBGE", "alta"))

    def test_lista_ate_2001_e_ibge(self):
        c = classificar(ev("1999-07-03", 8.26, referencia=None), {"1999-07-03": 8.26})
        self.assertEqual(c["referencia_publicada"], "IBGE")

    def test_lista_2008_2011_e_regua_antiga(self):
        c = classificar(ev("2008-11-24", 11.52, referencia=None), {"2008-11-24": 11.52})
        self.assertEqual((c["referencia_publicada"], c["certeza"]), ("régua antiga", "alta"))

    def test_setembro_2011_1280_e_ibge(self):
        # 12,60 régua antiga · 12,80 IBGE · 13,00 GPS — a mesma cheia, pela FURB.
        c = classificar(ev("2011-09-09", 12.80, referencia=None), {"2011-09-09": 12.60})
        self.assertEqual(c["referencia_publicada"], "IBGE")

    def test_janela_da_troca_fica_pendente(self):
        for data in ("2012-05-01", "2013", "2013-09-23"):
            c = classificar(ev(data, 10.51, referencia=None), {data: 10.51})
            self.assertIsNone(c["referencia_publicada"], data)
            self.assertEqual(c["certeza"], "pendente", data)

    def test_depois_de_2014_com_par_na_lista_e_regua_de_hoje(self):
        c = classificar(ev("2023-10-12", 10.76, referencia=None), {"2023-10-12": 10.76})
        self.assertEqual((c["referencia_publicada"], c["certeza"]), ("régua de hoje", "alta"))

    def test_depois_de_2014_sem_regua_declarada_fica_pendente(self):
        c = classificar(ev("2026-07-12", 5.65, referencia=None), {})
        self.assertEqual(c["certeza"], "pendente")

    def test_regua_antes_de_2014_nao_converte_sozinha(self):
        c = classificar(ev("2010-01-01", 8.0, referencia="régua"), {})
        self.assertEqual(c["certeza"], "pendente")


class TesteProposta(unittest.TestCase):
    def test_soma_e_arredonda(self):
        [l] = proposta([ev("1983-07-09", 15.34, referencia=ROTULO_IBGE)], {})
        self.assertEqual(l["novo"], 15.54)

    def test_trecho_em_disputa_so_e_alto_quando_a_planilha_confirma(self):
        linhas = proposta(
            [ev("1980-12-22", 13.27, referencia=ROTULO_IBGE), ev("1983-07-09", 15.34, referencia=ROTULO_IBGE)],
            {}, {"1980-12-22": 13.22, "1983-07-09": 15.54})
        por_data = {l["data"]: l["certeza"] for l in linhas}
        self.assertEqual(por_data, {"1980-12-22": "disputada", "1983-07-09": "alta"})

    def test_outra_cidade_fica_de_fora(self):
        self.assertEqual(proposta([{**ev("2011-09-09", 12.0), "cidade": "gaspar"}], {}), [])

    def test_nao_grava_no_json(self):
        # A simulação só escreve o relatório: o arquivo de dados não pode mudar.
        import converter_blumenau as cb
        antes = (cb.DADOS / "enchentes.json").read_bytes()
        cb.proposta(__import__("json").loads(antes)["eventos"], cb.lista_alertablu(), cb.planilha_gps())
        self.assertEqual((cb.DADOS / "enchentes.json").read_bytes(), antes)


def erros_de_conversao(eventos):
    vd.erros.clear()
    vd.valida_conversoes(eventos)
    return list(vd.erros)


class TesteAplicar(unittest.TestCase):
    def test_registro_convertido_guarda_o_publicado(self):
        e = converter_registro(ev("1983-07-09", 15.34, referencia=ROTULO_IBGE), "IBGE")
        self.assertEqual((e["pico_m"], e["pico_publicado_m"], e["referencia"]), (15.54, 15.34, "régua"))
        self.assertEqual(e["referencia_publicada"], ROTULO_IBGE)
        self.assertIn("+ 0,20 m", e["conversao"])

    def test_regua_antiga_soma_040(self):
        e = converter_registro(ev("2008-11-24", 11.52, referencia=None), "régua antiga")
        self.assertEqual(e["pico_m"], 11.92)

    def test_divergencia_igual_ao_convertido_vira_confirmacao(self):
        # set/2011: 13,00 m do CEOPS já era GPS; depois da conversão não diverge mais.
        e = converter_registro(ev("2011-09-09", 12.80, referencia=None, divergencias=[
            {"pico_m": 13.0, "fonte": "CEOPS"}, {"pico_m": 12.6, "fonte": "Defesa Civil"}]), "IBGE")
        self.assertEqual([d["pico_m"] for d in e["divergencias"]], [12.6])
        self.assertEqual(e["divergencias"][0]["referencia_publicada"], "régua antiga")
        self.assertIn("Confere com 13,00 m", e["conversao"])

    def test_validador_aceita_o_convertido_e_pega_a_mao(self):
        e = converter_registro(ev("1983-07-09", 15.34, referencia=ROTULO_IBGE), "IBGE")
        self.assertEqual(erros_de_conversao([e]), [])
        self.assertTrue(erros_de_conversao([{**e, "pico_m": 15.74}]), "soma errada passou")
        self.assertTrue(erros_de_conversao([{**e, "referencia": ROTULO_IBGE}]), "rótulo velho passou")
        self.assertTrue(erros_de_conversao([{**e, "conversao": ""}]), "sem justificativa passou")

    def test_aplicar_duas_vezes_nao_soma_duas_vezes(self):
        dados = {"eventos": [ev("1983-07-09", 15.34, referencia=ROTULO_IBGE)]}
        self.assertEqual(aplicar(dados, {}, {"1983-07-09": 15.54}), 1)
        self.assertEqual(aplicar(dados, {}, {"1983-07-09": 15.54}), 0)
        self.assertEqual(dados["eventos"][0]["pico_m"], 15.54)

    def test_disputado_nao_e_aplicado(self):
        dados = {"eventos": [ev("1980-12-22", 13.27, referencia=ROTULO_IBGE)]}
        self.assertEqual(aplicar(dados, {}, {"1980-12-22": 13.22}), 0)
        self.assertEqual(dados["eventos"][0]["pico_m"], 13.27)

    def test_dado_real_tem_57_convertidos_e_passa_no_validador(self):
        import json
        from converter_blumenau import DADOS
        eventos = json.loads((DADOS / "enchentes.json").read_text(encoding="utf-8"))["eventos"]
        convertidos = [e for e in eventos if "referencia_publicada" in e]
        self.assertEqual(len(convertidos), 57)
        self.assertTrue(all(e["cidade"] == "blumenau" for e in convertidos))
        self.assertEqual(erros_de_conversao(eventos), [])


if __name__ == "__main__":
    unittest.main()
