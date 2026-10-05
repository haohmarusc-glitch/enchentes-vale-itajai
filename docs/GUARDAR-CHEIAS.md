# Guardar as cheias para fazer a conta depois

Pedido do Jefferson em 05/10/2026. A pergunta de partida era: *"em 10/11/2008 a Rua José Domingos Machado
encheu em Itajaí; qual era o nível do rio em Brusque 6 horas antes?"*. Para 2008 não dá: não existe série com
hora das réguas daquela cheia no repositório. Este documento junta as três peças para que, nas próximas
cheias, a resposta exista.

## 1. Cópia fora da VPS — `scripts/copiar_series.sh`

**Por quê.** A série que o coletor grava a cada 15 min (`data/tempo-real/*.ndjson`) e o registro de cada
coleta (`data/eventos-registro/`) **só existem no disco da VPS**: são gitignorados no `main`. Se o disco se
perder, perde-se a única série com hora das cheias de 2026 em diante.

**O que faz.** Uma vez por semana, monta um commit com esses arquivos e o envia ao branch `arquivo-series`
do próprio repositório no GitHub.
- O branch **acumula**: cada cópia é filha da anterior e o push é **sem `--force`**. Um mês que sumir da VPS
  continua nas cópias anteriores.
- Mês fechado não muda, então o git o guarda uma vez só. O mês corrente cresce por acréscimo de linhas, e o
  git o comprime bem entre uma semana e outra (uns 5 MB por mês de série).
- Nada mudou desde a última cópia? Não envia nada.
- Não toca o `main`, a árvore de trabalho nem o índice. Monta a árvore com um índice temporário, do mesmo
  jeito que o `publicar_tempo_real.sh` monta a dele.
- Depois do push, confere no GitHub que o branch aponta para o commit enviado.
- Para avisando se algum arquivo passar de 90 MB (o GitHub recusa acima de 100 MB).

**Credencial.** A mesma deploy key que o `publicar_tempo_real.sh` já usa. Não precisa de segredo novo.

**Ligar na VPS** (como root, no checkout que o cron usa; conferir com `crontab -l`, que hoje roda de `/opt`):

```bash
cd /opt/enchentes-vale-itajai && git pull
scripts/copiar_series.sh --seco      # mostra o que iria, sem enviar
scripts/copiar_series.sh             # primeira cópia
crontab -e
# acrescentar (domingo, 04:17 UTC):
17 4 * * 0  cd /opt/enchentes-vale-itajai && scripts/copiar_series.sh >> /var/log/enchentes-copia.log 2>&1
```

**Recuperar** (em qualquer máquina com acesso ao repositório):

```bash
git fetch origin arquivo-series
git archive FETCH_HEAD tempo-real | tar -x -C /caminho/destino   # ou eventos-registro
```

**Testes.** `scripts/teste_copiar_series.py` roda o script de verdade num repositório de mentira com um
remoto local e verifica quatro coisas:
- a cópia acumula e não repete;
- um mês apagado na VPS continua na cópia anterior;
- não força por cima de commit alheio;
- o `--seco` não envia nada.

## 2. A hora em que as ruas alagam

**O que existe hoje:**

| Cidade | Fonte da hora | Situação |
|---|---|---|
| Blumenau | A régua do AlertaBlu (série com hora) mais a cota oficial de cada ponto de rua (`data/cotas-ruas.json`, 2.023 pontos). | **Feito.** `nivel_antes.py --rua` dá a hora em que a régua passou da cota de cada ponto. É a hora em que, pela cota oficial, o ponto começa a alagar. **Não é observação na rua.** |
| Blumenau | Página "Ruas alagadas agora" (`defesacivil.blumenau.sc.gov.br/p/ruas-alagadas`) | O site proíbe acesso automatizado (robots.txt; `docs/cotas-de-ruas.md`). **Não raspar.** O caminho é pedir os registros à Defesa Civil de Blumenau. |
| Gaspar, Brusque, Rio do Sul | Cotas de rua com régua declarada (1.617, 350 e 555 pontos) | Falta conferir qual estação do coletor é a régua dessas cotas. Até lá, `REGUA_DAS_COTAS` não liga essas cidades e a ferramenta diz isso em vez de dar hora. |
| Itajaí | Nenhuma cota de rua; só as manchas por cheia (sem hora). A página nova da Defesa Civil publica as réguas, sem lista de ruas. | Interdições de rua saem em redes sociais e boletins, sem hora estruturada. |

