# O portal da Defesa Civil de Brusque — quinze estações, duas regras e um script

**08/09/2026.** O Jefferson leu o JS do portal e escreveu um coletor
(`estacoes_brusque.py`, fora do repositório). Este documento guarda **o que ele
descobriu**, com a proveniência, e **o que deste projeto não pode ir para o
código dele sem ressalva**.

## Duas regras do servidor (do JS, sem disparar nada)

1. O botão faz um **POST em `/estacao/baixar-historico?validar`** antes de
   submeter o form para `/estacao/baixar-historico`. A sonda agora faz os dois.
2. **O servidor recusa janelas maiores que um ano.** É por isso que a Salseiro
   veio em dez fatias anuais. A sonda recusa antes de chamar.

Mais uma, do arquivo: **`pandas.read_html` trata a vírgula como separador de
milhar** e transforma `2,09` em `209`. É `decimal=","`, `thousands=None` — ou o
Mirim sobe cem vezes. O leitor deste projeto não usa pandas e faz a troca à
mão; fica registrado para quem usar.

## As quinze estações, como o portal as lista

| id | nome no portal | atenção / emergência (portal) | o que este projeto sabe |
|---|---|---|---|
| 31 | Salseiro – Vidal Ramos | 3,00 / 4,50 | **RECUSADA** como régua de Vidal Ramos: 6,8 km, 0,70 m medidos. Histórico 2018–2026 no repo (#242) |
| **3** | **Vidal Ramos** | 3,00 / 5,00 | **CANDIDATA à nossa régua (DCSC-00024)**. Ver abaixo |
| 18 | Botuverá | 3,50 / 6,00 | a conferir (DCSC-00018?) |
| 2 | CEOPS – Botuverá | 3,50 / 6,00 | a conferir; nome parecido já enganou |
| 32 | Botuverá – Prefeitura | 3,00 / 5,00 | a conferir |
| **79** | **Ponte Estaiada – DCSC** | 3,00 / 5,00 | **par PROVADO** com a nossa leitura de Brusque (07/09/2026). É a DCSC-00019 |
| **4** | **Ponte Estaiada – ANA** | 4,00 / 7,00 | **outra régua, mesmo nome** — provavelmente a 83900000 (BRUSQUE PCD). Zero próprio |
| 23 | Guarani | 4,10 / 6,00 | a conferir |
| 19 | Cedro Alto | 1,50 / 3,00 | a conferir |
| 24 | Limeira Alta | 1,50 / 3,00 | a conferir |
| 25 | Limeira Baixa | 2,50 / 4,00 | a conferir |
| 21 | Dom Joaquim | 2,50 / 4,00 | a conferir. ⚠️ o `ver/21` citado em `estacoes.json` é do portal de **Gaspar** — mesma plataforma, ids que se repetem |
| 20 | Zantão | 3,50 / 6,00 | a conferir |
| 17 | Paquetá | 3,00 / 5,00 | a conferir |
| 22 | Res. Felipe Heckert | 3,50 / 6,00 | a conferir |

**As cotas desta tabela são o que o portal publica, transcritas pelo Jefferson.
Nenhuma entrou em `estacoes.json`.** A regra continua a de sempre: cota só
pinta depois do par régua-leitura provado, e só quando se sabe de quem é a
escala.

## ⚠️ Um erro meu, corrigido aqui

No #241 rotulei a estação **4** como "par provado". O par provado (1,27 / 1,27 /
1,28 m no mesmo minuto) foi com a **79**. A 4 é a *Ponte Estaiada – ANA*: mesmo
nome, outra régua — o tipo de erro que este projeto mais comete, e que agora
tem teste na sonda.

## A estação 3 é a pista mais valiosa do dia

A 79 é o **repasse** da rede estadual (DCSC-00019) dentro do portal de Brusque.
Se a 3 for o repasse da **DCSC-00024** — a régua que a nossa coleta ao vivo lê
para Vidal Ramos —, então o **histórico dela desde 2018, baixável pelo mesmo
botão, é o histórico da NOSSA régua**. Seria a primeira série longa que Vidal
Ramos teria, e na régua certa.

**O que decide é o mesmo teste da 79:** três leituras do mesmo minuto — página
da estação 3, rede estadual DCSC-00024, nossa coleta. Até lá: nem série, nem
cota, nem trânsito. Está escrito em `estacoes.json` como
`candidata_historico_portal_brusque`, pista e não vínculo.

E mesmo com o par provado, o **3,00 / 5,00** que o portal publica para a 3
**não vira cota de Vidal Ramos** sem antes saber de quem é a escala: o portal é
de Brusque, a cidade é Vidal Ramos, e escala publicada por um município para
régua de outro não é cota municipal de ninguém até que alguém diga.

## O script do Jefferson, lido com a régua do projeto

O que está certo e o repositório absorveu: o `?validar`, o teto de um ano, o
`0,00 → NaN`, o `decimal=","`, a pausa entre chamadas, o cookie de sessão antes
do POST.

O que **não pode** entrar como está:

- **`situacao()` classifica por cota do portal.** É exatamente o gesto que o
  #233 recusou para a Salseiro: aplicar 3,00 m a uma leitura sem saber se a
  escala é daquela régua. Para a 3, pintaria *atenção* num estado que a
  própria régua pode chamar de normalidade. Cor sai de par provado, nunca de
  tabela.
- **`drop_duplicates("data")` fica com a PRIMEIRA linha.** As janelas anuais se
  sobrepõem um dia; se o lado que vem primeiro tem `0,00` e o outro tem
  valor, o valor se perde. O leitor do repo fica com o que **tem** valor.
- **`User-Agent: "uso pessoal"`** — o projeto identifica com `comum.USER_AGENT`,
  que diz o que é e como falar com a gente.
- **Sem `robots.txt`.** Fonte nova só entra com o robots conferido; foi por
  isso que o AlertaBlu ficou de fora. A sonda tem o porteiro.
- **`data/raw` e `data/processed`** não são o layout do projeto: bruto vai em
  `data/brutos/` com proveniência; série derivada não é versionada.
