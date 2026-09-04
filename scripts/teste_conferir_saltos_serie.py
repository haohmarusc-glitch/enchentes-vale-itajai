#!/usr/bin/env python3
"""Testes do conferidor de saltos da série publicada.

Este script é a guarda contra as réguas voltarem a ser misturadas. Se ele ficar
cego, o defeito volta em silêncio — e foi exatamente o que aconteceu com a
primeira versão dele, que passava verde no arquivo com salto de 13.320 cm/h.

    python3 scripts/teste_conferir_saltos_serie.py
"""

import json
import tempfile
import unittest
from pathlib import Path

import conferir_saltos_serie as csz
from conferir_saltos_serie import LIMITE_CM_H, conferir, por_regua, saltos

DC01 = "DC-01 Rio Itajaí-Açu - ICMBio/CEPSUL"
DC11 = "DC-11 Rio Itajaí-Açú – Santa Regina (Volta de Cima)"


def ponto(hhmm: str, nivel: float, r: int | None = None) -> dict:
    p = {"medido_em": f"2026-09-04T{hhmm}:00", "nivel_m": nivel}
    if r is not None:
        p["r"] = r
    return p


class Saltos(unittest.TestCase):
    def test_conta_a_taxa_em_cm_por_hora(self):
        # 1,00 m em 30 min = 200 cm/h.
        s = saltos([ponto("12:00", 1.0), ponto("12:30", 2.0)], 150)
        self.assertEqual(len(s), 1)
        self.assertEqual(s[0]["cm_h"], 200)

    def test_abaixo_do_limite_nao_e_salto(self):
        self.assertEqual(saltos([ponto("12:00", 1.0), ponto("13:00", 2.0)], 150), [])

    def test_descida_conta_igual_a_subida(self):
        # O defeito real aparecia como QUEDA: 3,00 -> 0,78 m em um minuto. Um
        # rio que parece cair 2 m em um minuto lê como "a cheia passou".
        s = saltos([ponto("12:00", 3.0), ponto("12:01", 0.78), ], 150)
        self.assertEqual(s[0]["cm_h"], 13320)

    def test_tempo_parado_ou_para_tras_nao_vira_divisao_por_zero(self):
        self.assertEqual(saltos([ponto("12:00", 1.0), ponto("12:00", 9.0)], 150), [])
        self.assertEqual(saltos([ponto("12:30", 1.0), ponto("12:00", 9.0)], 150), [])


class SerieSemReguaNaoPodeFicarCEGA(unittest.TestCase):
    """
    O caso que a primeira versão deste script deixava passar.

    Ela pulava todo grupo sem título (`if not titulo: continue`), e uma série
    SEM régua nenhuma cai inteira nesse grupo. Resultado: rodada contra o
    arquivo publicado em 04/09 às 15:16 — o que tinha 13.320 cm/h em Itajaí —
    ela dizia "nenhum salto acima do limite". A falsificação flagrou.
    """

    def doc_sem_regua(self):
        return {"series": {"itajai-acu": {"itajai": [
            ponto("12:00", 3.00), ponto("12:01", 0.78), ponto("12:10", 3.04),
        ]}}}

    def test_pega_o_salto_mesmo_sem_legenda_de_regua(self):
        p = conferir(self.doc_sem_regua())
        self.assertEqual(len(p), 1)
        self.assertIsNone(p[0]["regua"])
        self.assertIn("SEM RÉGUA", p[0]["motivo"])
        self.assertEqual(p[0]["saltos"][0]["cm_h"], 13320)

    def test_serie_sem_regua_e_SEM_salto_passa(self):
        # Cidade de uma régua só, publicada por um coletor antigo: não há o que
        # acusar. Alarme falso aqui ensinaria a ignorar o alarme verdadeiro.
        doc = {"series": {"itajai-acu": {"rio-do-sul": [
            ponto("12:00", 5.30), ponto("13:00", 5.35), ponto("14:00", 5.33),
        ]}}}
        self.assertEqual(conferir(doc), [])


