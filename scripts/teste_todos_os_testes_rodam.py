#!/usr/bin/env python3
"""
Trava que TODO teste escrito seja um teste que roda.

O CI executa cada arquivo direto (`python3 teste_x.py`), não por descoberta.
Quando `unittest.main()` fica no MEIO do arquivo, ele roda no import do
`__main__` — ou seja, antes de as classes definidas abaixo dele existirem. O
arquivo passa, verde, testando menos do que tem.

Foi o que aconteceu em 04/09/2026: dois arquivos ganharam classes anexadas
DEPOIS do bloco `if __name__`, e 27 testes deixaram de rodar no CI sem que nada
ficasse vermelho — entre eles os seis da coerência da chuva de Gaspar e os
vinte e um do validador. Descoberto por acaso, ao comparar a contagem de
execução direta com a da descoberta.

O comentário do próprio ci.yml já dizia a regra: "um teste que não roda na CI é
um teste que não existe no dia em que alguém apontar um importador para o
arquivo errado". Este arquivo passa a fazer valer.
"""
import re
import subprocess
import sys
import unittest
from pathlib import Path

AQUI = Path(__file__).resolve().parent
RE_MAIN = re.compile(r'^if __name__ == ["\']__main__["\']:', re.M)
RE_RAN = re.compile(r"Ran (\d+) tests?")


def arquivos_de_teste() -> list[Path]:
    """Os mesmos que o CI roda, menos este — que se testaria em laço."""
    return sorted(p for p in AQUI.glob("teste_*.py") if p.name != Path(__file__).name)


class TodoTesteRoda(unittest.TestCase):
    def test_o_bloco_main_fica_no_fim_do_arquivo(self):
        """
        Barato e direto: se houver classe definida DEPOIS do `if __name__`,
        ela não roda na execução direta.
        """
        problemas = []
        for p in arquivos_de_teste():
            texto = p.read_text(encoding="utf-8")
            m = list(RE_MAIN.finditer(texto))
            if not m:
                continue
            if len(m) > 1:
                problemas.append(f"{p.name}: {len(m)} blocos `if __name__` — só o primeiro conta")
                continue
            depois = texto[m[0].end():]
            if re.search(r"^(class|def) ", depois, re.M):
                problemas.append(
                    f"{p.name}: há classe ou função definida DEPOIS do bloco `if __name__`. "
                    "Ela não roda quando o CI executa o arquivo direto. Mova o bloco para o fim."
                )
        self.assertEqual(problemas, [], "\n".join(problemas))

    def test_execucao_direta_roda_tantos_testes_quanto_a_descoberta(self):
        """
        A prova de verdade: conta os testes das duas formas e exige o mesmo
        número. Pega qualquer jeito de esconder teste, não só o do `__main__`.
        """
        divergentes = []
        for p in arquivos_de_teste():
            direto = _quantos([sys.executable, p.name])
            descoberto = _quantos([sys.executable, "-m", "unittest", p.stem])
            if direto is None or descoberto is None:
                continue  # arquivo que não reporta contagem; não é o alvo daqui
            if direto != descoberto:
                divergentes.append(
                    f"{p.name}: execução direta roda {direto} teste(s), descoberta roda "
                    f"{descoberto}. {descoberto - direto} teste(s) não rodam no CI."
                )
        self.assertEqual(divergentes, [], "\n".join(divergentes))


def _quantos(comando: list[str]) -> int | None:
    r = subprocess.run(comando, cwd=AQUI, capture_output=True, text=True)
    m = RE_RAN.search(r.stderr + r.stdout)
    return int(m.group(1)) if m else None


if __name__ == "__main__":
    unittest.main()
