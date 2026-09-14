#!/usr/bin/env python3
"""Testes da rede estadual que pode pintar (faixas municipais na escala da própria estação)."""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import coleta_estadual_com_cota as cec  # noqa: E402
from comum import cidades  # noqa: E402
from coleta_nivel_sc import converter  # noqa: E402
from teste_coleta_nivel_sc import estacao  # noqa: E402


class TesteMontar(unittest.TestCase):
    def brutas(self, *estacoes):
        leituras, _, _, _ = converter(list(estacoes), so_cadeia=False)
        return leituras

    def teste_ascurra_entra_no_formato_do_site_e_pode_pintar(self):
        saida = cec.montar(self.brutas(
            estacao(codigo="DCSC-00003", nome="SDC-SC Ascurra", nivel=10.46,
                    carimbo="2026-09-12T03:00:00+00:00")))
        self.assertEqual(len(saida), 1)
        l = saida[0]
        self.assertEqual((l["cidade"], l["rio"]), ("ascurra", "itajai-acu"))
        self.assertEqual(l["nivel_m"], 10.46)
        self.assertEqual(l["medido_em"], "2026-09-12T00:00:00", "hora de Brasília, sem fuso")
        self.assertTrue(l["usar_para_cota"])
        self.assertEqual(l["origem"], "estadual")
        self.assertIn("DCSC-00003", l["estacao"])
        self.assertIn("C18", l["fonte"])

    def teste_estacao_fora_da_lista_nao_entra(self):
        saida = cec.montar(self.brutas(
            estacao(codigo="DCSC-00006", nome="SDC-SC Indaial", nivel=6.39),
            estacao(codigo="DCSC-00030", nome="SDC-SC Ilhota", nivel=9.96)))
        self.assertEqual(saida, [], "sem prova escrita da COMPDEC, o bruto estadual não pinta")

    def teste_sem_numero_ou_sem_carimbo_nao_entra(self):
        self.assertEqual(cec.montar([{"codigo": "DCSC-00003", "nivel_bruto_m": None,
                                      "medido_em": "2026-09-12T00:00:00"}]), [])
        self.assertEqual(cec.montar([{"codigo": "DCSC-00003", "nivel_bruto_m": 8.1,
                                      "medido_em": None}]), [])


class TesteColetarNuncaDerruba(unittest.TestCase):
    def teste_rede_fora_devolve_lista_vazia(self):
        def explode():
            raise OSError("rede fora")
        self.assertEqual(cec.coletar(buscar=explode, converter=converter), [])

    def teste_com_rede_devolve_ascurra(self):
        saida = cec.coletar(
            buscar=lambda: [estacao(codigo="DCSC-00003", nome="SDC-SC Ascurra", nivel=8.35)],
            converter=converter)
        self.assertEqual([l["cidade"] for l in saida], ["ascurra"])


class TesteOParEstaTrancadoNoEstacoesJson(unittest.TestCase):
    """Cada estação da allowlist tem de casar com o cadastro: código, cotas e fonte escrita.

    É o "teste do par" do C6. Se alguém puser uma estação aqui sem a cidade ter
    `codigo_dcsc` igual, `cotas_m.atencao` e `regua_das_cotas_fonte`, a cidade
    pintaria pelo zero errado — e este teste quebra antes.
    """

    def teste_allowlist_casa_com_o_cadastro(self):
        por_id = {c["id"]: c for c in cidades()}
        for codigo, cfg in cec.REGUAS_COM_COTA_PROPRIA.items():
            with self.subTest(codigo=codigo):
                cid = por_id.get(cfg["cidade"])
                self.assertIsNotNone(cid, f"{cfg['cidade']} não está em estacoes.json")
                self.assertEqual(cid.get("codigo_dcsc"), codigo,
                                 "a cidade tem de apontar para ESTA estação")
                self.assertIn("atencao", cid.get("cotas_m") or {}, "sem cota de atenção não há o que pintar")
                self.assertTrue((cid.get("regua_das_cotas_fonte") or "").strip(),
                                "a prova escrita da COMPDEC tem de estar no cadastro")

    def teste_ascurra_esta_na_lista(self):
        self.assertIn("DCSC-00003", cec.REGUAS_COM_COTA_PROPRIA)


if __name__ == "__main__":
    unittest.main()
