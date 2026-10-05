#!/usr/bin/env bash
#
# Cópia semanal, fora da VPS, das séries que o coletor guarda (pedido do Jefferson, 05/10/2026).
#
# O que copia (tudo gitignorado no `main`, que só existe na VPS):
#   - data/tempo-real/*.ndjson e *.ndjson.gz — a série de cada régua, chuva e nível estadual,
#     com `medido_em` em hora de Brasília. É o que `scripts/nivel_antes.py --series` lê.
#   - data/eventos-registro/ — os JSONs de cada coleta, arquivados pelo registrar_evento.py.
#
# Para onde: o branch `arquivo-series` do próprio repositório no GitHub. Ao contrário do
# `tempo-real` (órfão, substituído a cada publicação), este ACUMULA: cada cópia é um commit
# novo sobre o anterior, e o push é sem --force. Uma VPS que perdeu o disco não apaga a cópia;
# no máximo deixa de acrescentar. Mês fechado não muda, então o git guarda uma vez só; o mês
# corrente cresce por acréscimo de linhas, que o git comprime bem entre uma semana e outra.
#
# Não usa checkout nem mexe no índice de quem está no `main`: monta a árvore com um índice
# temporário (GIT_INDEX_FILE), como o publicar_tempo_real.sh faz com mktree.
#
# Credencial: a MESMA do publicar_tempo_real.sh (deploy key com escrita, remoto em SSH). Não
# precisa de segredo novo. Nunca token no URL do remoto.
#
# Cron sugerido na VPS (conferir o diretório com `crontab -l`: a coleta roda de /opt):
#     17 4 * * 0  cd /opt/enchentes-vale-itajai && scripts/copiar_series.sh >> /var/log/enchentes-copia.log 2>&1
#
# Uso:
#     scripts/copiar_series.sh          # copia
#     scripts/copiar_series.sh --seco   # mostra o que copiaria, sem enviar
set -euo pipefail

RAIZ="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BRANCH="arquivo-series"
# O GitHub recusa arquivo acima de 100 MB. Um mês de série tem uns 5 MB; passar disso é sinal
# de coisa errada, e é melhor parar avisando do que mandar um push que vai falhar no meio.
LIMITE_BYTES=$((90 * 1024 * 1024))
SECO=0
[ "${1:-}" = "--seco" ] && SECO=1

cd "$RAIZ"

shopt -s nullglob
SERIES=(data/tempo-real/*.ndjson data/tempo-real/*.ndjson.gz)
shopt -u nullglob
if [ "${#SERIES[@]}" -eq 0 ]; then
  echo "ERRO: nenhuma série em data/tempo-real/. Nada copiado (é o diretório certo? ver crontab -l)." >&2
  exit 1
fi

for arq in "${SERIES[@]}"; do
  tam=$(wc -c < "$arq")
  if [ "$tam" -gt "$LIMITE_BYTES" ]; then
    echo "ERRO: $arq tem $tam bytes, acima do limite de $LIMITE_BYTES. Nada copiado." >&2
    exit 1
  fi
done

INDICE="$(mktemp)"
trap 'rm -f "$INDICE"' EXIT
rm -f "$INDICE"

CAMINHOS=()
for arq in "${SERIES[@]}"; do CAMINHOS+=("${arq#data/}"); done
[ -d data/eventos-registro ] && CAMINHOS+=("eventos-registro")

# -f: os arquivos são gitignorados no `main` de propósito; aqui eles SÃO o conteúdo.
GIT_INDEX_FILE="$INDICE" git -C "$RAIZ/data" --work-tree="$RAIZ/data" add -f -- "${CAMINHOS[@]}"
TREE="$(GIT_INDEX_FILE="$INDICE" git write-tree)"

# O branch remoto é o pai: a cópia acumula. Branch ainda inexistente → primeiro commit, sem pai.
PAI=""
if git fetch --quiet origin "refs/heads/$BRANCH" 2>/dev/null; then
  PAI="$(git rev-parse FETCH_HEAD)"
fi

if [ -n "$PAI" ] && [ "$(git rev-parse "$PAI^{tree}")" = "$TREE" ]; then
  echo "nada mudou desde a última cópia ($PAI)."
  exit 0
fi

MSG="Cópia das séries da VPS em $(date -u +%Y-%m-%dT%H:%MZ)"
if [ -n "$PAI" ]; then
  COMMIT="$(git commit-tree "$TREE" -p "$PAI" -m "$MSG")"
else
  COMMIT="$(git commit-tree "$TREE" -m "$MSG")"
fi

if [ "$SECO" = "1" ]; then
  echo "copiaria o commit $COMMIT em refs/heads/$BRANCH (pai: ${PAI:-nenhum})"
  echo "arquivos:"
  git ls-tree -r --name-only "$TREE" | grep -v '^eventos-registro/.*/objetos/' | sed 's/^/  /'
  echo "  (+ $(git ls-tree -r --name-only "$TREE" | grep -c '^eventos-registro/.*/objetos/' || true) objetos do registro de eventos)"
  exit 0
fi

# Sem --force: se alguém mexeu no branch, o push falha e a cópia de antes fica intacta.
git push --quiet origin "$COMMIT:refs/heads/$BRANCH"

# Confere que chegou: o remoto tem de apontar para o commit que acabou de subir.
REMOTO="$(git ls-remote origin "refs/heads/$BRANCH" | cut -f1)"
if [ "$REMOTO" != "$COMMIT" ]; then
  echo "ERRO: o push terminou, mas $BRANCH no GitHub aponta para ${REMOTO:-nada}, não para $COMMIT." >&2
  exit 1
fi
echo "copiado em $BRANCH: $COMMIT ($(git ls-tree -r --name-only "$TREE" | wc -l) arquivos)"
