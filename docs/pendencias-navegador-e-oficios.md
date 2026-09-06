# Pendências: coletas no navegador + ofícios

## A. Coletas que exigem o Chrome (extensão Claude reconectada)

### A1. Reenviar `rio-do-sul-asthon-api.json` com nível ao vivo de Taió, Ituporanga e Vidal Ramos
Motivo: são as três estações que a Defesa Civil de SC (GraphQL) não resolve bem, mas a API Asthon de
Rio do Sul cobre (city_id 4214805). Passos no console de `defesacivil.riodosul.sc.gov.br`:
```js
const j=async u=>(await fetch(u)).json();
const B='https://public.asthon.com.br/public/';
const live=await j(B+'stations/live?city_id=4214805&_v=2');
const list=await j(B+'stations/list?city_id=4214805&_v=2');
const alvo=(list||[]).filter(s=>/ta[ií]o|ituporanga|vidal ramos/i.test(s.name||s.nome||''));
// baixar live + list + as 3 estações-alvo com seus station_id
```
Salvar em `data/brutos/rio-do-sul-asthon-api.json` e rodar `scripts/coleta_rio_do_sul.py`.
Se a Asthon não trouxer Vidal Ramos (fica no Itajaí-Mirim, não no Alto Vale), usar DCSC-00024 do GraphQL.

### A2. Baixar os três arquivos que bloqueiam robô (só pelo navegador logado)
1. **Estudo de cotas de Brusque 2024** — `https://bit.ly/novascotasbrusque` (redireciona p/ site da DC Brusque).
   Salvar PDF/planilha em `data/brutos/brusque-cotas-2024.*`.
2. **PDF de cotas de Blumenau 2014** (Prefeitura, via Farol Blumenau) —
   `https://farolblumenau.com/wp-content/uploads/2014/06/Cotas-de-enchente-das-ruas-Blumenau.pdf`.
   Salvar em `data/brutos/blumenau-cotas-2014.pdf`. Serve para conferir a lista de 2023 (1.938 pts) já baixada.
3. **KML de Gaspar** — abrir `https://defesacivil.gaspar.sc.gov.br/mapas/cotas-de-enchente-0`, pegar o `mid`
   do iframe do Google My Maps e baixar `https://www.google.com/maps/d/kml?mid=<MID>&forcekml=1`.
   (No teste de 31/08 a camada era `cotas_enchente_gaspar_01042020`, 1.615 pontos, campos cota/refer_1/refer_2/bairro/lat/lon.)
   Salvar em `data/brutos/gaspar-cotas-ruas-mymaps.kml` e rodar `scripts/converter_kml_cotas.py … gaspar`.

## B. Itajaí-Mirim não tem alerta adiantado — lacuna a resolver por ofício

Constatação (31/08/2026): no Itajaí-Mirim, o monitoramento pula de "abaixo das cotas" direto para
"inundação". As estações da Defesa Civil de Itajaí no Mirim (DC-03 a DC-06, DC-10) têm atenção/alerta/
emergência definidos (Plano de Contingência, Tabela 11), MAS:
- Em **Brusque** (a cidade a montante que dá o tempo de resposta para Itajaí) só se conhece publicamente a
  **cota de inundação da Beira-Rio: 4,80 m**. Não há cota de atenção nem de alerta divulgada — ou seja, não
  existe faixa amarela/laranja antes de inundar. Para uma cidade de resposta rápida (enxurrada, não cheia
  lenta), isso é o pior caso: quando passa de 4,80 m já está inundando.
- Consequência para o site: a tela do Itajaí-Mirim não consegue mostrar "atenção/alerta" em Brusque como
  mostra no Açu. Só dá para mostrar "abaixo de 4,80 m" vs "inundação".

Encaminhamentos (ofícios B1 e B2 abaixo) para obter as cotas de atenção/alerta de Brusque e fechar a lacuna.

## C. Ofícios a enviar (rascunhos prontos em C1–C5; enviar quando tiver os e-mails)

Destinatários prováveis:
- Defesa Civil de Brusque: pelo site `defesacivil.brusque.sc.gov.br` (menu Contato) ou protocolo da Prefeitura.
- Prefeitura/Defesa Civil de Itajaí (GEOItajaí / SEURB): `arcgis.itajai.sc.gov.br` é do município; o serviço
  `defesacivil` está fechado por token — pedir liberação de leitura ou export das camadas de cota por endereço.
