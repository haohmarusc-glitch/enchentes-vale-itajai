# Ofício pronto para envio — EPAGRI/CIRAM

Rascunhos complementares do bloco B1: [C15–C22](oficios-b1-c15-c22.md).

Contato preenchido: **Jefferson — (47) 98405-6082 · haohmarusc@gmail.com**

> **REGRA (02/10/2026): nunca pôr link do site em e-mail ou ofício.** O site só abre para e-mail cadastrado.
> Escrever, no lugar: "se quiser ver o site, basta me mandar o seu e-mail para cadastro". Ver `CLAUDE.md`.

Pronto para copiar e colar no e-mail. O texto-fonte, com a justificativa técnica de
cada pedido, e os demais ofícios (C1–C4) ficam em `docs/pendencias-navegador-e-oficios.md`.

---

## C5 — EPAGRI/CIRAM, Equipe de Hidrologia ✅ RESPONDIDO em 09/09/2026

> Resposta em `docs/RESPOSTA-EPAGRI-C5-2026-09-09.md`: sem acesso ao Rios On-line porque a rede
> telemétrica do litoral está sendo desmobilizada (fim até dez/2026); limiares não divulgados
> (sem revisão desde 2023); a divulgação passa à SDC; só quatro estações da bacia seguem ativas;
> Salseiro é de Vidal Ramos, com coordenada. Tabela de 19 estações anexa.

**Para:** sshidrosc@epagri.sc.gov.br
**Assunto:** Solicitação de acesso à API do Rios On-Line e à relação de estações da bacia do Itajaí-Açú

À Equipe de Hidrologia da EPAGRI/CIRAM,

Meu nome é Jefferson, sou morador da região do Vale do Itajaí e estudante de Engenharia de Software. Desenvolvo um site aberto e sem fins comerciais sobre as enchentes dos rios Itajaí-Açu e Itajaí-Mirim, que reúne o nível do rio em cada cidade, as cotas de referência e uma estimativa do tempo de chegada da cheia. O código e os dados são públicos (github.com/haohmarusc-glitch/enchentes-vale-itajai) e cada informação é apresentada com a fonte citada.

O Boletim de Monitoramento Hidrológico de vocês e o painel Rios On-Line são, de longe, o material mais completo que encontrei para as cabeceiras da bacia — Taió, Ituporanga, Vidal Ramos e Alfredo Wagner —, que são justamente as cidades para as quais eu tenho o nível do rio mas ainda não tenho a cota de referência que permitiria orientar a população. Duas coisas do painel me chamaram a atenção: ele publica o código da estação (que entendo ser o código da ANA) e classifica cada estação em faixas de situação (Atenção, Alerta e Emergência, para enchente e para estiagem). Essas duas informações são exatamente as que faltam ao meu projeto.

Gostaria de solicitar, se for possível:

1. A forma adequada de acessar os dados do Rios On-Line de maneira programática e estável — o painel consome um serviço que requer autenticação, e eu prefiro pedir o acesso correto a depender de uma solução frágil. Respeito integralmente qualquer limite de frequência ou termo de uso que vocês indicarem, e identifico todas as requisições com o nome do projeto.

2. A relação das estações da bacia do Rio Itajaí-Açú com o código da estação e as coordenadas geográficas de cada uma. Preciso das coordenadas para vincular com segurança cada estação de vocês à régua correspondente no meu cadastro, e não somar dados de réguas diferentes. Um caso que eu já consegui resolver mostra por que peço: a estação "Salseiro", em Vidal Ramos, que eu cheguei a supor ser a mesma régua que acompanho naquele município — o inventário público da ANA mostrou que estão a cerca de 6,8 km uma da outra e drenam áreas bem diferentes, ou seja, são estações distintas. Sem a coordenada eu não teria como saber, e o vínculo errado teria entrado no site.

3. Se estiverem disponíveis, os valores das faixas de Atenção, Alerta e Emergência (em centímetros de régua) de cada estação da bacia. É a informação que permitiria ao site dizer ao morador dessas cidades a partir de que nível o rio entra em cada faixa — hoje eu mostro o número, mas não tenho como qualificá-lo.

O site deixa claro em todas as páginas que não é sistema oficial de alerta, que não substitui a Defesa Civil nem os órgãos oficiais de monitoramento, e que em emergência se deve ligar 199. Os níveis de vocês são publicados em centímetros e assim seriam tratados, com o crédito à EPAGRI/CIRAM em cada dado utilizado.

Fico à disposição para qualquer esclarecimento e agradeço desde já a atenção.
Atenciosamente,
Jefferson — (47) 98405-6082 · haohmarusc@gmail.com

---

## C11 — Defesa Civil de Ilhota (COMPDEC) ✅ ENVIADO em 21/09/2026 09:16 BRT (Gmail, id 1a0c3e5126b896dd, para dpo@ilhota.sc.gov.br)

**Para:** dpo@ilhota.sc.gov.br · (47) 3343-8800 / 3343-0181 · Rua Leoberto Leal, 160, Centro, Ilhota-SC, 88320-438
**Assunto:** Em que régua estão as cotas do Plano de Contingência 2025/2028?

À Coordenadoria Municipal de Proteção e Defesa Civil de Ilhota,

Meu nome é Jefferson, sou morador da região e estudante de Engenharia de Software. Estou desenvolvendo, sem fins comerciais e ainda sem publicação, um site sobre as enchentes dos rios Itajaí-Açu e Itajaí-Mirim, que mostra o nível do rio em cada cidade e as cotas de referência de cada município, sempre com a ressalva de que não substitui a Defesa Civil.

O Plano de Contingência 2025/2028 de Ilhota (versão 016), na seção "Condições sobre o nível do Rio Itajaí", define **9,20 m** (atenção), **10,00 m** (prontidão) e **10,50 m** (emergência), e cita a estação hidrometeorológica da Ponte Cláudio Jeremias Cadorin. Em uma notícia de 2013 a Defesa Civil de Ilhota informava que não contava com régua própria e acompanhava a medição de Gaspar.

Tenho uma única dúvida, e ela decide se posso ou não mostrar essas cotas ao lado de um nível ao vivo:

**As cotas 9,20 / 10,00 / 10,50 m são lidas em qual régua — a de Gaspar, na Ponte Hercílio Deecke, ou uma régua em Ilhota (a da Ponte Cláudio Jeremias Cadorin)? E qual é o zero dessa régua?**

Pergunto porque a conta não fecha sozinha: a cota de emergência de Gaspar é 7,00 m, e se as cotas de Ilhota estivessem na régua de Gaspar, Ilhota só entraria em atenção com o rio 2,20 m acima da emergência de Gaspar. É possível, mas precisa estar escrito para não ser suposto.

Se a estação da Ponte Cadorin publicar leituras em algum endereço, agradeço a indicação. O site está em desenvolvimento e com acesso restrito; se desejarem acompanhá-lo, basta indicar um e-mail e eu libero o acesso, sem custo e sem cadastro.

Muito obrigado pelo trabalho de vocês.

Jefferson


### C11 — atualização de 04/10/2026 ✅ ENVIADA em 04/10/2026 por decisão do Jefferson (Gmail, id `1a104e1a1b02cd6c`, resposta na conversa de 21/09 com dpo@ilhota.sc.gov.br)

Resposta ao C11 ainda não chegou. Este texto vai como resposta na mesma conversa e pergunta só o que falta.
Envio é decisão do Jefferson. Sem link do site (regra de 02/10/2026).

**Assunto:** Re: Em que régua estão as cotas do Plano de Contingência 2025/2028?

À Coordenadoria Municipal de Proteção e Defesa Civil de Ilhota,

Retomo a mensagem anterior com uma pergunta mais simples, porque encontrei uma pista.

O painel dos Bombeiros Voluntários de Ilhota mostra a estação estadual **DCSC-00030** (Defesa Civil de SC)
com o aviso "Normal: até 9,20 m" e informa que as cotas são referenciais da COMPDEC.

**As faixas do Plano de Contingência, 9,20 / 10,00 / 10,50 m, são lidas na estação DCSC-00030, como o painel
dos bombeiros mostra?**

Se forem, uma segunda dúvida: na faixa de 9,20 a 10,00 m o plano diz que a COMPDEC monitora e não avisa a
população. Em setembro, a DCSC-00030 passou a maior parte do tempo um pouco acima de 9,20 m, oscilando com a
maré. Devo mostrar essa faixa como "represamento dos ribeirões", sem tom de aviso?

Se quiserem ver o site, basta me mandar o e-mail para cadastro.

Muito obrigado.

Jefferson
---

## C10 — Superintendência Municipal de Proteção e Defesa Civil de Gaspar

