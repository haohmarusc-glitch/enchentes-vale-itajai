# Ofícios prontos para envio

Contato preenchido: **Jefferson — (47) 98405-6082 · haohmarusc@gmail.com**

Cada ofício abaixo está pronto para copiar e colar no e-mail. Os textos-fonte, com as
justificativas técnicas de cada pedido, ficam em `docs/pendencias-navegador-e-oficios.md`.

Situação:

| Ofício | Destinatário | E-mail | Estado |
|---|---|---|---|
| C1 | Defesa Civil de Brusque | defesacivil@brusque.sc.gov.br | ✅ enviado 31/08 |
| C2 | Defesa Civil / GEOItajaí | (protocolo da Prefeitura / Defesa Civil de Itajaí) | a enviar |
| C3 | UNIVALI — marégrafo | michelena@univali.br; ariadne@univali.br | a reenviar |
| C4 | Defesa Civil de Gaspar | defesacivil@gaspar.sc.gov.br | a enviar |
| C5 | EPAGRI/CIRAM — Hidrologia | sshidrosc@epagri.sc.gov.br | a enviar |

---

## C4 — Defesa Civil de Gaspar

**Para:** defesacivil@gaspar.sc.gov.br
**Assunto:** Solicitação: acesso ao nível do Itajaí-Açu em Gaspar e confirmação da régua das cotas do Plano de Contingência

À Superintendência Municipal de Proteção e Defesa Civil de Gaspar,

Meu nome é Jefferson, sou morador da região e estudante de Engenharia de Software. Desenvolvo um site aberto e sem fins comerciais sobre as enchentes dos rios Itajaí-Açu e Itajaí-Mirim, que mostra o nível em cada cidade, as cotas de referência e uma estimativa do tempo de chegada da cheia. O código e os dados são públicos (github.com/haohmarusc-glitch/enchentes-vale-itajai) e tudo é apresentado com a fonte citada.

Antes dos pedidos, o agradecimento: o material que a Defesa Civil de Gaspar publica é, de longe, o mais completo que encontrei na bacia. O mapa "Cotas de enchente" no Google My Maps rendeu 1.619 pontos de rua com cota, e o Plano de Contingência trouxe as faixas de monitoramento do rio, que eram exatamente o que faltava para Gaspar. Conferi um material contra o outro: das 26 vias do quadro do item 4.2.2, 24 batem ao centavo com os pontos do mapa. É uma consistência que não encontrei em nenhuma outra cidade.

Tenho quatro pedidos, em ordem de importância.

1. Uma forma de ler o nível do rio de fora da região. A página defesacivil.gaspar.sc.gov.br/monitoramento/tabela não responde a acessos de fora de Santa Catarina: o endereço resolve normalmente, mas a conexão expira. Testei em duas datas, três tentativas, e o mesmo servidor de onde faço os testes acessa sem problema os sites das Defesas Civis de Itajaí, Blumenau e Rio do Sul. Consegui ler a tabela apenas uma vez, a partir de um arquivo salvo pelo navegador de dentro da região, e nela o Rio Itajaí-Açu em Gaspar marcava 3,85 m às 22h59 de 31/08/2026. Se houver um endereço de dados (JSON, CSV ou similar) que possa ser consultado de fora, ou se for possível liberar o acesso, o nível de Gaspar passa a aparecer no site junto com o das demais cidades. Também consultei a rede estadual (monitoramento.defesacivil.sc.gov.br), mas a estação de Gaspar ali publica apenas chuva, sem valor de nível de rio.

2. A confirmação de a que régua se referem as faixas do fluxograma do Plano. O item 4.2.3 traz 0 a 5 m como normalidade, 5 a 6 m como atenção/alerta, 6 a 7 m como alerta/alarme e acima de 7 m como resposta. Cadastrei essas faixas como as cotas de Gaspar, entendendo que estão na mesma régua das cotas de rua do item 4.2.2 e da tabela de monitoramento — a leitura de 3,85 m cai na faixa de normalidade e as cotas de rua vão de 6,20 m a 7,33 m, o que é coerente. Mas o Plano não nomeia o ponto da régua nem o zero a que ela se refere, e essa é a informação que não posso deduzir. Se forem réguas diferentes, o que está no site hoje está errado e eu retiro imediatamente.

3. A confirmação de três cotas de rua. Comparando o quadro do Plano com o mapa público, encontrei duas diferenças pequenas e uma ausência: a Rua Imaruí aparece com 7,02 m no Plano, enquanto o ponto do mapa (esquina com a Rua Santa Isabel) marca 7,00 m; a Rua Maria da Silva aparece com 6,99 m no Plano e 7,00 m no mapa; e a Rua Santa Isabel, que o Plano lista com 7,00 m, não existe com nome próprio no mapa. Mantive os dois valores registrados em cada caso, sem escolher entre eles.

