# Cotas de acionamento em 11 municípios — o que o levantamento de 08/09 acrescenta

Data: 09/09/2026. Fonte: memorando "Cotas de acionamento em réguas fluviométricas —
bacia do Itajaí (11 municípios): situação documental", entregue pelo Jefferson
(corte em 08/09/2026), mais as três verificações que ele fez no navegador em
08/09 à noite. Este ambiente não alcança nenhum dos hosts citados (403 do proxy
em `*.sc.gov.br`, Asthon, Google My Maps e agregadores), então tudo o que está
marcado **relatado** foi lido pelo memorando, e o que está marcado
**confirmado** foi visto pelo Jefferson no navegador.

Regra que decide cada linha: **cota só pinta a tela quando está amarrada à
mesma régua da leitura ao vivo**, com fonte documental. Imprensa é pista, não
cota. Onde a fonte oficial se contradiz, vale a que avisa mais cedo.

---

## Resumo por município

| Município | O que o memorando diz | O que o repo já tinha | Veredito | Mexeu em |
|---|---|---|---|---|
| **Gaspar** | `/estacao/ver/21` está viva sob o site DEXTAK; legenda 5,00 / 6 mm / 7,00 | Régua "saiu da página" (07/09); legenda 6,00 / 7,00 (03/09) | **Confirmado** no navegador em 08/09 ~21h. Saiu a *linha da tabela*, não a régua. Cota adotada não muda (Plano, 5/6/7) | `fonte_tempo_real_ressalva`, `fontes_tempo_real`, `cotas_divergencias` |
| **Ilhota** | DC diz não ter régua e usar a leitura de Gaspar; recomenda pintar Gaspar com as cotas de Ilhota | PLANCON cita a Ponte Cláudio Jeremias Cadorin; DCSC-00030 lê nível em datum próprio | **Recusado** o par Gaspar × cotas de Ilhota (regra nº 1). Contradição registrada; pergunta à COMPDEC | `cotas_ressalva`, `cotas_aviso_publico` |
| **Blumenau** | Cinco estágios na página oficial: 0–3 / 3–4 / 4–6 / 6–8 / >8 | 6,00 / 6,50 / 7,40 "AlertaBlu", sem bruto, desde 30/08 | **Bloqueante, relatado.** Se for a vigente, a tela pinta atenção 2 m tarde. Não trocado ainda: sonda `conferir_faixas_blumenau.py` decide. Aviso público até lá | `cotas_divergencias`, `cotas_pendencia`, `cotas_aviso_publico`, script novo |
| **Rio do Sul** | 4,50 / 5,50 / 6,50 na Dom Tito Buss; revistas em 15/08 e 31/08 | O mesmo, da API, 03/09 | Igual. Registrada a volatilidade, datada | `cotas_pendencia`, `cotas_aviso_publico` |
| **Timbó** | Quatro faixas no Benedito (ND Mais 31/08): 2,01 / 3,01 / 4,30 | Só o gatilho do PLANCON, 5,00 m | Imprensa citando a COMPDEC, régua não nomeada: **não pinta**, mas a tela avisa | `cotas_pendencia`, `cotas_aviso_publico` |
| **Guabiruba** | Estação no Rio Guabiruba, não no Mirim | O validador já sabia: pino a 4,24 km do Mirim (`LONGE_ACEITO`) | Duas fontes concordam. Instrução de cadastro | `cotas_ressalva`, `cotas_aviso_publico_nao_precisa` |
| **Ituporanga** | Ferramentas 2026; 3,25 m "primeira cota crítica" (rádio) | Escala estadual de OUTRA régua; `cotas_m` vazio de propósito | Dois My Maps lidos pelo Jefferson (abaixo). **Nenhum traz faixa**; `cotas_m` segue vazio | `cotas_pendencia` |
| Vidal Ramos | Sem documento; 3,5 m é imprensa | Idem, e a armadilha do Salseiro | Nada novo | — |
| Botuverá | Sem documento; 7,5 m é imprensa | Idem | Nada novo | — |
| Ascurra | Cota conhecida é da Travessa Zonta (Ribeirão São Paulo) | Idem, com ressalva | Nada novo | — |
| Lontras | 9,20 m "cota de segurança" (2022), imprensa | Idem | Nada novo | — |
| Trombudo Central | Sem documento | Idem | Nada novo | — |

