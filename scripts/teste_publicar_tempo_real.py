#!/usr/bin/env python3
"""
Testes do publicador — o script que leva a leitura ao ar.

Por que estes testes existem, e por que `bash -n` não bastava: em 04/09/2026,
ao acrescentar o arquivo de Taió, a última linha do grupo que monta a árvore
virou um `[ -n "$X" ] && printf ...` com X vazio. Sintaxe perfeita. Só que o
grupo sai com 1, o `pipefail` propaga, e o script MORRE ANTES DE PUBLICAR —
calado, sem mensagem, porque o `git mktree` nem chega a rodar.

Seria a coleta inteira parando de ir ao ar toda vez que Taió não coletasse. E o
risco já era latente antes: o `ultimo_nivel_sc.json` ocupava essa última linha e
nunca falhou só porque existe sempre na VPS.

O teste roda o script de verdade, num repositório de mentira, com e sem os
arquivos opcionais — que é o único jeito de pegar isso.
"""
import json
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
SCRIPT = RAIZ / "scripts" / "publicar_tempo_real.sh"

ULTIMO = {"leituras": [{"estacao": "X", "rio": "itajai-acu", "cidade": "taio",
                        "nivel_m": 5.25, "medido_em": "2026-09-04T01:00:00"}]}


class Publicador(unittest.TestCase):
    def monta(self, opcionais: dict[str, object]) -> Path:
        """Um repositório de mentira com o script e os arquivos pedidos."""
        base = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, base, ignore_errors=True)
        (base / "scripts").mkdir()
        shutil.copy2(SCRIPT, base / "scripts" / SCRIPT.name)
        tr = base / "data" / "tempo-real"
        tr.mkdir(parents=True)
        (tr / "ultimo.json").write_text(json.dumps(ULTIMO), encoding="utf-8")
        for nome, conteudo in opcionais.items():
            (tr / nome).write_text(json.dumps(conteudo), encoding="utf-8")
        for cmd in (["git", "init", "-q"],
                    ["git", "config", "user.email", "t@t"],
                    ["git", "config", "user.name", "t"]):
            subprocess.run(cmd, cwd=base, check=True)
        return base

    def roda(self, base: Path) -> subprocess.CompletedProcess:
        return subprocess.run(
            ["bash", "scripts/publicar_tempo_real.sh", "--seco"],
            cwd=base, capture_output=True, text=True,
            env={**os.environ, "GIT_CONFIG_NOSYSTEM": "1"},
        )

    def arvore(self, base: Path, saida: str) -> set[str]:
        """Os arquivos que o commit anunciado carrega."""
        # "publicaria o commit <SHA> em refs/heads/tempo-real" — o sha vem
        # DEPOIS de "commit", não no fim da linha (o fim é o ref).
        linha = next(l for l in saida.splitlines() if l.startswith("publicaria"))
        campos = linha.split()
        sha = campos[campos.index("commit") + 1]
        r = subprocess.run(["git", "ls-tree", "--name-only", sha],
                           cwd=base, capture_output=True, text=True, check=True)
        return set(r.stdout.split())

    def test_publica_sem_nenhum_arquivo_opcional(self):
        """
        O caso que quebrava: só o `ultimo.json`, os três opcionais ausentes.

        É o estado de uma VPS nova, e era o estado de toda VPS enquanto Taió não
        coletasse. Tem de publicar assim mesmo — o nível ao vivo não depende dos
        extras.
        """
        base = self.monta({})
        r = self.roda(base)
        self.assertEqual(r.returncode, 0, f"o publicador morreu calado:\n{r.stderr}")
        self.assertIn("publicaria", r.stdout)
        self.assertEqual(self.arvore(base, r.stdout), {"ultimo.json"})

    def test_leva_o_arquivo_de_taio_quando_ele_existe(self):
        base = self.monta({"ultimo_taio.json": {"barragem": {"comportas": {"abertas": 7}}}})
        r = self.roda(base)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("ultimo_taio.json", self.arvore(base, r.stdout))

    def test_leva_os_quatro_juntos(self):
        base = self.monta({
            "serie-recente.json": {"series": {}},
            "ultimo_nivel_sc.json": {"leituras": []},
            "ultimo_taio.json": {"barragem": {}},
        })
        r = self.roda(base)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(
            self.arvore(base, r.stdout),
            {"ultimo.json", "serie-recente.json", "ultimo_nivel_sc.json", "ultimo_taio.json"},
        )

    def test_arquivo_opcional_quebrado_nao_sobe_e_nao_derruba(self):
        """JSON quebrado num extra não pode levar junto o nível ao vivo."""
        base = self.monta({})
        (base / "data" / "tempo-real" / "ultimo_taio.json").write_text("{quebrado", encoding="utf-8")
        r = self.roda(base)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertNotIn("ultimo_taio.json", self.arvore(base, r.stdout))

    def test_o_ensaio_lista_TODOS_os_arquivos_que_iriam(self):
        """
        O `--seco` existe para conferir antes de publicar. Ele anunciava só o
        serie-recente; com quatro arquivos, calar sobre três faria a conferência
        não conferir nada.
        """
        base = self.monta({
            "serie-recente.json": {"series": {}},
            "ultimo_taio.json": {"barragem": {}},
        })
        r = self.roda(base)
        self.assertEqual(r.returncode, 0, r.stderr)
        for nome in ("ultimo.json", "serie-recente.json", "ultimo_taio.json"):
            self.assertIn(nome, r.stdout, f"o ensaio não anunciou {nome}")
        self.assertNotIn("ultimo_nivel_sc.json", r.stdout)

    def test_ultimo_json_sem_leituras_nao_vai_ao_ar(self):
        """O portão que já existia: publicar vazio apagaria o nível da tela."""
        base = self.monta({})
        (base / "data" / "tempo-real" / "ultimo.json").write_text('{"leituras": []}', encoding="utf-8")
        r = self.roda(base)
        self.assertEqual(r.returncode, 1)
        self.assertIn("Nada publicado", r.stderr)


if __name__ == "__main__":
    unittest.main()
