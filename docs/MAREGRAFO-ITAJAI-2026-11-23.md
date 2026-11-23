# Marégrafo de Itajaí (Cabeçudas Iate Clube) no portal da Defesa Civil — levantamento de 23/11/2026

Origem: o Prof. Mauro Michelena Andrade (UNIVALI) avisou por e-mail, em 06/11/2026, que o marégrafo está on-line em
`https://monitoramento.defesacivil.itajai.sc.gov.br/monitoramento/maregrafo`. Este documento é só o levantamento.
**Nada foi ligado ao site, ao chat nem aos avisos.** Usar o número na tela é decisão do Jefferson (regra "Maré medida"
do `CLAUDE.md`: "Entrada nova só com a fonte escrita, por decisão do Jefferson").

## 1. Acesso

- `robots.txt` do host: `User-agent: *` / `Disallow:` (vazio). Nada proibido. Conferido em 23/11/2026 12h33 UTC.
- É o mesmo host que `scripts/coleta_itajai_portal.py` já lê para as réguas DC-01 a DC-11.
- A página é Inertia, igual à de rios: os dados vêm no `data-page` do `<div id="app">`, em `props.maregrafo`. O código
  da página (`build/assets/app-B7cqiFle.js`) não chama endpoint de API para a maré. Ela se recarrega a cada 5 min
  pedindo só `maregrafo` e `consultadoEm`.
- Nenhum endereço foi presumido. A página de rios continua em `/monitoramento/rios`, e a tábua mensal em
  `/monitoramento/mares` (`props.tabuaMare`, "Publicação mensal da Defesa Civil de Itajaí").

## 2. O que a página traz

`props.maregrafo`, lido em 23/11/2026 12h33 UTC:

| Campo | Conteúdo |
|---|---|
| `id`, `nome` | `MRG01`, "Cabeçudas Iate Clube" |
| `leituras` | 144 leituras, **de 10 em 10 min, 24 h**. `datahora` em **UTC com `Z`** (`2026-11-23T12:30:01.874Z`). Última com 4 min de idade. |
| `leituras[].nivel_bruto` | distância do sensor até a água (ver §3) |
| `leituras[].altitude_ortometrica` | 2,838 m (constante) |
| `leituras[].nivel_ibge` | nível da água na referência do IBGE |
| `leituras[].nivel_reducao` | 0,4455 m (constante) |
| `leituras[].nivel_dhn` | nível da água no zero da DHN (nível de redução) |
| `previsoes` | 864 pontos, **de 5 em 5 min, 3 dias**, `datahora` com **`-03:00`**, só `nivel_dhn` |
| `cotas` | `muito_muito_alto` 1,75 · `muito_alto` 1,44 · `alto` 1,30 · `baixo` −0,50 · `muito_baixo` −1,00 m, **iguais nas três referências** e com `habilitado: false` |
| `leituras_indisponiveis`, `cotas_indisponiveis` | `false` |

Rótulos da própria página: título "MRG01 - Iate Clube - Maré Medida e Maré Prevista (DHN)"; subtítulo "Maré observada ·
Leituras a cada 10 minutos · Histórico de 24 horas · Previsão de 48 horas"; série "Maré DHN Medida (m)"; rodapé
"Fonte: Parceria Defesa Civil Itajai / Univali". A hora na tela é convertida para `America/Sao_Paulo`.

## 3. As contas fecham

Nas 144 leituras, sem nenhuma exceção (diferença máxima 0,0000 m):

- `nivel_ibge = altitude_ortometrica − nivel_bruto`. O `nivel_bruto` é a **distância do sensor (a 2,838 m de altitude
  ortométrica) até a água**, como num sensor de radar, e não um nível;
- `nivel_dhn = nivel_ibge + nivel_reducao` (0,4455 m).

Em 24 h, o DHN foi de 0,31 a 1,51 m, e o IBGE de −0,13 a 1,07 m.

## 4. A previsão é a da UNIVALI, com altura no zero da DHN

Extremos da previsão do portal comparados com as duas tábuas do projeto:

