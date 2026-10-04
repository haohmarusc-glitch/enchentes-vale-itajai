# Rodada 6 da varredura "o que falta para pintar" — 03/10/2026

A busca externa feita em 03/10/2026 ficou em `data/brutos/varredura-pintar-2026-10-03/`: 51 originais, o
manifesto e o relatório. Os 51 sha256 conferem. Abaixo vão os trechos que mudam alguma decisão, **relidos
nos originais** em 04/10/2026, e a proposta por cidade.

**Nada entrou em `estacoes.json`, `enchentes.json` nem no coletor.** Cada proposta espera a decisão do
Jefferson. A regra nº 1 continua: cota só pinta amarrada à mesma régua da leitura.

## Ibirama — a leitura tem vínculo escrito; a escala vigente é a dúvida

### Conferido nos originais
- **Decreto nº 5.431/2024, que homologa o PLAMCON, p. 11.** A tabela "NÍVEL DO RIO ITAJAÍ DO NORTE¹" traz
  "3,00m – OBSERVAÇÃO / 3,50 m - ATENÇÃO / 4,00 m - EMERGÊNCIA". A nota 1 diz: "Dados provenientes da
  Estação Hidrometeorológica da Defesa Civil de Santa Catarina, localizada na ponte Prefeito Osvaldo Tadeu
  Beltramini". A p. 9 lista a mesma estação como a fonte de monitoramento.
- **Decreto nº 5.824, de 11/12/2025.** Homologa um "PLAMCON 2025", que "passa a vigorar a partir da
  publicação". O decreto tem uma página só, sem anexo, e o texto do plano de 2025 não foi achado.

### Conferido na nossa coleta
- **O número do boletim municipal é o da DCSC-00020.** Às 22h46 de 11/09/2026 a estação marcava **4,04 m**.
  O boletim municipal das 22h45 também dá 4,04 m. Esse número está no e-mail a Ibirama de 13/09, que cita
  ainda 1,73 × 1,73 m em 14/08 e 3,57 × 3,56 m em 01/09.
- **Mas o boletim chamou 4,04 m de "atenção".** Pelo plano de 2024, 4,00 m já é emergência. A escala em uso
  em setembro de 2026 não é a de 2024, e o mais provável é que tenha mudado no PLAMCON 2025.
- **Hoje o site mostra Ibirama em "Atenção · Defesa Civil SC" quase o tempo todo.** Desde que a coleta passou
  a ler a faixa estadual (13/09), a DCSC classifica a DCSC-00020 como "atenção" entre 2,17 e 2,98 m (1.840
  leituras) e como "alerta" a partir de 3,00 m. Nenhuma leitura foi "normal". Pelo plano municipal de 2024,
  abaixo de 3,00 m o rio está normal.

### O que isso resolve e o que não resolve
- **Resolve o vínculo da leitura.** É prova escrita do município, num decreto publicado no Diário Oficial,
  de que o nível monitorado é o da estação estadual na ponte Beltramini. Isso cabe na regra atual de
  `REGUAS_COM_COTA_PROPRIA` ("prova escrita da COMPDEC").
  - Falta uma conferência: que a DCSC-00020 é a estação da ponte Beltramini. O cadastro liga a DCSC-00020 a
    Ibirama por coordenada, e o PLAMCON não escreve o código.
- **Não resolve a escala.** O boletim de 11/09 contradiz os números de 2024, e o plano de 2025 não está
  publicado.

### Proposta (não aplicada)
**Recomendação:** pedir a Ibirama só a tabela do PLAMCON 2025, como lembrete do e-mail de 13/09. Ao chegar,
pintar com ela. Se o Jefferson preferir não esperar, este é o conjunto com a escala de 2024.