---

## As três verificações do Jefferson (08/09/2026, à noite)

### 1. Asthon: rota fechada

`stations/live?city_id=` devolve **null** para Vidal Ramos (4219101), Botuverá
(4202453), Guabiruba (4206652), Ascurra (4201158), Lontras (4209904), Timbó
(4218004), Trombudo Central (4218707), Ituporanga (4208906), Gaspar, Ilhota e
Blumenau, com os códigos IBGE corretos. Nenhuma é cliente da plataforma. A régua
de Vidal Ramos só existe ali pendurada no `city_id` de Rio do Sul, e continua sem
`band_thresholds` (já estava em `docs/API-ASTHON-COMPLETA.md`). **A recomendação
nº 2 do memorando está encerrada**: não há cota a colher por essa via, e a sonda
por `city_id` que eu ia escrever não foi escrita.

### 2. Gaspar: a régua não morreu

`defesacivil.gaspar.sc.gov.br/estacao/ver/21`: "Rio Itajaí Açu Gaspar", **1,12 m**,
FONTE: DC. GASPAR, última medição **08/09/2026 08:03**. Legenda: normalidade
< 5,00 m · atenção > 5,00 m ou chuva > 6,00 mm · emergência > 7,00 m — os
valores do Plano de Contingência. A estação saiu da listagem de
`/monitoramento/tabela` mas sobrevive na URL direta: o mesmo padrão da estação 31
(Salseiro) no portal de Brusque. A página oferece **"BAIXAR SÉRIE HISTÓRICA"**.

Duas ressalvas, do próprio Jefferson, antes de reapontar o coletor:

- **Cadência.** Às 21h a leitura era das 08:03 — 13 h de idade. Com `MIN_VELHA`
  de 180 min, ela não pinta a maior parte do dia. Se for leitura manual por
  turno, Gaspar ganha número e continua cinza quase sempre. Medir a cadência
  (várias consultas num dia) antes de dizer "voltou".
- **Rede.** O host segue sem responder à VPS. A página viva não é coletável de
  fora; o caminho é `coleta_gaspar.py --arquivo` com o HTML salvo no celular, e
  o parser foi escrito para a tabela — pode precisar de adaptação.

O que a série histórica baixável renderia: **picos de Gaspar com hora**, que
pareados com os de Blumenau (AlertaBlu, 5 min) dariam o segundo trecho do Açu
com tempo de trânsito medido, depois de Salseiro → Brusque.

### 3. Ituporanga: dois Google My Maps, nenhum com faixa

| Mapa | `mid` | Conteúdo | Ressalva |
|---|---|---|---|
| "Cotas de cheias ruas - Ituporanga" (Prefeitura, 07/10/2023) | `1o9xZ2BceCkPzaqQQ2m0HIn0ixHVOJcU` | 60 pontos de cota de rua, 3,38 a 10,48 m | um ponto de **27,77 m** é lixo (digitação ou altitude na coluna errada): descartar e avisar a DC |
| "Cotas com Manchas de Inundação" | `19tpP2Tfsl58ue6GtY5ihBfK3MLkiUrA` | 78.547 polígonos em 8 camadas, COTA 3,00 a 6,50 de meio em meio metro; 34 MB de KML | manchas por **cota**, não por evento — o equivalente ao FeatureServer de Itajaí em outra resolução |

Saem por `https://www.google.com/maps/d/kml?mid=<mid>&forcekml=1`.

⚠️ **O site da prefeitura linka o mapa de manchas pela URL `/edit`.** Se as
permissões estiverem abertas, o mapa oficial é editável por quem abrir o link.
Avisar a Defesa Civil, e **congelar um snapshot agora**, porque mapa editável muda
sem aviso e sem versão (comandos em `docs/pendencias-navegador-e-oficios.md`, A3).