**Para:** defesacivil@gaspar.sc.gov.br
**Assunto:** Três dúvidas sobre os dados publicados no portal da Defesa Civil de Gaspar (régua do Itajaí-Açu, cotas de acionamento e histórico de enchentes)

À Superintendência Municipal de Proteção e Defesa Civil de Gaspar,

Meu nome é Jefferson, sou morador da região e estudante de Engenharia de Software. Estou desenvolvendo, sem fins comerciais e ainda sem publicação, um site sobre as enchentes dos rios Itajaí-Açu e Itajaí-Mirim, que reúne o nível do rio em cada cidade, as cotas de referência e uma estimativa do tempo de chegada da cheia. O código e os dados ficam no GitHub (github.com/haohmarusc-glitch/enchentes-vale-itajai), cada informação aparece com a fonte citada, e todas as páginas deixam claro que o site **não é sistema oficial de alerta** e não substitui a Defesa Civil — em emergência, 199.

Escrevo porque o portal de vocês é, de longe, o material mais completo que encontrei para Gaspar: as 1.617 cotas de rua, o histórico de enchentes desde 1852 e a tabela de monitoramento não têm equivalente nos outros municípios da bacia. Justamente por usar esse material com cuidado, cheguei a três dúvidas que só vocês podem responder.

**1. A régua do Rio Itajaí-Açu saiu da tabela de monitoramento, mas continua na página própria.**

Até 31/08/2026 a tabela em `/monitoramento/tabela` trazia a estação **"Rio Itajaí Açu Gaspar"** (naquele dia, 3,85 m às 22h59). Desde 07/09/2026 a tabela traz sete estações e nenhuma delas é o Itajaí-Açu: entraram as barragens Norte, Oeste e Sul, e a única estação de rio que restou é o Ribeirão Belchior Central. A página da estação, `/estacao/ver/21`, continua no ar e publicando (1,12 m em 08/09 às 08:03; 1,74 m em 10/09 às 05:53; 2,58 m em 10/09 às 19:07).

Gostaria de saber duas coisas: **a tabela deixou de ser a referência para o Açu, e a página da estação é o endereço a acompanhar?** E **qual é a cadência de atualização da leitura** — em 08/09, às 21h, a leitura mais recente era das 08:03, treze horas antes. Pergunto porque essa é a **única fonte de nível do Itajaí-Açu em Gaspar** que existe: a rede estadual (DCSC-00005) informa não medir nível de rio no município, e a estação da ANA em Gaspar (83840000) encerrou a escala em dezembro de 2021 sem substituta.

Aproveito para registrar uma observação técnica que pode ser útil: a série de 12 horas do Ribeirão Belchior Central publica **0,00 em todos os pontos** (consulta de 07/09/2026, das 03h28 às 15h18). Como 0,00 é um número válido, um sistema que leia essa página pode interpretá-lo como "ribeirão seco" em vez de "sem leitura".

**2. Cotas de atenção diferentes, nas publicações de vocês e entre consultas.**

O Plano de Contingência (item 4.2.3, fluxograma "MONITORAMENTO RIO ITAJAÍ AÇU", p. 25) trabalha com **atenção a partir de 5,00 m**. A legenda da estação 21, no próprio portal, mostrou **6,00 m** em 03/09/2026 e **5,00 m** em 08/09/2026 (atenção acima de 5,00 m ou chuva acima de 6,00 mm; emergência acima de 7,00 m). E em 10/09/2026, às 05:53, com o rio em **1,74 m**, a página informava "situação de **ALERTA**" — uma faixa que não aparece na legenda.

Adotei os 5,00 m, por ser o que avisa mais cedo, e deixei os 6,00 m registrados ao lado como divergência. Gostaria de confirmar **qual é o gatilho vigente** e **o que significa "ALERTA" a 1,74 m** (o gatilho de chuva?), porque a diferença é operacional: a primeira rua do cadastro de vocês alaga a 6,20 m, então a atenção a 5,00 m dá 1,20 m de margem e a 6,00 m dá 20 cm.

**3. A referência de nível do histórico de enchentes.**

A página `/enchentes` traz 70 registros, de 29/10/1852 a 12/10/2023, com data de início e metragem máxima. Não encontrei, em nenhum lugar do portal, a **referência de nível** dessas medidas — a que régua ou zero elas se referem.

Levanto a hipótese de que seja a mesma do levantamento de cotas de rua (o estudo do CEOPS/FURB coordenado por Ademar Cordeiro, que declara referência à régua da ANA na empresa Círculo), porque a menor cota de rua do cadastro é **6,20 m** e o menor registro do histórico é **6,19 m** — um centímetro de diferença, o que sugere que a lista registra as cheias que efetivamente alagaram. **É só uma hipótese**, e prefiro confirmá-la a supor.

**4. Onze registros do histórico cuja data não fecha com as cidades vizinhas.**

Esta é a que mais me deixou em dúvida, e por isso deixei os registros de fora do meu banco em vez de publicá-los.

Cruzando o histórico de vocês com o de Blumenau e Indaial, 48 dos 70 registros batem com um evento conhecido no mesmo dia ou no dia seguinte — o que é esperado, porque a cheia desce de Blumenau a Gaspar em poucas horas. Mas onze registros não batem com evento nenhum, e todos eles **batem exatamente se o ano for o da linha imediatamente acima na tabela**:

| Publicado por vocês | Metragem | Com o ano da linha acima | Evento conhecido |
|---|---|---|---|
| 31/10/1950 | 6,96 m | 31/10/1953 | Blumenau, 01/11/1953 (9,65 m) |
| 17/10/1948 | 8,85 m | 17/10/1950 | Blumenau, 17/10/1950 (9,45 m) |
| 17/05/1943 | 7,77 m | 17/05/1948 | Blumenau, 17/05/1948 (11,85 m) |
| 03/08/1939 | 8,43 m | 03/08/1943 | Blumenau, 03/08/1943 (10,50 m) |
| 27/11/1935 | 8,57 m | 27/11/1939 | Blumenau, 27/11/1939 (11,45 m) |
| 04/10/1932 | 7,49 m | 04/10/1933 | Blumenau, 04/10/1933 (11,85 m) |
| 18/06/1927 | 9,20 m | 18/06/1928 | Blumenau, 18/06/1928 (11,76 m) |
| 09/11/1926 | 7,24 m | 09/11/1927 | Indaial, 09/11/1927 (6,55 m) |
| 14/01/1925 | 7,80 m | 14/01/1926 | Blumenau, 14/01/1926 (9,50 m) |
| 14/05/1923 | 6,89 m | 14/05/1925 | Blumenau, 14/05/1925 (10,30 m) |
| 20/06/1911 | 7,49 m | 20/06/1923 | Blumenau, 20/06/1923 (9,00 m) |

Em dez dos onze casos o **dia e o mês são idênticos** aos de um evento já conhecido em outro ano — coincidência que teria cerca de uma chance em 365 por caso. Eles também ficam em **dois trechos seguidos** da tabela (as linhas de 1950 a 1932 e de 1927 a 1911), que é o padrão de uma coluna que escorregou uma linha em relação às outras.

**Não corrigi nada**, e é por isso que escrevo: pode ser que essas datas estejam certas e sejam cheias locais de Gaspar que não repercutiram nas cidades vizinhas — a confluência com o Rio Luís Alves torna isso perfeitamente possível. Se for esse o caso, são onze registros que só o histórico de vocês tem, e eu gostaria de publicá-los. Se for desalinhamento de tabela, os onze com o ano corrigido também entram. O que eu não posso é escolher por conta própria: se o ano estiver errado, eu estaria cruzando cheias de anos diferentes ao comparar Gaspar com Blumenau.

Registro também, no mesmo espírito, que o registro de 20/11/1855 traz data de término **24/11/9855** — um erro evidente de digitação que preservei como está, sem corrigir.

Sei que são muitas perguntas de uma vez, e nenhuma delas é urgente. Se for mais prático responder só a primeira — se a régua do Açu voltou ou onde encontrá-la —, já ajuda muito. Se houver um endereço direto (um arquivo ou serviço) de onde eu possa ler o nível sem consultar a página, também agradeço a indicação: eu identifico todas as consultas com o nome do projeto e respeito qualquer limite que vocês indicarem.

Todo dado de vocês que o site usa aparece com crédito à Defesa Civil de Gaspar. O site está em desenvolvimento e com acesso restrito; se desejarem acompanhá-lo, basta indicar um e-mail e eu libero o acesso, sem custo e sem cadastro.

Fico à disposição e agradeço a atenção.
Atenciosamente,
Jefferson — (47) 98405-6082 · haohmarusc@gmail.com

