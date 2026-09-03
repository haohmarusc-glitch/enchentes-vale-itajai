#!/usr/bin/env bash
#
# Deploy da VPS num comando só: traz o main e reinicia o bot SÓ se o código dele
# mudou. Os coletores não precisam de restart — o cron invoca o script novo a
# cada ciclo —, então reiniciar o bot à toa só cortaria uma conversa no meio.
#
# Roda como ROOT: o alias `github-enchentes` e a chave de deploy moram no
# ~/.ssh/config do root (é o mesmo caminho que o publicar_tempo_real.sh usa). O
# repo é do usuário `enchentes`, e o git do root precisa do safe.directory —
# este script garante os dois.
#
# Uso (na VPS, como root):
#     /opt/enchentes-vale-itajai/scripts/deploy.sh
#
set -euo pipefail

# Raiz do repo = pasta acima deste script, resolvida pelo caminho do próprio
# arquivo, para funcionar de qualquer cwd.
RAIZ="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

SERVICO="enchentes-bot"
# Se qualquer um destes mudar, o bot (processo longo) está com código velho e
# precisa reiniciar. bot.py e os módulos que ele importa (comum, transito,
# notificador). Coletores ficam de fora: rodam do zero a cada cron.
VIGIADOS=(scripts/bot.py scripts/comum.py scripts/transito.py scripts/notificador.py)

info() { printf '\033[1;34m›\033[0m %s\n' "$*"; }
ok()   { printf '\033[1;32m✓\033[0m %s\n' "$*"; }
aviso(){ printf '\033[1;33m!\033[0m %s\n' "$*" >&2; }

if [[ "$(id -u)" -ne 0 ]]; then
  aviso "rode como root: o alias github-enchentes e a chave de deploy estão no ~/.ssh/config do root."
  exit 1
fi

cd "$RAIZ"

# O repo é do usuário enchentes; sem isto o git do root recusa por "dubious
# ownership". Idempotente.
if ! git config --global --get-all safe.directory 2>/dev/null | grep -qxF "$RAIZ"; then
  git config --global --add safe.directory "$RAIZ"
  info "safe.directory adicionado para $RAIZ"
fi

antes="$(git rev-parse HEAD)"
info "estado atual: ${antes:0:9}"

info "buscando origin/main…"
git fetch --quiet origin main
alvo="$(git rev-parse origin/main)"

if [[ "$antes" == "$alvo" ]]; then
  ok "já está no topo (${antes:0:9}). Nada a fazer."
  exit 0
fi

# Fast-forward. Se um arquivo versionado estiver sujo (ex.: ultimo_gaspar.json,
# que um coletor reescreve), o ff falha — guarda a alteração local e refaz. Não
# desfaz o stash: o coletor regenera o arquivo no próximo ciclo. Arquivos não
# versionados (ultimo.json, chuva-*.json) não entram no stash e ficam intactos.
if ! git merge --ff-only origin/main >/dev/null 2>&1; then
  aviso "trabalho local versionado atrapalha o fast-forward; guardando com git stash."
  git stash push --quiet -m "deploy.sh $(date -Is)" || true
  git merge --ff-only origin/main >/dev/null
fi

depois="$(git rev-parse HEAD)"
ok "atualizado ${antes:0:9} → ${depois:0:9}"
info "arquivos alterados:"
git diff --name-only "$antes" "$depois" | sed 's/^/    /'

# Reinicia o bot só se algum arquivo vigiado mudou entre os dois commits.
mudou="$(git diff --name-only "$antes" "$depois" -- "${VIGIADOS[@]}")"
if [[ -z "$mudou" ]]; then
  ok "código do bot inalterado — sem restart. Coletores pegam o novo no próximo cron."
  exit 0
fi

info "código do bot mudou:"
echo "$mudou" | sed 's/^/    /'

# Reinicia direto e deixa o systemd ser a fonte da verdade. O `list-unit-files`
# dava falso "não encontrado" para um serviço que existe e roda; tentar o restart
# e olhar o resultado é mais honesto do que uma pré-checagem frágil.
info "reiniciando ${SERVICO}…"
# Captura o erro REAL do restart em vez de escondê-lo (o 2>/dev/null antigo
# transformava qualquer falha — inclusive transitória — no palpite errado
# "nome não encontrado", que confundiu num deploy real).
if ! saida_restart="$(systemctl restart "$SERVICO" 2>&1)"; then
  aviso "falha ao reiniciar ${SERVICO}:"
  [[ -n "$saida_restart" ]] && printf '    %s\n' "$saida_restart" >&2
  # Só sugere "nome errado" se o unit realmente não existir.
  if ! systemctl cat "$SERVICO" >/dev/null 2>&1; then
    aviso "o unit ${SERVICO} não existe. Serviços parecidos:"
    systemctl list-units --all --type=service 2>/dev/null | grep -i enchente | sed 's/^/    /' >&2
  else
    aviso "o unit existe; veja o log: journalctl -u ${SERVICO} -n 40 --no-pager"
  fi
  aviso "o código novo já está no /opt; reinicie à mão quando resolver."
  exit 1
fi
sleep 2
if systemctl is-active --quiet "$SERVICO"; then
  ok "${SERVICO} de pé (active)."
else
  aviso "${SERVICO} NÃO subiu. Veja: journalctl -u ${SERVICO} -n 40 --no-pager"
  exit 1
fi
