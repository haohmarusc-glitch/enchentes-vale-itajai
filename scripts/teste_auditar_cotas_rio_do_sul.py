#!/usr/bin/env python3
"""
Testes da auditoria das cotas de rua de Rio do Sul (04/10/2026).

A auditoria só serve se for reproduzível e se não esconder linha: estes testes
travam o parser do pacote (que não pode devolver lista parcial em silêncio,
como o importador fez com a Visconde de Cairu), a amostra com semente fixa e o
resultado contra os arquivos reais guardados no repositório.
"""

import hashlib
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import auditar_cotas_rio_do_sul as aud
from comum import DADOS


def _js(*itens: str, extra: str = "") -> str:
    return "x=1;const oo=[" + ",".join(itens) + "];" + extra


class TestExtrairTabela(unittest.TestCase):
    def test_le_minima_nula_e_teto_aberto(self):
        js = _js("{name:`A`,min:8.12,max:9.65}",
                 "{name:`B`,min:null,max:19.01}",
                 "{name:`C`,min:10.95,max:20,maxOpen:!0}")
        itens = aud.extrair_tabela(js)
        self.assertEqual([i["rua"] for i in itens], ["A", "B", "C"])
        self.assertIsNone(itens[1]["min"])
        self.assertEqual(itens[1]["max"], 19.01)
        self.assertTrue(itens[2]["max_aberto"])
        self.assertFalse(itens[0]["max_aberto"])

    def test_formato_desconhecido_para_em_vez_de_perder_linha(self):
        js = _js("{name:`A`,min:8.12,max:9.65}",
                 "{name:`B`,min:8,max:9,bairro:`Centro`}")
        with self.assertRaises(ValueError):
            aud.extrair_tabela(js)

    def test_sem_tabela_ou_com_duas(self):
        with self.assertRaises(ValueError):
            aud.extrair_tabela("nada aqui")
        dupla = _js("{name:`A`,min:1,max:2}") + _js("{name:`B`,min:1,max:2}")
        with self.assertRaises(ValueError):
            aud.extrair_tabela(dupla)


class TestReferencia(unittest.TestCase):
    def test_frase_da_regua_e_lida_como_esta(self):
        js = "children:[`Cotas em metros na régua da Ponte Dom Tito Buss. Total: `,oo.length]"
        self.assertEqual(aud.declaracao_de_regua(js),
                         "Cotas em metros na régua da Ponte Dom Tito Buss. Total:")
        self.assertIsNone(aud.declaracao_de_regua("Cotas em metros."))

    def test_correcao_de_zero_com_numero_de_javascript(self):
        js = 'zo=Object.freeze({"d2f60af1-53e3-497f-81d6-c6498d28f5a2":-.17});'
        self.assertEqual(aud.correcoes_de_zero(js),
                         {"d2f60af1-53e3-497f-81d6-c6498d28f5a2": -0.17})
        self.assertEqual(aud.correcoes_de_zero("sem tabela"), {})


class TestConferirRegistro(unittest.TestCase):
    PISO = 4.5

    def _reg(self, **campos):
        base = {"rua": "X", "cota_m": 8.0, "referencia": "régua"}
        base.update(campos)
        return base

    def test_linha_comum_confere(self):
        item = {"rua": "X", "min": 8.0, "max": 9.5, "max_aberto": False}
        self.assertEqual(aud.conferir_registro(self._reg(cota_max_m=9.5), item, self.PISO), [])

    def test_teto_nao_vira_cota_maxima_e_exige_nota(self):
        item = {"rua": "X", "min": 8.0, "max": 20.0, "max_aberto": True}
        com_nota = self._reg(nota="A fonte publica máxima 20,00 m, que é o teto da escala dela")
        self.assertEqual(aud.conferir_registro(com_nota, item, self.PISO), [])
        self.assertTrue(aud.conferir_registro(self._reg(), item, self.PISO))
        self.assertTrue(aud.conferir_registro(self._reg(cota_max_m=20.0, nota="teto da escala"),
                                              item, self.PISO))

    def test_abaixo_do_piso_exige_bloqueio_de_aviso(self):
        item = {"rua": "X", "min": 3.11, "max": 7.48, "max_aberto": False}
        livre = self._reg(cota_m=3.11, cota_max_m=7.48)
        bloqueado = self._reg(cota_m=3.11, cota_max_m=7.48, usar_para_aviso=False)
        self.assertTrue(aud.conferir_registro(livre, item, self.PISO))
        self.assertEqual(aud.conferir_registro(bloqueado, item, self.PISO), [])

    def test_minima_diferente_ao_centavo_diverge(self):
        item = {"rua": "X", "min": 8.01, "max": 9.5, "max_aberto": False}
        self.assertTrue(aud.conferir_registro(self._reg(cota_max_m=9.5), item, self.PISO))

    def test_minima_nula_no_bruto_nao_casa_com_numero(self):
        item = {"rua": "X", "min": None, "max": 19.01, "max_aberto": False}
        self.assertTrue(aud.conferir_registro(self._reg(cota_m=19.01), item, self.PISO))

    def test_referencia_tem_que_ser_regua_e_rua_tem_que_existir(self):
        item = {"rua": "X", "min": 8.0, "max": 9.5, "max_aberto": False}
        self.assertTrue(aud.conferir_registro(self._reg(cota_max_m=9.5, referencia=None),
                                              item, self.PISO))
        self.assertEqual(aud.conferir_registro(self._reg(), None, self.PISO),
                         ["rua ausente no bruto"])