---

## C12 — EPAGRI/CIRAM, Equipe de Hidrologia: Avisos Hidrológicos de novembro de 2023

> Por que: o Aviso 03 de 19/11/2023 (`aviso_n03_191120236281.pdf`) não está no portal (que publica
> só os seis boletins mais recentes), não está no WordPress (os PDFs ficam fora dele) e não está no
> Internet Archive (acervo do diretório termina em 2022). `docs/CIRAM-ACERVO.md`. Mandar como
> **resposta na mesma thread** do C5 (assunto "Re: Solicitação de acesso aos dados do Rios On-Line…",
> Mariane Souza Melo de Liz, 09/09/2026): o contexto já está lá e a carta de 09/09 abriu a porta.

**Para:** sshidrosc@epagri.sc.gov.br
**Assunto:** (na thread do C5) Avisos Hidrológicos nº 01 a 03 de novembro de 2023 — bacia do Itajaí

Prezada Equipe de Hidrologia,

Mais uma vez obrigado pela resposta de 09/09 e pela tabela de estações.

Estou desenvolvendo, sem fins comerciais e ainda sem publicação, um site com dados históricos de enchentes no Vale do Itajaí. Solicito os Avisos Hidrológicos nº 01, 02 e 03 do evento extremo de novembro de 2023 — em especial o de 19/11/2023, que no padrão de arquivos do portal seria `aviso_n03_19112023<id>.pdf` —, pelas leituras de Rio do Sul e Taió com horário e taxa de variação em cm/h.

Não os localizei no portal, que publica apenas os boletins mais recentes, nem no Internet Archive, cujo acervo do diretório se encerra em 2022. Aproveito para perguntar se há acesso programático ao acervo de boletins e avisos, ou listagem por período, o que evitaria novos pedidos como este.

Como a mensagem de 09/09 diz que os boletins hidrológicos diários seguem por e-mail até a remoção das estações, peço também a inclusão do endereço haohmarusc@gmail.com nessa lista, enquanto ela existir. O site está em desenvolvimento e com acesso restrito; se desejarem acompanhá-lo, basta indicar um e-mail e eu libero o acesso, sem custo e sem cadastro.

Atenciosamente,
Jefferson — (47) 98405-6082 · haohmarusc@gmail.com

## C13 — Defesa Civil de Brusque: a régua do 8,96 m de 17/11/2023, o zero e a COORDENADA da estação DCSC-00019 ✅ ENVIADO em 21/09/2026 09:16 BRT (Gmail, id 1a0c3e4f5ea7825b, para defesacivil@brusque.sc.gov.br, com as quatro perguntas)

> Por que: o histórico da rede estadual (`docs/DCSC-HISTORICO-2026-09-10.md`) mostra a DCSC-00019 lendo
> ~0,30 m ABAIXO dos números da Defesa Civil/imprensa nas três cheias de 2023 — 6,50 vs 6,85 (05/10),
> 6,63 vs 6,91 (13/10), 8,63 vs 8,96 (17/11) —, com deslocamento quase constante. Em 07/09/2026 o par
> DCSC-00019 = "Ponte Estaiada – DCSC" (estação 79 do portal) foi provado com 1,27 / 1,27 / 1,28 m. As
> duas coisas só fecham se houve ajuste de zero entre 2023 e 2026, ou se os números de 2023 vieram de outra
> leitura. Importa porque o 8,96 m é a base das 357 cotas de rua da camada "Cotas de cheia 2023" (cota da
> rua = 8,96 − lâmina medida no ponto) e porque o portal traz duas legendas para a mesma ponte (estação 4
> "Ponte Estaiada – ANA": 4,00 / 7,00; estação 79 "Ponte Estaiada – DCSC": 3,00 / 5,00). Três perguntas
> fechadas, cada uma com alternativas nomeadas.
>
> **Acrescentado em 21/09/2026, por decisão do Jefferson:** a quarta pergunta, sobre a COORDENADA da
> DCSC-00019. O corpo de `monitoramento.defesacivil.itajai.sc.gov.br/monitoramento/rios?municipio_id=2`
> (capturado em 21/09/2026) publica a estação com latitude e longitude nulas e uma TERCEIRA escala
> (3,50 / 5,00 / 6,00). Sem coordenada não há como provar que as três escalas descrevem a mesma régua,
> e o coletor do projeto, que prova identidade por coordenada, não pode ligar Brusque por aquele portal.

**Para:** defesacivil@brusque.sc.gov.br
**Assunto:** Cotas da cheia de 17/11/2023 e estação de referência da Ponte Estaiada — pedido de esclarecimento

Prezada Coordenadoria Municipal de Proteção e Defesa Civil de Brusque,

Estou desenvolvendo, sem fins comerciais e ainda sem publicação, um site com dados históricos de enchentes no Vale do Itajaí, que usa as cotas de rua publicadas pela Defesa Civil de Brusque e a leitura ao vivo da estação "Ponte Estaiada – DCSC" (DCSC-00019, rede estadual). Ao comparar as duas fontes encontrei uma diferença que não consigo resolver sozinho, e por isso peço três esclarecimentos:

1. **Em qual régua foi lido o pico de 8,96 m de 17/11/2023** que consta na revisão das cotas de rua de 2024? A série da estação DCSC-00019 registra máximo de 8,63 m às 21:30 daquele dia, e diferenças parecidas (cerca de 0,30 m) aparecem nas cheias de 05/10/2023 (6,50 m na estação; 6,85 m divulgado) e 13/10/2023 (6,63 m; 6,91 m). A leitura de 8,96 m foi (a) na própria estação DCSC-00019, (b) em régua manual da Ponte Estaiada, ou (c) em outra estação?

2. **Houve ajuste no zero (datum) da estação DCSC-00019 entre 2023 e 2026?** Em 07/09/2026 a leitura da estação e a da página "Ponte Estaiada – DCSC" do portal coincidiram ao centímetro; se em 2023 a mesma estação lia 0,30 m abaixo do valor oficial, um ajuste de zero explicaria as duas observações. Se houve, em que data e de quanto?

3. **Qual das duas legendas vale para a Ponte Estaiada hoje?** O portal mostra a estação 4 "Ponte Estaiada – ANA" com normalidade abaixo de 4,00 m, atenção acima de 4,00 m ou chuva acima de 30 mm e emergência acima de 7,00 m; e a estação 79 "Ponte Estaiada – DCSC" com atenção em 3,00 m e emergência em 5,00 m. As duas estações medem a mesma régua? Qual legenda é a de acionamento vigente? Registro que o portal de monitoramento da Defesa Civil de Itajaí, com o município de Brusque selecionado, publica para a mesma estação DCSC-00019 uma terceira escala (atenção 3,50 m, alerta 5,00 m, emergência 6,00 m).

4. **Qual é a coordenada geográfica (latitude e longitude) da estação DCSC-00019 e da régua da Ponte Estaiada?** O portal da Defesa Civil de Itajaí republica a estação sem coordenada, e sem ela não consigo comprovar que as três escalas acima descrevem o mesmo ponto de medição. Se a estação e a régua manual estiverem em pontos distintos, peço as duas coordenadas.

Os dados que uso serão publicados com a fonte citada, e qualquer correção que a Defesa Civil indicar será aplicada. O site está em desenvolvimento e com acesso restrito; se desejarem acompanhá-lo, basta indicar um e-mail e eu libero o acesso, sem custo e sem cadastro. Se for mais prático, um contato telefônico resolve em poucos minutos.

Atenciosamente,
Jefferson — (47) 98405-6082 · haohmarusc@gmail.com


## C14 — Defesa Civil de Blumenau / AlertaBlu: cache de 30 dias no `nivel_oficial.json` ✅ ENVIADO em 10/09/2026 20:58 BRT (Gmail, id 1a08dc0ec504818b)

> Por que: medido em 10/09/2026 (23:45Z, VPS): `static/data/nivel_oficial.json` é servido com
> `Cache-Control: max-age=2592000` e `Expires` um mês à frente, enquanto o `Last-Modified` muda a
> cada hora e a série `niveis` ganha um ponto por hora. Em plena cheia, um navegador comum recebeu
> a série terminando em 09/09 21:00Z (2,66 m) enquanto o arquivo real já ia em 4,26 m. Qualquer
> integrador que respeite o cabeçalho reproduz o mesmo atraso. Junto: `static/data/nivel.json`,
> de 07/11/2013, ainda responde 200 e pode ser lido como atual. É um aviso técnico de cortesia,
> não um pedido.

**Para:** secretaria.defesacivil@blumenau.sc.gov.br
**Assunto:** AlertaBlu — arquivo nivel_oficial.json servido com cache de 30 dias (aviso técnico)

