#!/usr/bin/env python3
"""Testes da conferência entre dois resumos do histórico DCSC.

O que precisa ficar travado: a conferência tem que ACUSAR quando o dado muda e ficar
QUIETA quando só a data da execução muda. Um comparador que nunca acusa passa despercebido
justamente no dia em que um zip falta na cópia — que é o risco do B5.
"""

from __future__ import annotations

import json
import unittest
from copy import deepcopy

from conferir_resumo_dcsc import comparar

BASE = {
    "_meta": {"descricao": "x", "fuso": "Brasília", "gerado_em": "2026-09-10"},
    "estacoes": [
        {
            "codigo": "DCSC-00013",
            "cidade": "rio-do-sul",
            "leituras": 156471,
            "leituras_com_nivel": 156000,
            "sentinelas_rio_nivel": 12,
            "nivel_max_m": 7.07,
            "cristas_candidatas": [{"ts": "2026-09-01T05:20", "nivel_m": 7.07}],
        },
        {
            "codigo": "DCSC-00006",
            "cidade": "indaial",
            "leituras": 100,
            "leituras_com_nivel": 99,
            "sentinelas_rio_nivel": 0,
            "nivel_max_m": 6.39,
            "cristas_candidatas": [],
        },
    ],
}


def clone() -> dict:
    return deepcopy(BASE)


class TesteComparar(unittest.TestCase):
    def teste_identico_nao_acusa(self):
        self.assertEqual(comparar(clone(), clone()), [])

    def teste_so_a_data_da_execucao_mudou_nao_acusa(self):
        """`gerado_em` é carimbo da rodada, não do dado: rodar de novo muda e não é erro."""
        novo = clone()
        novo["_meta"]["gerado_em"] = "2026-09-15"
        self.assertEqual(comparar(novo, clone()), [])

    def teste_contagem_diferente_acusa_com_os_dois_valores(self):
        novo = clone()
        novo["estacoes"][0]["leituras"] = 156472
        (problema,) = comparar(novo, clone())
        self.assertIn("DCSC-00013.leituras", problema)
        self.assertIn("156472", problema)
        self.assertIn("156471", problema)

    def teste_estacao_faltando_acusa_e_sugere_zip(self):
        """O caso que o B5 mais teme: a cópia chegou incompleta e ninguém viu."""
        novo = clone()
        novo["estacoes"] = [novo["estacoes"][0]]
        (problema,) = comparar(novo, clone())
        self.assertIn("DCSC-00006", problema)
        self.assertIn("zip faltando", problema)

    def teste_estacao_a_mais_acusa(self):
        novo = clone()
        novo["estacoes"].append({"codigo": "DCSC-00099", "cidade": "nova"})
        (problema,) = comparar(novo, clone())
        self.assertIn("DCSC-00099", problema)
        self.assertIn("a mais", problema)

    def teste_crista_diferente_acusa_sem_despejar_a_lista(self):
        """Lista longa vira contagem na mensagem — mas ainda acusa."""
        novo = clone()
        novo["estacoes"][0]["cristas_candidatas"] = []
        (problema,) = comparar(novo, clone())
        self.assertIn("cristas_candidatas", problema)
        self.assertIn("0 item(ns)", problema)

    def teste_nivel_maximo_diferente_acusa(self):
        """Um centímetro a mais no pico é exatamente o tipo de erro que não pode passar."""
        novo = clone()
        novo["estacoes"][0]["nivel_max_m"] = 7.08
        (problema,) = comparar(novo, clone())
        self.assertIn("nivel_max_m", problema)

    def teste_meta_de_conteudo_diferente_acusa(self):
        """`fuso` e `descricao` descrevem como o dado foi lido: mudar é mudar o dado."""
        novo = clone()
        novo["_meta"]["fuso"] = "UTC"
        (problema,) = comparar(novo, clone())
        self.assertIn("_meta.fuso", problema)

    def teste_varias_divergencias_saem_todas(self):
        """Não para na primeira: quem confere quer a lista inteira de uma vez."""
        novo = clone()
        novo["estacoes"][0]["leituras"] = 1
        novo["estacoes"][1]["leituras"] = 2
        self.assertEqual(len(comparar(novo, clone())), 2)

    def teste_resumo_de_verdade_igual_a_si_mesmo(self):
        """Contra o arquivo real do repo, não só contra o exemplo deste teste."""
        from pathlib import Path

        raiz = Path(__file__).resolve().parent.parent
        reais = sorted((raiz / "data" / "brutos").glob("dcsc-historico-resumo-*.json"))
        if not reais:
            self.skipTest("nenhum resumo real em data/brutos/")
        d = json.loads(reais[-1].read_text())
        self.assertEqual(comparar(d, deepcopy(d)), [])
        self.assertEqual(len(d["estacoes"]), 13)


if __name__ == "__main__":
    unittest.main()