**`data/estacoes.json`, Ibirama**
- `cotas_m`: `{"monitoramento": 3.00, "atencao": 3.50, "emergencia": 4.00}`. Sai de `cotas_pendentes_de_vinculo`.
- `cotas_nomes_na_fonte`: `{"monitoramento": "Observação", "_por_que": "O PLAMCON chama de OBSERVAÇÃO a fase de 3,00 m. Entrou como monitoramento, como em Blumenau; a tela escreve o nome do plano."}`
- `regua_das_cotas`: `"DCSC-00020 — Estação Hidrometeorológica da Defesa Civil de SC na Ponte Prefeito Osvaldo Tadeu Beltramini"`
- `regua_das_cotas_fonte`: `"PLAMCON de Ibirama, Decreto nº 5.431/2024, p. 11, nota 1: 'Dados provenientes da Estação Hidrometeorológica da Defesa Civil de Santa Catarina, localizada na ponte Prefeito Osvaldo Tadeu Beltramini' (data/brutos/varredura-pintar-2026-10-03/Ibirama_Decreto-5431-2024_PLAMCON.pdf). Pares boletim municipal × DCSC-00020: 11/09/2026 22h45, 4,04 × 4,04 m."`
- `cotas_pendencia` e `cotas_aviso_publico` têm de ser reescritos. Hoje dizem que o vínculo não está
  confirmado. O novo texto diz que a escala pode ter mudado no PLAMCON 2025.

**`scripts/coleta_estadual_com_cota.py`**: entrada `"DCSC-00020"`, com cidade `ibirama` e a fonte acima.

**Efeito, contado na coleta de 02/09 a 03/10, com a escala de 2024**
| Faixa | Leituras |
|---|---:|
| Normal | 2.821 |
| Observação (3,00) | 109 |
| Atenção (3,50) | 37 |
| Emergência (4,00) | 28 |

- O bot avisaria 10 vezes.
- O selo "Atenção · Defesa Civil SC" some, porque a faixa municipal manda.
- **Risco desta opção:** em 11/09 o site diria "emergência" a 4,04 m enquanto o boletim da cidade dizia
  "atenção". Por isso a recomendação é esperar a tabela de 2025.

## Ilhota — o PLANCON não liga as faixas a régua nenhuma

### Conferido no original (`Ilhota_PLANCON_2025-2028_v016.pdf`)
- **p. 15:** "O monitoramento do nível do Rio Itajaí, em Ilhota, será feito pela COMPDEC, através da leitura
  da régua instalada junto a ponte". A página não nomeia a ponte.
- **p. 16:** "De zero a Nove Metros e Vinte Centímetros: rio dentro da calha principal, estado normal. De Nove
  metros e Vinte Centímetros a Dez metros: represamento dos ribeirões, não é passado aviso para população,
  estado de atenção."
- **p. 21:** "Elaborar a Carta de Cheias, com base nas medições da Estação Hidrometeorológica localizada na
  Ponte Cláudio Jeremias Cadorin". Isso está numa tarefa da Secretaria de Planejamento, não junto das faixas.

### Leitura
- O plano não diz que as faixas são lidas na estação da ponte Cadorin, nem dá o zero.
- A hipótese do relatório: em 2013 a prefeitura escreveu que não tinha régua e usava "10 m em Blumenau"
  como gatilho. O "dez metros" do plano pode ter a mesma origem. É hipótese, não conclusão.
- Somado ao que a varredura de 04/10 mediu (89 % de setembro acima de 9,20 m na DCSC-00030, e o painel dos
  bombeiros misturando altitude de rua com a régua), **a recomendação de esperar o C11 fica mais firme.**
  A pergunta do C11 atualizado continua sendo a que falta.

## Timbó — um terceiro par, e um sinal de que a escala mudou em 2026

### Conferido nos originais
- **O Auditório, 13/10/2023:** "O nível do Rio Benedito em Timbó atingiu o pico de 7,46m às 21h desta
  quinta-feira (12)". O Boletim 010/2023 do SDE dá "Timbó 7,46 — 12/10/2023 21:00 — Emergência" para a
  estação da DCSC. A tabela do boletim é imagem: a leitura é do relatório, não conferida em texto.
  Com os dois pares de 12/09/2026, são três pares em que o número divulgado é o da DCSC-00023.
