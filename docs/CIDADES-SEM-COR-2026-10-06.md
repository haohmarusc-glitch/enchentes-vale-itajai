# Cidades sem cor no Monitor (06/10/2026)

O Jefferson auditou as 19 cidades do Monitor em 05/10/2026, por volta das 23h50. Este relatório responde à
auditoria com o que o código mostrou.

## O que separa as cidades

A cor do pino tem três origens, e a tela as confundia:
- **municipal:** leitura da régua das cotas, recente, comparada com as cotas da cidade;
- **estadual:** a classificação que a própria Defesa Civil de SC publica para a estação estadual;
- **várias réguas:** Itajaí, sem faixa única.

A cor do trecho de rio e as camadas de inundação são outras coisas. Ibirama tem pino com cor estadual
e o Hercílio cinza **de propósito**: só o eixo pinta rio, e cor de uma estação não se estende a um trecho
sem vínculo (`afluenteEhCinza.test.ts`).

## Cidade por cidade

| Cidade | Motivo antes | Causa no código | O que mudou | Depende de fora |
|---|---|---|---|---|
| **Lontras** | "Faltam faixas…" | O coletor manda os 21.474.836 m da DCSC-00032 para `suspeitas` (> 30 m), e o site só lia `leituras` | O painel diz que a estação publicou 21.474.836,00 m, valor impossível para nível de rio, e que a leitura foi rejeitada (não vira zero nem faixa). Também diz, à parte, que faltam faixas | Faixas de acionamento e a régua municipal (equivalência com a DCSC-00032 não confirmada) |
| **Apiúna** | "Faltam faixas…" | O coletor descarta toda estação "(H)" antes de qualquer balde, e o site nunca via a DCSC-00178 | Ver "Apiúna", abaixo | Referência vertical da DCSC-00178 (C30, pendente) e faixas |
| **Indaial** | "Não há leitura com horário válido…" | A DCSC-00006 está em `sem_leitura` desde 02/10 17:22, e o site não lia esse balde | O painel diz que a estação estadual DCSC-00006 não publica nível desde 02/10. Diz também que não há leitura da régua das cotas (fundos da Celesc) | Fonte de leitura da régua da Celesc |
| **Gaspar** | "Não há leitura com horário válido…" | O arquivo de agora não traz Gaspar, mas a série tem a última leitura | O painel diz "A última leitura recebida é de … (1,92 m): antiga demais para calcular a cor". Leitura velha mostrada no painel sai com a hora da medição. A janela de 3 h não mudou | Coleta da estação 21 voltar |
| **Ilhota** | "Há medição estadual abaixo, mas não há vínculo confirmado…" | Correto. A ressalva do bruto afirmava "zero diferente" sem documento | Fica o motivo. A ressalva passou a "a referência vertical não está validada para as cotas municipais acima" | Documento que ligue a DCSC-00030 às cotas 9,20/10,00/10,50 m |
| **Guabiruba** | Motivo de "vínculo", sem cota nenhuma | O motivo falava de vínculo com cotas que a cidade não tem | "Faltam faixas de acionamento… A medição estadual aparece só como número, sem classificação." Sem "zero diferente" | Faixas documentadas |
| **Ibirama, Botuverá** (estadual ATENÇÃO) | "Sem cota de referência cadastrada — a faixa fica cinza" sob um chip ATENÇÃO; a ressalva dizia que o bruto "não é comparável à faixa de cor deste pino" | Os textos eram fixos | "Sem cota municipal cadastrada. A cor do pino é a classificação que a Defesa Civil de SC publica." A ressalva diz que a cor é a classificação da própria rede | Faixas municipais (Ibirama: PLAMCON 2026) |
| **Ituporanga, Timbó, Trombudo Central, Vidal Ramos** (estadual NORMAL) | Igual ao caso de cima | Igual | Igual | Igual |
| **Rio dos Cedros** | Cotas cadastradas, cor estadual, ressalva contraditória | Ressalva fixa | A ressalva separa: a referência não está validada para as cotas acima, e a cor é a classificação estadual | Equivalência com a DCSC-00011 (não confirmada, decisão de 06/10) |
| **Itajaí** | Cotas por régua e, abaixo, "Sem cota de referência…" e "Faltam faixas…" | Os textos não sabiam de várias réguas | "Não existe uma faixa única da cidade… a cor não é a média nem a maior delas." O seletor de régua (PR #478) abre cada uma | — |
| Taió, Rio do Sul, Ascurra, Blumenau, Brusque | Faixa municipal | Sem defeito | Nada | — |

### Apiúna (DCSC-00178)

- **No cadastro:** `_topologia.nao_e_regua_de_rio` dizia que a coordenada "cai em área de mata sem curso
  d'água". Medida contra `data/rios/`, ela fica a **0,08 km do traçado do Açu**, então a frase não se confirma.
  A correção ficou anotada no mesmo campo. A estação **continua fora do eixo**: publica ~81 m, compatível com
  cota da superfície da água em referência altimétrica, mas sem referência documentada.
- **Coletor:** `scripts/coleta_nivel_sc.py` ganhou o balde `altimetricas` (`ALTIMETRICAS` em
  `cadastro_dcsc.py`), com o valor publicado e a ressalva. Nada dali vira leitura, série ou faixa.
- **Painel:** "A estação estadual DCSC-00178 publica cota altimétrica (81,17 m em …), não leitura de régua: a
  referência vertical não está validada, então o número não se compara com cota nenhuma."
- **Para aparecer no site,** falta atualizar o coletor na VPS (`scripts/deploy.sh`). Até lá, Apiúna continua
  só com "Faltam faixas…".

## Camadas

Com uma cidade escolhida, a caixa de camadas pedia para "selecionar a cidade no menu". Agora ela diz de qual
cidade são as camadas e só pede a escolha quando nenhuma cidade foi escolhida.

Os estados das camadas já estavam separados e não mudaram:
- sem área cadastrada;
- consulta só manual (Ituporanga);
- simulação abaixo da menor cota (Blumenau a 3,23 m, menor carta 8 m);
- referência estática (Ascurra, CPRM 2015);
- carregando, erro e desenhada.

## Como foi conferido

- **Código:** `logica/motivoSemCor.ts` (`motivoDaEstacaoEstadual` e os motivos que se somam),
  `logica/textosDoPainel.ts` (textos conforme a origem da cor) e `dados/nivelSc.ts` (`montarSituacoes` lê
  `suspeitas`, `sem_leitura` e `altimetricas`).
- **Testes:**
  - `textosDoPainel.test.ts` usa as linhas reais de `ultimo_nivel_sc.json` de 06/10 00:31 e cobre Lontras,
    Indaial, Apiúna, Ilhota, Guabiruba e Gaspar;
  - nenhum texto anuncia cinza sob cor estadual nem afirma "zero diferente";
  - `teste_coleta_nivel_sc.py` cobre o balde altimétrico.
- **Navegador:** Chromium, servindo o `tempo-real` publicado. Conferidos os painéis de Lontras, Apiúna (com o
  balde no arquivo), Indaial, Gaspar, Ilhota, Guabiruba, Ibirama, Itajaí e Rio dos Cedros.
- **Verificações que passaram:**
  - `npm test` e build;
  - trava do Monitor, fumaça e auditoria;
  - validador e testes dos scripts.

## Pendências que dependem de informação externa

- **Lontras:** faixas de acionamento e régua municipal. A DCSC-00032 publica valor impossível (código de falha
  do sensor, provavelmente; a causa técnica não está comprovada).
- **Apiúna:** referência vertical da DCSC-00178 (C30) e faixas.
- **Indaial:** leitura da régua dos fundos da Celesc.
- **Gaspar:** volta da coleta da estação 21.
- **Ilhota:** documento que ligue a DCSC-00030 às cotas.
- **Guabiruba:** faixas documentadas.
- **Ibirama:** tabela do PLAMCON 2026.
- **Áreas de inundação:** 15 cidades não têm área cadastrada. Desenhar só com polígono oficial, carta por cota
  ou evento histórico com fonte, nunca buffer do rio.
