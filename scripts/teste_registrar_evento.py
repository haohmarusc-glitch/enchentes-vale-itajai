import gzip
import json
import tempfile
import unittest
from pathlib import Path

from registrar_evento import registrar


class RegistroEvento(unittest.TestCase):
    def test_preserva_original_deduplica_e_registra_falhas(self):
        with tempfile.TemporaryDirectory() as temp:
            raiz = Path(temp)
            entrada = raiz / "entrada"
            entrada.mkdir()
            bruto = b'{"coletado_em":"2026-09-12T01:00:00Z","chuva_168h_mm":131.12}'
            (entrada / "ultimo.json").write_bytes(bruto)
            (entrada / "ultimo_nivel_sc.json").write_text("{", encoding="utf-8")
            for _ in range(2):
                r = registrar(entrada, raiz / "arquivo", "teste")
            pasta = raiz / "arquivo/teste"
            objetos = list((pasta / "objetos").glob("*.gz"))
            self.assertEqual(len(objetos), 1)
            self.assertEqual(gzip.decompress(objetos[0].read_bytes()), bruto)
            self.assertIn("ultimo_nivel_sc.json", r["problemas"])
            self.assertIn("ultimo_barragens.json", r["problemas"])
            self.assertEqual(len((pasta / "capturas.ndjson").read_text().splitlines()), 2)
            (entrada / "ultimo.json").write_text(json.dumps({"nivel": 7}), encoding="utf-8")
            registrar(entrada, raiz / "arquivo", "teste")
            self.assertEqual(len(list((pasta / "objetos").glob("*.gz"))), 2)

    def test_recusa_caminho_fora_do_evento(self):
        with self.assertRaises(ValueError):
            registrar(Path("."), Path("."), "../fora")


if __name__ == "__main__":
    unittest.main()
