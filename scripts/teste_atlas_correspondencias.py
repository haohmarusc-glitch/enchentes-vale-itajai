#!/usr/bin/env python3
"""Testes do cruzamento picos × ocorrências oficiais do Atlas."""
from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import atlas_correspondencias as ac  # noqa: E402

FONTE = (Path(__file__).resolve().parent / "atlas_correspondencias.py").read_text(encoding="utf-8")
NOMES = {"rio do sul": "rio-do-sul", "itajai": "itajai", "blumenau": "blumenau"}


def ocorrencia(municipio, data, cobrade="12100", protocolo=None, **danos):
    r = {"protocolo": protocolo or f"SC-{municipio[:3]}-{data}", "cod_ibge": "0000000",
         "municipio": municipio, "data_evento": data, "cobrade": cobrade,
         "tipo": "Inundações", "status": "Reconhecido",
         "mortos": 0, "desabrigados": 0, "desalojados": 0}
    r.update(danos)
    return r


class NaoEscreveNoProjeto(unittest.TestCase):
    """Decreto não é pico. A camada é à parte, e o código não pode nem citar
    os três JSONs em contexto de escrita."""

    def test_nao_toca_nos_jsons_do_projeto(self):
        for ln in FONTE.splitlines():
            despido = ln.strip()
            if despido.startswith("#") or despido.startswith('"""') or "grava_json" in despido:
                self.assertNotIn("grava_json", despido, "gravação nos JSONs do projeto")
        self.assertNotIn("grava_json(", FONTE)
        for ln in FONTE.splitlines():
            if "write_text" in ln and not ln.strip().startswith("#"):
                self.assertIn("destino", ln, f"escrita fora de data/desastres: {ln.strip()}")


class Classificacao(unittest.TestCase):
    def parear(self, pico_data, ocorrencias, cidade="rio-do-sul", municipio="Rio do Sul"):
        picos = [{"cidade": cidade, "data": pico_data, "pico_m": 10.0, "referencia": None}]
        regs = [ocorrencia(municipio, d) for d in ocorrencias]
        return ac.parear(picos, regs, NOMES)[0]

    def test_mesmo_dia_e_confirmado(self):
        l = self.parear("2023-11-18", ["2023-11-18"])
        self.assertEqual(l["classificacao"], "confirmado")
        self.assertEqual(l["diferenca_dias"], 0)

    def test_um_dia_antes_e_confirmado_e_a_diferenca_e_negativa(self):
        """O caso real: crista 18/11, decreto 16/11. Um dia ainda é confirmado;
        dois vira provável. E o sinal diz quem veio antes."""
        l = self.parear("2023-11-18", ["2023-11-17"])
        self.assertEqual(l["classificacao"], "confirmado")
        self.assertEqual(l["diferenca_dias"], -1)
        l = self.parear("2023-11-18", ["2023-11-16"])
        self.assertEqual(l["classificacao"], "provável")
        self.assertEqual(l["diferenca_dias"], -2)

    def test_cinco_dias_e_provavel_e_seis_nao(self):
        self.assertEqual(self.parear("2024-05-18", ["2024-05-23"])["classificacao"], "provável")
        self.assertEqual(self.parear("2024-05-18", ["2024-05-24"])["classificacao"],
                         "sem correspondência")

    def test_escolhe_a_ocorrencia_mais_proxima(self):
        l = self.parear("2024-07-12", ["2024-07-08", "2024-07-11", "2024-07-30"])
        self.assertEqual(l["data_atlas"], "2024-07-11")

    def test_pico_so_com_mes_casa_por_mes(self):
        """A série de Rio do Sul é quase toda mensal. Sem dia não há diferença
        em dias, e a classificação diz isso."""
        l = self.parear("1983-07", ["1983-07-09"])
        self.assertEqual(l["classificacao"], "provável (mês)")
        self.assertIsNone(l["diferenca_dias"])
        self.assertEqual(l["precisao_do_pico"], "mes")
        self.assertEqual(self.parear("1983-07", ["1983-08-01"])["classificacao"],
                         "sem correspondência")

    def test_pico_so_com_ano_nao_compara(self):
        l = self.parear("2013", ["2013-09-23"])
        self.assertEqual(l["classificacao"], "sem base")
        self.assertIsNone(l["data_atlas"])

    def test_cidade_sem_ocorrencia_nenhuma(self):
        l = self.parear("2011-09-09", [], cidade="blumenau", municipio="Blumenau")
        self.assertEqual(l["classificacao"], "sem correspondência")

    def test_a_ocorrencia_de_outra_cidade_nao_serve(self):
        picos = [{"cidade": "rio-do-sul", "data": "2011-09-09", "pico_m": 12.96, "referencia": None}]
        regs = [ocorrencia("Itajaí", "2011-09-09")]
        self.assertEqual(ac.parear(picos, regs, NOMES)[0]["classificacao"], "sem correspondência")

    def test_o_pico_nunca_e_alterado(self):
        picos = [{"cidade": "rio-do-sul", "data": "2023-11-18", "pico_m": 13.04, "referencia": None}]
        antes = json.dumps(picos)
        ac.parear(picos, [ocorrencia("Rio do Sul", "2023-11-16")], NOMES)
        self.assertEqual(json.dumps(picos), antes)

    def test_os_danos_vem_junto(self):
        picos = [{"cidade": "itajai", "data": "2011-09-09", "pico_m": 1.0, "referencia": "régua"}]
        regs = [ocorrencia("Itajaí", "2011-09-09", desabrigados=3215, desalojados=45630, mortos=1)]
        l = ac.parear(picos, regs, NOMES)[0]
        self.assertEqual((l["desabrigados"], l["desalojados"], l["mortos"]), (3215, 45630, 1))


