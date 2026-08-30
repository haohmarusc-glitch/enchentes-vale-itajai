#!/usr/bin/env bash
#
# Publica a última leitura de nível no branch `tempo-real`, de onde o site a
# busca pelo raw.githubusercontent.com.
#
# Por que um branch separado: coletando de 15 em 15 minutos, um commit por
# coleta daria 35 mil commits por ano no `main`. Aqui o branch é órfão e cada
# publicação SUBSTITUI a anterior — o histórico fica sempre com um commit só, e
# o `main` não vê nada disso.
#
# Não usa checkout: monta o commit direto com git plumbing, então a árvore de
# trabalho de quem está no `main` não é tocada. Pode rodar no mesmo cron da
# coleta, logo depois dela.
#
# Precisa de credencial de push. Numa VPS, o jeito usual é um token com escopo
# de repositório no remoto:
#     git remote set-url origin https://USUARIO:TOKEN@github.com/OWNER/REPO.git
# ou uma chave SSH com o remoto em git@github.com:OWNER/REPO.git
#
# Uso:
#     scripts/publicar_tempo_real.sh          # publica
#     scripts/publicar_tempo_real.sh --seco   # mostra o que faria, sem enviar
set -euo pipefail

RAIZ="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ARQUIVO="$RAIZ/data/tempo-real/ultimo.json"
BRANCH="tempo-real"
SECO=0
[ "${1:-}" = "--seco" ] && SECO=1

cd "$RAIZ"

if [ ! -f "$ARQUIVO" ]; then
  echo "ERRO: $ARQUIVO não existe. Rode scripts/coleta_niveis.py primeiro." >&2
  exit 1
fi

# Um JSON quebrado publicado é pior que nenhum: o site pararia de mostrar
# nível sem ninguém entender por quê.
if ! python3 -c 'import json,sys; d=json.load(open(sys.argv[1])); sys.exit(0 if d.get("leituras") else 1)' "$ARQUIVO" 2>/dev/null; then
  echo "ERRO: $ARQUIVO não é JSON válido ou está sem leituras. Nada publicado." >&2
  exit 1
fi

BLOB="$(git hash-object -w "$ARQUIVO")"
TREE="$(printf '100644 blob %s\tultimo.json\n' "$BLOB" | git mktree)"
COMMIT="$(git commit-tree "$TREE" -m "Leitura de $(date -u +%Y-%m-%dT%H:%M:%SZ)")"

if [ "$SECO" = "1" ]; then
  echo "publicaria o commit $COMMIT em refs/heads/$BRANCH"
  echo "conteúdo:"
  git show "$COMMIT:ultimo.json" | head -5
  exit 0
fi

git push --force --quiet origin "$COMMIT:refs/heads/$BRANCH"
echo "publicado em $BRANCH: $(git show --no-patch --format=%s "$COMMIT")"