**Para Itajaí (e para conferir as cotas nas outras cidades) a hora precisa ser observada.** Havia dois caminhos:

1. **Registro na mão durante a cheia** — **escolhido pelo Jefferson em 05/10/2026 e feito.**
   - Quem acompanha anota rua, hora e fonte na planilha `docs/modelos/ruas-alagadas.csv`.
   - `scripts/ruas_alagadas.py` importa para `data/ruas-alagadas.json`, conferindo linha por linha.
   - `nivel_antes.py --registradas` faz a conta com essas horas.
   - Passo a passo em `docs/REGISTRO-RUAS-ALAGADAS.md`.
2. **Botão "minha rua alagou agora" no site.** Guardaria rua e hora no KV da Cloudflare. Precisaria de
   moderação (relato falso ou repetido), aviso de privacidade e uma regra de que o relato nunca vira alerta.
   **Não feito.**

**O que não fazer.** Inventar a hora a partir da mancha. A mancha de Itajaí diz *onde* alagou, não *quando*.

## 3. A ferramenta da conta — `scripts/nivel_antes.py`

Responde: "quando a régua X chegou à crista (ou passou de um nível, ou da cota de uma rua), como estavam as
réguas de cima N horas antes?". É **somente leitura** e **descritiva**: não é previsão nem calibração.

```bash
python3 scripts/nivel_antes.py --listar                                  # séries e cristas
python3 scripts/nivel_antes.py --alvo DC-11 --data 2026-09-12            # crista do dia
python3 scripts/nivel_antes.py --alvo AlertaBlu --data 2026-09-11 --nivel 6   # 1ª passagem de 6 m
python3 scripts/nivel_antes.py --rua "Rua São Rafael" --horas 3 6        # Blumenau, pela cota da rua
python3 scripts/nivel_antes.py --relatorio docs/NIVEL-ANTES.md           # todas as cristas possíveis
python3 scripts/nivel_antes.py --series /caminho/tempo-real --listar     # com a série inteira da VPS
```

**Regras da conta:**
- Cada régua tem o seu zero, e os números não se comparam entre réguas. Saem lado a lado, cada um na sua
  régua, com a hora.
- Só entram as réguas **a montante, no mesmo rio**. A cabeceira conta; o afluente lateral e o que está a
  jusante ficam de fora (`estacoes.json`, `_topologia`). `--todas` mostra o resto.
- **Fuso.** As fontes de 2026 estão em hora de Brasília. A telemetria da ANA (2020–2023) **não teve o fuso
  conferido**, por isso ANA só se cruza com ANA.
- A publicação "Blumenau" da página antiga de Itajaí fica de fora: vinha 3 h atrasada.
- **Crista:** máximo da média móvel de 1 h, que é o maior valor num raio de 48 h e subiu ao menos 0,5 m.
  - Nas réguas de Itajaí que sentem a maré, a média é de 12,42 h (um ciclo de maré).
  - Crista na borda dos dados é marcada como piso.
- **"N h antes":** a leitura até 10 min de distância, ou a interpolação entre leituras com até 60 min de vão.
  Fora disso, "sem leitura". Nunca se estima.
- **Itajaí:** sai junto a preamar ou baixa-mar mais próxima da tábua da Marinha. A altura da maré é sobre o
  zero da carta náutica e nunca é régua.

**O que dá hoje** (o relatório completo está em `docs/NIVEL-ANTES.md`):
- **Cheia de 11–12/09/2026 no Açu:** Rio do Sul, Lontras, Ascurra e Indaial (Defesa Civil de SC, 10 min),
  Blumenau (AlertaBlu), Ilhota e as réguas de Itajaí.
- **Itajaí-Mirim em 2026:** só a Asthon de Vidal Ramos até 10/09. Brusque **não tem série com hora no
  repositório**. Com a série inteira da VPS (`--series`), as cristas do Mirim em Itajaí ganham Brusque.
- **ANA 2021–2023:** pares Taió → Blumenau e Taió → Rio do Sul.

**Testes.** `scripts/teste_nivel_antes.py` trava:
- a leitura (perto, interpolada, vão);
- as cristas, inclusive com maré;
- a topologia;
- as famílias de fuso;
- a exclusão da publicação atrasada;
- a rua de Blumenau;
- que o relatório salvo é o recalculado.
