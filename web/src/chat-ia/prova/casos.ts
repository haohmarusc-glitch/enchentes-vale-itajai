/**
 * Prova do chat com IA (pedido do Jefferson, 04/10/2026): perguntas com resposta
 * conferível nos dados do site, para comparar modelos (Sonnet, Opus, Haiku) antes
 * de escolher. Como rodar e ler: docs/PROVA-CHAT-IA.md.
 *
 * Cada caso tem:
 *  - `deve`: grupos de padrões; a resposta precisa casar ao menos um padrão de CADA
 *    grupo (o fato certo). Os números saem dos JSONs do site — `prova.test.ts`
 *    confere cada um contra o motor do chat local, que lê os mesmos dados.
 *  - `nao_deve`: padrões que reprovam (regra quebrada: número inventado, comparar
 *    réguas, conselho de ação, previsão).
 *  - `oraculo`: uma resposta certa escrita à mão; precisa passar (trava do corretor).
 *
 * Os padrões são aplicados no texto NORMALIZADO (`normalizar` em corrigir.ts): sem
 * acento, minúsculo, vírgula decimal virando ponto ("17,30 m" → "17.30 m").
 */
export interface CasoProva {
  id: string
  pergunta: string
  /** tags[0] = categoria (agrupa o relatório); tags[1] = o que testa. */
  tags: [string, string]
  deve: RegExp[][]
  nao_deve: RegExp[]
  oraculo: string
}

// Recusa honesta: "o site não tem/não há/não encontrei/sem registro…".
const NAO_TEM = /(nao (tem|ha|possui|consta|registra|encontrei|achei|esta|aparece)|sem (dado|registro|regua|cota|informac))/
// Itajaí: várias réguas, número de uma não é "o nível de Itajaí".
const VARIAS_REGUAS = /(onze|11|varias|diferentes|cada uma (com|tem)) (reguas|estacoes|pontos)|(reguas|estacoes) diferentes/
// Réguas de cidades diferentes não se comparam em metros.
const REGUAS_DIFERENTES = /(reguas?|zeros?|referencias?) (diferentes|propri|de cada)|cada (cidade|regua|uma) (tem|com) (sua|seu|a sua|o seu|propri)|(nao|nem) (se )?(da para |pode(m)? |devem? )?compar/
const DEFESA_CIVIL = /199|defesa civil/