O que isso **não** resolve: escala de atenção/alerta/emergência. Os três números
encontrados se cercam — primeira mancha 3,00 m, menor cota de rua 3,38 m, "primeira
cota crítica" 3,25 m (secretário de Planejamento, Rádio Educadora) — mas nenhum é
faixa de acionamento, e nenhum diz a régua. `cotas_m` segue vazio. Contato direto:
Defesa Civil de Ituporanga, coordenador Elias Sieves, (47) 9148-1378,
`ituporanga.sc.gov.br/secretaria/view/15/defesa-civil`.

As cotas de rua só entram em `cotas-ruas.json` quando se souber a régua delas: a
leitura ao vivo de Ituporanga é a DCSC-00039, em datum estadual bruto, com
`usar_para_cota: false`. Casar as duas seria a regra nº 1 quebrada.

---

## O que foi recusado do memorando, e por quê

1. **"Para Ilhota, exibir o nível ao vivo da régua de Gaspar com as cotas próprias
   de Ilhota."** É aplicar a cota de uma régua à leitura de outra. Gaspar fica a
   ~17 km; o limite do projeto para "mesma régua" é 1 km, e há teste travando isso.
   Se a COMPDEC de Ilhota opera pela leitura de Gaspar, a pergunta certa é *em que
   régua estão os 9,20 / 10,00 / 10,50* — e ela vai no ofício, não na tela.
2. **"Publicar já Timbó (2,01 / 3,01 / 4,30)."** É imprensa citando a COMPDEC, sem
   nomear a régua, numa cidade com três réguas. Vai à tela como **aviso em
   texto**, que avisa mais cedo sem fingir que é cota cadastrada.
3. **"Publicar já Blumenau (cinco estágios)."** Provavelmente certo, e por isso
   mesmo não foi feito no escuro: trocar um número não conferido por outro não
   conferido é o mesmo erro com o sinal trocado. A sonda resolve em um minuto
   na VPS; até lá a tela avisa que o AlertaBlu pode avisar antes.

## O que o memorando confirma sem mudar nada

Vidal Ramos, Botuverá, Ascurra, Lontras e Trombudo Central: o repositório já
tinha as mesmas pistas de imprensa, com a mesma classificação (não é cota), e as
mesmas pendências de ofício. Guabiruba: o validador já tinha achado sozinho que a
cidade fica no ribeirão, em 05/09; agora há uma segunda fonte.

## Agregadores citados (referência cruzada, nunca fonte)

`deolhonorio.riodosulmilgrau.com.br` e `nivelrio.com.br` republicam cotas por
régua e leituras da EPAGRI para estas cidades, renderizadas por JS. Nenhum
publica o zero da régua. Servem para conferir o que a fonte oficial diz, não
para substituí-la — e não entram em `fontes_tempo_real`.

---

## Resultado, mais tarde em 09/09/2026: Blumenau conferido e trocado

O Jefferson rodou `conferir_faixas_blumenau.py` na VPS. O JSON oficial
(`static/data/nivel_oficial.json`, fonte "AlertaBLU") publica em `condicoes`:
Normalidade 0 · **Observação 3** · **Atenção 4** · **Alerta 6** · **Alerta Máximo 8** m,
todas `tipo: nvl`. Leitura da meia-noite: 2,68 m (normalidade). Bruto em
`data/brutos/blumenau-alertablu-nivel-oficial-sem-serie-2026-09-09.json`.

Adotado no cadastro com as chaves que a tela já pinta — Observação →
`monitoramento` (como Taió), Alerta Máximo → `emergencia` (o topo) — e os
6,00 / 6,50 / 7,40 foram para `cotas_divergencias` com o que se sabe da origem
(nada, além de 7,40 coincidir com a menor cota de rua). O aviso público de
Blumenau saiu: a tela agora pinta pela escala oficial. A linha 3 de "O que foi
recusado" acima está resolvida do jeito que dizia: com a fonte, não no escuro.

**Pintou?** Sim: com o rio a 2,68 m nada muda de cor hoje, mas a partir de 3 m
Blumenau passa a mostrar Observação, e a 4 m Atenção — onde antes ficava
"normal" até 6 m.
