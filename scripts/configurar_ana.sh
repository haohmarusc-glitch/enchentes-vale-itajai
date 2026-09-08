#!/usr/bin/env bash
#
# Grava ANA_IDENTIFICADOR e ANA_SENHA no .env SEM a senha aparecer na tela,
# sem entrar no histórico do shell e sem passar por argumento de comando
# (que apareceria no `ps`).
#
# Uso, na VPS:
#     /opt/enchentes-vale-itajai/scripts/configurar_ana.sh
#
# POR QUE ISTO É UM SCRIPT E NÃO UM BLOCO PARA COLAR. Um bloco colado com
# `read` dentro é uma armadilha: o terminal já tem o resto do texto colado no
# buffer, e o `read` consome a PRÓXIMA LINHA DA COLAGEM em vez de esperar você
# digitar. A senha iria para a tela e para o histórico — exatamente o que este
# script existe para evitar. Num arquivo, o `read` só roda quando você invoca.
#
# POR QUE SUBSTITUI NO LUGAR E NÃO ACRESCENTA NO FIM. O `carrega_env` do
# comum.py usa `os.environ.setdefault`: a PRIMEIRA ocorrência da chave vence.
# O .env.example traz `ANA_SENHA=` vazio; acrescentar a senha no fim deixaria a
# linha vazia ganhando, e o ana_hidroweb.py diria "ANA_IDENTIFICADOR e ANA_SENHA
# não estão no ambiente" — erro que parece credencial errada e não é.
set -euo pipefail

RAIZ="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$RAIZ"

umask 077

if [[ ! -f .env ]]; then
  cp .env.example .env
  echo "criei o .env a partir do .env.example"
fi
chmod 600 .env

echo
echo "Os valores não vão para a tela nem para o histórico. Ctrl-C aborta."
echo
read -r  -p 'ANA_IDENTIFICADOR: ' ANA_ID
read -rs -p 'ANA_SENHA........: ' ANA_PW
echo

if [[ -z "$ANA_ID" || -z "$ANA_PW" ]]; then
  echo "vazio — nada foi gravado." >&2
  exit 1
fi

# Os valores viajam por AMBIENTE, não por argumento: argumento apareceria no
# `ps` para qualquer processo. O ambiente de um processo do root só o root lê.
ANA_ID="$ANA_ID" ANA_PW="$ANA_PW" python3 - <<'PY'
import hashlib
import os
import re
import sys
from pathlib import Path

sys.path.insert(0, "scripts")

alvo = {"ANA_IDENTIFICADOR": os.environ["ANA_ID"], "ANA_SENHA": os.environ["ANA_PW"]}
env = Path(".env")

vistos: set[str] = set()
saida: list[str] = []
for linha in env.read_text(encoding="utf-8").splitlines():
    casa = re.match(r"\s*([A-Za-z_][A-Za-z0-9_]*)\s*=", linha)
    chave = casa.group(1) if casa else None
    if chave in alvo:
        if chave in vistos:
            continue                      # duplicata some: com setdefault ela seria lixo mudo
        saida.append(f"{chave}={alvo[chave]}")
        vistos.add(chave)
    else:
        saida.append(linha)
for chave, valor in alvo.items():
    if chave not in vistos:
        saida.append(f"{chave}={valor}")

env.write_text("\n".join(saida) + "\n", encoding="utf-8")

# A conferência que importa: o que o carrega_env vai ENTREGAR é o que foi
# digitado? Ele faz `.strip().strip("'\"")` no valor — uma senha com espaço nas
# pontas ou entre aspas chega DIFERENTE ao script, e falharia como se a
# credencial estivesse errada. Comparamos sem imprimir a senha: tamanho e um
# prefixo de hash bastam para você reconhecer, e não servem para ninguém mais.
from comum import carrega_env  # noqa: E402

for chave in alvo:
    os.environ.pop(chave, None)
carrega_env(env)

problema = False
for chave, valor in alvo.items():
    lido = os.environ.get(chave, "")
    marca = hashlib.sha256(valor.encode()).hexdigest()[:8]
    if lido == valor:
        print(f"  ✓ {chave}: {len(valor)} caracteres, sha256 {marca}")
    else:
        problema = True
        print(f"  ✗ {chave}: você digitou {len(valor)} caracteres, mas o .env entrega "
              f"{len(lido)}. O leitor remove espaços nas pontas e aspas ao redor — "
              "se a senha tem isso, ela precisa ser tratada antes de servir.")
if problema:
    raise SystemExit(1)
print("\n.env gravado com permissão 600. Agora:")
print("    python3 scripts/ana_hidroweb.py --verificar")
PY
