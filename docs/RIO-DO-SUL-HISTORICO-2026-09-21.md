# Rio do Sul — Histórico de Cheias: os 77 registros da tabela municipal contra os 13 cadastrados (21/09/2026)

**Fonte:** página "Histórico de Cheias" do portal da Defesa Civil de Rio do Sul
(defesacivil.riodosul.sc.gov.br), tabela com Ano · Data do Pico · Nível (m) ·
Volume (mm) · Dias de Chuva. A página diz: *"Registro histórico das ocorrências
de enchente em Rio do Sul. O ano, mês e nível mais alto estão destacados em
vermelho."* e traz o nível "Normal 4,34 m".

**Captura:** `data/brutos/riodosul-historico-cheias-2026-09-21.html`, salva no
navegador pelo Jefferson em 21/09/2026, como veio (61 868 bytes, sha256
`522a847a…`). **Conversão:** `data/brutos/riodosul-historico-cheias-2026-09-21.json`,
gerada por `scripts/riodosul_historico.py --escrever`, com os 77 registros, os
avisos do validador e a reconciliação. **Referência altimétrica:** a página não
diz; `referencia: null`, como nos 13 já cadastrados.

**Regra desta etapa:** nada daqui entrou em `enchentes.json`. O script não
tem como escrever lá (teste trava), e o relatório abaixo existe para o Jefferson
decidir com inclusões, alterações e divergências na mão, como o "Plano seguro"
manda.

## O que a tabela é

| | |
|---|---|
| linhas | **77**, de out/1911 a jul/2024, todas válidas, **nenhum aviso** (sem duplicata exata, sem nível ausente, sem data ilegível, sem empate no mesmo ano) |
| com dia | só **4**: 13/10/2023, 17/11/2023, 18/05/2024, 12/07/2024 |
| só com mês | 73 |
| chuva (volume e dias) | de 1992 em diante; antes de 1984, `-` em todas (ausência, gravada como `null`, não zero) |
| maior | **jul/1983, 13,58 m**, 606,7 mm em 20 dias |
| picos por mês repetido | nov/2023 tem 4 linhas (13,04 · 8,33 · 8,20 · 6,77); out/2015 tem 3; jun/2014, ago/2011, out/2022, mai e jul/2024 têm 2 — são cristas distintas, não duplicatas |

O "~70 linhas" da pendência de 19/09 eram 77. E a transcrição à mão que produziu
o erro de 1911 (maio → outubro) e as datas de 2023 não se repete: a tabela entra
por script, com teste contra a captura.

## Reconciliação com `enchentes.json` (rio-do-sul)

| | |
|---|---|
| já cadastradas | **13 de 13** — todos os registros do JSON têm a sua linha na tabela, com o mesmo nível |
| cadastrados sem linha na tabela | 0 |
| com dia diferente | 0 (nov/2023: tabela 17, JSON 18 com `data_na_fonte` 17; out/2023: 13 nos dois) |
| candidatas a inclusão | **57** |
| segundo pico no mesmo mês de um cadastrado | **7** |

### Candidatas a inclusão, as maiores primeiro

