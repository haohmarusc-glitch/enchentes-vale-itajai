"""O script que grava a credencial da ANA não pode deixar a chave duplicada.

`comum.carrega_env` usa `os.environ.setdefault`: a PRIMEIRA ocorrência da chave
vence. O `.env.example` traz `ANA_SENHA=` vazio. Acrescentar a senha no fim
deixaria a linha vazia ganhando, e o `ana_hidroweb.py` diria "não estão no
ambiente" — erro que parece credencial errada e não é. Este teste roda o script
de verdade e confere o que o leitor ENTREGA, não o que o arquivo contém.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
SCRIPT = RAIZ / "scripts" / "configurar_ana.sh"


def _roda(env_inicial: str, identificador: str, senha: str) -> tuple[int, str, Path]:
    tmp = Path(tempfile.mkdtemp())
    (tmp / "scripts").mkdir()
    shutil.copy(RAIZ / "scripts" / "comum.py", tmp / "scripts" / "comum.py")
    shutil.copy(SCRIPT, tmp / "scripts" / "configurar_ana.sh")
    (tmp / "scripts" / "configurar_ana.sh").chmod(0o755)
    (tmp / ".env").write_text(env_inicial, encoding="utf-8")
    r = subprocess.run(
        [str(tmp / "scripts" / "configurar_ana.sh")],
        input=f"{identificador}\n{senha}\n",
        capture_output=True, text=True, cwd=tmp, timeout=60,
    )
    return r.returncode, r.stdout + r.stderr, tmp


def _entregue(pasta: Path, chave: str) -> str:
    """O que `carrega_env` põe no ambiente a partir daquele .env."""
    codigo = (
        "import os,sys;sys.path.insert(0,'scripts');"
        "from comum import carrega_env;from pathlib import Path;"
        f"carrega_env(Path('.env'));print(os.environ.get({chave!r},''))"
    )
    r = subprocess.run([sys.executable, "-c", codigo], capture_output=True,
                       text=True, cwd=pasta, timeout=30, env={**os.environ, "PATH": os.environ["PATH"]})
    return r.stdout.rstrip("\n")


class GravaSemDuplicar(unittest.TestCase):
    VAZIO = "TELEGRAM_BOT_TOKEN=abc\nANA_IDENTIFICADOR=\nANA_SENHA=\n"

    def test_a_linha_vazia_do_exemplo_e_substituida_nao_acompanhada(self):
        codigo, saida, pasta = _roda(self.VAZIO, "usuario@exemplo", "s3nh4#com$peso")
        try:
            self.assertEqual(codigo, 0, saida)
            self.assertEqual(_entregue(pasta, "ANA_SENHA"), "s3nh4#com$peso")
            texto = (pasta / ".env").read_text(encoding="utf-8")
            self.assertEqual(texto.count("ANA_SENHA="), 1, "ficou duplicada")
        finally:
            shutil.rmtree(pasta)

    def test_chave_ausente_e_acrescentada(self):
        codigo, saida, pasta = _roda("TELEGRAM_BOT_TOKEN=abc\n", "u", "p")
        try:
            self.assertEqual(codigo, 0, saida)
            self.assertEqual(_entregue(pasta, "ANA_IDENTIFICADOR"), "u")
        finally:
            shutil.rmtree(pasta)

    def test_duplicata_preexistente_some(self):
        """Se alguém já tinha acrescentado no fim, a linha morta é removida."""
        sujo = "ANA_SENHA=\nTELEGRAM_CHAT_ID=1\nANA_SENHA=tentativa_anterior\n"
        codigo, saida, pasta = _roda(sujo, "u", "certa")
        try:
            self.assertEqual(codigo, 0, saida)
            self.assertEqual((pasta / ".env").read_text(encoding="utf-8").count("ANA_SENHA="), 1)
            self.assertEqual(_entregue(pasta, "ANA_SENHA"), "certa")
        finally:
            shutil.rmtree(pasta)

    def test_senha_que_o_leitor_mutila_e_denunciada_na_hora(self):
        """
        O leitor faz `.strip().strip("'\\"")`. Uma senha entre aspas chegaria
        DIFERENTE ao ana_hidroweb.py e falharia como se estivesse errada. O
        script tem de acusar isso na gravação, não deixar para o --verificar.
        """
        codigo, saida, pasta = _roda(self.VAZIO, "u", '"senha_entre_aspas"')
        try:
            self.assertNotEqual(codigo, 0, "gravou uma senha que o leitor vai mutilar")
            self.assertIn("aspas", saida)
        finally:
            shutil.rmtree(pasta)

    def test_a_senha_nunca_aparece_na_saida(self):
        segredo = "senha_muito_secreta_1234"
        codigo, saida, pasta = _roda(self.VAZIO, "u", segredo)
        try:
            self.assertEqual(codigo, 0, saida)
            self.assertNotIn(segredo, saida, "a senha vazou para a tela")
            self.assertIn("24 caracteres", saida)
        finally:
            shutil.rmtree(pasta)

    def test_o_env_fica_com_permissao_600(self):
        codigo, saida, pasta = _roda(self.VAZIO, "u", "p")
        try:
            self.assertEqual(codigo, 0, saida)
            self.assertEqual(oct((pasta / ".env").stat().st_mode & 0o777), "0o600")
        finally:
            shutil.rmtree(pasta)


if __name__ == "__main__":
    unittest.main()