- **Misturebas, 31/12/2025:** "Por volta das 3h30 … o equipamento de medição apontava 4 metros e 34
  centímetros, colocando os órgãos de monitoramento em **estado de atenção**".
  - Pela escala que a imprensa e a prefeitura divulgam em 2026, 4,34 m é alto risco (a partir de 4,30 m).
  - Ou a escala mudou entre dez/2025 e jul/2026, ou "atenção" foi usada em sentido solto.
  - É mais um motivo para o C27 perguntar a data da escala, além dos números.

### Proposta
Nada muda na proposta da varredura de 04/10. O vínculo da leitura ganha um terceiro par. O C27 deve citar
o 4,34 m de 31/12/2025 e perguntar desde quando vale a escala de 2026.

## Indaial — a prefeitura disse por escrito que a régua estadual não é a base

### Conferido no original (Olhar do Vale, 05/10/2023, comunicado da prefeitura)
"A Defesa Civil está utilizando para monitoramento do nível do Rio Itajaí-Açu a régua física, instalada nos
fundos da Celesc. A régua eletrônica do Governo do Estado, que fica na terceira ponte, ainda não foi feita
calibragem para alinhamento dos níveis de metragem, por isso não deve ser usada como base." A faixa
municipal é 3 / 4 / 5,5 m, a mesma do cadastro.

### O que isso muda
- Confirma, com palavra da prefeitura, o `usar_para_cota: false` da DCSC-00006.
- Traz leituras municipais novas, que podem virar pares se a série da DCSC-00006 de 2023 existir no servidor:
  - 5,27 m em 05/10/2023 às 08h;
  - 5,20 m em 07/10/2023 às 15h;
  - 5,00 m em 07/10/2023 às 14h.
- O 5,14 m de 04/05/2022 é de antes da estação estadual, instalada em 18/11/2022.

```
grep -E "^2023-10-05T0[78]:|^2023-10-07T1[45]:" /opt/enchentes-vale-itajai/data/series/dcsc/DCSC-00006.csv
```

Se a série de 2023 estiver lá, isso dá mais pares para a pergunta do C19 ("cerca de 2,43 m? constante?").

## Guabiruba — mais um indício da volta à régua local

### Conferido no original (Araguaia FM, publicado em 01/10/2026 às 13h40)
"Já em Guabiruba, o rio está em 1,02 metro, após pico de 1,27 metro." A fonte é a Defesa Civil de Brusque.

### O que isso muda (item 3 da auditoria de 03/10)
Se esse ponto da Defesa Civil de Brusque for a DCSC-00029, a estação já estava na régua local em 01/10/2026.
A janela da volta encolhe de "09/09 a 03/10" para "09/09 a 01/10". Não está escrito que é a mesma estação. O
comando de leitura no servidor (`docs/PROPOSTAS-AUDITORIA-2026-10-03.md`, item 3) continua sendo o que decide.

## Rio dos Cedros — escala confirmada no plano vigente

### Conferido no original (Plano de Contingência v10.9, abr/2026)
- **p. 9:** "De zero a 4,80 metros … estado normal. De 4,80 a 5,30 metros … ESTADO DE ATENÇÃO" e a tabela
  "5,70 Alarme / 5,30 Alerta / 4,80 Atenção / Abaixo Normal".
- **p. 4:** a sede de operações é o Paço Municipal pela "proximidade da régua de medição".

### Proposta (texto de fonte, decisão do Jefferson)
- O `fonte_cotas` de Rio dos Cedros cita o "PLANCON ~10.7, 2022". Pode passar a citar o Plano v10.9 de
  abr/2026, p. 9, com o original em `data/brutos/`. Os números não mudam.