4. Uma dúvida antiga sobre um nome de rua. Em um levantamento mais antigo do CEOPS, reproduzido pela imprensa, consta uma "Rua Lino" com cota de 6,57 m. No mapa de vocês existe uma "Rua Lírio" cuja cota mínima é exatamente 6,57 m, e não existe nenhuma "Rua Lino". Suponho que seja a mesma rua com um erro de transcrição em algum ponto da cadeia, mas mantive as duas cadastradas por não ter como confirmar.

O site avisa em todas as páginas que não é sistema oficial de alerta, que não substitui a Defesa Civil e que, em emergência, deve-se ligar 199. Nenhum número que vocês publicam é alterado ou convertido por mim: quando duas fontes divergem, as duas ficam registradas com a origem de cada uma. O crédito à Defesa Civil de Gaspar aparece em cada dado utilizado.

Fico à disposição para qualquer esclarecimento e agradeço desde já.
Atenciosamente,
Jefferson — (47) 98405-6082 · haohmarusc@gmail.com

---

## C5 — EPAGRI/CIRAM, Equipe de Hidrologia

**Para:** sshidrosc@epagri.sc.gov.br
**Assunto:** Solicitação de acesso à API do Rios On-Line e à relação de estações da bacia do Itajaí-Açú

À Equipe de Hidrologia da EPAGRI/CIRAM,

Meu nome é Jefferson, sou morador da região do Vale do Itajaí e estudante de Engenharia de Software. Desenvolvo um site aberto e sem fins comerciais sobre as enchentes dos rios Itajaí-Açu e Itajaí-Mirim, que reúne o nível do rio em cada cidade, as cotas de referência e uma estimativa do tempo de chegada da cheia. O código e os dados são públicos (github.com/haohmarusc-glitch/enchentes-vale-itajai) e cada informação é apresentada com a fonte citada.

O Boletim de Monitoramento Hidrológico de vocês e o painel Rios On-Line são, de longe, o material mais completo que encontrei para as cabeceiras da bacia — Taió, Ituporanga, Vidal Ramos e Alfredo Wagner —, que são justamente as cidades para as quais eu tenho o nível do rio mas ainda não tenho a cota de referência que permitiria orientar a população. Duas coisas do painel me chamaram a atenção: ele publica o código da estação (que entendo ser o código da ANA) e classifica cada estação em faixas de situação (Atenção, Alerta e Emergência, para enchente e para estiagem). Essas duas informações são exatamente as que faltam ao meu projeto.

Gostaria de solicitar, se for possível:

1. A forma adequada de acessar os dados do Rios On-Line de maneira programática e estável — o painel consome um serviço que requer autenticação, e eu prefiro pedir o acesso correto a depender de uma solução frágil. Respeito integralmente qualquer limite de frequência ou termo de uso que vocês indicarem, e identifico todas as requisições com o nome do projeto.

2. A relação das estações da bacia do Rio Itajaí-Açú com o código da estação e as coordenadas geográficas de cada uma. Preciso das coordenadas para vincular com segurança cada estação de vocês à régua correspondente no meu cadastro — por exemplo, para confirmar se a estação "Salseiro", em Vidal Ramos, é a mesma régua que eu já acompanho por outra rede naquele município. Sem a coordenada, eu não faço o vínculo, para não arriscar somar dados de réguas diferentes.

3. Se estiverem disponíveis, os valores das faixas de Atenção, Alerta e Emergência (em centímetros de régua) de cada estação da bacia. É a informação que permitiria ao site dizer ao morador dessas cidades a partir de que nível o rio entra em cada faixa — hoje eu mostro o número, mas não tenho como qualificá-lo.

O site deixa claro em todas as páginas que não é sistema oficial de alerta, que não substitui a Defesa Civil nem os órgãos oficiais de monitoramento, e que em emergência se deve ligar 199. Os níveis de vocês são publicados em centímetros e assim seriam tratados, com o crédito à EPAGRI/CIRAM em cada dado utilizado.

Fico à disposição para qualquer esclarecimento e agradeço desde já a atenção.
Atenciosamente,
Jefferson — (47) 98405-6082 · haohmarusc@gmail.com

---

## C2 — Defesa Civil de Itajaí / GEOItajaí

**Para:** protocolo da Prefeitura de Itajaí / Defesa Civil de Itajaí (defesacivil.itajai.sc.gov.br, menu Contato)
**Assunto:** Solicitação de acesso às camadas de cota de inundação por endereço (ArcGIS da Prefeitura)

À Defesa Civil de Itajaí / equipe de Geoprocessamento (GEOItajaí),