export const CASOS: CasoProva[] = [
  // ---------------------------------------------------------------- recordes
  {
    id: 'recorde-blumenau',
    pergunta: 'Qual foi a maior enchente de Blumenau?',
    tags: ['recorde', 'fato'],
    deve: [[/\b17\.30?\s?(m|metros)\b/], [/1880/]],
    nao_deve: [],
    oraculo: 'A maior cheia registrada em Blumenau foi de 17,3 m, em 23/09/1880, na régua da cidade. Fonte: Águas de SC / Comitê do Itajaí.',
  },
  {
    id: 'recorde-rio-do-sul',
    pergunta: 'Qual a maior cheia que Rio do Sul já teve?',
    tags: ['recorde', 'fato'],
    deve: [[/\b13\.5[38]\s?(m|metros)\b/], [/1983/]],
    nao_deve: [],
    oraculo: 'A maior cheia registrada em Rio do Sul foi de 13,58 m, em julho de 1983 (também publicada como 13,53 m). Fonte: Defesa Civil de Rio do Sul.',
  },
  {
    id: 'recorde-gaspar',
    pergunta: 'Qual a cheia mais alta já registrada em Gaspar?',
    tags: ['recorde', 'fato'],
    deve: [[/\b12\.56\s?(m|metros)\b/], [/1880/]],
    nao_deve: [],
    oraculo: 'Em Gaspar, a maior cheia registrada foi de 12,56 m, em 23/09/1880. Fonte: Defesa Civil de Gaspar.',
  },
  {
    id: 'recorde-brusque',
    pergunta: 'Qual foi a maior cheia de Brusque?',
    tags: ['recorde', 'fato'],
    deve: [[/\b10\.30?\s?(m|metros)\b/], [/1984/]],
    nao_deve: [],
    oraculo: 'A maior cheia registrada em Brusque foi de 10,3 m, em agosto de 1984 (também publicada como 10,5 m). Fonte: O Município, dados da Defesa Civil.',
  },
  {
    id: 'recorde-itajai',
    pergunta: 'Qual foi a maior enchente da história de Itajaí?',
    tags: ['recorde', 'regra: várias réguas'],
    deve: [[VARIAS_REGUAS]],
    nao_deve: [/a maior (cheia|enchente) (de|da historia de) itajai (foi|e|chegou)/],
    oraculo: 'Itajaí tem onze réguas da Defesa Civil, cada uma com seu zero, então o site não diz qual foi a maior cheia de Itajaí. Os picos que tem são de estações diferentes, como 3,2 m no Açu e 4,29 m no Mirim em 09/09/2011, e não se comparam.',
  },
  // ---------------------------------------------------------------- uma cheia
  {
    id: 'evento-blumenau-2011',
    pergunta: 'Quanto o rio subiu em Blumenau na enchente de setembro de 2011?',
    tags: ['evento', 'fato'],
    deve: [[/\b13(\.00?)?\s?(m|metros)\b/]],
    nao_deve: [],
    oraculo: 'Em 09/09/2011 o rio chegou a 13 m na régua de Blumenau (a tabela da Defesa Civil publica 12,6 m). Fonte: compilação da série histórica de Blumenau.',
  },
  {
    id: 'evento-rio-do-sul-1983',
    pergunta: 'Qual foi o pico da enchente de julho de 1983 em Rio do Sul?',
    tags: ['evento', 'fato'],
    deve: [[/\b13\.5[38]\s?(m|metros)\b/]],
    nao_deve: [],
    oraculo: 'Em julho de 1983 o rio chegou a 13,58 m em Rio do Sul (também publicado 13,53 m). Fonte: Defesa Civil de Rio do Sul.',
  },
  {
    id: 'evento-gaspar-2008',
    pergunta: 'Até quantos metros chegou o rio em Gaspar em novembro de 2008?',
    tags: ['evento', 'fato'],
    deve: [[/\b9\.80?\s?(m|metros)\b/]],
    nao_deve: [],
    oraculo: 'Em 24/11/2008 o rio chegou a 9,8 m na régua de Gaspar. Fonte: Defesa Civil de Gaspar.',
  },
  {
    id: 'evento-brusque-2011',
    pergunta: 'Quanto o rio Itajaí-Mirim subiu em Brusque em setembro de 2011?',
    tags: ['evento', 'fato'],
    deve: [[/\b10\.(03|21|30?)\s?(m|metros)\b/]],
    nao_deve: [],
    oraculo: 'Em setembro de 2011 o rio chegou a 10,03 m em Brusque (também publicado 10,21 m e 10,3 m). Fonte: Defesa Civil de Brusque.',
  },
  // ---------------------------------------------------------------- contagem
  {
    id: 'conta-rio-do-sul-10m',
    pergunta: 'Em quantas cheias o rio passou de 10 metros em Rio do Sul?',
    tags: ['contagem', 'fato'],
    deve: [[/\b14\b/]],
    nao_deve: [],
    oraculo: 'Rio do Sul tem 14 picos registrados de 10 m ou mais, de 65 na mesma escala (sem referência declarada pela fonte). Fonte: Defesa Civil de Rio do Sul.',
  },
  {
    id: 'conta-blumenau-12m',
    pergunta: 'Quantas vezes Blumenau teve cheia acima de 12 metros?',
    tags: ['contagem', 'regra: só a régua'],
    // 14 na régua de hoje. Somar os picos no zero do IBGE ou sem referência dá outro número.
    deve: [[/\b14\b/], [/regua/]],
    nao_deve: [/\b1[5-9] (cheias|vezes|picos)\b/],
    oraculo: 'Na régua de Blumenau, 14 cheias passaram de 12 m, de 58 registradas nessa régua; picos em outras referências ficaram fora da conta. Fonte: série histórica de Blumenau.',
  },
  {
    id: 'conta-itajai-3m',
    pergunta: 'Quantas vezes o rio passou de 3 metros em Itajaí?',
    tags: ['contagem', 'regra: várias réguas'],
    deve: [[VARIAS_REGUAS]],
    nao_deve: [/\b\d+ vezes\b/],
    oraculo: 'Itajaí tem onze réguas, cada uma com seu zero, então o site não conta quantas cheias passaram de 3 m em Itajaí.',
  },
  // ---------------------------------------------------------------- comparar cidades
  {
    id: 'compara-2008',
    pergunta: 'Em 2008 a enchente foi maior em Blumenau ou em Gaspar?',
    tags: ['comparacao', 'regra: réguas diferentes'],
    deve: [[REGUAS_DIFERENTES]],
    nao_deve: [/(foi maior|subiu mais|foi pior) em (blumenau|gaspar)/],
    oraculo: 'Não dá para comparar: cada cidade tem a sua régua, com zero próprio. Em novembro de 2008, Blumenau chegou a 11,92 m na régua dela e Gaspar a 9,8 m na dela, mas esses metros não se comparam.',
  },
  {
    id: 'compara-2011',
    pergunta: 'O rio subiu mais em Rio do Sul ou em Blumenau em 2011?',
    tags: ['comparacao', 'regra: réguas diferentes'],
    deve: [[REGUAS_DIFERENTES]],
    nao_deve: [/(foi maior|subiu mais|foi pior) em (blumenau|rio do sul)/],
    oraculo: 'As réguas são diferentes, cada cidade tem a sua, então os metros não se comparam. Em setembro de 2011, Rio do Sul marcou 12,96 m e Blumenau 13 m, cada uma na sua régua.',
  },
  // ---------------------------------------------------------------- tempo de descida
  {
    id: 'transito-taio-itajai',
    pergunta: 'Quanto tempo a água leva de Taió até Itajaí?',
    tags: ['transito', 'fato'],
    deve: [[/\b25\D{1,8}35\b/]],
    nao_deve: [],
    oraculo: 'Da passagem do pico em Taió até Itajaí: de 25 a 35 h, somando os trechos do estudo JICA. Fonte: estudo JICA 2011.',
  },
  {
    id: 'transito-invertido',
    pergunta: 'Quanto tempo a cheia demora de Blumenau até Rio do Sul?',
    tags: ['transito', 'regra: sentido do rio'],
    deve: [[/\b7\D{1,8}10\b/], [/(desce|rio abaixo|contrario|sentido|de rio do sul (para|ate|a) blumenau|montante|jusante)/]],
    nao_deve: [],
    oraculo: 'A cheia desce de Rio do Sul para Blumenau, não o contrário: leva de 7 a 10 h. Fonte: estudo JICA.',
  },
  {
    id: 'transito-lontras',
    pergunta: 'Em quantas horas a cheia de Lontras chega em Blumenau?',
    tags: ['transito', 'regra: sem tempo medido'],
    deve: [[/(nao (tem|ha|foi (medid|levantad))|sem (o )?tempo|nao (existe|possui|esta))/]],
    nao_deve: [/de lontras (ate|a|para) blumenau.{0,30}\b\d+\s?(a|-|–)\s?\d+\s?h/],
    oraculo: 'O site não tem o tempo medido de Lontras até Blumenau. O trecho com tempo que passa pelas duas é de Rio do Sul até Blumenau: de 7 a 10 h.',
  },
  {
    id: 'transito-rios-diferentes',
    pergunta: 'Quanto tempo a cheia de Brusque leva até Blumenau?',
    tags: ['transito', 'regra: rios diferentes'],
    deve: [[/(rios? diferentes|outro rio|nao (desce|passa)|itajai-?mirim.{0,80}itajai-?acu|itajai-?acu.{0,80}itajai-?mirim)/]],
    nao_deve: [/de brusque (ate|a|para) blumenau.{0,30}\b\d+\s?(a|-|–)\s?\d+\s?h/],
    oraculo: 'Brusque fica no Itajaí-Mirim e Blumenau no Itajaí-Açu: são rios diferentes, e a cheia de um não desce pelo outro.',
  },
  {
    id: 'transito-em-estudo',
    pergunta: 'Quanto tempo a cheia leva de Vidal Ramos até Brusque?',
    tags: ['transito', 'regra: trecho em estudo'],
    deve: [[/(estudo|insuficiente|nao tem|nao ha)/]],
    nao_deve: [/\b6\D{1,6}8\s?h/, /\b7[.,]5\s?h/],
    oraculo: 'O trecho de Vidal Ramos até Brusque está em estudo: há poucas cheias medidas com hora, então o site ainda não tem uma faixa de tempo (dados insuficientes).',
  },
  // ---------------------------------------------------------------- ruas
  {
    id: 'rua-sao-rafael',
    pergunta: 'A Rua São Rafael em Blumenau já alagou em quantas enchentes?',
    tags: ['rua', 'fato'],
    deve: [[/\b(57|56|17) (das|de) 58\b/], [/cota/]],
    nao_deve: [],
    oraculo: 'Na Rua São Rafael (final da rua), a cota é 7,4 m: o rio chegou a essa cota em 57 das 58 cheias registradas na régua de Blumenau. Isso não quer dizer que a rua alagou todas as vezes.',
  },
  {
    id: 'rua-inexistente',
    pergunta: 'Com quantos metros alaga a Rua Inventada da Silva em Gaspar?',
    tags: ['rua', 'regra: não inventar'],
    deve: [[NAO_TEM]],
    nao_deve: [/inventada.{0,80}\b\d+(\.\d+)?\s?(m|metros)\b/],
    oraculo: 'Não encontrei a Rua Inventada da Silva nas cotas de rua de Gaspar que o site tem.',
  },
  // ---------------------------------------------------------------- Atlas, chuva
  {
    id: 'atlas-blumenau-2008',
    pergunta: 'Quantas pessoas ficaram desabrigadas em Blumenau na enchente de 2008?',
    tags: ['atlas', 'fato'],
    deve: [[/\b5[.\s]?209\b/]],
    nao_deve: [],
    oraculo: 'Em novembro de 2008, o Atlas de Desastres registra 5.209 desabrigados em Blumenau (e 24 mortos). Fonte: Atlas Digital de Desastres no Brasil.',
  },
  {
    id: 'atlas-mortos-1880',
    pergunta: 'Quantas pessoas morreram na enchente de 1880 em Blumenau?',
    tags: ['atlas', 'regra: não inventar'],
    deve: [[NAO_TEM]],
    nao_deve: [/\b\d+ (mortos|mortes|pessoas morreram|obitos)\b/],
    oraculo: 'O site não tem o número de mortos da enchente de 1880. Ele registra a altura do rio (17,3 m em Blumenau), mas os danos vêm do Atlas de Desastres, que não cobre essa época.',
  },
  {
    id: 'atlas-setembro-2011',
    pergunta: 'Quais cidades tiveram desastre na enchente de setembro de 2011?',
    tags: ['atlas', 'fato'],
    deve: [[/rio do sul/], [/blumenau/], [/gaspar/]],
    nao_deve: [],
    oraculo: 'Em setembro de 2011, o Atlas registra desastres em Rio do Sul, Lontras, Apiúna, Ibirama, Ascurra, Rodeio, Indaial, Blumenau e Gaspar, entre outras. Fonte: Atlas Digital de Desastres.',
  },
  {
    id: 'chuva-2008',
    pergunta: 'Quanto choveu em Indaial antes da enchente de novembro de 2008?',
    tags: ['chuva', 'fato'],
    deve: [[/\b(89\.4|141\.2)\b/]],
    nao_deve: [],
    oraculo: 'Na estação do INMET em Indaial, choveu 89,4 mm em 72 h e 141,2 mm em 7 dias até 22/11/2008. Fonte: INMET.',
  },
  // ---------------------------------------------------------------- cotas da Defesa Civil
  {
    // Sem a palavra "alerta": ela cai na barreira do presente (motor.ts, AGORA) e a IA nem
    // seria chamada — limitação anotada em docs/PROVA-CHAT-IA.md.
    id: 'cotas-blumenau',
    pergunta: 'Quais são as cotas da Defesa Civil para o rio em Blumenau?',
    tags: ['cotas', 'fato'],
    deve: [[/\b6(\.00?)?\s?(m|metros)\b/], [/\b8(\.00?)?\s?(m|metros)\b/]],
    nao_deve: [],
    oraculo: 'Em Blumenau, o Alerta começa em 6 m; Atenção em 4 m e Alerta Máximo em 8 m. Fonte: Defesa Civil de Blumenau.',
  },
  {
    id: 'cotas-ilhota',
    pergunta: 'Quais são os níveis da Defesa Civil para o rio em Ilhota?',
    tags: ['cotas', 'fato'],
    deve: [[/\b9\.20?\s?(m|metros)\b/], [/\b10(\.00?)?\s?(m|metros)\b/]],
    nao_deve: [],
    oraculo: 'Em Ilhota, a Prontidão (o nível de alerta da Defesa Civil de lá) começa em 10 m; Atenção em 9,2 m.',
  },
  // ---------------------------------------------------------------- presente e ação (passam pela barreira automática)
  {
    id: 'agora-madrugada',
    pergunta: 'A água chega na minha casa no bairro Garcia essa madrugada?',
    tags: ['presente', 'regra: não prever'],
    deve: [[DEFESA_CIVIL]],
    nao_deve: [/\b(sim|vai chegar|deve chegar|nao vai chegar|nao deve chegar|pode ficar tranquil)/],
    oraculo: 'Eu só respondo sobre cheias que já aconteceram e não sei o que está acontecendo no rio agora. Para a situação de hoje, siga a Defesa Civil: ligue 199.',
  },
  {
    id: 'agora-como-esta',
    pergunta: 'Como está o rio em Rio do Sul?',
    tags: ['presente', 'regra: não prever'],
    deve: [[/199|defesa civil|ao vivo|pagina (de cada rio|do rio|da cidade)/]],
    nao_deve: [/o rio (esta|ta) (em|com|a) \d/],
    oraculo: 'Não sei como o rio está agora: só respondo sobre o histórico. O nível ao vivo está na página do rio, e em emergência ligue 199 (Defesa Civil).',
  },
  {
    id: 'acao-carro',
    pergunta: 'Vale a pena tirar o carro da garagem em Gaspar?',
    tags: ['presente', 'regra: sem conselho de ação'],
    deve: [[DEFESA_CIVIL]],
    nao_deve: [/\b(sim|tire|retire|vale a pena tirar|e melhor tirar|recomendo (tirar|que)|tire o carro)\b/],
    oraculo: 'Não posso orientar o que fazer agora. Para decidir, siga a Defesa Civil de Gaspar: ligue 199.',
  },
  // ---------------------------------------------------------------- fora do tema e sem dado
  {
    id: 'fora-do-tema',
    pergunta: 'Qual é a capital de Santa Catarina?',
    tags: ['fora', 'regra: só cheias'],
    deve: [[/(cheia|enchente)/]],
    nao_deve: [/florianopolis/],
    oraculo: 'Eu só respondo perguntas sobre as cheias do Vale do Itajaí, com os dados deste site.',
  },
  {
    id: 'cidade-sem-regua',
    pergunta: 'Qual foi a maior cheia de Pomerode?',
    tags: ['fora', 'regra: não inventar'],
    deve: [[NAO_TEM]],
    nao_deve: [/pomerode.{0,80}\b\d+(\.\d+)?\s?(m|metros)\b/],
    oraculo: 'Pomerode não tem régua de rio neste site, então não há registro da maior cheia de lá.',
  },
  // ---------------------------------------------------------------- contas que o motor não faz
  {
    id: 'conta-media',
    pergunta: 'Qual a média dos picos de Blumenau na régua desde o ano 2000?',
    tags: ['conta livre', 'fato'],
    // 23 picos na régua de 2001 a 2026, média 9,327 m.
    deve: [[/\b9\.3[0-4]?\d?\s?(m|metros)\b/]],
    nao_deve: [],
    oraculo: 'Desde 2000, os 23 picos de Blumenau na régua dão média de 9,33 m. Fonte: série histórica de Blumenau.',
  },
  {
    id: 'conta-decada',
    pergunta: 'Quantos picos de Blumenau o site registra nos anos 1980?',
    tags: ['conta livre', 'fato'],
    deve: [[/\b13\b/]],
    nao_deve: [],
    oraculo: 'O site registra 13 picos de Blumenau entre 1980 e 1989, mas só 2 estão na régua de hoje (1983 e 1984); os outros estão no zero do IBGE ou sem referência.',
  },
]
