# Ituporanga: a régua a jusante da Barragem Sul e a régua do Centro

Decisões do Jefferson de 08/10/2026, depois da auditoria de `https://www.ituporanga.sc.gov.br/nivel-rio`.

## O que a auditoria encontrou

| | Régua da cidade no site | Régua do "Centro" da Prefeitura |
|---|---|---|
| Identidade | DCSC-00039 "SDC-SC Ituporanga" = ANA 83145140 **"Barragem Sul Ituporanga Jusante"** | não nomeada, não situada, zero não informado |
| Onde | −27,4822 / −49,5825, ≈3,7 km rio abaixo do barramento da Barragem Sul (DCSC-00038, −27,5039 / −49,5536) | "Centro" |
| Leitura em 08/10/2026 | 4,17 m às 09:46 (DCSC); a coluna "Jusante (m)" do Boletim Diário marcava **4,21 m às 07:00** — a mesma régua | **2,04 m às 07:00**, "Nível de Criticidade: Alerta" |
| Classificação | estadual (`rio_alarmes`: emergência, `status=3`) | a da Prefeitura, nas cotas dela, que a página não publica |
| Cadência | 10 min | 2 leituras/dia (07:00 e 17:00), manuais |

A leitura da DCSC-00039 é de água **já amortecida pela barragem**: isso importa para a previsão a jusante e para
não ler a série como regime natural (já estava em `codigo_ana_verificacao`; agora está também em `observacao`,
que a aba Fontes mostra, e no painel do Monitor).

## O que mudou

1. **Descrição.** `data/estacoes.json` → `ituporanga.observacao` começa por "RÉGUA A JUSANTE DA BARRAGEM SUL"; o
   painel do Monitor diz "Fonte da cor: DCSC-00039, régua a jusante da Barragem Sul (≈3,7 km abaixo do
   barramento)".
2. **Coleta do Centro.** `scripts/coleta_ituporanga.py --publicar` lê o Boletim Diário (robots.txt: `Allow: /`),
   extrai "Última leitura", "Nível do Rio (Centro)" e "Nível de Criticidade" mais a primeira linha da tabela da
   Barragem Sul (montante, jusante, comportas, canal extravasor), e grava
   `data/tempo-real/ultimo_ituporanga_centro.json`. `publicar_tempo_real.sh` sobe o arquivo a cada publicação,
   só se gerado há ≤ 30 min; falha apaga o anterior. **A Prefeitura recusa a VPS** (ver "Coleta pelo Actions",
   abaixo): na VPS o coletor tenta a página e, recusado, usa o que o GitHub Actions leu e publicou.
3. **Tela.** Na página de Ituporanga (aba Agora), o painel "Régua do Centro (Prefeitura)": número, hora de
   Brasília, idade, fonte com link e a criticidade **como a fonte escreve** ("A Prefeitura classifica como
   'Alerta' — classificação dela, nas cotas dela"). No Monitor, uma linha no painel da cidade. **Sem cor**,
   sem pino, sem faixa deste site.

## Regras

- **Nunca em `leituras`.** Se a leitura do Centro entrasse em `ultimo.json` como leitura de Ituporanga, ela
  viraria "a leitura municipal" da cidade (`leituraDaCidade`) e desligaria a classificação estadual da
  DCSC-00039 — a municipal manda. Por isso o arquivo próprio, como a maré do CIRAM.
- **Sem cor até confirmar as cotas na mesma régua.** A Prefeitura classifica ("Alerta") por cotas que não
  publica; não se sabe o zero da régua. Até a Defesa Civil de Ituporanga confirmar as cotas **nesta** régua, o
  número aparece com horário e fonte e nenhuma faixa deste projeto se aplica. A pergunta à Defesa Civil já foi
  enviada e reforçada (Gmail).
- **Leitura antiga nunca como atual.** Mais de 18 h sem leitura nova (duas por dia): a tela diz a hora da última
  e não mostra o número. Arquivo de publicação parada (> 30 min): "indisponível".
- **O nível da barragem não é o da cidade.** "Montante (m)" (~20 m) fica em `barragem_sul`, campo próprio;
  nunca vira leitura de régua.
- **Horário.** A página publica hora local; `medido_em` vai sem fuso (contrato do projeto). `gerado_em` é UTC.

## Coleta pelo Actions (08/10/2026): a Prefeitura recusa a VPS

Depois do primeiro deploy (16:38 UTC), duas publicações saíram sem o arquivo. Na VPS:

```
$ python3 scripts/coleta_ituporanga.py --publicar
aviso: leitura do Centro de Ituporanga indisponível (https://www.ituporanga.sc.gov.br/robots.txt:
403 Client Error: Forbidden for url: https://www.ituporanga.sc.gov.br/robots.txt); nada publicado
```

O host responde **403 ao `robots.txt`** quando quem pede é a VPS (Hetzner, Helsinque) — o mesmo que o Atlas de
Desastres faz. O projeto não pede página sem ler o robots, então nada foi coletado. Da sessão de código e do
runner do GitHub a página abre e o robots diz `Allow: /`.

A saída é a mesma de Gaspar (decisão de 04/10/2026, `docs/gaspar-ponte-pc.md`):

| | |
|---|---|
| runner | `.github/workflows/coletar-ituporanga.yml`, a cada 30 min (minutos 11 e 41): robots → página → `extrair()`. Só quando a leitura **muda** (duas por dia) publica `ituporanga-centro.json` + o HTML bruto no branch `coleta-ituporanga` (órfão, um commit). Falha deixa o run vermelho, guarda o diagnóstico e abre/atualiza a issue "Coleta de Ituporanga (Centro) pelo Actions falhando". |
| VPS | `coleta_ituporanga.py --publicar` tenta a página primeiro. Recusado, lê `raw.githubusercontent.com/…/coleta-ituporanga/ituporanga-centro.json` (`ituporanga_actions.ler_publicado`), aceita só o deste coletor, com a página lida há ≤ 3 h, `medido_em` sem fuso e nível plausível, e grava `ultimo_ituporanga_centro.json` como antes. Sem nenhum dos dois, apaga o arquivo. |
| arquivo | `via`: `{"coletor": "vps" \| "github-actions", "pagina_lida_em": <UTC>}`. `gerado_em` continua sendo a hora da publicação na VPS (o publicador e a tela medem por ele se a publicação está viva); a idade da leitura continua por `medido_em` (18 h). |

Lógica em `scripts/ituporanga_actions.py`, testes em `scripts/teste_ituporanga_actions.py` (robots 403 não pede a
página; mesma leitura não regrava; a VPS recusa outro coletor, página velha e `medido_em` com fuso; o `publicar`
cai para o Actions e diz isso em `via`). O agendamento só vale no `main`.

## Como conferir

```bash
cd scripts
python3 teste_coleta_ituporanga.py                       # 10 testes
python3 coleta_ituporanga.py                              # busca e mostra, sem gravar
python3 coleta_ituporanga.py --arquivo pagina-salva.html  # sem rede
```

No site: `npm test` roda `web/src/dados/ituporangaCentro.test.ts` (arquivo bom, fuso quebrado, publicação parada,
leitura antiga, leitura do futuro).

## Pendente

- Confirmação, pela Defesa Civil de Ituporanga, de qual régua é o "Centro", onde fica, qual o zero e quais as
  cotas de atenção/alerta/emergência **nela**. Só então a leitura pode receber cor — e entra como régua própria
  da cidade, com `alerta_automatico` decidido à parte.