| data | m | chuva | leitura |
|---|---|---|---|
| 1931-05 | 10,18 | — | maior das candidatas; sem chuva na fonte |
| 1927-06 | 10,00 | — | |
| 1966-02 | 10,00 | — | |
| 1961-11 | 9,75 | — | |
| 2014-06 | **9,42** | 152,6 mm / 6 d | bate com a camada de 2014 do ArcGIS de Itajaí; Atlas: inundação em 11/06/2014 (Registro, 1 016 desalojados) |
| 2022-05 | **9,34** | 165,0 mm / 2 d | Atlas: inundação reconhecida em 03/05/2022, 2 300 desalojados — era lacuna |
| 1972-08 | 9,15 | — | |
| 1933-09 | 9,12 | — | |
| 2001-10 | **9,10** | 159,5 mm / 12 d | Atlas: enxurrada em 01/10/2001, 2 885 desabrigados — era lacuna |
| 1948-10 | 9,00 | — | |
| 2024-05-18 | **8,97** | 175,4 mm / 3 d | com dia; Atlas: chuvas intensas reconhecida em 19/05/2024 |
| 1977-08 | 8,85 | — | |
| 2011-08 | 8,83 | 143,4 mm / 5 d | duas linhas em ago/2011 (8,83 e 8,76, esta com 344,2 mm em 17 dias) |
| 1939-08 | 8,80 | — | |
| 1950-10 | 8,75 | — | |
| 2011-08 | 8,76 | 344,2 mm / 17 d | |
| 1997-02 | 8,72 | 297,0 mm / 16 d | Atlas: inundação em 01/02/1997 — era lacuna |
| 1928-05 | 8,63 | — | |
| 2009-09 | 8,55 | 292,0 mm / 13 d | Atlas: enxurrada reconhecida em 28/09/2009 |
| 1992-05 | 8,52 | 295,1 mm / 12 d | |
| 1955-05 | 8,30 | — | |
| 1953-10 | 8,25 | — | |
| 1961-09 | 8,20 | — | |
| 2014-10 | 8,16 | 147,4 mm / 8 d | Atlas: inundação em 10/10/2014 |
| 1928-08 | 8,13 | — | |
| 1973-08 | 8,10 | — | |
| 1998-04 | 7,96 | 198,0 mm / 10 d | Atlas: inundação em 28/04/1998 |
| 1975-10 | 7,88 | — | |
| 2014-06 | 7,76 | 147,5 mm / 4 d | segunda linha de jun/2014 |
| 2005-09 | 7,64 | 234,3 mm / 19 d | |
| 2018-05 | 7,55 | 114,6 mm / 4 d | |
| 2010-04 | 7,53 | 254,0 mm / 7 d | Atlas: enxurrada em 27/04/2010 |
| 2024-07-12 | 7,49 | 51,4 mm / 2 d | com dia; Atlas: chuvas intensas em 08/07/2024 |
| 2022-10 | 7,47 | 76,8 mm / 3 d | Atlas: inundação em 10/10/2022 |
| 1969-04 | 7,45 | — | |
| 2024-07 | 7,39 | 70,8 mm / 2 d | segunda linha de jul/2024 |
| 1957-07 | 7,37 | — | |
| 2024-05 | 7,34 | 46,8 mm / 2 d | segunda linha de mai/2024 |
| 1997-10 | 7,33 | 247,0 mm / 22 d | Atlas: inundação em 11/10/1997 |
| 2023-07 | 7,30 | 92,2 mm / 3 d | Atlas: inundação em 13/07/2023 |
| 2015-09 | 7,23 | 70,4 mm / 2 d | |
| 1980-12 | 7,20 | — | |
| 1957-09 | 7,20 | — | |
| 2002-11 | 7,15 | 225,3 mm / 14 d | Atlas: enxurrada em 21/11/2002 |
| 1973-07 | 7,15 | — | |
| 1999-07 | 7,00 | 183,0 mm / 15 d | Atlas: inundação em 03/07/1999 |
| 1971-06 | 7,00 | — | |
| 2019-12 | 6,89 | 85,6 mm / 1 d | |
| 2004-09 | 6,89 | 110,3 mm / 4 d | |
| 2005-05 | 6,87 | 187,5 mm / 9 d | |
| 2007-11 | 6,76 | 142,9 mm / 12 d | |
| 2022-06 | 6,72 | 84,2 mm / 3 d | |
| 2016-10 | 6,68 | 131,0 mm / 4 d | |
| 2011-07 | 6,50 | 72,2 mm / 3 d | |
| 2020-09 | 6,46 | 50,2 mm / 1 d | |
| 2022-10 | 6,42 | 27,3 mm / 1 d | segunda linha de out/2022 |

As menções ao Atlas vêm de `data/desastres/correspondencias.json` (lacunas de
Rio do Sul) e são leitura minha, não pareamento automático: a tabela só dá o mês.

### Segundo pico no mesmo mês de um cadastrado (7)

| mês | cadastrado | também na tabela |
|---|---|---|
| nov/2023 | 13,04 (18/11) | 8,33 · 8,20 · 6,77 |
| out/2023 | 11,86 (13/10) | 7,78 |
| out/2015 | 10,71 | 8,75 · 7,24 |
| ago/1957 | 10,65 | 9,65 |

Não são alterações: o cadastrado continua sendo o maior do mês. São cristas
menores que o site hoje não mostra.

## O que isto muda no Atlas

Três lacunas grandes de Rio do Sul no Atlas têm pico na tabela municipal:
**mai/2022 (9,34 m)**, **out/2001 (9,10 m)** e **jun/2014 (9,42 m)**. A
quarta, **jul/2014** (6 498 desalojados no Atlas), **não tem linha na tabela**:
a tabela tem jun/2014 (9,42 e 7,76) e out/2014, não julho. Ou o decreto de
21/07/2014 se refere à cheia de junho com atraso, ou a tabela não registrou um
pico de julho. Fica anotado, sem inventar.

