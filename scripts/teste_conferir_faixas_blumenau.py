#!/usr/bin/env python3
"""Testes da sonda das faixas de Blumenau.

O que não pode falhar: a série horária (milhares de pontos) não pode inundar a
saída e esconder o campo que interessa, e uma faixa publicada sob um nome que
não adivinhamos ainda precisa aparecer na varredura.

    python3 scripts/teste_conferir_faixas_blumenau.py
"""

import unittest

from conferir_faixas_blumenau import candidatas_a_faixa, sem_serie

EXEMPLO = {
    "atualizado": "2026-09-09T02:00:00Z",
    "niveis": [{"horaLeitura": f"2026-09-0{d}T00:00:00Z", "nivel": 2.1} for d in range(1, 9)],
    "condicoes": [
        {"nome": "Normalidade", "de": 0, "ate": 3, "cor": "#0a0"},
        {"nome": "Observação", "de": 3, "ate": 4, "cor": "#ff0"},
    ],
    "cotaAlertaMaximo": "8,00 m",
    "titulo": "Nível do Rio",
}


class SemSerie(unittest.TestCase):
    def test_serie_vira_contagem_e_ultima(self):
        fora = sem_serie(EXEMPLO)
        self.assertEqual(fora["niveis"]["quantos"], 8)
        self.assertEqual(fora["niveis"]["ultima"]["nivel"], 2.1)
        self.assertIn("condicoes", fora)

    def test_raiz_que_nao_e_dict_nao_quebra(self):
        self.assertEqual(sem_serie([1, 2]), {"_raiz": [1, 2]})


class Candidatas(unittest.TestCase):
    def test_acha_faixas_por_nome_de_chave_sem_ler_a_serie(self):
        achados = dict(candidatas_a_faixa(EXEMPLO))
        self.assertEqual(achados["condicoes[0].de"], 0)
        self.assertEqual(achados["condicoes[1].ate"], 4)
        self.assertEqual(achados["cotaAlertaMaximo"], "8,00 m")
        self.assertFalse(any(c.startswith("niveis") for c in achados))

    def test_texto_sem_numero_e_booleano_ficam_de_fora(self):
        achados = dict(candidatas_a_faixa({"condicao": "Normalidade", "alertaAtivo": True}))
        self.assertEqual(achados, {})


if __name__ == "__main__":
    unittest.main()
