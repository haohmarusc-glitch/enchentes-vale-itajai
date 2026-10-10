#!/usr/bin/env python3
"""Testes da coleta das réguas do Itajaí do Sul e do Oeste em Rio do Sul (10/10/2026).

O que não pode falhar: estação fora da lista fechada (barragem, altitude, outro rio) entrar como régua; o carimbo UTC
virar hora local sem converter; a série repetir leitura; e falha deixar um arquivo velho passando por atual.
"""

import json
import sys
import tempfile
import unittest
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import coleta_riodosul_rios as C  # noqa: E402

KANITZ = {"station_id": "30475400-b7ba-4551-9646-19df0c3bfa38", "name": "Ponte Ricardo Kanitz",
          "river_name": "Rio Itajaí do Sul", "level_m": 5.004501992031871, "last_reading_at": "2026-10-10T10:27:58.975748Z",
          "band_thresholds": [{"band_key": "atencao", "cota_m": 4.5, "origin": "authored"},
                              {"band_key": "alerta", "cota_m": 5.5, "origin": "authored"},
                              {"band_key": "emergencia", "cota_m": 6.5, "origin": "authored"}]}
BR470 = {"station_id": "3167e629-3bbe-48f2-9244-c65dfe6882d8", "name": "Ponte BR 470",
         "river_name": "Rio Itajaí do Oeste", "level_m": 4.3882872340425525, "last_reading_at": "2026-10-10T10:28:53.788456Z"}
BARRAGEM = {"station_id": "d6e340c8-c1d6-441d-8fd0-4381ff17cb54", "name": "Barragem Oeste Taió",
            "river_name": "Rio Itajaí do Oeste", "level_m": 4.05, "last_reading_at": "2026-10-10T10:28:12.463Z"}
ALTITUDE = {"station_id": "caca79cc-d21b-4333-bea8-0128a4fd3117", "name": "Petrolândia",
            "level_m": 417.84, "last_reading_at": "2026-10-10T10:28:23.011Z"}
AGORA = datetime(2026, 10, 10, 7, 31)  # Brasília


class TesteExtrair(unittest.TestCase):
    def test_so_a_lista_fechada_com_o_rio_conferido_e_hora_de_brasilia(self):
        reguas, recusas = C.extrair({"stations": [KANITZ, BR470, BARRAGEM, ALTITUDE]})
        self.assertEqual([r["nome"] for r in reguas], ["Ponte Ricardo Kanitz", "Ponte BR 470"])
        k = reguas[0]
        self.assertEqual((k["medido_em"], k["nivel_m"], k["ramo"]), ("2026-10-10T07:27:58", 5.0, "itajai_do_sul"))
        self.assertEqual(k["cotas_na_fonte"]["atencao"], {"cota_m": 4.5, "origem": "authored"})
        self.assertEqual(reguas[1]["ramo"], "itajai_do_oeste")
        self.assertTrue(any("Hannelore" in f and "ausente" in f for f in recusas))

    def test_rio_trocado_na_fonte_nao_substitui(self):
        trocada = {**BR470, "river_name": "Rio Itajaí do Sul"}
        reguas, recusas = C.extrair({"stations": [trocada]})
        self.assertEqual(reguas, [])
        self.assertTrue(any("não substituir" in f for f in recusas))

    def test_nivel_implausivel_ou_sem_hora_fica_fora(self):
        reguas, _ = C.extrair({"stations": [{**KANITZ, "level_m": 0.0}, {**BR470, "last_reading_at": None}]})
        self.assertEqual(reguas, [])


class TestePublicar(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.raiz = Path(self.tmp.name)

    def test_grava_o_arquivo_proprio_e_a_serie_sem_repetir(self):
        painel = {"stations": [KANITZ, BR470]}
        self.assertEqual(C.publicar(AGORA, buscador=lambda: painel, raiz=self.raiz), 0)
        d = json.loads((self.raiz / C.ARQUIVO_PUBLICAVEL).read_text(encoding="utf-8"))
        self.assertEqual(d["versao"], 1)
        self.assertEqual([r["situacao"] for r in d["reguas"]], ["fresca", "fresca"])
        self.assertIn("não pinta o mapa", d["aviso"])
        serie = self.raiz / C.SERIE.format(mes="2026-10")
        self.assertEqual(len(serie.read_text(encoding="utf-8").splitlines()), 2)
        C.publicar(AGORA, buscador=lambda: painel, raiz=self.raiz)
        self.assertEqual(len(serie.read_text(encoding="utf-8").splitlines()), 2, "a mesma leitura não se repete")

    def test_falha_apaga_o_arquivo_anterior(self):
        C.publicar(AGORA, buscador=lambda: {"stations": [KANITZ]}, raiz=self.raiz)
        self.assertTrue((self.raiz / C.ARQUIVO_PUBLICAVEL).exists())

        def quebra():
            raise RuntimeError("HTTP 503")

        self.assertEqual(C.publicar(AGORA, buscador=quebra, raiz=self.raiz), 1)
        self.assertFalse((self.raiz / C.ARQUIVO_PUBLICAVEL).exists())

    def test_leitura_velha_sai_como_antiga(self):
        velha = {**KANITZ, "last_reading_at": "2026-10-10T06:00:00Z"}  # 03:00 em Brasília
        C.publicar(AGORA, buscador=lambda: {"stations": [velha]}, raiz=self.raiz)
        d = json.loads((self.raiz / C.ARQUIVO_PUBLICAVEL).read_text(encoding="utf-8"))
        self.assertEqual(d["reguas"][0]["situacao"], "antiga")


class TesteForaDoSite(unittest.TestCase):
    def test_o_site_e_o_aviso_nao_leem_este_arquivo(self):
        """Arquivo próprio: nenhuma tela, aviso ou classificação o lê (mostrar é outra decisão)."""
        raiz = Path(__file__).resolve().parent.parent
        arquivos = [*(raiz / "web" / "src").rglob("*.ts"), *(raiz / "web" / "src").rglob("*.tsx"),
                    raiz / "scripts" / "alerta_cotas.py", raiz / "scripts" / "classificar_reguas.py"]
        leitores = [str(f.relative_to(raiz)) for f in arquivos
                    if "rio_do_sul_rios" in f.read_text(encoding="utf-8", errors="replace")]
        self.assertEqual(leitores, [])


if __name__ == "__main__":
    unittest.main()