- Defesa Civil de Gaspar: `defesacivil@gaspar.sc.gov.br` — endereço oficial, do cabeçalho de todas as páginas
  do Plano de Contingência. É o único destinatário desta lista que já veio confirmado por documento.

---

### C1. Ofício — Defesa Civil de Brusque ✅ ENVIADO 31/08/2026
Enviado para `defesacivil@brusque.sc.gov.br`. O texto abaixo é o que foi mandado. Ao receber resposta:
gravar as cotas de atenção/alerta em `data/estacoes.json` (cidade `brusque`) e tirar a nota da lacuna de
aviso adiantado do Mirim. **O ponto de 3,76 m só foi achado depois do envio** — se houver resposta, vale
completar com a comparação que reforça a pergunta: dos 47 marcadores do bairro Limoeiro, o segundo mais
baixo é 6,86 m e a mediana é 8,33 m, e a própria rua Maria Scarpa Formonti aparece em outro ponto a
7,48 m. Ou seja: ou é a faixa marginal do rio, ou houve algo na medição — e é isso que só eles podem
dizer.

#### Texto enviado
Assunto: Solicitação: cotas de atenção e alerta do Itajaí-Mirim em Brusque e planilha de cotas por rua

À Defesa Civil de Brusque,

Meu nome é Jefferson, sou morador da região e estudante de Engenharia de Software. Estou desenvolvendo um site aberto e sem fins comerciais sobre enchentes dos rios Itajaí-Açu e Itajaí-Mirim, que mostra o nível em cada cidade, uma estimativa para a cidade a jusante e o tempo de chegada da cheia. O código e os dados são públicos (github.com/haohmarusc-glitch/enchentes-vale-itajai) e sempre com a fonte citada.

Ao montar a parte do Itajaí-Mirim, notei uma lacuna que gostaria de confirmar com vocês. Para Brusque, encontrei publicamente apenas a cota de inundação da Beira-Rio (4,80 m na Ponte Estaiada). Não localizei cotas de atenção e de alerta anteriores à inundação. Como o Itajaí-Mirim responde rápido, essa faixa de aviso adiantado é justamente o que dá tempo de reação em Itajaí, a jusante.

Usei o mapa "Cotas Enchente de Brusque", que vocês publicam no Google My Maps, e gostaria de registrar duas coisas que encontrei nele — a segunda me parece do interesse de vocês.

Primeiro, o agradecimento: a camada de 2023 é um dado excelente. Cada marcador traz a cota e a lâmina d'água medida no local, e a soma das duas fecha em 8,96 m — o pico de 17/11/2023 — em 338 dos 344 pontos que trazem lâmina, com diferença de um centímetro. Foi essa conferência que me permitiu usar esses pontos com segurança, citando a Defesa Civil de Brusque como fonte.

Segundo, o ponto que me preocupou: o marcador mais baixo dessa camada é a Av. Beira Rio, esquina com a Rua Maria Scarpa Formonti, no Limoeiro, com cota de 3,76 m (e 5,20 m de lâmina em 2023 — a soma fecha certo). Ele fica 1,04 m ABAIXO da cota de 4,80 m, que é a mais baixa que encontrei publicada para a cidade. Se estiver correto, naquele ponto a água chega bem antes de qualquer aviso baseado nos 4,80 m. No site eu deixei o número visível com a ressalva de que não foi confirmado com vocês e não o usei para disparar aviso, justamente para não criar alarme indevido — mas achei que valia comunicar.

Gostaria de solicitar, se puderem disponibilizar:
1. As cotas oficiais de atenção e de alerta do Itajaí-Mirim na régua de Brusque (Ponte Estaiada), além da cota de inundação de 4,80 m.
2. A confirmação do ponto de 3,76 m acima, e do nível em que o rio costuma ficar na Ponte Estaiada fora de cheia — preciso disso para saber se essa cota pode ou não servir de aviso.
3. A 2ª etapa do levantamento de cotas por rua, com os pontos que não foram atingidos em novembro de 2023, em planilha ou PDF. A 1ª etapa eu já consegui pelo mapa público.
4. Se existir, o tempo médio de deslocamento da cheia entre Brusque e a foz em Itajaí observado nos últimos eventos.

