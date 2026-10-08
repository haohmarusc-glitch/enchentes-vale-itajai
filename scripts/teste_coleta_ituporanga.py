#!/usr/bin/env python3
"""Testes do coletor da régua do Centro de Ituporanga (Boletim Diário da Prefeitura).

O que pode enganar, e por isso tem teste:
* a vírgula é decimal ("2,04 m"); lida como ponto de milhar viraria 204 m;
* o horário é hora local sem fuso — é o contrato do `medido_em`, e converter daria 3 h de erro;
* a mesma página traz o nível da BARRAGEM (montante ~20 m): nunca pode virar nível da cidade;
* a criticidade da fonte é texto DA FONTE, nunca faixa deste site;
* página sem leitura legível falha alto e apaga o arquivo anterior.

    python3 scripts/teste_coleta_ituporanga.py
"""

import json
import tempfile
import unittest
from datetime import datetime
from pathlib import Path

import coleta_ituporanga as c

#: O cabeçalho REAL da página em 08/10/2026 07:00 (recorte do HTML salvo), mais a tabela da barragem.
PAGINA = """
<h1>Acompanhe o nível do Rio Itajaí do Sul e Barragem Sul</h1>
<div class="conselho-meta-info" title="Rio Itajaí do Sul"><i class="fa"></i>
    Última leitura: 08/10/2026 07:00                </div>
<div class="conselho-meta-info" title="Categoria"><i class="fa"></i>
    Nível do Rio (Centro): 2,04 m                </div>
<div class="conselho-meta-info" title="Status de Criticidade"><i class="fa"></i>
    Nível de Criticidade:
        <span style="color: #fd7e14; font-weight: bold;">
            Alerta                        </span>
</div>
<h2>Barragem Sul</h2>
<table><tr><th>Início da Operação</th><td>Março de 1976</td></tr></table>
<h3>Histórico de Leituras</h3>
<table>
<tr><th>Data / Hora</th><th>Montante (m)</th><th>Jusante (m)</th><th>Comp. Aberta(s)</th><th>Comp. Fechada(s)</th>
<th>Canal Extravasor</th><th>Lâmina Canal Extravasor</th><th>Lâmina Vertedouro</th></tr>
<tr><td>08/10/2026 07:00</td><td>19,23</td><td>4,21</td><td>5</td><td>0</td><td>Aberto</td><td>0</td><td>0</td></tr>
<tr><td>07/10/2026 17:00</td><td>20,94</td><td>4,35</td><td>5</td><td>0</td><td>Aberto</td><td>0</td><td>0</td></tr>
</table>
"""

AGORA = datetime(2026, 10, 8, 9, 46)  # Brasília, sem fuso


class OCabecalho(unittest.TestCase):
    def test_nivel_do_centro_com_virgula_decimal(self):
        d = c.extrair(PAGINA)
        self.assertEqual(d["nivel_m"], 2.04)

    def test_horario_e_brasilia_sem_fuso(self):
        d = c.extrair(PAGINA)
        self.assertEqual(d["medido_em"], "2026-10-08T07:00:00")
        self.assertNotIn("+", d["medido_em"])
        self.assertNotIn("Z", d["medido_em"])

    def test_criticidade_e_texto_da_fonte(self):
        d = c.extrair(PAGINA)
        self.assertEqual(d["criticidade_na_fonte"], "Alerta")
        # Nenhuma faixa deste projeto sai daqui.
        self.assertNotIn("faixa", d)

    def test_pagina_sem_leitura_falha_alto(self):
        with self.assertRaises(ValueError):
            c.extrair("<html><body>Nível do Rio</body></html>")

    def test_nivel_implausivel_falha_alto(self):
        with self.assertRaises(ValueError):
            c.extrair(PAGINA.replace("2,04 m", "204 m"))


class ABarragemNaoEACidade(unittest.TestCase):
    def test_montante_e_jusante_ficam_em_campos_proprios(self):
        d = c.extrair(PAGINA)
        b = d["barragem_sul"]
        self.assertEqual(b["montante_m"], 19.23)
        self.assertEqual(b["jusante_m"], 4.21)
        self.assertEqual(b["comportas_abertas"], 5)
        self.assertEqual(b["canal_extravasor"], "Aberto")
        self.assertEqual(b["medido_em"], "2026-10-08T07:00:00")
        # O nível da cidade continua sendo o do Centro, não o do reservatório.
        self.assertEqual(d["nivel_m"], 2.04)

    def test_sem_tabela_a_leitura_do_centro_continua(self):
        so_cabecalho = PAGINA.split("<h2>Barragem Sul</h2>")[0]
        d = c.extrair(so_cabecalho)
        self.assertEqual(d["nivel_m"], 2.04)
        self.assertIsNone(d["barragem_sul"])


class OArquivoPublicado(unittest.TestCase):
    def test_resumo_diz_que_a_regua_nao_e_identificada_e_nao_tem_cor(self):
        s = c.resumo_publicavel(c.extrair(PAGINA), AGORA, "2026-10-08T12:46:00+00:00")
        self.assertEqual(s["versao"], 1)
        self.assertEqual(s["unidade"], "m")
        self.assertEqual(s["cidade"], "ituporanga")
        self.assertFalse(s["regua"]["identificada"])
        self.assertIn("Sem cor", s["regua"]["nota"])
        self.assertEqual(s["ultima_leitura"]["nivel_m"], 2.04)
        self.assertEqual(s["ultima_leitura"]["criticidade_na_fonte"], "Alerta")
        self.assertEqual(s["situacao"], "fresca")
        self.assertEqual(s["idade_min_na_coleta"], 166)

    def test_leitura_com_mais_de_18h_e_antiga(self):
        s = c.resumo_publicavel(c.extrair(PAGINA), datetime(2026, 10, 9, 2, 0), "x")
        self.assertEqual(s["situacao"], "antiga")

    def test_publicar_grava_e_a_falha_apaga_o_anterior(self):
        with tempfile.TemporaryDirectory() as tmp:
            raiz = Path(tmp)
            self.assertEqual(c.publicar(AGORA, buscador=lambda: PAGINA, raiz=raiz), 0)
            arquivo = raiz / c.ARQUIVO_PUBLICAVEL
            d = json.loads(arquivo.read_text(encoding="utf-8"))
            self.assertEqual(d["ultima_leitura"]["nivel_m"], 2.04)
            self.assertTrue(d["gerado_em"].endswith("+00:00"), "gerado_em é UTC com fuso")

            def cai():
                raise RuntimeError("fora do ar")
            # Sem a página e sem o publicado pelo Actions (teste_ituporanga_actions.py cobre esse caminho).
            self.assertEqual(c.publicar(AGORA, buscador=cai, raiz=raiz, publicado=lambda: None), 1)
            self.assertFalse(arquivo.exists(), "falha não pode deixar leitura velha passando por atual")


if __name__ == "__main__":
    unittest.main()