Prezada Diretoria de Proteção e Defesa Civil de Blumenau,

Estou desenvolvendo, sem fins comerciais e ainda sem publicação, um site com dados históricos de enchentes no Vale do Itajaí, que lê o nível do Itajaí-Açu no AlertaBlu. Escrevo para relatar um detalhe técnico observado na cheia de 10/09/2026, que pode afetar quem consome os dados de vocês.

O arquivo `https://defesacivil.blumenau.sc.gov.br/static/data/nivel_oficial.json` é atualizado a cada hora (`Last-Modified` de 10/09/2026 23:41 UTC, último ponto 23:00 UTC), mas é entregue com os cabeçalhos `Cache-Control: max-age=2592000` e `Expires` trinta dias à frente. Com isso, navegadores e sistemas que respeitam o cache guardam a cópia por até um mês: em 10/09, com o rio em 4,26 m, um navegador comum recebia a série terminando em 09/09 às 21:00 UTC, com 2,66 m. Um `Cache-Control: no-cache` ou `max-age` de poucos minutos nesse arquivo resolveria.

Aproveito para apontar que `static/data/nivel.json`, com dados de 07/11/2013, continua respondendo normalmente e pode ser lido por engano como atual.

Fico à disposição para qualquer esclarecimento, e agradeço pelo AlertaBlu, que é a fonte mais completa da bacia.

Atenciosamente,
Jefferson — (47) 98405-6082 · haohmarusc@gmail.com

---

## C23 — Defesa Civil de Itajaí: o nível de Blumenau é publicado com carimbo de hora 3 h atrasado (⛔ NÃO ENVIAR — decisão do Jefferson em 14/09/2026: mantida a orientação de não enviar ofício ao município de Itajaí)

> ⛔ **NÃO ENVIAR (decisão do Jefferson, 14/09/2026).** Vale a mesma orientação do C21: nenhum ofício ao
> município de Itajaí; o contato com a Defesa Civil de Itajaí é por telefone (47 3228-7700, como o
> próprio dcoperacoes@itajai.sc.gov.br pediu em 02/09). O texto fica aqui como registro técnico do
> achado — o desvio de 3 h continua real e documentado (E12) — e pode ser dito na ligação.
>
> ✅ Direção do desvio confirmada em 14/09/2026 (madrugada). A direção do desvio ficou em dúvida por algumas horas
> em 13/09 (a crista de Ilhota parecia contradizer o AlertaBlu) e foi fechada por uma prova
> independente da física: os boletins da Defesa Civil de Blumenau e as matérias da noite de 11/09,
> em **hora de parede**, batem com o relógio do AlertaBlu e não com o do repasse — "5,78 m às 20h"
> (repasse: 7,07), "6,32 m às 21h" (repasse: 7,31), taxa de ~20 cm/h à 0h30 (AlertaBlu: 24 cm/h;
> repasse: 4–10 cm/h). A Defesa Civil de Blumenau lê a própria régua na ponte; não publicaria 5,78 m
> com o rio a 7,07 m na frente dela. Ver E12 no checklist e o documento do evento.
>
> Por que: medido em 13/09/2026 na série do projeto. A página
> `defesacivil.itajai.sc.gov.br/monitoramento/nivel-rios` publica o nível de Blumenau com um
> carimbo de hora exatamente 3 h 00 anterior ao instante real da leitura. O **valor está certo** —
> o erro é só no horário. Confirmado de três formas: (1) leitura simultânea em 13/09 às 20:22, com
> 4,29 m carimbado 17:15 na página e o mesmo 4,29 m carimbado 20:00 (23:00Z) no AlertaBlu;
> (2) 218 pares da cheia de 11–12/09 concordam com desvio de 1 cm quando se soma 3 h ao carimbo da
> página, contra 55 cm sem o deslocamento; (3) as demais estações da MESMA página (DC-01 a DC-11,
> Brusque) têm carimbo correto no minuto — é específico da linha de Blumenau.
> **Não enviar sem o endereço confirmado**: o e-mail da Defesa Civil de Itajaí ainda não foi
> levantado. Vale procurar no portal da Prefeitura ou ligar para a Defesa Civil municipal.
> **Relação com o C21** (`oficios-b1-c15-c22.md`), que também é para a Defesa Civil de Itajaí e que o
> Jefferson decidiu não enviar: o C21 pede a tabela de cotas e faixas das DC-01 a DC-11 — um favor.
> Este C23 relata um defeito concreto e verificável na página deles, com a medição junto — é outra
> conversa, e não depende do C21. Se for enviado, dá para anexar as perguntas do C21 no mesmo e-mail;
> decisão do Jefferson.

**Para:** *(a confirmar — Defesa Civil de Itajaí)*
**Assunto:** Monitoramento de níveis — horário da leitura de Blumenau está 3 h atrasado

Prezada Defesa Civil de Itajaí,

Estou desenvolvendo, sem fins comerciais e ainda sem publicação, um site com dados históricos de enchentes nos rios Itajaí-Açu e Itajaí-Mirim, que lê a página de monitoramento de níveis de vocês. Escrevo para relatar um detalhe técnico que encontrei e que pode confundir quem acompanha a página durante uma cheia.

A linha de **Blumenau** aparece com um horário de leitura exatamente **três horas anterior** ao instante real da medição. O valor do nível está correto — é só o horário que sai atrasado.

Em 13/09/2026, às 20h22, a página mostrava para Blumenau **4,29 m com horário de 17h15**. No mesmo minuto, o AlertaBlu, de onde vem essa régua, publicava **os mesmos 4,29 m com horário de 20h00**. Comparando as duas fontes ao longo de toda a cheia de 11 e 12 de setembro, 218 leituras coincidem com diferença média de 1 cm quando se somam 3 horas ao horário da página — e divergem em até 1,75 m quando não se soma.

O detalhe que ajuda a localizar a causa: **todas as outras estações da mesma página estão com o horário certo** — no mesmo instante, o DC-10 do Limoeiro marcava 20h10, doze minutos antes. O desvio aparece apenas na linha de Blumenau, o que sugere que a integração que traz esse dado converte o fuso duas vezes (o AlertaBlu publica em UTC, e uma hora UTC convertida para o horário de Brasília duas vezes fica exatamente 3 h atrás).

O efeito prático é que, numa cheia, a leitura de Blumenau na página aparenta ser velha de três horas quando na verdade é recente — e um pico do rio parece ter acontecido três horas antes do que aconteceu.

Fico à disposição para qualquer esclarecimento, e agradeço pela página, que é a única fonte pública que reúne o Açu, o Mirim e os ribeirões de Itajaí no mesmo lugar.

Atenciosamente,
Jefferson — (47) 98405-6082 · haohmarusc@gmail.com

---

## C24 — Cemaden: o que são as estações HIDROLÓGICAS do cadastro (pedido NOVO na LAI, não recurso) (✅ APROVADO pelo Jefferson em 21/09/2026 — NÃO é e-mail: registra-se no Informa.BR, com o login do Jefferson; o texto abaixo está pronto para colar)