class Entrada(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def test_le_a_lista_plana_do_nosso_script(self):
        p = self.dir / "eventos.json"
        p.write_text(json.dumps([ocorrencia("Itajaí", "2008-11-23"),
                                 ocorrencia("Itajaí", "2008-11-23", cobrade="13214")]), encoding="utf-8")
        regs = ac.carregar_registros(p)
        self.assertEqual(len(regs), 2)
        self.assertEqual({r["cobrade"] for r in regs}, {"12100", "13214"})

    def test_le_o_recorte_por_rio(self):
        p = self.dir / "recorte.json"
        p.write_text(json.dumps({"eventos": [{"registros": [
            {"protocolo": "X", "cod_ibge": 4208203, "municipio": "Itajaí",
             "data_evento": "2008-11-23", "cobrade": 12200, "tipologia": "Enxurradas",
             "status": "Registro", "mortos": 5, "desabrigados": 18208, "desalojados": 1929}]}]}),
            encoding="utf-8")
        regs = ac.carregar_registros(p)
        self.assertEqual(len(regs), 1)
        self.assertEqual(regs[0]["tipo"], "Enxurradas")
        self.assertEqual(regs[0]["cobrade"], "12200")

    def test_so_entram_os_quatro_cobrades_de_enchente(self):
        """Vendaval, granizo, estiagem: fora da camada de enchentes."""
        p = self.dir / "eventos.json"
        p.write_text(json.dumps([ocorrencia("Itajaí", "2020-01-01", cobrade="13215"),
                                 ocorrencia("Itajaí", "2020-01-02", cobrade="14110"),
                                 ocorrencia("Itajaí", "2020-01-03", cobrade="12300")]), encoding="utf-8")
        self.assertEqual([r["cobrade"] for r in ac.carregar_registros(p)], ["12300"])

    def test_cobrade_com_ponto_zero(self):
        p = self.dir / "eventos.json"
        p.write_text(json.dumps([ocorrencia("Itajaí", "2020-01-03", cobrade="12100.0")]), encoding="utf-8")
        self.assertEqual(ac.carregar_registros(p)[0]["cobrade"], "12100")


class Cadastro(unittest.TestCase):
    def test_nomes_do_cadastro_viram_ids(self):
        estacoes = json.loads((ac.RAIZ / "data" / "estacoes.json").read_text(encoding="utf-8"))
        nomes = ac.cidades_por_nome(estacoes)
        self.assertEqual(nomes["rio do sul"], "rio-do-sul")
        self.assertEqual(nomes["itajai"], "itajai")
        self.assertEqual(nomes["botuvera"], "botuvera")


if __name__ == "__main__":
    unittest.main(verbosity=2)