## Decisão que falta

Os 57 candidatos e os 7 segundos picos entram em `enchentes.json` **só com o
"sim" do Jefferson**, e entram por script (o conversor já produz `data`,
`pico_m`, `data_na_fonte`, `fonte` e `referencia: null`; `confianca: media`
como os 13 atuais, porque é tabela municipal sem estação nomeada). Opções que
ele pode escolher: (a) os 57 inteiros; (b) só os com chuva, de 1992 em diante,
que são os que a fonte parece ter medido em vez de compilado; (c) só os
≥ 8,00 m. Os 7 segundos picos podem entrar como registros próprios ou ficar
fora; a série do site mostra um pico por evento.

## A decisão, e a importação (21/09/2026, meio-dia)

Decisão do Jefferson, na íntegra:

- **Opção (a): os 57 candidatos entram**, sem corte em 1992 nem em 8 m. Os
  cortes seriam artificiais: a tabela municipal apresenta as 77 linhas como
  ocorrências históricas, e ausência de chuva antiga não invalida o pico.
- **Os 7 segundos picos não entram** agora. São ocorrências legítimas, mas
  quase todos só têm mês; `enchentes.json` exige unicidade por (rio, cidade,
  data), e incluí-los criaria registro duplicado ou exigiria inventar dia.
  Ficam preservados na conversão bruta, **nunca como `divergencias`**, porque
  são cristas diferentes.
- **Cinco colisões de mês dentro dos 57**: entra o maior pico do mês; o menor
  fica na camada bruta até existir dia exato ou identificador próprio.
- Resultado: **52 registros novos, Rio do Sul de 13 para 65**; **12 cristas
  preservadas e explicitamente pendentes**, sem perda nem data inventada.

### Como entrou

`riodosul_historico.plano_de_inclusao()` aplica a decisão à reconciliação e
grava o plano no JSON convertido (`plano_de_inclusao.entram` = 52,
`.pendentes` = 12, cada pendente com o motivo). `importar_riodosul_historico.py`
lê o plano e grava em `enchentes.json`: ensaio sem `--escrever`; idempotente
(rodar de novo diz "nada a gravar"); conflito de `pico_m` na mesma chave
aborta sem tocar em nada; nunca apaga. Cada registro novo diz na `nota` a
linha da tabela e a decisão; os cinco vencedores de colisão dizem qual foi o
outro pico do mês. Campos novos, registrados em `_meta.campos`: `chuva_mm` e
`dias_de_chuva`, só onde a fonte deu (de 1992 em diante).

| colisão | entrou | ficou pendente |
|---|---|---|
| jun/2014 | 9,42 m | 7,76 m |
| ago/2011 | 8,83 m | 8,76 m (344,2 mm em 17 dias) |
| out/2022 | 7,47 m | 6,42 m |
| mai/2024 | 8,97 m (18/05) | 7,34 m |
| jul/2024 | 7,49 m (12/07) | 7,39 m |

Os 12 pendentes: estes 5 e os 7 segundos picos (nov/2023 ×3, out/2023,
out/2015 ×2, ago/1957).

### O que mudou nos guardas do repositório

- **Validador:** 24 avisos novos, todos "rio-do-sul X não tem evento de
  indaial/blumenau no mesmo mês". Não é erro de data: a tabela municipal
  registra cheias de 6,4 m para cima, e as listas de Indaial (PDF da COMPDEC)
  e de Blumenau só trazem as grandes. Um pico de 7 m em Rio do Sul que não
  passou de "normal" a jusante não tem par. Cada um foi **nomeado** em
  `DESALINHADOS_CONHECIDOS` (`teste_validar_dados.py`), com esse motivo, para
  que um desalinhamento novo continue reprovando. Total: 13 → 37 avisos, 0
  erros.
- **Contagem de referências:** 219 → 271 registros; 131 sem referência
  (eram 79), e a maior fatia passou de Blumenau (41) para Rio do Sul (65), por
  uma causa só: a tabela não nomeia a régua.
- **Atlas:** o cruzamento foi refeito com 271 picos. Rio do Sul passou a ter
  1 confirmado (18/05/2024 × 19/05), 2 prováveis (18/11/2023; 12/07/2024 ×
  08/07), 19 prováveis por mês, 12 sem correspondência e 31 fora da cobertura.
  As lacunas de Rio do Sul caíram de 33 para 16; **jul/2014 (6 498
  desalojados) continua lacuna**, porque a tabela não tem julho de 2014.