Meu nome é Jefferson, sou morador de Itajaí e estudante de Engenharia de Software. Estou desenvolvendo um site aberto e sem fins comerciais sobre enchentes dos rios Itajaí-Açu e Itajaí-Mirim (github.com/haohmarusc-glitch/enchentes-vale-itajai), sempre citando a fonte.

Usei com muito proveito os serviços públicos do ArcGIS da Prefeitura (arcgis.itajai.sc.gov.br), em especial as camadas de áreas atingidas e de cotas de inundação de 2011 a 2015, os pontos cotados altimétricos e o terreno sujeito a inundação, todos acessíveis em GeoJSON. Agradeço por manter esses dados abertos.

Notei, porém, que a pasta de serviços "defesacivil" exige token de autenticação e não pude consultá-la. Gostaria de solicitar:

1. Se possível, a liberação de leitura pública (ou um export em GeoJSON/shapefile) das camadas de cota de inundação por endereço mantidas nessa pasta, para que o site possa informar ao morador a partir de que nível do rio sua rua é atingida, como as Defesas Civis de Blumenau, Gaspar e Brusque já fazem.

2. A confirmação da licença de uso das camadas públicas do serviço historico_inundacoes e do Relevo_Ponto_Cotado_Altimetrico, para eu citá-la corretamente.

3. O dicionário de dados da camada Hidrografia_Terreno_Sujeito_Inundacao: o que ela representa e em que escala. Baixei os 110 polígonos e eles somam 38,7 hectares, com o menor tendo 4 m² — enquanto a mancha da cheia de 1983, do próprio serviço de vocês, cobre 7.086 ha. Como não sei o que a camada mapeia, preferi não publicá-la: com o nome que ela tem, quem morasse fora dos polígonos poderia entender que sua rua não alaga.

4. Se houver, a cota do marégrafo de Cabeçudas (UNIVALI/Porto) em formato aberto, para relacionar maré e nível do rio na foz.

O site não substitui a Defesa Civil e informa isso em todas as páginas (emergência: 199). O objetivo é puramente informativo e comunitário.

Fico à disposição para conversar e para atender às condições de uso que a Prefeitura considerar adequadas.
Atenciosamente,
Jefferson — (47) 98405-6082 · haohmarusc@gmail.com

---

## C3 — UNIVALI (marégrafo de Cabeçudas)

**Para:** michelena@univali.br; ariadne@univali.br
**Assunto:** Reforço: acesso aberto aos dados do marégrafo de Cabeçudas

Prezados,

Meu nome é Jefferson, sou morador da região e estudante de Engenharia de Software. Escrevi em 30/08 (para bjast@univali.br) sobre um site aberto e sem fins comerciais das enchentes dos rios Itajaí-Açu e Itajaí-Mirim (github.com/haohmarusc-glitch/enchentes-vale-itajai). Reencaminho o pedido, entendendo que vocês são os contatos titular e suplente da UNIVALI/CTTMAR no GRAC do Plano de Contingência de Itajaí.

O site tem uma tela para a foz, em Itajaí, que relaciona a chegada da cheia dos dois rios com o estado da maré — porque na foz a maré influencia o nível do Açu e do Mirim. Hoje uso a tábua de maré prevista; o dado que faltaria para fechar essa análise é a medição real do marégrafo de Cabeçudas, cuja ampliação, pelo que li, foi feita justamente para medir esse efeito.

Gostaria de saber se há uma forma de acesso aberto aos dados do marégrafo (um endereço de dados, um export, ou a indicação de com quem falar), em qualquer frequência que vocês considerem adequada. Identifico todas as requisições com o nome do projeto e cito a UNIVALI/CTTMAR como fonte.

O site deixa claro que não é sistema oficial de alerta e que, em emergência, deve-se ligar 199.

Agradeço desde já e fico à disposição.
Atenciosamente,
Jefferson — (47) 98405-6082 · haohmarusc@gmail.com

---

## C1 — Defesa Civil de Brusque (já enviado 31/08, referência)

**Para:** defesacivil@brusque.sc.gov.br — **ENVIADO em 31/08/2026.**

Se houver resposta, o complemento a mandar (achado depois do envio): dos 47 marcadores do bairro Limoeiro, o segundo mais baixo é 6,86 m e a mediana é 8,33 m, e a própria Rua Maria Scarpa Formonti aparece em outro ponto a 7,48 m — enquanto o marcador de 3,76 m fica isolado. Ou seja: ou é a faixa marginal do rio, ou houve algo na medição daquele ponto, e é isso que só a Defesa Civil de Brusque pode dizer. O texto integral enviado está em `docs/pendencias-navegador-e-oficios.md`, seção C1.