- O vínculo com a DCSC-00011 continua sem prova.
- **O 8,96 m de 2014:** está em `enchentes.json` com data 2014-06-08. Pelo cruzamento de valores do relatório,
  se a sequência de 15 em 15 minutos começa em 07/06 às 18h30, o 8,96 cai na madrugada de 09/06. É
  consistência de valores, e o PDF não escreve o dia. Fica para a decisão do Jefferson, ou para uma pergunta à
  Defesa Civil de Rio dos Cedros.

## Trombudo Central — os 8,71 m não são da régua municipal

- **Pelo relatório**, sem reler o áudio ou a matéria: a prefeita disse em 17/11/2023 que a régua "só tem até
  6,15 metros", e que no dia anterior deu 5,36 m.
- **No SDE:** o Boletim 011/2023 dá "Trombudo Central 8,71 — 17/11/2023 18:00 — Emergência" para a estação da
  DCSC.
- **O que isso indica:** o pico de 8,71 m de `enchentes.json` (17/11/2023 17h, notícia da prefeitura) e a
  `inundacao_historica` de 8,71 m do cadastro devem ser da estação estadual. É a DCSC-00035, ligada a Trombudo
  na varredura de 04/10. Não são da régua municipal.
- **Proposta:** nota no registro e no cadastro dizendo isso. A `referencia` continua ausente e nada pinta.

## Sem mudança
- **Ituporanga:** o manual de barragens da SDC confirma o que o cadastro já diz. As faixas 1,4 / 1,9 / 2,6 m
  são da ANA 83250000, e o monitoramento oficial é por ela.
  - Há um par no mesmo horário: em 24/05/2024 às 05h00, a ANA dá 276,00 e a DCSC dá 3,54 m.
  - O campo da ANA vem sem unidade e não foi convertido.
- **Botuverá:** o plano da Saúde (ago/2023) dá 3 / 4 / 6 m sem nomear a régua. Em 31/08/2026 há três escalas
  em conflito: 3,87 m "normalidade" (Defesa Civil de Botuverá), 4,86 m "atenção" (Defesa Civil de Brusque) e,
  no SDE, 3,58 m "Emergência" (dez/2023). Nada a aplicar.
- **Lontras, Vidal Ramos, Apiúna:** só limites do SDE e leituras sem régua. Nada a aplicar.

## Contatos novos para os ofícios (de páginas oficiais salvas)
- **Apiúna:** Defesa Civil defesacivil@apiuna.sc.gov.br e WhatsApp (47) 98809-3007. O e-mail de 13/09 foi para
  gabinete@apiuna.sc.gov.br. Vale reenviar para a Defesa Civil.
- **Vidal Ramos:** Defesa Civil (47) 99721-9870 e defesacivil@vidalramos.sc.gov.br, coordenador Francisco de
  Assis Velho Junior. Os horários estão na página salva.
- **Lontras:** Defesa Civil (47) 99130-8481.
- **Ilhota:** Defesa Civil (47) 3343-0181.
- **Brusque:** Defesa Civil (47) 4042-0605 / 4042-0606, e WhatsApp só para mensagem, (47) 98873-1843. Foi
  lido por serviço de busca, sem original.

## O que espera decisão do Jefferson
1. **Ibirama:** esperar a tabela do PLAMCON 2025 (recomendado) ou pintar já com a escala de 2024.
2. **Timbó:** incluir no C27 o 4,34 m de 31/12/2025 e a pergunta sobre a data da escala.
3. **Indaial:** rodar o `grep` no servidor para tentar pares de 2023.
4. **Rio dos Cedros:** atualizar a fonte das cotas para o plano v10.9, e a data do 8,96 m de 2014.
5. **Trombudo Central:** nota de que os 8,71 m são da estação estadual.
6. **Apiúna:** reenviar o pedido de 13/09 para o e-mail da Defesa Civil.
