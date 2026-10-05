#!/usr/bin/env python3
"""
Testes da cópia semanal das séries para fora da VPS (scripts/copiar_series.sh, 05/10/2026).

Roda o script de verdade num repositório de mentira com um remoto local (bare): a cópia tem de
acumular (cada uma é filha da anterior), não reenviar o que não mudou, levar os arquivos que o
`main` ignora e nunca empurrar com --force.
"""
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
SCRIPT = RAIZ / "scripts" / "copiar_series.sh"
ENV = {**os.environ, "GIT_CONFIG_NOSYSTEM": "1", "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t",
       "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@t"}


def git(*args, cwd):
    return subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True, text=True, env=ENV).stdout.strip()


@unittest.skipIf(os.name == "nt", "Script POSIX: verificado na CI Linux, não no shell Windows")
class CopiaDasSeries(unittest.TestCase):
    def setUp(self):
        base = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, base, ignore_errors=True)
        self.remoto = base / "remoto.git"
        git("init", "-q", "--bare", str(self.remoto), cwd=base)
        self.vps = base / "vps"
        (self.vps / "scripts").mkdir(parents=True)
        shutil.copy2(SCRIPT, self.vps / "scripts" / SCRIPT.name)
        tr = self.vps / "data" / "tempo-real"
        tr.mkdir(parents=True)
        (tr / "2026-10.ndjson").write_text('{"estacao":"X","nivel_m":1.0,"medido_em":"2026-10-05T10:00:00"}\n', encoding="utf-8")
        (tr / "2026-09.ndjson.gz").write_bytes(b"\x1f\x8b fechado")
        (tr / "ultimo.json").write_text("{}", encoding="utf-8")  # não é série: não vai
        reg = self.vps / "data" / "eventos-registro" / "cheia-x" / "objetos"
        reg.mkdir(parents=True)
        (reg / "abc.json.gz").write_bytes(b"obj")
        (self.vps / ".gitignore").write_text("data/tempo-real/\ndata/eventos-registro/\n", encoding="utf-8")
        git("init", "-q", cwd=self.vps)
        git("add", ".gitignore", "scripts", cwd=self.vps)
        git("commit", "-q", "-m", "main", cwd=self.vps)
        git("remote", "add", "origin", str(self.remoto), cwd=self.vps)

    def roda(self, *args):
        return subprocess.run(["bash", "scripts/copiar_series.sh", *args], cwd=self.vps, capture_output=True, text=True, env=ENV)

    def arquivos(self, ref="arquivo-series"):
        return set(git("ls-tree", "-r", "--name-only", ref, cwd=self.remoto).splitlines())

    def test_copia_acumula_e_nao_repete(self):
        r = self.roda()
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(self.arquivos(), {"tempo-real/2026-10.ndjson", "tempo-real/2026-09.ndjson.gz",
                                           "eventos-registro/cheia-x/objetos/abc.json.gz"})
        primeiro = git("rev-parse", "arquivo-series", cwd=self.remoto)

        r = self.roda()
        self.assertIn("nada mudou", r.stdout)
        self.assertEqual(git("rev-parse", "arquivo-series", cwd=self.remoto), primeiro)

        with open(self.vps / "data" / "tempo-real" / "2026-10.ndjson", "a", encoding="utf-8") as f:
            f.write('{"estacao":"X","nivel_m":1.2,"medido_em":"2026-10-05T10:15:00"}\n')
        r = self.roda()
        self.assertEqual(r.returncode, 0, r.stderr)
        segundo = git("rev-parse", "arquivo-series", cwd=self.remoto)
        self.assertEqual(git("rev-parse", "arquivo-series^", cwd=self.remoto), primeiro)  # filha da anterior
        self.assertIn("10:15", git("show", f"{segundo}:tempo-real/2026-10.ndjson", cwd=self.remoto))
        # O `main` e o índice de quem está na VPS não foram tocados.
        self.assertEqual(git("status", "--porcelain", cwd=self.vps), "")

    def test_mes_apagado_na_vps_continua_na_copia_anterior(self):
        self.roda()
        (self.vps / "data" / "tempo-real" / "2026-09.ndjson.gz").unlink()
        self.roda()
        self.assertNotIn("tempo-real/2026-09.ndjson.gz", self.arquivos())
        self.assertIn("tempo-real/2026-09.ndjson.gz", self.arquivos("arquivo-series^"))

    def test_nao_forca_por_cima_de_historico_alheio(self):
        self.roda()
        # Alguém pôs no branch um commit que a VPS não conhece; a próxima cópia é filha dele, sem --force.
        outro = self.remoto.parent / "outro"
        git("clone", "-q", "-b", "arquivo-series", str(self.remoto), str(outro), cwd=self.remoto.parent)
        (outro / "LEIAME.md").write_text("nota", encoding="utf-8")
        git("add", "LEIAME.md", cwd=outro)
        git("commit", "-q", "-m", "nota", cwd=outro)
        git("push", "-q", "origin", "arquivo-series", cwd=outro)
        nota = git("rev-parse", "arquivo-series", cwd=self.remoto)
        with open(self.vps / "data" / "tempo-real" / "2026-10.ndjson", "a", encoding="utf-8") as f:
            f.write("{}\n")
        self.assertEqual(self.roda().returncode, 0)
        self.assertEqual(git("rev-parse", "arquivo-series^", cwd=self.remoto), nota)
        self.assertNotIn("--force", SCRIPT.read_text(encoding="utf-8").split("set -euo pipefail", 1)[1].replace("Sem --force", ""))

    def test_seco_nao_envia_e_sem_series_falha(self):
        r = self.roda("--seco")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("tempo-real/2026-10.ndjson", r.stdout)
        self.assertIn("+ 1 objetos", r.stdout)
        self.assertNotIn("arquivo-series", git("for-each-ref", "--format=%(refname)", cwd=self.remoto))
        for p in (self.vps / "data" / "tempo-real").glob("*.ndjson*"):
            p.unlink()
        r = self.roda()
        self.assertEqual(r.returncode, 1)
        self.assertIn("nenhuma série", r.stderr)


if __name__ == "__main__":
    unittest.main()