| Previsão do portal | UNIVALI (`mare-itajai.json`) | Marinha (`mare-itajai-chm.json`) |
|---|---|---|
| 22/11 12h20 PM 0,96 m | 12h25 (+5 min) | 12h47 0,96 m (+27 min, Δh +0,00) |
| 22/11 19h25 BM 0,20 m | 19h20 (−5 min) | 19h40 0,21 m (+15 min, Δh −0,01) |
| 23/11 00h55 PM 1,16 m | 00h55 (0 min) | 01h06 1,15 m (+11 min, Δh +0,01) |
| 23/11 07h30 BM 0,16 m | 07h35 (+5 min) | 08h04 0,21 m (+34 min, Δh −0,05) |
| 23/11 13h00 PM 0,96 m | 13h05 (+5 min) | 13h19 0,94 m (+19 min, Δh +0,02) |
| 23/11 20h05 BM 0,15 m | 20h05 (0 min) | 20h19 0,15 m (+14 min, Δh +0,00) |
| 24/11 01h35 PM 1,20 m | 01h40 (+5 min) | 01h51 1,17 m (+16 min, Δh +0,03) |
| 24/11 08h30 BM 0,24 m | 08h30 (0 min) | 09h06 0,25 m (+36 min, Δh −0,01) |

- **Horário:** bate com a UNIVALI em até 5 min, que é o passo das duas séries. É a mesma previsão harmônica, ou uma
  gêmea. O atraso da Marinha (+11 a +36 min) repete o cruzamento de 2026 (`docs/TABUA-UNIVALI-2026.md`).
- **Altura:** bate com a tábua da Marinha, que é referida ao nível de redução da DHN, em até 5 cm. Isso dá evidência
  de que o `nivel_dhn` do portal está no **zero da DHN**.

Até agora, a planilha da UNIVALI não declarava referência vertical, por isso `mare-itajai.json` só tem horário e
`_meta.referencia_altura` é `null`. O portal é uma fonte escrita (título "(DHN)", campo `nivel_dhn`) da mesma parceria
que dá a altura nesse zero. Trocar o `null` continua sendo decisão do Jefferson, com a fonte citada.

## 5. Observado × previsto

Nas 144 leituras de 22/11 12h40 a 23/11 12h30 UTC, a **diferença entre nível observado e maré astronômica prevista**
(DHN) ficou entre +0,09 e +0,37 m, com média de +0,23 m. O período teve chuva e rios subindo no vale.

Pela regra do `CLAUDE.md`, essa diferença nunca é chamada de "maré meteorológica" nem atribuída só a vento e pressão.
O Iate Clube de Cabeçudas fica na foz do Itajaí-Açu, então em cheia a diferença tem a água do rio dentro.

## 6. O que serve e o que não serve

| Item | Situação |
|---|---|
| Nível medido no zero da DHN, de 10 em 10 min | **Serve**, com horário, estação, unidade e referência escritos na fonte |
| Nível no IBGE | Serve como dado. A tela do portal só mostra o DHN; usar o IBGE pede a mesma decisão |
| `nivel_bruto` | **Não é nível**: é a distância do sensor |
| Previsão de 3 dias em DHN | Serve para conferir a tábua da UNIVALI e para a diferença observado − previsto da mesma estação |
| `cotas` | **Não servem**: `habilitado: false` e os mesmos números nas três referências |

Comparado com o CIRAM (`coleta_mare_ciram.py`, estação de Balneário Camboriú): este marégrafo fica **na foz, em
Itajaí**, e a referência está escrita. No CIRAM, `REFERENCIA_VERTICAL` segue vazia e a tela diz "referência pendente".

## 7. Decisões que ficam com o Jefferson

1. Ligar um coletor deste marégrafo (leitura da página, no mesmo padrão do `coleta_itajai_portal.py`, só GET, com
   `User-Agent` do projeto, uma vez por publicação) e mostrar a maré medida em `/itajai` no lugar do CIRAM, ou ao lado.
2. Registrar a altura da tábua da UNIVALI no zero da DHN a partir desta fonte.
3. Mostrar a diferença observado − previsto da mesma estação, com o nome da regra.

A orientação de **não enviar ofício a Itajaí** continua valendo. Este levantamento só leu a página pública.
