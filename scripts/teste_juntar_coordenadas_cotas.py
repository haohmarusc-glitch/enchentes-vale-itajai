#!/usr/bin/env python3
"""Testes do juntador de coordenadas às cotas de rua.

Uma coordenada errada aqui pinta a RUA ERRADA no mapa de uma cidade que alaga.
Errar para um lado deixa o morador achando que a rua dele está seca; para o
outro, faz a rua seca parecer alagada até ele desistir do site. Por isso o que
os testes cobram não é "juntou", é "juntou o par certo, e recusou o incerto".

Cada guarda é SABOTADA num teste próprio: guarda que não falha quando quebrada
é decoração.

    python3 scripts/teste_juntar_coordenadas_cotas.py
"""

import json
import unittest

import juntar_coordenadas_cotas as j
from juntar_coordenadas_cotas import (
    JUNCOES,
    PROIBIDOS,
    chave,
    duas_casas,
    juntar,
    norma,
    parear_por_chave,
    parear_por_ordem,
)


def linha(rua, cota, cidade="gaspar", fonte="Defesa Civil de Gaspar — My Maps"):
    return {"cidade": cidade, "rua": rua, "cota_m": cota, "fonte": fonte}


def ponto(rua, cota, lat, lon):
    return {"rua": rua, "cota_rotulo": cota, "lat": lat, "lon": lon}


class ONomeDaRuaEComparadoComTolerancia(unittest.TestCase):
    def test_acento_caixa_e_espaco_duplo_nao_separam_a_mesma_rua(self):
        self.assertEqual(norma("Rua  São  José"), norma("RUA SAO JOSE"))

    def test_virgula_e_ponto_sao_a_mesma_cota(self):
        self.assertEqual(duas_casas("8,25"), duas_casas(8.25))

    def test_cota_ilegivel_vira_None_e_nao_zero(self):
        # Zero seria uma cota plausível e catastrófica: rua que alaga sempre.
        self.assertIsNone(duas_casas("sem número"))
        self.assertIsNone(duas_casas(None))


class PareamentoPorOrdem(unittest.TestCase):
    """Gaspar: a ordem foi preservada, e é ela que resolve as ruas repetidas."""

    def test_ruas_repetidas_recebem_coordenadas_na_ordem(self):
        linhas = [linha("Rua A", 5.0), linha("Rua A", 5.0)]
        pontos = [ponto("Rua A", "5,00", -26.90, -49.00),
                  ponto("Rua A", "5,00", -26.91, -49.01)]
        pares = parear_por_ordem(linhas, pontos, "cota_rotulo")
        self.assertEqual(pares[0]["lat"], -26.90)
        self.assertEqual(pares[1]["lat"], -26.91)

    def test_ponto_descartado_na_consolidacao_nao_desloca_o_resto(self):
        # O bruto tem um ponto a mais no meio. Sem alinhamento, todas as linhas
        # depois dele receberiam a coordenada da seguinte — o erro que move a
        # cidade inteira uma rua para o lado.
        linhas = [linha("Rua A", 5.0), linha("Rua C", 7.0)]
        pontos = [ponto("Rua A", "5,00", -26.90, -49.00),
                  ponto("Rua B", "6,00", -26.95, -49.05),
                  ponto("Rua C", "7,00", -26.99, -49.09)]
        pares = parear_por_ordem(linhas, pontos, "cota_rotulo")
        self.assertEqual(pares[0]["rua"], "Rua A")
        self.assertEqual(pares[1]["rua"], "Rua C")

    def test_linha_sem_ponto_correspondente_fica_de_fora(self):
        linhas = [linha("Rua A", 5.0), linha("Rua Z", 9.0)]
        pontos = [ponto("Rua A", "5,00", -26.90, -49.00)]
        pares = parear_por_ordem(linhas, pontos, "cota_rotulo")
        self.assertIn(0, pares)
        self.assertNotIn(1, pares)


class PareamentoPorChave(unittest.TestCase):
    """Brusque: a ordem se perdeu; chave repetida no bruto é 'não sei'."""

    def test_chave_unica_casa(self):
        pares = parear_por_chave([linha("Rua A", 5.0)],
                                 [ponto("Rua A", "5,00", -27.10, -48.90)], "cota_rotulo")
        self.assertEqual(pares[0]["lat"], -27.10)

    def test_chave_repetida_no_bruto_NAO_casa(self):
        # Dois pontos reais para uma linha só. Escolher um seria inventar
        # posição — é o caso "General Osório 7,87", dois pontos a 330 m.
        pares = parear_por_chave([linha("General Osório", 7.87)],
                                 [ponto("General Osório", "7,87", -27.0977, -48.9371),
                                  ponto("General Osório", "7,87", -27.0989, -48.9403)],
                                 "cota_rotulo")
        self.assertEqual(pares, {}, "escolheu um ponto entre dois — isso é inventar posição")

    def test_ordem_embaralhada_nao_atrapalha(self):
        linhas = [linha("Rua B", 6.0), linha("Rua A", 5.0)]
        pontos = [ponto("Rua A", "5,00", -27.10, -48.90),
                  ponto("Rua B", "6,00", -27.11, -48.91)]
        pares = parear_por_chave(linhas, pontos, "cota_rotulo")
        self.assertEqual(pares[0]["rua"], "Rua B")
        self.assertEqual(pares[1]["rua"], "Rua A")


