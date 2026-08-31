#!/usr/bin/env python3
"""Testes das cotas de rua e das manchas de inundação.

Cota de rua é o dado mais direto que este projeto tem: não passa por modelo
nenhum, é leitura de tabela. Por isso o erro aqui é silencioso e caro — um
número errado não destoa de nada, só manda a pessoa para o lado errado.

Estes casos travam as invariantes que importam, contra os dados de verdade.

    python3 scripts/teste_cotas_ruas.py
"""

import json
import unittest
from pathlib import Path

from comum import DADOS, le_json

MANCHAS = DADOS / "manchas"


class TestCotasRuas(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.dados = le_json("cotas-ruas.json")
        cls.cotas = cls.dados["cotas"]
        estacoes = le_json("estacoes.json")
        cls.cidades = {}
        cls.rios = {}
        for rio_id, rio in estacoes["rios"].items():
            for c in rio["cidades"]:
                cls.cidades.setdefault(c["id"], {}).update(c.get("cotas_m") or {})
                cls.rios.setdefault(c["id"], set()).add(rio_id)

    def test_tem_dados(self):
        self.assertGreater(len(self.cotas), 20)

    def test_toda_cota_tem_fonte_e_confianca(self):
        """Regra do CLAUDE.md, e aqui ela vale duplo: é dado que vira decisão."""
        for r in self.cotas:
            with self.subTest(rua=r.get("rua")):
                self.assertTrue(r.get("fonte"), "sem fonte")
                self.assertIn(r.get("confianca"), ("alta", "media", "baixa"))
                self.assertTrue(r.get("data_fonte"), "sem data da fonte")

    def test_cidade_e_rio_existem(self):
        for r in self.cotas:
            with self.subTest(rua=r.get("rua")):
                self.assertIn(r["cidade"], self.rios)
                self.assertIn(r["rio"], self.rios[r["cidade"]])

    def test_cota_nula_explica_por_que(self):
        """
        Rua sem número é legítima — a fonte cita e não publica a cota. Mas sem
        nota vira buraco silencioso, e alguém depois preencheria com um chute.
        """
        for r in self.cotas:
            if r["cota_m"] is None:
                with self.subTest(rua=r["rua"]):
                    self.assertTrue(r.get("nota"), "cota nula sem explicação")

    def test_cotas_em_faixa_plausivel(self):
        for r in self.cotas:
            if r["cota_m"] is not None:
                with self.subTest(rua=r["rua"]):
                    self.assertGreater(r["cota_m"], 0)
                    self.assertLess(r["cota_m"], 25, "nenhuma régua da bacia chega perto disso")

    def test_o_aviso_nao_chega_depois_da_agua(self):
        """
        A invariante que motivou este arquivo.

        Se a cota mais baixa cadastrada para a cidade for maior que a cota da
        primeira rua, o Telegram toca depois que a água já entrou — e um aviso
        atrasado é pior que nenhum, porque dá a impressão de que havia tempo.
        Foi o caso de Brusque: aviso só em 6,00 m, primeira rua em 4,80 m.
        """
        primeira: dict[str, float] = {}
        for r in self.cotas:
            # Cota marcada para não mover aviso fica de fora, pelo mesmo
            # motivo do validador: exigir que a cidade baixe a cota de atenção
            # por causa de um número que ninguém conferiu faria o aviso tocar
            # em dia de sol. Rio do Sul publica duas assim, a 3,11 e 3,26 m,
            # com a régua marcando 3,35 m sem chuva.
            if r["cota_m"] is not None and r.get("usar_para_aviso") is not False:
                atual = primeira.get(r["cidade"])
                primeira[r["cidade"]] = r["cota_m"] if atual is None else min(atual, r["cota_m"])

        for cidade, rua in primeira.items():
            cadastradas = {
                k: v for k, v in (self.cidades.get(cidade) or {}).items()
                if isinstance(v, (int, float))
            }
            if not cadastradas:
                continue  # cidade sem cota nenhuma: o validador avisa à parte
            menor = min(cadastradas.values())
            with self.subTest(cidade=cidade):
                self.assertLessEqual(
                    menor, rua,
                    f"em {cidade} o aviso dispara a {menor:.2f} m, "
                    f"depois da primeira rua alagar a {rua:.2f} m",
                )

    def test_cota_fora_do_aviso_explica_e_e_mesmo_baixa(self):
        """
        A saída da regra acima não pode virar porta dos fundos: só entra aí a
        cota que fica abaixo da menor cota da cidade, e sempre com a nota
        dizendo por quê.
        """
        for r in self.cotas:
            if r.get("usar_para_aviso") is not False:
                continue
            with self.subTest(rua=r["rua"]):
                self.assertTrue(r.get("nota"), "sem nota explicando")
                cadastradas = [
                    v for v in (self.cidades.get(r["cidade"]) or {}).values()
                    if isinstance(v, (int, float))
                ]
                self.assertTrue(cadastradas, "cidade sem cota para comparar")
                self.assertLess(
                    r["cota_m"], min(cadastradas),
                    "está fora do aviso sem ser mais baixa que a cota da cidade",
                )

    def test_mesma_rua_pode_ter_varias_cotas(self):
        """
        Rua comprida tem mais de uma cota, e o registro é por PONTO. Se alguém
        deduplicar por nome de rua, perde a cota mais baixa — justamente a que
        importa.
        """
        chaves = [(r["cidade"], r["rua"], r.get("ponto")) for r in self.cotas]
        self.assertEqual(len(chaves), len(set(chaves)), "registro duplicado (cidade, rua, ponto)")
        nomes = [(r["cidade"], r["rua"]) for r in self.cotas]
        self.assertLess(len(set(nomes)), len(nomes), "esperava alguma rua com mais de um ponto")


    def test_cotas_de_rua_sao_sempre_em_regua(self):
        """
        Item 4 da REGRA BLOQUEANTE do CLAUDE.md.

        A busca "minha rua" e o simulador comparam a cota da rua com o nível ao
        vivo, que vem da Defesa Civil e é régua. Uma cota em referência IBGE
        produziria "faltam 2,30 m" com 20 cm de erro embutido e nada na tela
        denunciando. Hoje isto é verdade por construção; o teste faz com que
        continue sendo por decisão.
        """
        for r in self.cotas:
            with self.subTest(rua=r.get("rua")):
                self.assertIn(r.get("referencia", "régua"), ("régua",),
                              "cota de rua fora da referência régua")


class TestManchas(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.indice = json.loads((MANCHAS / "index.json").read_text(encoding="utf-8"))

    def test_todo_arquivo_do_indice_existe_e_e_geojson(self):
        for m in self.indice["manchas"]:
            with self.subTest(arquivo=m["arquivo"]):
                caminho = DADOS / m["arquivo"]
                self.assertTrue(caminho.exists(), "arquivo do índice não está no disco")
                d = json.loads(caminho.read_text(encoding="utf-8"))
                self.assertEqual(d.get("type"), "FeatureCollection")
                self.assertEqual(len(d["features"]), m["feicoes"])

    def test_coordenadas_em_wgs84(self):
        """
        Leaflet espera longitude/latitude em WGS84. Um arquivo em UTM entraria
        sem erro e desenharia a mancha no meio do oceano.
        """
        for m in self.indice["manchas"]:
            with self.subTest(arquivo=m["arquivo"]):
                self.assertIn("CRS84", (m.get("crs") or ""), "CRS não é WGS84")

    def test_credito_da_licenca_preservado(self):
        for m in self.indice["manchas"]:
            self.assertEqual(m["licenca"], "MIT")
            self.assertIn("geoitajai", m["fonte"].lower())

    def test_mancha_nao_promete_nivel_de_rio(self):
        """
        Os polígonos não trazem cota. A ligação com o pico é pela data e só
        aparece quando o pico existe em enchentes.json — inventá-la faria
        alguém concluir que a sua rua alaga a tal metro.
        """
        for m in self.indice["manchas"]:
            pico = m.get("pico_registrado")
            if pico is not None:
                self.assertIn("pico_m", pico)
        self.assertIn("não são previsão", self.indice["_meta"]["aviso"].lower()
                      .replace("não é previsão", "não são previsão"))


if __name__ == "__main__":
    unittest.main(verbosity=2)