class TestAmostra(unittest.TestCase):
    def test_semente_fixa_e_ordem_de_entrada_nao_importa(self):
        regs = [{"rua": f"RUA {i:03d}"} for i in range(100)]
        a = aud.sortear(regs, semente=7, n=10)
        b = aud.sortear(list(reversed(regs)), semente=7, n=10)
        self.assertEqual([r["rua"] for r in a], [r["rua"] for r in b])
        self.assertNotEqual([r["rua"] for r in a],
                            [r["rua"] for r in aud.sortear(regs, semente=8, n=10)])

    def test_duplicata_por_acento_e_caixa(self):
        self.assertEqual(aud.duplicatas(["Jurací Dalfovo", "JURACI DALFOVO", "Outra"]),
                         ["JURACI DALFOVO"])


def _sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


class TestArquivosReais(unittest.TestCase):
    """Contra os arquivos do repositório. Se um destes cair, refaça o relatório."""

    @classmethod
    def setUpClass(cls):
        cls.antes = {p: _sha(p) for p in (aud.COTAS, aud.ESTACOES)}
        cls.rel = aud.auditar()

    def test_nao_grava_nada(self):
        for p, h in self.antes.items():
            self.assertEqual(_sha(p), h, f"{p} mudou durante a auditoria")

    def test_bruto_confere_com_o_manifesto(self):
        self.assertNotIn("erro", self.rel)
        self.assertEqual(self.rel["fonte"]["sha256"], self.rel["fonte"]["sha256_manifesto"])

    def test_fonte_declara_a_regua_e_corrige_a_estadual(self):
        ref = self.rel["referencia"]
        self.assertIn("régua da Ponte Dom Tito Buss", ref["declaracao_no_pacote"])
        corr = ref["correcoes_de_zero_no_pacote"]
        self.assertEqual(list(corr), ["d2f60af1-53e3-497f-81d6-c6498d28f5a2"])
        self.assertAlmostEqual(corr["d2f60af1-53e3-497f-81d6-c6498d28f5a2"]["deslocamento_m"], -0.17)
        self.assertEqual(corr["d2f60af1-53e3-497f-81d6-c6498d28f5a2"]["estacao"], "SDC-SC Rio do Sul")

    def test_censo_555_contra_555(self):
        c = self.rel["censo"]
        self.assertEqual((c["cadastro"], c["bruto"]), (555, 555))
        self.assertEqual(c["so_no_cadastro"], [])
        self.assertEqual(c["so_no_bruto"], [])
        self.assertEqual(c["duplicatas_cadastro"], [])
        self.assertEqual(c["duplicatas_bruto"], [])
        self.assertEqual(c["teto_no_bruto"], 216)
        self.assertEqual((c["com_bairro"], c["com_coordenada"]), (0, 0))

    def test_a_unica_divergencia_e_a_visconde_de_cairu(self):
        # A NSC publicou 19,01 como MÍNIMA; o pacote oficial traz min:null e
        # max:19,01. Se este teste cair porque a linha foi corrigida, ótimo:
        # atualize o teste e o relatório.
        div = self.rel["censo"]["divergentes"]
        self.assertEqual([d["rua"] for d in div], ["VISCONDE DE CAIRU"])

    def test_implausiveis_sao_os_ja_conhecidos(self):
        nomes = sorted(t.split(":")[0] for t in self.rel["censo"]["implausiveis"])
        self.assertEqual(nomes, ["POUSO REDONDO", "SD 1604", "VISCONDE DE CAIRU"])

    def test_amostra_de_30_confere_inteira(self):
        linhas = self.rel["amostra"]["linhas"]
        self.assertEqual(len(linhas), 30)
        self.assertEqual(self.rel["amostra"]["semente"], 20261004)
        self.assertEqual([l["resultado"] for l in linhas], ["confere"] * 30)
        # As três primeiras do sorteio, para o relatório não descolar do script.
        self.assertEqual([l["rua"] for l in linhas[:3]],
                         ["FERNANDINO JAHN", "ANTONIO JOSE POLEZA", "LUIZ STEDILE"])


if __name__ == "__main__":
    unittest.main()