class OBrutoProibido(unittest.TestCase):
    def test_o_mymaps_de_brusque_e_recusado_pelo_nome(self):
        # Tem coordenada e é o arquivo maior (3.688 pontos) — a tentação é usá-lo.
        # O `_meta` dele diz que a `cota` não é nível de régua.
        self.assertIn("brusque-mymaps-cotas.json", PROIBIDOS)
        with self.assertRaises(ValueError) as e:
            j.carregar_bruto("brusque-mymaps-cotas.json", "cota")
        self.assertIn("nível de régua", str(e.exception))

    def test_nenhuma_juncao_usa_bruto_proibido(self):
        for _, _, bruto, _, _ in JUNCOES:
            self.assertNotIn(bruto, PROIBIDOS)

    def test_o_arquivo_proibido_realmente_diz_isso_no_proprio_meta(self):
        # O motivo tem que vir da fonte, não da minha lembrança dela.
        meta = json.loads((j.BRUTOS / "brusque-mymaps-cotas.json").read_text(encoding="utf-8"))["_meta"]
        self.assertIn("NÃO IMPORTADO", meta["aviso"])


class AGuardaDeTrocaDeLinha(unittest.TestCase):
    def test_coordenada_na_nuvem_da_outra_cidade_aborta(self):
        # Sabotagem: uma linha de Gaspar já trazendo coordenada de Brusque. As
        # duas nuvens são disjuntas por ~10 km, então isso só acontece por troca.
        cotas = json.loads(j.COTAS.read_text(encoding="utf-8"))["cotas"]
        plantada = dict(cotas[0])
        plantada.update({"cidade": "gaspar", "rua": "PLANTADA",
                         "fonte": "outra fonte qualquer", "cota_m": 5.0,
                         "lat": -27.10, "lon": -48.90})   # isto é Brusque
        with self.assertRaises(ValueError) as e:
            juntar(cotas + [plantada])
        self.assertIn("troca de linha", str(e.exception))


class SobreODadoDeVerdade(unittest.TestCase):
    """Roda sobre o `cotas-ruas.json` real — é ele que vai para a tela."""

    @classmethod
    def setUpClass(cls):
        cls.doc = json.loads(j.COTAS.read_text(encoding="utf-8"))
        cls.novas, cls.relatos = juntar(cls.doc["cotas"])

    def test_nenhuma_coordenada_do_bruto_e_usada_duas_vezes(self):
        for cidade in ("gaspar", "brusque"):
            usados = [(x["lat"], x["lon"]) for x in self.novas
                      if x["cidade"] == cidade and x.get("lat") is not None]
            self.assertEqual(len(usados), len(set(usados)),
                             f"{cidade}: um ponto do bruto foi para duas linhas")

    def test_toda_linha_com_coordenada_bate_com_a_chave_no_bruto(self):
        for cidade, _, bruto, campo, _ in JUNCOES:
            pontos = j.carregar_bruto(bruto, campo)
            certos = {}
            for p in pontos:
                certos.setdefault(chave(p.get("rua"), p.get(campo)), set()).add(
                    (round(p["lat"], 6), round(p["lon"], 6)))
            for x in self.novas:
                if x["cidade"] == cidade and x.get("lat") is not None:
                    k = chave(x.get("rua"), x.get("cota_m"))
                    self.assertIn((x["lat"], x["lon"]), certos.get(k, set()),
                                  f"{cidade}: {x['rua']} recebeu coordenada de outra chave")

    def test_nenhuma_linha_perdeu_cota_ou_rua_na_juncao(self):
        self.assertEqual(len(self.novas), len(self.doc["cotas"]))
        for antes, depois in zip(self.doc["cotas"], self.novas):
            self.assertEqual(antes.get("cota_m"), depois.get("cota_m"))
            self.assertEqual(antes.get("rua"), depois.get("rua"))
            self.assertEqual(antes.get("cidade"), depois.get("cidade"))

    def test_blumenau_e_rio_do_sul_seguem_SEM_coordenada(self):
        # Não há bruto georreferenciado para elas. Uma coordenada aqui só
        # poderia ter vindo de geocodificação por nome, que ainda não foi feita
        # nem revisada — e rua homônima manda o morador para o bairro errado.
        for cidade in ("blumenau", "rio-do-sul"):
            com = [x for x in self.novas if x["cidade"] == cidade and x.get("lat") is not None]
            self.assertEqual(com, [], f"{cidade} ganhou coordenada sem geocodificação revisada")

    def test_a_juncao_e_idempotente(self):
        outra, _ = juntar(self.novas)
        self.assertEqual(outra, self.novas)

    def test_quantidade_casada_nao_regride(self):
        # Números medidos em 04/09/2026. Se um deles cair, alguma coisa no
        # consolidado ou no bruto mudou e o pareamento precisa ser reconferido
        # antes de a tela usar as coordenadas.
        por_cidade = {r["cidade"]: r["com_coordenada"] for r in self.relatos}
        self.assertEqual(por_cidade["gaspar"], 1613)
        self.assertEqual(por_cidade["brusque"], 348)


if __name__ == "__main__":
    unittest.main()
