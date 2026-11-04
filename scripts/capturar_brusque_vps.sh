#!/usr/bin/env bash
# Roda `capturar_brusque.py` NA VPS e publica os brutos no branch `captura-brusque` (04/11/2026).
#
# Por que na VPS: o servidor de Brusque (srv-web-02.brusque.sc.gov.br, 132.255.223.229) não responde nem às sessões
# de código nem ao runner do GitHub (IPv4 em timeout, IPv6 recusado — rodadas de 04/11/2026 no Actions). A VPS já
# alcançava o portal de Brusque. Só GET, robots.txt antes de tudo, User-Agent do projeto (as regras moram no .py).
#
# Uso, na VPS, como o usuário das coletas (que já tem a chave de publicação do `tempo-real`):
#     cd /opt/enchentes-vale-itajai
#     sudo -u enchentes git fetch -q origin claude/projeto-critico-seguranca-ubkk9l-captura-brusque
#     sudo -u enchentes git show FETCH_HEAD:scripts/capturar_brusque_vps.sh | sudo -u enchentes bash
#
# Não muda nada no checkout da VPS (o script e a captura ficam em /tmp) e não toca no `tempo-real` nem no main.
set -euo pipefail
REPO=/opt/enchentes-vale-itajai
RAMO=claude/projeto-critico-seguranca-ubkk9l-captura-brusque
TMP="$(mktemp -d /tmp/captura-brusque.XXXXXX)"
cd "$REPO"
git show "FETCH_HEAD:scripts/capturar_brusque.py" > "$TMP/capturar_brusque.py" 2>/dev/null \
  || git show "origin/$RAMO:scripts/capturar_brusque.py" > "$TMP/capturar_brusque.py"
mkdir -p "$TMP/captura"
set +e
PYTHONPATH="$REPO/scripts" python3 "$TMP/capturar_brusque.py" --saida "$TMP/captura" > "$TMP/captura/captura.txt" 2>&1
set -e
{
  echo "rodada na VPS em $(date -u +%Y-%m-%dT%H:%M:%SZ), host $(hostname)"
  getent ahosts defesacivil.brusque.sc.gov.br | head -2
} > "$TMP/captura/rede.txt" 2>&1
cat "$TMP/captura/captura.txt"
linhas=""
for f in "$TMP"/captura/*; do
  [ -f "$f" ] || continue
  linhas="$linhas$(printf '100644 blob %s\t%s' "$(git hash-object -w "$f")" "$(basename "$f")")"$'\n'
done
arvore=$(printf '%s' "$linhas" | git mktree)
commit=$(git commit-tree "$arvore" -m "Captura de Brusque pela VPS, $(date -u +%Y-%m-%dT%H:%M:%SZ)")
git push --force --quiet origin "$commit:refs/heads/captura-brusque"
echo "publicado em captura-brusque: $commit"
rm -rf "$TMP"