O site deixa claro em todas as páginas que não substitui a Defesa Civil e que, em emergência, deve-se ligar 199. O objetivo é ajudar a população a entender o comportamento do rio e dar o crédito devido à Defesa Civil de Brusque em tudo o que for utilizado.

Fico à disposição e agradeço desde já.
Atenciosamente, Jefferson — [telefone / e-mail]

### C2. Ofício — Defesa Civil / GEOItajaí (cotas por endereço no ArcGIS + maré)
Assunto: Solicitação de acesso às camadas de cota de inundação por endereço (ArcGIS da Prefeitura)

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
Atenciosamente, Jefferson — [telefone / e-mail]

### C4. Ofício — Defesa Civil de Gaspar (leitura do nível + confirmação da régua)

**Rascunho pronto. Contato oficial, do cabeçalho do próprio Plano de Contingência:**
`defesacivil@gaspar.sc.gov.br` · Rua Coronel Aristiliano Ramos, 435 — Centro, Gaspar/SC · (47) 3091-2020.

**Por que este ofício existe.** Gaspar é a única cidade do eixo do Açu com cota de régua e sem leitura.
As faixas 5 / 6 / 7 m vieram do Plano de Contingência (item 4.2.3) e já estão no site. O que falta é o
número ao vivo, e as duas vias automáticas estão fechadas:

- `defesacivil.gaspar.sc.gov.br` **não responde de fora da região**: o DNS resolve (186.250.184.3), e a
  conexão IPv4 estoura o tempo em 15 s, em três tentativas e duas datas, tanto em `/` quanto em
  `/robots.txt`. Não é IPv6, DNS, TLS nem cliente nosso. A tabela só foi lida a partir de um HTML salvo
  pelo navegador de dentro da região.
- A estação de Gaspar na rede estadual (`DCSC-00005`) responde com carimbo de hora fresco e **sem valor
  de nível** — três vezes seguidas em 01/09/2026 (03:09, 03:24 e 03:33 UTC). A metadados do GraphQL
  estadual **declara** sensor de rio (`rio_nivel.value=true`, observado na coleta de resgate de
  01/09/2026), então não é pluviômetro puro; mas o **valor** de nível não veio em nenhuma das três. Na
  prática ela entrega só chuva, e **não serve como nível ao vivo enquanto não reportar** — por isso não
  entra em `data/estacoes.json`: registrar uma régua que nunca devolveu número seria cobertura aparente,
  pior que o buraco declarado. O mesmo já valia para Blumenau (`DCSC-00026`, `rio_nivel: null`), a outra
  cidade da bacia com sistema municipal próprio.

**Ao receber resposta:** gravar a origem da leitura em `data/estacoes.json` (cidade `gaspar`,
`fontes_tempo_real`), e, se a régua for nomeada, trocar o rótulo provisório
`"Rio Itajaí-Açu em Gaspar (o Plano não nomeia o ponto nem publica o zero)"` pelo nome real. Se a
resposta disser que as faixas do Plano se referem a outra régua que não a das cotas de rua, isso é
**bloqueante**: derruba a coerência que sustenta o cadastro de hoje e as cotas voltam a `{}` até nova
medição.

#### Texto a enviar

Assunto: Solicitação: acesso ao nível do Itajaí-Açu em Gaspar e confirmação da régua das cotas do Plano de Contingência

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
Atenciosamente, Jefferson — [telefone / e-mail]

### C5. Ofício — EPAGRI/CIRAM, Equipe de Hidrologia (acesso à API + código ANA ↔ coordenada)

**Rascunho pronto.** Contato oficial, do rodapé do Boletim: `sshidrosc@epagri.sc.gov.br` · Rodovia Admar
Gonzaga, 1347, Itacorubi, Florianópolis/SC · (48) 3665-5124.

**Por que este ofício, e por que ele é o caminho principal e não a alternativa.** O Rios On-Line da EPAGRI
é a fonte aberta mais promissora que o projeto achou para as cabeceiras (Taió, Ituporanga, Vidal Ramos),
por três razões: publica **código ANA** por estação — nenhuma outra fonte faz isso; **classifica cada
estação em faixas** (Enchente/Normal/Estiagem), ou seja, tem os limiares que faltam a essas cidades; e o
`robots.txt` **libera** o acesso. Mas o endpoint das estações (`estacoesMapa`) exige um header
`Authorization` que o app injeta em runtime — não é o cookie. Dá para achá-lo lendo o bundle na VPS, só
que um coletor apoiado num endpoint interno de uma app que resiste a inspeção é frágil: muda no próximo
build, sem aviso. O acesso documentado resolve isso de vez, e de quebra traz a relação código↔coordenada,
que é o que decide se a estação "Salseiro" (`83892990`) é a nossa régua de Vidal Ramos.

