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

## C. Ofícios a enviar (rascunhos prontos em C1–C3; enviar quando tiver os e-mails)

Destinatários prováveis:
- Defesa Civil de Brusque: pelo site `defesacivil.brusque.sc.gov.br` (menu Contato) ou protocolo da Prefeitura.
- Prefeitura/Defesa Civil de Itajaí (GEOItajaí / SEURB): `arcgis.itajai.sc.gov.br` é do município; o serviço
  `defesacivil` está fechado por token — pedir liberação de leitura ou export das camadas de cota por endereço.

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
3. Se houver, a cota do marégrafo de Cabeçudas (UNIVALI/Porto) em formato aberto, para relacionar maré e nível do rio na foz.

O site não substitui a Defesa Civil e informa isso em todas as páginas (emergência: 199). O objetivo é puramente informativo e comunitário.

Fico à disposição para conversar e para atender às condições de uso que a Prefeitura considerar adequadas.
Atenciosamente, Jefferson — [telefone / e-mail]

### C3. (opcional) Reforço à Univali sobre o marégrafo
Já enviado em 30/08 para bjast@univali.br. Reenviar para michelena@univali.br (titular no GRAC, do Plano de
Contingência) e ariadne@univali.br (suplente), pedindo o formato de acesso aberto ao marégrafo de Cabeçudas.
