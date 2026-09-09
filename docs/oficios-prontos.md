# Ofício pronto para envio — EPAGRI/CIRAM

Contato preenchido: **Jefferson — (47) 98405-6082 · haohmarusc@gmail.com**

Pronto para copiar e colar no e-mail. O texto-fonte, com a justificativa técnica de
cada pedido, e os demais ofícios (C1–C4) ficam em `docs/pendencias-navegador-e-oficios.md`.

---

## C5 — EPAGRI/CIRAM, Equipe de Hidrologia

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

## C11 — Defesa Civil de Ilhota (COMPDEC)

**Para:** dpo@ilhota.sc.gov.br · (47) 3343-8800 / 3343-0181 · Rua Leoberto Leal, 160, Centro, Ilhota-SC, 88320-438
**Assunto:** Em que régua estão as cotas do Plano de Contingência 2025/2028?

À Coordenadoria Municipal de Proteção e Defesa Civil de Ilhota,

Meu nome é Jefferson, sou morador da região e estudante de Engenharia de Software. Desenvolvo um site aberto e sem fins comerciais sobre as enchentes dos rios Itajaí-Açu e Itajaí-Mirim, que mostra o nível do rio em cada cidade e as cotas de referência de cada município, sempre com a ressalva de que não substitui a Defesa Civil.

O Plano de Contingência 2025/2028 de Ilhota (versão 016), na seção "Condições sobre o nível do Rio Itajaí", define **9,20 m** (atenção), **10,00 m** (prontidão) e **10,50 m** (emergência), e cita a estação hidrometeorológica da Ponte Cláudio Jeremias Cadorin. Em uma notícia de 2013 a Defesa Civil de Ilhota informava que não contava com régua própria e acompanhava a medição de Gaspar.

Tenho uma única dúvida, e ela decide se posso ou não mostrar essas cotas ao lado de um nível ao vivo:

**As cotas 9,20 / 10,00 / 10,50 m são lidas em qual régua — a de Gaspar, na Ponte Hercílio Deecke, ou uma régua em Ilhota (a da Ponte Cláudio Jeremias Cadorin)? E qual é o zero dessa régua?**

Pergunto porque a conta não fecha sozinha: a cota de emergência de Gaspar é 7,00 m, e se as cotas de Ilhota estivessem na régua de Gaspar, Ilhota só entraria em atenção com o rio 2,20 m acima da emergência de Gaspar. É possível, mas precisa estar escrito para não ser suposto.

Se a estação da Ponte Cadorin publicar leituras em algum endereço, agradeço a indicação.

Muito obrigado pelo trabalho de vocês.

Jefferson

---

## C10 — Superintendência Municipal de Proteção e Defesa Civil de Gaspar

**Para:** defesacivil@gaspar.sc.gov.br
**Assunto:** Três dúvidas sobre os dados publicados no portal da Defesa Civil de Gaspar (régua do Itajaí-Açu, cotas de acionamento e histórico de enchentes)

À Superintendência Municipal de Proteção e Defesa Civil de Gaspar,

Meu nome é Jefferson, sou morador da região e estudante de Engenharia de Software. Desenvolvo um site aberto e sem fins comerciais sobre as enchentes dos rios Itajaí-Açu e Itajaí-Mirim, que reúne o nível do rio em cada cidade, as cotas de referência e uma estimativa do tempo de chegada da cheia. O código e os dados são públicos (github.com/haohmarusc-glitch/enchentes-vale-itajai), cada informação aparece com a fonte citada, e todas as páginas deixam claro que o site **não é sistema oficial de alerta** e não substitui a Defesa Civil — em emergência, 199.

Escrevo porque o portal de vocês é, de longe, o material mais completo que encontrei para Gaspar: as 1.617 cotas de rua, o histórico de enchentes desde 1852 e a tabela de monitoramento não têm equivalente nos outros municípios da bacia. Justamente por usar esse material com cuidado, cheguei a três dúvidas que só vocês podem responder.

> ✏️ **Antes de enviar (09/09/2026):** a régua NÃO saiu do portal — `/estacao/ver/21` está viva (1,12 m em 08/09 08:03, conferido no navegador). Reescrever a pergunta 1 como: *a estação saiu da listagem de `/monitoramento/tabela` mas continua na página própria; a tabela deixou de ser a referência? e qual é a cadência de atualização da leitura (às 21h ela era das 08:03)?* A pergunta 2 ganha um dado: em 08/09 a legenda já mostrava 5,00 m, não 6,00 — a legenda varia entre consultas?

**1. A régua do Rio Itajaí-Açu saiu da tabela de monitoramento.**

Até 31/08/2026 a tabela em `/monitoramento/tabela` trazia a estação **"Rio Itajaí Açu Gaspar"** (naquele dia, 3,85 m às 22h59). Consultando em 07/09/2026, a tabela passou a trazer sete estações e nenhuma delas é o Itajaí-Açu: entraram as barragens Norte, Oeste e Sul, e a única estação de rio que restou é o Ribeirão Belchior Central.

Gostaria de saber se **a régua do Açu continua ativa** — e, se sim, em que endereço, já que a página da estação que eu acompanhava era `/estacao/ver/21`. Pergunto porque essa é a **única fonte de nível do Itajaí-Açu em Gaspar** que existe: a rede estadual (DCSC-00005) informa não medir nível de rio no município, e a estação da ANA em Gaspar (83840000) encerrou a escala em dezembro de 2021 sem substituta. Sem ela, meu site simplesmente não consegue dizer a que nível o rio está em Gaspar, e mostra o município sem leitura — o que é o correto, mas é uma lacuna grande justamente na cidade para a qual eu tenho mais cotas de rua levantadas.

Aproveito para registrar uma observação técnica que pode ser útil: a série de 12 horas do Ribeirão Belchior Central publica **0,00 em todos os pontos** (consulta de 07/09/2026, das 03h28 às 15h18). Como 0,00 é um número válido, um sistema que leia essa página pode interpretá-lo como "ribeirão seco" em vez de "sem leitura".

**2. Duas cotas de atenção diferentes, nas duas publicações de vocês.**

O Plano de Contingência (item 4.2.3, fluxograma "MONITORAMENTO RIO ITAJAÍ AÇU", p. 25) trabalha com **atenção a partir de 5,00 m**. A legenda da estação 21, no próprio portal, indica **normalidade abaixo de 6,00 m** e atenção acima disso.

Adotei os 5,00 m, por ser o que avisa mais cedo, e deixei os 6,00 m registrados ao lado como divergência. Mas gostaria de confirmar **qual dos dois é o vigente**, porque a diferença é operacional: a primeira rua do cadastro de vocês alaga a 6,20 m, então a atenção a 5,00 m dá 1,20 m de margem e a 6,00 m dá 20 cm.

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

Todo dado de vocês que o site usa aparece com crédito à Defesa Civil de Gaspar.

Fico à disposição e agradeço a atenção.
Atenciosamente,
Jefferson — (47) 98405-6082 · haohmarusc@gmail.com