**Ao receber resposta:** se vier a relação código↔coordenada, conferir `83892990` contra `-27.38547 /
-49.35812`; se bater, gravar `codigo_ana` em `vidal-ramos` e o `verificado: true`. Se vierem os limiares
por estação, é a cota de referência dessas cidades — grava em `cotas_m`, com `fonte_cotas` apontando a
EPAGRI, e as três saem de "nível na tela, nenhum aviso".

#### Texto a enviar

Assunto: Solicitação de acesso à API do Rios On-Line e à relação de estações da bacia do Itajaí-Açú

À Equipe de Hidrologia da EPAGRI/CIRAM,

Meu nome é Jefferson, sou morador da região do Vale do Itajaí e estudante de Engenharia de Software. Desenvolvo um site aberto e sem fins comerciais sobre as enchentes dos rios Itajaí-Açu e Itajaí-Mirim, que reúne o nível do rio em cada cidade, as cotas de referência e uma estimativa do tempo de chegada da cheia. O código e os dados são públicos (github.com/haohmarusc-glitch/enchentes-vale-itajai) e cada informação é apresentada com a fonte citada.

O Boletim de Monitoramento Hidrológico de vocês e o painel Rios On-Line são, de longe, o material mais completo que encontrei para as cabeceiras da bacia — Taió, Ituporanga, Vidal Ramos e Alfredo Wagner —, que são justamente as cidades para as quais eu tenho o nível do rio mas ainda não tenho a cota de referência que permitiria orientar a população. Duas coisas do painel me chamaram a atenção: ele publica o código da estação (que entendo ser o código da ANA) e classifica cada estação em faixas de situação (Atenção, Alerta e Emergência, para enchente e para estiagem). Essas duas informações são exatamente as que faltam ao meu projeto.

Gostaria de solicitar, se for possível:

1. A forma adequada de acessar os dados do Rios On-Line de maneira programática e estável — o painel consome um serviço que requer autenticação, e eu prefiro pedir o acesso correto a depender de uma solução frágil. Respeito integralmente qualquer limite de frequência ou termo de uso que vocês indicarem, e identifico todas as requisições com o nome do projeto.

2. A relação das estações da bacia do Rio Itajaí-Açú com o código da estação e as coordenadas geográficas de cada uma. Preciso das coordenadas para vincular com segurança cada estação de vocês à régua correspondente no meu cadastro, e não somar dados de réguas diferentes. Um caso que eu já consegui resolver mostra por que peço: a estação "Salseiro", em Vidal Ramos, que eu cheguei a supor ser a mesma régua que acompanho naquele município — o inventário público da ANA mostrou que estão a cerca de 6,8 km uma da outra e drenam áreas bem diferentes, ou seja, são estações distintas. Sem a coordenada eu não teria como saber, e o vínculo errado teria entrado no site.

3. Se estiverem disponíveis, os valores das faixas de Atenção, Alerta e Emergência (em centímetros de régua) de cada estação da bacia. É a informação que permitiria ao site dizer ao morador dessas cidades a partir de que nível o rio entra em cada faixa — hoje eu mostro o número, mas não tenho como qualificá-lo.

O site deixa claro em todas as páginas que não é sistema oficial de alerta, que não substitui a Defesa Civil nem os órgãos oficiais de monitoramento, e que em emergência se deve ligar 199. Os níveis de vocês são publicados em centímetros e assim seriam tratados, com o crédito à EPAGRI/CIRAM em cada dado utilizado.

Fico à disposição para qualquer esclarecimento e agradeço desde já a atenção.
Atenciosamente, Jefferson — [telefone / e-mail]

### C3. (opcional) Reforço à Univali sobre o marégrafo
Já enviado em 30/08 para bjast@univali.br. Reenviar para michelena@univali.br (titular no GRAC, do Plano de
Contingência) e ariadne@univali.br (suplente), pedindo o formato de acesso aberto ao marégrafo de Cabeçudas.