> 📌 **Por que é pedido novo e não recurso** (16/09/2026). O pedido anterior,
> protocolo **01217.006547/2026-93**, pediu a *relação das estações com coordenadas* e **foi
> respondido em 10/09/2026** com a planilha `Rede_Observacional_Santa_Catarina___SC.xlsx`
> (415 códigos, já importada — ver `docs/rede-observacional-cemaden.md`). Ou seja: entregaram o
> que foi perguntado, e não há indeferimento a contestar.
> O e-mail de resposta do Fala.BR traz a frase *"No caso de indeferimento... A data limite é:
> 21/09/2026"* — é **texto automático**, vai em toda resposta, deferida ou não, e **não** é um
> prazo a cumprir aqui. Esse 21/09 chegou a ser anotado como pendência por leitura equivocada
> dessa linha; fica desfeito.
> O que falta (medições, cotas, datum, endpoint) **nunca foi pedido** — por isso entra como
> **pedido novo** no mesmo sistema, referenciando o protocolo anterior.
>
> **Motivo técnico**, medido no próprio cadastro: das 18 hidrológicas de SC, só **duas** ficam na
> bacia — `421320321H` em **Pomerode**, *operacional* (-26,7259 / -49,1720), e `420290901H` em
> **Brusque**, *inativa*. A de Pomerode fica a **860 m** da nossa DCSC-00007
> (-26,73285 / -49,17579), que está em `SUSPEITAS` por oscilar de forma implausível. 860 m é perto
> o bastante para ser a mesma estrutura e longe o bastante para não ser — e a lição do "Salseiro"
> (C5) é exatamente essa: coordenada próxima não prova mesma régua, só a fonte diz. Se for outra
> régua, é uma segunda leitura independente no Rio do Testo; se for a mesma, o datum pedido aqui
> pode explicar a oscilação.
> ⚠️ `420290901H` **não** identifica a DCSC-00019 de Brusque — são redes diferentes, e o status
> "inativa" de uma não se transfere para a outra.
>
> **Como registrar:** o Fala.BR avisa que pedidos e histórico migraram para o
> **[Informa.BR](https://informabr.cgu.gov.br/)** — é lá que o pedido novo se registra e que os
> dois protocolos aparecem. Decisão de enviar é do Jefferson.
>
> 🔁 **REESCRITO em 19/09/2026, e o motivo é um erro deste rascunho.** A auditoria abriu a
> resposta ao 01217.006547/2026-93 (Concluída, *Acesso Concedido*, 10/09/2026 às 14h34) e ela
> declara mais do que a planilha: as PCDs hidrológicas **têm sensor de chuva e de nível**,
> transmitem a cada **10 min com chuva** e **1 h sem chuva**, em **UTC**, com dados brutos
> sujeitos a falhas, e o acesso programático ao histórico se pede por **ped@cemaden.gov.br**.
> A versão anterior dos itens 1 e 2 perguntava *que variável ela mede* e *a frequência de
> atualização* como se nunca tivessem sido respondidas — perguntar de novo o que já
> responderam queima a boa vontade de quem respondeu em nove dias. Os itens passam a
> perguntar a **aplicação àquela estação**, que é o que de fato falta. A orientação do
> webservice veio no contexto de dados **pluviométricos**; não presumir que ela valha para o
> nível. Ver `docs/rede-observacional-cemaden.md`.

**Para:** Fala.BR — Cemaden (pedido de acesso à informação, Lei 12.527/2011)
**Assunto:** Estações hidrológicas do Cemaden em Santa Catarina — curso d'água, variável, referência de nível e acesso às leituras

Ao Serviço de Informação ao Cidadão do Cemaden,

Meu nome é Jefferson, sou morador do Vale do Itajaí e estudante de Engenharia de Software. Desenvolvo um site aberto e sem fins comerciais sobre as enchentes dos rios Itajaí-Açu e Itajaí-Mirim, que mostra o nível do rio em cada cidade com a fonte citada em cada dado (github.com/haohmarusc-glitch/enchentes-vale-itajai).

Agradeço a resposta ao pedido **01217.006547/2026-93**, de 10/09/2026: a relação da rede observacional de Santa Catarina com coordenadas foi recebida e já está em uso para vincular corretamente cada pluviômetro ao município. Este é um pedido novo, sobre as estações **hidrológicas** daquele mesmo cadastro, cujas leituras eu não sei interpretar sem as informações abaixo.

Solicito, na medida do que estiver disponível:

1. Para a estação **421320321H**, em Pomerode (SC), registrada como operacional nas coordenadas -26,7259 / -49,1720: **em que curso d'água ela está instalada** e, quanto ao sensor de nível, **em que unidade a medida é expressa** e **em relação a que referência** — zero de régua próprio da estação, altitude (datum, por exemplo SIRGAS 2000 / Imbituba) ou outra. A resposta ao pedido anterior já me informou que as PCDs hidrológicas possuem sensor de chuva e de nível, que a transmissão ocorre a cada 10 minutos com chuva e a cada 1 hora sem chuva, e que os horários estão em UTC; **peço a confirmação de que essas regras se aplicam a esta estação**, e não volto a perguntar o que já me foi respondido. Insisto na referência porque há, a cerca de 860 m dela, uma régua de outra rede em Pomerode; sem saber a referência de cada uma, qualquer comparação entre as duas seria indevida, e eu prefiro não exibir o dado a exibi-lo com o significado errado.

2. **A forma adequada de acessar as leituras de NÍVEL dessa estação de maneira programática** — endereço do serviço, formato e eventual necessidade de cadastro. A orientação que recebi para solicitar acesso programático ao histórico pelo endereço ped@cemaden.gov.br veio no contexto dos dados pluviométricos, e não sei se ela vale também para as leituras hidrológicas; é isso que pergunto. Respeito integralmente qualquer limite de requisições ou termo de uso que for indicado, e identifico todas as requisições com o nome do projeto.

3. Se existirem, os **limiares ou cotas de acionamento** adotados para essa estação (os valores de nível a partir dos quais o Cemaden considera situação de atenção, alerta ou emergência), e a referência em que estão expressos.

4. Se houver **série histórica** dessa estação disponível ao público, como obtê-la.

5. Para a estação **420290901H**, em Brusque (SC), registrada como inativa: **desde quando está inativa** e se a série do período em que operou permanece disponível. Registro, para evitar confusão, que não estou tratando esse código como equivalente a nenhuma estação da rede estadual de Santa Catarina no mesmo município.

O site deixa claro em todas as páginas que **não é sistema oficial de alerta**, que não substitui a Defesa Civil nem os órgãos oficiais de monitoramento, e que em emergência se deve ligar 199. Os dados do Cemaden que já utilizo (chuva acumulada dos pluviômetros) são exibidos como contexto, nunca como cota ou aviso, com crédito ao Cemaden. Qualquer dado de nível obtido por este pedido receberia o mesmo tratamento, com a referência altimétrica declarada na tela.

Fico à disposição para qualquer esclarecimento e agradeço desde já a atenção.

Atenciosamente,
Jefferson — (47) 98405-6082 · haohmarusc@gmail.com

---

## C25 — FURB (Prof. Ademar Cordero): a referência da série histórica de Blumenau ✅ ENVIADO em 02/10/2026 12:30 BRT (Gmail, id 1a0fd3d22a8cd3f4, para cordero@furb.br, sem cópia, a pedido do Jefferson) · 💬 RESPONDIDO PARCIALMENTE em 02/10/2026 12:38–12:40 BRT · seguimento enviado em 02/10/2026 12:44 BRT · respondido "IBGE" às 12:44 · 📎 tabela recebida em 02/10/2026 18:10 BRT · agradecimento enviado em 02/10/2026 · ✅ RESPONDIDO 19:33 BRT (régua de hoje = GPS) · nota de correção do link enviada · 💬 resposta 02/10/2026 21:06 BRT: quer o link mais adiante · ⏳ cadastrar cordero@furb.br no acesso do site

> Por que: é a saída que a **REGRA BLOQUEANTE** de Blumenau (`CLAUDE.md`) prevê para ser removida — "teste no
> HidroWeb ... ou resposta da FURB". A sétima rodada (`docs/PICOS-FALTANTES.md` §14, `docs/fontes-academicas.md`)
> juntou três números para a mesma pergunta, e nenhum deles fecha a conta sozinho:
> **0,20 m** (a regra; e o CEOPS na Tabela 3 do Esboços, +0,20 sobre o AlertaBlu em 31/08 e 09/09/2011),
> **≤ 0,15 m em 1983** (o valor diário 1519 da ANA 83800002 em 09/07/1983, se for cm na régua da época) e
> **0,40 m depois de 2011** (o próprio artigo do Prof. Cordero no XX SBRH). A lista oficial do AlertaBlu
> reproduz a Tabela 4 de Cordero & Medeiros ao centímetro até 2001 (58 eventos) e não diz a régua.
> Destinatário: **cordero@furb.br** — o endereço publicado no artigo "Cotas-enchente do município de Blumenau"
> (XX SBRH) e no artigo ARMAX de Rio do Sul (XIX SBRH; coautores momo@furb.br e severo@furb.br, em cópia se o
> Jefferson quiser). O CEOPS foi desativado em 2022, então o endereço pode estar inativo: se voltar, tentar a
> secretaria do departamento de Engenharia Civil da FURB. Cinco perguntas fechadas, cada uma com alternativas
> nomeadas; a 4 é o "teste no HidroWeb" que a regra pede, feito por quem tem a série.

**Para:** cordero@furb.br
**Assunto:** Referência (régua ANA ou zero IBGE) da série histórica de enchentes de Blumenau — pedido de esclarecimento

Prezado Prof. Ademar Cordero,

Estou desenvolvendo, sem fins comerciais, um site com dados históricos de enchentes no Vale do Itajaí, voltado a moradores, que usa a série de picos de Blumenau publicada pelo senhor e por Medeiros (Tabela 4, XV SBRH, 1852–2001), a lista "Enchentes Registradas" da Defesa Civil de Blumenau e as leituras ao vivo da estação ANA 83800002. Para não exibir números de referências diferentes como se fossem comparáveis, preciso saber em que referência está cada trecho da série, e encontrei três indicações que não consigo conciliar sozinho:

- No artigo "Cotas-enchente do município de Blumenau" (Cordero, Salvador e Refosco, XX SBRH), consta que, depois da enchente de setembro de 2011, a ANA aceitou alterar a referência da régua para a do IBGE levantada por GPS, "que deu 40 cm. Assim a referência da régua da ANA ficou 40 cm a menos do que as enchentes anteriores". O mesmo artigo dá 13,0 m para o pico de setembro de 2011.
- A Tabela 3 da revista Esboços (UFSC, 2013), com fonte CEOPS, dá 12,8 m para 09/09/2011 e 8,7 m para 31/08/2011, enquanto a lista da Defesa Civil dá 12,6 m e 8,5 m — diferença de 0,20 m. Em 01/10/2001 as duas dão 11,02 m.
- O serviço HidroSerieHistorica da ANA (estação 83800002, dados consistidos) traz 1519 como valor diário de 09/07/1983 e 1485 para 07/08/1984, sem unidade declarada. A Tabela 4 dá 15,34 m e 15,46 m para essas cheias.

Por isso peço, se possível, cinco esclarecimentos:

1. **Em que referência estão os valores da Tabela 4 (1852–2001)?** (a) na régua da estação fluviométrica de Blumenau como era lida na época de cada cheia; (b) no zero do IBGE; ou (c) outra. Se for o IBGE, qual a diferença para a régua — 0,20 m, 0,40 m ou outra — e ela é a mesma para todo o período?

2. **O que significa, em leitura de régua, "ficou 40 cm a menos"?** (a) depois da mudança, uma mesma altura da água passou a ser lida 0,40 m mais baixa do que antes; (b) passou a ser lida 0,40 m mais alta; ou (c) outra coisa. Em que data a mudança entrou em vigor?

3. **O valor diário 1519 da ANA para 09/07/1983 está em centímetros e na régua da época?** Se estiver, a crista daquele dia na mesma régua foi de pelo menos 15,19 m, o que não cabe com 15,34 m em IBGE e uma diferença de 0,20 m (a crista na régua seria 15,14 m). Há algo nessa leitura que eu esteja deixando passar — por exemplo, a série consistida ter sido ajustada depois?

4. **O senhor dispõe das cotas de pico na régua (com hora) de 09/07/1983 e 07/08/1984** na estação 83800002? São a comparação que permitiria fechar a questão.

5. **A partir de que ano a lista "Enchentes Registradas" da Defesa Civil de Blumenau deixa de reproduzir a Tabela 4** e passa a publicar a leitura da régua operacional? Os valores coincidem ao centímetro até 2001, e de 2008 em diante diferem dos do CEOPS.

Nenhuma conversão será aplicada aos dados antes da sua resposta, e a fonte será citada no site. O site está em desenvolvimento e com acesso restrito; se desejar acompanhá-lo, basta indicar um e-mail e eu libero o acesso, sem custo e sem cadastro. Se for mais prático, um contato telefônico resolve em poucos minutos.

Atenciosamente,
Jefferson — (47) 98405-6082 · haohmarusc@gmail.com

### Resposta do Prof. Cordero (02/10/2026, três e-mails, 12:38, 12:39 e 12:40 BRT, mesmo fio)

Transcrição literal, sem correção:

> "Ola Jefferson ! Existe três referências! 12,60m na régua 12,80 (IBGE) 13,00(GPS) isto relativo a enchente
> de 2011! A régua nova tem que somar 40 cm aos níveis da régua antiga !"
>
> "Antes era somas o 20 cm para a referência do IBGE"
>
> "Tenho a séria ! Pode enviar um e-mail cordero @furb.br"

**O que responde:** set/2011 em três referências — régua 12,60 m, IBGE 12,80 m (régua + 0,20), GPS 13,00 m
(régua + 0,40); "antes" (da troca de régua) somavam-se 0,20 m para o IBGE; ele tem a série e oferece enviá-la
(pergunta 4). **O que não responde:** a pergunta 1 (Tabela 4 em IBGE?), a data e o sentido da troca (a frase dos
40 cm admite as duas leituras), a 3 (unidade do 1519 da ANA) e a 5 (desde quando a lista do AlertaBlu muda).

### Seguimento ✅ ENVIADO em 02/10/2026 12:44 BRT (Gmail, id 1a0fd4978880e449, mesmo fio, a pedido do Jefferson)

Prezado Prof. Ademar,

Muito obrigado pela resposta rápida! Aceito com gratidão a série — pode enviar para este e-mail (haohmarusc@gmail.com).

Só para eu não interpretar errado, dois pontos curtos:

1. Uma água que marcava 10,00 m na régua antiga passou a marcar quanto na régua nova: 9,60 m ou 10,40 m? E a troca valeu a partir de que data?

2. Os valores da Tabela 4 (1852–2001), como 15,34 m em 1983, estão na referência IBGE, ou seja, régua antiga + 0,20 m?

Abraço,
Jefferson

### Resposta ao seguimento (02/10/2026, 12:44 e 12:45 BRT, mesmo fio)

Transcrição literal:

> "IBGE" (12:44:47, id 1a0fd4a2daca6570)
>
> "Quando chegar e casa envio a tabela" (12:45:18, id 1a0fd4aa30f89c4d)

**Leitura:** o "IBGE" responde à pergunta 2 do seguimento — os valores da Tabela 4 (1852–2001), como 15,34 m em
1983, estão na referência IBGE (régua antiga + 0,20 m), que é o que o rótulo `IBGE (régua + 0,20 m)` dos 72
registros já diz. A pergunta 1 do seguimento (10,00 m na régua antiga = 9,60 ou 10,40 na nova, e a data da troca)
**ficou sem resposta**. A tabela ainda não chegou.

### A tabela (02/10/2026, 18:10 BRT, mesmo fio, id 1a0fe741b3d6fddf)

Transcrição literal:

> "Olá! Encaminho os picos com as enchentes com as duas referências (Régua antiga +0,2 = IBGE) a outra
> (IBGE+0,2=GPS)
> Após enchente de 2011 foi instalada nova régua (em relação a régua antiga tem 40 cm). A partir desta data não
> precisa somar nem o 20 cm nem o 40 cm."

Anexo `Picos-Blumenau-1888-2024-IBGE-GPS.xls`, guardado como veio em `data/brutos/furb-cordero-2026-10-02/`
(sha256 e transcrição no `LEIAME.md` da pasta).

**Leitura:** responde à pergunta 1 do seguimento. A régua nova lê **0,40 m mais alto** que a antiga (10,00 m na
antiga = 10,40 m na nova) e já está na referência GPS = IBGE + 0,20 m. A planilha marca "Mudança da regua nova"
na linha de 2013. A análise linha a linha está em `docs/fontes-academicas.md`, seção "A planilha do Prof. Cordero".

### Agradecimento enviado (02/10/2026, mesmo fio, id 1a0feb75f94f4b3b)

Resposta ao e-mail da tabela, a pedido do Jefferson: agradece ("foi de enorme importância para o projeto"), avisa
que a série de Blumenau no site citará o Prof. Cordero e o CEOPS/FURB como fonte da conversão, manda o link do site
(**erro**: o site tem acesso restrito e não abriu para ele; daqui em diante, sem link, ver a regra no topo) e faz
duas perguntas: (1) a data de instalação da régua nova; (2) se as leituras de hoje (ANA 83800002 e AlertaBlu)
já estão na régua nova/GPS, ou seja, se 15,34 m de 1983 (IBGE) = 15,54 m na régua atual. Respondido abaixo.

### Resposta ao agradecimento (02/10/2026, 19:33 BRT, mesmo fio, id 1a0fec01dcba5a96)

Transcrição literal:

> "A régua atual já está na referência gps ! Olha que depois de 2011 não somei os 20 cm ! Não lembro bem a data mas
> foi depois da enchente de 2011! Porque na referida enchente o talude do rio deslizou e levou as réguas juntos !
> Então após da enchente de 2011 foi instalada no pilar da ponte com referência GPS ! Depois foram montadas as réguas
> a montante da ponte com a mesma referência GPS"

**Leitura:**
* **Pergunta 2, respondida: sim.** A régua de hoje está em GPS (IBGE + 0,20 m). Os 15,34 m de 1983 (IBGE)
  equivalem a 15,54 m na régua atual.
* **Pergunta 1, sem dia.** A troca veio depois da cheia de set/2011, porque o talude deslizou e levou as réguas.
  Primeiro foi instalada uma régua no pilar da ponte, já em GPS; depois, as réguas a montante da ponte, na mesma
  referência. A planilha marca a mudança em 2013. Janela: set/2011 a set/2013. O cadastro de Blumenau não tem
  leitura nesse intervalo.
* "Depois de 2011 não somei os 20 cm" explica por que as colunas IBGE e GPS da planilha são iguais de 2013 em diante.
* A divergência da planilha com a Tabela 4 em 1931–1983 não foi comentada.

### Segundo agradecimento e correção do link (02/10/2026, mesmo fio, id 1a0fec884d39d16b)

A pedido do Jefferson: agradece de novo a explicação e a rapidez, e corrige o e-mail anterior. O site tem acesso
restrito e o link não abre sem cadastro; se ele quiser acompanhar, basta indicar o e-mail para cadastro. **Sem
link**, conforme a regra do `CLAUDE.md`.

### Resposta à correção do link (02/10/2026, 21:06 BRT, mesmo fio, id 1a0ff1550a08beb7)

Transcrição literal:

> "Olá Jefferson
> Quando estiver num estágio mais avançado você manda o link
> Meu e_mail é este que está enviando estas mensagens."

**Leitura:** ele quer acompanhar o site e indicou o próprio e-mail, `cordero@furb.br`. Não pede resposta agora.

**Pendências (Jefferson):**
* **Cadastrar `cordero@furb.br`** na lista de acesso do site (Cloudflare Access). Não se faz pelo repositório.
* **Mandar o link quando o site estiver mais avançado**, só depois do cadastro feito, para não repetir o erro de
  02/10/2026 (regra do `CLAUDE.md`: link sem cadastro abre a tela fechada). Sem mais perguntas técnicas ao Prof.
  Cordero (decisão de 03/10/2026).

---

## C27 — Defesa Civil de Timbó — ✅ ENVIADO pelo Jefferson em 04/10/2026 às 00h38 BRT

Enviado para **defesacivil@timbo.sc.gov.br** (Gmail, id `1a104fdd08d4e63a`), com o assunto "Régua e faixas de
nível do Rio Benedito em Timbó — pedido de esclarecimento". O Jefferson redigiu e enviou o texto. O rascunho
abaixo fica como referência.

O envio foi autorizado pelo Jefferson em 04/10/2026, mas o e-mail não foi mandado. O único endereço achado,
comdec@timbo.sc.gov.br, vem de resumo de busca da rodada 6, sem página oficial salva. Ver
`data/brutos/varredura-pintar-2026-10-03/RELATORIO-rodada6.pdf`, seção 3.

**Para:** a confirmar (Defesa Civil de Timbó)
**Assunto:** Confirmação da tabela de cotas do Rio Benedito

Não leva link do site (regra de 02/10/2026). Envio é decisão do Jefferson.

À Defesa Civil de Timbó,

Meu nome é Jefferson, sou morador da região e estudante de Engenharia de Software. Mantenho, sem fins
comerciais e com acesso restrito, um site sobre as enchentes dos rios Itajaí-Açu e Itajaí-Mirim. Ele cita a
origem de cada dado e avisa que não é sistema oficial de alerta nem substitui a Defesa Civil. Em emergência,
199.

Comparei o nível do Rio Benedito que vocês divulgaram na cheia de 12/09/2026 com a estação estadual
**DCSC-00023** (Defesa Civil de SC). Os números batem ao centímetro: 5,52 m às 3h nas duas, e 5,53 m contra
5,52 m no pico da madrugada.

Só preciso confirmar a tabela:

**A escala do Rio Benedito é esta, lida nessa mesma estação?**
- normal até 2,00 m;
- atenção de 2,01 a 3,00 m;
- alerta de 3,01 a 4,29 m;
- alto risco a partir de 4,30 m.

E ela convive com o acionamento do Plano de Contingência a 5,00 m, ou o substituiu?

Se quiserem ver o site, basta me mandar o e-mail para cadastro.

Muito obrigado pelo trabalho de vocês.

Jefferson — (47) 98405-6082 · haohmarusc@gmail.com

---

## C26 — Defesa Civil de Ibirama — ✅ ENVIADO em 04/10/2026 como lembrete, por decisão do Jefferson (Gmail, id `1a104e1d45640b24`, resposta na conversa de 13/09)

**✅ RESPONDIDO em 05/10/2026** (`docs/resposta-ibirama-c26-2026-10-05.md`):
- a régua das faixas é a DCSC-00020;
- as faixas do PLAMCON são aproximadas, e o plano de 2026 está em ajustes finais;
- não há cotas de rua.

A tabela vigente continua em aberto.

**Resposta enviada em 05/10/2026:** e-mail cadastrado no site e link enviado, por decisão do Jefferson.

**O texto enviado não é o rascunho abaixo.** Ele foi encurtado como lembrete e acrescentou o que a rodada 6 trouxe:
- o Decreto 5.431/2024 liga o nível à estação da ponte Beltramini;
- o boletim de 11/09 chamou 4,04 m de "atenção";
- existe o PLAMCON 2025 homologado pelo Decreto 5.824/2025.

A pergunta enviada: as faixas são lidas na DCSC-00020, e qual tabela vale, a de 2024 ou a nova do PLAMCON 2025?

**Já houve pedido:** em 13/09/2026 às 17h14 BRT foi enviado e-mail mais completo a defesacivil@ibirama.sc.gov.br
("Régua e cotas de referência para o monitoramento de enchentes em Ibirama", Gmail, thread `1a09c686c39f1996`).
Ele comparava quatro boletins com a DCSC-00020 (1,73 × 1,73 m em 14/08; 3,57 × 3,56 m em 01/09) e perguntava a
régua, as faixas vigentes (o plano de 2024 dá 3,00 / 3,50 / 4,00 m) e as cotas de rua. Sem resposta até 04/10/2026.
Se for mandar, mandar como resposta naquela conversa, encurtando o texto abaixo para "retomo a mensagem de 13/09".

**Para:** defesacivil@ibirama.sc.gov.br · (47) 98838-5645 (contato da varredura de 04/10, não conferido daqui)
**Assunto:** Faixas do Rio Itajaí do Norte e a estação estadual DCSC-00020

Não leva link do site (regra de 02/10/2026). Envio é decisão do Jefferson.

À Defesa Civil de Ibirama,

Meu nome é Jefferson, sou morador da região e estudante de Engenharia de Software. Mantenho, sem fins
comerciais e com acesso restrito, um site sobre as enchentes dos rios Itajaí-Açu e Itajaí-Mirim. Ele cita a
origem de cada dado e avisa que não é sistema oficial de alerta nem substitui a Defesa Civil. Em emergência,
199.

O site mostra a leitura da estação estadual **DCSC-00020** (Defesa Civil de SC) para Ibirama, mas não mostra
cor de cota, porque não sei em que régua estão as faixas do Plano de Contingência.

**As faixas de monitoramento do Rio Itajaí do Norte (Hercílio) são lidas na estação DCSC-00020? Se não, em
qual régua, e qual é a tabela vigente?**

Se quiserem ver o site, basta me mandar o e-mail para cadastro.

Muito obrigado pelo trabalho de vocês.

Jefferson — (47) 98405-6082 · haohmarusc@gmail.com

---

## C28 a C30 — Trombudo Central, Rio dos Cedros e Apiúna — ✅ ENVIADOS pelo Jefferson em 04/10/2026

O Jefferson redigiu e enviou os três textos. Aqui fica o registro do que foi perguntado, conferido na caixa
de Enviados do Gmail em 04/10/2026. Nenhum leva link do site, e todos dizem: "se quiserem conhecer o site,
basta me enviar um e-mail para cadastro". Os três citam o repositório público do código no GitHub, que não é
o site. Sem resposta até 04/10/2026.

### C28 — Defesa Civil de Trombudo Central — 04/10/2026 às 00h39 BRT
**Para:** defesacivil@trombudocentral.sc.gov.br (Gmail, id `1a104feb75ee7bef`)
**Assunto:** "Régua e faixas de nível do Rio Itajaí do Oeste em Trombudo Central — pedido de esclarecimento"

1. A página da Defesa Civil diz que o município "trabalha com as seguintes cotas", mas a lista não aparece
   (talvez seja imagem). Quais são as faixas vigentes, com nomes e valores, e em qual régua?
2. A régua municipal é a mesma da estação da DCSC em Trombudo Central (DCSC-00035)? Se não, há diferença
   documentada? A régua municipal "só mede até 6,15 m", e a estação estadual já passou bem disso.

### C29 — Defesa Civil de Rio dos Cedros — 04/10/2026 às 00h42 BRT
**Para:** defesacivil@riodoscedros.sc.gov.br (Gmail, id `1a105014b2aecbbb`)
**Assunto:** "Régua do Rio dos Cedros e estação da Defesa Civil de SC — pedido de esclarecimento"

Cita as faixas 4,80 (atenção) / 5,30 (alerta) / 5,70 m (alarme) do Plano v10.9, p. 9, lidas na régua do Paço.
1. A estação da DCSC (DCSC-00011) mede na mesma régua do Paço? Se não, há diferença documentada? Onde e com
   qual zero a régua do Paço foi instalada?
2. Em que dia e hora foi o pico de 8,96 m de 2014 do documento "Históricos de Enchentes"? O PDF tem a tabela
   de 15 em 15 minutos, mas não escreve a data.

**Resposta (07/10/2026, 09h36, Jucinei Ivan Vicenzi, Coordenador de Proteção e Defesa Civil):** "temos apenas uma
estação de nível de rio, que fica na ponte próxima ao Paço Municipal, sendo usado o Paço Municipal apenas como
referência"; "o pico aconteceu as 00:45 do dia 09/06/2014 atingindo 8,96m". Transcrição em
`data/brutos/respostas/rio-dos-cedros-c29-2026-10-07.txt`. Aplicada no mesmo dia por decisão do Jefferson
(equivalência com a DCSC-00011 confirmada; data e hora do pico de 2014). Sem resposta: o zero da régua.

### C30 — Defesa Civil de Apiúna — 04/10/2026 às 00h42 BRT (reenvio)
**Para:** defesacivil@apiuna.sc.gov.br (Gmail, id `1a10501b439a84e5`)
**Assunto:** "Régua e cotas de referência do Rio Itajaí-Açu em Apiúna — pedido de esclarecimento"

Reenvio direto à Defesa Civil do pedido de 13/09/2026, que tinha ido ao gabinete (gabinete@apiuna.sc.gov.br,
Gmail, id `1a09c75462779e6d`) sem retorno. Endereço indicado pela rodada 6.
1. Qual régua a Defesa Civil usa (local, código)? É a ANA 83500000, Apiúna–Régua Nova? Automática ou por
   observador? Há página com as leituras?
2. Quais as faixas vigentes, com nomes e valores? Plano de contingência ou tabela, se houver.
3. A estação da DCSC em Apiúna (DCSC-00178) publica altitude, não nível. Qual é a cota do zero da régua?

Referência citada: os boletins municipais de 4 e 5/05/2022 (6,43 m às 17h de 04/05).

---

## C32 — Defesa Civil de Rio dos Cedros: confirmação das cotas na DCSC-00011 — 📝 RASCUNHO no Gmail, não enviado (07/10/2026; rascunho `r3697923724363143209`, resposta na conversa do C29)

**Origem.** Decisão do Jefferson de 07/10/2026: Rio dos Cedros fica **sem classificação municipal** até a COMPDEC
confirmar as cotas, sem exceção (`docs/CLASSIFICACAO-ESTADUAL-MUNICIPAL.md`, "Piloto ampliado").

**O que ainda falta saber.** A resposta ao C29 (07/10/2026) confirmou que a cidade tem uma estação de nível só, a
DCSC-00011. Ela não disse três coisas:
- se as cotas do Plano v10.9, p. 9 (4,80 / 5,30 / 5,70 m), são lidas diretamente nessa estação, no mesmo zero;
- qual é o zero da régua;
- se a escala continua valendo depois do desassoreamento de 2026.

**Pergunta nova.** Em 07/10, com 3,69 m, a Defesa Civil de SC classificava a estação em *atenção*, faixa própria do
Estado, enquanto pelo Plano o nível estaria abaixo da atenção. Falta saber qual das duas o município usa para acionar.

**Como enviar.** Responder na conversa do C29 (Gmail, id `1a105014b2aecbbb`), para defesacivil@riodoscedros.sc.gov.br,
que é onde o coordenador já respondeu.
- Sem link do site (regra de 02/10/2026).
- Sem números que a COMPDEC não publicou.
- O pedido de cadastro vai no fim, como nos anteriores.

**Para:** defesacivil@riodoscedros.sc.gov.br (resposta na conversa do C29)
**Assunto:** Re: Régua do Rio dos Cedros e estação da Defesa Civil de SC — pedido de esclarecimento

Bom dia, Jucinei,

Obrigado pela resposta do dia 7. Com ela, passei a usar a estação da Defesa Civil de SC na ponte próxima ao Paço
Municipal (DCSC-00011) como a régua de Rio dos Cedros, e corrigi o pico de 2014 para 00h45 de 09/06/2014, com 8,96 m.

Falta uma confirmação para eu poder comparar o nível com as cotas do município. Por isso, até a resposta, o site não
classifica Rio dos Cedros pelas cotas municipais. Ele mostra o nível e, quando há, a faixa que a Defesa Civil de SC
publica para a estação, identificada como faixa estadual.

As perguntas:

1. As cotas do Plano de Contingência v10.9 (abril de 2026, p. 9) — atenção em 4,80 m, alerta em 5,30 m e alarme em
   5,70 m — são lidas diretamente na estação DCSC-00011, no mesmo zero, sem correção?
2. Qual é o zero (a referência) dessa régua? Ele mudou em algum momento desde 2014?
3. Essas cotas continuam valendo depois do desassoreamento do rio feito em 2026, ou há revisão prevista?
4. A Defesa Civil de SC publica faixas próprias para a mesma estação. No dia 7, com 3,69 m, ela aparecia em "atenção"
   na rede estadual, enquanto pelo Plano o nível estaria abaixo da atenção. Para o acionamento do município, valem as
   faixas do Plano, as do Estado ou as duas?

Se quiserem conhecer o site, basta me enviar um e-mail para cadastro.

Muito obrigado pela atenção.

Jefferson — (47) 98405-6082 · haohmarusc@gmail.com

---

## C31 — INMET, Direção: manifestação de interesse em Acordo de Cooperação Técnica — ✅ ENVIADO em 04/10/2026, por pedido do Jefferson ("faça o 4"), com o texto abaixo sem alteração (Gmail, id `1a1066b689e7fad1`, para diretor@inmet.gov.br)

Origem: a resposta da LAI C8 (NUP 21210.009435/2026-61, 22/09/2026) diz que a API do INMET só abre com Acordo de
Cooperação Técnica, a começar por ofício de manifestação de interesse à Direção, seguido de reunião
(`docs/LAI-INMET-2026-09-22.md`). Até a resposta, o projeto continua só com os canais públicos (BDMEP e a tabela do
portal, consulta de tela). Não leva link do site (regra de 02/10/2026).

**Ressalva para o Jefferson antes de enviar:** o ACT é entre instituições, e o projeto não tem pessoa jurídica. O
texto diz isso de saída e pergunta se há caminho para pessoa física ou projeto acadêmico. Se houver instituição
parceira (universidade, Defesa Civil), vale citá-la; o rascunho não inventa nenhuma.

**Para:** diretor@inmet.gov.br
**Assunto:** Manifestação de interesse em Acordo de Cooperação Técnica — dados de chuva da bacia do Itajaí (SC)

À Direção do Instituto Nacional de Meteorologia,

Meu nome é Jefferson, sou morador do Vale do Itajaí e estudante de Engenharia de Software. Mantenho, sem fins
comerciais e com acesso restrito, um site sobre as enchentes dos rios Itajaí-Açu e Itajaí-Mirim. Ele cita a origem
de cada dado e avisa que não é sistema oficial de alerta nem substitui a Defesa Civil.

Pelo pedido de acesso à informação NUP 21210.009435/2026-61, respondido em 22/09/2026, soube que a API do INMET é
restrita a instituições com Acordo de Cooperação Técnica, e que o primeiro passo é esta manifestação de interesse.

O uso seria só a chuva horária das estações automáticas da bacia (A817 Indaial, A861 Rio do Campo, A863 Ituporanga
e A868 Itajaí), como contexto das cheias, sempre com crédito ao INMET e com a ressalva de que são dados brutos, sem
consistência.

Antes de pedir a reunião, gostaria de saber:

1. O projeto não tem pessoa jurídica. Existe alguma modalidade de acesso para pessoa física ou projeto acadêmico,
   ou o ACT exige instituição?
2. Quais são a documentação da API, os formatos de saída e os limites de uso (a resposta citou 60 requisições por
   minuto por token)?
3. Quais condições de uso e de crédito valeriam para exibir esses dados num site de acesso restrito?

Se o caminho for o ACT, fico à disposição para a reunião. Se quiserem ver o site, basta me mandar o e-mail para
cadastro.

Muito obrigado pela atenção.

Jefferson — (47) 98405-6082 · haohmarusc@gmail.com