class ComReguaSeparadaOProblemaSome(unittest.TestCase):
    """
    A prova de que a correção é a SEPARAÇÃO, não o limite.

    Os mesmos níveis, com o `r` de cada régua no lugar, deixam de acusar nada —
    porque cada régua, sozinha, é uma série mansa. Medido no dado real: a maior
    taxa da bacia inteira cai de 13.320 para 96 cm/h.
    """

    def doc(self, com_r: bool):
        pts = []
        for i, hhmm in enumerate(("12:00", "12:01", "12:10", "12:11")):
            regua, nivel = (0, 3.00) if i % 2 == 0 else (1, 0.78)
            pts.append(ponto(hhmm, nivel, regua if com_r else None))
        return {
            "reguas": {"itajai-acu": {"itajai": [DC11, DC01]}},
            "series": {"itajai-acu": {"itajai": pts}},
        }

    def test_sem_r_acusa(self):
        self.assertTrue(conferir(self.doc(com_r=False)))

    def test_com_r_nao_acusa(self):
        self.assertEqual(conferir(self.doc(com_r=True)), [])


class ReguaDeEstuarioGanhaFolgaEXPLICITA(unittest.TestCase):
    def test_a_folga_vem_do_cadastro_nao_de_omissao(self):
        # DC-01 é de estuário (`alerta_automatico: false` no cadastro) e chega a
        # 96 cm/h só com a maré. DC-11 não é.
        self.assertTrue(csz.eh_estuario(DC01))
        self.assertFalse(csz.eh_estuario(DC11))
        self.assertGreater(csz.LIMITE_ESTUARIO_CM_H, LIMITE_CM_H)

    def test_titulo_desconhecido_NAO_ganha_folga(self):
        # Régua que não está no cadastro é tratada como rio. Dar folga a quem
        # não se sabe o que é seria pular a conferência por omissão.
        self.assertFalse(csz.eh_estuario("Régua que não existe"))


class PorRegua(unittest.TestCase):
    def test_r_fora_da_legenda_vira_desconhecida_nao_a_primeira(self):
        doc = {
            "reguas": {"itajai-acu": {"itajai": [DC11]}},
            "series": {"itajai-acu": {"itajai": [ponto("12:00", 1.0, 7)]}},
        }
        self.assertEqual(list(por_regua(doc, "itajai-acu", "itajai")), [""])

    def test_ordena_no_tempo_dentro_de_cada_regua(self):
        doc = {
            "reguas": {"itajai-acu": {"itajai": [DC11]}},
            "series": {"itajai-acu": {"itajai": [
                ponto("13:00", 2.0, 0), ponto("12:00", 1.0, 0),
            ]}},
        }
        g = por_regua(doc, "itajai-acu", "itajai")[DC11]
        self.assertEqual([p["nivel_m"] for p in g], [1.0, 2.0])


class Cli(unittest.TestCase):
    def test_arquivo_que_nao_existe_sai_com_erro_e_nao_estoura(self):
        with tempfile.TemporaryDirectory() as tmp:
            import sys
            argv = sys.argv
            sys.argv = ["x", "--arquivo", str(Path(tmp) / "nao-existe.json")]
            try:
                self.assertEqual(csz.main(), 1)
            finally:
                sys.argv = argv

    def test_arquivo_limpo_sai_zero(self):
        with tempfile.TemporaryDirectory() as tmp:
            alvo = Path(tmp) / "serie.json"
            alvo.write_text(json.dumps({"series": {"itajai-acu": {"rio-do-sul": [
                ponto("12:00", 5.30), ponto("13:00", 5.35),
            ]}}}), encoding="utf-8")
            import sys
            argv = sys.argv
            sys.argv = ["x", "--arquivo", str(alvo)]
            try:
                self.assertEqual(csz.main(), 0)
            finally:
                sys.argv = argv


if __name__ == "__main__":
    unittest.main()
